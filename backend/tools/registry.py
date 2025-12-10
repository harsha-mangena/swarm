"""Tool registry"""

from typing import Dict, Any, Callable, Optional
from backend.tools.web_search import TavilySearchTool, BraveSearchTool, GeminiSearchTool
from backend.tools.web_fetch import WebFetchTool
from backend.config import settings


class ToolRegistry:
    """Central registry for all tools"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all available tools"""
        # Web search - with fallback chain
        if settings.tavily_api_key:
            tavily = TavilySearchTool(settings.tavily_api_key)
            self.register("web_search", tavily.search)
            print("✓ Web search: Tavily enabled")
        elif settings.brave_api_key:
            brave = BraveSearchTool(settings.brave_api_key)
            self.register("web_search", brave.search)
            print("✓ Web search: Brave enabled")
        elif settings.google_api_key:
            # Fallback to Gemini-based search when Tavily/Brave not available
            gemini = GeminiSearchTool(settings.google_api_key)
            self.register("web_search", gemini.search)
            print("✓ Web search: Gemini (fallback) enabled")
        else:
            print("⚠ Web search: No API keys configured (TAVILY_API_KEY, BRAVE_API_KEY, or GOOGLE_API_KEY)")

        # Web fetch
        web_fetch = WebFetchTool()
        self.register("fetch_url", web_fetch.fetch)

    def register(self, name: str, func: Callable):
        """Register a tool"""
        self.tools[name] = func

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        func = self.tools[tool_name]
        if callable(func):
            return await func(**params)
        raise ValueError(f"Tool '{tool_name}' is not callable")

    def list_tools(self) -> Dict[str, Dict]:
        """List all available tools with schemas"""
        return {
            "web_search": {
                "description": "Search the web for current information",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5},
                },
            },
            "fetch_url": {
                "description": "Extract content from a specific URL",
                "parameters": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
            },
        }

