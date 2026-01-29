"""Intelligent Query Router - Routes queries to the best AI model"""
from typing import Tuple, List
from app.config import PROVIDERS, QUERY_CATEGORIES


class QueryRouter:
    """Routes user queries to the most appropriate AI model"""

    # Model preferences by category - Groq is fastest, DeepSeek for reasoning, Cerebras for general
    CATEGORY_MODEL_MAP = {
        "coding": ["groq", "deepseek", "openrouter", "cerebras", "bytez"],
        "research": ["deepseek", "groq", "openrouter", "cerebras", "perplexity"],
        "creative": ["groq", "cerebras", "openrouter", "bytez", "gemini"],
        "analysis": ["deepseek", "groq", "openrouter", "cerebras", "bytez"],
        "math": ["deepseek", "groq", "openrouter", "cerebras", "bytez"],
        "health": ["groq", "deepseek", "openrouter", "cerebras", "perplexity"],
        "business": ["groq", "deepseek", "openrouter", "cerebras", "bytez"],
        "general": ["groq", "cerebras", "openrouter", "deepseek", "bytez"]
    }

    def __init__(self, available_providers: List[str]):
        """Initialize router with list of providers that have valid API keys"""
        self.available_providers = available_providers

    def classify_query(self, query: str) -> str:
        """Classify the query into a category"""
        query_lower = query.lower()

        # Score each category
        scores = {}
        for category, keywords in QUERY_CATEGORIES.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            scores[category] = score

        # Get highest scoring category (default to general if no matches)
        best_category = max(scores, key=scores.get)
        if scores[best_category] == 0:
            best_category = "general"

        return best_category

    def route(self, query: str, preferred_provider: str = None) -> Tuple[str, str, str]:
        """
        Route query to best provider and model

        Returns:
            Tuple of (provider, model, category)
        """
        # If user specified a provider, use it
        if preferred_provider and preferred_provider in self.available_providers:
            provider = preferred_provider
            model = PROVIDERS[provider]["models"][0]
            category = self.classify_query(query)
            return provider, model, category

        # Classify and route automatically
        category = self.classify_query(query)
        preferred_providers = self.CATEGORY_MODEL_MAP.get(category, ["openrouter", "bytez"])

        # Find first available provider
        for provider in preferred_providers:
            if provider in self.available_providers:
                model = PROVIDERS[provider]["models"][0]
                return provider, model, category

        # Fallback to any available provider
        if self.available_providers:
            provider = self.available_providers[0]
            model = PROVIDERS[provider]["models"][0]
            return provider, model, category

        raise ValueError("No AI providers available. Please configure at least one API key.")

    def get_routing_explanation(self, query: str, provider: str, category: str) -> str:
        """Explain why this provider was chosen"""
        provider_info = PROVIDERS.get(provider, {})
        strengths = provider_info.get("strengths", [])

        return f"Query classified as '{category}'. Routed to {provider_info.get('name', provider)} (strengths: {', '.join(strengths[:3])})"


