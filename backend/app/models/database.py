"""
数据库模块 — SQLAlchemy 引擎、会话工厂与 ORM 基类

负责创建数据库引擎、定义会话生成器（供 FastAPI Depends 注入），
以及通过 init_db() 在应用启动时自动建表。
当前使用 SQLite，生产环境可通过修改 DATABASE_URL 切换至 PostgreSQL。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.config import settings

# 创建数据库引擎
# check_same_thread=False：SQLite 允许跨线程共享连接（FastAPI 异步场景必需）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # 设为 True 可打印所有 SQL 语句，调试用
)

# 会话工厂，每次调用 SessionLocal() 返回一个新的数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 模型基类，所有表模型均继承此 Base
Base = declarative_base()


def init_db():
    """
    应用启动时调用，创建所有尚未存在的表。
    必须先 import tables 模块，确保所有 ORM 模型被注册到 Base.metadata。
    """
    from . import tables  # noqa: F401 — 触发模型注册
    Base.metadata.create_all(bind=engine)
