# Competitive Intelligence Research Agent

An agentic system that autonomously plans and conducts competitor research across multiple dynamic information sources. It extracts source-backed facts, evaluates research completeness, performs follow-up searches, stores historical findings, compares companies across strategic dimensions, and generates executive reports, visual summaries, alerts, and recommendations.

Unlike a single-prompt LLM solution, this system uses an **iterative observe-reason-act workflow** with persistent memory, external tools, and evidence validation.

## Features

- **LangGraph agent workflow** with planning, search, extraction, validation, and completeness loops
- **ReAct reasoning loop** with short-term memory tracking (Checkpoint 2.1)
- **ChromaDB RAG** with semantic document retrieval (Checkpoint 3.1)
- **Tree-of-Thought beam search** with Critic agent evaluation (Checkpoint 4.1)
- **Six-agent multi-agent architecture** with Memory & Coordination agent (Checkpoint 5.1)
- **Safety guardrails** with human escalation and evaluation metrics (Checkpoint 6.1)
- **Source-backed fact extraction** with confidence scoring and credibility ranking
- **SQLite long-term memory** for findings, scores, and alerts
- **Historical change detection** across research runs
- **SWOT analysis**, weighted scorecards, and strategic recommendations
- **Streamlit UI** with charts, human review, and downloadable reports
- **Tavily search integration** with sample-data fallback for demos
- **MCP tool servers** for search and memory (Cursor-compatible)

## Quick Start

### Prerequisites

- Python 3.9+ (3.10+ recommended)
- OpenAI API key (required for research)
- Tavily API key (optional, for live web search)

### Option A: One-command run

```bash
cd competitive-intelligence-agent
./scripts/run.sh
```

This creates the venv, installs dependencies, initializes the database, and starts Streamlit at http://localhost:8501.

### Option B: Manual setup

```bash
cd competitive-intelligence-agent
make setup          # venv + deps + .env + database
```

Edit `.env` and add your API keys:

- `OPENAI_API_KEY` — **required** for LLM-powered analysis
- `TAVILY_API_KEY` — optional; enables live web search (falls back to sample data without it)

Placeholder values in `.env` are ignored automatically.

```bash
make run            # start Streamlit at http://localhost:8501
```

### Run tests

```bash
make test
```

### Option C: Step by step

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
make db-init
streamlit run app.py
```

## MCP (Model Context Protocol)

This project includes two MCP servers that expose agent tools to external clients (including Cursor):

| Server | Script | Tools |
|--------|--------|-------|
| `ci-search` | `mcp_servers/search_server.py` | web, news, GitHub, job search |
| `ci-memory` | `mcp_servers/memory_server.py` | findings, scores, alerts, research runs |

### Cursor integration

MCP config is at `.cursor/mcp.json`. After opening this project in Cursor:

1. Go to **Cursor Settings → MCP**
2. Confirm `ci-search` and `ci-memory` appear
3. Use the tools from Cursor chat or let the agent call them

### Agent integration

The LangGraph workflow calls MCP tools via `tools/mcp_tools.py`:

```
Agent → MCP Client → Search/Memory MCP Server → Python tools / SQLite
```

Configure in `.env`:

```bash
USE_MCP=true              # set false to call Python tools directly
MCP_TRANSPORT=inprocess   # inprocess (default) or stdio
```

- **`inprocess`** — fast, no subprocess (good for local dev)
- **`stdio`** — true MCP subprocess transport (good for demos)

### Run MCP servers manually (stdio)

```bash
python mcp_servers/search_server.py
python mcp_servers/memory_server.py
```

## Project Structure

```
competitive-intelligence-agent/
├── app.py                          # Streamlit UI (human review, metrics)
├── config.py                       # Settings and environment
├── requirements.txt
├── agents/
│   ├── planner.py                  # Planner Agent — research planning
│   ├── researcher.py               # Research Agent — collection + RAG indexing
│   ├── extractor.py                # Fact extraction with RAG context
│   ├── validator.py                # Validation Agent — evidence + safety
│   ├── completeness.py             # Research gap detection
│   ├── analyst.py                  # Analysis Agent — ToT + SWOT + scoring
│   ├── critic.py                   # Critic Agent — ToT branch evaluation
│   ├── coordinator.py              # Memory & Coordination Agent
│   ├── reporter.py                 # Report Generation Agent
│   └── memory_agent.py             # SQLite persistence
├── rag/
│   ├── chunking.py                 # Document chunking (500-800 tokens)
│   └── vector_store.py             # ChromaDB semantic retrieval
├── reasoning/
│   └── tot_engine.py               # Tree-of-Thought beam search
├── safety/
│   ├── guardrails.py               # Input validation, output constraints
│   ├── escalation.py               # Human intervention triggers
│   └── metrics.py                  # Evaluation metrics
├── memory/
│   ├── short_term.py               # ReAct short-term memory
│   ├── database.py                 # SQLite operations
│   └── schemas.py                  # Pydantic models
├── prompts/                        # LLM prompt templates
├── visualizations/
│   └── charts.py                   # Plotly charts
├── reports/                        # Generated reports (gitignored)
└── tests/
```

## Agent Workflow

```
START
  │
  ▼
Parse & Validate Request (Checkpoint 6.1)
  │
  ▼
Check Memory (SQLite) ──────────────────────┐
  │                                          │
  ▼                                          │
Coordinate (Memory & Coordination Agent)     │
  │                                          │
  ▼                                          │
Create Research Plan (ReAct: plan)           │
  │                                          │
  ▼                                          │
Search Sources ◄──────────────────┐         │
  │                               │         │
  ▼                               │         │
RAG Index (ChromaDB)              │         │
  │                               │         │
  ▼                               │         │
Extract Facts (RAG context)       │         │
  │                               │         │
  ▼                               │         │
Validate Evidence (multi-source)  │         │
  │                               │         │
  ▼                               │         │
Check Completeness ── Missing? ──►┘         │
  │                                          │
  ▼ (Complete)                               │
ToT Analysis (beam search + Critic)          │
  │                                          │
  ▼                                          │
Detect Historical Changes ◄──────────────────┘
  │
  ▼
Safety Check (escalation if confidence < 70%)
  │
  ├── Low confidence ──► Human Review Pause
  │
  ▼ (Approved)
Save to Memory → Generate Report
  │
  ▼
END
```

## Default Capstone Scope

| Setting | Value |
|---------|-------|
| Industry | Cloud Data & AI Platforms |
| Competitors | Snowflake, Databricks, Google BigQuery |
| Categories | Products, Features, Pricing, AI, Partnerships, Hiring |
| Sources | Official sites, docs, blogs, news, GitHub, jobs |
| Outputs | Executive summary, comparison matrix, SWOT, scorecard, charts |

## Seven-Week Implementation Plan

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Problem definition & design | Architecture, schema, sample output |
| 2 | Search & data collection | Search API, page extraction, filtering |
| 3 | Fact extraction & validation | Structured JSON facts with citations |
| 4 | Memory & workflow | SQLite, completeness loop, search-again |
| 5 | Competitive analysis | SWOT, scorecard, recommendations |
| 6 | UI & reporting | Streamlit app, charts, report download |
| 7 | Testing & presentation | Evaluation metrics, demo, documentation |

## Evaluation Metrics

| Metric | Target | Checkpoint |
|--------|--------|------------|
| Correctness (verified findings) | ≥ 95% | 6.1 |
| Groundedness (cited claims) | ≥ 90% | 6.1 |
| Source credibility (official/trusted) | ≥ 70% | 6.1 |
| Research coverage | ≥ 90% | 1.1 |
| Safety compliance | ≥ 95% | 6.1 |
| Human escalation rate | Low-confidence only | 6.1 |

## Guardrails

- Input validation rejects confidential/proprietary requests (Checkpoint 6.1)
- Every important claim must include a source
- Multi-source verification for critical findings (2+ independent sources)
- Unknown information marked as "not publicly available"
- Marketing statements labeled as company claims
- No invented pricing or private-company revenue
- Facts distinguished from analysis
- Conflicting sources shown, not hidden
- Human review required when confidence falls below 70%

## Future Enhancements

- Automated daily monitoring with email/Slack alerts
- Financial statement analysis
- Patent and social sentiment analysis
- Multi-language research
- Knowledge graph visualization
- Cloud deployment with role-based access

## License

Educational capstone project.
