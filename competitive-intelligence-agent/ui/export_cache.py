"""Session-scoped cache for PDF export bytes."""

from __future__ import annotations

from typing import Any

import streamlit as st

from reporting.pdf_export import build_analysis_pdf


def _export_pdf_cache_key(result: dict[str, Any], config: dict[str, Any]) -> str:
    return "|".join(
        [
            str(config.get("industry", "")),
            ",".join(config.get("companies", [])),
            str(result.get("requires_human_review")),
            str(len(result.get("findings", []))),
            str(len(result.get("final_report", ""))),
            str(len(result.get("scorecard", {}))),
        ]
    )


def get_export_pdf_bytes(result: dict[str, Any], config: dict[str, Any]) -> bytes:
    cache_key = _export_pdf_cache_key(result, config)
    if st.session_state.get("_pdf_export_cache_key") == cache_key:
        cached = st.session_state.get("_pdf_export_bytes")
        if isinstance(cached, bytes):
            return cached
    pdf_bytes = build_analysis_pdf(result, config)
    st.session_state["_pdf_export_cache_key"] = cache_key
    st.session_state["_pdf_export_bytes"] = pdf_bytes
    return pdf_bytes
