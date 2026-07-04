"""
RAG Engine: 文档解析 -> 切分 -> 向量化 -> 检索
"""
import os
from pathlib import Path


def parse_document(file_path: str) -> str:
    """解析文档为纯文本"""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        import pymupdf
        doc = pymupdf.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    elif ext in (".docx", ".doc"):
        from docx import Document
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    elif ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """按长度切分文本，带重叠"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks


def embed_and_store(chunks: list[str], kb_id: int, doc_id: int, collection_name: str):
    """将文本块向量化并存入 ChromaDB"""
    import chromadb
    from ..core.config import settings

    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks))]
    collection.upsert(
        ids=ids,
        documents=chunks,
        metadatas=[{"doc_id": doc_id, "kb_id": kb_id}] * len(chunks),
    )
    return len(chunks)


def retrieve(query: str, collection_name: str, top_k: int = 5, min_score: float = 0.0) -> list[dict]:
    """从 ChromaDB 检索最相关的文档块"""
    import chromadb
    from ..core.config import settings

    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return []

    results = collection.query(query_texts=[query], n_results=top_k)

    retrieved = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
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
    """删除指定文档的所有向量"""
    import chromadb
    from ..core.config import settings

    client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return

    # Find all vector IDs for this document
    results = collection.get(
        where={"doc_id": doc_id},
        include=[]
    )

    if results and results["ids"]:
        collection.delete(ids=results["ids"])
