"""Safety guardrails and input validation (Checkpoint 6.1)."""

from __future__ import annotations

import re
from typing import Any

BLOCKED_REQUEST_PATTERNS = [
    r"\b(ssn|social security)\b",
    r"\b(password|credential|api[_\s]?key)\b",
    r"\bconfidential\b",
    r"\bproprietary\b",
    r"\binternal\s+only\b",
    r"\bprivate\s+financial\b",
    r"\bunreleased\b",
]

APPROVED_SOURCE_TYPES = {
    "official_website",
    "official_documentation",
    "regulatory_filing",
    "official_blog",
    "press_release",
    "news",
    "research_paper",
    "github",
    "job_posting",
}


class InputValidationError(Exception):
    """Raised when a research request violates safety policies."""

    def __init__(self, message: str, violations: list[str] | None = None):
        super().__init__(message)
        self.violations = violations or []


def validate_research_request(
    industry: str,
    companies: list[str],
    categories: list[str],
) -> dict[str, Any]:
    """
    Validate user input before workflow execution.
    Rejects requests for confidential/proprietary information.
    """
    violations: list[str] = []

    if not industry or not industry.strip():
        violations.append("Industry/market is required")

    if len(companies) < 2:
        violations.append("At least 2 companies are required for comparison")

    if len(companies) > 5:
        violations.append("Maximum 5 companies allowed")

    if not categories:
        violations.append("At least one analysis category is required")

    combined_text = f"{industry} {' '.join(companies)} {' '.join(categories)}".lower()
    for pattern in BLOCKED_REQUEST_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            violations.append(f"Request contains prohibited terms (pattern: {pattern})")

    if violations:
        raise InputValidationError(
            "Research request failed input validation",
            violations=violations,
        )

    return {
        "validated": True,
        "industry": industry.strip(),
        "companies": [c.strip() for c in companies if c.strip()],
        "categories": [c.strip() for c in categories if c.strip()],
    }


def verify_multi_source(findings: list[dict[str, Any]], min_sources: int = 2) -> dict[str, Any]:
    """
    Verify critical findings have multi-source support.
    Returns verification results and unsupported claims.
    """
    claim_sources: dict[str, set[str]] = {}

    for finding in findings:
        claim_key = f"{finding.get('company')}:{finding.get('category')}:{finding.get('claim', '')[:80]}"
        source_url = finding.get("source_url", "")
        if claim_key not in claim_sources:
            claim_sources[claim_key] = set()
        if source_url:
            claim_sources[claim_key].add(source_url)

    verified: list[str] = []
    unverified: list[str] = []

    for claim_key, sources in claim_sources.items():
        if len(sources) >= min_sources:
            verified.append(claim_key)
        else:
            unverified.append(claim_key)

    verification_rate = len(verified) / len(claim_sources) if claim_sources else 1.0

    return {
        "verified_claims": verified,
        "unverified_claims": unverified,
        "verification_rate": round(verification_rate, 3),
        "multi_source_threshold": min_sources,
    }


def check_output_constraints(finding: dict[str, Any]) -> dict[str, Any]:
    """Apply output labeling constraints to a finding."""
    labeled = dict(finding)

    if finding.get("is_company_claim"):
        labeled["claim_type"] = "company_statement"
    elif finding.get("confidence", 0) >= 0.7:
        labeled["claim_type"] = "verified_fact"
    elif finding.get("confidence", 0) >= 0.5:
        labeled["claim_type"] = "analytical_assessment"
    else:
        labeled["claim_type"] = "unverified"

    if not finding.get("source_url"):
        labeled["claim"] = f"[not publicly available] {finding.get('claim', '')}"

    return labeled


def filter_approved_sources(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Filter findings to approved public source types only."""
    approved: list[dict[str, Any]] = []
    warnings: list[str] = []

    for finding in findings:
        source_type = str(finding.get("source_type", "other"))
        if source_type in APPROVED_SOURCE_TYPES or source_type == "other":
            approved.append(finding)
        else:
            warnings.append(f"Filtered finding from unapproved source type: {source_type}")

    return approved, warnings
