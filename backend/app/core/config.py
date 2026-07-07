"""
配置模块 — 全局应用配置

使用 pydantic-settings 管理所有配置项，支持 .env 文件和环境变量覆盖。
所有配置在模块加载时通过 Settings() 单例化，通过 settings 变量全局访问。
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用全局配置类，涵盖数据库、安全、LLM、RAG、文件存储等所有设置项"""

    # ---- 数据库 ----
    # SQLite 连接字符串，生产环境可替换为 PostgreSQL/MySQL
    DATABASE_URL: str = "sqlite:///./data/sqlite.db"

    # ---- 安全 / JWT ----
    SECRET_KEY: str = "smart-campus-agent-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Token 有效期（分钟）
    ALGORITHM: str = "HS256"  # JWT 签名算法

    # ---- 大语言模型 (LLM) ----
    LLM_PROVIDER: str = "mock"  # 提供商类型: mock / ollama / deepseek / api
    LLM_API_KEY: str = ""  # API 密钥，优先从环境变量 DeepSeek_API_KEY 读取
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # ---- RAG（检索增强生成） ----
    EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"  # 向量化模型
    CHUNK_SIZE: int = 500  # 文档分块大小（字符数）
    CHUNK_OVERLAP: int = 50  # 分块重叠区域，保证上下文连贯
    TOP_K: int = 5  # 检索返回的最相关文档片段数
    MIN_SCORE: float = 0.3  # 相似度阈值，低于此值的片段被丢弃
    MAX_CONTEXT_TURNS: int = 10  # 历史对话最大上下文轮数
    MAX_ANSWER_LENGTH: int = 1000  # LLM 生成回答的最大长度（字符）
    MAX_UPLOAD_SIZE_MB: int = 50  # 单文件上传大小上限（MB）

    # ---- 文件存储 ----
    UPLOAD_DIR: str = "./data/storage"  # 用户上传文件的本地存储目录
    CHROMA_DIR: str = "./data/chromadb"  # ChromaDB 向量数据库存储目录

    class Config:
        env_file = ".env"  # 自动读取项目根目录的 .env 文件
        env_file_encoding = "utf-8"


# 全局配置单例，整个应用通过 from ..config import settings 引用
settings = Settings()

# 如果 .env 中未配置 LLM_API_KEY，则尝试从系统环境变量 DeepSeek_API_KEY 读取
if not settings.LLM_API_KEY:
    env_key = os.environ.get("DeepSeek_API_KEY", "")
    if env_key:
        settings.LLM_API_KEY = env_key
        # 自动将 LLM_PROVIDER 切换为 deepseek（免去手动改 .env）
        if settings.LLM_PROVIDER == "mock":
            settings.LLM_PROVIDER = "deepseek"
