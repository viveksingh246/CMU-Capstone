"""Tests for Research Agent and RAG indexing."""

from unittest.mock import patch

from agents.researcher import collect_research, index_documents_for_rag


def test_collect_research_deduplicates_urls():
    state = {
        "search_queries": ["Snowflake products"],
        "completed_queries": [],
        "documents": [],
        "errors": [],
        "short_term_memory": {},
    }
    mock_results = [
        {"url": "https://snowflake.com", "title": "Snowflake", "snippet": "Data cloud", "content": "Data cloud platform"},
        {"url": "https://snowflake.com", "title": "Snowflake dup", "snippet": "dup", "content": "dup"},
    ]

    with patch("agents.researcher.search_web_mcp", return_value=mock_results):
        result = collect_research(state)

    assert len(result["documents"]) == 1
    assert "Snowflake products" in result["completed_queries"]


def test_collect_research_no_pending_queries():
    state = {"search_queries": ["done"], "completed_queries": ["done"], "documents": []}
    result = collect_research(state)
    assert "No pending" in result["status_message"]


def test_index_documents_for_rag_disabled():
    state = {"documents": [{"url": "https://a.com", "content": "text"}], "errors": []}
    with patch("agents.researcher.settings") as mock_settings:
        mock_settings.use_rag = False
        result = index_documents_for_rag(state)
    assert "skipped" in result["status_message"].lower()


def test_index_documents_for_rag_indexes_chunks(tmp_path):
    state = {
        "documents": [
            {
                "url": "https://snowflake.com/ai",
                "title": "AI",
                "content": "Snowflake Cortex AI capabilities for analytics and machine learning workloads in the cloud.",
                "source_type": "official_website",
            }
        ],
        "errors": [],
        "short_term_memory": {},
    }
    with patch("agents.researcher.settings") as mock_settings, patch(
        "agents.researcher.DocumentVectorStore"
    ) as MockStore:
        mock_settings.use_rag = True
        mock_settings.chroma_path = tmp_path
        mock_settings.rag_chunk_tokens = 650
        mock_settings.rag_chunk_overlap = 0.15
        instance = MockStore.return_value
        instance.index_documents.return_value = 2

        result = index_documents_for_rag(state)

    assert result["rag_chunks_indexed"] == 2
    instance.index_documents.assert_called_once()
