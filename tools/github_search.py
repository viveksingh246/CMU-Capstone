"""GitHub search tool."""

from memory.schemas import SearchResult, SourceType
from tools.web_search import search_web


def search_github(company: str, topic: str = "open source") -> list[SearchResult]:
    query = f"{company} {topic} site:github.com"
    results = search_web(query, max_results=3)
    for result in results:
        result.source_type = SourceType.GITHUB
    return results
