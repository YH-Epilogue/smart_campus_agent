# Smart Campus Agent - 校园智能体平台

## 项目概述

Smart Campus Agent 是一款基于 RAG（检索增强生成）技术的校园智能问答与事务处理平台。整合学生手册、校园新闻等知识，通过 AI 对话为师生提供信息查询和事务办理服务。

## 工作流程

```
用户输入问题
    ↓
┌─────────────────────────────┐
│  1. 敏感词过滤              │
│  2. 保存用户消息到数据库     │
│  3. 加载对话历史             │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  4. 检查拒绝规则            │
│     → 命中则返回拒绝话术    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  5. 检查对话规则            │
│     → 命中则返回规则回复    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  6. 检查工具调用            │
│     → 查询学生/请假/请假状态 │
│     → 执行工具并返回结果    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  7. 意图识别                │
│     → 问候/帮助/知识库/文档  │
│     → 命中则返回固定回复    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  8. 问题重写 + RAG 检索     │
│     → 语义纠错              │
│     → 多知识库检索           │
│     → 相似度过滤             │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  9. 调用 DeepSeek LLM       │
│     → 检索结果作为上下文     │
│     → 对话历史作为上下文     │
│     → 生成回答               │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  10. 后处理                  │
│      → 截断过长回答          │
│      → 敏感词过滤            │
│      → 生成推荐追问          │
│      → 保存助手消息          │
│      → 返回给前端            │
└─────────────────────────────┘
```

**关键模块协作：**

| 模块 | 文件 | 作用 |
|------|------|------|
| NLU | nlu.py | 意图识别 + 问题重写 + 语义纠错 |
| 规则引擎 | rules.py | 对话规则 + 拒绝回答规则 |
| 工具调用 | agent_tools.py | 学生查询 / 请假申请 / 请假状态 |
| RAG 引擎 | rag_engine.py | 文档解析 → 切分 → 向量化 → 检索 |
| LLM 客户端 | llm_client.py | DeepSeek / Ollama / Mock 多模式 |
| 多模态 | multimodal.py | 图片 OCR (PaddleOCR) + 语音 ASR |

## 技术架构

```
smart_campus_agent/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # API 路由层
│   │   │   ├── auth.py        # 注册/登录 (JWT + 失败限制)
│   │   │   ├── users.py       # 用户管理 + RBAC 角色
│   │   │   ├── kb.py          # 知识库 CRUD + 筛选
│   │   │   ├── doc.py         # 文档上传/解析/预览/删除/版本/向量预览
│   │   │   ├── chat.py        # 多轮对话 + RAG + 工具调用
│   │   │   ├── logs.py        # 日志记录/统计/CSV导出/可视化
│   │   │   └── settings.py    # 系统参数配置
│   │   ├── core/
│   │   │   ├── config.py      # 全局配置
│   │   │   └── security.py    # JWT + 密码加密
│   │   ├── models/
│   │   │   ├── database.py    # SQLite 连接
│   │   │   ├── tables.py      # ORM 模型
│   │   │   └── schemas.py     # Pydantic 模型
│   │   ├── services/
│   │   │   ├── rag_engine.py  # RAG 引擎
│   │   │   ├── llm_client.py  # LLM 客户端
│   │   │   ├── nlu.py         # 意图识别 + 问题重写
│   │   │   ├── rules.py       # 对话规则引擎
│   │   │   ├── multimodal.py  # OCR + ASR
│   │   │   └── agent_tools.py # 工具注册表
│   │   └── main.py            # FastAPI 入口
│   ├── data/                  # 数据目录 (SQLite + ChromaDB + 上传文件)
│   ├── .env                   # 环境变量
│   └── requirements.txt       # Python 依赖
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 可复用组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── api/               # API 调用封装
│   │   └── router/            # 路由配置
│   └── package.json           # Node 依赖
└── README.md
```

## 快速部署（从 GitHub 拉取）

### 1. 克隆项目
```bash
git clone <仓库地址> smart_campus_agent
cd smart_campus_agent
```

### 2. 后端部署
```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 方法一：编辑 .env 文件，设置 DeepSeek_API_KEY
# 方法二：设置系统环境变量 DeepSeek_API_KEY

# 启动后端
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 前端部署
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问地址
- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs

### 5. 默认账号
- 用户名：admin
- 密码：123456

## API 接口说明

### 认证接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 注册 |
| POST | /api/v1/auth/login | 登录，返回 JWT token |

### 知识库接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/kb/ | 列表（支持 name/department 筛选） |
| POST | /api/v1/kb/ | 创建 |
| PUT | /api/v1/kb/{id} | 编辑 |
| DELETE | /api/v1/kb/{id} | 删除 |
| POST | /api/v1/kb/{id}/clone | 克隆 |

### 文档接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/doc/upload | 上传文档 |
| GET | /api/v1/doc/{kb_id} | 文档列表 |
| GET | /api/v1/doc/{id}/preview | 预览 |
| PUT | /api/v1/doc/{id}/edit | 编辑 |
| DELETE | /api/v1/doc/{id} | 删除 |
| POST | /api/v1/doc/multimodal | 多模态上传(OCR/ASR) |

### 对话接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/chat/ | 发送消息（支持 top_k/min_score 参数） |
| GET | /api/v1/chat/{session_id} | 获取会话历史 |
| DELETE | /api/v1/chat/{session_id} | 删除会话 |

### 日志接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/logs/ | 日志列表 |
| GET | /api/v1/logs/stats | 统计数据 |
| GET | /api/v1/logs/analytics | 数据分析 |
| GET | /api/v1/logs/export | CSV 导出 |

### 配置接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/settings/ | 获取配置 |
| PUT | /api/v1/settings/ | 更新配置 |

### 工具调用（通过对话触发）
在对话中输入以下关键词触发工具：
- "查询学生张三" → 调用 query_student
- "帮我请假 2024-01-01 到 2024-01-05" → 调用 create_leave_request
- "查询请假状态" → 调用 get_leave_status

## 功能清单

### 后台管理
- [x] 知识库 CRUD + 筛选 + 部门/负责人
- [x] 文档管理 + 版本 + 向量预览 + 拆分预览
- [x] 系统参数配置
- [x] 角色权限 (admin/kb_admin/user)
- [x] Redis 缓存

### RAG 引擎
- [x] 文档解析 (PDF/Word/TXT)
- [x] 文本切分 (可配置 chunk_size/overlap)
- [x] ChromaDB 向量化 + 检索
- [x] 向量去重

### 对话系统
- [x] 多轮对话 + 上下文维护
- [x] 多知识库检索
- [x] 意图识别 + 问题重写 + 语义纠错
- [x] 敏感词 + 兜底 + 反问引导
- [x] 对话规则引擎
- [x] 工具调用 (学生查询/请假)

### 日志与分析
- [x] 对话日志记录
- [x] 统计 + CSV 导出 + 数据可视化
- [x] 过期日志清理

### 多模态
- [x] 图片 OCR (PaddleOCR)
- [x] 语音 ASR (云端 API)

## 环境要求

### Python 依赖
- Python >= 3.10
- fastapi >= 0.139.0
- pydantic >= 2.9.0
- sqlalchemy >= 2.0.0
- chromadb >= 0.5.0
- redis >= 5.0.0 (可选)
- paddleocr (OCR)

### Node.js 依赖
- Node.js >= 18
- Vue 3 + Vite
- Element Plus
- Pinia
- Axios

### 外部服务
- DeepSeek API Key（系统环境变量）
- Redis（可选，未安装时使用内存缓存）
