"""Bytez provider - Access to 100,000+ models"""
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class BytezProvider(BaseProvider):
    """Bytez API integration - 100,000+ models"""
    
    provider_name = "bytez"
    default_model = "Qwen/Qwen3-4B"
    api_base = "https://api.bytez.com/models/v2"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        } if api_key else {}
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to Bytez"""
        if not self.is_available():
            raise ValueError("Bytez provider not configured")
        
        model = model or self.default_model
        
        # Convert messages to Bytez format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/{model}",
                headers=self._headers,
                json={
                    "messages": api_messages,
                    "params": {
                        "max_new_tokens": 2048,
                        "temperature": 0.7
                    }
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Bytez API error: {response.text}")
            
            result = response.json()
            
            # Check for errors
            if result.get("error"):
                raise ValueError(f"Bytez error: {result['error']}")
            
            # Extract content
            output = result.get("output", "")
            if isinstance(output, dict):
                content = output.get("content", str(output))
            elif isinstance(output, list):
                content = output[0] if output else ""
            else:
                content = str(output)
            
            # Clean up thinking tokens if present
            if "</think>" in content:
                content = content.split("</think>")[-1]
            
            return ChatResponse(
                content=content.strip(),
                provider=self.provider_name,
                model=model,
                tokens_used=None
            )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat from Bytez"""
        if not self.is_available():
            raise ValueError("Bytez provider not configured")
        
        model = model or self.default_model
        
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/{model}",
                headers=self._headers,
                json={
                    "messages": api_messages,
                    "stream": True,
                    "params": {
                        "max_new_tokens": 2048
                    }
                }
            ) as response:
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk
