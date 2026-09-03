"""MCP server exposing web search and research collection tools."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Ensure project root is importable when run as a script
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_mcp.server import MCPServer
from tools.github_search import search_github
from tools.job_search import search_jobs
from tools.news_search import search_news
from tools.web_search import search_web

search_mcp = MCPServer("ci-search")


@search_mcp.tool(description="Search the web for competitive intelligence sources")
def search_web_tool(query: str, max_results: int = 5) -> list[dict]:
    """Search official sites, news, and documentation for a query."""
    results = search_web(query, max_results=max_results)
    return [result.model_dump() for result in results]


@search_mcp.tool(description="Search recent news and announcements for a company")
def search_news_tool(company: str, topic: str = "", days: int = 90) -> list[dict]:
    """Find recent news articles and press coverage."""
    results = search_news(company, topic=topic, days=days)
    return [result.model_dump() for result in results]


@search_mcp.tool(description="Search GitHub for company open-source activity")
def search_github_tool(company: str, topic: str = "open source") -> list[dict]:
    """Find GitHub repositories and open-source projects."""
    results = search_github(company, topic=topic)
    return [result.model_dump() for result in results]


@search_mcp.tool(description="Search job postings for hiring trend signals")
def search_jobs_tool(company: str, role: str = "AI engineer") -> list[dict]:
    """Find job postings that indicate strategic hiring direction."""
    results = search_jobs(company, role=role)
    return [result.model_dump() for result in results]


def main() -> None:
    search_mcp.run_stdio()


if __name__ == "__main__":
    main()
