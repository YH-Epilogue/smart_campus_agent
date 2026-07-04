import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data/sqlite.db"

    # Security
    SECRET_KEY: str = "smart-campus-agent-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # LLM
    LLM_PROVIDER: str = "mock"  # mock / ollama / deepseek / api
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # RAG
    EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    MIN_SCORE: float = 0.3  # 相似度阈值
    MAX_CONTEXT_TURNS: int = 10  # 最大上下文轮数
    MAX_ANSWER_LENGTH: int = 1000  # 最大回答长度（字符）

    # File Storage
    UPLOAD_DIR: str = "./data/storage"
    CHROMA_DIR: str = "./data/chromadb"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Auto-load DeepSeek API key from system environment if not set
if not settings.LLM_API_KEY:
    env_key = os.environ.get("DeepSeek_API_KEY", "")
    if env_key:
        settings.LLM_API_KEY = env_key
        if settings.LLM_PROVIDER == "mock":
            settings.LLM_PROVIDER = "deepseek"
