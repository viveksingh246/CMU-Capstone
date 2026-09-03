"""Tests for RAG chunking and vector store (Checkpoint 3.1)."""

from rag.chunking import chunk_document
from rag.vector_store import DocumentVectorStore


def test_chunk_document_splits_with_overlap():
    text = "A" * 5000
    chunks = chunk_document(text, metadata={"url": "https://example.com"}, chunk_tokens=500, overlap_ratio=0.15)

    assert len(chunks) >= 2
    assert all("text" in c and "metadata" in c for c in chunks)
    assert chunks[0]["metadata"]["url"] == "https://example.com"
    assert chunks[0]["metadata"]["chunk_index"] == 0


def test_chunk_document_empty_text():
    assert chunk_document("") == []
    assert chunk_document("   ") == []


def test_vector_store_index_and_query(tmp_path):
    store = DocumentVectorStore(persist_path=tmp_path / "chroma_test")

    documents = [
        {
            "url": "https://snowflake.com/ai",
            "title": "Snowflake AI Features",
            "content": "Snowflake Cortex provides generative AI capabilities for data analytics and machine learning workloads.",
            "source_type": "official_website",
        },
        {
            "url": "https://databricks.com/ml",
            "title": "Databricks ML Platform",
            "content": "Databricks offers MLflow and Unity Catalog for enterprise machine learning and data governance.",
            "source_type": "official_website",
        },
    ]

    indexed = store.index_documents(documents, run_id="test_run")
    assert indexed >= 2

    results = store.query("Snowflake AI generative capabilities", top_k=3)
    assert len(results) >= 1
    assert results[0]["text"]

    store.reset()
