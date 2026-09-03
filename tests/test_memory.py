"""Tests for SQLite memory database."""

import tempfile
from pathlib import Path

from memory.database import CompetitiveIntelligenceDB
from memory.schemas import Alert, CompanyScore, ExtractedFact, SourceType


def test_database_create_and_save_finding():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = CompetitiveIntelligenceDB(db_path)

        company_id = db.upsert_company("Snowflake", "Cloud Data")
        run_id = db.create_research_run(
            research_topic="Cloud Data: Snowflake",
            industry="Cloud Data",
            categories=["Pricing"],
            start_date="2026-01-01",
            end_date="2026-04-01",
        )

        fact = ExtractedFact(
            company="Snowflake",
            category="Pricing",
            claim="Usage-based pricing model",
            evidence="Charges based on compute credits and storage.",
            source_url="https://snowflake.com/pricing",
            source_title="Pricing Page",
            source_type=SourceType.OFFICIAL_WEBSITE,
            confidence=0.95,
        )

        finding_id = db.save_finding(run_id, company_id, fact)
        assert finding_id > 0

        findings = db.get_previous_findings("Snowflake")
        assert len(findings) == 1
        assert findings[0]["claim"] == "Usage-based pricing model"


def test_database_save_score_and_alert():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = CompetitiveIntelligenceDB(db_path)

        company_id = db.upsert_company("Databricks", "Cloud Data")
        run_id = db.create_research_run(
            research_topic="Test",
            industry="Cloud Data",
            categories=["AI"],
            start_date="2026-01-01",
            end_date="2026-04-01",
        )

        score = CompanyScore(
            company="Databricks",
            product_breadth=4.0,
            feature_differentiation=4.0,
            pricing_attractiveness=3.0,
            ai_maturity=5.0,
            partnerships=4.0,
            innovation_momentum=4.0,
            hiring_momentum=3.0,
        )
        db.save_score(run_id, company_id, score)

        alert = Alert(
            company="Databricks",
            alert_type="product_launch",
            description="New AI feature announced",
            priority="high",
        )
        alert_id = db.save_alert(company_id, alert, run_id)
        assert alert_id > 0

        saved_score = db.get_latest_scores("Databricks")
        assert saved_score is not None
        assert saved_score["overall_score"] == 4.0
