"""Fact extraction agent - converts documents to structured facts."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import get_llm, load_prompt
from memory.schemas import ExtractedFact, SourceType
from workflows.state import ResearchState


def extract_facts(state: ResearchState) -> dict[str, Any]:
    """Extract structured facts from collected documents."""
    documents = state.get("documents", [])
    if not documents:
        return {"status_message": "No documents to extract facts from"}

    findings = list(state.get("findings", []))
    processed_urls = {f.get("source_url") for f in findings}
    llm = get_llm()
    system_prompt = load_prompt("extraction")
    companies = state.get("companies", [])
    categories = state.get("categories", [])

    for doc in documents:
        if doc["url"] in processed_urls:
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
            return {"findings": findings, "errors": errors}

    return {
        "findings": findings,
        "status_message": f"Extracted {len(findings)} facts from {len(documents)} documents",
    }
