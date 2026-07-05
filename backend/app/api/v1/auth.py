import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.tables import User
from ...models.schemas import UserCreate, UserLogin, TokenResponse, UserOut
from ...core.security import hash_password, verify_password, create_access_token
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["认证"])

# 登录失败记录 {username: (fail_count, last_fail_time)}
login_failures: dict[str, tuple[int, float]] = {}
MAX_FAIL_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5分钟锁定


@router.post("/register", response_model=UserOut)
def register(body: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=body.username, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, db: Session = Depends(get_db)):
    username = body.username

    # Check if account is locked
    if username in login_failures:
        fail_count, last_fail_time = login_failures[username]
        if fail_count >= MAX_FAIL_ATTEMPTS:
            elapsed = time.time() - last_fail_time
            if elapsed < LOCKOUT_SECONDS:
                remaining = int(LOCKOUT_SECONDS - elapsed)
                raise HTTPException(
                    status_code=429,
                    detail=f"登录失败次数过多，请 {remaining} 秒后重试"
                )
            else:
                # Lockout expired, reset
                login_failures.pop(username)

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        # Record failure
        fail_count = login_failures.get(username, (0, 0))[0] + 1
        login_failures[username] = (fail_count, time.time())
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Login success, clear failures
    login_failures.pop(username, None)

    token = create_access_token(data={"sub": str(user.id), "role": user.role, "username": user.username})
    return TokenResponse(access_token=token, role=user.role)
