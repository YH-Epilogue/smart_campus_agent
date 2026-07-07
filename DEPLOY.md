# 灵犀 (Smart Campus Agent) 部署指南

## 从 GitHub 拉取后部署

### 步骤 1：克隆仓库
```bash
git clone <仓库地址> smart_campus_agent
cd smart_campus_agent
```

### 步骤 2：后端环境

#### 2.1 创建虚拟环境
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 2.2 安装依赖
```bash
pip install -r requirements.txt
```

#### 2.3 配置环境变量

设置系统环境变量 DeepSeek_API_KEY（推荐）：

```bash
# Windows PowerShell
[System.Environment]::SetEnvironmentVariable("DeepSeek_API_KEY", "你的API密钥", "Machine")

# Linux/Mac
export DeepSeek_API_KEY="你的API密钥"
```

#### 2.4 启动后端
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 步骤 3：前端环境

```bash
cd frontend
npm install
npm run dev
```

### 步骤 4：访问
- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- 默认账号：admin / 123456

## 一键启动（Windows）

将项目克隆到 `E:\实训\smart_campus_agent` 后，双击以下脚本即可：

| 脚本 | 功能 |
|------|------|
| `E:\实训\Yan\启动.py` | 启动后端 + 前端，独立窗口运行 |
| `E:\实训\Yan\关闭.py` | 关闭所有服务进程 |
| `E:\实训\Yan\重启.py` | 先关闭再启动 |

也可以直接运行 `python E:\实训\Yan\启动.py`。

## 角色与权限

| 角色 | 用户名 | 登录后可用页面 |
|------|--------|----------------|
| 管理员 | admin | 全部页面 |
| 教师 | zzl | 对话 + 知识库 + 文档 + 请假审批 |
| 学生 | yanhao | 对话 + 我的请假 |

登录时需选择对应角色，角色不匹配会提示错误。

## API 调用示例

### 登录获取 Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'
```

### 对话
```python
import requests

resp = requests.post("http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "123456"})
token = resp.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
resp = requests.post("http://localhost:8000/api/v1/chat/",
    json={"session_id": "test", "kb_id": 1, "query": "你好"},
    headers=headers)
print(resp.json()["answer"])
```

### 工具调用
```python
# 查询学生
requests.post("http://localhost:8000/api/v1/chat/",
    json={"session_id": "test", "query": "查询学生 学号2023001"},
    headers=headers)

# 提交请假
requests.post("http://localhost:8000/api/v1/chat/",
    json={"session_id": "test", "query": "帮我请假 学号2023001 2024-01-01 到 2024-01-05 因为生病"},
    headers=headers)
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| ModuleNotFoundError | 确保在虚拟环境中：`pip install -r requirements.txt` |
| DeepSeek API 调用失败 | 检查环境变量 DeepSeek_API_KEY 是否设置 |
| ChromaDB 首次加载慢 | 首次下载 embedding 模型（~80MB），之后自动缓存 |
| 前端跨域错误 | 检查 vite.config.js 代理配置和后端 CORS |
| pip 安装 SSL 错误 | 执行 `$env:NO_PROXY="*"; $env:no_proxy="*"` |
| pydantic 版本冲突 | `pip install pydantic==2.9.2 pydantic-core==2.23.4 pydantic-settings` |
| 登录页面黑屏 | F12 控制台查看报错，重启前端 dev server |
| 后端启动超时 | 确认 DeepSeek_API_KEY 环境变量已设置 |
