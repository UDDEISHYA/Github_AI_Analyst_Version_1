# AI Analyst - V1

# AI Analyst — Ask Your Data a Question, Get a Real Answer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytics%20Engine-FFC107?logo=duckdb)
![Claude](https://img.shields.io/badge/Claude-Anthropic-blueviolet?logo=anthropic)
![GPT](https://img.shields.io/badge/GPT--4o-OpenAI-412991?logo=openai)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557c)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Agents](https://img.shields.io/badge/Agent%20Templates-43-informational)

</div>

---

An AI-powered analysis platform that takes natural language questions and returns SQL, charts, and full analytical reports — not chat responses dressed up as insight.

---

## Background

Most AI data tools follow the same pattern: you ask a question, the model writes a query, you get a table. That's a lookup, not analysis.

This project draws a line between the two. Simple questions — "How many users signed up last quarter?" — get answered instantly. But the kind of question that actually matters in a business context — "Why did conversion drop in Q4?" — triggers something fundamentally different: a multi-agent pipeline that frames the problem, generates hypotheses, explores the data, validates findings, and constructs a narrative.

> The goal isn't to chat with your data. It's to analyze it the way a real analyst would — systematically, with evidence, and with a clear story at the end.

Upload any CSV or use the bundled NovaMart e-commerce dataset (13 tables, ~1M rows at full scale). Works with Claude (Anthropic) or GPT-4o (OpenAI).

---

## What Makes This Different

The core differentiator is the **question complexity router**. Every question gets classified into one of five levels, and each level gets a different treatment.

| Level | Type | Example | What Happens |
|-------|------|---------|--------------|
| L1 | Lookup | "How many users signed up in 2024?" | Direct SQL, immediate answer |
| L2 | Comparison | "Revenue by product category" | SQL + auto-generated chart |
| L3 | Analysis | "Why did conversion rates drop in Q4?" | 4-agent pipeline with validation |
| L4 | Investigation | "Root cause of revenue decline — size the opportunity" | 8-agent pipeline with cross-verification |
| L5 | Presentation | "Build a deck on checkout funnel optimization" | 15-agent pipeline producing a full report |

L1 and L2 questions get handled in a single LLM call with tool use. L3 through L5 spin up a full analytical workflow — agents running sequentially, each one building on the last, with real-time progress streaming to the sidebar via SSE.

That distinction matters. A lookup tool that pretends to do analysis is worse than one that knows it can't.

---

## The Interface

The design follows an "Analyst Workspace" pattern — structured content cards, not chat bubbles. No generic AI chrome.

| Welcome Screen | Data Profile | Chat Analysis |
|---|---|---|
| Upload CSV or select demo dataset | Auto-profiled schema with quality grades | Natural language Q&A with SQL + charts |

Charts follow Storytelling with Data principles: highlight bars, action titles, clean design. The goal is output you could put in front of a stakeholder without redesigning it.

---

## Quick Start

### Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.10+ |
| LLM API Key | [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/api-keys) |

### Setup

```bash
# Clone
git clone https://github.com/<your-username>/AI-Analyst.git
cd AI-Analyst

# Environment (one command)
bash scripts/setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Add your API key to `.env`:

```env
# Pick one (or both — Claude takes priority if both are set):
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
```

### Run

```bash
source .venv/bin/activate
uvicorn web.app:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000**.

The repo ships with a pre-built NovaMart DuckDB file. To regenerate or resize:

```bash
python scripts/generate_all.py              # 10% scale (default, fast)
python scripts/generate_all.py --scale 1.0  # Full dataset (~1.4M sessions)
python scripts/generate_all.py --scale 0.01 # Tiny dataset for quick testing
```

---

## How It Works

### Architecture

Three layers, no framework overhead on the frontend.

```
Frontend (vanilla HTML/CSS/JS — zero build step)
    ↕ REST API + SSE
Backend (FastAPI)
    ↕ DuckDB (local) / LLM APIs
Data + AI
```

### The Chat Pipeline

The routing logic is the backbone. When a user types a question:

1. `analysis_service.py` classifies the question into L1–L5 using pattern matching
2. **L1–L2:** The question, schema context, and SQL/chart tools go to the LLM in a single call. Response is immediate.
3. **L3–L5:** `pipeline_orchestrator.py` creates a run, selects agents based on complexity, and executes them sequentially. Each agent is a markdown prompt template from `agents/`, with variables like `{{BUSINESS_CONTEXT}}` and `{{DATA_INVENTORY}}` substituted at runtime. The LLM executes each agent with `execute_sql`, `generate_chart`, and `write_finding` tools. Progress events stream to the frontend via SSE.

### Agent Plans by Complexity

| Level | Plan | Agent Chain |
|-------|------|-------------|
| L3 | Guided Analysis | question-framing → data-explorer → descriptive-analytics → validation |
| L4 | Deep Investigation | + hypothesis, root-cause-investigator, cross-verification, opportunity-sizer |
| L5 | Full Presentation | + story-architect, chart-maker, storytelling, deck-creator, comms-drafter |

There are 43 agent templates total, each encoding a specific analytical role. The pipeline selects and sequences them based on what the question requires.

---

## Using the Platform

**Upload your own data** — click the **+** button in the sidebar or drag-and-drop a CSV. It's auto-ingested into DuckDB, profiled (column types, null rates, unique counts, data quality grading), and immediately queryable.

**Use the demo dataset** — click any NovaMart table in the sidebar. Auto-generated profiles show row counts, column distributions, and data quality grades. Suggested queries are provided as starting points.

**Ask a question** — type in the chat bar. For L3+ questions, the sidebar shows real-time agent progress: Framing → Hypotheses → Exploring → Analyzing → Validating. Each finding appears as a card in the main workspace with inline charts.

---

## NovaMart Demo Dataset

The bundled dataset simulates a mid-size e-commerce company across 13 tables. It's designed for learning — realistic enough to practice on, messy enough to be interesting.

| Table | Description | Rows (10%) |
|-------|-------------|------------|
| `users` | Customer profiles | ~15K |
| `orders` | Purchase transactions | ~47K |
| `products` | Product catalog | ~200 |
| `promotions` | Discount campaigns | ~20 |
| `categories` | Product categories | ~10 |
| `sessions` | Website sessions | ~138K |
| `events` | Granular user events | ~651K |
| `order_items` | Line items per order | ~75K |
| `memberships` | NovaMart Plus subscriptions | ~5.5K |
| `experiments` | A/B test definitions | 2 |
| `experiment_assignments` | User–experiment assignments | ~20K |
| `nps_responses` | Net Promoter Score surveys | ~8K |
| `channels` | Marketing channels | ~8 |

Data covers Jan–Dec 2024 with realistic patterns: power-law user activity distributions, hourly traffic curves, seasonal trends, and intentional data quirks. One worth flagging — `sessions.had_purchase` is unreliable for Nov–Dec 2024. That's by design. Real data has problems, and an analyst who doesn't check for them isn't analyzing.

---

## Project Structure

```
.
├── web/                          # FastAPI web application
│   ├── app.py                    # Entry point — FastAPI app, CORS, static mount
│   ├── config.py                 # Paths, upload limits
│   ├── models/schemas.py         # Pydantic request/response models
│   ├── routers/                  # API endpoints
│   │   ├── datasets.py           #   POST /api/datasets/upload, GET/DELETE datasets
│   │   ├── schema.py             #   GET /api/datasets/{name}/profile
│   │   ├── query.py              #   POST /api/query, POST /api/chat
│   │   ├── charts.py             #   GET /api/charts/{filename}
│   │   └── pipeline.py           #   POST /api/pipeline/start, GET events/status/results
│   ├── services/                 # Business logic
│   │   ├── dataset_service.py    #   CSV ingestion, DuckDB table management
│   │   ├── query_service.py      #   SQL execution (read-only, sanitized)
│   │   ├── profiling_service.py  #   Column-level data profiling
│   │   ├── chart_service.py      #   Chart generation (matplotlib + SWD style)
│   │   ├── llm_service.py        #   LLM chat (Claude or GPT with tool use)
│   │   ├── analysis_service.py   #   Question classification + routing
│   │   ├── agent_executor.py     #   Agent template loading + LLM execution
│   │   └── pipeline_orchestrator.py  # Multi-agent pipeline orchestration
│   └── static/                   # Frontend (vanilla HTML/CSS/JS, zero build step)
│       ├── index.html
│       ├── css/style.css         #   Design system (tokens, layout, components)
│       ├── css/components.css    #   Result cards, schema tables, pipeline stepper
│       └── js/
│           ├── app.js            #   Core: dataset list, routing, chat input
│           ├── chat.js           #   LLM chat + block rendering
│           ├── dashboard.js      #   Profile cards, data tables, card factory
│           ├── pipeline.js       #   SSE connection + pipeline stepper
│           └── upload.js         #   Drag-and-drop CSV upload
│
├── helpers/                      # Python utility modules
│   ├── chart_helpers.py          #   SWD-style chart functions (highlight_bar, etc.)
│   ├── chart_palette.py          #   Theme-aware color palettes
│   ├── data_helpers.py           #   Data source detection and fallback
│   ├── connection_manager.py     #   Multi-warehouse connection management
│   ├── sql_helpers.py            #   SQL sanity checks
│   ├── sql_dialect.py            #   Warehouse-specific SQL adapters
│   ├── experiment_stats/         #   A/B testing, power analysis, causal inference
│   └── ...                       #   (See helpers/INDEX.md for full list)
│
├── agents/                       # Agent prompt templates (markdown)
│   ├── registry.yaml             #   Machine-readable agent index
│   ├── question-framing.md       #   Step 1: Frame the business question
│   ├── hypothesis.md             #   Step 2: Generate testable hypotheses
│   ├── data-explorer.md          #   Step 3: Explore and profile data
│   ├── descriptive-analytics.md  #   Step 4: Run the analysis
│   ├── validation.md             #   Step 5: Validate findings
│   └── ...                       #   (43 agent templates total)
│
├── data/
│   └── practice/
│       └── novamart_practice.duckdb  # Pre-built demo dataset (~38MB)
│
├── scripts/
│   ├── setup.sh                  # Environment setup
│   └── generate_all.py           # Demo data generator
│
├── themes/                       # Marp deck themes (for presentation output)
├── tests/                        # Test suite
├── .env.example                  # Template for API keys (copy to .env)
├── requirements.txt              # Python dependencies
└── pyproject.toml                # Package configuration
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/datasets/upload` | Upload a CSV file |
| `GET` | `/api/datasets` | List all datasets |
| `GET` | `/api/datasets/{name}` | Get dataset info + sample rows |
| `DELETE` | `/api/datasets/{name}` | Delete an uploaded dataset |
| `GET` | `/api/datasets/{name}/profile` | Column-level profiling |
| `GET` | `/api/datasets/{source}/profile-all` | Profile all tables in a source |
| `POST` | `/api/query` | Execute a raw SQL query |
| `POST` | `/api/chat` | Send a natural language question |
| `POST` | `/api/pipeline/start` | Start an L3–L5 analysis pipeline |
| `GET` | `/api/pipeline/{id}/events` | SSE stream of pipeline progress |
| `GET` | `/api/pipeline/{id}/status` | Pipeline status snapshot |
| `GET` | `/api/pipeline/{id}/results` | Pipeline findings + charts |
| `GET` | `/api/charts/{filename}` | Serve a generated chart image |

---

## Security

Worth calling out explicitly — this runs arbitrary LLM-generated SQL against your data, so the guardrails matter.

| Layer | Protection |
|-------|------------|
| SQL filtering | Only `SELECT` and `WITH` (CTE) queries allowed. `DROP`, `ALTER`, `DELETE`, `INSERT`, `CREATE`, `TRUNCATE` are blocked by regex filter. |
| Database access | Query connections opened with `read_only=True` |
| File uploads | Only `.csv` accepted, with size limits enforced |
| Path traversal | Chart filenames validated — no `..` or `/` allowed |
| Credentials | All API keys loaded from `.env` via `python-dotenv` — nothing in code |

---

## Configuration

### LLM Provider

The app auto-detects which LLM to use based on which API key is present in `.env`:

| Key Set | Provider | Model |
|---------|----------|-------|
| `ANTHROPIC_API_KEY` | Anthropic | claude-sonnet-4 |
| `OPENAI_API_KEY` | OpenAI | gpt-4o |
| Both | Anthropic (priority) | claude-sonnet-4 |

### Snowflake (optional)

For connecting to a live Snowflake warehouse instead of local DuckDB, add credentials to `.env`. See `.env.example` for required variables.

---

## Development

### Tests

```bash
source .venv/bin/activate
pytest                              # All tests
pytest tests/test_chart_palette.py  # Single file
pytest -m "not slow"                # Skip slow tests
```

### Linting

```bash
python scripts/lint_chart_colors.py   # Flag color conflicts
python scripts/lint_wcag.py           # WCAG contrast checks
python scripts/check_imports.py       # Verify helper imports
```

---

## Tech Stack

| Package | Role |
|---------|------|
| `fastapi` + `uvicorn` | Web framework + ASGI server |
| `duckdb` | In-process analytical database |
| `pandas` | Data manipulation |
| `matplotlib` + `seaborn` | Chart generation |
| `numpy` + `scipy` | Numerical computation |
| `anthropic` / `openai` | LLM API clients |
| `pyyaml` | Agent registry configuration |
| `python-dotenv` | Environment variable management |
| `python-docx` | Report generation |
| `python-multipart` | File upload handling |

Full list in `requirements.txt`.

---

## Troubleshooting

**"No LLM API key configured"** — Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env` and restart the server.

**"Database not found"** — The demo file belongs at `data/practice/novamart_practice.duckdb`. Regenerate with `python scripts/generate_all.py`.

**Port already in use** — `uvicorn web.app:app --port 8001 --reload`

**Charts not rendering** — Reinstall matplotlib: `pip install matplotlib --force-reinstall`

---

## Why This Project Exists

There's a gap between "AI that can query a database" and "AI that can analyze data." The first one is a text-to-SQL wrapper. The second requires the kind of structured thinking that most single-prompt LLM calls can't sustain — framing the right question, testing hypotheses against evidence, validating conclusions before presenting them.

This project bridges that gap with a multi-agent architecture where each agent handles one step of the analytical process. The result isn't a chatbot that happens to know SQL. It's a system that follows the same workflow a human analyst would — just faster.

The 43 agent templates are the headline. The question complexity router, the real-time pipeline, and the SWD-style output are what make it useful.

---

## License

MIT — see [LICENSE](LICENSE) for details.
