"""Fact extraction agent - converts documents to structured facts."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import get_llm, load_prompt
from config import settings
from memory.schemas import ExtractedFact, SourceType
from memory.short_term import record_react_step
from rag.vector_store import retrieve_relevant_chunks
from workflows.state import ResearchState


def _get_rag_context(companies: list[str], categories: list[str]) -> list[dict[str, Any]]:
    """Retrieve semantically relevant chunks for extraction (Checkpoint 3.1)."""
    if not settings.use_rag:
        return []

    queries = [
        f"{company} {category} competitive intelligence"
        for company in companies[:3]
        for category in categories[:3]
    ]

    all_chunks: list[dict[str, Any]] = []
    seen_texts: set[str] = set()

    for query in queries[:6]:
        chunks = retrieve_relevant_chunks(query, top_k=2)
        for chunk in chunks:
            text_key = chunk.get("text", "")[:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                all_chunks.append(chunk)

    return all_chunks[: settings.rag_top_k]


def extract_facts(state: ResearchState) -> dict[str, Any]:
    """Extract structured facts from collected documents and RAG context."""
    documents = state.get("documents", [])
    if not documents:
        return {"status_message": "No documents to extract facts from"}

    findings = list(state.get("findings", []))
    processed_urls = {f.get("source_url") for f in findings}
    llm = get_llm()
    system_prompt = load_prompt("extraction")
    companies = state.get("companies", [])
    categories = state.get("categories", [])

    # RAG: retrieve relevant context before extraction
    retrieved_context = _get_rag_context(companies, categories)

    for doc in documents:
        if doc["url"] in processed_urls:
            continue

        # Augment document with relevant RAG chunks
        rag_supplement = ""
        if retrieved_context:
            rag_supplement = "\n\nAdditional retrieved context:\n" + "\n---\n".join(
                c.get("text", "")[:500] for c in retrieved_context[:3]
            )

        user_content = f"""
Companies to analyze: {', '.join(companies)}
Categories: {', '.join(categories)}

Source document:
Title: {doc.get('title', 'Unknown')}
URL: {doc.get('url', '')}
Published: {doc.get('published_date', 'Unknown')}
Content:
{doc.get('content', doc.get('snippet', ''))[:4000]}
{rag_supplement}

Extract facts as a JSON array. Each fact must have:
company, category, claim, evidence, source_url, source_title,
published_date, source_type, confidence (0-1), is_company_claim (bool)

Return only the JSON array, no other text.
"""

        try:
            response = llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
            )
            content = response.content
            if isinstance(content, list):
                content = "".join(str(part) for part in content)

            text = str(content).strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            facts_data = json.loads(text)
            if isinstance(facts_data, dict):
                facts_data = facts_data.get("facts", [facts_data])

            for fact_dict in facts_data:
                fact_dict.setdefault("source_url", doc["url"])
                fact_dict.setdefault("source_title", doc.get("title", ""))
                fact_dict.setdefault("published_date", doc.get("published_date"))
                if "source_type" in fact_dict:
                    try:
                        fact_dict["source_type"] = SourceType(fact_dict["source_type"])
                    except ValueError:
                        fact_dict["source_type"] = SourceType.OTHER
                fact = ExtractedFact.model_validate(fact_dict)
                findings.append(fact.model_dump())

        except (json.JSONDecodeError, ValueError, Exception) as exc:
            errors = list(state.get("errors", []))
            errors.append(f"Extraction failed for {doc.get('url', 'unknown')}: {exc}")
            return {"findings": findings, "errors": errors, "retrieved_context": retrieved_context}

    react = record_react_step(
        state,
        "observe",
        f"Extracted {len(findings)} facts",
        f"Used {len(retrieved_context)} RAG context chunks",
    )

    return {
        **react,
        "findings": findings,
        "retrieved_context": retrieved_context,
        "status_message": f"Extracted {len(findings)} facts from {len(documents)} documents (RAG: {len(retrieved_context)} chunks)",
    }
