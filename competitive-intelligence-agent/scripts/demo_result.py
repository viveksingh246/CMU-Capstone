"""Rich demo state for presentation screenshots."""

from __future__ import annotations

from typing import Any


def demo_config() -> dict[str, Any]:
    return {
        "industry": "Cloud Data Platforms",
        "companies": ["Snowflake", "Databricks", "Google BigQuery"],
        "categories": [
            "Products",
            "Features",
            "Pricing",
            "AI capabilities",
            "Partnerships",
            "Hiring trends",
        ],
        "date_range_days": 90,
        "geographic_market": "Global",
        "report_depth": "standard",
        "compare_historical": True,
        "enable_alerts": True,
    }


def demo_pipeline_steps() -> list[dict[str, Any]]:
    return [
        {"node": "parse_request", "label": "Parse Request", "status": "complete", "detail": "Validated 3 companies"},
        {"node": "check_memory", "label": "Check Memory", "status": "complete", "detail": "Loaded prior run"},
        {"node": "coordinate", "label": "Coordinate", "status": "complete", "detail": "Phase: research"},
        {"node": "create_plan", "label": "Research Plan", "status": "complete", "detail": "18 queries planned"},
        {"node": "search", "label": "Search Sources", "status": "complete", "detail": "42 documents collected"},
        {"node": "index_rag", "label": "RAG Index", "status": "complete", "detail": "128 chunks indexed"},
        {"node": "extract", "label": "Extract Facts", "status": "complete", "detail": "36 findings extracted"},
        {"node": "validate", "label": "Validate Evidence", "status": "complete", "detail": "31 validated"},
        {"node": "completeness", "label": "Check Completeness", "status": "complete", "detail": "5/6 categories complete"},
        {"node": "analyze", "label": "ToT Analysis", "status": "complete", "detail": "Beam search complete"},
        {"node": "safety_check", "label": "Safety Check", "status": "active", "detail": "Evaluating confidence"},
        {"node": "generate_report", "label": "Generate Report", "status": "pending", "detail": ""},
    ]


def demo_pipeline_active_steps() -> list[dict[str, Any]]:
    steps = demo_pipeline_steps()
    for step in steps:
        if step["node"] == "safety_check":
            step["status"] = "active"
        elif step["node"] == "generate_report":
            step["status"] = "pending"
        else:
            step["status"] = "complete"
    # Mark search as active for pipeline-in-progress screenshot
    for step in steps:
        if step["node"] == "search":
            step["status"] = "active"
            step["detail"] = "Querying Tavily: Snowflake AI capabilities"
        elif step["node"] not in ("parse_request", "check_memory", "coordinate", "create_plan"):
            if step["node"] != "search":
                step["status"] = "pending"
                step["detail"] = ""
    return steps[:6] + [
        {"node": "search", "label": "Search Sources", "status": "active", "detail": "Querying Tavily: Snowflake AI capabilities"},
        {"node": "index_rag", "label": "RAG Index", "status": "pending", "detail": ""},
        {"node": "extract", "label": "Extract Facts", "status": "pending", "detail": ""},
        {"node": "validate", "label": "Validate Evidence", "status": "pending", "detail": ""},
        {"node": "completeness", "label": "Check Completeness", "status": "pending", "detail": ""},
        {"node": "analyze", "label": "ToT Analysis", "status": "pending", "detail": ""},
    ]


def demo_findings() -> list[dict[str, Any]]:
    samples = [
        ("Snowflake", "Products", "Snowflake Cortex AI provides LLM functions in SQL", "verified_fact", "official_website", 0.92),
        ("Snowflake", "AI capabilities", "Document AI and Cortex Analyst announced at Summit", "verified_fact", "press_release", 0.88),
        ("Databricks", "Products", "Unity Catalog provides unified governance across clouds", "verified_fact", "official_documentation", 0.91),
        ("Databricks", "AI capabilities", "Mosaic AI Model Serving for production LLM deployment", "verified_fact", "official_website", 0.89),
        ("Google BigQuery", "Pricing", "On-demand pricing starts at $6.25 per TB scanned", "company_claim", "official_website", 0.75),
        ("Google BigQuery", "AI capabilities", "BigQuery ML and Gemini integration for SQL workflows", "verified_fact", "official_blog", 0.87),
        ("Snowflake", "Partnerships", "Expanded NVIDIA partnership for GPU-accelerated workloads", "verified_fact", "news", 0.84),
        ("Databricks", "Hiring trends", "Increased ML engineer hiring in Seattle and Amsterdam", "verified_fact", "news", 0.78),
    ]
    findings = []
    for company, category, claim, claim_type, source_type, confidence in samples:
        slug = company.lower().replace(" ", "")
        findings.append(
            {
                "company": company,
                "category": category,
                "claim": claim,
                "claim_type": claim_type,
                "source_type": source_type,
                "source_url": f"https://www.{slug}.com/product",
                "confidence": confidence,
                "published_date": "2026-08-15",
            }
        )
    return findings


def demo_scorecard() -> list[dict[str, Any]]:
    return [
        {
            "company": "Snowflake",
            "product_breadth": 4.2,
            "feature_differentiation": 4.0,
            "pricing_attractiveness": 3.5,
            "ai_maturity": 4.3,
            "partnerships": 4.1,
            "innovation_momentum": 4.0,
            "hiring_momentum": 3.8,
            "overall_score": 4.0,
            "rationale": {"summary": "Strong AI push via Cortex; governance and ecosystem depth."},
        },
        {
            "company": "Databricks",
            "product_breadth": 4.4,
            "feature_differentiation": 4.3,
            "pricing_attractiveness": 3.6,
            "ai_maturity": 4.5,
            "partnerships": 4.0,
            "innovation_momentum": 4.4,
            "hiring_momentum": 4.2,
            "overall_score": 4.2,
            "rationale": {"summary": "Lakehouse + Mosaic AI leadership; strong open-source momentum."},
        },
        {
            "company": "Google BigQuery",
            "product_breadth": 4.0,
            "feature_differentiation": 3.8,
            "pricing_attractiveness": 4.1,
            "ai_maturity": 4.2,
            "partnerships": 3.9,
            "innovation_momentum": 3.9,
            "hiring_momentum": 3.7,
            "overall_score": 3.9,
            "rationale": {"summary": "GCP integration and Gemini-in-SQL; competitive on price."},
        },
    ]


def demo_result(requires_review: bool = False) -> dict[str, Any]:
    findings = demo_findings()
    return {
        "requires_human_review": requires_review,
        "status_message": "Research complete — pending human approval" if requires_review else "Analysis complete",
        "tot_confidence": 0.68 if requires_review else 0.86,
        "escalation": {
            "requires_human_review": requires_review,
            "overall_confidence": 0.68 if requires_review else 0.86,
            "reasons": ["Overall confidence below 70% threshold"] if requires_review else [],
        },
        "executive_summary": (
            "Snowflake, Databricks, and Google BigQuery are converging on AI-native data platforms. "
            "Databricks leads on lakehouse + Mosaic AI breadth; Snowflake differentiates via Cortex in SQL; "
            "BigQuery competes on GCP integration and pricing."
        ),
        "final_report": (
            "## Market Intelligence Brief\n\n"
            "The cloud data platform market shows accelerating AI feature parity. "
            "All three competitors are embedding LLM capabilities directly into SQL workflows. "
            "Partnerships (NVIDIA, open-source foundations) are key differentiators.\n\n"
            "**Key finding:** Databricks shows strongest innovation momentum; Snowflake leads enterprise governance narrative."
        ),
        "findings": findings,
        "scorecard": demo_scorecard(),
        "comparison": {
            "feature_matrix": {
                "Snowflake": {"Products": 4.2, "Features": 4.0, "AI capabilities": 4.3},
                "Databricks": {"Products": 4.4, "Features": 4.3, "AI capabilities": 4.5},
                "Google BigQuery": {"Products": 4.0, "Features": 3.8, "AI capabilities": 4.2},
            },
            "pricing_comparison": {"Snowflake": 3.5, "Databricks": 3.6, "Google BigQuery": 4.1},
        },
        "swot_analysis": {
            "companies": [
                {
                    "company": "Snowflake",
                    "strengths": [{"point": "Cortex AI embedded in familiar SQL workflows"}],
                    "weaknesses": [{"point": "Premium pricing vs. BigQuery on-demand"}],
                    "opportunities": [{"point": "Expand vertical AI solutions"}],
                    "threats": [{"point": "Databricks open-source ecosystem growth"}],
                }
            ]
        },
        "recommendations": [
            {
                "recommendation": "Accelerate AI feature parity in SQL interfaces",
                "evidence": "All three competitors shipping LLM-in-SQL capabilities in 2026.",
                "priority": "High",
                "impact": "Product differentiation",
                "time_horizon": "Q4 2026",
            },
            {
                "recommendation": "Strengthen NVIDIA/GPU partnership narrative",
                "evidence": "Snowflake and Databricks both announced expanded NVIDIA integrations.",
                "priority": "Medium",
                "impact": "Enterprise sales",
                "time_horizon": "6 months",
            },
        ],
        "evaluation_metrics": {
            "correctness": {"value": 0.96, "target": 0.95, "passed": True},
            "groundedness": {"value": 1.0, "target": 0.90, "passed": True},
            "source_credibility": {"value": 0.875, "target": 0.70, "passed": True},
            "freshness": {"value": 1.0, "target": 0.50, "passed": True},
            "research_coverage": {"value": 0.833, "target": 0.90, "passed": False},
            "safety_compliance": {"value": 1.0, "target": 0.95, "passed": True},
            "human_escalation": {"value": 1 if requires_review else 0, "description": "1 = escalated"},
            "companies_analyzed": 3,
            "findings_count": len(findings),
        },
        "category_completeness": {
            "Products": "complete",
            "Features": "complete",
            "Pricing": "complete",
            "AI capabilities": "complete",
            "Partnerships": "complete",
            "Hiring trends": "partial",
        },
        "react_trace": [
            {"step": "reason", "thought": "Compare 3 cloud data platforms across 6 strategic categories"},
            {"step": "plan", "thought": "Generate 18 targeted search queries across official and news sources"},
            {"step": "act", "thought": "Collected 42 documents; indexed 128 RAG chunks"},
            {"step": "observe", "thought": "Hiring trends category has partial coverage for BigQuery"},
            {"step": "reflect", "thought": "Trigger follow-up search for BigQuery hiring signals"},
            {"step": "decide", "thought": "Proceed to ToT analysis with noted coverage gap"},
        ],
        "historical_changes": [
            {"company": "Databricks", "description": "New Mosaic AI Model Serving GA announced"},
            {"company": "Snowflake", "description": "Cortex Analyst feature expanded to EU regions"},
        ],
        "alerts": [],
    }
