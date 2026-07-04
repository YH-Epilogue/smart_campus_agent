import os
import uuid
import threading
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...models.tables import Document, KnowledgeBase
from ...models.schemas import DocOut
from ...core.config import settings
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/doc", tags=["文档"])


def process_document(doc_id: int, file_path: str, kb_id: int):
    """后台处理文档：解析 -> 切分 -> 向量化"""
    from ...models.database import SessionLocal
    from ...services.rag_engine import parse_document, split_text, embed_and_store

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        doc.status = "parsing"
        doc.progress = 10
        db.commit()

        try:
            # Step 1: Parse document (10% -> 40%)
            doc.progress = 20
            db.commit()
            text = parse_document(file_path)
            doc.progress = 40
            db.commit()

            # Step 2: Split into chunks (40% -> 60%)
            chunks = split_text(
                text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            doc.progress = 60
            db.commit()

            if not chunks:
                doc.status = "error"
                doc.error_message = "文档内容为空"
                db.commit()
                return

            # Step 3: Embed and store (60% -> 95%)
            doc.status = "indexing"
            doc.progress = 70
            db.commit()
            collection_name = f"kb_{kb_id}"
            chunk_count = embed_and_store(chunks, kb_id, doc_id, collection_name)

            # Done (100%)
            doc.status = "ready"
            doc.progress = 100
            doc.chunk_count = chunk_count
            db.commit()

        except Exception as e:
            doc.status = "error"
            doc.progress = 0
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocOut)
async def upload_doc(
    kb_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        kb_id=kb_id,
        filename=file.filename,
        file_path=file_path,
        status="uploading",
        progress=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Start background processing (non-blocking)
    thread = threading.Thread(target=process_document, args=(doc.id, file_path, kb_id))
    thread.daemon = True
    thread.start()

    return DocOut.model_validate(doc)


@router.get("/{kb_id}", response_model=list[DocOut])
def list_docs(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    docs = db.query(Document).filter(Document.kb_id == kb_id).all()
    return [DocOut.model_validate(d) for d in docs]


@router.delete("/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # Delete vectors from ChromaDB
    from ...services.rag_engine import delete_vectors
    collection_name = f"kb_{doc.kb_id}"
    delete_vectors(doc_id, collection_name)

    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Delete from database
    db.delete(doc)
    db.commit()

    return {"detail": "已删除"}


@router.get("/{doc_id}/preview")
def preview_doc(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """预览文档内容"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        from ...services.rag_engine import parse_document
        content = parse_document(doc.file_path)
        return {
            "filename": doc.filename,
            "content": content[:5000],
            "total_length": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


class DocEdit(BaseModel):
    content: str


@router.put("/{doc_id}/edit")
def edit_doc(doc_id: int, body: DocEdit, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """编辑文档内容并重新向量化"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # Save new content to file
    try:
        with open(doc.file_path, "w", encoding="utf-8") as f:
            f.write(body.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

    # Re-vectorize in background
    thread = threading.Thread(target=process_document, args=(doc.id, doc.file_path, doc.kb_id))
    thread.daemon = True
    thread.start()

    return {"detail": "文档已更新，正在重新向量化"}


@router.post("/batch_upload")
async def batch_upload(
    kb_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """批量上传文档"""
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id
    ).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    results = []
    for file in files:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename)[1]
        saved_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            kb_id=kb_id,
            filename=file.filename,
            file_path=file_path,
            status="uploading",
            progress=0,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        thread = threading.Thread(target=process_document, args=(doc.id, file_path, kb_id))
        thread.daemon = True
        thread.start()

        results.append(DocOut.model_validate(doc))

    return results
