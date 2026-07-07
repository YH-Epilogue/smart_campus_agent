"""
数据传输对象 (DTO) — Pydantic 请求/响应模型

定义所有 API 接口的输入验证与输出序列化模型。
模型按功能分组：认证、知识库、文档、对话、学生/请假。
使用 from_attributes=True 支持直接从 ORM 模型转换。
"""
from pydantic import BaseModel
from datetime import datetime


# ---- 认证相关 ----

class UserCreate(BaseModel):
    """用户注册请求体"""
    username: str
    password: str


class UserLogin(BaseModel):
    """用户登录请求体"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """登录成功后的 Token 响应体"""
    access_token: str
    token_type: str = "bearer"
    role: str  # 用户角色，前端据此决定路由跳转


class UserOut(BaseModel):
    """用户信息输出（不含密码）"""
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # 支持 ORM 对象直接序列化


# ---- 知识库相关 ----

class KBCreate(BaseModel):
    """创建知识库请求体"""
    name: str
    description: str = ""
    department: str = ""  # 所属部门
    owner_name: str = ""  # 创建者姓名


class KBOut(BaseModel):
    """知识库详情输出"""
    id: int
    name: str
    description: str
    department: str = ""
    owner_name: str = ""
    owner_id: int | None  # 创建者 ID，用于权限判断
    embedding_model: str = "shibing624/text2vec-base-chinese"
    created_at: datetime
    document_count: int = 0  # 关联文档数量（由接口动态计算）

    class Config:
        from_attributes = True


# ---- 文档相关 ----

class DocOut(BaseModel):
    """文档信息输出"""
    id: int
    kb_id: int  # 所属知识库 ID
    filename: str
    status: str  # uploading/parsing/indexing/ready/error
    progress: int = 0  # 处理进度 0-100
    chunk_count: int  # 向量化后的分块数
    error_message: str  # 处理失败时的错误信息
    created_at: datetime

    class Config:
        from_attributes = True


# ---- 对话相关 ----

class ChatRequest(BaseModel):
    """对话请求体，支持单知识库或多知识库检索"""
    session_id: str  # 会话 ID，同一会话内保持上下文连贯
    kb_id: int | None = None  # 单知识库 ID（旧版兼容）
    kb_ids: list[int] = []  # 多知识库 ID 列表（新版推荐）
    query: str  # 用户提问
    top_k: int | None = None  # 自定义检索数量
    min_score: float | None = None  # 自定义相似度阈值


class ChatResponse(BaseModel):
    """对话响应体"""
    session_id: str
    answer: str  # AI 生成的回答
    sources: list[dict] = []  # RAG 检索到的文档片段
    follow_ups: list[str] = []  # 建议的追问


# ---- 学生 / 请假相关 ----

class StudentCreate(BaseModel):
    """创建学生信息请求体"""
    student_id: str  # 学号
    name: str
    class_name: str = ""  # 班级
    phone: str = ""


class LeaveRequestCreate(BaseModel):
    """创建请假申请请求体"""
    student_id: int  # 学生表主键 ID
    start_date: str  # 开始日期
    end_date: str  # 结束日期
    reason: str  # 请假原因
