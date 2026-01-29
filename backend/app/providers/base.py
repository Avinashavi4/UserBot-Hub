"""Base provider interface"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message structure"""
    role: str  # "user" or "assistant"
    content: str


class ChatResponse(BaseModel):
    """Response from AI provider"""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    

class BaseProvider(ABC):
    """Abstract base class for AI providers"""
    
    provider_name: str = "base"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    @abstractmethod
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send a chat completion request"""
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream a chat completion response"""
        pass
    
    def is_available(self) -> bool:
        """Check if provider is configured with valid API key"""
        return bool(self.api_key and len(self.api_key) > 10)
