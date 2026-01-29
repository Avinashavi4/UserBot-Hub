"""Anthropic Claude provider"""
import anthropic
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class ClaudeProvider(BaseProvider):
    """Anthropic Claude API integration"""
    
    provider_name = "claude"
    default_model = "claude-3-sonnet-20240229"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        if self.is_available():
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to Claude"""
        if not self._client:
            raise ValueError("Claude provider not configured")
        
        model = model or self.default_model
        
        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        response = await self._client.messages.create(
            model=model,
            max_tokens=4096,
            messages=anthropic_messages
        )
        
        return ChatResponse(
            content=response.content[0].text,
            provider=self.provider_name,
            model=model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens
        )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat completion from Claude"""
        if not self._client:
            raise ValueError("Claude provider not configured")
        
        model = model or self.default_model
        
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        async with self._client.messages.stream(
            model=model,
            max_tokens=4096,
            messages=anthropic_messages
        ) as stream:
            async for text in stream.text_stream:
                yield text
