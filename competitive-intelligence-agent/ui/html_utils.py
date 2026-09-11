"""Safe HTML rendering for Streamlit (avoids indented-markdown code blocks)."""

from __future__ import annotations

from textwrap import dedent

import streamlit as st


def normalize_html(markup: str) -> str:
    """Strip indentation so Streamlit does not treat HTML as a code block."""
    text = dedent(markup).strip()
    return "\n".join(line.lstrip() for line in text.splitlines())


def render_html(markup: str) -> None:
    """Render HTML without leading-indent code-block artifacts."""
    st.markdown(normalize_html(markup), unsafe_allow_html=True)
