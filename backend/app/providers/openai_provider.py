"""OpenAI GPT provider"""
from openai import AsyncOpenAI
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class OpenAIProvider(BaseProvider):
    """OpenAI API integration"""
    
    provider_name = "openai"
    default_model = "gpt-3.5-turbo"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        if self.is_available():
            self._client = AsyncOpenAI(api_key=api_key)
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to OpenAI"""
        if not self._client:
            raise ValueError("OpenAI provider not configured")
        
        model = model or self.default_model
        
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = await self._client.chat.completions.create(
            model=model,
            messages=openai_messages,
            max_tokens=4096
        )
        
        return ChatResponse(
            content=response.choices[0].message.content,
            provider=self.provider_name,
            model=model,
            tokens_used=response.usage.total_tokens if response.usage else None
        )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat completion from OpenAI"""
        if not self._client:
            raise ValueError("OpenAI provider not configured")
        
        model = model or self.default_model
        
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        stream = await self._client.chat.completions.create(
            model=model,
            messages=openai_messages,
            max_tokens=4096,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
