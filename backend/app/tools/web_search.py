"""Web Search Tool using DuckDuckGo - No API key required"""
import httpx
from typing import List, Dict, Any
import re
from urllib.parse import quote_plus
import asyncio


class WebSearchTool:
    """Free web search using DuckDuckGo"""
    
    def __init__(self):
        self.base_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search DuckDuckGo and return results
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.post(
                    self.base_url,
                    data={"q": query, "b": ""},
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    return [{"error": f"Search failed with status {response.status_code}"}]
                
                html = response.text
                results = self._parse_results(html, max_results)
                return results
                
        except Exception as e:
            return [{"error": f"Search error: {str(e)}"}]
    
    def _parse_results(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results"""
        results = []
        
        # Find all result blocks
        result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>.*?<a class="result__snippet"[^>]*>(.+?)</a>'
        matches = re.findall(result_pattern, html, re.DOTALL)
        
        for i, (url, title, snippet) in enumerate(matches[:max_results]):
            # Clean HTML tags
            title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            
            # Decode URL
            if url.startswith("//duckduckgo.com/l/?uddg="):
                url_match = re.search(r'uddg=([^&]+)', url)
                if url_match:
                    from urllib.parse import unquote
                    url = unquote(url_match.group(1))
            
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "position": i + 1
            })
        
        return results
    
    async def search_and_summarize(self, query: str, max_results: int = 5) -> str:
        """
        Search and return formatted text summary
        
        Args:
            query: Search query
            max_results: Number of results
            
        Returns:
            Formatted string with search results
        """
        results = await self.search(query, max_results)
        
        if not results:
            return "No search results found."
        
        if "error" in results[0]:
            return f"Search failed: {results[0]['error']}"
        
        output = f"🔍 Web Search Results for: {query}\n\n"
        for r in results:
            output += f"**{r['position']}. {r['title']}**\n"
            output += f"   {r['snippet']}\n"
            output += f"   🔗 {r['url']}\n\n"
        
        return output


# Alternative: Use DuckDuckGo API directly (more reliable)
class DuckDuckGoSearch:
    """DuckDuckGo Instant Answer API"""
    
    def __init__(self):
        self.api_url = "https://api.duckduckgo.com/"
    
    async def instant_answer(self, query: str) -> Dict[str, Any]:
        """Get instant answer from DuckDuckGo"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.api_url,
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "abstract": data.get("Abstract", ""),
                        "abstract_source": data.get("AbstractSource", ""),
                        "abstract_url": data.get("AbstractURL", ""),
                        "answer": data.get("Answer", ""),
                        "definition": data.get("Definition", ""),
                        "related_topics": [
                            {"text": t.get("Text", ""), "url": t.get("FirstURL", "")}
                            for t in data.get("RelatedTopics", [])[:5]
                            if isinstance(t, dict) and "Text" in t
                        ]
                    }
                return {"error": f"API returned status {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}


# Test function
async def test_search():
    tool = WebSearchTool()
    results = await tool.search("Python programming tutorial", 3)
    print(results)
    
    summary = await tool.search_and_summarize("latest AI news 2024", 3)
    print(summary)


if __name__ == "__main__":
    asyncio.run(test_search())
