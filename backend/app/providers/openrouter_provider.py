"""OpenRouter provider - Access to 100+ AI models through unified API"""
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class OpenRouterProvider(BaseProvider):
    """OpenRouter API integration - 100+ models including Claude, GPT-4, Llama, etc."""
    
    provider_name = "openrouter"
    default_model = "liquid/lfm-2.5-1.2b-instruct:free"
    api_base = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "UserBot Hub"
        } if api_key else {}
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to OpenRouter"""
        if not self.is_available():
            raise ValueError("OpenRouter provider not configured")
        
        model = model or self.default_model
        
        # Convert messages to OpenAI-compatible format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
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
                raise ValueError(f"OpenRouter API error: {response.text}")
            
            result = response.json()
            
            # Extract content from OpenAI-compatible response
            try:
                content = result["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                content = str(result)
            
            return ChatResponse(
                content=content.strip(),
                provider=self.provider_name,
                model=model,
                tokens_used=result.get("usage", {}).get("total_tokens")
            )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat from OpenRouter"""
        if not self.is_available():
            raise ValueError("OpenRouter provider not configured")
        
        model = model or self.default_model
        
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers=self._headers,
                json={
                    "model": model,
                    "messages": api_messages,
                    "max_tokens": 4096,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            import json
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0]["delta"].get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except:
                                pass



