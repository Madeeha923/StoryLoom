from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings


class WikipediaClient:
    """Small async client for pulling public summary data from Wikipedia."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.wikipedia_api_base).rstrip("/")
        self.headers = {"User-Agent": "StoryLoom/0.1 (FastAPI backend)"}

    async def fetch_cultural_summary(self, topic: str) -> dict[str, Any]:
        query = topic.strip()
        if not query:
            return {
                "topic": "",
                "description": "",
                "summary": "",
                "source_url": None,
                "matched_title": None,
                "error": "A topic is required to query Wikipedia.",
            }

        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(headers=self.headers, timeout=timeout) as client:
            try:
                title = await self._search_title(client, query)
                if not title:
                    return {
                        "topic": query,
                        "description": "",
                        "summary": "",
                        "source_url": None,
                        "matched_title": None,
                        "error": "No Wikipedia page matched the requested topic.",
                    }

                summary_response = await client.get(
                    f"{self.base_url}/api/rest_v1/page/summary/{quote(title)}"
                )
                summary_response.raise_for_status()
                data = summary_response.json()
            except httpx.HTTPError as exc:
                return {
                    "topic": query,
                    "description": "",
                    "summary": "",
                    "source_url": None,
                    "matched_title": None,
                    "error": f"Wikipedia lookup failed: {exc}",
                }

        return {
            "topic": query,
            "matched_title": data.get("title"),
            "description": data.get("description", ""),
            "summary": data.get("extract", ""),
            "source_url": data.get("content_urls", {})
            .get("desktop", {})
            .get("page"),
            "error": None,
        }

    async def _search_title(
        self, client: httpx.AsyncClient, query: str
    ) -> str | None:
        response = await client.get(
            f"{self.base_url}/w/api.php",
            params={
                "action": "opensearch",
                "search": query,
                "limit": 1,
                "namespace": 0,
                "format": "json",
            },
        )
        response.raise_for_status()
        data = response.json()
        titles = data[1] if len(data) > 1 else []
        return titles[0] if titles else None
