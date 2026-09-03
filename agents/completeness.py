"""Research completeness checker."""

from typing import Any

from workflows.state import ResearchState

MIN_FINDINGS_PER_CATEGORY = 2


def check_completeness(state: ResearchState) -> dict[str, Any]:
    """Assess whether research is sufficient for each category."""
    categories = state.get("categories", [])
    companies = state.get("companies", [])
    findings = state.get("findings", [])

    category_completeness: dict[str, str] = {}
    missing_information: list[str] = []
    additional_queries: list[str] = []

    for category in categories:
        category_findings = [f for f in findings if f.get("category", "").lower() == category.lower()]
        companies_covered = {f.get("company") for f in category_findings}

        if len(category_findings) >= MIN_FINDINGS_PER_CATEGORY * len(companies):
            category_completeness[category] = "complete"
        elif len(category_findings) > 0:
            category_completeness[category] = "insufficient_evidence"
            missing_information.append(category)
            for company in companies:
                if company not in companies_covered:
                    additional_queries.append(f"{company} {category} official documentation")
                    additional_queries.append(f"{company} {category} recent news")
        else:
            category_completeness[category] = "incomplete"
            missing_information.append(category)
            for company in companies:
                additional_queries.append(f"{company} {category} official site")
                additional_queries.append(f"{company} {category} product features 2026")

    iteration = state.get("iteration_count", 0)
    max_iterations = 3

    if missing_information and iteration < max_iterations:
        existing_queries = set(state.get("search_queries", []))
        new_queries = [q for q in additional_queries if q not in existing_queries]
        return {
            "category_completeness": category_completeness,
            "missing_information": missing_information,
            "search_queries": list(existing_queries) + new_queries,
            "iteration_count": iteration + 1,
            "status_message": f"Research incomplete for: {', '.join(missing_information)}. Iteration {iteration + 1}",
        }

    return {
        "category_completeness": category_completeness,
        "missing_information": missing_information if iteration >= max_iterations else [],
        "status_message": "Research completeness check passed" if not missing_information else "Max iterations reached",
    }


def should_continue_research(state: ResearchState) -> str:
    """Routing function: continue searching or proceed to analysis."""
    missing = state.get("missing_information", [])
    iteration = state.get("iteration_count", 0)
    if missing and iteration < 3:
        return "search_more"
    return "analyze"
