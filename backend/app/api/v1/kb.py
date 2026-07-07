"""
知识库管理模块：知识库的增删改查与克隆

提供以下接口：
- GET /kb/        — 查询知识库列表（带筛选、分页、文档计数）
- POST /kb/       — 创建知识库
- PUT /kb/{id}    — 更新知识库信息
- DELETE /kb/{id} — 删除知识库及其关联文档
- POST /kb/{id}/clone — 克隆知识库（复制配置和文档记录）

权限规则：
    - admin/teacher：可操作所有知识库
- 普通用户：只能操作自己创建的知识库
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...models.tables import KnowledgeBase, Document, User
from ...models.schemas import KBCreate, KBOut
from ...core.cache import cache
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/kb", tags=["知识库"])


def check_kb_permission(user: User):
    """知识库操作权限检查

    仅 admin、kb_admin、teacher 角色可执行知识库的增删改操作。
    普通用户/student 角色无法调用创建/更新/删除接口。
    """
    if user.role not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="无权限操作知识库")


class KBUpdate(BaseModel):
    """知识库更新请求体（所有字段可选，仅更新传入的字段）"""
    name: str | None = None
    description: str | None = None
    department: str | None = None
    owner_name: str | None = None
    embedding_model: str | None = None


@router.get("/", response_model=list[KBOut])
def list_kbs(
    name: str = None,
    department: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """查询知识库列表

    - teacher/admin：可查看所有知识库
    - 普通用户：只看自己创建的知识库（owner_id 过滤）
    - 支持按名称、部门、创建时间范围筛选
    - 每个知识库附带关联文档数量
    """
    query = db.query(KnowledgeBase)
    # 可见性控制：普通用户只看自己的，老师和管理员看全部
    if user.role not in ("teacher", "admin"):
        query = query.filter(KnowledgeBase.owner_id == user.id)
    if name:
        query = query.filter(KnowledgeBase.name.contains(name))
    if department:
        query = query.filter(KnowledgeBase.department == department)
    if start_date:
        query = query.filter(KnowledgeBase.created_at >= start_date)
    if end_date:
        query = query.filter(KnowledgeBase.created_at <= end_date)

    kbs = query.all()
    # 为每个知识库统计关联文档数
    result = []
    for kb in kbs:
        doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
        kb_out = KBOut.model_validate(kb)
        kb_out.document_count = doc_count
        result.append(kb_out)

    return result


@router.post("/", response_model=KBOut)
def create_kb(body: KBCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """创建知识库

    - 需要 admin/teacher 权限
    - owner_id 设置为当前用户的 ID
    - owner_name 默认取当前用户名
    - 创建后清除该用户的知识库列表缓存
    """
    check_kb_permission(user)
    kb = KnowledgeBase(
        name=body.name,
        description=body.description,
        department=body.department,
        owner_name=body.owner_name or user.username,
        owner_id=user.id,
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    cache.delete(f"kb_list_{user.id}")
    return KBOut.model_validate(kb)


@router.put("/{kb_id}", response_model=KBOut)
def update_kb(kb_id: int, body: KBUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """更新知识库信息

    - 需要 admin/teacher 权限
    - 非 admin/teacher 的用户只能更新自己的知识库
    - 仅更新传入的非 None 字段（部分更新）
    - 更新后清除缓存并返回最新的文档计数
    """
    check_kb_permission(user)
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # 非管理员/教师只能操作自己的知识库
    if user.role not in ("teacher", "admin") and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限操作该知识库")
    # 仅更新传入的字段
    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    if body.department is not None:
        kb.department = body.department
    if body.owner_name is not None:
        kb.owner_name = body.owner_name
    if body.embedding_model is not None:
        kb.embedding_model = body.embedding_model
    db.commit()
    db.refresh(kb)
    cache.delete(f"kb_list_{user.id}")
    doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
    kb_out = KBOut.model_validate(kb)
    kb_out.document_count = doc_count
    return kb_out


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """删除知识库

    - 需要 admin/teacher 权限
    - 非 admin/teacher 的用户只能删除自己的知识库
    - 级联删除：先删除关联的所有文档记录，再删除知识库本身
    - 注意：仅删除数据库记录，不会清理 ChromaDB 中的向量数据
    - 删除后清除缓存
    """
    check_kb_permission(user)
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # admin 和 teacher 可删除所有知识库，普通用户只能删除自己的
    if user.role == "student" and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限删除该知识库")

    # 先删除关联文档记录
    docs = db.query(Document).filter(Document.kb_id == kb_id).all()
    for doc in docs:
        db.delete(doc)

    db.delete(kb)
    db.commit()
    cache.delete(f"kb_list_{user.id}")
    return {"detail": "已删除"}


@router.post("/{kb_id}/clone", response_model=KBOut)
def clone_kb(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """克隆知识库：复制配置和文档记录

    - 需要 admin/teacher 权限
    - 创建新知识库，名称加 "(副本)" 后缀
    - 复制源知识库的文档记录（filename、file_path、status、chunk_count）
    - 注意：不复制 ChromaDB 中的向量数据，需重新向量化
    - 新知识库的 owner_id 设置为当前用户
    """
    check_kb_permission(user)
    source_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not source_kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # admin 和 teacher 可克隆所有知识库，普通用户只能克隆自己的
    if user.role == "student" and source_kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限克隆该知识库")

    # 创建新知识库
    new_kb = KnowledgeBase(
        name=f"{source_kb.name} (副本)",
        description=source_kb.description,
        owner_id=user.id,
    )
    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)

    # 复制文档记录（仅数据库记录，不含向量数据）
    source_docs = db.query(Document).filter(Document.kb_id == kb_id).all()
    for doc in source_docs:
        new_doc = Document(
            kb_id=new_kb.id,
            filename=doc.filename,
            file_path=doc.file_path,
            status=doc.status,
            chunk_count=doc.chunk_count,
        )
        db.add(new_doc)
    db.commit()

    # 注：ChromaDB 向量数据不会被复制，需要对新知识库重新执行向量化
    doc_count = db.query(Document).filter(Document.kb_id == new_kb.id).count()
    kb_out = KBOut.model_validate(new_kb)
    kb_out.document_count = doc_count
    cache.delete(f"kb_list_{user.id}")
    return kb_out
