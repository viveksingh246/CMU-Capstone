"""Tests for web search functionality."""

from tools.web_search import _filter_results, _classify_source, search_web
from memory.schemas import SearchResult, SourceType


def test_classify_github_source():
    assert _classify_source("https://github.com/org/repo", "Repo") == SourceType.GITHUB


def test_classify_news_source():
    assert _classify_source("https://techcrunch.com/article", "Article") == SourceType.NEWS


def test_filter_removes_duplicate_urls():
    results = [
        SearchResult(
            title="A",
            url="https://example.com/a",
            source_name="test",
            snippet="Some content here that is long enough",
        ),
        SearchResult(
            title="B",
            url="https://example.com/a",
            source_name="test",
            snippet="Duplicate URL content here",
        ),
    ]
    filtered = _filter_results(results)
    assert len(filtered) == 1


def test_search_fallback_without_api_key():
    results = search_web("Snowflake pricing", max_results=2)
    assert len(results) <= 2
    assert all(isinstance(r, SearchResult) for r in results)
