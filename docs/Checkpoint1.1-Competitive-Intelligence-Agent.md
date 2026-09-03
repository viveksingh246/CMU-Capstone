# Project Checkpoint 1.1 — Competitive Intelligence Research Agent

**Submission format:** PDF or Microsoft Word (500–750 words for Sections 1–5)  
**Category:** Research Assistant  
**Status:** Planning and system design (no code required for this checkpoint)

---

## 1. Describe Your Agent and the Problem It Solves

My project is a **Competitive Intelligence Research Agent** — a Research Assistant that autonomously monitors and analyzes competitors across multiple public information sources. Organizations in fast-moving industries (for example, cloud data and AI platforms) must track competitor products, pricing, partnerships, hiring trends, and AI capabilities. Today this work is manual, fragmented across browser tabs and spreadsheets, and quickly becomes outdated.

The agent solves this by planning structured research, collecting evidence from external sources, validating claims, comparing companies across strategic dimensions, and producing executive-ready reports with citations. The problem matters because leadership and product teams need timely, source-backed intelligence to prioritize roadmaps, prepare for sales conversations, and respond to market shifts — not one-off summaries that lack evidence or historical context.

**Target users** include product managers, business analysts, sales enablement teams, strategy researchers, and executives who need recurring competitive briefings without hiring a dedicated market-research function.

**Default MVP scope (capstone):**

| Setting | Value |
|---------|-------|
| Industry | Cloud Data & AI Platforms |
| Competitors | Snowflake, Databricks, Google BigQuery |
| Categories | Products, Features, Pricing, AI capabilities, Partnerships, Hiring trends |
| Outputs | Executive summary, comparison matrix, SWOT, weighted scorecard, charts, alerts |

---

## 2. Explain Why a Standalone LLM Is Not Enough

A single ChatGPT prompt cannot solve this problem reliably. Competitive intelligence requires **continuous, multi-step agentic behavior**, not a one-shot chat response.

A standalone LLM lacks:

- **Tool calling** — It cannot autonomously query web search APIs, news feeds, GitHub, or job boards.
- **External data** — It has no live access to current competitor websites, press releases, or hiring pages.
- **Memory** — It cannot store prior research runs, compare findings over time, or detect what changed since last month.
- **Planning** — It does not break a broad request (“compare three cloud platforms”) into category-specific search tasks with completion criteria.
- **Multiple steps** — It does not follow an observe → reason → act loop across planning, search, extraction, validation, analysis, and reporting.
- **Feedback loop** — It cannot recognize missing evidence, generate follow-up queries, and search again before producing a final report.
- **Decision making** — It does not rank source credibility, distinguish company marketing claims from verified facts, or route the workflow based on completeness checks.

Instead of “ChatGPT summarizes competitors,” the agent **plans research**, **searches multiple sources**, **extracts structured facts with citations**, **validates evidence quality**, **loops until coverage thresholds are met**, **compares companies with SWOT and scorecards**, **detects historical changes**, **persists results to a database**, and **generates updated executive reports**.

---

## 3. Describe the Environment

The environment is **not** simply “the Internet.” It is a defined ecosystem of data sources, tools, storage, and users.

### Data Sources

| Source type | Examples | Used for |
|-------------|----------|----------|
| Official websites & docs | Product pages, pricing pages, documentation | Feature and product claims |
| News & press | Industry news APIs, press releases | Announcements, partnerships, launches |
| GitHub | Public repositories, release activity | Open-source signals, engineering momentum |
| Job postings | Public career pages and job boards | Hiring trends, capability investments |
| Regulatory filings | SEC filings (where applicable) | Financial and strategic disclosures |

### Tools & APIs

| Tool | Role |
|------|------|
| OpenAI API (GPT-4o-mini) | Planning, extraction, validation, analysis, report generation |
| Tavily Search API | Live web, news, and document retrieval |
| LangGraph | Multi-step agent workflow orchestration |
| SQLite database | Long-term memory for findings, scores, alerts, and research runs |
| MCP (Model Context Protocol) servers | Expose search and memory tools to external clients (e.g., Cursor IDE) |
| Streamlit | User interface for configuration, research execution, and visualizations |
| Plotly | Scorecard bar charts, radar charts, heatmaps, timelines |

### Users

- **Primary:** Product managers and strategy analysts running competitor comparisons
- **Secondary:** Sales enablement and executives consuming generated reports
- **Developer:** Capstone student building and extending the agent via Python, tests, and MCP integration

### Guardrails

- Every important claim must include a source URL
- Unknown information is marked “not publicly available”
- Marketing statements are labeled as company claims
- Facts are distinguished from analytical assessments (e.g., scorecard ratings)

---

## 4. Describe the Actions Your Agent Performs

The agent executes the following major tasks in sequence, orchestrated by a LangGraph state machine:

1. **Parse user request** — Accept industry, companies (2–5), categories, date range, report depth, and alert preferences.
2. **Check memory** — Load previous findings for requested companies from SQLite to enable historical comparison.
3. **Create research plan** — LLM generates structured tasks with search queries, preferred sources, and completion criteria per category.
4. **Search sources** — Execute web/news/GitHub/job queries via MCP search tools; deduplicate documents by URL.
5. **Extract facts** — Convert raw documents into structured JSON facts (company, category, claim, evidence, source, confidence).
6. **Validate evidence** — Score source credibility, flag unsupported claims, and filter low-confidence findings.
7. **Check completeness** — Measure coverage per category per company; if gaps exist, generate additional queries and loop back to search (up to 3 iterations).
8. **Compare companies** — Produce feature matrix, pricing comparison, SWOT analysis, weighted scorecard, and strategic recommendations.
9. **Detect historical changes** — Compare current findings against prior memory to surface deltas and generate alerts.
10. **Save to memory** — Persist research run, findings, scores, and alerts to SQLite.
11. **Generate report** — Produce a Markdown executive report with downloadable output and Plotly visualizations.

**MCP tool servers (optional integration layer):**

| Server | Tools |
|--------|-------|
| `ci-search` | Web search, news search, GitHub search, job search |
| `ci-memory` | Save/retrieve findings, scores, alerts, research runs |

---

## 5. Explain the Feedback Loop

The agent’s core feedback loop operates at **two levels**: automated internal refinement and user-driven configuration.

### Internal feedback loop (automated)

```
Search → Extract → Validate → Check Completeness
                                    │
                    Missing evidence? ──Yes──► Generate new queries → Search again
                                    │
                                   No
                                    ▼
                          Compare → Detect Changes → Save → Report
```

**Example:** The user requests analysis of “AI capabilities” for three cloud platforms. After the first search pass, the completeness checker finds only one sourced fact for Company B in that category. The agent marks the category as “insufficient evidence,” appends targeted queries (`"Company B AI capabilities official documentation"`, `"Company B AI recent news"`), increments the iteration counter, and returns to the search step. This repeats until coverage thresholds are met or the maximum of three iterations is reached, at which point the agent proceeds to analysis and notes remaining gaps in the report.

A second feedback loop occurs at **memory comparison**: when prior findings exist, the agent detects changes (new product launches, pricing updates, hiring shifts) and generates alerts that inform the next research run’s context.

### User feedback loop (configuration)

Through the Streamlit UI, users refine future runs by adjusting:

- Industry preset and competitor list
- Analysis categories (e.g., add “Partnerships”)
- Research period (30–365 days)
- Report depth (summary / standard / detailed)
- Historical comparison and alert toggles

Each completed run is stored in memory, so subsequent analyses build on prior intelligence rather than starting from zero.

---

## Appendix A — Implementation Blueprint (Post–Checkpoint 1.1)

This appendix describes how to build the agent to match the reference implementation. It contains no proprietary or employer-specific information.

### Architecture overview

```
Streamlit UI (app.py)
        │
        ▼
LangGraph Workflow (workflows/competitive_intelligence_graph.py)
        │
        ├── agents/planner.py          → Research plan + search queries
        ├── agents/researcher.py       → Document collection
        ├── agents/extractor.py        → Structured fact extraction
        ├── agents/validator.py        → Evidence validation
        ├── agents/completeness.py      → Gap detection + re-search loop
        ├── agents/analyst.py          → SWOT, scorecard, recommendations
        ├── agents/memory_agent.py     → SQLite read/write
        └── agents/reporter.py         → Executive Markdown report
        │
        ▼
MCP Tool Layer (tools/mcp_tools.py)
        │
        ├── mcp_servers/search_server.py   → ci-search
        └── mcp_servers/memory_server.py   → ci-memory
        │
        ▼
SQLite (memory/competitive_intelligence.db)
```

### Recommended project structure

```
competitive-intelligence-agent/
├── app.py                          # Streamlit UI
├── config.py                       # Settings and environment
├── agents/                         # One module per workflow step
├── tools/                          # Search, MCP facade, document reader
├── workflows/                      # LangGraph state + graph definition
├── memory/                         # SQLite operations + Pydantic schemas
├── mcp_servers/                    # MCP search and memory servers
├── agent_mcp/                      # MCP client/server protocol
├── prompts/                        # LLM prompt templates
├── visualizations/                 # Plotly charts
├── tests/                          # Unit and integration tests
└── docs/                           # Design documents (this file)
```

### Seven-week build plan

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Problem definition & design | Architecture, schema, sample output (this checkpoint) |
| 2 | Search & data collection | Tavily integration, page extraction, source filtering |
| 3 | Fact extraction & validation | Structured JSON facts with citations and confidence |
| 4 | Memory & workflow | SQLite persistence, LangGraph completeness loop |
| 5 | Competitive analysis | SWOT, weighted scorecard, recommendations |
| 6 | UI & reporting | Streamlit app, Plotly charts, report download |
| 7 | Testing & presentation | Evaluation metrics, demo, documentation |

### Evaluation targets

| Metric | Target |
|--------|--------|
| Research coverage | ≥ 90% |
| Citation coverage | ≥ 90% |
| Source quality (official/reputable) | ≥ 70% |
| Extraction accuracy (manual review) | ≥ 85% |

### Key dependencies

- Python 3.9+
- `langgraph`, `langchain-core`, `langchain-openai`
- `streamlit`, `plotly`, `pydantic`, `pydantic-settings`
- `tavily-python` (optional; sample-data fallback for demos)

### Environment variables

```bash
OPENAI_API_KEY=          # Required
TAVILY_API_KEY=          # Optional (enables live search)
USE_MCP=true             # MCP tool layer on/off
MCP_TRANSPORT=inprocess  # inprocess | stdio
```

### Quick start (for later checkpoints)

```bash
make setup    # venv + deps + .env + database
make run      # Streamlit at http://localhost:8501
make test     # Run test suite
```

---

## Appendix B — Checkpoint 1.1 Submission Text (Copy-Paste Ready)

*The block below is the 500–750 word submission body covering all five required sections. Export to PDF or Word for Canvas upload.*

---

### 1. Describe Your Agent and the Problem It Solves

My project is a **Competitive Intelligence Research Agent** in the **Research Assistant** category. It autonomously monitors competitor websites, product releases, pricing pages, partnership announcements, hiring trends, GitHub activity, and AI-related news to help business leaders understand how their market is evolving.

Organizations in fast-moving technology markets struggle to maintain current, evidence-backed competitive intelligence. Information is scattered across official product pages, press releases, third-party news, open-source repositories, and job boards. Teams often rely on ad-hoc Google searches or static slide decks that are outdated within weeks. This matters because product roadmaps, sales positioning, and executive strategy all depend on knowing what competitors shipped, how they price, where they are hiring, and which capabilities they are emphasizing — ideally with verifiable sources, not assumptions.

**Target users** include product managers preparing roadmap decisions, business analysts producing market briefings, sales enablement teams supporting competitive deals, and executives who need concise, recurring intelligence summaries. My MVP focuses on the cloud data and AI platform market, comparing three public competitors (Snowflake, Databricks, and Google BigQuery) across products, features, pricing, AI capabilities, partnerships, and hiring trends.

### 2. Explain Why a Standalone LLM Is Not Enough

If ChatGPT alone could solve this with a single prompt, the project would not need to be an agent. A standalone LLM cannot autonomously retrieve live competitor data, remember what it found last month, or decide when more research is needed before answering.

My system requires **tool calling** to query web search APIs and retrieve documents; **external data** from current websites, news feeds, GitHub, and job postings; **persistent memory** in a SQLite database to store findings, scores, alerts, and prior research runs; **planning** that transforms a broad comparison request into category-specific tasks with search queries and completion criteria; **multiple steps** across planning, searching, extracting, validating, analyzing, and reporting; **decision making** to rank source credibility and route the workflow based on evidence quality; and a **feedback loop** that detects missing coverage and triggers follow-up searches before generating the final report. The agent also distinguishes verified facts from analytical assessments, labels marketing claims as company statements, and marks unavailable information rather than inventing pricing or private data.

### 3. Describe the Environment

The environment is not simply “the Internet.” It is a defined set of data sources, tools, storage, and users working together.

**Data sources:** competitor official websites and product documentation; industry news articles and press releases; GitHub repositories for engineering signals; public job postings for hiring trends; and regulatory filings where publicly available.

**Tools and APIs:** OpenAI API (GPT-4o-mini) for planning, extraction, validation, and analysis; Tavily Search API for live web retrieval; LangGraph for multi-step workflow orchestration; SQLite for long-term memory; Model Context Protocol (MCP) servers exposing search and memory tools; Streamlit for the user interface; and Plotly for scorecard and timeline visualizations.

**Users:** product managers and strategy analysts who configure and run research; sales and executive stakeholders who consume generated reports; and the capstone developer who builds, tests, and extends the system.

### 4. Describe the Actions Your Agent Performs

The agent performs these major tasks in sequence: (1) parse the user’s research request (industry, companies, categories, date range); (2) check memory for previous findings on the same companies; (3) create a structured research plan with targeted search queries per category; (4) search external sources and collect documents; (5) extract structured, source-backed facts with confidence scores; (6) validate evidence quality and filter unsupported claims; (7) check research completeness and, if gaps remain, generate additional queries and search again; (8) compare companies using feature matrices, SWOT analysis, and weighted scorecards; (9) detect historical changes against prior runs and generate alerts; (10) save findings, scores, and alerts to the database; and (11) produce an executive Markdown report with downloadable charts.

### 5. Explain the Feedback Loop

The core feedback loop is automated. After the first search-and-extract pass, a completeness checker evaluates whether each category has sufficient sourced findings for every company. If the “AI capabilities” category has only one credible fact for one of three competitors, the agent marks the category as insufficient, appends targeted follow-up queries (for example, “Company X AI capabilities official documentation”), and returns to the search step. This loop repeats up to three iterations before proceeding to analysis, ensuring the report reflects the best available public evidence rather than premature conclusions.

A second loop operates through memory: each research run is stored, so subsequent analyses compare new findings against prior results to detect product launches, pricing changes, or hiring shifts. Users also refine future runs by adjusting competitors, categories, research period, and report depth in the UI — progressively improving the relevance of each briefing.

---

*Word count (Section B body): ~680 words*
