"""Web search tools"""

import httpx
from typing import Optional, List, Dict


class TavilySearchTool:
    """Tavily AI-native search integration"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Execute search query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "max_results": max_results,
                    "include_domains": include_domains or [],
                    "exclude_domains": exclude_domains or [],
                },
                timeout=30.0,
            )
            data = response.json()
            return [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "content": r["content"],
                    "score": r.get("score", 0),
                    "published_date": r.get("published_date"),
                }
                for r in data.get("results", [])
            ]


class BraveSearchTool:
    """Brave Search fallback"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1"

    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Execute Brave search"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/web/search",
                params={"q": query, "count": max_results},
                headers={"X-Subscription-Token": self.api_key},
                timeout=30.0,
            )
            data = response.json()
            return [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "content": r.get("description", ""),
                    "score": r.get("relevance_score", 0),
                }
                for r in data.get("web", {}).get("results", [])
            ]


class GeminiSearchTool:
    """Google Gemini-based search fallback using grounding with Google Search"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Execute search using Gemini's grounded search capability"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            
            # Use Gemini with search grounding
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                tools='google_search_retrieval'
            )
            
            response = await model.generate_content_async(
                f"Search the web for current information about: {query}\n\n"
                f"Return the top {max_results} most relevant results with their titles, URLs, and key content.",
                generation_config={"temperature": 0.3}
            )
            
            # Parse the response into structured results
            content = response.text if response.text else ""
            
            # Try to extract grounding metadata if available
            results = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding = candidate.grounding_metadata
                    if hasattr(grounding, 'grounding_chunks'):
                        for i, chunk in enumerate(grounding.grounding_chunks[:max_results]):
                            results.append({
                                "title": getattr(chunk.web, 'title', f'Result {i+1}') if hasattr(chunk, 'web') else f'Result {i+1}',
                                "url": getattr(chunk.web, 'uri', '') if hasattr(chunk, 'web') else '',
                                "content": content[:500] if content else '',
                                "score": 1.0 - (i * 0.1),
                            })
            
            # Fallback: if no grounding metadata, use the response as a single result
            if not results and content:
                results.append({
                    "title": f"Search results for: {query}",
                    "url": "",
                    "content": content[:1000],
                    "score": 0.8,
                })
            
            return results
            
        except Exception as e:
            print(f"GeminiSearchTool error: {e}")
            return []

