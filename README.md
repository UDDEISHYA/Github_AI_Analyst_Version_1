# AI Analyst

# AI Analyst — Ask Your Data a Question, Get a Real Answer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytics%20Engine-FFC107?logo=duckdb)
![Claude](https://img.shields.io/badge/Claude-Anthropic-blueviolet?logo=anthropic)
![GPT](https://img.shields.io/badge/GPT--4o-OpenAI-412991?logo=openai)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557c)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

---

An AI-powered analysis platform that takes natural language questions and returns SQL, charts, and full analytical reports — not chat responses dressed up as insight.

> Note: This is Version 1.  
> Check the latest version here: [Siftory](https://github.com/UDDEISHYA/Siftory)



https://github.com/user-attachments/assets/0270eaeb-e66b-42ee-a44d-09b2e55d181a



---

## Background

Most AI data tools follow the same pattern: you ask a question, the model writes a query, you get a table. That's a lookup, not analysis.

This project draws a line between the two. Simple questions — "How many users signed up last quarter?" — get answered instantly. But the kind of question that actually matters in a business context — "Why did conversion drop in Q4?" — triggers something fundamentally different: a multi-agent pipeline that frames the problem, generates hypotheses, explores the data, validates findings, and constructs a narrative.

> The goal isn't to chat with your data. It's to analyze it the way a real analyst would — systematically, with evidence, and with a clear story at the end.

Upload any CSV or use the bundled NovaMart e-commerce dataset (13 tables, ~1M rows at full scale). Works with Claude (Anthropic) or GPT-4o (OpenAI).

---

## What Makes This Different

The core differentiator is the **question complexity router**. Every question gets classified by complexity, and each level gets a fundamentally different treatment.

| Level | Type | Example | What Happens |
|-------|------|---------|--------------|
| L1 | Lookup | "How many users signed up in 2024?" | Direct SQL, immediate answer |
| L2 | Comparison | "Revenue by product category" | SQL + auto-generated chart |
| L3 | Analysis | "Why did conversion rates drop in Q4?" | Multi-agent pipeline with validation |
| L4 | Investigation | "Root cause of revenue decline — size the opportunity" | Deep pipeline with cross-verification |
| L5 | Presentation | "Build a deck on checkout funnel optimization" | Full pipeline producing a presentation-ready report |

Simple lookups and comparisons resolve immediately. Analytical and investigative questions spin up a coordinated pipeline of specialized AI agents — each one building on the last, with real-time progress streaming to the interface.

That distinction matters. A lookup tool that pretends to do analysis is worse than one that knows it can't.

---

## Multi-Agent Analysis

For complex questions, analysis isn't a single LLM call — it's a structured workflow. The pipeline orchestrates multiple specialized agents, each handling one stage of the analytical process:

**Question Framing** — structures the business question before any data is touched, identifying what "answering" actually means in context.

**Hypothesis Generation** — proposes testable explanations rather than jumping to the first pattern in the data.

**Data Exploration** — profiles the relevant tables, identifies data quality issues, and maps what's available to what's needed.

**Analysis and Root Cause Investigation** — runs segmentation, funnels, trend analysis, and iterative drill-downs to isolate actionable causes.

**Cross-Verification and Validation** — re-derives key findings through independent calculations and runs a multi-layer validation check covering structural integrity, logical consistency, business rules, and Simpson's paradox.

**Opportunity Sizing** — quantifies the business impact of findings with sensitivity analysis.

**Storytelling and Presentation** — builds a narrative arc from validated findings, generates charts following Storytelling with Data principles, and assembles stakeholder-ready output.

The pipeline selects and sequences agents based on what the question requires. An L3 question gets a focused subset. An L5 gets the full chain. Each agent's output feeds into the next, and progress streams to the interface in real time.

---

## The Interface

The design follows an "Analyst Workspace" pattern — structured content cards, not chat bubbles. No generic AI chrome.

| Welcome Screen | Data Profile | Chat Analysis |
|---|---|---|
| Upload CSV or select demo dataset | Auto-profiled schema with quality grades | Natural language Q&A with SQL + charts |

Charts follow Storytelling with Data principles: highlight bars, action titles that state the finding, clean design. The goal is output you could put in front of a stakeholder without redesigning it.

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

## Using the Platform

**Upload your own data** — click the **+** button in the sidebar or drag-and-drop a CSV. It's auto-ingested, profiled (column types, null rates, unique counts, data quality grading), and immediately queryable.

**Use the demo dataset** — click any NovaMart table in the sidebar. Auto-generated profiles show row counts, column distributions, and data quality grades. Suggested queries are provided as starting points.

**Ask a question** — type in the chat bar. For L3+ questions, the sidebar shows real-time agent progress as each stage executes. Each finding appears as a card in the main workspace with inline charts.

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

## Architecture Overview

The system is built on three layers:

**Frontend** — a lightweight interface with zero build step, designed around the analyst workspace pattern. Content cards, schema views, and a pipeline progress tracker.

**Backend** — a FastAPI application handling question classification, LLM orchestration, SQL execution, chart generation, and real-time event streaming.

**Data + AI** — DuckDB for local analytical queries, with dual LLM provider support (Claude and GPT-4o) for both direct chat and multi-agent pipeline execution.

All SQL execution is read-only and sanitized. Only `SELECT` queries are permitted. File uploads are validated and size-limited. API keys are loaded from environment variables — nothing hardcoded.

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

## Tech Stack

| Package | Role |
|---------|------|
| `fastapi` + `uvicorn` | Web framework + ASGI server |
| `duckdb` | In-process analytical database |
| `pandas` | Data manipulation |
| `matplotlib` + `seaborn` | Chart generation |
| `numpy` + `scipy` | Numerical computation |
| `anthropic` / `openai` | LLM API clients |
| `python-dotenv` | Environment variable management |
| `python-multipart` | File upload handling |

Full list in `requirements.txt`.

---

## Development

### Tests

```bash
source .venv/bin/activate
pytest                              # All tests
pytest tests/test_chart_palette.py  # Single file
pytest -m "not slow"                # Skip slow tests
```

---

## Troubleshooting

**"No LLM API key configured"** — Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to `.env` and restart the server.

**"Database not found"** — The demo DuckDB file may need to be regenerated. Run `python scripts/generate_all.py`.

**Port already in use** — `uvicorn web.app:app --port 8001 --reload`

**Charts not rendering** — Reinstall matplotlib: `pip install matplotlib --force-reinstall`

---

## Why This Project Exists

There's a gap between "AI that can query a database" and "AI that can analyze data." The first one is a text-to-SQL wrapper. The second requires the kind of structured thinking that most single-prompt LLM calls can't sustain — framing the right question, testing hypotheses against evidence, validating conclusions before presenting them.

This project bridges that gap with a multi-agent architecture where each agent handles one step of the analytical process. The result isn't a chatbot that happens to know SQL. It's a system that follows the same workflow a human analyst would — just faster.

---

## License

MIT — see [LICENSE](LICENSE) for details.
