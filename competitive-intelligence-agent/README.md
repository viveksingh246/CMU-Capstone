# Competitive Intelligence Research Agent

An agentic system that autonomously plans and conducts competitor research across multiple dynamic information sources. It extracts source-backed facts, evaluates research completeness, performs follow-up searches, stores historical findings, compares companies across strategic dimensions, and generates executive reports, visual summaries, alerts, and recommendations.

Unlike a single-prompt LLM solution, this system uses an **iterative observe-reason-act workflow** with persistent memory, external tools, and evidence validation.

## Features

- **LangGraph agent workflow** with planning, search, extraction, validation, and completeness loops
- **Source-backed fact extraction** with confidence scoring and credibility ranking
- **SQLite long-term memory** for findings, scores, and alerts
- **Historical change detection** across research runs
- **SWOT analysis**, weighted scorecards, and strategic recommendations
- **Streamlit UI** with charts and downloadable reports
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
├── app.py                          # Streamlit UI
├── config.py                       # Settings and environment
├── requirements.txt
├── agents/
│   ├── planner.py                  # Research planning
│   ├── researcher.py               # Source collection
│   ├── extractor.py                # Fact extraction
│   ├── validator.py                # Evidence validation
│   ├── completeness.py             # Research gap detection
│   ├── analyst.py                  # SWOT, scoring, recommendations
│   ├── reporter.py                 # Executive report generation
│   └── memory_agent.py             # SQLite persistence
├── tools/
│   ├── web_search.py               # Tavily + fallback search
│   ├── mcp_tools.py                # MCP client facade for agents
│   ├── news_search.py
│   ├── github_search.py
│   ├── job_search.py
│   └── document_reader.py
├── agent_mcp/
│   ├── server.py                   # MCP server implementation
│   ├── client.py                   # MCP client (inprocess / stdio)
│   └── protocol.py                 # JSON-RPC helpers
├── mcp_servers/
│   ├── search_server.py            # MCP search tools
│   └── memory_server.py            # MCP memory tools
├── .cursor/
│   └── mcp.json                    # Cursor MCP configuration
├── workflows/
│   ├── state.py                    # LangGraph state definition
│   └── competitive_intelligence_graph.py
├── memory/
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
Parse User Request
  │
  ▼
Check Memory ─────────────────────────────┐
  │                                        │ Previous findings
  ▼                                        │ reused for comparison
Create Research Plan                       │
  │                                        │
  ▼                                        │
Search Sources ◄──────────────────┐      │
  │                               │      │
  ▼                               │      │
Extract Facts                     │      │
  │                               │      │
  ▼                               │      │
Validate Evidence                 │      │
  │                               │      │
  ▼                               │      │
Check Completeness ── Missing? ──►┘      │
  │                                        │
  ▼ (Complete)                             │
Compare Companies ◄────────────────────────┘
  │
  ▼
Detect Historical Changes
  │
  ▼
Save to Memory
  │
  ▼
Generate Report & Charts
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

| Metric | Target |
|--------|--------|
| Research coverage | ≥ 90% |
| Citation coverage | ≥ 90% |
| Source quality (official/reputable) | ≥ 70% |
| Extraction accuracy (manual review) | ≥ 85% |

## Guardrails

- Every important claim must include a source
- Unknown information marked as "not publicly available"
- Marketing statements labeled as company claims
- No invented pricing or private-company revenue
- Facts distinguished from analysis
- Conflicting sources shown, not hidden

## Future Enhancements

- Automated daily monitoring with email/Slack alerts
- Financial statement analysis
- Patent and social sentiment analysis
- Multi-language research
- Knowledge graph visualization
- Cloud deployment with role-based access

## License

Educational capstone project.
