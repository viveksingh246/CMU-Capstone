"""Evidence validation agent."""

from typing import Any

from memory.schemas import SOURCE_CREDIBILITY_SCORES, SourceType
from workflows.state import ResearchState


MIN_CONFIDENCE = 0.5
MIN_CONTENT_LENGTH = 50


def validate_evidence(state: ResearchState) -> dict[str, Any]:
    """Validate findings and filter low-quality evidence."""
    findings = state.get("findings", [])
    validated: list[dict[str, Any]] = []
    errors = list(state.get("errors", []))

    seen_claims: set[str] = set()

    for finding in findings:
        claim_key = f"{finding.get('company')}:{finding.get('claim', '')[:100]}"
        if claim_key in seen_claims:
            continue

        confidence = finding.get("confidence", 0)
        if confidence < MIN_CONFIDENCE:
            continue

        evidence = finding.get("evidence", "")
        if len(evidence) < MIN_CONTENT_LENGTH and confidence < 0.8:
            continue

        source_type_str = finding.get("source_type", "other")
        try:
            source_type = SourceType(source_type_str)
        except ValueError:
            source_type = SourceType.OTHER

        finding["credibility_score"] = SOURCE_CREDIBILITY_SCORES.get(source_type, 1)
        validated.append(finding)
        seen_claims.add(claim_key)

    removed = len(findings) - len(validated)
    if removed:
        errors.append(f"Filtered {removed} low-confidence or duplicate findings")

    return {
        "findings": validated,
        "errors": errors,
        "status_message": f"Validated {len(validated)} findings",
    }
