from pydantic import BaseModel
from datetime import datetime


# ---- Auth ----
class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Knowledge Base ----
class KBCreate(BaseModel):
    name: str
    description: str = ""
    department: str = ""
    owner_name: str = ""


class KBOut(BaseModel):
    id: int
    name: str
    description: str
    department: str = ""
    owner_name: str = ""
    owner_id: int | None
    embedding_model: str = "shibing624/text2vec-base-chinese"
    created_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


# ---- Document ----
class DocOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    status: str
    progress: int = 0
    chunk_count: int
    error_message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Chat ----
class ChatRequest(BaseModel):
    session_id: str
    kb_id: int | None = None
    kb_ids: list[int] = []
    query: str
    top_k: int | None = None
    min_score: float | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[dict] = []
    follow_ups: list[str] = []


# ---- Student / Leave ----
class StudentCreate(BaseModel):
    student_id: str
    name: str
    class_name: str = ""
    phone: str = ""


class LeaveRequestCreate(BaseModel):
    student_id: int
    start_date: str
    end_date: str
    reason: str
