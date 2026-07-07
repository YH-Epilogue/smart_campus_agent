# 灵犀 (Smart Campus Agent)

## 项目概述

灵犀是一款基于 RAG（检索增强生成）和 AI Agent 技术的校园智能问答与事务处理平台。整合学生手册、校园新闻等知识，通过 AI 对话为师生提供信息查询和事务办理服务。

## 角色体系

| 角色 | 说明 | 可用功能 |
|------|------|----------|
| 管理员 (admin) | 全功能管理 | 对话 + 知识库 + 文档 + 请假审批 + 用户管理 + 数据统计 + 日志 + 配置 |
| 教师 (teacher) | 教学管理 | 对话 + 知识库管理 + 文档管理 + 请假审批 |
| 学生 (student) | 日常使用 | 对话 + 我的请假记录 |

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
│  4. 拒绝规则 → 对话规则     │
│     → 意图识别              │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  5. ReAct 推理循环          │
│     Think → Act → Observe   │
│     LLM 自主选择工具        │
│     最多 5 步推理           │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  6. 后处理                   │
│     截断 → 过滤 → 记忆提取   │
│     保存回复 → 返回前端      │
└─────────────────────────────┘
```

## 技术架构

```
smart_campus_agent/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # 8 个 API 路由模块（31 个端点）
│   │   │   ├── auth.py        # 注册/登录 (JWT + PBKDF2 + 失败限制)
│   │   │   ├── users.py       # 用户管理 + RBAC 角色
│   │   │   ├── kb.py          # 知识库 CRUD
│   │   │   ├── doc.py         # 文档管理（上传/版本/向量/去重/拆分）
│   │   │   ├── chat.py        # ReAct 推理循环 + RAG + 工具调用
│   │   │   ├── logs.py        # 日志/统计/CSV 导出/数据分析
│   │   │   ├── settings.py    # 系统参数配置
│   │   │   └── leave.py       # 请假审批（提交/批准/驳回）
│   │   ├── services/          # 核心服务层
│   │   │   ├── llm_client.py  # LLM 客户端（Function Calling）
│   │   │   ├── agent_tools.py # 工具注册表（学生查询/请假）
│   │   │   ├── rag_engine.py  # RAG 检索引擎
│   │   │   ├── nlu.py         # 意图识别 + 问题重写
│   │   │   ├── rules.py       # 对话规则引擎
│   │   │   ├── memory.py      # 长期记忆系统
│   │   │   └── multimodal.py  # 图片 OCR (PaddleOCR)
│   │   ├── models/            # 数据模型（6 张表）
│   │   └── core/              # 配置 + JWT + 缓存
│   ├── data/                  # SQLite + ChromaDB + 上传文件
│   └── requirements.txt
├── frontend/                   # Vue 3 + Element Plus
│   ├── src/
│   │   ├── views/             # 8 个页面组件
│   │   ├── components/        # 5 个可复用组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── api/               # 统一 HTTP 层 (http.js)
│   │   └── router/            # 路由守卫 + 角色控制
│   └── package.json
├── README.md
└── DEPLOY.md
```

## 核心功能

### AI Agent（ReAct 推理）
- **Function Calling**：LLM 自主选择工具，无需关键词匹配
- **ReAct 循环**：Think → Act → Observe，最多 5 步推理
- **长期记忆**：跨会话记住用户偏好和历史事实
- **动态 Prompt**：根据工具/记忆/知识库动态构建 system prompt

### 工具调用
- 查询学生信息（学号/姓名）
- 提交请假申请（学号+日期+原因）
- 查询请假状态

### RAG 检索
- 文档解析（PDF/Word/TXT/Markdown）
- 文本切分（可配置 chunk_size/overlap）
- ChromaDB 向量化 + 多知识库检索
- 向量去重优化

### 日志与分析
- Dashboard 科幻大数据监控面板
- 热门关键词 + 每日消息量 + 检索成功率 + 用户活跃度
- CSV 导出 + 过期清理

## 快速部署

### 环境要求
- Python >= 3.10
- Node.js >= 18
- DeepSeek API Key

### 后端
```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 一键启动
双击 `E:\实训\Yan\启动.bat` 或运行 `python E:\实训\Yan\启动.py`

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 123456 | 管理员 |
| zzl | 123456 | 教师 |
| yanhao | 123456 | 学生 |

## 安全特性

- PBKDF2-SHA256 密码哈希（10 万轮迭代 + 随机盐值）
- JWT Token 认证 + 登录失败 5 次锁定
- 角色权限控制（路由守卫 + 后端校验）
- 文件上传类型白名单 + 大小限制
- XSS 防护（ChatBubble HTML 转义）
- 输入验证（用户名/密码格式校验）
