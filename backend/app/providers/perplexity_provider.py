"""Perplexity provider - Real-time search and research"""
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class PerplexityProvider(BaseProvider):
    """Perplexity API integration - Best for real-time search and research"""
    
    provider_name = "perplexity"
    default_model = "pplx-70b-online"
    api_base = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to Perplexity"""
        if not self.is_available():
            raise ValueError("Perplexity provider not configured")
        
        model = model or self.default_model
        
        # Convert messages to Perplexity format (OpenAI-compatible)
        pplx_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_base,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": pplx_messages,
                    "max_tokens": 4096
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Perplexity API error: {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return ChatResponse(
                content=content,
                provider=self.provider_name,
                model=model,
                tokens_used=result.get("usage", {}).get("total_tokens")
            )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat completion from Perplexity"""
        if not self.is_available():
            raise ValueError("Perplexity provider not configured")
        
        model = model or self.default_model
        
        pplx_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                self.api_base,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": pplx_messages,
                    "max_tokens": 4096,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            import json
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
