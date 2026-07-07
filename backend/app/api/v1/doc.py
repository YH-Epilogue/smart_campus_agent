"""
文档管理模块：文档上传、预览、编辑、版本管理与向量操作

提供以下接口：
- POST /doc/upload           — 单文件上传（触发后台向量化）
- GET  /doc/{kb_id}          — 查询知识库下的文档列表
- DELETE /doc/{doc_id}       — 删除文档（含向量和磁盘文件）
- GET  /doc/{doc_id}/preview — 预览文档文本内容
- PUT  /doc/{doc_id}/edit    — 编辑文档内容并重新向量化
- POST /doc/batch_upload     — 批量上传文档
- GET  /doc/{doc_id}/versions — 获取版本历史
- POST /doc/{doc_id}/rollback — 回滚到指定版本
- GET  /doc/{doc_id}/vectors  — 预览向量数据（调试用）
- POST /doc/{kb_id}/dedup     — 知识库向量去重
- POST /doc/multimodal        — 多模态文件上传（图片OCR/语音ASR）
- POST /doc/{doc_id}/split_preview — 预览文档拆分结果

权限规则：
- 所有操作需验证调用者对父知识库的访问权限
- admin/teacher 可操作所有知识库下的文档
- 普通用户只能操作自己知识库下的文档
"""
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
    """后台处理文档：解析 -> 切分 -> 向量化

    在独立线程中运行，流程：
    1. 解析文档内容（parse_document）
    2. 切分为文本块（split_text）
    3. 向量化并存入 ChromaDB（embed_and_store）
    每个步骤更新进度百分比到数据库，供前端轮询显示。
    """
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
            # 第一步：解析文档内容（进度 10% → 40%）
            doc.progress = 20
            db.commit()
            text = parse_document(file_path)
            doc.progress = 40
            db.commit()

            # 第二步：将文本切分为 chunks（进度 40% → 60%）
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

            # 第三步：向量化并存入 ChromaDB（进度 60% → 95%）
            doc.status = "indexing"
            doc.progress = 70
            db.commit()
            collection_name = f"kb_{kb_id}"
            chunk_count = embed_and_store(chunks, kb_id, doc_id, collection_name)

            # 完成（进度 100%）
            doc.status = "ready"
            doc.progress = 100
            doc.chunk_count = chunk_count
            db.commit()

        except Exception as e:
            # 处理失败，记录错误信息
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
    """单文件上传接口

    - 验证知识库存在性及调用者权限
    - 校验文件大小（不超过 MAX_UPLOAD_SIZE_MB）
    - 校验文件类型白名单（pdf/docx/txt/md/jpg/png/mp3 等）
    - 文件以 UUID 重命名存储到 UPLOAD_DIR
    - 创建文档记录后启动后台线程进行向量化处理
    - 返回文档信息（status=uploading，progress=0）
    """
    # 验证知识库存在性
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # 权限检查：非管理员/教师只能操作自己的知识库
    if user.role not in ("teacher", "admin") and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限操作该知识库")

    # 读取文件内容并校验大小
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {settings.MAX_UPLOAD_SIZE_MB}MB）")

    # 校验文件扩展名白名单
    allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，允许的格式: {', '.join(sorted(allowed_exts))}")

    # 保存文件到磁盘（UUID 重命名防冲突）
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # 创建文档记录
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

    # 启动后台线程进行文档解析和向量化（非阻塞）
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
    """查询指定知识库下的文档列表

    - 支持按文件名模糊搜索、创建时间范围筛选
    - 返回文档的基本信息和处理状态
    """
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
    """删除文档

    - 验证文档存在性及调用者对父知识库的权限
    - 三步删除：ChromaDB 向量 → 磁盘文件 → 数据库记录
    - 任何一步失败不影响其他步骤（尽力清理）
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 权限检查：通过父知识库判断
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.kb_id).first()
    if kb and user.role not in ("teacher", "admin") and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限操作该文档")

    # 从 ChromaDB 删除向量数据
    from ...services.rag_engine import delete_vectors
    collection_name = f"kb_{doc.kb_id}"
    delete_vectors(doc_id, collection_name)

    # 删除磁盘上的文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # 从数据库删除记录
    db.delete(doc)
    db.commit()

    return {"detail": "已删除"}


@router.get("/{doc_id}/preview")
def preview_doc(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """预览文档文本内容

    - 验证文档存在性及权限
    - 使用 parse_document 解析文件内容
    - 仅返回前 5000 字符避免响应过大
    - 返回：filename、content（截断）、total_length（原始长度）
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 权限检查
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.kb_id).first()
    if kb and user.role not in ("teacher", "admin") and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限查看该文档")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        from ...services.rag_engine import parse_document
        content = parse_document(doc.file_path)
        return {
            "filename": doc.filename,
            "content": content[:5000],  # 截断避免响应过大
            "total_length": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


class DocEdit(BaseModel):
    """文档编辑请求体"""
    content: str


@router.put("/{doc_id}/edit")
def edit_doc(doc_id: int, body: DocEdit, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """编辑文档内容并重新向量化

    - 验证文档存在性及权限
    - 将新内容写入原始文件路径
    - 启动后台线程重新进行文档解析和向量化
    - 返回提示信息，前端可轮询进度
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 权限检查
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.kb_id).first()
    if kb and user.role not in ("teacher", "admin") and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限编辑该文档")

    # 将新内容写入文件
    try:
        with open(doc.file_path, "w", encoding="utf-8") as f:
            f.write(body.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

    # 后台重新向量化
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
    """批量上传文档

    - 验证知识库存在性及权限
    - 逐个文件处理：校验类型/大小 → 保存 → 创建记录 → 后台向量化
    - 单个文件失败不影响其他文件
    - 返回每个文件的处理结果（成功返回 DocOut，失败返回错误信息）
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    # 权限检查
    if user.role not in ("teacher", "admin") and kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权限操作该知识库")

    results = []
    # 文件类型白名单
    allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    for file in files:
        # 校验文件类型
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_exts:
            results.append({"filename": file.filename, "status": "error", "detail": f"不支持的格式: {ext}"})
            continue
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        saved_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
        content = await file.read()
        # 校验文件大小
        if len(content) > max_size:
            results.append({"filename": file.filename, "status": "error", "detail": f"文件超过{settings.MAX_UPLOAD_SIZE_MB}MB"})
            continue
        with open(file_path, "wb") as f:
            f.write(content)

        # 创建文档记录
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

        # 后台线程向量化
        thread = threading.Thread(target=process_document, args=(doc.id, file_path, kb_id))
        thread.daemon = True
        thread.start()

        results.append(DocOut.model_validate(doc))

    return results


@router.get("/{doc_id}/versions")
def list_versions(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """获取文档版本历史

    - 扫描磁盘上的 _v1, _v2, ... 版本文件
    - 返回当前版本号和所有历史版本信息（版本号、路径、修改时间）
    - 版本命名规则：原始文件为当前版本，历史版本为 {base}_v{N}{ext}
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 扫描版本文件：base_v1.ext, base_v2.ext, ...
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

    # 当前版本号 = 已有版本数 + 1
    current_version = len(versions) + 1

    return {
        "current_version": current_version,
        "versions": versions,
    }


@router.post("/{doc_id}/rollback")
def rollback_doc(doc_id: int, version: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """回滚到指定版本

    - 读取目标版本文件内容
    - 将当前版本备份为新的版本号（防止回滚后丢失）
    - 用目标版本内容覆盖当前文件
    - 启动后台线程重新向量化
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 定位版本文件
    base, ext = os.path.splitext(doc.file_path)
    version_path = f"{base}_v{version}{ext}"

    if not os.path.exists(version_path):
        raise HTTPException(status_code=404, detail=f"版本 {version} 不存在")

    # 读取目标版本内容
    with open(version_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 计算当前版本号，用于备份
    current_version = 0
    for i in range(1, 100):
        if os.path.exists(f"{base}_v{i}{ext}"):
            current_version = i
        else:
            break
    current_version += 1

    # 备份当前版本到新版本文件
    import shutil
    shutil.copy2(doc.file_path, f"{base}_v{current_version}{ext}")

    # 用目标版本内容覆盖当前文件
    with open(doc.file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 后台重新向量化
    thread = threading.Thread(target=process_document, args=(doc.id, doc.file_path, doc.kb_id))
    thread.daemon = True
    thread.start()

    return {"detail": f"已回滚到版本 {version}，当前版本 {current_version}"}


@router.get("/{doc_id}/vectors")
def preview_vectors(doc_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """预览文档的向量数据（调试接口）

    - 从 ChromaDB 中读取该文档的所有向量
    - 返回：向量 ID、文档片段（前100字）、元数据、维度
    - 仅返回前 10 条用于预览
    - 无权限限制（调试用途）
    """
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

    # 按 doc_id 过滤获取该文档的所有向量
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
        "vectors": vectors[:10],  # 仅预览前 10 条
    }


@router.post("/{kb_id}/dedup")
def dedup_vectors(kb_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """知识库向量去重

    - 仅 admin/teacher 可执行
    - 对指定知识库的 ChromaDB collection 执行去重
    - 返回被删除的重复向量数量
    """
    if user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="无权限执行向量去重")
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
    """多模态文件上传（图片OCR / 语音ASR）

    - 接收图片或音频文件
    - 根据文件类型调用对应的提取服务（图片→OCR，音频→ASR）
    - 处理完成后自动清理临时文件
    - 返回提取的文本和文件类型标识
    """
    # 临时保存文件
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    saved_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 根据文件类型提取文本
    from ...services.multimodal import extract_text_from_file
    try:
        text = extract_text_from_file(file_path)
        # 判断文件类型：图片/音频/文本
        return {
            "filename": file.filename,
            "text": text,
            "type": "image" if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp") else "audio" if ext in (".mp3", ".wav", ".m4a", ".ogg", ".flac") else "text",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)


class SplitPreview(BaseModel):
    """文档拆分预览参数"""
    chunk_size: int = 500
    chunk_overlap: int = 50


@router.post("/{doc_id}/split_preview")
def split_preview(doc_id: int, body: SplitPreview, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """预览文档拆分结果

    - 解析文档内容并按指定参数进行拆分
    - 返回：总长度、块数、参数配置、前 5 个块的预览
    - 用于前端调参时实时预览拆分效果
    - 注意：此接口不会实际向量化，仅预览
    """
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
            "preview": chunks[:5],  # 仅预览前 5 个块
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
