"""
数据表模型 — 所有 ORM 模型定义

定义系统中所有数据库表的结构，包括：
- User: 系统用户（支持 student/teacher/admin 三种角色）
- KnowledgeBase: 知识库，支持按部门/创建者分类
- Document: 文档记录，关联知识库，跟踪解析/索引进度
- Student: 学生信息表（独立于 User 的业务数据）
- LeaveRequest: 请假申请，关联学生
- ChatLog: 对话日志，支持 RAG 检索结果追溯
- Memory: Agent 长期记忆，用于跨会话上下文延续
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """系统用户表，存储登录凭证与角色信息"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)  # PBKDF2 哈希，格式: salt$hash
    role = Column(String(20), default="student")  # student / teacher / admin
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chat_logs = relationship("ChatLog", back_populates="user")


class KnowledgeBase(Base):
    """知识库表，存储 RAG 知识库元信息"""
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    department = Column(String(100), default="")  # 所属部门/院系
    owner_name = Column(String(50), default="")  # 创建者姓名（冗余字段，方便展示）
    owner_id = Column(Integer, ForeignKey("users.id"))  # 创建者用户 ID
    embedding_model = Column(String(100), default="shibing624/text2vec-base-chinese")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="knowledge_base")


class Document(Base):
    """文档表，记录上传文件的解析与索引进度"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 服务器存储路径
    # 处理状态: uploading -> parsing -> indexing -> ready / error
    status = Column(String(20), default="uploading")
    progress = Column(Integer, default=0)  # 处理进度 0-100
    chunk_count = Column(Integer, default=0)  # 向量化后的分块数
    error_message = Column(Text, default="")  # 处理失败时的错误信息
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


class Student(Base):
    """学生信息表，存储学籍相关数据（独立于 User 登录表）"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True, nullable=False)  # 学号
    name = Column(String(50), nullable=False)
    class_name = Column(String(50), default="")  # 班级
    phone = Column(String(20), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    leave_requests = relationship("LeaveRequest", back_populates="student")


class LeaveRequest(Base):
    """请假申请表，记录学生的请假信息与审批状态"""
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    start_date = Column(String(20), nullable=False)  # 请假开始日期
    end_date = Column(String(20), nullable=False)  # 请假结束日期
    reason = Column(Text, nullable=False)
    # 审批状态: pending（待审批）/ approved（已通过）/ rejected（已驳回）
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("Student", back_populates="leave_requests")


class ChatLog(Base):
    """对话日志表，记录用户与 AI 的每一轮交互"""
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(50), index=True, nullable=False)  # 会话 ID，区分不同对话
    role = Column(String(10), nullable=False)  # user（用户输入）/ assistant（AI 回复）
    content = Column(Text, nullable=False)  # 对话内容
    sources = Column(Text, default="")  # JSON 字符串，存储 RAG 检索到的文档片段
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_logs")


class Memory(Base):
    """Agent 长期记忆表，用于跨会话保持用户偏好与事实"""
    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 记忆类型: fact（事实）/ preference（偏好）/ summary（摘要）
    memory_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)  # 记忆内容
    source_session = Column(String(50), default="")  # 来源会话 ID
    importance = Column(Integer, default=5)  # 重要度 1-10，用于记忆检索排序
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime, default=lambda: datetime.now(timezone.utc))
