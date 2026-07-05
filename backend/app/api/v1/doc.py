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

    # Check file size
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE_MB}MB）")

    # Check file type whitelist
    allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，允许的格式: {', '.join(sorted(allowed_exts))}")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
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
def list_docs(
    kb_id: int,
    filename: str = None,
    start_time: str = None,
    end_time: str = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(Document).filter(Document.kb_id == kb_id)
    if filename:
        query = query.filter(Document.filename.contains(filename))
    if start_time:
        query = query.filter(Document.created_at >= start_time)
    if end_time:
        query = query.filter(Document.created_at <= end_time)
    docs = query.all()
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


@router.get("/{doc_id}/versions")
def list_versions(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """获取文档版本历史"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # Find version files
    base, ext = os.path.splitext(doc.file_path)
    versions = []
    for i in range(1, 100):
        version_path = f"{base}_v{i}{ext}"
        if os.path.exists(version_path):
            mtime = os.path.getmtime(version_path)
            versions.append({
                "version": i,
                "path": version_path,
                "time": mtime,
            })
        else:
            break

    # Current version is the latest
    current_version = len(versions) + 1

    return {
        "current_version": current_version,
        "versions": versions,
    }


@router.post("/{doc_id}/rollback")
def rollback_doc(doc_id: int, version: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """回滚到指定版本"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # Find version file
    base, ext = os.path.splitext(doc.file_path)
    version_path = f"{base}_v{version}{ext}"

    if not os.path.exists(version_path):
        raise HTTPException(status_code=404, detail=f"版本 {version} 不存在")

    # Read version content
    with open(version_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Save current version before rollback
    current_version = 0
    for i in range(1, 100):
        if os.path.exists(f"{base}_v{i}{ext}"):
            current_version = i
        else:
            break
    current_version += 1

    # Copy current file to version
    import shutil
    shutil.copy2(doc.file_path, f"{base}_v{current_version}{ext}")

    # Restore version content
    with open(doc.file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Re-vectorize in background
    thread = threading.Thread(target=process_document, args=(doc.id, doc.file_path, doc.kb_id))
    thread.daemon = True
    thread.start()

    return {"detail": f"已回滚到版本 {version}，当前版本 {current_version}"}


@router.get("/{doc_id}/vectors")
def preview_vectors(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """预览文档的向量数据（调试用）"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    import chromadb
    from ...core.config import settings

    collection_name = f"kb_{doc.kb_id}"
    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return {"vectors": [], "count": 0, "dimension": 0}

    # Get all vectors for this document
    results = collection.get(
        where={"doc_id": doc_id},
        include=["documents", "metadatas", "embeddings"]
    )

    vectors = []
    if results and results["ids"]:
        for i, doc_id_str in enumerate(results["ids"]):
            dim = len(results["embeddings"][i]) if results["embeddings"] is not None and len(results["embeddings"]) > i else 0
            vectors.append({
                "id": doc_id_str,
                "document": results["documents"][i][:100] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
                "dimension": dim,
            })

    return {
        "doc_id": doc_id,
        "filename": doc.filename,
        "count": len(vectors),
        "dimension": vectors[0]["dimension"] if vectors else 0,
        "vectors": vectors[:10],  # Limit to first 10 for preview
    }


@router.post("/{kb_id}/dedup")
def dedup_vectors(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """知识库向量去重"""
    from ...services.rag_engine import deduplicate_vectors
    collection_name = f"kb_{kb_id}"
    removed = deduplicate_vectors(collection_name)
    return {"detail": f"已删除 {removed} 个重复向量"}


@router.post("/multimodal")
async def multimodal_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """多模态文件上传（图片OCR / 语音ASR）"""
    # Save file temporarily
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text based on file type
    from ...services.multimodal import extract_text_from_file
    try:
        text = extract_text_from_file(file_path)
        return {
            "filename": file.filename,
            "text": text,
            "type": "image" if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp") else "audio" if ext in (".mp3", ".wav", ".m4a", ".ogg", ".flac") else "text",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)


class SplitPreview(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 50


@router.post("/{doc_id}/split_preview")
def split_preview(doc_id: int, body: SplitPreview, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """预览文档拆分结果"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        from ...services.rag_engine import parse_document, split_text
        text = parse_document(doc.file_path)
        chunks = split_text(text, chunk_size=body.chunk_size, chunk_overlap=body.chunk_overlap)

        return {
            "total_length": len(text),
            "chunk_count": len(chunks),
            "chunk_size": body.chunk_size,
            "chunk_overlap": body.chunk_overlap,
            "preview": chunks[:5],  # Show first 5 chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
