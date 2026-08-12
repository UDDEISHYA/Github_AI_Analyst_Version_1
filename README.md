# AI Analyst

An AI-powered data analysis platform that turns natural language questions into SQL queries, charts, and full analytical reports. Upload a CSV or use the bundled NovaMart e-commerce demo dataset, then ask questions in plain English.

---

## What It Does

**Simple questions** ("How many users do we have?", "Revenue by category") get answered instantly — the LLM writes SQL, executes it against your data, and returns results with optional charts.

**Complex questions** ("Why did conversion drop in Q3?", "Investigate root cause of revenue decline") trigger a multi-agent pipeline that runs through question framing, hypothesis generation, data exploration, analysis, validation, and storytelling — streaming real-time progress in the sidebar.

### Key Features

- **Upload any CSV** — drag-and-drop into the sidebar, auto-ingested into DuckDB
- **Bundled demo dataset** — 13-table NovaMart e-commerce dataset (users, orders, products, sessions, events, experiments, NPS, etc.) ready to explore
- **Natural language chat** — ask questions, get SQL + results + charts
- **Multi-agent pipeline** — L3-L5 questions trigger a full analytical workflow with multiple AI agents
- **Real-time pipeline progress** — SSE-powered sidebar shows each agent's status as it runs
- **Auto data profiling** — column types, null rates, unique counts, min/max ranges, data quality grading
- **SWD-style charts** — Storytelling with Data visualization style (highlight bars, action titles, clean design)
- **Dual LLM support** — works with either Claude (Anthropic) or GPT (OpenAI)

---

## Screenshots

The app uses an "Analyst Workspace" design — content cards, not chat bubbles. Clean, professional, no generic AI chrome.

| Welcome Screen | Data Profile | Chat Analysis |
|---|---|---|
| Upload CSV or select demo dataset | Auto-profiled schema with quality grades | Natural language Q&A with SQL + charts |

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **An LLM API key** — either [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/api-keys)

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/AI-Analyst.git
cd AI-Analyst
```

### 2. Set up the environment

```bash
# Create virtual environment and install dependencies
bash scripts/setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and add your API key:

```env
# Pick one (or both — Claude takes priority if both are set):
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
```

### 4. Generate demo data (optional)

The repo includes a pre-built NovaMart DuckDB file. If you want to regenerate it:

```bash
source .venv/bin/activate
python scripts/generate_all.py              # 10% scale (default, fast)
python scripts/generate_all.py --scale 1.0  # Full dataset (~1.4M sessions)
python scripts/generate_all.py --scale 0.01 # Tiny dataset for quick testing
```

### 5. Start the server

```bash
source .venv/bin/activate
uvicorn web.app:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** in your browser.

---

## How to Use

### Upload your own data
1. Click the **+** button in the sidebar (or drag-and-drop a CSV)
2. The file is auto-ingested into DuckDB, profiled, and ready to query

### Use the demo dataset
1. Click any **NovaMart** table in the sidebar
2. See auto-generated profile (row counts, column types, null rates, data quality)
3. Try suggested queries or type your own

### Ask a question
Type in the chat bar at the bottom. Examples:

| Question | Complexity | What Happens |
|---|---|---|
| "How many users signed up in 2024?" | L1 (lookup) | Direct SQL → answer |
| "Compare revenue by product category" | L2 (comparison) | SQL + chart |
| "Why did conversion rates drop in Q4?" | L3 (analysis) | Multi-agent pipeline |
| "Investigate root cause of the revenue decline and size the opportunity" | L4 (investigation) | Deep pipeline with 8 agents |
| "Full pipeline: build a presentation on checkout funnel optimization" | L5 (presentation) | 15-agent pipeline → deck |

### Pipeline progress
For L3+ questions, the sidebar shows real-time agent progress:
- **Framing Question** → **Generating Hypotheses** → **Exploring Data** → **Analyzing** → **Validating** → ...
- Each finding appears as a card in the main workspace
- Charts are generated and displayed inline

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

## Architecture

### Three-layer system

```
Frontend (vanilla HTML/CSS/JS)
    ↕ REST API + SSE
Backend (FastAPI)
    ↕ DuckDB (local) / LLM APIs
Data + AI
```

### How the chat works

1. User types a question
2. `analysis_service.py` classifies it (L1-L5) using regex patterns
3. **L1-L2**: `llm_service.py` sends the question + schema context to the LLM with SQL/chart tools → immediate response
4. **L3-L5**: `pipeline_orchestrator.py` creates a run, selects agents based on level, and executes them sequentially:
   - Each agent is a markdown template loaded from `agents/`
   - Variables (`{{BUSINESS_CONTEXT}}`, `{{DATA_INVENTORY}}`, etc.) are substituted
   - The LLM executes the agent with `execute_sql`, `generate_chart`, and `write_finding` tools
   - Progress events stream to the frontend via SSE

### Pipeline plans by complexity

| Level | Plan | Agents |
|---|---|---|
| L3 | Guided Analysis | question-framing → data-explorer → descriptive-analytics → validation |
| L4 | Deep Investigation | + hypothesis, root-cause-investigator, cross-verification, opportunity-sizer |
| L5 | Full Presentation | + story-architect, chart-maker, storytelling, deck-creator, comms-drafter |

### Security

- **SQL injection protection**: Only `SELECT` and `WITH` (CTE) queries are allowed. `DROP`, `ALTER`, `DELETE`, `INSERT`, `CREATE`, `TRUNCATE`, etc. are blocked by regex filter.
- **DuckDB read-only mode**: Query connections are opened with `read_only=True`
- **File upload validation**: Only `.csv` files accepted, with size limits
- **Path traversal protection**: Chart filenames are validated (no `..` or `/`)
- **No credentials in code**: All API keys loaded from `.env` via `python-dotenv`

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/datasets/upload` | Upload a CSV file |
| `GET` | `/api/datasets` | List all datasets |
| `GET` | `/api/datasets/{name}` | Get dataset info + sample rows |
| `DELETE` | `/api/datasets/{name}` | Delete an uploaded dataset |
| `GET` | `/api/datasets/{name}/profile` | Column-level profiling |
| `GET` | `/api/datasets/{source}/profile-all` | Profile all tables in a source |
| `POST` | `/api/query` | Execute a raw SQL query |
| `POST` | `/api/chat` | Send a natural language question |
| `POST` | `/api/pipeline/start` | Start an L3-L5 analysis pipeline |
| `GET` | `/api/pipeline/{id}/events` | SSE stream of pipeline progress |
| `GET` | `/api/pipeline/{id}/status` | Pipeline status snapshot |
| `GET` | `/api/pipeline/{id}/results` | Pipeline findings + charts |
| `GET` | `/api/charts/{filename}` | Serve a generated chart image |

---

## NovaMart Demo Dataset

The bundled demo dataset simulates a mid-size e-commerce company with 13 tables:

| Table | Description | Rows (10% scale) |
|---|---|---|
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
| `experiment_assignments` | User-experiment assignments | ~20K |
| `nps_responses` | Net Promoter Score surveys | ~8K |
| `channels` | Marketing channels | ~8 |

Data covers Jan-Dec 2024 with realistic patterns: power-law user activity, hourly traffic patterns, seasonal trends, and intentional data quirks for learning (e.g., `sessions.had_purchase` is unreliable for Nov-Dec 2024).

---

## Configuration

### LLM Provider

The app auto-detects which LLM to use based on which API key is set in `.env`:

| Key Set | Provider | Chat Model | Agent Model |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic | claude-sonnet-4 | claude-sonnet-4 |
| `OPENAI_API_KEY` | OpenAI | gpt-4o | gpt-4o |
| Both | Anthropic (priority) | claude-sonnet-4 | claude-sonnet-4 |

### Snowflake (optional)

For connecting to a live Snowflake warehouse instead of local DuckDB, add Snowflake credentials to `.env`. See `.env.example` for the required variables.

---

## Development

### Running tests

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

## Dependencies

Core dependencies (see `requirements.txt` for full list):

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `duckdb` | In-process SQL database |
| `pandas` | Data manipulation |
| `matplotlib` | Chart generation |
| `seaborn` | Statistical visualization |
| `numpy` / `scipy` | Numerical computation |
| `pyyaml` | YAML configuration |
| `python-dotenv` | Environment variable loading |
| `anthropic` | Claude API client |
| `openai` | GPT API client |
| `python-docx` | Document generation |
| `python-multipart` | File upload handling |

---

## Troubleshooting

### "No LLM API key configured"
Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to your `.env` file and restart the server.

### "Database not found"
The demo DuckDB file should be at `data/practice/novamart_practice.duckdb`. If missing, regenerate it:
```bash
python scripts/generate_all.py
```

### Port already in use
```bash
uvicorn web.app:app --port 8001 --reload
```

### Charts not rendering
Ensure `matplotlib` is installed. On some systems you may need:
```bash
pip install matplotlib --force-reinstall
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
