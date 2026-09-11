"""Research collection agent - searches sources and gathers documents."""

from typing import Any

from agents.llm import get_effective_max_queries_per_pass, is_cloud_efficiency_mode
from config import settings
from memory.short_term import record_react_step
from rag.vector_store import DocumentVectorStore
from tools.mcp_tools import search_web_mcp
from workflows.state import ResearchState


def collect_research(state: ResearchState) -> dict[str, Any]:
    """Execute pending search queries and collect documents."""
    queries = state.get("search_queries", [])
    completed = set(state.get("completed_queries", []))
    pending = [q for q in queries if q not in completed]

    if not pending:
        return {"status_message": "No pending search queries"}

    documents = list(state.get("documents", []))
    seen_urls = {doc["url"] for doc in documents}
    new_completed: list[str] = []
    errors = list(state.get("errors", []))

    # Process a limited number of queries per iteration (fewer in fast/efficiency mode)
    query_limit = get_effective_max_queries_per_pass()
    for query in pending[:query_limit]:
        try:
            results = search_web_mcp(query, max_results=3)
            for result in results:
                if result["url"] not in seen_urls:
                    documents.append(result)
                    seen_urls.add(result["url"])
            new_completed.append(query)
        except Exception as exc:
            errors.append(f"Search failed for '{query}': {exc}")

    react = record_react_step(
        state,
        "act",
        f"Executed {len(new_completed)} search queries",
        f"Collected {len(documents)} total documents",
        {"queries": new_completed},
    )

    return {
        **react,
        "documents": documents,
        "completed_queries": list(completed) + new_completed,
        "errors": errors,
        "status_message": f"Collected {len(documents)} documents ({len(new_completed)} queries executed)",
    }


def index_documents_for_rag(state: ResearchState) -> dict[str, Any]:
    """Index collected documents into ChromaDB for semantic retrieval (Checkpoint 3.1)."""
    if not settings.use_rag or is_cloud_efficiency_mode():
        return {"status_message": "RAG indexing skipped (disabled or fast mode)"}

    documents = state.get("documents", [])
    if not documents:
        return {"rag_chunks_indexed": 0, "status_message": "No documents to index"}

    try:
        store = DocumentVectorStore()
        run_id = str(state.get("run_id", "current"))
        chunks_indexed = store.index_documents(documents, run_id=run_id)

        react = record_react_step(
            state,
            "observe",
            f"Indexed {chunks_indexed} document chunks into ChromaDB",
            f"From {len(documents)} source documents",
        )

        return {
            **react,
            "rag_chunks_indexed": chunks_indexed,
            "status_message": f"RAG: indexed {chunks_indexed} chunks from {len(documents)} documents",
        }
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(f"RAG indexing failed: {exc}")
        return {"rag_chunks_indexed": 0, "errors": errors, "status_message": "RAG indexing failed"}
