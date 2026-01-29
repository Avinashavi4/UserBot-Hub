"""Cerebras provider - Fast inference on Cerebras hardware"""
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class CerebrasProvider(BaseProvider):
    """Cerebras API integration - Fast AI inference"""
    
    provider_name = "cerebras"
    default_model = "llama3.1-8b"
    api_base = "https://api.cerebras.ai/v1"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        } if api_key else {}
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to Cerebras"""
        if not self.is_available():
            raise ValueError("Cerebras provider not configured")
        
        model = model or self.default_model
        
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers=self._headers,
                json={
                    "model": model,
                    "messages": api_messages,
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Cerebras API error: {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return ChatResponse(
                content=content.strip(),
                provider=self.provider_name,
                model=model,
                tokens_used=result.get("usage", {}).get("total_tokens")
            )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat from Cerebras"""
        if not self.is_available():
            raise ValueError("Cerebras provider not configured")
        
        model = model or self.default_model
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers=self._headers,
                json={"model": model, "messages": api_messages, "stream": True}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line[6:] != "[DONE]":
                        import json
                        try:
                            chunk = json.loads(line[6:])
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except:
                            pass
