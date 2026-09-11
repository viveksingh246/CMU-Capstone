"""Build a presentation-ready PDF export of competitive intelligence analysis."""

from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from typing import Any

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from ui.recommendation_view import (
    build_recommendations_intro,
    recommendation_basis,
    recommendation_meta_line,
)
from visualizations.charts import (
    create_category_heatmap,
    create_completeness_chart,
    create_radar_chart,
    create_score_bar_chart,
)

BRAND_BROWN = (61, 41, 20)
BRAND_GOLD = (200, 146, 10)
BRAND_CREAM = (255, 248, 240)
TEXT_DARK = (44, 24, 16)
MUTED = (122, 101, 82)
LIGHT_FILL = (245, 237, 224)

PAGE_W = 210
MARGIN_L = 12
MARGIN_R = 12
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# Sections in markdown report that are rendered separately in the PDF.
_DUPLICATE_SECTIONS = {
    "product comparison matrix",
    "pricing comparison",
    "competitive scorecard",
    "strategic recommendations",
    "sources",
    "recent strategic moves",
    "ai capability analysis",
    "key trends",
    "company profiles",
}


def export_pdf_filename(config: dict[str, Any]) -> str:
    industry = re.sub(r"[^A-Za-z0-9]+", "_", config.get("industry", "analysis")).strip("_")
    stamp = datetime.now().strftime("%Y%m%d")
    return f"competitive_intelligence_{industry or 'report'}_{stamp}.pdf"


def _clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _clean_claim(text: str, *, max_len: int = 220) -> str:
    cleaned = _clean_text(text)
    cleaned = re.sub(r"^#+\s*", "", cleaned)
    cleaned = re.sub(r"Jump to content.*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"!\[.*", "", cleaned)
    cleaned = re.sub(r"#{1,6}\s+", "", cleaned)
    if len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 3].rstrip() + "..."
    return cleaned


def _looks_like_raw_data(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped[0] in "{[":
        return True
    if re.search(r"'\w+':\s*[\[{]", stripped):
        return True
    if stripped.startswith("|") and stripped.count("|") > 4:
        return False
    return bool(re.match(r"^[\[{].*[\]}]$", stripped))


class AnalysisPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        self.set_margins(MARGIN_L, 18, MARGIN_R)
        self.set_auto_page_break(auto=True, margin=16)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_fill_color(*BRAND_BROWN)
        self.rect(0, 0, PAGE_W, 12, style="F")
        self.set_xy(MARGIN_L, 3)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 248, 240)
        self.cell(0, 6, "Competitive Intelligence Research Agent", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")

    def ensure_space(self, height: float) -> None:
        if self.get_y() + height > self.page_break_trigger:
            self.add_page()

    def section_title(self, title: str) -> None:
        self.ensure_space(14)
        self.ln(3)
        self.set_x(MARGIN_L)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*BRAND_BROWN)
        self.cell(0, 8, _clean_text(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = self.get_y()
        self.set_draw_color(*BRAND_GOLD)
        self.set_line_width(0.4)
        self.line(MARGIN_L, y, PAGE_W - MARGIN_R, y)
        self.ln(4)

    def subsection_title(self, title: str) -> None:
        self.ensure_space(10)
        self.set_x(MARGIN_L)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BRAND_BROWN)
        self.cell(0, 6, _clean_text(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def body_text(self, text: str, size: int = 10) -> None:
        self.ensure_space(8)
        self.set_x(MARGIN_L)
        self.set_font("Helvetica", "", size)
        self.set_text_color(*TEXT_DARK)
        self.multi_cell(CONTENT_W, 5, _clean_text(text))

    def bullet(self, text: str, size: int = 9) -> None:
        self.ensure_space(6)
        self.set_x(MARGIN_L)
        self.set_font("Helvetica", "", size)
        self.set_text_color(*TEXT_DARK)
        self.multi_cell(CONTENT_W, 4.5, f"- {_clean_text(text)}")

    def bold_text(self, text: str, size: int = 10) -> None:
        self.ensure_space(8)
        self.set_x(MARGIN_L)
        self.set_font("Helvetica", "B", size)
        self.set_text_color(*BRAND_BROWN)
        self.multi_cell(CONTENT_W, 5, _clean_text(text))

    def metric_cards(self, items: list[tuple[str, str]]) -> None:
        if not items:
            return
        self.ensure_space(22)
        col_w = CONTENT_W / min(len(items), 4)
        cols = min(len(items), 4)
        y_start = self.get_y()
        for index, (label, value) in enumerate(items[:4]):
            x = MARGIN_L + (index % cols) * col_w
            if index > 0 and index % cols == 0:
                y_start = self.get_y() + 2
            self.set_xy(x + 2, y_start)
            self.set_fill_color(*LIGHT_FILL)
            self.set_draw_color(*BRAND_GOLD)
            self.rect(x, y_start, col_w - 4, 18, style="DF")
            self.set_xy(x + 4, y_start + 3)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*MUTED)
            self.cell(col_w - 8, 4, _clean_text(label)[:28], new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_xy(x + 4, y_start + 9)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*BRAND_BROWN)
            self.cell(col_w - 8, 6, _clean_text(value)[:20], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y_start + 22)


def _plotly_png(fig) -> bytes | None:
    if fig is None:
        return None
    try:
        return fig.to_image(format="png", width=1000, height=480, scale=2)
    except Exception:
        return None


def _add_chart(pdf: AnalysisPDF, fig, caption: str) -> None:
    png = _plotly_png(fig)
    if not png:
        return
    pdf.ensure_space(100)
    pdf.set_x(MARGIN_L)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BRAND_BROWN)
    pdf.cell(0, 6, _clean_text(caption), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.image(BytesIO(png), x=MARGIN_L, w=CONTENT_W)
    pdf.ln(6)


def _estimate_cell_height(text: str, width: float, line_height: float = 4.5) -> float:
    cleaned = _clean_text(text)
    if not cleaned:
        return 7.0
    chars_per_line = max(10, int(width / 1.9))
    lines = max(1, (len(cleaned) + chars_per_line - 1) // chars_per_line)
    return max(7.0, lines * line_height + 2)


def _draw_table_cell(
    pdf: AnalysisPDF,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    *,
    bold: bool = False,
    fill: bool = False,
) -> None:
    pdf.set_xy(x, y)
    if fill:
        pdf.set_fill_color(*LIGHT_FILL)
    pdf.rect(x, y, width, height, style="DF" if fill else "D")
    pdf.set_xy(x + 1.5, y + 1.5)
    pdf.set_font("Helvetica", "B" if bold else "", 8)
    pdf.set_text_color(*BRAND_BROWN if bold else TEXT_DARK)
    pdf.multi_cell(width - 3, 4.5, _clean_text(text), border=0)


def _add_table(pdf: AnalysisPDF, headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        return

    col_count = len(headers)
    widths = _column_widths(headers, rows, col_count)

    def draw_header() -> None:
        y = pdf.get_y()
        x = MARGIN_L
        for header, width in zip(headers, widths):
            _draw_table_cell(pdf, x, y, width, 8, header, bold=True, fill=True)
            x += width
        pdf.set_y(y + 8)

    pdf.ensure_space(14)
    draw_header()

    for row in rows:
        row_height = max(_estimate_cell_height(value, width) for value, width in zip(row, widths))
        if pdf.get_y() + row_height > pdf.page_break_trigger:
            pdf.add_page()
            draw_header()
        y = pdf.get_y()
        x = MARGIN_L
        for value, width in zip(row, widths):
            _draw_table_cell(pdf, x, y, width, row_height, value)
            x += width
        pdf.set_y(y + row_height)


def _column_widths(headers: list[str], rows: list[list[str]], col_count: int) -> list[float]:
    if col_count == 0:
        return []
    if col_count == 1:
        return [CONTENT_W]
    first_col = min(42.0, CONTENT_W * 0.28)
    remaining = (CONTENT_W - first_col) / (col_count - 1)
    return [first_col] + [remaining] * (col_count - 1)


def _scorecard_rows(scorecard: list[dict[str, Any]]) -> tuple[list[str], list[list[str]]]:
    if not scorecard:
        return [], []
    headers = ["Company", "Overall", "Product", "Features", "Pricing", "AI"]
    rows: list[list[str]] = []
    for entry in scorecard:
        rows.append(
            [
                str(entry.get("company", "")),
                f"{entry.get('overall_score', 0):.1f}",
                f"{entry.get('product_breadth', 0):.1f}",
                f"{entry.get('feature_differentiation', 0):.1f}",
                f"{entry.get('pricing_attractiveness', 0):.1f}",
                f"{entry.get('ai_maturity', 0):.1f}",
            ]
        )
    return headers, rows


def _matrix_rows(matrix: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    if not matrix:
        return [], []
    companies = sorted(matrix.keys())
    categories = sorted({key for company in matrix.values() for key in company.keys()})
    headers = ["Category", *companies]
    rows = []
    for category in categories:
        row = [category]
        for company in companies:
            value = matrix.get(company, {}).get(category, "-")
            row.append(str(value))
        rows.append(row)
    return headers, rows


def _render_cover_page(
    pdf: AnalysisPDF,
    *,
    industry: str,
    companies: str,
    config: dict[str, Any],
    confidence: float,
    findings_count: int,
    status: str,
) -> None:
    pdf.add_page()
    pdf.set_fill_color(*BRAND_BROWN)
    pdf.rect(0, 0, PAGE_W, 52, style="F")
    pdf.set_xy(MARGIN_L, 16)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 248, 240)
    pdf.multi_cell(CONTENT_W, 10, _clean_text(industry))
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*BRAND_CREAM)
    pdf.multi_cell(CONTENT_W, 6, "Competitive Intelligence Brief")
    pdf.ln(14)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Companies analyzed", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(CONTENT_W, 6, _clean_text(companies))
    pdf.ln(4)
    pdf.metric_cards(
        [
            ("Confidence", f"{confidence:.0%}"),
            ("Findings", str(findings_count)),
            ("Depth", str(config.get("report_depth", "standard")).title()),
            ("Window", f"{config.get('date_range_days', 60)} days"),
        ]
    )
    pdf.ln(4)
    pdf.body_text(f"Market: {config.get('geographic_market', 'Global')}", size=9)
    pdf.body_text(f"Generated: {datetime.now().strftime('%B %d, %Y')}", size=9)
    pdf.body_text(f"Status: {_clean_text(status)}", size=9)


def _render_executive_narrative(pdf: AnalysisPDF, report_text: str) -> None:
    if not report_text:
        return

    pdf.add_page()
    pdf.section_title("Executive Summary")

    skip_section = False
    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _looks_like_raw_data(line):
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            title = _clean_text(heading.group(2))
            title_key = title.lower()
            if title_key in _DUPLICATE_SECTIONS or title_key == "competitive intelligence report":
                skip_section = title_key != "executive summary"
                if title_key == "executive summary":
                    continue
                continue
            if level <= 2 and title_key not in {"executive summary", "market overview"}:
                skip_section = title_key in _DUPLICATE_SECTIONS
            if skip_section:
                continue
            if level == 2:
                pdf.subsection_title(title)
            elif level >= 3:
                pdf.bold_text(title, size=10)
            continue

        if skip_section:
            continue
        if line.startswith(("- ", "* ")):
            pdf.bullet(line[2:])
            continue
        if re.match(r"^\d+\.\s+", line):
            pdf.bullet(re.sub(r"^\d+\.\s+", "", line))
            continue
        if line.startswith("#"):
            continue
        pdf.body_text(line)


def _render_recommendations(pdf: AnalysisPDF, recommendations: list[dict[str, Any]], result: dict[str, Any]) -> None:
    if not recommendations:
        return
    pdf.add_page()
    pdf.section_title("Strategic Recommendations")
    pdf.body_text(build_recommendations_intro(result), size=9)
    pdf.ln(2)
    for index, rec in enumerate(recommendations[:8], start=1):
        if not isinstance(rec, dict):
            continue
        basis = recommendation_basis(rec)
        card_height = 26 + (10 if basis else 0)
        pdf.ensure_space(card_height + 4)
        pdf.set_fill_color(*LIGHT_FILL)
        pdf.set_draw_color(*BRAND_GOLD)
        y = pdf.get_y()
        pdf.rect(MARGIN_L, y, CONTENT_W, card_height, style="DF")
        pdf.set_xy(MARGIN_L + 4, y + 3)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*BRAND_GOLD)
        pdf.cell(12, 5, f"{index}.", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*BRAND_BROWN)
        pdf.multi_cell(CONTENT_W - 16, 5, _clean_text(rec.get("recommendation", "")))
        pdf.set_x(MARGIN_L + 16)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(CONTENT_W - 16, 4, _clean_text(recommendation_meta_line(rec)))
        if basis:
            pdf.set_x(MARGIN_L + 16)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*BRAND_BROWN)
            pdf.cell(28, 4, "Why:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*TEXT_DARK)
            pdf.multi_cell(CONTENT_W - 44, 4, _clean_text(basis))
        pdf.set_y(y + card_height + 3)


def _render_swot(pdf: AnalysisPDF, swot: list[dict[str, Any]]) -> None:
    if not swot:
        return
    pdf.add_page()
    pdf.section_title("SWOT Analysis")
    section_labels = {
        "strengths": "Strengths",
        "weaknesses": "Weaknesses",
        "opportunities": "Opportunities",
        "threats": "Threats",
    }
    for entry in swot:
        company = entry.get("company", "Company")
        pdf.subsection_title(str(company))
        for key, label in section_labels.items():
            points = entry.get(key, [])
            if not points:
                continue
            pdf.ensure_space(8)
            pdf.set_x(MARGIN_L)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*BRAND_BROWN)
            pdf.cell(0, 5, label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for point in points[:5]:
                text = point.get("point", "") if isinstance(point, dict) else str(point)
                pdf.bullet(_clean_claim(text, max_len=180), size=9)
        pdf.ln(2)


def _render_findings(pdf: AnalysisPDF, findings: list[dict[str, Any]]) -> None:
    if not findings:
        return
    pdf.add_page()
    pdf.section_title("Key Findings")
    for finding in findings[:30]:
        company = finding.get("company", "Company")
        category = finding.get("category", "Category")
        claim = _clean_claim(finding.get("claim", ""), max_len=200)
        if not claim or len(claim) < 12:
            continue
        pdf.ensure_space(12)
        pdf.set_x(MARGIN_L)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*BRAND_BROWN)
        pdf.cell(0, 5, f"{company}  |  {category}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.body_text(claim, size=9)
        pdf.ln(1)


def _render_sources(pdf: AnalysisPDF, findings: list[dict[str, Any]]) -> None:
    sources = sorted({f.get("source_url") for f in findings if f.get("source_url")})
    if not sources:
        return
    pdf.section_title("Sources & References")
    for url in sources[:40]:
        pdf.bullet(url, size=8)


def build_analysis_pdf(result: dict[str, Any], config: dict[str, Any]) -> bytes:
    """Render a presentation-ready multi-section PDF."""
    pdf = AnalysisPDF()
    pdf.alias_nb_pages()

    industry = config.get("industry", "Research engagement")
    companies = ", ".join(config.get("companies", []))
    escalation = result.get("escalation", {})
    confidence = escalation.get("overall_confidence", result.get("tot_confidence", 0))
    findings = result.get("findings", [])

    _render_cover_page(
        pdf,
        industry=industry,
        companies=companies,
        config=config,
        confidence=confidence,
        findings_count=len(findings),
        status=result.get("status_message", "Complete"),
    )

    _render_executive_narrative(pdf, result.get("final_report", ""))

    recommendations = result.get("recommendations", [])
    _render_recommendations(pdf, recommendations, result)

    metrics = result.get("evaluation_metrics", {})
    if metrics:
        pdf.add_page()
        pdf.section_title("Quality & Governance Metrics")
        metric_rows = []
        for key, payload in metrics.items():
            if isinstance(payload, dict) and "value" in payload:
                label = key.replace("_", " ").title()
                metric_rows.append((label, f"{payload['value']:.0%}"))
        for label, value in metric_rows:
            pdf.set_x(MARGIN_L)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*BRAND_BROWN)
            pdf.cell(55, 6, _clean_text(label), new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(0, 6, _clean_text(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    scorecard = result.get("scorecard", [])
    headers, rows = _scorecard_rows(scorecard)
    if rows:
        pdf.add_page()
        pdf.section_title("Competitive Scorecard")
        _add_table(pdf, headers, rows)

    comparison = result.get("comparison", {})
    feature_headers, feature_rows = _matrix_rows(comparison.get("feature_matrix", {}))
    pricing = comparison.get("pricing_comparison", {})
    if feature_rows or pricing:
        pdf.add_page()
        pdf.section_title("Competitive Comparison")
        if feature_rows:
            pdf.subsection_title("Feature Matrix")
            _add_table(pdf, feature_headers, feature_rows)
        if pricing:
            pdf.ln(2)
            pdf.subsection_title("Pricing Comparison")
            _add_table(
                pdf,
                ["Company", "Score"],
                [[company, str(score)] for company, score in sorted(pricing.items())],
            )

    swot = result.get("swot_analysis", {}).get("companies", [])
    _render_swot(pdf, swot)

    charts = [
        (create_score_bar_chart(scorecard), "Overall competitive scores"),
        (create_radar_chart(scorecard), "Capability radar comparison"),
        (create_category_heatmap(scorecard), "Category heatmap"),
        (
            create_completeness_chart(result.get("category_completeness", {})),
            "Research coverage by category",
        ),
    ]
    if any(fig for fig, _ in charts):
        pdf.add_page()
        pdf.section_title("Analytics")
        for fig, caption in charts:
            _add_chart(pdf, fig, caption)

    _render_findings(pdf, findings)
    _render_sources(pdf, findings)

    return bytes(pdf.output())
