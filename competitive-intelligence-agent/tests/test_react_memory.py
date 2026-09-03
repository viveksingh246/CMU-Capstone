"""Tests for ReAct short-term memory (Checkpoint 2.1)."""

from memory.short_term import ShortTermMemory, record_react_step


def test_short_term_memory_records_steps():
    memory = ShortTermMemory()
    memory.set_objective("Compare Snowflake vs Databricks")
    memory.record_step("reason", "Interpret objective", "Two cloud data platforms")
    memory.record_step("plan", "Create research plan", "6 categories, 12 queries")

    data = memory.to_dict()
    assert data["objective"] == "Compare Snowflake vs Databricks"
    assert data["step_count"] == 2
    assert data["reasoning_steps"][0]["phase"] == "reason"
    assert data["reasoning_steps"][1]["phase"] == "plan"


def test_short_term_memory_roundtrip():
    memory = ShortTermMemory()
    memory.set_objective("Test objective")
    memory.record_step("act", "Search sources", "Found 10 documents")
    memory.update_search_progress(documents_collected=10)

    restored = ShortTermMemory.from_dict(memory.to_dict())
    assert restored.to_dict()["objective"] == "Test objective"
    assert restored.to_dict()["search_progress"]["documents_collected"] == 10


def test_record_react_step_updates_state():
    state = {"short_term_memory": {}}
    result = record_react_step(state, "observe", "Validate evidence", "85% verification rate")

    assert "short_term_memory" in result
    assert result["short_term_memory"]["step_count"] == 1
    assert result["short_term_memory"]["reasoning_steps"][0]["phase"] == "observe"
