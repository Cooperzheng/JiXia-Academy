# src/engine/search.py
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@runtime_checkable
class SearchEngine(Protocol):
    def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        ...


class TavilySearch:
    """使用 Tavily API 搜索，超时 5 秒，失败计数超 3 次后停用。"""

    def __init__(self, api_key: str) -> None:
        from tavily import TavilyClient  # type: ignore[import]
        self._client = TavilyClient(api_key=api_key)
        self._fail_count = 0
        self._disabled = False

    def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        if self._disabled:
            return []
        try:
            response = self._client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
            )
            results = []
            for r in response.get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", "")[:300],
                ))
            self._fail_count = 0
            return results
        except Exception as e:
            self._fail_count += 1
            if self._fail_count >= 3:
                self._disabled = True
                print(f"[search] Tavily 连续失败 3 次，已停用。最后错误：{e}")
            else:
                print(f"[search] Tavily 搜索失败（第 {self._fail_count} 次）：{e}")
            return []


class DuckDuckGoSearch:
    """使用 DuckDuckGo 搜索（无需 API key），失败计数超 3 次后停用。"""

    def __init__(self) -> None:
        self._fail_count = 0
        self._disabled = False

    def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        if self._disabled:
            return []
        try:
            try:
                from ddgs import DDGS  # type: ignore[import]
            except ImportError:
                from duckduckgo_search import DDGS  # type: ignore[import]
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", "")[:300],
                    ))
            self._fail_count = 0
            return results
        except Exception as e:
            self._fail_count += 1
            if self._fail_count >= 3:
                self._disabled = True
                print(f"[search] DuckDuckGo 连续失败 3 次，已停用。最后错误：{e}")
            else:
                print(f"[search] DuckDuckGo 搜索失败（第 {self._fail_count} 次）：{e}")
            return []


def make_search_engine() -> SearchEngine | None:
    """
    根据环境变量决定使用哪个搜索引擎：
    - SEARCH_DISABLED=1  → None
    - TAVILY_API_KEY 存在 → TavilySearch
    - 否则              → DuckDuckGoSearch
    """
    if os.environ.get("SEARCH_DISABLED") == "1":
        return None
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if tavily_key:
        return TavilySearch(api_key=tavily_key)
    return DuckDuckGoSearch()
