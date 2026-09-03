"""Job posting search tool."""

from memory.schemas import SearchResult, SourceType
from tools.web_search import search_web


def search_jobs(company: str, role: str = "AI engineer") -> list[SearchResult]:
    query = f"{company} careers {role} job openings"
    results = search_web(query, max_results=3)
    for result in results:
        result.source_type = SourceType.JOB_POSTING
    return results
