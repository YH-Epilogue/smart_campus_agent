"""
安全模块 — 密码哈希与 JWT Token 管理

提供密码的 PBKDF2 哈希/校验，以及 JWT access token 的签发与解码。
存储格式: salt$hash（salt 为 16 字节随机十六进制串）。
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from .config import settings


def hash_password(password: str) -> str:
    """
    对明文密码进行 PBKDF2-SHA256 哈希。
    返回格式: "{salt}${hashed_hex}"，盐值随机生成以防止彩虹表攻击。
    迭代次数 100000 次，在安全性和性能之间取得平衡。
    """
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码与存储的哈希值是否匹配。
    从存储格式中提取 salt，用相同参数重新计算哈希后逐字节比较。
    """
    try:
        salt, stored_hash = hashed_password.split("$")
        check_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), 100000)
        return check_hash.hex() == stored_hash
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    签发 JWT access token。
    data 中至少包含 {"sub": user_id}；可选传入 expires_delta 自定义过期时间，
    默认使用配置中的 ACCESS_TOKEN_EXPIRE_MINUTES。
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    解码并验证 JWT token，返回 payload 字典。
    任何验证失败（过期、签名错误等）均返回 None，由调用方决定如何处理。
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
