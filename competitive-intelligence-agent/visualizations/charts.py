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

CHART_FONT = dict(family="Inter, system-ui, sans-serif", size=11, color="#7A6552")
CHART_TITLE = dict(font=dict(size=12, color="#3D2914", family="Inter, system-ui"), x=0, xanchor="left")
CHART_MARGIN = dict(l=44, r=20, t=40, b=40)
CHART_HEIGHT = 280
CHART_COLORS = ["#3D2914", "#C8920A", "#F5B041", "#8B6914", "#7A6552", "#5C3D1E"]
CHART_GRID = "#F5EDE0"
CHART_AXIS = "#E8DCC8"
CHART_SCALE = [[0, "#FFF8E7"], [0.5, "#D4A017"], [1, "#3D2914"]]


def _apply_compact_layout(fig, height: int = CHART_HEIGHT) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=CHART_MARGIN,
        title=CHART_TITLE,
        font=CHART_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=CHART_GRID, linecolor=CHART_AXIS)
    fig.update_yaxes(showgrid=True, gridcolor=CHART_GRID, linecolor=CHART_AXIS)
    return fig


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
        title="Scorecard",
        color="Overall Score",
        color_continuous_scale=CHART_SCALE,
        range_y=[0, 5],
    )
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    fig.update_traces(marker_line_width=0)
    return _apply_compact_layout(fig)


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
                opacity=0.55,
                line=dict(width=2),
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], gridcolor=CHART_AXIS, linecolor=CHART_AXIS),
            bgcolor="rgba(0,0,0,0)",
        ),
        title="Category Comparison",
        showlegend=True,
        colorway=CHART_COLORS,
    )
    return _apply_compact_layout(fig)


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
            colorscale=CHART_SCALE,
            zmin=1,
            zmax=5,
        )
    )
    fig.update_layout(title="Feature Heatmap")
    return _apply_compact_layout(fig)


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
        title="Announcements",
        color="Company",
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(textposition="top center", marker=dict(size=8))
    return _apply_compact_layout(fig, height=220)


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
        "complete": "#5D7A4A",
        "insufficient_evidence": "#D97706",
        "incomplete": "#A63D2F",
    }

    fig = px.bar(
        df,
        x="Category",
        y="Score",
        color="Status",
        title="Coverage",
        color_discrete_map=color_map,
    )
    fig.update_layout(showlegend=False)
    return _apply_compact_layout(fig, height=220)
