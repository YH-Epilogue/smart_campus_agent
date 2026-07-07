"""
认证模块：用户注册与登录

提供以下接口：
- POST /register：用户注册（需提供用户名、密码、角色）
- POST /login：用户登录（返回 JWT Token）

安全机制：
- 登录失败次数限制：最多 5 次，锁定 300 秒
- 密码使用 bcrypt 哈希存储
- Token 中包含用户 ID、角色、用户名信息
"""
import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from ...models.tables import User
from ...models.schemas import UserLogin, TokenResponse, UserOut
from ...core.security import hash_password, verify_password, create_access_token
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["认证"])

# 登录失败记录：{username: (连续失败次数, 最后一次失败时间戳)}
# 用于实现登录频率限制，防止暴力破解
login_failures: dict[str, tuple[int, float]] = {}
MAX_FAIL_ATTEMPTS = 5  # 最大失败次数
LOCKOUT_SECONDS = 300  # 锁定时长（秒）


class SecureUserCreate(BaseModel):
    """注册请求体，包含字段格式校验"""
    username: str
    password: str
    role: str = "student"  # 默认角色为学生

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError("用户名长度需在3-20个字符之间")
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("密码长度至少6个字符")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("student", "teacher", "admin"):
            raise ValueError("角色只能是 student/teacher/admin")
        return v


@router.post("/register", response_model=UserOut)
def register(body: SecureUserCreate, db: Session = Depends(get_db)):
    """用户注册接口

    - 验证用户名是否已存在
    - 密码经 bcrypt 哈希后存储
    - 返回新创建的用户信息
    """
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=body.username, hashed_password=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    """用户登录接口

    - 检查登录失败次数，超限则返回 429（锁定）
    - 验证用户名密码，失败则记录失败次数
    - 成功后清除失败记录，签发 JWT Token
    - Token 中包含 sub(user_id)、role、username 三个字段
    """
    username = body.username

    # 检查是否被锁定
    if username in login_failures:
        fail_count, last_fail_time = login_failures[username]
        if fail_count >= MAX_FAIL_ATTEMPTS:
            elapsed = time.time() - last_fail_time
            if elapsed < LOCKOUT_SECONDS:
                remaining = int(LOCKOUT_SECONDS - elapsed)
                raise HTTPException(status_code=429, detail=f"登录失败次数过多，请 {remaining} 秒后重试")
            else:
                # 锁定时间已过，清除记录
                login_failures.pop(username)

    # 验证用户名密码
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        # 密码错误或用户不存在，累加失败次数
        fail_count = login_failures.get(username, (0, 0))[0] + 1
        login_failures[username] = (fail_count, time.time())
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 登录成功，清除失败记录
    login_failures.pop(username, None)
    # 签发 JWT Token，包含用户 ID、角色、用户名
    token = create_access_token(data={"sub": str(user.id), "role": user.role, "username": user.username})
    return TokenResponse(access_token=token, role=user.role)
