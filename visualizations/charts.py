"""Chart and visualization utilities for competitive intelligence reports."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


SCORE_CATEGORIES = [
    "product_breadth",
    "feature_differentiation",
    "pricing_attractiveness",
    "ai_maturity",
    "partnerships",
    "innovation_momentum",
    "hiring_momentum",
]


SCORE_LABELS = {
    "product_breadth": "Product Breadth",
    "feature_differentiation": "Feature Differentiation",
    "pricing_attractiveness": "Pricing",
    "ai_maturity": "AI Maturity",
    "partnerships": "Partnerships",
    "innovation_momentum": "Innovation",
    "hiring_momentum": "Hiring",
}


def create_score_bar_chart(scorecard: list[dict[str, Any]]):
    """Bar chart comparing overall scores across companies."""
    if not scorecard:
        return None

    df = pd.DataFrame(
        [
            {"Company": s.get("company", ""), "Overall Score": s.get("overall_score", 0)}
            for s in scorecard
        ]
    )

    fig = px.bar(
        df,
        x="Company",
        y="Overall Score",
        title="Competitive Scorecard",
        color="Overall Score",
        color_continuous_scale="Blues",
        range_y=[0, 5],
    )
    fig.update_layout(showlegend=False)
    return fig


def create_radar_chart(scorecard: list[dict[str, Any]]):
    """Radar chart comparing category scores across companies."""
    if not scorecard:
        return None

    fig = go.Figure()

    for score in scorecard:
        company = score.get("company", "Unknown")
        values = [score.get(cat, 3) for cat in SCORE_CATEGORIES]
        values.append(values[0])  # close the polygon

        labels = [SCORE_LABELS[cat] for cat in SCORE_CATEGORIES]
        labels.append(labels[0])

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=labels,
                fill="toself",
                name=company,
                opacity=0.6,
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        title="Category Score Comparison",
        showlegend=True,
    )
    return fig


def create_category_heatmap(scorecard: list[dict[str, Any]]):
    """Heatmap of category scores by company."""
    if not scorecard:
        return None

    companies = [s.get("company", "") for s in scorecard]
    data = []
    for cat in SCORE_CATEGORIES:
        row = [s.get(cat, 0) for s in scorecard]
        data.append(row)

    fig = go.Figure(
        data=go.Heatmap(
            z=data,
            x=companies,
            y=[SCORE_LABELS[c] for c in SCORE_CATEGORIES],
            colorscale="Blues",
            zmin=1,
            zmax=5,
        )
    )
    fig.update_layout(title="Feature Comparison Heatmap")
    return fig


def create_announcement_timeline(findings: list[dict[str, Any]]):
    """Timeline of announcements from findings with dates."""
    dated = [
        f
        for f in findings
        if f.get("published_date")
        and f.get("category", "").lower() in ("products", "partnerships", "ai capabilities")
    ]

    if not dated:
        return None

    df = pd.DataFrame(
        [
            {
                "Date": f.get("published_date"),
                "Company": f.get("company"),
                "Event": f.get("claim", "")[:80],
            }
            for f in dated
        ]
    )

    fig = px.scatter(
        df,
        x="Date",
        y="Company",
        text="Event",
        title="Recent Announcements Timeline",
        color="Company",
    )
    fig.update_traces(textposition="top center")
    return fig


def create_completeness_chart(category_completeness: dict[str, str]):
    """Show research coverage by category."""
    if not category_completeness:
        return None

    status_map = {"complete": 3, "insufficient_evidence": 2, "incomplete": 1}
    df = pd.DataFrame(
        [
            {"Category": cat, "Status": status, "Score": status_map.get(status, 0)}
            for cat, status in category_completeness.items()
        ]
    )

    color_map = {
        "complete": "#2ecc71",
        "insufficient_evidence": "#f39c12",
        "incomplete": "#e74c3c",
    }

    fig = px.bar(
        df,
        x="Category",
        y="Score",
        color="Status",
        title="Research Coverage by Category",
        color_discrete_map=color_map,
    )
    return fig
