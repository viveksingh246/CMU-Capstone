"""Evidence validation agent."""

from typing import Any

from config import settings
from memory.schemas import SOURCE_CREDIBILITY_SCORES, SourceType
from memory.short_term import record_react_step
from safety.guardrails import check_output_constraints, filter_approved_sources, verify_multi_source
from workflows.state import ResearchState


MIN_CONFIDENCE = 0.5
MIN_CONTENT_LENGTH = 50


def validate_evidence(state: ResearchState) -> dict[str, Any]:
    """Validate findings, apply safety guardrails, and filter low-quality evidence."""
    findings = state.get("findings", [])
    errors = list(state.get("errors", []))

    # Tool access limits: approved public sources only (Checkpoint 6.1)
    findings, source_warnings = filter_approved_sources(findings)
    errors.extend(source_warnings)

    validated: list[dict[str, Any]] = []
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

        # Apply output labeling constraints (Checkpoint 6.1)
        labeled = check_output_constraints(finding)
        validated.append(labeled)
        seen_claims.add(claim_key)

    # Multi-source verification for critical findings (Checkpoint 6.1)
    verification_results = verify_multi_source(
        validated,
        min_sources=settings.min_sources_per_major_claim,
    )

    removed = len(findings) - len(validated)
    if removed:
        errors.append(f"Filtered {removed} low-confidence or duplicate findings")

    react = record_react_step(
        state,
        "reflect",
        f"Validated {len(validated)} findings",
        f"Verification rate: {verification_results['verification_rate']:.0%}",
        {"unverified_count": len(verification_results.get("unverified_claims", []))},
    )

    return {
        **react,
        "findings": validated,
        "verification_results": verification_results,
        "errors": errors,
        "status_message": f"Validated {len(validated)} findings (multi-source rate: {verification_results['verification_rate']:.0%})",
    }
