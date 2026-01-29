"""Google Gemini provider using REST API"""
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class GeminiProvider(BaseProvider):
    """Google Gemini API integration via REST"""
    
    provider_name = "gemini"
    default_model = "gemini-2.0-flash"
    api_base = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to Gemini"""
        if not self.is_available():
            raise ValueError("Gemini provider not configured")
        
        model_name = model or self.default_model
        
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        url = f"{self.api_base}/{model_name}:generateContent?key={self.api_key}"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={"contents": contents},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Gemini API error: {response.text}")
            
            result = response.json()
            
            # Extract text from response
            try:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                content = str(result)
            
            return ChatResponse(
                content=content,
                provider=self.provider_name,
                model=model_name,
                tokens_used=None
            )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat - simulate by returning full response in chunks"""
        response = await self.chat(messages, model)
        words = response.content.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
