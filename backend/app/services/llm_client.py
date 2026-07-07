"""
LLM Client: 统一大模型接口模块

本模块封装了与大语言模型（LLM）的所有交互逻辑，是灵犀智能体的核心通信层。
主要职责：
1. 构建动态系统提示词（System Prompt），将工具描述、用户记忆、知识库检索结果注入上下文
2. 通过 OpenAI 兼容 API 发送非流式请求，支持 Function Calling（工具调用）
3. 统一管理模型配置（provider、model、base_url、api_key）

底层使用 httpx 异步客户端，兼容任何 OpenAI API 格式的大模型服务（如 DeepSeek、通义千问等）。
"""
import json
import httpx
from ..core.config import settings


class LLMClient:
    """大语言模型统一调用客户端

    通过 settings 读取模型配置（LLM_PROVIDER / LLM_MODEL / LLM_BASE_URL / LLM_API_KEY），
    提供两个核心方法：
    - build_system_prompt: 根据当前上下文动态组装系统提示词
    - chat_with_tools: 发送对话请求，支持传入工具定义供模型选择调用
    """

    def __init__(self):
        # 记录当前使用的模型提供方（如 "deepseek"、"openai"），便于日志和扩展
        self.provider = settings.LLM_PROVIDER

    def build_system_prompt(self, tools_desc: str = "", memories: str = "", context: str = "") -> str:
        """构建动态系统提示词

        将三类上下文信息拼接到基础 prompt 中：
        - tools_desc: 可用工具的文本描述，让模型知道能调用哪些工具
        - memories: 从长期记忆系统检索到的用户偏好/历史事实
        - context: 从知识库（RAG）检索到的相关文档片段

        每项为空时跳过拼接，避免输出多余空白。
        """
        prompt = """你是灵犀（Smart Campus Agent），一个校园智能助手。
你的职责是帮助师生解答校园问题、查询学生信息、管理请假事务。

## 推理规则
当用户提出请求时：
1. 分析用户意图
2. 如果需要查询数据或执行操作，选择合适的工具
3. 执行工具后，将结果整合为自然语言回答
4. 如果没有合适的工具，基于知识库检索回答
5. 回答要简洁、准确、友好
"""
        if tools_desc:
            prompt += f"\n## 可用工具\n{tools_desc}\n"
        if memories:
            prompt += f"\n## 用户记忆\n{memories}\n"
        if context:
            prompt += f"\n## 知识库检索结果\n{context}\n"
        return prompt

    async def chat_with_tools(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """非流式调用大模型，支持 Function Calling

        Args:
            messages: 对话历史列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            tools: OpenAI 格式的工具定义列表（可选），传入后模型可返回 tool_calls

        Returns:
            dict: 包含三个字段：
                - content: 模型生成的文本回复（可能为空字符串，当模型选择调用工具时）
                - tool_calls: 工具调用列表（OpenAI 格式，含 function.name 和 arguments）
                - finish_reason: 结束原因（"stop" / "tool_calls"）
        """
        # 构建请求载荷，遵循 OpenAI Chat Completions API 规范
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
        }
        # 仅在有工具时传入 tools 字段，避免模型尝试调用不存在的工具
        if tools:
            payload["tools"] = tools

        # 构建请求头，仅在配置了 API Key 时附加认证头
        headers = {}
        if settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
            headers["Content-Type"] = "application/json"

        # 使用异步 httpx 客户端，超时设为 120 秒以应对大模型推理延迟
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.LLM_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            # 检查 HTTP 状态码，非 200 时返回错误信息
            if resp.status_code != 200:
                error_detail = resp.text[:200] if resp.text else "未知错误"
                return {
                    "content": f"LLM 服务返回异常（{resp.status_code}），请稍后重试",
                    "tool_calls": [],
                    "finish_reason": "error",
                    "error": error_detail,
                }
            data = resp.json()
            # OpenAI API 返回 choices 数组，取第一个（通常只有一个）
            choice = data["choices"][0]
            message = choice["message"]

            return {
                "content": message.get("content", ""),
                "tool_calls": message.get("tool_calls", []),
                "finish_reason": choice.get("finish_reason", ""),
            }


# 模块级单例，供整个应用共享同一个 LLMClient 实例
llm_client = LLMClient()
