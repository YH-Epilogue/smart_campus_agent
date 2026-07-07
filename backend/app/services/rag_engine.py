"""
RAG Engine: 检索增强生成引擎模块

本模块实现了完整的 RAG（Retrieval-Augmented Generation）流水线：
文档解析 → 文本切分 → 向量化存储 → 语义检索 → 向量管理

核心组件：
- parse_document: 支持 PDF/DOCX/TXT/MD 四种格式的文档解析
- split_text: 基于固定长度的文本切分（带重叠窗口，保证上下文连贯）
- embed_and_store: 使用 ChromaDB 存储文本向量（ChromaDB 自动调用内置 embedding 模型）
- retrieve: 语义相似度检索，返回最相关的文档片段
- delete_vectors / deduplicate_vectors: 向量维护工具

存储后端使用 ChromaDB（本地持久化），embedding 距离使用余弦相似度（cosine）。
"""
import os
from pathlib import Path


def parse_document(file_path: str) -> str:
    """解析文档为纯文本

    支持格式：
    - .pdf: 使用 pymupdf 逐页提取文本
    - .docx / .doc: 使用 python-docx 提取段落文本
    - .txt / .md: 直接读取 UTF-8 编码文本

    Raises:
        ValueError: 不支持的文件格式

    注意：此处仅提取纯文本，不保留格式/表格/图片等信息。
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        # pymupdf（fitz）是高性能 PDF 解析库，按页提取文本
        import pymupdf
        doc = pymupdf.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    elif ext in (".docx", ".doc"):
        # python-docx 仅支持 .docx，.doc 需要额外处理（此处假设 .doc 也是 docx 格式）
        from docx import Document
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    elif ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """按固定长度切分文本，带重叠窗口

    Args:
        text: 待切分的完整文本
        chunk_size: 每个文本块的最大字符数（默认 500）
        chunk_overlap: 相邻块之间的重叠字符数（默认 50）

    重叠窗口的作用：避免在句子中间切断导致语义断裂，
    例如一句话跨越两个块时，重叠部分能保证至少一个块包含完整句子。

    Returns:
        非空文本块列表（已过滤空白块）
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # 跳过纯空白块（如连续换行产生的空段落）
        if chunk.strip():
            chunks.append(chunk)
        # 下一块的起始位置 = 当前起始 + (块大小 - 重叠)
        start += chunk_size - chunk_overlap
    return chunks


def embed_and_store(chunks: list[str], kb_id: int, doc_id: int, collection_name: str):
    """将文本块向量化并存入 ChromaDB

    Args:
        chunks: 文本块列表
        kb_id: 所属知识库 ID（写入元数据，用于后续按知识库过滤）
        doc_id: 所属文档 ID（写入元数据，用于按文档删除/查询）
        collection_name: ChromaDB 集合名称（通常为知识库名称）

    ChromaDB 的 upsert 行为：ID 相同时覆盖旧记录，适合重新上传文档时更新向量。
    向量 ID 格式为 "doc{doc_id}_chunk{i}"，保证同一文档重新上传时自动覆盖。
    """
    import chromadb
    from ..core.config import settings

    # 使用持久化客户端，数据存储在 settings.CHROMA_DIR 目录下
    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    # get_or_create: 集合不存在时自动创建，hnsw:space=cosine 表示使用余弦相似度
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # 生成唯一 ID：doc{文档ID}_chunk{块序号}，确保同一文档的向量可被覆盖
    ids = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks))]
    collection.upsert(
        ids=ids,
        documents=chunks,
        # 所有块共享相同的元数据（doc_id 和 kb_id），便于后续按条件过滤
        metadatas=[{"doc_id": doc_id, "kb_id": kb_id}] * len(chunks),
    )
    return len(chunks)


def retrieve(query: str, collection_name: str, top_k: int = 5, min_score: float = 0.0) -> list[dict]:
    """从 ChromaDB 检索最相关的文档块

    Args:
        query: 用户查询文本（会被 ChromaDB 自动向量化）
        collection_name: 目标集合名称
        top_k: 返回的最大结果数（默认 5）
        min_score: 最小相似度阈值（0~1，默认 0 表示不过滤）

    ChromaDB 返回的 distance 是余弦距离（0=完全相同，2=完全相反），
    转换为 score = 1 - distance（1=完全相同，0=完全相反）。

    Returns:
        相似度 >= min_score 的文档块列表，按相关性降序排列
    """
    import chromadb
    from ..core.config import settings

    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        # 集合不存在（知识库为空或已删除），返回空结果
        return []

    # n_results 控制 ChromaDB 返回的候选数量，后续还会按 min_score 过滤
    results = collection.query(query_texts=[query], n_results=top_k)

    retrieved = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            # 提取元数据和距离值（ChromaDB 返回嵌套列表，取 [0][i]）
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            # 余弦距离转相似度分数：distance=0 → score=1（完全匹配）
            score = round(1 - distance, 4)
            if score >= min_score:
                retrieved.append({
                    "content": doc,
                    "doc_id": meta.get("doc_id"),
                    "kb_id": meta.get("kb_id"),
                    "score": score,
                })
    return retrieved


def delete_vectors(doc_id: int, collection_name: str):
    """删除指定文档的所有向量

    用于文档删除时同步清理 ChromaDB 中的向量数据。
    通过元数据过滤 where={"doc_id": doc_id} 定位所有属于该文档的向量块。
    """
    import chromadb
    from ..core.config import settings

    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return

    # 按元数据条件查询该文档的所有向量 ID
    results = collection.get(
        where={"doc_id": doc_id},
        include=[]  # 不需要返回文档内容，只要 ID
    )

    if results and results["ids"]:
        collection.delete(ids=results["ids"])


def deduplicate_vectors(collection_name: str):
    """向量去重：删除重复文本块的向量

    当同一文档被多次上传时，可能产生内容完全相同的向量块。
    此函数通过内容哈希检测重复，保留首次出现的向量，删除后续重复项。

    Returns:
        被删除的重复向量数量
    """
    import chromadb
    from ..core.config import settings

    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return 0

    # 获取集合中所有向量的 ID、文档内容和元数据
    results = collection.get(include=["documents", "metadatas"])

    if not results or not results["ids"]:
        return 0

    # 用字典记录每个内容首次出现的向量 ID
    seen = {}
    ids_to_delete = []

    for i, doc_id in enumerate(results["ids"]):
        doc_content = results["documents"][i]
        if doc_content in seen:
            # 内容已存在，标记当前向量为重复项
            ids_to_delete.append(doc_id)
        else:
            seen[doc_content] = doc_id

    # 批量删除重复向量
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    return len(ids_to_delete)
