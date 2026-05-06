"""Search client abstraction for ResearcherAgent."""

from typing import Any

import requests

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client with multiple backend support."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._tavily_key = self._settings.tavily_api_key

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Tries Tavily API first if available, falls back to DuckDuckGo HTML scrape.
        """
        if self._tavily_key:
            return self._search_tavily(query, max_results)
        return self._search_ddg(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        """Search using Tavily API."""
        headers = {
            "Content-Type": "application/json",
            "api-key": self._tavily_key,
        }
        payload: dict[str, Any] = {
            "query": query,
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        results: list[dict[str, Any]] = data.get("results", [])
        return [
            SourceDocument(
                title=r.get("title", ""),
                url=r.get("url"),
                snippet=r.get("content", "")[:500],
                metadata={"score": r.get("score", 0)},
            )
            for r in results
        ]

    def _search_ddg(self, query: str, max_results: int) -> list[SourceDocument]:
        """Fallback search using DuckDuckGo HTML."""
        params: dict[str, Any] = {
            "q": query,
            "kl": "en-us",
            "vaes": "1",
            "msg": "1",
            "ad": "1",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)",
        }
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        sources: list[SourceDocument] = []
        for line in response.text.split("\n"):
            if 'class="result__title"' in line or 'class="result__a"' in line:
                title_start = line.find(">") + 1
                title_end = line.find("<", title_start)
                if title_start > 0 and title_end > title_start:
                    title = line[title_start:title_end].strip()
                    link_start = line.find('href="') + 6
                    link_end = line.find('"', link_start)
                    if link_start > 5 and link_end > link_start:
                        url = line[link_start:link_end]
                        sources.append(
                            SourceDocument(
                                title=title,
                                url=url,
                                snippet=f"Search result for: {query}",
                            )
                        )
            if len(sources) >= max_results:
                break

        if not sources:
            sources = [
                SourceDocument(
                    title=f"Placeholder: {query}",
                    url=None,
                    snippet=f"Search returned no results for query: {query}",
                )
            ]
        return sources
