"""Web content fetching"""

import httpx
from typing import Dict, Optional


class WebFetchTool:
    """Fetch and extract content from URLs"""

    async def fetch(
        self, url: str, extract_mode: str = "text"
    ) -> Dict[str, str]:
        """Extract content from a specific URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                content = response.text

                # Simple text extraction (in production, use BeautifulSoup or similar)
                if extract_mode == "text":
                    # Basic HTML stripping
                    import re

                    # Remove script and style tags
                    content = re.sub(
                        r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL
                    )
                    content = re.sub(
                        r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL
                    )
                    # Remove HTML tags
                    content = re.sub(r"<[^>]+>", " ", content)
                    # Clean up whitespace
                    content = " ".join(content.split())

                return {
                    "url": url,
                    "content": content[:10000],  # Limit content size
                    "status_code": response.status_code,
                }
        except Exception as e:
            return {
                "url": url,
                "content": "",
                "error": str(e),
                "status_code": 0,
            }

