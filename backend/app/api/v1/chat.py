import json
import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...models.schemas import ChatRequest, ChatResponse
from ...models.tables import ChatLog
from ...services.llm_client import llm_client
from ...services.rag_engine import retrieve
from ...services.nlu import recognize_intent, rewrite_question
from ...services.rules import rules_engine
from ...services.agent_tools import tool_registry
from ...core.config import settings
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/chat", tags=["对话"])

FALLBACK_ANSWER = "抱歉，我在知识库中没有找到与您问题相关的信息。请尝试换个方式提问，或者联系管理员获取帮助。"
SENSITIVE_WORDS = ["暴力", "色情", "赌博", "毒品"]

TOOL_INTENTS = {
    "query_student": ["查询学生", "学生信息", "查一下", "找一下学生"],
    "create_leave_request": ["请假", "提交请假", "申请请假"],
    "get_leave_status": ["请假状态", "请假进度", "请假审核"],
}

INTENT_REPLIES = {
    "greeting": "你好！我是 Smart Campus Agent，有什么可以帮你的吗？",
    "help": "Smart Campus Agent 功能：\n1. 知识库问答 - 基于上传的文档回答问题\n2. 多轮对话 - 支持上下文追问\n3. 学生查询 - 查询学生信息\n4. 请假管理 - 提交和查询请假申请",
    "knowledge_base": "知识库管理功能位于左侧导航栏底部的「知识库管理」页面。",
    "document": "文档管理功能位于左侧导航栏底部的「文档管理」页面。",
    "system": "Smart Campus Agent v0.1.0",
}


def load_history(db: Session, session_id: str, user_id: int, max_turns: int = 10) -> list[dict]:
    logs = (
        db.query(ChatLog)
        .filter(ChatLog.session_id == session_id, ChatLog.user_id == user_id)
        .order_by(ChatLog.created_at.desc())
        .limit(max_turns * 2)
        .all()
    )
    logs.reverse()
    return [{"role": log.role, "content": log.content} for log in logs]


def retrieve_multi_kb(query: str, kb_ids: list[int], top_k: int = 5, min_score: float = 0.0) -> list[dict]:
    all_results = []
    per_kb = max(2, top_k // len(kb_ids)) if kb_ids else top_k
    for kb_id in kb_ids:
        collection_name = f"kb_{kb_id}"
        results = retrieve(query, collection_name, top_k=per_kb, min_score=min_score)
        for item in results:
            item["kb_id"] = kb_id
        all_results.extend(results)
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results[:top_k]


def filter_sensitive(text: str) -> str:
    for word in SENSITIVE_WORDS:
        text = text.replace(word, "*" * len(word))
    return text


async def execute_tool(query: str, db: Session) -> str | None:
    """检测工具意图并执行"""
    for tool_name, keywords in TOOL_INTENTS.items():
        for kw in keywords:
            if kw in query:
                args = {}
                if tool_name == "query_student":
                    id_match = re.search(r'(\d{8,})', query)
                    name_match = re.search(r'[\u4e00-\u9fa5]{2,4}(?=的|是谁|是谁的|信息)', query)
                    if id_match:
                        args["student_id"] = id_match.group(1)
                    elif name_match:
                        args["name"] = name_match.group(0)
                elif tool_name == "create_leave_request":
                    date_match = re.findall(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', query)
                    if len(date_match) >= 2:
                        args["start_date"] = date_match[0]
                        args["end_date"] = date_match[1]
                    reason_match = re.search(r'(?:因为|由于|因|原因)[：:]?\s*(.+?)(?:。|$)', query)
                    if reason_match:
                        args["reason"] = reason_match.group(1)
                elif tool_name == "get_leave_status":
                    id_match = re.search(r'(\d{8,})', query)
                    if id_match:
                        args["student_id_str"] = id_match.group(1)

                result = await tool_registry.execute(tool_name, args, db)
                if result.get("success"):
                    return json.dumps(result["result"], ensure_ascii=False, indent=2)
                else:
                    return f"工具执行失败：{result.get('error', '未知错误')}"
    return None


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    query = filter_sensitive(body.query)

    user_msg = ChatLog(user_id=user.id, session_id=body.session_id, role="user", content=query)
    db.add(user_msg)
    db.commit()

    history = load_history(db, body.session_id, user.id, max_turns=settings.MAX_CONTEXT_TURNS)
    answer = ""
    sources = []

    # 1. Check refusal rules
    refusal_response = rules_engine.check_refusal(query)
    if refusal_response:
        answer = refusal_response
    else:
        # 2. Check dialogue rules
        rule_response = rules_engine.check_rules(query)
        if rule_response:
            answer = rule_response
        else:
            # 3. Check tool intents
            tool_answer = await execute_tool(query, db)
            if tool_answer:
                answer = tool_answer
            else:
                # 4. Intent recognition
                intent = recognize_intent(query)
                if intent in INTENT_REPLIES:
                    answer = INTENT_REPLIES[intent]
                else:
                    # 5. Question rewriting + RAG
                    rewritten_query = rewrite_question(query, history)
                    kb_ids = body.kb_ids if body.kb_ids else ([body.kb_id] if body.kb_id else [])
                    top_k = body.top_k if body.top_k is not None else settings.TOP_K
                    min_score = body.min_score if body.min_score is not None else settings.MIN_SCORE

                    if kb_ids:
                        retrieved = retrieve_multi_kb(rewritten_query, kb_ids, top_k=top_k, min_score=min_score)
                    else:
                        retrieved = []

                    if not retrieved:
                        answer = FALLBACK_ANSWER
                    else:
                        context_parts = []
                        for i, item in enumerate(retrieved):
                            context_parts.append(f"[{i+1}] {item['content']}")
                            sources.append({
                                "content": item["content"][:200],
                                "doc_id": item.get("doc_id"),
                                "kb_id": item.get("kb_id"),
                                "score": item.get("score", 0),
                            })
                        context = "\n\n".join(context_parts)
                        answer = ""
                        async for chunk in llm_client.chat_stream(rewritten_query, context, history):
                            answer += chunk

    # Truncate
    if len(answer) > settings.MAX_ANSWER_LENGTH:
        answer = answer[:settings.MAX_ANSWER_LENGTH] + "..."

    # Filter sensitive
    answer = filter_sensitive(answer)

    # Follow-up suggestions
    follow_ups = []
    if sources and len(sources) > 0:
        follow_ups = ["能详细说说吗？", "还有其他相关信息吗？", "这个的适用范围是什么？"]

    # Save
    assistant_msg = ChatLog(user_id=user.id, session_id=body.session_id, role="assistant", content=answer, sources=json.dumps(sources, ensure_ascii=False))
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(session_id=body.session_id, answer=answer, sources=sources, follow_ups=follow_ups)


@router.get("/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    logs = db.query(ChatLog).filter(ChatLog.session_id == session_id, ChatLog.user_id == user.id).order_by(ChatLog.created_at).all()
    return [{"role": log.role, "content": log.content, "sources": json.loads(log.sources) if log.sources else [], "created_at": log.created_at.isoformat()} for log in logs]


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    logs = db.query(ChatLog).filter(ChatLog.session_id == session_id, ChatLog.user_id == user.id).all()
    for log in logs:
        db.delete(log)
    db.commit()
    return {"detail": "已删除"}
