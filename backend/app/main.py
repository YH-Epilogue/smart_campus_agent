"""
应用入口 — FastAPI 主程序

创建 FastAPI 实例、配置 CORS 中间件、注册所有 API 路由。
通过 lifespan 上下文管理器在启动时初始化数据库。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models.database import init_db
from .api.v1 import auth, kb, doc, chat, logs, settings, users, leave


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库，关闭时无额外清理"""
    # 应用启动
    init_db()
    yield
    # 应用关闭


app = FastAPI(
    title="Smart Campus Agent",
    description="校园智能体后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件配置，允许前端开发服务器跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite 开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各功能模块路由，统一挂载到 /api/v1 前缀下
app.include_router(auth.router, prefix="/api/v1")  # 认证：登录/注册
app.include_router(kb.router, prefix="/api/v1")    # 知识库 CRUD
app.include_router(doc.router, prefix="/api/v1")   # 文档上传/解析/索引
app.include_router(chat.router, prefix="/api/v1")  # AI 对话
app.include_router(logs.router, prefix="/api/v1")  # 对话日志与统计分析
app.include_router(settings.router, prefix="/api/v1")  # 系统设置
app.include_router(users.router, prefix="/api/v1")  # 用户管理
app.include_router(leave.router, prefix="/api/v1")  # 请假管理


@app.get("/")
def root():
    """根路径，返回 API 基本信息与文档入口"""
    return {"message": "Smart Campus Agent API", "docs": "/docs"}
