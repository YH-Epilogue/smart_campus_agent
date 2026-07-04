from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...models.tables import KnowledgeBase, Document
from ...models.schemas import KBCreate, KBOut
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/kb", tags=["知识库"])


class KBUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@router.get("/", response_model=list[KBOut])
def list_kbs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    kbs = db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).all()
    result = []
    for kb in kbs:
        doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
        kb_out = KBOut.model_validate(kb)
        kb_out.document_count = doc_count
        result.append(kb_out)
    return result


@router.post("/", response_model=KBOut)
def create_kb(body: KBCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    kb = KnowledgeBase(name=body.name, description=body.description, owner_id=user.id)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KBOut.model_validate(kb)


@router.put("/{kb_id}", response_model=KBOut)
def update_kb(kb_id: int, body: KBUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    db.commit()
    db.refresh(kb)
    doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
    kb_out = KBOut.model_validate(kb)
    kb_out.document_count = doc_count
    return kb_out


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # Delete associated documents first
    docs = db.query(Document).filter(Document.kb_id == kb_id).all()
    for doc in docs:
        db.delete(doc)

    db.delete(kb)
    db.commit()
    return {"detail": "已删除"}


@router.post("/{kb_id}/clone", response_model=KBOut)
def clone_kb(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """克隆知识库：复制配置和文档记录"""
    source_kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id
    ).first()
    if not source_kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # Create new knowledge base
    new_kb = KnowledgeBase(
        name=f"{source_kb.name} (副本)",
        description=source_kb.description,
        owner_id=user.id,
    )
    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)

    # Copy document records
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

    # Note: ChromaDB vectors are not copied (would require re-indexing)
    doc_count = db.query(Document).filter(Document.kb_id == new_kb.id).count()
    kb_out = KBOut.model_validate(new_kb)
    kb_out.document_count = doc_count
    return kb_out
