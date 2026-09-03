"""Tests for fact extraction schemas."""

import pytest

from memory.schemas import ExtractedFact, SourceType


def test_extracted_fact_validation():
    fact = ExtractedFact(
        company="Snowflake",
        category="Pricing",
        claim="Offers usage-based pricing",
        evidence="Snowflake charges based on compute and storage usage.",
        source_url="https://snowflake.com/pricing",
        source_title="Snowflake Pricing",
        published_date="2026-01-15",
        source_type=SourceType.OFFICIAL_WEBSITE,
        confidence=0.9,
    )
    assert fact.company == "Snowflake"
    assert fact.confidence == 0.9


def test_extracted_fact_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        ExtractedFact(
            company="Test",
            category="Products",
            claim="Test claim",
            evidence="Evidence text",
            source_url="https://example.com",
            source_title="Test",
            confidence=1.5,
        )
