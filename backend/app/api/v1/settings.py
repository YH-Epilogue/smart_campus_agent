"""
系统配置模块：管理 RAG 和 LLM 的运行时参数

提供以下接口：
- GET  /settings/ — 获取当前系统配置
- PUT  /settings/ — 更新系统配置（仅 admin）

可配置项：
- chunk_size / chunk_overlap：文档切分参数
- top_k / min_score：检索参数
- max_context_turns / max_answer_length：对话参数
- llm_model / embedding_model：模型选择
- max_upload_size_mb：上传文件大小限制

注意：配置修改立即生效，无需重启服务。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ...core.config import settings
from ..deps import get_current_user

router = APIRouter(prefix="/settings", tags=["系统配置"])

# 快捷提问模板（前端展示用）
QUICK_QUESTIONS = [
    "知识库中有多少份文档？",
    "如何创建知识库？",
    "支持哪些文件格式？",
    "如何上传文档？",
    "系统支持哪些功能？",
]


class SettingsUpdate(BaseModel):
    """配置更新请求体（所有字段可选，仅更新传入的非 None 字段）"""
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    top_k: int | None = None
    min_score: float | None = None
    max_context_turns: int | None = None
    max_answer_length: int | None = None
    llm_model: str | None = None
    embedding_model: str | None = None
    max_upload_size_mb: int | None = None


class SettingsOut(BaseModel):
    """配置响应体（包含所有配置项和可用选项列表）"""
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
    max_context_turns: int
    max_answer_length: int
    llm_model: str
    llm_provider: str
    embedding_model: str
    embedding_models: list[str]  # 可选的 embedding 模型列表
    max_upload_size_mb: int
    quick_questions: list[str]  # 快捷提问模板


# 可选的 embedding 模型列表
EMBEDDING_MODELS = [
    "shibing624/text2vec-base-chinese",
    "BAAI/bge-small-zh-v1.5",
    "BAAI/bge-base-zh-v1.5",
    "BAAI/bge-large-zh-v1.5",
]


@router.get("/", response_model=SettingsOut)
def get_settings(user=Depends(get_current_user)):
    """获取当前系统配置

    - 所有已登录用户均可读取
    - 返回当前生效的配置值和可选模型列表
    - 不包含敏感信息（API Key 等）
    """
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
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        quick_questions=QUICK_QUESTIONS,
    )


@router.put("/", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, user=Depends(get_current_user)):
    """更新系统配置

    - 仅 admin 角色可修改
    - 仅更新传入的非 None 字段（部分更新）
    - 修改立即生效，无需重启服务
    - 注意：配置存储在内存中，重启服务后恢复默认值
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可修改系统配置")
    # 逐个字段更新（仅更新传入的非 None 值）
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
    if body.max_upload_size_mb is not None:
        settings.MAX_UPLOAD_SIZE_MB = body.max_upload_size_mb

    # 返回更新后的完整配置
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
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        quick_questions=QUICK_QUESTIONS,
    )
