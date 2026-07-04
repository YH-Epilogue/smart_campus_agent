"""
LLM Client: 统一大模型接口，支持 Mock / Ollama / DeepSeek 切换
"""
import json
import httpx
from ..core.config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    async def chat_stream(self, prompt: str, context: str = "", history: list[dict] = None):
        """流式输出，返回 async generator"""
        if self.provider == "mock":
            async for chunk in self._mock_stream(prompt, context, history):
                yield chunk
        elif self.provider == "ollama":
            async for chunk in self._ollama_stream(prompt, context, history):
                yield chunk
        elif self.provider == "deepseek":
            async for chunk in self._deepseek_stream(prompt, context, history):
                yield chunk
        else:
            async for chunk in self._api_stream(prompt, context, history):
                yield chunk

    def _build_messages(self, prompt: str, context: str = "", history: list[dict] = None) -> list[dict]:
        """构建消息列表，包含系统提示、历史对话、当前问题"""
        system_msg = "你是一个校园智能助手，基于知识库回答问题。请用中文回答。"
        if context:
            system_msg += f"\n\n以下是从知识库检索到的相关信息：\n{context}"

        messages = [{"role": "system", "content": system_msg}]

        # Add conversation history
        if history:
            messages.extend(history)

        # Add current question
        messages.append({"role": "user", "content": prompt})

        return messages

    async def _mock_stream(self, prompt: str, context: str, history: list[dict] = None):
        """Mock 模式：拼接返回，用于开发调试"""
        if context:
            answer = f"根据知识库检索到以下相关内容：\n\n{context[:200]}\n\n基于以上信息，回答你的问题：{prompt}"
        else:
            answer = f"[Mock 模式] 收到问题：{prompt}\n\n这是模拟回复，请配置 LLM_PROVIDER 切换到真实模型。"

        for char in answer:
            yield char

    async def _ollama_stream(self, prompt: str, context: str, history: list[dict] = None):
        """Ollama 本地模型流式输出"""
        payload = {
            "model": settings.LLM_MODEL,
            "messages": self._build_messages(prompt, context, history),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{settings.LLM_BASE_URL}/api/chat",
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

    async def _deepseek_stream(self, prompt: str, context: str, history: list[dict] = None):
        """DeepSeek API 流式输出"""
        payload = {
            "model": settings.LLM_MODEL,
            "messages": self._build_messages(prompt, context, history),
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{settings.LLM_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]

    async def _api_stream(self, prompt: str, context: str, history: list[dict] = None):
        """兼容 OpenAI 格式的通用云端 API"""
        payload = {
            "model": settings.LLM_MODEL,
            "messages": self._build_messages(prompt, context, history),
            "stream": True,
        }

        headers = {}
        if settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{settings.LLM_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]


llm_client = LLMClient()
