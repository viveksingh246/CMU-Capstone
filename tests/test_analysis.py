"""Tests for competitive analysis scoring."""

from memory.schemas import CompanyScore


def test_overall_score_weighted_calculation():
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
    # 4*0.2 + 4*0.2 + 3*0.15 + 5*0.2 + 4*0.1 + 4*0.1 + 3*0.05
    # = 0.8 + 0.8 + 0.45 + 1.0 + 0.4 + 0.4 + 0.15 = 4.0
    assert score.overall_score == 4.0


def test_score_range():
    score = CompanyScore(
        company="Test",
        product_breadth=1.0,
        feature_differentiation=1.0,
        pricing_attractiveness=1.0,
        ai_maturity=1.0,
        partnerships=1.0,
        innovation_momentum=1.0,
        hiring_momentum=1.0,
    )
    assert score.overall_score == 1.0
