"""HuggingFace provider - Access to thousands of models"""
import httpx
from typing import AsyncGenerator
from app.providers.base import BaseProvider, Message, ChatResponse


class HuggingFaceProvider(BaseProvider):
    """HuggingFace Inference API integration"""
    
    provider_name = "huggingface"
    default_model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    api_base = "https://router.huggingface.co/hf-inference/models"
    
    # Popular models for different tasks
    SPECIALIZED_MODELS = {
        "chat": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "code": "codellama/CodeLlama-34b-Instruct-hf",
        "summarization": "facebook/bart-large-cnn",
        "translation": "Helsinki-NLP/opus-mt-en-de",
        "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "qa": "deepset/roberta-base-squad2"
    }
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    def _format_prompt(self, messages: list[Message]) -> str:
        """Format messages into a single prompt for HuggingFace models"""
        prompt_parts = []
        for msg in messages:
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            else:
                prompt_parts.append(f"Assistant: {msg.content}")
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    async def chat(self, messages: list[Message], model: str = None) -> ChatResponse:
        """Send chat completion to HuggingFace"""
        if not self.is_available():
            raise ValueError("HuggingFace provider not configured")
        
        model = model or self.default_model
        prompt = self._format_prompt(messages)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/{model}",
                headers=self._headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 2048,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"HuggingFace API error: {response.text}")
            
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list):
                content = result[0].get("generated_text", "")
            else:
                content = result.get("generated_text", str(result))
            
            return ChatResponse(
                content=content.strip(),
                provider=self.provider_name,
                model=model,
                tokens_used=None
            )
    
    async def stream_chat(self, messages: list[Message], model: str = None) -> AsyncGenerator[str, None]:
        """Stream chat - HuggingFace doesn't support streaming well, so we simulate"""
        response = await self.chat(messages, model)
        # Simulate streaming by yielding chunks
        words = response.content.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
    
    def get_model_for_task(self, task: str) -> str:
        """Get specialized model for a specific task"""
        return self.SPECIALIZED_MODELS.get(task, self.default_model)
