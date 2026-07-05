# 部署指南 - 组员协作

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

**方法一：编辑 .env 文件**
```
# 编辑 backend/.env
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

**方法二：设置系统环境变量（推荐）**
```bash
# Windows PowerShell
[System.Environment]::SetEnvironmentVariable("DeepSeek_API_KEY", "你的API密钥", "User")

# Linux/Mac
export DeepSeek_API_KEY="你的API密钥"
```

#### 2.4 启动后端
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 步骤 3：前端环境

#### 3.1 安装依赖
```bash
cd frontend
npm install
```

#### 3.2 启动前端
```bash
npm run dev
```

### 步骤 4：访问
- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- 默认账号：admin / 123456

## Windows 一键启动

双击 `启动.bat` 即可自动启动前后端。

## API 调用示例

### 使用 curl 测试
```bash
# 登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'

# 使用 token 调用对话接口
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"session_id":"test","kb_id":1,"query":"你好"}'
```

### 使用 Python requests
```python
import requests

# 登录
resp = requests.post("http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "123456"})
token = resp.json()["access_token"]

# 对话
headers = {"Authorization": f"Bearer {token}"}
resp = requests.post("http://localhost:8000/api/v1/chat/",
    json={"session_id": "test", "kb_id": 1, "query": "你好"},
    headers=headers)
print(resp.json())
```

### 工具调用示例
```python
# 查询学生
resp = requests.post("http://localhost:8000/api/v1/chat/",
    json={"session_id": "test", "query": "查询学生张三"},
    headers=headers)

# 提交请假
resp = requests.post("http://localhost:8000/api/v1/chat/",
    json={"session_id": "test", "query": "帮我请假，从2024-01-01到2024-01-05，因为生病"},
    headers=headers)
```

## 常见问题

### Q: 启动报 ModuleNotFoundError
A: 确保在虚拟环境中安装了所有依赖：`pip install -r requirements.txt`

### Q: DeepSeek API 调用失败
A: 检查环境变量 DeepSeek_API_KEY 是否正确设置

### Q: ChromaDB 首次加载慢
A: 首次使用会下载 embedding 模型（约 80MB），之后会缓存

### Q: 前端跨域错误
A: 确保后端 CORS 配置包含前端地址，检查 vite.config.js 代理配置
