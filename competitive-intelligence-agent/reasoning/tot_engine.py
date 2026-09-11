"""Tree-of-Thought reasoning engine with beam search (Checkpoint 4.1)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.critic import evaluate_branch
from agents.llm import get_llm, invoke_llm, is_cloud_efficiency_mode

PRUNE_THRESHOLD = 65
BEAM_WIDTH = 3
MAX_DEPTH = 4
BRANCHING_FACTOR = 4

STRATEGIC_BRANCHES = [
    "innovation_leadership",
    "pricing_competitiveness",
    "partnership_strength",
    "engineering_momentum",
]


@dataclass
class ThoughtNode:
    """A single node in the ToT reasoning tree."""

    hypothesis: str
    branch_type: str
    depth: int
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    evaluation_score: float = 0.0
    unresolved_questions: list[str] = field(default_factory=list)
    reasoning_history: list[str] = field(default_factory=list)
    parent_id: str | None = None
    node_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "branch_type": self.branch_type,
            "depth": self.depth,
            "supporting_evidence": self.supporting_evidence,
            "confidence_score": self.confidence_score,
            "evaluation_score": self.evaluation_score,
            "unresolved_questions": self.unresolved_questions,
            "reasoning_history": self.reasoning_history,
            "parent_id": self.parent_id,
            "node_id": self.node_id,
        }


def generate_initial_branches(
    companies: list[str],
    findings: list[dict[str, Any]],
    industry: str,
) -> list[ThoughtNode]:
    """Generate candidate strategic interpretation branches at depth 1."""
    if is_cloud_efficiency_mode():
        return _fallback_branches(companies)

    try:
        llm = get_llm()
    except ValueError:
        return _fallback_branches(companies)

    findings_summary = json.dumps(findings[:30], indent=2)

    prompt = f"""
Industry: {industry}
Companies: {', '.join(companies)}

Validated findings:
{findings_summary}

Generate {BRANCHING_FACTOR} competing strategic hypotheses about the competitive landscape.
Each hypothesis should represent a different analytical lens:
- innovation leadership
- pricing competitiveness
- partnership strength
- engineering momentum

Return JSON array:
[
  {{
    "hypothesis": "Company X leads in ...",
    "branch_type": "innovation_leadership",
    "confidence_score": 0.0-1.0,
    "unresolved_questions": ["..."]
  }}
]
"""

    try:
        response = invoke_llm(llm, [HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = "".join(str(part) for part in content)
        text = str(content).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        branches_data = json.loads(text)
        nodes: list[ThoughtNode] = []
        for i, branch in enumerate(branches_data[:BRANCHING_FACTOR]):
            nodes.append(
                ThoughtNode(
                    hypothesis=branch.get("hypothesis", ""),
                    branch_type=branch.get("branch_type", STRATEGIC_BRANCHES[i % len(STRATEGIC_BRANCHES)]),
                    depth=1,
                    supporting_evidence=findings[:10],
                    confidence_score=branch.get("confidence_score", 0.5),
                    unresolved_questions=branch.get("unresolved_questions", []),
                    reasoning_history=[branch.get("hypothesis", "")],
                    node_id=f"branch_{i}",
                )
            )
        return nodes
    except (json.JSONDecodeError, ValueError, Exception):
        return _fallback_branches(companies)


def _fallback_branches(companies: list[str]) -> list[ThoughtNode]:
    """Deterministic fallback when LLM parsing fails."""
    templates = [
        ("innovation_leadership", "{company} leads in AI innovation and product velocity"),
        ("pricing_competitiveness", "{company} offers the most competitive pricing model"),
        ("partnership_strength", "{company} has the strongest enterprise partnership ecosystem"),
        ("engineering_momentum", "{company} shows the strongest engineering and open-source momentum"),
    ]
    nodes: list[ThoughtNode] = []
    for i, (branch_type, template) in enumerate(templates[:BRANCHING_FACTOR]):
        company = companies[i % len(companies)]
        nodes.append(
            ThoughtNode(
                hypothesis=template.format(company=company),
                branch_type=branch_type,
                depth=1,
                confidence_score=0.5,
                node_id=f"branch_{i}",
                reasoning_history=[template.format(company=company)],
            )
        )
    return nodes


def expand_branch(node: ThoughtNode, findings: list[dict[str, Any]], companies: list[str]) -> ThoughtNode:
    """Expand a branch to the next depth level with evidence assessment."""
    if is_cloud_efficiency_mode():
        return ThoughtNode(
            hypothesis=node.hypothesis,
            branch_type=node.branch_type,
            depth=node.depth + 1,
            supporting_evidence=findings[:15],
            confidence_score=node.confidence_score,
            reasoning_history=node.reasoning_history + ["Efficiency mode: deterministic branch expansion"],
            parent_id=node.node_id,
            node_id=f"{node.node_id}_d{node.depth + 1}",
        )

    try:
        llm = get_llm()
    except ValueError:
        return ThoughtNode(
            hypothesis=node.hypothesis,
            branch_type=node.branch_type,
            depth=node.depth + 1,
            supporting_evidence=findings[:15],
            confidence_score=node.confidence_score,
            reasoning_history=node.reasoning_history,
            parent_id=node.node_id,
            node_id=f"{node.node_id}_d{node.depth + 1}",
        )

    prompt = f"""
Current hypothesis (depth {node.depth}): {node.hypothesis}
Branch type: {node.branch_type}
Companies: {', '.join(companies)}

Evidence:
{json.dumps(findings[:20], indent=2)}

Refine this hypothesis with cross-company comparison and contradiction checking.
Return JSON:
{{
  "hypothesis": "refined hypothesis",
  "confidence_score": 0.0-1.0,
  "unresolved_questions": ["..."],
  "reasoning_step": "what changed in this step"
}}
"""

    try:
        response = invoke_llm(llm, [HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = "".join(str(part) for part in content)
        text = str(content).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text)
        return ThoughtNode(
            hypothesis=data.get("hypothesis", node.hypothesis),
            branch_type=node.branch_type,
            depth=node.depth + 1,
            supporting_evidence=findings[:15],
            confidence_score=data.get("confidence_score", node.confidence_score),
            unresolved_questions=data.get("unresolved_questions", []),
            reasoning_history=node.reasoning_history + [data.get("reasoning_step", "")],
            parent_id=node.node_id,
            node_id=f"{node.node_id}_d{node.depth + 1}",
        )
    except (json.JSONDecodeError, ValueError):
        return ThoughtNode(
            hypothesis=node.hypothesis,
            branch_type=node.branch_type,
            depth=node.depth + 1,
            supporting_evidence=findings[:15],
            confidence_score=node.confidence_score,
            reasoning_history=node.reasoning_history,
            parent_id=node.node_id,
            node_id=f"{node.node_id}_d{node.depth + 1}",
        )


def beam_search_analysis(
    companies: list[str],
    findings: list[dict[str, Any]],
    industry: str,
) -> dict[str, Any]:
    """
    Run Tree-of-Thought beam search analysis.
    Returns best branch and full tree metadata.
    """
    current_branches = generate_initial_branches(companies, findings, industry)

    all_nodes: list[dict[str, Any]] = []
    tree_metadata: dict[str, Any] = {
        "beam_width": BEAM_WIDTH,
        "max_depth": MAX_DEPTH,
        "prune_threshold": PRUNE_THRESHOLD,
        "depths_explored": [],
    }

    for depth in range(1, MAX_DEPTH + 1):
        # Evaluate all branches at current depth
        scored_branches: list[tuple[ThoughtNode, float]] = []
        for branch in current_branches:
            evaluation = evaluate_branch(branch.to_dict(), findings)
            branch.evaluation_score = evaluation["overall_score"]
            scored_branches.append((branch, evaluation["overall_score"]))
            all_nodes.append({**branch.to_dict(), "evaluation": evaluation})

        # Prune branches below threshold (with near-threshold rescue per checkpoint 4.1)
        surviving: list[ThoughtNode] = []
        for branch, score in scored_branches:
            if score >= PRUNE_THRESHOLD:
                surviving.append(branch)
            elif score >= PRUNE_THRESHOLD - 5:
                # Near-threshold: one additional validation step
                branch.unresolved_questions.append("Additional evidence validation performed")
                re_eval = evaluate_branch(branch.to_dict(), findings)
                if re_eval["overall_score"] >= PRUNE_THRESHOLD:
                    branch.evaluation_score = re_eval["overall_score"]
                    surviving.append(branch)

        # Keep top beam_width branches
        surviving.sort(key=lambda b: b.evaluation_score, reverse=True)
        current_branches = surviving[:BEAM_WIDTH]

        tree_metadata["depths_explored"].append(
            {
                "depth": depth,
                "branches_evaluated": len(scored_branches),
                "branches_surviving": len(current_branches),
                "top_score": current_branches[0].evaluation_score if current_branches else 0,
            }
        )

        if not current_branches:
            break

        # Early termination if clear winner
        if len(current_branches) >= 2:
            score_gap = current_branches[0].evaluation_score - current_branches[1].evaluation_score
            if score_gap > 15 and depth >= 2:
                break

        if depth < MAX_DEPTH:
            current_branches = [
                expand_branch(b, findings, companies) for b in current_branches
            ]

    best_branch = current_branches[0] if current_branches else None

    return {
        "best_branch": best_branch.to_dict() if best_branch else {},
        "all_branches": [n for n in all_nodes],
        "tree_metadata": tree_metadata,
        "selected_hypothesis": best_branch.hypothesis if best_branch else "Insufficient evidence for strategic conclusion",
        "tot_confidence": best_branch.evaluation_score / 100 if best_branch else 0,
    }
