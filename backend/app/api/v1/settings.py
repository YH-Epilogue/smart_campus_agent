from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ...core.config import settings
from ..deps import get_current_user

router = APIRouter(prefix="/settings", tags=["系统配置"])

# 快捷提问模板
QUICK_QUESTIONS = [
    "知识库中有多少份文档？",
    "如何创建知识库？",
    "支持哪些文件格式？",
    "如何上传文档？",
    "系统支持哪些功能？",
]


class SettingsUpdate(BaseModel):
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    top_k: int | None = None
    min_score: float | None = None
    max_context_turns: int | None = None
    max_answer_length: int | None = None
    llm_model: str | None = None
    embedding_model: str | None = None


class SettingsOut(BaseModel):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
    max_context_turns: int
    max_answer_length: int
    llm_model: str
    llm_provider: str
    embedding_model: str
    embedding_models: list[str]
    quick_questions: list[str]


EMBEDDING_MODELS = [
    "shibing624/text2vec-base-chinese",
    "BAAI/bge-small-zh-v1.5",
    "BAAI/bge-base-zh-v1.5",
    "BAAI/bge-large-zh-v1.5",
]


@router.get("/", response_model=SettingsOut)
def get_settings(user=Depends(get_current_user)):
    return SettingsOut(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        top_k=settings.TOP_K,
        min_score=settings.MIN_SCORE,
        max_context_turns=settings.MAX_CONTEXT_TURNS,
        max_answer_length=settings.MAX_ANSWER_LENGTH,
        llm_model=settings.LLM_MODEL,
        llm_provider=settings.LLM_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_models=EMBEDDING_MODELS,
        quick_questions=QUICK_QUESTIONS,
    )


@router.put("/", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, user=Depends(get_current_user)):
    if body.chunk_size is not None:
        settings.CHUNK_SIZE = body.chunk_size
    if body.chunk_overlap is not None:
        settings.CHUNK_OVERLAP = body.chunk_overlap
    if body.top_k is not None:
        settings.TOP_K = body.top_k
    if body.min_score is not None:
        settings.MIN_SCORE = body.min_score
    if body.max_context_turns is not None:
        settings.MAX_CONTEXT_TURNS = body.max_context_turns
    if body.max_answer_length is not None:
        settings.MAX_ANSWER_LENGTH = body.max_answer_length
    if body.llm_model is not None:
        settings.LLM_MODEL = body.llm_model
    if body.embedding_model is not None:
        settings.EMBEDDING_MODEL = body.embedding_model

    return SettingsOut(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        top_k=settings.TOP_K,
        min_score=settings.MIN_SCORE,
        max_context_turns=settings.MAX_CONTEXT_TURNS,
        max_answer_length=settings.MAX_ANSWER_LENGTH,
        llm_model=settings.LLM_MODEL,
        llm_provider=settings.LLM_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_models=EMBEDDING_MODELS,
        quick_questions=QUICK_QUESTIONS,
    )
