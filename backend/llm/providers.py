"""Provider health monitoring"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import httpx

from backend.config import settings


class ProviderStatus:
    """Track provider health and availability"""

    def __init__(self):
        self.providers: Dict[str, Dict] = {}
        self.last_check: Dict[str, datetime] = {}
        self.check_interval = timedelta(minutes=5)

    async def check_all(self) -> Dict[str, Dict]:
        """Check all provider statuses"""

        checks = {
            "ollama": self._check_ollama,
            "anthropic": self._check_anthropic,
            "google": self._check_google,
            "openai": self._check_openai,
            "openrouter": self._check_openrouter,
        }

        results = {}
        for provider, check_fn in checks.items():
            try:
                results[provider] = await check_fn()
            except Exception as e:
                results[provider] = {
                    "available": False,
                    "error": str(e),
                    "models": [],
                }

        return results

    async def _check_ollama(self) -> Dict:
        """Check Ollama local server"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.ollama_base_url}/api/tags", timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {"available": True, "models": models, "type": "local"}
        except Exception:
            pass
        return {"available": False, "models": [], "type": "local"}

    async def _check_anthropic(self) -> Dict:
        """Check Anthropic API"""
        if not settings.anthropic_api_key:
            return {"available": False, "reason": "no_key", "models": []}
        return {
            "available": True,
            "models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
            ],
            "type": "cloud",
        }

    async def _check_google(self) -> Dict:
        """Check Google API"""
        if not settings.google_api_key:
            return {"available": False, "reason": "no_key", "models": []}
        return {
            "available": True,
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "type": "cloud",
        }

    async def _check_openai(self) -> Dict:
        """Check OpenAI API"""
        if not settings.openai_api_key:
            return {"available": False, "reason": "no_key", "models": []}
        return {
            "available": True,
            "models": ["gpt-4o", "gpt-4o-mini"],
            "type": "cloud",
        }

    async def _check_openrouter(self) -> Dict:
        """Check OpenRouter API"""
        if not settings.openrouter_api_key:
            return {"available": False, "reason": "no_key", "models": []}
        return {
            "available": True,
            "models": ["openrouter/anthropic/claude-3-sonnet"],
            "type": "cloud",
        }

