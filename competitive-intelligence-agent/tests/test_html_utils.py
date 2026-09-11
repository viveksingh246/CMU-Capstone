"""Tests for safe HTML rendering."""

from ui.html_utils import normalize_html


def test_normalize_html_removes_leading_indentation():
    markup = """
        <div class="outer">
            <div class="inner">child</div>
        </div>
    """
    normalized = normalize_html(markup)
    assert not normalized.startswith(" ")
    assert "<div class=\"inner\">child</div>" in normalized
    assert all(not line.startswith("    ") for line in normalized.splitlines())
