"""Facade for agent code to call MCP tools."""

from __future__ import annotations

import json
from typing import Any, Optional

from config import settings
from agent_mcp.client import get_mcp_client
from memory.database import CompetitiveIntelligenceDB
from memory.schemas import Alert, CompanyScore, ExtractedFact
from tools.web_search import search_web as direct_search_web


def search_web_mcp(query: str, max_results: Optional[int] = None) -> list[dict[str, Any]]:
    """Search the web via MCP search server or direct fallback."""
    if not settings.use_mcp:
        results = direct_search_web(query, max_results=max_results)
        return [result.model_dump() for result in results]

    client = get_mcp_client()
    payload = client.call_tool(
        "search",
        "search_web_tool",
        {"query": query, "max_results": max_results or settings.max_search_results},
    )
    return payload if isinstance(payload, list) else []


def get_previous_findings_mcp(
    company: str,
    category: Optional[str] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Load previous findings via MCP memory server or direct fallback."""
    if not settings.use_mcp:
        db = CompetitiveIntelligenceDB()
        return db.get_previous_findings(company, category=category, limit=limit)

    client = get_mcp_client()
    payload = client.call_tool(
        "memory",
        "get_previous_findings",
        {
            "company": company,
            "category": category or "",
            "limit": limit,
        },
    )
    return payload if isinstance(payload, list) else []


def list_research_runs_mcp(limit: int = 10) -> list[dict[str, Any]]:
    """List recent research runs via MCP or direct DB access."""
    if not settings.use_mcp:
        db = CompetitiveIntelligenceDB()
        with db._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, research_topic, industry, status, created_at
                FROM research_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    client = get_mcp_client()
    payload = client.call_tool("memory", "list_research_runs", {"limit": limit})
    return payload if isinstance(payload, list) else []


def save_research_run_mcp(state: dict[str, Any]) -> dict[str, Any]:
    """Persist a research run via MCP memory server or direct fallback."""
    if not settings.use_mcp:
        db = CompetitiveIntelligenceDB()
        industry = state.get("industry", "")
        companies = state.get("companies", [])
        categories = state.get("categories", [])
        date_range = state.get("date_range", {})

        company_ids: dict[str, int] = {}
        for company in companies:
            company_ids[company] = db.upsert_company(company, industry)

        run_id = state.get("run_id")
        if not run_id:
            run_id = db.create_research_run(
                research_topic=f"{industry}: {', '.join(companies)}",
                industry=industry,
                categories=categories,
                start_date=date_range.get("start", ""),
                end_date=date_range.get("end", ""),
            )

        for finding_dict in state.get("findings", []):
            company = finding_dict.get("company", "")
            if company in company_ids:
                fact = ExtractedFact.model_validate(finding_dict)
                db.save_finding(run_id, company_ids[company], fact)

        for score_dict in state.get("scorecard", []):
            company = score_dict.get("company", "")
            if company in company_ids:
                score = CompanyScore.model_validate(score_dict)
                db.save_score(run_id, company_ids[company], score)

        for alert_dict in state.get("alerts", []):
            company = alert_dict.get("company", "")
            if company in company_ids:
                alert = Alert.model_validate(alert_dict)
                db.save_alert(company_ids[company], alert, run_id)

        db.complete_research_run(run_id)
        return {"run_id": run_id, "company_ids": company_ids}

    client = get_mcp_client()
    payload = client.call_tool(
        "memory",
        "persist_research_run",
        {"state_json": json.dumps(state, default=str)},
    )
    return payload if isinstance(payload, dict) else {}
