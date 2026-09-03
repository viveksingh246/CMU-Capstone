"""MCP server exposing SQLite competitive intelligence memory tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_mcp.server import MCPServer
from memory.database import CompetitiveIntelligenceDB
from memory.schemas import Alert, CompanyScore, ExtractedFact

memory_mcp = MCPServer("ci-memory")


@memory_mcp.tool(description="Load previous findings for a company from long-term memory")
def get_previous_findings(company: str, category: str = "", limit: int = 20) -> list[dict]:
    """Retrieve historical research findings for a company."""
    db = CompetitiveIntelligenceDB()
    category_filter: Optional[str] = category or None
    return db.get_previous_findings(company, category=category_filter, limit=limit)


@memory_mcp.tool(description="Get the latest competitive scorecard for a company")
def get_latest_scores(company: str) -> dict:
    """Return the most recent scorecard entry for a company."""
    db = CompetitiveIntelligenceDB()
    scores = db.get_latest_scores(company)
    return scores or {}


@memory_mcp.tool(description="List recent research runs stored in memory")
def list_research_runs(limit: int = 10) -> list[dict]:
    """Return recent research runs with status and topic."""
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


@memory_mcp.tool(description="Save a structured finding to the memory database")
def save_finding(
    run_id: int,
    company: str,
    industry: str,
    fact_json: str,
) -> dict:
    """Persist a single extracted fact linked to a research run."""
    db = CompetitiveIntelligenceDB()
    company_id = db.upsert_company(company, industry)
    fact_data = json.loads(fact_json)
    fact = ExtractedFact.model_validate(fact_data)
    finding_id = db.save_finding(run_id, company_id, fact)
    return {"finding_id": finding_id, "company_id": company_id}


@memory_mcp.tool(description="Save a company scorecard entry to memory")
def save_score(run_id: int, company: str, industry: str, score_json: str) -> dict:
    """Persist a competitive scorecard for a company."""
    db = CompetitiveIntelligenceDB()
    company_id = db.upsert_company(company, industry)
    score = CompanyScore.model_validate(json.loads(score_json))
    db.save_score(run_id, company_id, score)
    return {"company_id": company_id, "overall_score": score.overall_score}


@memory_mcp.tool(description="Create an alert for a significant competitive change")
def create_alert(
    company: str,
    industry: str,
    alert_type: str,
    description: str,
    source_url: str = "",
    priority: str = "medium",
    run_id: int = 0,
) -> dict:
    """Store a competitive intelligence alert."""
    db = CompetitiveIntelligenceDB()
    company_id = db.upsert_company(company, industry)
    alert = Alert(
        company=company,
        alert_type=alert_type,
        description=description,
        source_url=source_url or None,
        priority=priority,
    )
    alert_id = db.save_alert(company_id, alert, run_id or None)
    return {"alert_id": alert_id}


@memory_mcp.tool(description="Persist a complete research run with findings, scores, and alerts")
def persist_research_run(state_json: str) -> dict:
    """Save an entire research run to SQLite memory."""
    state = json.loads(state_json)
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


def main() -> None:
    memory_mcp.run_stdio()


if __name__ == "__main__":
    main()
