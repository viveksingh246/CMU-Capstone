"""Tests for competitive analysis scoring."""

from memory.schemas import CompanyScore, CompetitiveReport


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


def test_rationale_accepts_string_from_llm():
    score = CompanyScore(
        company="Coursera",
        product_breadth=4.0,
        feature_differentiation=4.0,
        pricing_attractiveness=3.0,
        ai_maturity=3.0,
        partnerships=3.0,
        innovation_momentum=4.0,
        hiring_momentum=3.0,
        rationale="Coursera has a strong product portfolio and partnerships to attract new users.",
    )
    assert score.rationale == {
        "summary": "Coursera has a strong product portfolio and partnerships to attract new users.",
    }


def test_competitive_report_key_trends_accepts_dict_items_from_llm():
    report = CompetitiveReport(
        executive_summary="summary",
        market_overview="overview",
        company_profiles={},
        feature_matrix={},
        pricing_comparison={},
        strategic_moves=[],
        hiring_signals={},
        ai_analysis={},
        swot=[],
        scorecard=[],
        key_trends=[
            {"trend": "Growing demand for cloud-based data platforms"},
            {"trend": "Rising importance of machine learning capabilities"},
            "Expanding into adjacent markets",
        ],
        recommendations=[],
        sources=[],
    )
    assert report.key_trends == [
        "Growing demand for cloud-based data platforms",
        "Rising importance of machine learning capabilities",
        "Expanding into adjacent markets",
    ]
