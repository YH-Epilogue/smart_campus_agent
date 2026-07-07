"""
用户管理模块：用户 CRUD 和角色管理

提供以下接口：
- GET  /users/roles    — 获取角色列表（无需权限）
- GET  /users/         — 查询所有用户（仅 admin）
- PUT  /users/{user_id} — 更新用户信息（admin 可改任意用户，普通用户仅改自己）
- DELETE /users/{user_id} — 删除用户（仅 admin，不可删除自己）

角色体系：
- admin：超级管理员，拥有所有权限
- teacher：教师，可管理知识库、文档和审批请假
- student：学生，对话和查看请假记录
- user：普通用户，仅可使用对话功能
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...models.tables import User
from ...models.schemas import UserOut
from ...core.security import hash_password
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/users", tags=["用户管理"])

# 预定义角色及其描述
ROLES = {
    "admin": {"name": "超级管理员", "description": "拥有所有权限"},
    "teacher": {"name": "教师", "description": "可管理知识库、文档和审批请假"},
    "student": {"name": "学生", "description": "对话和查看请假记录"},
    "user": {"name": "普通用户", "description": "仅可使用对话功能"},
}


class UserUpdate(BaseModel):
    """用户更新请求体（所有字段可选）"""
    username: str | None = None
    password: str | None = None
    role: str | None = None


@router.get("/roles")
def list_roles():
    """获取角色列表

    - 无需登录即可访问
    - 返回角色 ID、名称和描述
    - 用于前端注册/用户管理页面的角色选择下拉框
    """
    return [{"id": k, "name": v["name"], "description": v["description"]} for k, v in ROLES.items()]


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """查询所有用户列表

    - 仅 admin 可访问
    - 返回所有用户的基本信息（不含密码）
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    users = db.query(User).all()
    return users


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """更新用户信息

    - admin 可更新任意用户
    - 普通用户仅可更新自己的信息
    - 修改用户名时检查是否与已有用户名冲突
    - 修改密码时自动进行哈希处理
    - 仅 admin 可修改用户角色
    - 角色修改时验证角色值是否合法
    """
    # 权限检查：admin 可操作任意用户，普通用户仅操作自己
    if user.role != "admin" and user.id != user_id:
        raise HTTPException(status_code=403, detail="无权限")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 更新用户名（检查唯一性）
    if body.username is not None:
        existing = db.query(User).filter(User.username == body.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        target.username = body.username
    # 更新密码（哈希处理）
    if body.password is not None:
        target.hashed_password = hash_password(body.password)
    # 更新角色（仅 admin 可操作）
    if body.role is not None and user.role == "admin":
        if body.role not in ROLES:
            raise HTTPException(status_code=400, detail="无效的角色")
        target.role = body.role
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """删除用户

    - 仅 admin 可执行
    - 不允许删除自己（防止管理员误删导致无法登录）
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    # 禁止删除自己
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(target)
    db.commit()
    return {"detail": "已删除"}
