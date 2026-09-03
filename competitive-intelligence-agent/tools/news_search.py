"""News search tool - wraps web search with news-focused queries."""

from memory.schemas import SearchResult
from tools.web_search import search_web


def search_news(company: str, topic: str = "", days: int = 90) -> list[SearchResult]:
    query = f"{company} {topic} news announcements last {days} days".strip()
    return search_web(query, max_results=5)
