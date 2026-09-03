"""Document reader for fetching and cleaning web page content."""

from tools.web_search import _fetch_page_content, _classify_source
from memory.schemas import SearchResult


def read_document(url: str, title: str = "") -> SearchResult:
    content = _fetch_page_content(url)
    source_type = _classify_source(url, title or url)

    return SearchResult(
        title=title or url,
        url=url,
        source_name=url.split("/")[2] if "/" in url else "web",
        snippet=content[:500],
        content=content,
        source_type=source_type,
    )
