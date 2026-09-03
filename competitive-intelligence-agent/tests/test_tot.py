"""Tests for Tree-of-Thought reasoning (Checkpoint 4.1)."""

from agents.critic import evaluate_branch
from reasoning.tot_engine import _fallback_branches, beam_search_analysis


SAMPLE_FINDINGS = [
    {
        "company": "Snowflake",
        "category": "AI capabilities",
        "claim": "Snowflake Cortex provides generative AI",
        "evidence": "Official documentation describes Cortex AI functions for SQL-based ML.",
        "source_url": "https://snowflake.com/cortex",
        "source_type": "official_documentation",
        "confidence": 0.9,
        "published_date": "2025-06-01",
    },
    {
        "company": "Databricks",
        "category": "AI capabilities",
        "claim": "Databricks offers Mosaic AI for enterprise LLM deployment",
        "evidence": "Press release announces Mosaic AI platform for building and deploying models.",
        "source_url": "https://databricks.com/mosaic",
        "source_type": "press_release",
        "confidence": 0.85,
        "published_date": "2025-08-15",
    },
]


def test_critic_evaluates_branch():
    branch = {
        "hypothesis": "Snowflake leads in AI innovation",
        "branch_type": "innovation_leadership",
        "confidence_score": 0.8,
        "supporting_evidence": SAMPLE_FINDINGS,
        "unresolved_questions": [],
    }

    result = evaluate_branch(branch, SAMPLE_FINDINGS)

    assert "overall_score" in result
    assert 0 <= result["overall_score"] <= 100
    assert "criterion_scores" in result
    assert result["criterion_scores"]["source_credibility"] > 50


def test_fallback_branches_generates_alternatives():
    branches = _fallback_branches(["Snowflake", "Databricks", "BigQuery"])
    assert len(branches) == 4
    branch_types = {b.branch_type for b in branches}
    assert "innovation_leadership" in branch_types
    assert "pricing_competitiveness" in branch_types


def test_beam_search_selects_best_branch():
    result = beam_search_analysis(
        companies=["Snowflake", "Databricks"],
        findings=SAMPLE_FINDINGS,
        industry="Cloud Data Platforms",
    )

    assert "best_branch" in result
    assert "selected_hypothesis" in result
    assert "tree_metadata" in result
    assert result["tot_confidence"] >= 0
    assert len(result["tree_metadata"]["depths_explored"]) >= 1
