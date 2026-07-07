"""
Agent Memory: 长期记忆系统模块

本模块实现了灵犀智能体的用户级长期记忆功能，让智能体能够：
1. 从对话中自动提取关键事实（学生信息、偏好表达等）并持久化存储
2. 在后续对话中检索相关记忆，注入到 LLM 上下文中实现个性化回答
3. 在会话结束时生成简要摘要，便于跨会话记忆

记忆类型：
- fact: 用户陈述的事实信息（如"我是张三"、"我的学号是2023001"）
- preference: 用户偏好表达（如"我喜欢简洁回答"、"以后请用中文"）
- summary: 会话摘要（自动生成，记录用户问了哪些问题）

存储后端使用 SQLAlchemy + Memory 表，按 user_id 隔离，支持 importance 优先级排序。
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.tables import Memory, ChatLog


class AgentMemory:
    """Agent 记忆管理器

    负责记忆的提取、存储、检索和会话摘要生成。
    记忆按 user_id 隔离，每个用户独立维护记忆库。
    """

    def __init__(self):
        # 触发记忆提取的关键词模式
        # 当用户输入包含这些模式时，认为用户在陈述个人信息，应提取为记忆
        self._memory_keywords = [
            "我是", "我的", "我叫", "我喜欢", "我需要", "我的学号",
            "我们班", "我们学校", "我在", "我想", "我负责",
        ]

    def extract_and_store(self, query: str, answer: str, user_id: int, session_id: str, db: Session):
        """从对话中提取关键信息并存储为长期记忆

        提取策略（基于关键词匹配，非 LLM 推理）：
        1. 用户消息包含个人信息关键词 → 提取为 fact（重要性 7）
        2. 工具返回学生信息或请假成功 → 提取为 fact（重要性 6）
        3. 用户表达偏好 → 提取为 preference（重要性 8，最高优先级）

        去重机制：存储前检查内容是否已存在，避免重复记忆。

        Args:
            query: 用户原始输入
            answer: 智能体回复（含工具调用结果）
            user_id: 当前用户 ID
            session_id: 当前会话 ID
            db: 数据库会话
        """
        memories_to_store = []

        # 策略1：从用户消息中提取个人信息事实
        for pattern in self._memory_keywords:
            if pattern in query:
                memories_to_store.append(("fact", query, 7))
                break  # 一条消息只提取一次，避免重复

        # 策略2：从工具返回结果中提取操作事实
        if "学生信息" in answer or "请假申请已提交" in answer:
            memories_to_store.append(("fact", f"用户查询了：{query[:100]}，结果：{answer[:200]}", 6))

        # 策略3：检测用户偏好表达
        preference_patterns = ["我喜欢", "我习惯", "以后都", "以后请", "请用"]
        for pattern in preference_patterns:
            if pattern in query:
                memories_to_store.append(("preference", query[:200], 8))
                break

        # 存储新记忆（去重检查）
        for mem_type, content, importance in memories_to_store:
            # 检查是否已有完全相同的记忆内容
            existing = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.content == content,
            ).first()
            if not existing:
                mem = Memory(
                    user_id=user_id,
                    memory_type=mem_type,
                    content=content[:500],  # 截断过长内容
                    source_session=session_id,
                    importance=importance,
                )
                db.add(mem)

        if memories_to_store:
            db.commit()

    def recall(self, query: str, user_id: int, db: Session, top_k: int = 3) -> str:
        """检索与当前查询相关的记忆，注入到 LLM 上下文

        检索策略：
        1. 先按重要性降序、最后访问时间降序取出该用户最多 20 条记忆
        2. 对每条记忆计算与查询的字符重叠度（简单但有效的相关性度量）
        3. 综合得分 = importance + 字符重叠数，取 top_k 条返回

        返回格式为 Markdown 列表，每条标注类型（用户偏好/历史记录）。
        同时更新被检索记忆的 last_accessed 时间（LRU 效果）。

        Args:
            query: 当前用户查询
            user_id: 当前用户 ID
            db: 数据库会话
            top_k: 返回的记忆条数（默认 3）

        Returns:
            格式化的记忆文本，空字符串表示无记忆
        """
        memories = (
            db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(Memory.importance.desc(), Memory.last_accessed.desc())
            .limit(20)
            .all()
        )

        if not memories:
            return ""

        # 计算每条记忆与查询的相关性得分
        scored = []
        query_words = set(query)  # 按字符切分（中文无空格分词，字符级匹配足够）
        for mem in memories:
            content_words = set(mem.content)
            # 字符重叠度：查询与记忆内容共有多少个不同字符
            overlap = len(query_words & content_words)
            # 综合得分 = 重要性权重 + 相关性
            score = mem.importance + overlap
            scored.append((score, mem))

        # 按得分降序排列，取前 top_k 条
        scored.sort(key=lambda x: x[0], reverse=True)
        relevant = scored[:top_k]

        lines = []
        for _, mem in relevant:
            # 根据记忆类型添加前缀标签
            prefix = "用户偏好" if mem.memory_type == "preference" else "历史记录"
            lines.append(f"- [{prefix}] {mem.content[:150]}")
            # 更新最后访问时间，实现 LRU 效果（最近使用的记忆更容易被检索到）
            mem.last_accessed = datetime.now(timezone.utc)

        db.commit()
        return "\n".join(lines)

    def summarize_session(self, session_id: str, user_id: int, db: Session):
        """生成会话摘要并存储为记忆

        简单版摘要策略：提取会话中的第一条用户消息和问题总数。
        当会话消息少于 4 条时跳过（不值得摘要）。

        摘要记忆的 importance=4（低于事实和偏好），确保不干扰直接相关记忆。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            db: 数据库会话
        """
        logs = (
            db.query(ChatLog)
            .filter(ChatLog.session_id == session_id, ChatLog.user_id == user_id)
            .order_by(ChatLog.created_at)
            .all()
        )
        # 消息太少不生成摘要
        if len(logs) < 4:
            return

        # 提取所有用户消息
        user_msgs = [l for l in logs if l.role == "user"]
        if len(user_msgs) >= 2:
            summary = f"会话摘要：用户问了「{user_msgs[0].content[:80]}」等 {len(user_msgs)} 个问题"
            # 检查是否已有该会话的摘要（避免重复存储）
            existing = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.memory_type == "summary",
                Memory.source_session == session_id,
            ).first()
            if not existing:
                mem = Memory(
                    user_id=user_id,
                    memory_type="summary",
                    content=summary[:500],
                    source_session=session_id,
                    importance=4,
                )
                db.add(mem)
                db.commit()


# 模块级单例，供整个应用共享同一个记忆管理器实例
agent_memory = AgentMemory()
