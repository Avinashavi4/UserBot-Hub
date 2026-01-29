"""
Web Search Service
Provides real-time web search capabilities using DuckDuckGo
"""
from typing import List, Dict, Any, Optional

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


class WebSearchService:
    """Service for web search using DuckDuckGo"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        region: str = "wt-wt"
    ) -> Dict[str, Any]:
        """
        Search the web for information
        
        Args:
            query: Search query
            max_results: Maximum number of results
            region: Search region (wt-wt = worldwide)
            
        Returns:
            Dict with search results
        """
        try:
            results = list(self.ddgs.text(
                query, 
                max_results=max_results,
                region=region
            ))
            
            formatted_results = []
            context_parts = []
            
            for r in results:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
                context_parts.append(f"**{r.get('title', '')}**\n{r.get('body', '')}")
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "context": "\n\n".join(context_parts)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }
    
    async def news_search(
        self, 
        query: str, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search for news articles"""
        try:
            results = list(self.ddgs.news(query, max_results=max_results))
            
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "date": r.get("date", ""),
                    "source": r.get("source", "")
                })
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }


# Global instance
web_search_service = WebSearchService()
