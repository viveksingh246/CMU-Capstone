"""ChromaDB vector store for semantic retrieval."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from config import settings
from rag.chunking import chunk_document


class _LocalHashEmbedding(embedding_functions.EmbeddingFunction):
    """Deterministic local embeddings for offline/testing use."""

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in input:
            digest = hashlib.sha256(text.encode()).digest()
            vector = [(digest[i % len(digest)] / 255.0) for i in range(384)]
            embeddings.append(vector)
        return embeddings


class DocumentVectorStore:
    """ChromaDB-backed vector store for research documents."""

    def __init__(self, collection_name: str = "ci_documents", persist_path: Path | None = None):
        path = persist_path or settings.chroma_path
        path.mkdir(parents=True, exist_ok=True)

        # Keep Chroma model cache inside the project directory
        cache_dir = path / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("CHROMA_CACHE_DIR", str(cache_dir))

        self._client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._embedding_fn = _LocalHashEmbedding()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._embedding_fn,
        )

    def index_documents(self, documents: list[dict[str, Any]], run_id: str | None = None) -> int:
        """Chunk and index documents. Returns number of chunks indexed."""
        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for doc in documents:
            content = doc.get("content") or doc.get("snippet", "")
            if not content:
                continue

            base_meta = {
                "url": doc.get("url", ""),
                "title": doc.get("title", ""),
                "source_name": doc.get("source_name", ""),
                "published_date": doc.get("published_date") or "",
                "source_type": str(doc.get("source_type", "other")),
                "run_id": run_id or "",
            }

            for chunk in chunk_document(
                content,
                metadata=base_meta,
                chunk_tokens=settings.rag_chunk_tokens,
                overlap_ratio=settings.rag_chunk_overlap,
            ):
                chunk_id = hashlib.md5(
                    f"{base_meta['url']}:{chunk['metadata']['chunk_index']}".encode()
                ).hexdigest()
                ids.append(chunk_id)
                texts.append(chunk["text"])
                metadatas.append(chunk["metadata"])

        if not ids:
            return 0

        self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        return len(ids)

    def query(
        self,
        query_text: str,
        top_k: int | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic similarity search returning ranked chunks."""
        k = top_k or settings.rag_top_k
        results = self._collection.query(
            query_texts=[query_text],
            n_results=k,
            where=where,
        )

        chunks: list[dict[str, Any]] = []
        if not results["documents"] or not results["documents"][0]:
            return chunks

        for idx, text in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][idx] if results["metadatas"] else {}
            distance = results["distances"][0][idx] if results.get("distances") else None
            similarity = round(1 - distance, 4) if distance is not None else None

            chunks.append(
                {
                    "text": text,
                    "metadata": meta,
                    "similarity": similarity,
                    "source_url": meta.get("url", ""),
                    "title": meta.get("title", ""),
                    "published_date": meta.get("published_date", ""),
                }
            )

        return chunks

    def reset(self) -> None:
        """Clear the collection (useful for tests)."""
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._embedding_fn,
        )


def retrieve_relevant_chunks(
    query: str,
    store: DocumentVectorStore | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Retrieve top-ranked document chunks for a query."""
    vector_store = store or DocumentVectorStore()
    return vector_store.query(query, top_k=top_k)
