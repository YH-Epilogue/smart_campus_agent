"""
对话模块：基于 ReAct 推理循环的智能问答

提供以下接口：
- POST /chat/           — 发送对话请求（核心问答接口）
- GET  /chat/{session_id} — 获取会话历史
- DELETE /chat/{session_id} — 删除会话

核心流程（POST /chat/）：
1. 敏感词过滤 → 2. 拒绝规则（硬拦截）→ 3. 对话规则（快速回复）
→ 4. 意图识别（简单意图快速回复）→ 5. ReAct 推理循环（知识库检索+工具调用）
→ 6. 兜底（旧关键词匹配）→ 7. 记忆提取 → 8. 保存并返回

ReAct 循环：
Think（LLM 思考）→ Act（调用工具）→ Observe（观察结果）→ 循环直到 LLM 给出最终答案
最多执行 MAX_REACT_STEPS=5 轮。
"""
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
from ...services.memory import agent_memory
from ...core.config import settings
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/chat", tags=["对话"])

# 兜底回复：知识库未命中时使用
FALLBACK_ANSWER = "抱歉，我在知识库中没有找到与您问题相关的信息。请尝试换个方式提问，或者联系管理员获取帮助。"
# 敏感词列表（用于输入输出过滤）
SENSITIVE_WORDS = ["暴力", "色情", "赌博", "毒品"]

# 简单意图的快速回复模板（跳过 LLM 调用，节省延迟）
INTENT_REPLIES = {
    "greeting": "你好！我是灵犀（Smart Campus Agent），有什么可以帮你的吗？",
    "help": "灵犀功能：\n1. 知识库问答 - 基于上传的文档回答问题\n2. 多轮对话 - 支持上下文追问\n3. 学生查询 - 查询学生信息\n4. 请假管理 - 提交和查询请假申请\n5. 文件分析 - 上传文件后可进行总结、问答",
    "knowledge_base": "知识库管理功能位于左侧导航栏底部的「知识库管理」页面。",
    "document": "文档管理功能位于左侧导航栏底部的「文档管理」页面。",
    "system": "灵犀（Smart Campus Agent）v1.0 — 校园智能助手",
}

MAX_REACT_STEPS = 5  # ReAct 循环最大步数


def load_history(db: Session, session_id: str, user_id: int, max_turns: int = 10) -> list[dict]:
    """加载会话历史记录

    - 按时间倒序查询最近 max_turns*2 条消息（用户+助手各一条为一轮）
    - 反转为时间正序返回
    - 返回格式：[{"role": "user"/"assistant", "content": "..."}]
    """
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
    """多知识库联合检索

    - 对每个知识库分别检索，每个知识库分到 top_k // len(kb_ids) 个结果（至少 2 个）
    - 合并所有结果后按 score 降序排列，取 top_k 个返回
    - 每个结果附带 kb_id 标识来源知识库
    """
    all_results = []
    per_kb = max(2, top_k // len(kb_ids)) if kb_ids else top_k
    for kb_id in kb_ids:
        collection_name = f"kb_{kb_id}"
        results = retrieve(query, collection_name, top_k=per_kb, min_score=min_score)
        for item in results:
            item["kb_id"] = kb_id
        all_results.extend(results)
    # 按相关性分数降序排列，取 top_k 个
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results[:top_k]


def filter_sensitive(text: str) -> str:
    """敏感词过滤：将匹配的敏感词替换为等长的星号"""
    for word in SENSITIVE_WORDS:
        text = text.replace(word, "*" * len(word))
    return text


def format_tool_result(tool_name: str, result: dict) -> str:
    """将工具执行结果格式化为自然语言

    根据工具类型和返回数据结构，生成人类可读的描述文本。
    支持的工具结果类型：
    - 学生信息查询：显示姓名、学号、班级、电话
    - 请假申请：显示工单号和状态
    - 请假记录列表：逐条显示日期、原因、状态
    """
    if not result.get("success"):
        return f"工具执行失败：{result.get('error', '未知错误')}"
    data = result["result"]
    if isinstance(data, dict):
        # 学生信息
        if "name" in data:
            return f"学生信息：{data['name']}（学号{data.get('student_id', '')}，{data.get('class_name', '')}，电话{data.get('phone', '')}）"
        # 请假申请结果
        if "leave_id" in data:
            return f"请假申请已提交！工单号：{data['leave_id']}，状态：{data.get('status', '')}"
        if "error" in data:
            return data["error"]
        return data.get("message", str(data))
    if isinstance(data, list):
        if not data:
            return "暂无请假记录"
        # 请假记录列表格式化
        lines = [f"- {l.get('start_date', '')} 至 {l.get('end_date', '')} | {l.get('reason', '')} | {l.get('status', '')}" for l in data]
        return "请假记录：\n" + "\n".join(lines)
    return str(data)


async def react_loop(query: str, db: Session, user, history: list[dict], kb_ids: list[int]) -> tuple[str, list[dict]]:
    """ReAct 推理循环：Think → Act → Observe → 直到 LLM 给出最终答案

    流程：
    1. 对用户问题进行改写（多轮对话上下文补全）
    2. 从多个知识库中检索相关文档片段
    3. 构建 system prompt（包含工具描述、记忆、检索上下文）
    4. 进入循环：调用 LLM → 若返回 tool_calls 则执行工具 → 将结果反馈 → 继续循环
    5. 循环终止条件：LLM 不再调用工具（给出最终答案）或达到最大步数

    返回：(最终答案文本, 引用来源列表)
    """
    # 对问题进行改写（补全多轮上下文中的指代）
    rewritten = rewrite_question(query, history)
    top_k = settings.TOP_K
    # 从知识库检索相关文档
    retrieved = retrieve_multi_kb(rewritten, kb_ids, top_k=top_k, min_score=settings.MIN_SCORE) if kb_ids else []

    # 将检索结果格式化为上下文文本
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

    # 构建动态 system prompt（包含可用工具描述和用户记忆）
    tools_desc = "\n".join([
        f"- {t['name']}: {t['description']}"
        for t in tool_registry.get_tool_descriptions()
    ])
    memories = agent_memory.recall(query, user.id, db)
    system_prompt = llm_client.build_system_prompt(tools_desc=tools_desc, memories=memories, context=context)

    # 构建消息列表
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-20:])  # 最近 20 条历史
    messages.append({"role": "user", "content": query})

    # 获取 OpenAI 格式的工具定义
    tools = tool_registry.get_openai_tools()

    all_sources = list(sources)

    # ReAct 循环
    for step in range(MAX_REACT_STEPS):
        # Think + Act：调用 LLM，可能返回 tool_calls
        response = await llm_client.chat_with_tools(messages, tools)

        # 无 tool_calls → LLM 给出最终答案，退出循环
        if not response["tool_calls"]:
            return response["content"], all_sources

        # 有 tool_calls → 执行工具
        assistant_msg = {"role": "assistant", "content": response["content"] or ""}
        if response["tool_calls"]:
            assistant_msg["tool_calls"] = response["tool_calls"]
        messages.append(assistant_msg)

        # 逐个执行工具调用
        for tc in response["tool_calls"]:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            arguments = func.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}

            # 工具调用权限检查：仅 admin/kb_admin/teacher 可执行工具
            if user and user.role not in ("admin", "kb_admin", "teacher"):
                tool_result = "权限不足，无法执行工具操作"
            else:
                result = await tool_registry.execute(tool_name, arguments, db)
                tool_result = format_tool_result(tool_name, result)

            # 将工具执行结果加入消息列表（Observe 阶段）
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": tool_result,
            })

    # 循环结束，返回最后一条回复
    if messages[-1].get("content"):
        return messages[-1]["content"], all_sources
    return "处理超时，请重新提问", all_sources


async def legacy_tool_match(query: str, db: Session, user) -> str | None:
    """旧版关键词匹配工具（快速通道兜底）

    - 仅 admin/kb_admin/teacher 可用
    - 通过关键词匹配直接调用工具，跳过 LLM 推理
    - 用于 ReAct 循环未命中时的兜底处理
    - 支持：查询学生、提交请假、查看请假状态
    """
    if user and user.role not in ("admin", "kb_admin", "teacher"):
        return None
    # 关键词到工具的映射
    simple_patterns = {
        "query_student": ["查询学生", "学生信息", "查一下", "找一下学生"],
        "create_leave_request": ["帮我请假", "申请请假", "提交请假", "我要请假", "想请假"],
        "get_leave_status": ["请假状态", "请假进度", "请假审核"],
    }
    for tool_name, keywords in simple_patterns.items():
        for kw in keywords:
            if kw in query:
                args = {}
                # 从用户输入中提取参数
                if tool_name == "query_student":
                    # 提取学号或姓名
                    id_match = re.search(r'学号\s*(\d{4,})', query) or re.search(r'(\d{6,})', query)
                    name_match = re.search(r'[\u4e00-\u9fa5]{2,4}(?=的|是谁|是谁的|信息)', query)
                    if id_match:
                        args["student_id"] = id_match.group(1)
                    elif name_match:
                        args["name"] = name_match.group(0)
                elif tool_name == "create_leave_request":
                    # 提取学号
                    id_match = re.search(r'学号\s*(\d{4,})', query) or re.search(r'(\d{6,})', query)
                    if id_match:
                        args["student_id_str"] = id_match.group(1)
                    # 提取日期范围
                    date_match = re.findall(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', query)
                    if len(date_match) >= 2:
                        args["start_date"] = date_match[0]
                        args["end_date"] = date_match[1]
                    # 提取请假原因
                    reason_match = re.search(r'(?:因为|由于|因|原因)[：:]?\s*(.+?)(?:。|$)', query)
                    if reason_match:
                        args["reason"] = reason_match.group(1)
                    if "student_id_str" not in args:
                        return "请提供学号，例如：帮我请假 学号2023001 2024-01-01 到 2024-01-05"
                elif tool_name == "get_leave_status":
                    id_match = re.search(r'学号\s*(\d{4,})', query) or re.search(r'(\d{6,})', query)
                    if id_match:
                        args["student_id_str"] = id_match.group(1)

                result = await tool_registry.execute(tool_name, args, db)
                return format_tool_result(tool_name, result)
    return None


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """对话核心接口

    完整处理流程：
    1. 敏感词过滤（输入）
    2. 保存用户消息到数据库
    3. 加载会话历史
    4. 按优先级尝试获取回复：
       a. 拒绝规则（硬拦截，如违规内容）
       b. 对话规则（快速回复，如固定问答）
       c. 意图识别（简单意图直接回复，跳过 LLM）
       d. ReAct 推理循环（知识库检索+工具调用）
       e. 兜底：旧关键词匹配 → 默认提示
    5. 截断过长回复
    6. 敏感词过滤（输出）
    7. 记忆提取（学习用户偏好）
    8. 保存助手回复并返回
    """
    query = filter_sensitive(body.query)

    # 保存用户消息
    user_msg = ChatLog(user_id=user.id, session_id=body.session_id, role="user", content=query)
    db.add(user_msg)
    db.commit()

    # 加载会话历史用于上下文
    history = load_history(db, body.session_id, user.id, max_turns=settings.MAX_CONTEXT_TURNS)
    answer = ""
    sources = []

    # 1. 拒绝规则（硬拦截违规内容）
    refusal_response = rules_engine.check_refusal(query)
    if refusal_response:
        answer = refusal_response
    else:
        # 2. 对话规则（固定问答快速回复）
        rule_response = rules_engine.check_rules(query)
        if rule_response:
            answer = rule_response
        else:
            # 3. 意图识别（短文本才走，避免长文本误判）
            if len(query) < 100:
                intent = recognize_intent(query)
                if intent in INTENT_REPLIES:
                    answer = INTENT_REPLIES[intent]

            # 4. 无快速回复时，进入 ReAct 推理循环
            if not answer:
                kb_ids = body.kb_ids if body.kb_ids else ([body.kb_id] if body.kb_id else [])
                try:
                    answer, sources = await react_loop(query, db, user, history, kb_ids)
                except Exception as e:
                    # ReAct 循环异常时回退到兜底答案
                    answer = f"抱歉，处理过程中遇到了问题：{str(e)[:100]}。请稍后重试。"

                # ReAct 未命中时，尝试旧关键词匹配作为兜底
                if not answer or answer == FALLBACK_ANSWER:
                    legacy_answer = await legacy_tool_match(query, db, user)
                    if legacy_answer:
                        answer = legacy_answer

                if not answer:
                    answer = FALLBACK_ANSWER

    # 截断过长回复
    if len(answer) > settings.MAX_ANSWER_LENGTH:
        answer = answer[:settings.MAX_ANSWER_LENGTH] + "..."

    # 敏感词过滤（输出）
    answer = filter_sensitive(answer)

    # 记忆提取：从对话中学习用户信息用于后续个性化
    agent_memory.extract_and_store(query, answer, user.id, body.session_id, db)

    # 生成推荐追问（有检索来源时才推荐）
    follow_ups = []
    if sources and len(sources) > 0:
        follow_ups = ["能详细说说吗？", "还有其他相关信息吗？", "这个的适用范围是什么？"]

    # 保存助手回复
    assistant_msg = ChatLog(user_id=user.id, session_id=body.session_id, role="assistant", content=answer, sources=json.dumps(sources, ensure_ascii=False))
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(session_id=body.session_id, answer=answer, sources=sources, follow_ups=follow_ups)


@router.get("/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """获取指定会话的历史消息

    - 仅返回当前用户自己的消息（user_id 过滤）
    - 按时间正序排列
    - 每条消息包含角色、内容、引用来源、时间戳
    """
    logs = db.query(ChatLog).filter(ChatLog.session_id == session_id, ChatLog.user_id == user.id).order_by(ChatLog.created_at).all()
    return [{"role": log.role, "content": log.content, "sources": json.loads(log.sources) if log.sources else [], "created_at": log.created_at.isoformat()} for log in logs]


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """删除指定会话的所有消息

    - 仅删除当前用户自己的消息（防止越权删除他人会话）
    """
    logs = db.query(ChatLog).filter(ChatLog.session_id == session_id, ChatLog.user_id == user.id).all()
    for log in logs:
        db.delete(log)
    db.commit()
    return {"detail": "已删除"}
