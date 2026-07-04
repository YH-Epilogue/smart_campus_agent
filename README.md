# Smart Campus Agent

校园智能体 —— 基于 RAG 的校园问答与事务处理平台

## 技术栈

- **后端：** FastAPI + SQLAlchemy + ChromaDB + sentence-transformers
- **前端：** Vue 3 + Element Plus + Pinia + Axios
- **数据库：** SQLite（关系型）+ ChromaDB（向量）

## 快速启动

### 后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
