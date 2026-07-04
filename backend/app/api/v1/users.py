from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...models.tables import User
from ...models.schemas import UserOut
from ...core.security import hash_password
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/users", tags=["用户管理"])


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    users = db.query(User).all()
    return users


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "admin" and user.id != user_id:
        raise HTTPException(status_code=403, detail="无权限")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.username is not None:
        existing = db.query(User).filter(User.username == body.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        target.username = body.username
    if body.password is not None:
        target.hashed_password = hash_password(body.password)
    if body.role is not None and user.role == "admin":
        target.role = body.role
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(target)
    db.commit()
    return {"detail": "已删除"}
