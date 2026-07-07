"""
依赖注入模块 — FastAPI 公共依赖

提供所有 API 路由共用的依赖项：
- get_db: 数据库会话注入（每个请求一个会话，请求结束自动关闭）
- get_current_user: JWT Token 解析 + 用户身份验证
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..models.database import SessionLocal
from ..models.tables import User
from ..core.security import decode_token

# HTTP Bearer 认证方案，自动从 Authorization 头提取 Token
security = HTTPBearer()


def get_db():
    """
    数据库会话生成器，作为 FastAPI Depends 使用。
    每个请求创建独立会话，请求结束后自动关闭，防止连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    从请求头的 JWT Token 中提取并验证当前用户。
    验证流程: 解码 Token -> 提取 sub (user_id) -> 查询数据库 -> 返回 User 对象。
    任何步骤失败均返回 401，调用方无需重复处理认证逻辑。
    """
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 Token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 无效")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user
