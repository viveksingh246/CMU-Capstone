"""Fact extraction agent - converts documents to structured facts."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import (
    LLMBudgetExhausted,
    can_invoke_llm,
    get_llm,
    invoke_llm,
    is_cloud_efficiency_mode,
    load_prompt,
)
from config import settings
from memory.schemas import ExtractedFact, SourceType
from memory.short_term import record_react_step
from rag.vector_store import retrieve_relevant_chunks
from workflows.state import ResearchState


def _get_rag_context(companies: list[str], categories: list[str]) -> list[dict[str, Any]]:
    """Retrieve semantically relevant chunks for extraction (Checkpoint 3.1)."""
    if not settings.use_rag or is_cloud_efficiency_mode():
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


def _normalize_fact_dict(fact_dict: dict[str, Any], doc: dict[str, Any]) -> dict[str, Any]:
    if not fact_dict.get("source_url"):
        fact_dict["source_url"] = doc["url"]
    if not fact_dict.get("source_title"):
        fact_dict["source_title"] = doc.get("title") or "Unknown"
    if not fact_dict.get("evidence"):
        fact_dict["evidence"] = (
            fact_dict.get("claim")
            or doc.get("snippet")
            or doc.get("content", "")[:500]
            or "See source document"
        )
    if not fact_dict.get("published_date"):
        fact_dict["published_date"] = doc.get("published_date")
    if "source_type" in fact_dict:
        try:
            fact_dict["source_type"] = SourceType(fact_dict["source_type"])
        except ValueError:
            fact_dict["source_type"] = SourceType.OTHER
    elif doc.get("source_type"):
        try:
            raw = doc["source_type"]
            fact_dict["source_type"] = raw if isinstance(raw, SourceType) else SourceType(str(raw))
        except ValueError:
            fact_dict["source_type"] = SourceType.OTHER
    return fact_dict


def _append_parsed_facts(
    findings: list[dict[str, Any]],
    facts_data: Any,
    doc: dict[str, Any],
) -> None:
    if isinstance(facts_data, dict):
        facts_data = facts_data.get("facts", [facts_data])
    if not isinstance(facts_data, list):
        return

    for fact_dict in facts_data:
        if not isinstance(fact_dict, dict):
            continue
        normalized = _normalize_fact_dict(dict(fact_dict), doc)
        fact = ExtractedFact.model_validate(normalized)
        findings.append(fact.model_dump(mode="json"))


def _parse_llm_json(text: str) -> Any:
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0]
    return json.loads(cleaned)


def _heuristic_facts_from_doc(
    doc: dict[str, Any],
    companies: list[str],
    categories: list[str],
) -> list[dict[str, Any]]:
    """Deterministic extraction when LLM budget is exhausted or in efficiency mode."""
    content = (doc.get("content") or doc.get("snippet") or "").strip()
    if len(content) < 20:
        return []

    facts: list[dict[str, Any]] = []
    source_type = doc.get("source_type", SourceType.OTHER)
    for company in companies:
        if company.lower() not in content.lower() and company.lower() not in doc.get("title", "").lower():
            continue
        for category in categories:
            claim = content[:240].strip()
            if not claim:
                continue
            facts.append(
                ExtractedFact(
                    company=company,
                    category=category,
                    claim=claim,
                    evidence=content[:500],
                    source_url=doc["url"],
                    source_title=doc.get("title") or "Unknown",
                    published_date=doc.get("published_date"),
                    source_type=source_type if isinstance(source_type, SourceType) else SourceType.OTHER,
                    confidence=0.55,
                    is_company_claim=False,
                ).model_dump(mode="json")
            )
    return facts


def _extract_with_llm_batch(
    docs: list[dict[str, Any]],
    companies: list[str],
    categories: list[str],
    system_prompt: str,
    rag_supplement: str,
) -> list[dict[str, Any]]:
    """Extract facts from multiple documents in a single LLM call."""
    if not docs or not can_invoke_llm():
        return []

    doc_blocks = []
    for index, doc in enumerate(docs, start=1):
        doc_blocks.append(
            f"""Document {index}:
Title: {doc.get('title', 'Unknown')}
URL: {doc.get('url', '')}
Published: {doc.get('published_date', 'Unknown')}
Content:
{doc.get('content', doc.get('snippet', ''))[:2500]}
"""
        )

    user_content = f"""
Companies to analyze: {', '.join(companies)}
Categories: {', '.join(categories)}

{chr(10).join(doc_blocks)}
{rag_supplement}

Extract facts as a JSON array. Each fact must include:
company, category, claim, evidence, source_url, source_title,
published_date, source_type, confidence (0-1), is_company_claim (bool)

Use the matching document URL for source_url. Return only the JSON array.
"""

    llm = get_llm()
    response = invoke_llm(
        llm,
        [SystemMessage(content=system_prompt), HumanMessage(content=user_content)],
    )
    content = response.content
    if isinstance(content, list):
        content = "".join(str(part) for part in content)

    facts_data = _parse_llm_json(str(content))
    findings: list[dict[str, Any]] = []
    if isinstance(facts_data, list):
        url_to_doc = {doc["url"]: doc for doc in docs}
        for fact_dict in facts_data:
            if not isinstance(fact_dict, dict):
                continue
            doc = url_to_doc.get(fact_dict.get("source_url", ""), docs[0])
            normalized = _normalize_fact_dict(dict(fact_dict), doc)
            fact = ExtractedFact.model_validate(normalized)
            findings.append(fact.model_dump(mode="json"))
    return findings


def extract_facts(state: ResearchState) -> dict[str, Any]:
    """Extract structured facts from collected documents and RAG context."""
    documents = state.get("documents", [])
    if not documents:
        return {"status_message": "No documents to extract facts from"}

    findings = list(state.get("findings", []))
    processed_urls = {f.get("source_url") for f in findings}
    companies = state.get("companies", [])
    categories = state.get("categories", [])
    errors = list(state.get("errors", []))
    efficiency_mode = is_cloud_efficiency_mode()

    retrieved_context = _get_rag_context(companies, categories)
    rag_supplement = ""
    if retrieved_context:
        rag_supplement = "\n\nAdditional retrieved context:\n" + "\n---\n".join(
            c.get("text", "")[:500] for c in retrieved_context[:3]
        )

    pending_docs = [doc for doc in documents if doc["url"] not in processed_urls]
    if not pending_docs:
        return {"findings": findings, "status_message": "All documents already processed"}

    system_prompt = load_prompt("extraction")

    if efficiency_mode:
        llm_doc_limit = settings.max_llm_extraction_documents
        llm_docs = pending_docs[:llm_doc_limit]
        heuristic_docs = pending_docs[llm_doc_limit:]

        if llm_docs and can_invoke_llm():
            try:
                findings.extend(
                    _extract_with_llm_batch(
                        llm_docs, companies, categories, system_prompt, rag_supplement
                    )
                )
            except (json.JSONDecodeError, ValueError, LLMBudgetExhausted) as exc:
                errors.append(f"Batch extraction fallback: {exc}")
                for doc in llm_docs:
                    findings.extend(_heuristic_facts_from_doc(doc, companies, categories))
        elif llm_docs:
            for doc in llm_docs:
                findings.extend(_heuristic_facts_from_doc(doc, companies, categories))

        for doc in heuristic_docs:
            findings.extend(_heuristic_facts_from_doc(doc, companies, categories))
    else:
        for doc in pending_docs:
            if not can_invoke_llm():
                findings.extend(_heuristic_facts_from_doc(doc, companies, categories))
                continue

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
                llm = get_llm()
                response = invoke_llm(
                    llm,
                    [SystemMessage(content=system_prompt), HumanMessage(content=user_content)],
                )
                content = response.content
                if isinstance(content, list):
                    content = "".join(str(part) for part in content)
                facts_data = _parse_llm_json(str(content))
                _append_parsed_facts(findings, facts_data, doc)
            except (json.JSONDecodeError, ValueError, LLMBudgetExhausted) as exc:
                errors.append(f"Extraction failed for {doc.get('url', 'unknown')}: {exc}")
                findings.extend(_heuristic_facts_from_doc(doc, companies, categories))

    react = record_react_step(
        state,
        "observe",
        f"Extracted {len(findings)} facts",
        f"Efficiency mode: {efficiency_mode}, RAG chunks: {len(retrieved_context)}",
    )

    mode_note = " (cloud efficiency mode)" if efficiency_mode else ""
    return {
        **react,
        "findings": findings,
        "retrieved_context": retrieved_context,
        "errors": errors,
        "status_message": (
            f"Extracted {len(findings)} facts from {len(documents)} documents{mode_note}"
        ),
    }
