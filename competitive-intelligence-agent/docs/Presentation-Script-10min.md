# 10-Minute Capstone Presentation Script

**Project:** Competitive Intelligence Research Agent  
**Presenter:** Vivek Singh  
**Target length:** ~10 minutes (18 slides)  
**GitHub:** https://github.com/viveksingh246/CMU-Capstone  
**Path:** `competitive-intelligence-agent/`

---

## Delivery tips

- Speak at a natural pace — about 130–150 words per minute.
- Use **Presenter View** in PowerPoint to see speaker notes and timing.
- On **Slide 1** and **Slide 16**, briefly mention the GitHub repo (or click the blue button in slideshow mode).
- Point at screenshots when you reference the UI — they are live captures from the system.
- Section divider slides (4, 9, 11) are short transitions — 5–10 seconds each.

---

## Slide 1 — Title *(~30 seconds)*

> Hi, I'm Vivek Singh, and today I'm presenting my CMU Agentic AI capstone project: the **Competitive Intelligence Research Agent**.
>
> This is an autonomous multi-agent system that plans, conducts, validates, and reports on competitor research — with source citations, not just LLM summaries.
>
> On the right you can see the Streamlit workspace. The full project is public on GitHub at **github.com/viveksingh246/CMU-Capstone**, in the `competitive-intelligence-agent` folder. I'll come back to the repo at the end.

---

## Slide 2 — The Problem & Intended Users *(~45 seconds)*

> Let me start with the problem.
>
> Organizations in fast-moving markets — like cloud data and AI platforms — need to know what competitors ship, how they price, where they hire, and what AI capabilities they're emphasizing. Today, that work is **manual**: scattered across browser tabs, spreadsheets, and slide decks that go stale within weeks.
>
> A single ChatGPT prompt doesn't solve this. You need live data, memory across runs, evidence validation, and follow-up research when coverage is incomplete.
>
> My system's goal is to autonomously plan, research, validate, compare, and report — with citations.
>
> **Primary users** are product managers and strategy analysts. **Secondary users** are sales enablement teams and executives who consume the briefings.
>
> For the capstone demo, I compare **Snowflake, Databricks, and Google BigQuery** across six categories: products, features, pricing, AI, partnerships, and hiring.

---

## Slide 3 — Why an Agent-Based Approach *(~45 seconds)*

> So why build an agent instead of a better prompt?
>
> Competitive intelligence requires six capabilities a standalone LLM doesn't have:
>
> First, **tool calling** — querying web search, news, GitHub, and job boards.
>
> Second, **planning** — breaking a broad comparison into category-specific tasks with completion criteria.
>
> Third, **memory** — storing findings in SQLite and detecting what changed since the last run.
>
> Fourth, a **feedback loop** — when evidence is thin in a category, the agent generates follow-up queries and searches again.
>
> Fifth, **validation** — ranking source credibility and labeling claims as verified facts versus company marketing.
>
> And sixth, **guardrails** — escalating to human review when confidence drops below seventy percent.
>
> That's the difference between a chat response and an autonomous research system.

---

## Slide 4 — Section: System Design *(~10 seconds)*

> Now let me walk you through the system design — the architecture, agents, and workflow.

---

## Slide 5 — Live System: Research Workspace *(~45 seconds)*

> Here's the live Streamlit interface.
>
> On the left sidebar, the user configures the industry preset, competitor list, analysis categories, and research period.
>
> In the main workspace, they set report depth and launch analysis with one click. The system supports both **live search** via the Tavily API and a **demo data mode** for offline presentations.
>
> This UI isn't just a wrapper — it's where human oversight happens. When the system escalates a low-confidence run, the user reviews findings here and clicks **Approve and Generate Report** before anything is finalized.

---

## Slide 6 — System Architecture *(~70 seconds)*

> The architecture is orchestrated by **LangGraph** as a state machine with conditional routing.
>
> The flow starts at the Streamlit UI. The request is **parsed and validated** — invalid or confidential requests halt immediately.
>
> Then the system **checks memory** in SQLite for prior findings on the same companies. The **Coordinator agent** sets the workflow phase.
>
> The **Planner** creates a structured research plan using a **ReAct** reasoning loop — reason, plan, act, observe, reflect, decide.
>
> The **Research agent** searches external sources. Documents are indexed into **ChromaDB** for RAG retrieval. The **Extractor** pulls structured facts with citations. The **Validator** scores evidence quality.
>
> A **completeness check** loops back to search up to three times if coverage is insufficient.
>
> Then **Tree-of-Thought analysis** with a **Critic agent** explores multiple strategic interpretations before producing SWOT and scorecard outputs.
>
> A **safety check** runs before reporting. If confidence is below seventy percent, the workflow **pauses for human review**.
>
> Finally, findings are saved to memory and an executive report is generated.
>
> Tools are exposed via **MCP servers** for search and memory, backed by SQLite and ChromaDB.

---

## Slide 7 — Agent Workflow in Action *(~50 seconds)*

> This screenshot shows the pipeline during an active research run.
>
> The horizontal progress bar tracks each stage — parse, plan, search, RAG indexing, extraction, validation, analysis, and reporting.
>
> Three design patterns are working together here:
>
> The **ReAct loop** tracks reasoning steps visible in the UI for auditability.
>
> The **completeness loop** triggers follow-up searches — for example, if only one sourced fact exists for a competitor's AI capabilities, the agent doesn't proceed to analysis prematurely.
>
> And **Tree-of-Thought** explores four strategic branches with beam search, pruned by a Critic agent scoring below sixty-five out of one hundred.

---

## Slide 8 — Six-Agent Architecture *(~40 seconds)*

> I formalized six specialized agents, each with a clear responsibility:
>
> The **Planner** generates the research plan and search queries.
>
> The **Research agent** collects documents and indexes them for RAG.
>
> The **Validation agent** filters evidence and enforces multi-source verification.
>
> The **Analysis agent** runs Tree-of-Thought, SWOT, and competitive scorecards, with a **Critic** evaluating branches.
>
> The **Report agent** produces executive Markdown, PDF, and JSON output.
>
> And the **Memory and Coordination agent** manages SQLite persistence and workflow phase tracking.
>
> This separation makes each stage independently testable — I have over 130 automated tests covering the workflow.

---

## Slide 9 — Section: Design Evolution *(~10 seconds)*

> The system didn't start here. It evolved incrementally across Modules one through six. Let me show that progression.

---

## Slide 10 — Design Evolution Across the Program *(~60 seconds)*

> In **Module 1**, Checkpoint 1.1, I scoped the problem and designed the LangGraph workflow with SQLite memory, a completeness loop, MCP tools, and the Streamlit UI.
>
> **Module 2** added the **ReAct reasoning loop** with short-term memory and a visible trace in the UI.
>
> **Module 3** integrated **ChromaDB RAG** — six-hundred-fifty-token chunks with fifteen percent overlap and top-six semantic retrieval to augment fact extraction.
>
> **Module 4** added **Tree-of-Thought beam search** with a Critic agent that prunes weak strategic branches.
>
> **Module 5** formalized the **six-agent architecture** with hybrid coordination — sequential pipeline flow plus conditional feedback edges.
>
> **Module 6** added **safety guardrails**: input validation, multi-source verification, escalation below seventy percent confidence, and a human approval gate in the UI.
>
> Post-audit, I also fixed critical gaps — invalid input now halts the workflow, and human approval state is preserved across re-entry.

---

## Slide 11 — Section: Evaluation & Results *(~10 seconds)*

> Now let me show how I evaluated the system — the metrics, results, strengths, and limitations.

---

## Slide 12 — Results Dashboard *(~50 seconds)*

> This is the results view after a completed analysis.
>
> At the top, a **KPI strip** shows evaluation metrics — correctness, groundedness, source credibility, research coverage, and safety compliance.
>
> Below that, a **phase rail** shows which pipeline stages completed, followed by **top strategic recommendations** with evidence.
>
> The tabbed interface gives the user an **Overview**, **Executive Brief**, **Competitive Matrix**, **Analytics** charts, and a **Trace and Sources** panel for full auditability.
>
> My targets are: ninety percent research coverage, ninety percent groundedness with source URLs, seventy percent source credibility from trusted sources, and ninety-five percent correctness on verified findings.

---

## Slide 13 — Analytics Visualizations *(~40 seconds)*

> The analytics tab renders Plotly visualizations from the competitive scorecard.
>
> On the left, a **bar chart** compares overall scores across Snowflake, Databricks, and Google BigQuery.
>
> On the right, a **radar chart** breaks down seven dimensions — product breadth, feature differentiation, pricing, AI maturity, partnerships, innovation momentum, and hiring momentum.
>
> These are analytical assessments grounded in validated findings — the system always distinguishes facts from analysis in the report.

---

## Slide 14 — Evaluation Metrics & ReAct Trace *(~55 seconds)*

> Evaluation happens three ways.
>
> First, **automated per-run metrics** computed in `safety/metrics.py` and displayed in the UI — you can see them in this screenshot.
>
> Second, **131 pytest tests** covering workflow routing, RAG chunking, Tree-of-Thought beam search, Critic pruning, guardrails, escalation, and MCP tool servers.
>
> Third, **manual review** of demo runs archived in the `reports/` directory.
>
> **Strengths:** the workflow routes correctly through all stages, guardrails reject bad input before any search occurs, and when public data is insufficient, the system reports "insufficient evidence" instead of inventing conclusions.
>
> **Limitations:** RAG currently uses local hash embeddings in test mode rather than production OpenAI embeddings, and report quality depends on public data availability for the chosen competitors.

---

## Slide 15 — Safety & Human-in-the-Loop *(~45 seconds)*

> Safety was a core requirement from Checkpoint 6.1.
>
> This screenshot shows the **human review pause**. When overall confidence falls below seventy percent, the workflow stops and the user sees an escalation summary with reasons.
>
> They must click **Approve and Generate Report** before the final output is produced.
>
> Other guardrails include: rejecting confidential or proprietary requests, requiring two or more independent sources for major claims, labeling marketing statements separately from verified facts, and marking unknown information as "not publicly available" — never inventing pricing or private revenue.
>
> Fallback logic handles Tavily API outages with sample data, LLM failures with ToT-grounded analysis, and RAG retrieval failures with re-search loops.

---

## Slide 16 — Implementation Stack & GitHub *(~50 seconds)*

> On the implementation side, the stack is **Python** with **LangGraph** for orchestration, **OpenAI GPT-4o-mini** for planning and analysis, **Tavily** for live search, **ChromaDB** for RAG, **SQLite** for long-term memory, **Streamlit** and **Plotly** for the UI, and custom **MCP servers** exposing search and memory tools.
>
> The public repository is at **github.com/viveksingh246/CMU-Capstone** — you can scan the QR code on this slide.
>
> Inside `competitive-intelligence-agent`, you'll find a README with setup instructions, the full agent codebase, 131 tests, sample inputs and outputs, and checkpoint documentation.
>
> To run it locally: `make setup`, add your OpenAI API key, then `make run` — Streamlit starts at localhost eight-five-zero-one. Run `make test` for the full test suite.

---

## Slide 17 — Closing Reflection *(~35 seconds)*

> My main takeaway from this capstone: **autonomous competitive intelligence requires more than a better prompt**. It needs tools, persistent memory, feedback loops, and safety guardrails working together as one integrated system.
>
> What worked best was LangGraph orchestration with the completeness loop and the human-in-the-loop safety gate.
>
> What I learned is that agent design is really about **reliable workflows and evidence quality** — not just generating fluent text.
>
> Next steps I'd pursue: OpenAI embeddings for production RAG quality, scheduled monitoring with alerts, and cloud deployment with role-based access.

---

## Slide 18 — Thank You *(~20 seconds)*

> Thank you for watching. I'm happy to take questions.
>
> Again, the full project is at **github.com/viveksingh246/CMU-Capstone** — feel free to clone it, run the tests, and explore the agent workflow yourself.

---

## Timing summary

| Slide | Topic | Target |
|-------|-------|--------|
| 1 | Title | 0:30 |
| 2 | Problem & users | 0:45 |
| 3 | Why agent | 0:45 |
| 4 | Section divider | 0:10 |
| 5 | Workspace screenshot | 0:45 |
| 6 | Architecture | 1:10 |
| 7 | Pipeline screenshot | 0:50 |
| 8 | Six agents | 0:40 |
| 9 | Section divider | 0:10 |
| 10 | Design evolution | 1:00 |
| 11 | Section divider | 0:10 |
| 12 | Results dashboard | 0:50 |
| 13 | Analytics charts | 0:40 |
| 14 | Metrics & evaluation | 0:55 |
| 15 | Safety & human review | 0:45 |
| 16 | Implementation & GitHub | 0:50 |
| 17 | Closing reflection | 0:35 |
| 18 | Thank you | 0:20 |
| **Total** | | **~10:05** |

---

## Rubric checklist (for self-review before recording)

- [ ] Clear explanation of real-world problem and intended user (Slides 2–3)
- [ ] Coherent final architecture — components working together (Slides 6–8)
- [ ] System goal, scope, and constraints (Slides 2, 5, 12)
- [ ] Evaluation criteria and results (Slides 12–14)
- [ ] Design evolution across program (Slide 10)
- [ ] Implementation approach — tools, frameworks, APIs (Slide 16)
- [ ] Strengths and limitations (Slide 14)
- [ ] Safety, reliability, human oversight (Slide 15)
- [ ] Public GitHub repository referenced clearly (Slides 1, 16, 18)
- [ ] Appropriate for technical audience (~10 minutes)

---

*End of script*
