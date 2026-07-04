import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...models.schemas import ChatRequest, ChatResponse
from ...models.tables import ChatLog
from ...services.llm_client import llm_client
from ...services.rag_engine import retrieve
from ...services.nlu import recognize_intent, rewrite_question
from ...services.rules import rules_engine
from ...core.config import settings
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/chat", tags=["对话"])

# 兜底话术
FALLBACK_ANSWER = "抱歉，我在知识库中没有找到与您问题相关的信息。请尝试换个方式提问，或者联系管理员获取帮助。"

# 敏感词列表（可扩展）
SENSITIVE_WORDS = ["暴力", "色情", "赌博", "毒品"]

# 意图回复
INTENT_REPLIES = {
    "greeting": "你好！我是 Smart Campus Agent，有什么可以帮你的吗？",
    "help": "Smart Campus Agent 功能：\n1. 知识库问答 - 基于上传的文档回答问题\n2. 多轮对话 - 支持上下文追问\n3. 快捷提问 - 点击预设问题快速提问\n\n使用方法：在对话框输入问题即可。",
    "knowledge_base": "知识库管理功能位于左侧导航栏底部的「知识库管理」页面，支持创建、编辑、删除和克隆知识库。",
    "document": "文档管理功能位于左侧导航栏底部的「文档管理」页面，支持上传 PDF、Word、TXT 格式文档。",
    "system": "Smart Campus Agent v0.1.0\n基于 RAG 技术的校园智能问答平台",
}


def load_history(db: Session, session_id: str, user_id: int, max_turns: int = 10) -> list[dict]:
    """加载会话历史"""
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
    """从多个知识库检索，合并结果并按相关度排序"""
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
    """过滤敏感词"""
    for word in SENSITIVE_WORDS:
        text = text.replace(word, "*" * len(word))
    return text


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Filter sensitive words in query
    query = filter_sensitive(body.query)

    # Save user message
    user_msg = ChatLog(
        user_id=user.id,
        session_id=body.session_id,
        role="user",
        content=query,
    )
    db.add(user_msg)
    db.commit()

    # Load conversation history
    history = load_history(db, body.session_id, user.id, max_turns=settings.MAX_CONTEXT_TURNS)

    # Check refusal rules first
    refusal_response = rules_engine.check_refusal(query)
    if refusal_response:
        answer = refusal_response
        sources = []
    else:
        # Check dialogue rules
        rule_response = rules_engine.check_rules(query)
        if rule_response:
            answer = rule_response
            sources = []
        else:
            # Intent recognition
            intent = recognize_intent(query)

            # Check for fixed intent replies
            if intent in INTENT_REPLIES:
                answer = INTENT_REPLIES[intent]
                sources = []
            else:
                # Question rewriting for better retrieval
                rewritten_query = rewrite_question(query, history)

                # Determine which knowledge bases to search
                kb_ids = body.kb_ids if body.kb_ids else ([body.kb_id] if body.kb_id else [])

                # RAG: retrieve from knowledge bases with similarity threshold
                if kb_ids:
                    retrieved = retrieve_multi_kb(rewritten_query, kb_ids, top_k=settings.TOP_K, min_score=settings.MIN_SCORE)
                else:
                    retrieved = []

                # Fallback if no relevant results
                if not retrieved:
                    answer = FALLBACK_ANSWER
                    sources = []
                else:
                    # Build context from retrieved chunks
                    context_parts = []
                    sources = []
                    for i, item in enumerate(retrieved):
                        context_parts.append(f"[{i+1}] {item['content']}")
                        sources.append({
                            "content": item["content"][:200],
                            "doc_id": item.get("doc_id"),
                            "kb_id": item.get("kb_id"),
                            "score": item.get("score", 0),
                        })
                    context = "\n\n".join(context_parts)

                    # Call LLM with context + conversation history
                    answer = ""
                    async for chunk in llm_client.chat_stream(rewritten_query, context, history):
                        answer += chunk

    # Truncate answer if too long
    if len(answer) > settings.MAX_ANSWER_LENGTH:
        answer = answer[:settings.MAX_ANSWER_LENGTH] + "..."

    # Filter sensitive words in answer
    answer = filter_sensitive(answer)

    # Add follow-up suggestions if there are sources
    follow_ups = []
    if sources and len(sources) > 0:
        follow_ups = [
            "能详细说说吗？",
            "还有其他相关信息吗？",
            "这个的适用范围是什么？",
        ]

    # Save assistant message
    assistant_msg = ChatLog(
        user_id=user.id,
        session_id=body.session_id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        session_id=body.session_id,
        answer=answer,
        sources=sources,
        follow_ups=follow_ups,
    )


@router.get("/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    logs = (
        db.query(ChatLog)
        .filter(ChatLog.session_id == session_id, ChatLog.user_id == user.id)
        .order_by(ChatLog.created_at)
        .all()
    )
    return [
        {
            "role": log.role,
            "content": log.content,
            "sources": json.loads(log.sources) if log.sources else [],
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """删除整个会话的所有消息"""
    logs = db.query(ChatLog).filter(
        ChatLog.session_id == session_id, ChatLog.user_id == user.id
    ).all()
    for log in logs:
        db.delete(log)
    db.commit()
    return {"detail": "已删除"}
