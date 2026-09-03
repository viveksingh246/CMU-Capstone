"""Short-term memory for ReAct reasoning loop (Checkpoint 2.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

ReActPhase = Literal["reason", "plan", "act", "observe", "reflect", "decide", "report"]


class ShortTermMemory:
    """Tracks intermediate reasoning, search progress, and workflow context."""

    def __init__(self) -> None:
        self._steps: list[dict[str, Any]] = []
        self._objective: str = ""
        self._search_progress: dict[str, Any] = {}
        self._comparison_results: dict[str, Any] = {}

    def set_objective(self, objective: str) -> None:
        self._objective = objective

    def record_step(
        self,
        phase: ReActPhase,
        action: str,
        observation: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._steps.append(
            {
                "phase": phase,
                "action": action,
                "observation": observation,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def update_search_progress(self, **kwargs: Any) -> None:
        self._search_progress.update(kwargs)

    def set_comparison_results(self, results: dict[str, Any]) -> None:
        self._comparison_results = results

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self._objective,
            "reasoning_steps": self._steps,
            "search_progress": self._search_progress,
            "comparison_results": self._comparison_results,
            "step_count": len(self._steps),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShortTermMemory:
        memory = cls()
        memory._objective = data.get("objective", "")
        memory._steps = list(data.get("reasoning_steps", []))
        memory._search_progress = dict(data.get("search_progress", {}))
        memory._comparison_results = dict(data.get("comparison_results", {}))
        return memory


def record_react_step(
    state: dict[str, Any],
    phase: ReActPhase,
    action: str,
    observation: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Helper to append a ReAct step to workflow state."""
    stm_data = state.get("short_term_memory", {})
    memory = ShortTermMemory.from_dict(stm_data)
    memory.record_step(phase, action, observation, metadata)
    return {"short_term_memory": memory.to_dict()}
