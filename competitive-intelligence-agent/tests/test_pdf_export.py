"""Tests for PDF export builder."""

from reporting.pdf_export import build_analysis_pdf, export_pdf_filename


def test_export_pdf_filename_slugifies_industry():
    name = export_pdf_filename({"industry": "Education Industry"})
    assert name.startswith("competitive_intelligence_Education_Industry_")
    assert name.endswith(".pdf")


def test_build_analysis_pdf_returns_pdf_bytes():
    result = {
        "requires_human_review": False,
        "final_report": "Executive summary for the market.",
        "status_message": "Complete",
        "tot_confidence": 0.82,
        "escalation": {"overall_confidence": 0.82},
        "findings": [
            {
                "company": "Acme",
                "category": "Products",
                "claim": "Launched new API",
                "source_url": "https://example.com",
            }
        ],
        "scorecard": [
            {
                "company": "Acme",
                "overall_score": 4.2,
                "product_breadth": 4.0,
                "feature_differentiation": 4.1,
                "pricing_attractiveness": 3.8,
                "ai_maturity": 4.0,
            }
        ],
        "comparison": {
            "feature_matrix": {"Acme": {"API": "Yes"}},
            "pricing_comparison": {"Acme": 4.0},
        },
        "recommendations": [
            {
                "recommendation": "Expand partnerships",
                "evidence": "Validated findings show partnership gaps in enterprise segments.",
                "priority": "High",
                "impact": "Revenue",
                "time_horizon": "6 months",
            }
        ],
        "evaluation_metrics": {
            "correctness": {"value": 0.9},
        },
        "category_completeness": {"Products": 0.8},
    }
    config = {
        "industry": "Cloud Data Platforms",
        "companies": ["Acme", "Beta"],
        "date_range_days": 60,
        "report_depth": "standard",
        "geographic_market": "Global",
    }

    pdf_bytes = build_analysis_pdf(result, config)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500
