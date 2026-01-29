"""Configuration management for ClawdBot Hub"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    huggingface_api_key: str = os.getenv("HUGGINGFACE_API_KEY", "")
    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    bytez_api_key: str = os.getenv("BYTEZ_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    cerebras_api_key: str = os.getenv("CEREBRAS_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Model defaults
    default_model: str = "auto"  # Auto-route to best model

    class Config:
        env_file = ".env"


settings = Settings()


# Available providers and their models
PROVIDERS = {
    "groq": {
        "name": "Groq",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "strengths": ["ultra-fast", "llama", "mixtral", "free-tier"]
    },
    "cerebras": {
        "name": "Cerebras",
        "models": ["llama3.1-8b", "llama3.1-70b"],
        "strengths": ["fast", "llama", "free-tier"]
    },
    "deepseek": {
        "name": "DeepSeek",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "strengths": ["reasoning", "coding", "math", "cheap"]
    },
    "openrouter": {
        "name": "OpenRouter",
        "models": ["liquid/lfm-2.5-1.2b-instruct:free", "arcee-ai/trinity-large-preview:free"],
        "strengths": ["multi-model", "100+ models", "free-tier"]
    },
    "bytez": {
        "name": "Bytez",
        "models": ["Qwen/Qwen3-4B", "mistralai/Mistral-7B-Instruct-v0.3"],
        "strengths": ["multi-model", "fast", "affordable"]
    },
    "claude": {
        "name": "Anthropic Claude",
        "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "strengths": ["reasoning", "analysis", "coding", "writing", "math"]
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
        "strengths": ["general", "coding", "creative", "conversation"]
    },
    "gemini": {
        "name": "Google Gemini",
        "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "strengths": ["multimodal", "research", "factual"]
    },
    "huggingface": {
        "name": "HuggingFace",
        "models": ["meta-llama/Llama-2-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
        "strengths": ["specialized", "open-source", "customizable"]
    },
    "perplexity": {
        "name": "Perplexity",
        "models": ["pplx-70b-online", "pplx-7b-online"],
        "strengths": ["search", "real-time", "citations", "research"]
    }
}


# Query categories for routing
QUERY_CATEGORIES = {
    "coding": ["code", "programming", "debug", "function", "api", "javascript", "python", "error", "bug"],
    "research": ["search", "find", "latest", "news", "current", "today", "recent"],
    "creative": ["write", "story", "poem", "creative", "imagine", "fiction"],
    "analysis": ["analyze", "explain", "why", "how", "compare", "evaluate"],
    "math": ["calculate", "math", "equation", "solve", "formula", "statistics"],
    "health": ["health", "medical", "symptom", "disease", "medicine", "doctor"],
    "business": ["business", "marketing", "sales", "strategy", "revenue", "startup"],
    "general": []  # Default fallback
}
