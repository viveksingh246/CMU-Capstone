"""Research collection agent - searches sources and gathers documents."""

from typing import Any

from tools.mcp_tools import search_web_mcp
from workflows.state import ResearchState


def collect_research(state: ResearchState) -> dict[str, Any]:
    """Execute pending search queries and collect documents."""
    queries = state.get("search_queries", [])
    completed = set(state.get("completed_queries", []))
    pending = [q for q in queries if q not in completed]

    if not pending:
        return {"status_message": "No pending search queries"}

    documents = list(state.get("documents", []))
    seen_urls = {doc["url"] for doc in documents}
    new_completed: list[str] = []
    errors = list(state.get("errors", []))

    # Process up to 5 queries per iteration to manage API costs
    for query in pending[:5]:
        try:
            results = search_web_mcp(query, max_results=3)
            for result in results:
                if result["url"] not in seen_urls:
                    documents.append(result)
                    seen_urls.add(result["url"])
            new_completed.append(query)
        except Exception as exc:
            errors.append(f"Search failed for '{query}': {exc}")

    return {
        "documents": documents,
        "completed_queries": list(completed) + new_completed,
        "errors": errors,
        "status_message": f"Collected {len(documents)} documents ({len(new_completed)} queries executed)",
    }
