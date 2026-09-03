"""Research planning agent."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import get_llm, load_prompt
from memory.schemas import ResearchPlan, ResearchRequest
from workflows.state import ResearchState


def create_research_plan(state: ResearchState) -> dict[str, Any]:
    """Transform user request into a structured research plan."""
    request = ResearchRequest(
        industry=state["industry"],
        companies=state["companies"],
        categories=state["categories"],
        date_range_days=state.get("date_range_days", 90),
        geographic_market=state.get("geographic_market", "Global"),
        report_depth=state.get("report_depth", "standard"),
        include_historical_comparison=state.get("include_historical_comparison", True),
        generate_alerts=state.get("generate_alerts", True),
    )

    system_prompt = load_prompt("planner")
    user_content = f"""
Industry: {request.industry}
Companies: {', '.join(request.companies)}
Categories: {', '.join(request.categories)}
Research period: last {request.date_range_days} days
Geographic market: {request.geographic_market}
Report depth: {request.report_depth}

Create a detailed research plan as JSON with this structure:
{{
  "companies": [...],
  "categories": [...],
  "date_range": {{"start": "...", "end": "..."}},
  "tasks": [
    {{
      "category": "...",
      "questions": [...],
      "preferred_sources": [...],
      "search_queries": [...],
      "evidence_required": "...",
      "completion_criteria": "..."
    }}
  ]
}}
"""

    llm = get_llm()
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    )

    content = response.content
    if isinstance(content, list):
        content = "".join(str(part) for part in content)

    try:
        # Extract JSON from response (handle markdown code blocks)
        text = str(content).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        plan_data = json.loads(text)
        plan = ResearchPlan.model_validate(plan_data)
    except (json.JSONDecodeError, ValueError):
        plan = _fallback_plan(request)

    search_queries: list[str] = []
    for task in plan.tasks:
        search_queries.extend(task.search_queries)

    return {
        "research_plan": plan.model_dump(),
        "search_queries": search_queries,
        "status_message": f"Created research plan with {len(search_queries)} search queries",
    }


def _fallback_plan(request: ResearchRequest) -> ResearchPlan:
    """Generate a basic plan when LLM parsing fails."""
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=request.date_range_days)

    tasks = []
    for category in request.categories:
        queries = [
            f"{company} {category} official site"
            for company in request.companies
        ] + [
            f"{company} {category} news {request.date_range_days} days"
            for company in request.companies
        ]
        tasks.append(
            {
                "category": category,
                "questions": [f"What is {company}'s {category}?" for company in request.companies],
                "preferred_sources": ["official websites", "news"],
                "search_queries": queries,
                "evidence_required": "At least one credible source per company",
                "completion_criteria": f"Findings for all companies in {category}",
            }
        )

    from memory.schemas import ResearchPlanTask

    return ResearchPlan(
        companies=request.companies,
        categories=request.categories,
        date_range={"start": start.isoformat(), "end": end.isoformat()},
        tasks=[ResearchPlanTask.model_validate(t) for t in tasks],
    )
