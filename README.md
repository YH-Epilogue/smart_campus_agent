# Smart Campus Agent

校园智能体 —— 基于 RAG 的校园问答与事务处理平台

## 项目简介

Smart Campus Agent 是一个面向校园场景的智能问答与事务处理平台。通过 RAG（检索增强生成）技术，将校园文档（如规章制度、办事指南等）向量化存储，实现精准的校园知识问答。同时支持智能体工具调用，可自动处理请假申请、学生信息查询等事务。

### 核心功能

- **智能问答** — 基于知识库的 RAG 检索，精准回答校园相关问题
- **知识库管理** — 支持上传 PDF、Word、TXT 文档，自动解析并建立向量索引
- **流式对话** — 实时流式输出，支持多轮对话上下文
- **事务处理** — 智能体工具调用，自动执行学生查询、请假申请等操作
- **用户系统** — 注册登录、JWT 认证、角色权限管理
- **管理后台** — 知识库管理、文档管理、系统设置

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI |
| **关系数据库** | SQLite + SQLAlchemy |
| **向量数据库** | ChromaDB |
| **Embedding** | sentence-transformers（text2vec-base-chinese） |
| **前端框架** | Vue 3 + Vite |
| **UI 组件库** | Element Plus |
| **状态管理** | Pinia |
| **HTTP 客户端** | Axios |

## 项目结构

```
smart_campus_agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 路由
│   │   │   ├── auth.py      # 认证接口
│   │   │   ├── chat.py      # 对话接口
│   │   │   ├── kb.py        # 知识库管理
│   │   │   ├── doc.py       # 文档管理
│   │   │   ├── users.py     # 用户管理
│   │   │   ├── logs.py      # 日志查询
│   │   │   └── settings.py  # 系统设置
│   │   ├── core/
│   │   │   ├── config.py    # 配置管理
│   │   │   └── security.py  # JWT 认证
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   │   ├── rag_engine.py    # RAG 检索引擎
│   │   │   ├── llm_client.py    # 大模型接口
│   │   │   ├── agent_tools.py   # 智能体工具
│   │   │   ├── nlu.py           # 意图识别
│   │   │   └── rules.py         # 规则引擎
│   │   └── main.py          # 应用入口
│   ├── data/                # 数据目录
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # API 请求封装
│   │   ├── components/      # 组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态
│   │   ├── views/           # 页面视图
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 快速启动

### 环境要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 后端启动

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

启动后访问 API 文档：http://localhost:8000/docs

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问前端页面：http://localhost:5173

### 配置大模型（可选）

在 `backend/` 目录下创建 `.env` 文件：

```env
# 选择 LLM 提供商：mock / ollama / deepseek / api
LLM_PROVIDER=deepseek

# DeepSeek 配置
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

不配置时默认使用 Mock 模式，可正常体验所有功能。

### 支持的 LLM 模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `mock` | 模拟回复 | 开发调试，无需 API Key |
| `ollama` | 本地模型 | 需安装 Ollama 并下载模型 |
| `deepseek` | DeepSeek API | 需 API Key |
| `api` | 通用 OpenAI 兼容接口 | 适用于任意兼容接口 |

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/chat/send` | POST | 发送对话（流式） |
| `/api/v1/kb/list` | GET | 获取知识库列表 |
| `/api/v1/kb/create` | POST | 创建知识库 |
| `/api/v1/doc/upload` | POST | 上传文档 |
| `/api/v1/doc/list` | GET | 获取文档列表 |
| `/api/v1/users/me` | GET | 获取当前用户信息 |
| `/api/v1/logs/list` | GET | 获取对话日志 |

完整接口文档请访问：http://localhost:8000/docs

## License

MIT
