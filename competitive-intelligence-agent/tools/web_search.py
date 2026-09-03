"""Web search tool with Tavily API and fallback mock data."""

from __future__ import annotations

from datetime import datetime, timedelta
import re

import httpx
from bs4 import BeautifulSoup

from typing import Optional

from config import settings
from memory.schemas import SearchResult, SourceType


def _classify_source(url: str, title: str) -> SourceType:
    url_lower = url.lower()
    title_lower = title.lower()

    if any(x in url_lower for x in [".gov", "sec.gov", "edgar"]):
        return SourceType.REGULATORY_FILING
    if "github.com" in url_lower:
        return SourceType.GITHUB
    if any(x in url_lower for x in ["careers", "jobs", "greenhouse", "lever.co"]):
        return SourceType.JOB_POSTING
    if any(x in url_lower for x in ["docs.", "documentation", "/docs/"]):
        return SourceType.OFFICIAL_DOCUMENTATION
    if any(x in url_lower for x in ["blog.", "/blog/", "newsroom", "press"]):
        return SourceType.OFFICIAL_BLOG
    if "pricing" in url_lower or "pricing" in title_lower:
        return SourceType.OFFICIAL_WEBSITE
    if any(
        x in url_lower
        for x in ["reuters", "bloomberg", "techcrunch", "venturebeat", "wsj", "nytimes"]
    ):
        return SourceType.NEWS
    if any(x in url_lower for x in ["arxiv", "research", "paper"]):
        return SourceType.RESEARCH_PAPER
    return SourceType.OTHER


def _fetch_page_content(url: str, max_chars: int = 3000) -> str:
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(
                url,
                headers={"User-Agent": "CompetitiveIntelligenceBot/1.0"},
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return re.sub(r"\s+", " ", text)[:max_chars]
    except Exception:
        return ""


def search_web(query: str, max_results: Optional[int] = None) -> list[SearchResult]:
    """Search the web using Tavily API, with sample data fallback for demos."""
    max_results = max_results or settings.max_search_results

    if settings.has_tavily_api_key:
        return _search_tavily(query, max_results)

    return _search_fallback(query, max_results)


def _search_tavily(query: str, max_results: int) -> list[SearchResult]:
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(query=query, max_results=max_results, include_raw_content=True)

    results: list[SearchResult] = []
    for item in response.get("results", []):
        url = item.get("url", "")
        title = item.get("title", "")
        source_type = _classify_source(url, title)
        content = item.get("raw_content") or item.get("content", "")
        if not content and url:
            content = _fetch_page_content(url)

        results.append(
            SearchResult(
                title=title,
                url=url,
                source_name=item.get("source", url.split("/")[2] if "/" in url else "web"),
                snippet=item.get("content", "")[:500],
                published_date=item.get("published_date"),
                content=content,
                source_type=source_type,
            )
        )

    return _filter_results(results)


def _search_fallback(query: str, max_results: int) -> list[SearchResult]:
    """Return sample data when no search API key is configured."""
    today = datetime.utcnow().date()
    company = query.split()[0] if query else "Company"

    samples = [
        SearchResult(
            title=f"{company} Product Overview",
            url=f"https://www.{company.lower().replace(' ', '')}.com/products",
            source_name=f"{company} Official",
            snippet=f"{company} offers a comprehensive cloud data platform with AI capabilities.",
            published_date=(today - timedelta(days=5)).isoformat(),
            content=(
                f"{company} provides enterprise data warehousing, analytics, and AI/ML tools. "
                f"Recent features include generative AI assistants, vector search, and "
                f"automated data pipelines. Pricing includes usage-based and subscription tiers."
            ),
            source_type=SourceType.OFFICIAL_WEBSITE,
        ),
        SearchResult(
            title=f"{company} Announces AI Features",
            url=f"https://techcrunch.com/{company.lower()}-ai-announcement",
            source_name="TechCrunch",
            snippet=f"{company} launched new AI capabilities for enterprise customers.",
            published_date=(today - timedelta(days=15)).isoformat(),
            content=(
                f"In a recent announcement, {company} unveiled generative AI features "
                f"including natural language querying, automated insights, and model serving. "
                f"The company also announced partnerships with major cloud providers."
            ),
            source_type=SourceType.NEWS,
        ),
        SearchResult(
            title=f"{company} Pricing",
            url=f"https://www.{company.lower().replace(' ', '')}.com/pricing",
            source_name=f"{company} Official",
            snippet=f"{company} offers pay-as-you-go and enterprise pricing tiers.",
            published_date=(today - timedelta(days=30)).isoformat(),
            content=(
                f"{company} pricing model: Free trial available. Standard tier starts at "
                f"usage-based pricing. Enterprise pricing requires contact with sales. "
                f"Storage and compute are billed separately."
            ),
            source_type=SourceType.OFFICIAL_WEBSITE,
        ),
    ]

    return _filter_results(samples[:max_results])


def _filter_results(results: list[SearchResult]) -> list[SearchResult]:
    """Remove duplicates and rank by credibility."""
    seen_urls: set[str] = set()
    filtered: list[SearchResult] = []

    for result in results:
        if result.url in seen_urls:
            continue
        if len(result.snippet) < 10 and len(result.content) < 50:
            continue
        seen_urls.add(result.url)
        from memory.schemas import SOURCE_CREDIBILITY_SCORES

        result.credibility_score = SOURCE_CREDIBILITY_SCORES.get(result.source_type, 1)
        filtered.append(result)

    filtered.sort(key=lambda r: r.credibility_score, reverse=True)
    return filtered
