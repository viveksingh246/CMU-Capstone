"""Extended tests for Critic Agent (Checkpoint 4.1)."""

from agents.critic import SCORING_WEIGHTS, evaluate_branch


def test_scoring_weights_sum_to_one():
    assert abs(sum(SCORING_WEIGHTS.values()) - 1.0) < 0.001


def test_critic_prunes_weak_branch():
    branch = {
        "hypothesis": "",
        "branch_type": "unknown",
        "confidence_score": 0.1,
        "supporting_evidence": [],
        "unresolved_questions": ["q1", "q2", "q3", "q4"],
    }
    result = evaluate_branch(branch, [])
    assert result["overall_score"] < 65
    assert result["pruned"] is True


def test_critic_scores_strong_branch_high():
    findings = [
        {
            "company": "Snowflake",
            "category": "AI",
            "source_type": "official_documentation",
            "confidence": 0.95,
            "published_date": "2025-09-01",
        },
        {
            "company": "Databricks",
            "category": "AI",
            "source_type": "press_release",
            "confidence": 0.9,
            "published_date": "2025-08-01",
        },
        {
            "company": "Snowflake",
            "category": "Products",
            "source_type": "official_website",
            "confidence": 0.92,
            "published_date": "2025-07-01",
        },
        {
            "company": "Databricks",
            "category": "Partnerships",
            "source_type": "news",
            "confidence": 0.88,
            "published_date": "2025-06-01",
        },
    ]
    branch = {
        "hypothesis": "Snowflake leads in AI innovation",
        "branch_type": "innovation_leadership",
        "confidence_score": 0.85,
        "supporting_evidence": findings,
        "unresolved_questions": [],
    }
    result = evaluate_branch(branch, findings)
    assert result["overall_score"] >= 65
    assert result["pruned"] is False


def test_critic_generates_notes_for_low_scores():
    branch = {
        "hypothesis": "test",
        "branch_type": "unknown",
        "confidence_score": 0.1,
        "supporting_evidence": [],
        "unresolved_questions": ["many", "questions"],
    }
    result = evaluate_branch(branch, [])
    assert len(result["evaluation_notes"]) > 0
