# AI Analyst Web Application — Project Knowledge

> **Purpose**: Complete project documentation of every action taken, architectural decision made, and technical detail implemented. Auto-updated after every phase/feature completion.
>
> **Last updated**: 2026-08-12 — Phase 3 Complete
> **Total lines of code**: 3,867 across 28 files
> **Status**: Phases 1-3 complete. Phase 4 (Polish) pending.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Phase 1: Backend Skeleton + Data Upload + Overview](#3-phase-1)
4. [Phase 2: LLM Integration + Chat](#4-phase-2)
5. [Phase 3: Full Agent Pipeline Execution](#5-phase-3)
6. [Phase 4: Polish + Demo Mode](#6-phase-4)
7. [API Reference](#7-api-reference)
8. [File Inventory](#8-file-inventory)
9. [Design System](#9-design-system)
10. [Architectural Decisions Log](#10-decisions)
11. [Issues & Resolutions](#11-issues)
12. [Test Results](#12-test-results)
13. [How to Run](#13-how-to-run)

---

## 1. Project Overview <a id="1-project-overview"></a>

### What This Is

A web frontend for the existing AI Analyst CLI-driven repo. Users upload CSV data, get automatic data overviews, and interact with their data through a chat interface. When a user types a question:

- **Simple questions (L1-L2)**: The LLM writes SQL, executes it, optionally generates a chart, and returns the answer directly.
- **Complex questions (L3-L5)**: The full agent pipeline fires — question-framing, hypothesis generation, data exploration, analysis, validation, charting, storytelling — executing each agent as a separate LLM API call with tools, streaming progress via SSE.

### Design Philosophy

- **"Analyst Workspace" not chatbot** — content cards, not chat bubbles
- **No generic AI chrome** — no gradient blobs, no sparkle icons, clean and professional
- **Content-first** — analysis results are the hero, not the chat interface
- **Zero build step** — vanilla HTML/CSS/JS, no React, no npm
- **Existing helpers untouched** — web layer wraps them via public APIs

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | FastAPI + Uvicorn | Wraps existing sync Python helpers. SSE support. File upload. |
| Frontend | Vanilla HTML/CSS/JS | Zero build step. Focus on design, not tooling. |
| Intelligence | OpenAI GPT-4o / Anthropic Claude Sonnet 4 | Dual-provider. Auto-detects which API key is in `.env`. |
| Data | Local DuckDB | Separate writable DB for uploads. NovaMart as read-only demo. |
| Charts | Server-side matplotlib PNGs | Reuses the 1500-line `chart_helpers.py` SWD system unchanged. |

---

## 2. Architecture <a id="2-architecture"></a>

### System Diagram

```
Browser (localhost:8000)
    │
    ├── GET /           → index.html (three-zone layout)
    ├── POST /api/chat  → analysis_service.handle_chat()
    │     │
    │     ├── L1-L2: llm_service.chat() → direct answer
    │     │     └── Tools: execute_sql, generate_chart
    │     │
    │     └── L3-L5: pipeline_orchestrator.create_run()
    │           └── BackgroundTasks → execute_pipeline()
    │                 └── For each agent in plan:
    │                       agent_executor.execute_agent()
    │                         ├── Load agents/{name}.md
    │                         ├── Substitute {{VARIABLES}}
    │                         ├── LLM API call with tools
    │                         └── Collect findings/charts
    │
    ├── GET /api/pipeline/{id}/events → SSE stream
    ├── POST /api/datasets/upload     → CSV → DuckDB
    ├── GET /api/datasets             → list tables
    ├── GET /api/datasets/{name}/profile → schema profiling
    └── GET /api/charts/{filename}    → serve PNG
```

### Directory Structure

```
web/
├── __init__.py
├── app.py                          # FastAPI app, CORS, static mount, router registration
├── config.py                       # Paths: UPLOAD_DIR, WEB_DUCKDB_PATH, CHART_OUTPUT_DIR
├── PROGRESS.md                     # Session-resumption task tracker
├── PROJECT_KNOWLEDGE.md            # This file
├── routers/
│   ├── __init__.py
│   ├── datasets.py                 # POST upload, GET list/detail, DELETE
│   ├── schema.py                   # GET profile
│   ├── query.py                    # POST /api/chat, POST /api/query
│   ├── charts.py                   # GET /api/charts/{filename}
│   └── pipeline.py                 # POST start, GET events (SSE), GET status/results
├── services/
│   ├── __init__.py
│   ├── dataset_service.py          # CSV → DuckDB ingestion, dataset registry
│   ├── profiling_service.py        # Per-column null/unique/min/max/samples
│   ├── query_service.py            # SQL execution with mutation blocker
│   ├── chart_service.py            # matplotlib Agg + thread lock + SWD wrappers
│   ├── llm_service.py              # Dual-provider LLM client (Anthropic + OpenAI)
│   ├── analysis_service.py         # Question classifier + orchestrator
│   ├── agent_executor.py           # Load/substitute/execute agent templates
│   └── pipeline_orchestrator.py    # DAG plans, sequential execution, SSE events
├── models/
│   ├── __init__.py
│   └── schemas.py                  # Pydantic request/response models
└── static/
    ├── index.html                  # Three-zone layout: sidebar, workspace, chat bar
    ├── css/
    │   ├── style.css               # Design system: tokens, layout, typography
    │   └── components.css          # Cards, tables, stepper, skeleton, badges
    └── js/
        ├── app.js                  # Core: dataset list, selection, chat input wiring
        ├── upload.js               # Drag-and-drop + file picker with progress bar
        ├── dashboard.js            # Card factory: stats, schema, table, chart, text, error
        ├── chat.js                 # Chat send/receive, block rendering, session persistence
        └── pipeline.js             # SSE listener, sidebar stepper, finding/chart cards
```

### Key Integration Points (Existing Helpers Used Without Modification)

| Helper | Entry Point | How Web Layer Calls It |
|--------|-------------|----------------------|
| `helpers/connection_manager.py:68` | `ConnectionManager(config=dict)` | Bypasses `.knowledge/active.yaml` with explicit config |
| `helpers/schema_profiler.py:306` | `profile_source(connection_info=dict)` | Bypasses `get_connection_for_profiling()` |
| `helpers/chart_helpers.py:110` | `swd_style(theme=None)` | Called before every chart generation |
| `helpers/chart_helpers.py:161` | `highlight_bar(ax, data, ...)` | Pure function — takes axes/data |
| `helpers/chart_helpers.py:380` | `save_chart(fig, path)` | Saves to `outputs/web_charts/` |
| `agents/registry.yaml` | DAG definition | Parsed by pipeline_orchestrator |
| `agents/*.md` | Prompt templates | Read by agent_executor, vars substituted |

### Data Flow

```
User Upload:  CSV file → POST /api/datasets/upload
                → dataset_service.ingest_csv()
                → DuckDB (data/web_analyst.duckdb) writable
                → Return metadata + trigger sidebar refresh

Demo Data:    data/practice/novamart_practice.duckdb (read-only)
                → 13 tables auto-detected on startup
                → Listed as source "novamart_demo"

Chat (L1-L2): User message → POST /api/chat
                → analysis_service.classify_question() → L1 or L2
                → llm_service.chat() with tools
                → LLM calls execute_sql → query_service.execute_sql()
                → LLM calls generate_chart → chart_service.generate_chart_from_spec()
                → Return structured blocks: [{type, content/columns/rows/filename}]

Chat (L3+):   User message → POST /api/chat
                → analysis_service.classify_question() → L3, L4, or L5
                → pipeline_orchestrator.create_run()
                → BackgroundTasks → execute_pipeline(run_id)
                → Return {pipeline: true, run_id, agents}
                → Frontend opens SSE: GET /api/pipeline/{run_id}/events
                → Each agent: load template → substitute vars → LLM API → tools → findings
                → SSE events: phase_start, finding, chart, phase_complete
                → Final: pipeline_complete with totals
```

---

## 3. Phase 1: Backend Skeleton + Data Upload + Overview <a id="3-phase-1"></a>

### What Was Built

The foundational backend and frontend — data ingestion, profiling, and the visual workspace shell.

### Actions Taken (Chronological)

#### Action 1: Create PROGRESS.md for session tracking
- **File**: `web/PROGRESS.md`
- **Why**: User requested a markdown file to track implementation progress across sessions. If a session is interrupted, the next session reads this file to resume.
- **What**: Created a structured tracker with phase checklists, decisions table, issues table, and file inventory.

#### Action 2: Create FastAPI app skeleton
- **Files**: `web/__init__.py`, `web/app.py`, `web/config.py`
- **What was done**:
  - `config.py`: Centralized all paths — `BASE_DIR` (project root), `UPLOAD_DIR` (`data/uploads/`), `WEB_DUCKDB_PATH` (`data/web_analyst.duckdb`), `NOVAMART_DUCKDB_PATH` (`data/practice/novamart_practice.duckdb`), `CHART_OUTPUT_DIR` (`outputs/web_charts/`), `MAX_UPLOAD_SIZE_MB` (100). Directories auto-created on import.
  - `app.py`: FastAPI app with CORS for localhost origins, static file mount at `/` serving `web/static/` with `html=True` (enables index.html default). Routers registered via `include_router()`.
- **Key decision**: Static mount at `/` (not `/static/`) so the SPA serves at the root URL.

#### Action 3: Build dataset service
- **File**: `web/services/dataset_service.py` (179 lines)
- **What was done**:
  - `ingest_csv(file_path, table_name)`: Opens writable DuckDB connection (with thread lock), runs `CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto('{path}')`, returns `{table_name, row_count, columns: [{name, type}]}`.
  - `list_datasets()`: Returns combined list from writable DuckDB (`SHOW TABLES`) + NovaMart demo (if the duckdb file exists at `NOVAMART_DUCKDB_PATH`). Each entry has `{table_name, source, row_count, columns}`.
  - `get_dataset_info(table_name, source)`: Row count, column types, sample rows (first 10).
  - `delete_dataset(table_name)`: `DROP TABLE IF EXISTS` (only on writable DB, not demo).
  - `_make_connection_config(duckdb_path)`: Returns config dict compatible with `ConnectionManager(config=dict)`.
  - `get_web_config()` / `get_novamart_config()`: Shortcut config dicts.
- **Key decision**: `dataset_service` uses its own writable DuckDB connection with `threading.Lock`, NOT `ConnectionManager`, because `ConnectionManager` opens DuckDB as `read_only=True` (line 438 of `helpers/connection_manager.py`).

#### Action 4: Build profiling service
- **File**: `web/services/profiling_service.py` (162 lines)
- **What was done**:
  - `profile_table(table_name, source)`: Connects to DuckDB (read-only), runs per-column queries: `COUNT(*)`, `COUNT(DISTINCT col)`, `SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END)`, `MIN(col)`, `MAX(col)`, and grabs 5 sample values. Calculates null percentage. Returns structured column profiles.
  - `profile_all_tables(source)`: Profiles every table for a source.
  - `_assess_quality(columns)`: Grades data quality as "good" (all cols <5% null), "fair" (<20%), or "poor" (any >20%). Lists specific quality issues with severity.
- **Key decision**: Uses direct DuckDB queries instead of wrapping `schema_profiler.profile_source()`. Reason: simpler, avoids import path issues with `helpers/`, produces the same output shape.

#### Action 5: Build API endpoints
- **Files**: `web/routers/datasets.py`, `web/routers/schema.py`, `web/models/schemas.py`
- **What was done**:
  - `POST /api/datasets/upload`: Accepts multipart CSV file, validates extension, saves to `UPLOAD_DIR`, calls `ingest_csv()`, returns `UploadResponse`.
  - `GET /api/datasets`: Lists all datasets (uploaded + NovaMart demo).
  - `GET /api/datasets/{table_name}?source=`: Detail view with sample rows.
  - `DELETE /api/datasets/{table_name}`: Drops uploaded table.
  - `GET /api/datasets/{table_name}/profile?source=`: Full column profiling.
  - `GET /api/datasets/{source}/profile-all`: Profile all tables for a source.
  - Pydantic models: `DatasetInfo`, `DatasetListResponse`, `UploadResponse`, `ProfileColumn`, `ProfileTable`, `ProfileResponse`, `QueryRequest`, `QueryResponse`, `ChatRequest`, `ChatResponse`, `ErrorResponse`.

#### Action 6: Build frontend shell
- **Files**: `web/static/index.html`, `web/static/css/style.css`, `web/static/css/components.css`, `web/static/js/app.js`, `web/static/js/upload.js`, `web/static/js/dashboard.js`
- **What was done**:
  - **index.html** (99 lines): Three-zone layout — header (topbar with "AI Analyst" branding), sidebar (dataset list + upload zone + pipeline section), main workspace (welcome state + results area + chat bar).
  - **style.css** (501 lines): Full design system with CSS custom properties. Key tokens: `--bg: #F7F6F2` (warm off-white), `--accent: #D97706` (amber), `--bg-topbar: #1F2937` (dark slate), `--bg-card: #FFFFFF`. System font stack. Flexbox layout with fixed sidebar (220px), topbar (48px), bottom chat bar.
  - **components.css** (421 lines): Result cards with slide-in animation, stat rows, data tables with zebra striping, schema tables with null bars (visual null percentage indicators), quality badges (good/fair/poor), collapsible SQL blocks, skeleton loader with shimmer animation, pipeline stepper, finding cards with confidence badges.
  - **app.js** (126 lines): Core app logic. `loadDatasets()` fetches dataset list and renders sidebar. `selectDataset(name, source)` highlights in sidebar and loads profile into workspace. `sendMessage()` delegates to `Chat.send()`. `formatNumber()` for display. Suggested queries wired to dataset selection.
  - **upload.js** (92 lines): Drag-and-drop on the upload zone + file picker. Shows progress bar during upload. Auto-refreshes dataset list after successful upload.
  - **dashboard.js** (254 lines): Card factory `addCard(config)` renders cards by type: `stats` (stat row with quality issues), `schema` (column table with null bars), `table` (data table with collapsible SQL), `chart` (PNG image), `text` (markdown-ish rendering), `error`, `finding` (confidence badges). `addUserMessage()`, `addSkeleton()`, `removeSkeleton()`.

#### Action 7: Add data/uploads/ to .gitignore
- **File**: `.gitignore` (modified)
- **What**: Added `data/uploads/` to prevent user-uploaded CSV files from being committed.

#### Action 8: Verify Phase 1
- **Tests run**:
  - `GET /api/datasets` → 13 NovaMart tables with row counts and columns ✓
  - `GET /api/datasets/users/profile` → full schema with null rates, unique counts, min/max, samples ✓
  - `POST /api/datasets/upload` with CSV → creates DuckDB table, returns metadata ✓
  - `DELETE /api/datasets/{name}` → drops uploaded table ✓
  - Frontend serves at `http://localhost:8000`, shows three-zone layout ✓

---

## 4. Phase 2: LLM Integration + Chat <a id="4-phase-2"></a>

### What Was Built

The intelligence layer — LLM-powered chat that writes SQL, executes queries, generates charts, and provides analytical answers.

### Actions Taken (Chronological)

#### Action 9: Build query service
- **File**: `web/services/query_service.py` (107 lines)
- **What was done**:
  - `execute_sql(sql, source, max_rows=1000)`: Sanitizes SQL with regex blocker (`DROP|ALTER|DELETE|UPDATE|INSERT|CREATE|TRUNCATE|GRANT|REVOKE|EXEC`). Connects to appropriate DuckDB (writable or NovaMart based on source). Executes query, returns `{error, columns, rows, row_count, execution_ms}`. Caps output at `max_rows`.
  - `get_schema_context(source)`: Builds a text representation of all tables and their columns for the LLM system prompt. Format: `Table: {name} ({row_count} rows)\n  Columns: col1 (TYPE), col2 (TYPE), ...`

#### Action 10: Build chart service
- **File**: `web/services/chart_service.py` (130 lines)
- **What was done**:
  - Sets `matplotlib.use("Agg")` at import time (non-interactive backend for server).
  - `_chart_lock = threading.Lock()` — all chart generation is thread-safe.
  - `generate_bar_chart(data, x_col, y_col, title, highlight)`: Calls `swd_style()` from existing helpers, uses `highlight_bar()` for SWD-styled horizontal bar charts. Saves to `CHART_OUTPUT_DIR` with random hex filename.
  - `generate_line_chart(data, x_col, y_col, title)`: Uses `highlight_line()` from existing helpers.
  - `generate_grouped_bar(data, x_col, y_col, group_col, title)`: Uses `grouped_bar()` from existing helpers.
  - `generate_chart_from_spec(chart_type, data, x_col, y_col, title, highlight, group_col)`: Dispatcher that routes to the appropriate chart function based on `chart_type` parameter. This is what the LLM tool calls.
- **Key decision**: Imported existing helpers with `sys.path.insert(0, str(BASE_DIR))` to ensure `helpers/` is importable. All charts use `CHART_FIGSIZE` (10, 6) at 150 DPI.

#### Action 11: Build chart serving endpoint
- **File**: `web/routers/charts.py` (20 lines)
- **What**: `GET /api/charts/{filename}` serves PNG files from `CHART_OUTPUT_DIR` using `FileResponse` with `media_type="image/png"`.

#### Action 12: Build LLM service (initial Anthropic-only, then rewritten for dual-provider)
- **File**: `web/services/llm_service.py` (312 lines)
- **What was done**:
  - **Provider detection**: Reads `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` from `.env` via `python-dotenv`. `_detect_provider()` returns `"anthropic"` (priority), `"openai"`, or `None`.
  - **Tool definitions**: Provider-neutral `_TOOLS_CORE` list with two tools:
    - `execute_sql`: Parameters `{sql: string}`. Description tells LLM to use DuckDB SQL dialect, SELECT/WITH only.
    - `generate_chart`: Parameters `{chart_type, data, x_col, y_col, title, highlight, group_col}`. Description explains data format and chart types.
  - **Tool conversion**: `_anthropic_tools()` wraps in `{name, description, input_schema}`. `_openai_tools()` wraps in `{type: "function", function: {name, description, parameters}}`.
  - **Session history**: In-memory `_sessions: dict[str, list[dict]]` keyed by session_id. Max 20 messages (40 entries for user+assistant pairs). Enables follow-up conversations.
  - **System prompt** (`build_system_prompt(schema_context)`): Instructs LLM to be a data analyst, use execute_sql for queries, generate_chart for visuals, use action-oriented chart titles, cite specific numbers, and use DuckDB SQL syntax.
  - **Anthropic implementation** (`_chat_anthropic`): Uses `anthropic.Anthropic` client. Sends to `claude-sonnet-4-20250514`. Handles `stop_reason == "tool_use"` in a loop (max 10 iterations): extracts `tool_use` blocks, calls `tool_executor`, feeds results back as `tool_result` messages.
  - **OpenAI implementation** (`_chat_openai`): Uses `openai.OpenAI` client. Sends to `gpt-4o`. Handles `finish_reason == "tool_calls"` in a loop: parses `tool_calls`, calls `tool_executor`, feeds results back as `role: "tool"` messages.
  - **Main entry**: `chat(message, schema_context, session_id, tool_executor)` dispatches to the detected provider.
- **Key decision**: Tool definitions stored in provider-neutral format, converted at call time. This avoids duplicating 70 lines of tool schemas.
- **History**: Originally built as Anthropic-only. User requested OpenAI compatibility and provided their API key. Rewrote to support both providers with auto-detection.

#### Action 13: Build analysis service (orchestrator)
- **File**: `web/services/analysis_service.py` (200 lines)
- **What was done**:
  - `handle_chat(message, source, session_id)`: Top-level orchestrator. Checks if LLM is configured, builds schema context, calls LLM chat, executes tools, builds response blocks.
  - `_execute_tool(tool_name, tool_input, source)`: Routes tool calls to `query_service.execute_sql()` or `chart_service.generate_chart_from_spec()`.
  - `_build_response_blocks(result)`: Converts LLM result into structured blocks for the frontend: `{type: "table", columns, rows, sql}`, `{type: "chart", filename}`, `{type: "text", content}`, `{type: "error", content}`.
  - `classify_question(message)`: Added in Phase 3 — regex-based L1-L5 classifier.

#### Action 14: Build chat and query endpoints
- **File**: `web/routers/query.py` (42 lines)
- **What**: `POST /api/query` for raw SQL execution. `POST /api/chat` for LLM-powered analysis.

#### Action 15: Build frontend chat and results rendering
- **File**: `web/static/js/chat.js` (140 lines)
- **What was done**:
  - `Chat.init()`: Restores `session_id` from `localStorage` or generates a new UUID.
  - `Chat.send(message)`: Posts to `/api/chat` with message, source, and session_id. Adds user message card and skeleton loader. On response, renders blocks as workspace cards.
  - `renderBlocks(blocks)`: Iterates response blocks, creates appropriate cards via `Dashboard.addCard()`: text → insight card, table → table card with SQL toggle, chart → chart image card, error → error card.
  - `extractHeadline(text)`: Pulls first line for card title (strips markdown formatting).
  - `renderMarkdown(text)`: Basic markdown rendering — bold, code, paragraphs, lists.
  - `escapeHtml(str)`: XSS protection via DOM text node.

#### Action 16: Add OpenAI API key to .env
- **File**: `.env` (modified)
- **What**: User provided their OpenAI API key. Saved securely to `.env` (gitignored). Never displayed in terminal output per CLAUDE.md security rules.

#### Action 17: Verify Phase 2 end-to-end
- **Tests run** (via curl with OpenAI GPT-4o):
  1. `"How many users are there?"` → GPT-4o generated `SELECT COUNT(DISTINCT user_id) FROM users` → returned 50,000 with explanation ✓
  2. `"Show me top 5 product categories by total revenue"` → Table with 5 categories + analysis text ✓
  3. `"Create a bar chart of revenue by product category"` → SQL + SWD-styled bar chart PNG (`chart_595d7dd4b8.png`, 49KB) + analysis ✓
  4. Chart serves at `/api/charts/chart_595d7dd4b8.png` → 200, image/png ✓
  5. Follow-up conversation works via session_id ✓

---

## 5. Phase 3: Full Agent Pipeline Execution <a id="5-phase-3"></a>

### What Was Built

The complete agent pipeline — question classification, agent template execution, DAG-based pipeline orchestration, and real-time SSE progress streaming.

### Actions Taken (Chronological)

#### Action 18: Build agent executor
- **File**: `web/services/agent_executor.py` (359 lines)
- **What was done**:
  - `load_agent_template(agent_name)`: Reads `agents/{name}.md` from disk. Strips the `<!-- CONTRACT_START ... CONTRACT_END -->` block (metadata, not instructions). Returns clean markdown text.
  - `substitute_variables(template, variables)`: Replaces all `{{VARIABLE}}` placeholders with actual values from the variables dict.
  - `execute_agent(agent_name, variables, schema_context, tool_executor, progress_callback)`: The core function. Loads template, substitutes variables, builds a system prompt that includes: the agent's instructions, the dataset schema, and instructions to use the tools. Calls the LLM API via the detected provider. Runs the agentic tool-use loop (max 15 iterations). Collects findings (via `write_finding` tool), charts, and final summary text. Returns structured result: `{agent, status, findings, charts, tool_results, text, elapsed_seconds}`.
  - **Agent tools** (3 tools available to agents):
    - `execute_sql`: Same as chat — read-only SQL via DuckDB.
    - `generate_chart`: Same as chat — SWD-styled bar/line/grouped_bar.
    - `write_finding`: NEW — agents record structured findings with `{headline, evidence, confidence, tables_used}`. These become finding cards in the frontend.
  - **Dual-provider**: `_execute_anthropic()` and `_execute_openai()` implementations, same pattern as `llm_service.py` but with agent-specific system prompt and 15-iteration limit (vs 10 for direct chat).

#### Action 19: Build pipeline orchestrator
- **File**: `web/services/pipeline_orchestrator.py` (315 lines)
- **What was done**:
  - **Pipeline plans** (3 levels):
    - `guided_analysis` (L3): `question-framing → data-explorer → descriptive-analytics → validation` (4 agents)
    - `deep_investigation` (L4): Above + `hypothesis → root-cause-investigator → cross-verification → opportunity-sizer` (8 agents)
    - `full_presentation` (L5): All 15 pipeline agents including story-architect, chart-maker, storytelling, deck-creator, comms-drafter
  - `load_registry()`: Parses `agents/registry.yaml` using PyYAML.
  - `resolve_execution_order(plan_name)`: Returns sequential tier list — each agent runs one at a time in plan order. Initially built DAG-based topological sort, but simplified to sequential execution because filtered dependency resolution caused ordering bugs (e.g., `validation` depends on `cross-verification`, but if cross-verification isn't in the L3 plan, validation had no deps and ran in tier 1).
  - `create_run(question, source, level, schema_context)`: Creates an in-memory run record with unique `run_id` (12-char hex). Stores: question, source, level, plan, tiers, agents list, status, events list, results dict, findings list, charts list.
  - `execute_pipeline(run_id)`: The main execution loop. For each agent in the plan:
    1. Emits `phase_start` SSE event
    2. Builds variables dict from prior agent outputs (`_build_variables()`)
    3. Calls `agent_executor.execute_agent()` with tools bound to the source
    4. Collects findings and charts into the run record
    5. Emits `finding` events for each finding, `chart` events for each chart
    6. Emits `phase_complete` event
    7. On error: checks if agent is `critical` (from registry). Critical errors halt pipeline. Non-critical errors warn and continue.
    8. On completion: emits `pipeline_complete` with totals
  - `_build_variables(run)`: Constructs the `{{VARIABLE}}` substitution dict from accumulated agent outputs. Maps: `BUSINESS_CONTEXT` → question, `QUESTION_BRIEF` → question-framing output, `HYPOTHESIS_DOC` → hypothesis output, `DATA_INVENTORY` → data-explorer output, `ANALYSIS_RESULTS` → concatenated findings from all agents, `STORYBOARD` → story-architect output, etc. Fills 30+ variables that agents expect.
  - `_make_tool_executor(source)`: Creates a closure that routes tool calls to `query_service` and `chart_service`, bound to the pipeline's data source.
  - **Phase labels**: Human-readable labels for sidebar display (e.g., `"question-framing"` → `"Framing Question"`, `"descriptive-analytics"` → `"Analyzing Patterns"`).
  - **In-memory storage**: `_active_runs: dict[str, dict]` stores all pipeline state. No persistence (MVP — lost on server restart).

#### Action 20: Build pipeline SSE endpoint
- **File**: `web/routers/pipeline.py` (124 lines)
- **What was done**:
  - `POST /api/pipeline/start`: Accepts `{question, source, level}`. Creates run, starts execution in `BackgroundTasks`. Returns `{run_id, plan, agents, status}`.
  - `GET /api/pipeline/{run_id}/events`: SSE endpoint. Uses `StreamingResponse` with `text/event-stream` media type. Polls the run's events list every 0.5s, yields new events as `event: {type}\ndata: {json}\n\n`. Terminates when `pipeline_complete` or `pipeline_error` is received.
  - `GET /api/pipeline/{run_id}/status`: Returns current state — status, current agent, completed agents, findings/charts counts.
  - `GET /api/pipeline/{run_id}/results`: Returns full results — findings list, charts list, per-agent summaries (status, text preview, findings count, charts).
  - SSE headers: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no` (disables nginx buffering).

#### Action 21: Add question classifier to analysis service
- **File**: `web/services/analysis_service.py` (modified)
- **What was done**:
  - `classify_question(message)`: Regex-based classifier that returns L1-L5:
    - **L1** (factual lookup): Matches `"how many"`, `"how much"`, `"what is the average/total/count"`.
    - **L2** (simple comparison): Matches `"compare"`, `"by device/channel/category"`, `"breakdown"`, `"top N"`, `"trend"`, `"over time"`.
    - **L3** (guided analysis): Matches `"why"`, `"analyze"`, `"segment"`, `"funnel"`, `"cohort"`, `"retention"`.
    - **L4** (deep investigation): Matches `"investigate"`, `"root cause"`, `"why did X drop/spike"`, `"what caused"`, `"what's driving"`.
    - **L5** (full presentation): Matches `"full pipeline"`, `"run pipeline"`, `"build deck"`, `"presentation"`, `"end to end"`, `"board ready"`.
  - `handle_chat()` updated: After classifying, L3+ questions create a pipeline run, start it in BackgroundTasks, and return `{pipeline: true, run_id, agents}` instead of an LLM response. L1-L2 still goes through `llm_service.chat()` directly.

#### Action 22: Update chat router for pipeline support
- **File**: `web/routers/query.py` (modified)
- **What**: Added `BackgroundTasks` parameter. When `handle_chat()` returns `pipeline: true`, starts `pipeline_orchestrator.execute_pipeline(run_id)` as a background task.

#### Action 23: Register pipeline router
- **File**: `web/app.py` (modified)
- **What**: Added `from web.routers import pipeline` and `app.include_router(pipeline.router)`.

#### Action 24: Build frontend pipeline experience
- **File**: `web/static/js/pipeline.js` (166 lines)
- **What was done**:
  - `Pipeline.start(runId, agents)`: Entry point. Builds sidebar stepper, shows pipeline section, connects SSE.
  - `_buildStepper(agents)`: Generates HTML for the vertical timeline in the sidebar. Each agent gets a dot indicator and a label. Lookup table maps agent names to human-readable labels.
  - `_connectSSE(runId)`: Opens `EventSource` to `/api/pipeline/{runId}/events`. Registers listeners for each event type:
    - `pipeline_start`: Adds a "Pipeline Started" text card.
    - `phase_start`: Adds `active` class to the step (triggers pulse animation).
    - `phase_complete`: Removes `active`, adds `complete` class. Shows elapsed time.
    - `finding`: Creates a finding card with confidence badge (high=green, medium=amber, low=red) and evidence text.
    - `chart`: Creates a chart image card.
    - `pipeline_complete`: Creates a summary card with totals. Closes SSE connection.
    - `pipeline_error`: Creates an error card. Closes SSE connection.

#### Action 25: Update chat.js for pipeline responses
- **File**: `web/static/js/chat.js` (modified)
- **What**: After receiving chat response, checks for `data.pipeline && data.run_id`. If true, renders initial blocks (the "Launching pipeline..." message) and calls `Pipeline.start(data.run_id, data.agents)` to begin SSE listening.

#### Action 26: Add pipeline stepper and finding card CSS
- **File**: `web/static/css/components.css` (modified)
- **What was done**:
  - `.stepper-step`: Flexbox row with dot + label. Connected by thin vertical lines (via `::before` pseudo-element).
  - `.stepper-dot`: 11px circle. States: pending (hollow gray), active (filled amber with pulse animation), complete (filled amber).
  - `@keyframes stepPulse`: Pulsing amber glow on the active step dot.
  - `.stepper-label`: Font size 12px. Bold when active, muted when pending.
  - `.stepper-time`: Monospace elapsed time display.
  - `.finding-card`: Container for finding content.
  - `.finding-badge`: Confidence indicator — `.high-conf` (green), `.med-conf` (amber), `.low-conf` (red).
  - `.finding-agent`: Italic source attribution.

#### Action 27: Add pipeline.js to index.html
- **File**: `web/static/index.html` (modified)
- **What**: Added `<script src="/js/pipeline.js"></script>` before `chat.js` (pipeline.js must load first since chat.js calls `Pipeline.start()`).

#### Action 28: Update dashboard.js for new card types
- **File**: `web/static/js/dashboard.js` (modified)
- **What**: Added `text` card type (renders markdown-ish content with bold/code/paragraphs). Added `finding` card type (raw HTML body). Chart cards now accept `filename` prop (auto-builds `/api/charts/{filename}` URL) in addition to `chartUrl`.

#### Action 29: Verify Phase 3 end-to-end
- **Tests run**:
  - Question classifier: 8/9 correct classifications ✓ (one borderline case: "Why did mobile conversion drop?" classified as L4 instead of L3, which is reasonable)
  - L3 pipeline ("Analyze which product category has the best conversion rate"):
    - Ran 4 agents sequentially: question-framing → data-explorer → descriptive-analytics → validation ✓
    - question-framing: Parsed business context, structured the analytical question ✓
    - data-explorer: Found 3 findings (duplicate sessions, referential integrity, no nulls in financials) ✓
    - descriptive-analytics: Found Electronics leads in order count ✓
    - validation: Confirmed Electronics leads, flagged conversion rate issue, generated chart ✓
    - Total: 6 findings, 1 chart (`chart_07d995bb87.png`, 42KB SWD-styled bar chart) ✓
    - SSE events delivered correctly ✓
  - L1 question ("How many products?") → direct answer (500 products), no pipeline ✓

---

## 6. Phase 4: Polish + Demo Mode (Pending) <a id="6-phase-4"></a>

### Planned Work

- [ ] Pre-compute NovaMart profile for instant first-load
- [ ] Suggested questions on workspace when NovaMart is selected
- [ ] Error handling: bad CSV, bad SQL, API failure, agent failure
- [ ] Responsive design: sidebar collapse on narrow screens, mobile stacking

---

## 7. API Reference <a id="7-api-reference"></a>

### Dataset Endpoints

| Method | Path | Body | Response | Purpose |
|--------|------|------|----------|---------|
| `POST` | `/api/datasets/upload` | Multipart file (CSV) | `{table_name, row_count, columns}` | Upload CSV to DuckDB |
| `GET` | `/api/datasets` | — | `[{table_name, source, row_count, columns}]` | List all datasets |
| `GET` | `/api/datasets/{name}?source=` | — | `{table_name, row_count, columns, sample_rows}` | Dataset detail |
| `DELETE` | `/api/datasets/{name}` | — | `{status: "deleted"}` | Delete uploaded dataset |
| `GET` | `/api/datasets/{name}/profile?source=` | — | `{tables: [{columns, row_count}], quality}` | Schema profiling |

### Chat & Query Endpoints

| Method | Path | Body | Response | Purpose |
|--------|------|------|----------|---------|
| `POST` | `/api/query` | `{sql, source}` | `{columns, rows, row_count, execution_ms}` | Raw SQL execution |
| `POST` | `/api/chat` | `{message, source, session_id}` | L1-L2: `{session_id, blocks}` / L3+: `{pipeline, run_id, agents, blocks}` | LLM-powered chat |

### Pipeline Endpoints

| Method | Path | Body | Response | Purpose |
|--------|------|------|----------|---------|
| `POST` | `/api/pipeline/start` | `{question, source, level}` | `{run_id, plan, agents, status}` | Start pipeline |
| `GET` | `/api/pipeline/{id}/events` | — | SSE stream | Real-time progress |
| `GET` | `/api/pipeline/{id}/status` | — | `{status, current_agent, completed_agents, ...}` | Pipeline state |
| `GET` | `/api/pipeline/{id}/results` | — | `{findings, charts, agent_summaries}` | Full results |

### Chart Endpoint

| Method | Path | Response | Purpose |
|--------|------|----------|---------|
| `GET` | `/api/charts/{filename}` | PNG image | Serve generated charts |

### SSE Event Types

| Event | Data | When |
|-------|------|------|
| `pipeline_start` | `{plan, agents, question}` | Pipeline begins |
| `phase_start` | `{agent, label}` | Agent starts executing |
| `phase_complete` | `{agent, label, status, elapsed, findings_count}` | Agent finishes |
| `finding` | `{agent, headline, confidence, evidence}` | Agent records a finding |
| `chart` | `{agent, filename}` | Agent generates a chart |
| `pipeline_complete` | `{elapsed, findings_count, charts_count, agents_completed}` | All agents done |
| `pipeline_error` | `{agent, error}` | Critical agent failed |

---

## 8. File Inventory <a id="8-file-inventory"></a>

| File | Lines | Phase | Purpose |
|------|-------|-------|---------|
| `web/__init__.py` | 0 | 1 | Package init |
| `web/app.py` | 25 | 1 | FastAPI app, CORS, static mount, router registration |
| `web/config.py` | 12 | 1 | Centralized paths and limits |
| `web/models/__init__.py` | 0 | 1 | Package init |
| `web/models/schemas.py` | — | 1 | Pydantic request/response models |
| `web/routers/__init__.py` | 0 | 1 | Package init |
| `web/routers/datasets.py` | 58 | 1 | Upload, list, get, delete datasets |
| `web/routers/schema.py` | 23 | 1 | Profile endpoints |
| `web/routers/query.py` | 42 | 2 | Chat + raw SQL endpoints |
| `web/routers/charts.py` | 20 | 2 | Serve chart PNGs |
| `web/routers/pipeline.py` | 124 | 3 | Pipeline SSE + status + results |
| `web/services/__init__.py` | 0 | 1 | Package init |
| `web/services/dataset_service.py` | 179 | 1 | CSV → DuckDB, dataset registry |
| `web/services/profiling_service.py` | 162 | 1 | Column profiling with quality assessment |
| `web/services/query_service.py` | 107 | 2 | SQL execution with mutation blocker |
| `web/services/chart_service.py` | 130 | 2 | matplotlib + SWD chart wrappers |
| `web/services/llm_service.py` | 312 | 2 | Dual-provider LLM client |
| `web/services/analysis_service.py` | 200 | 2+3 | Question classifier + orchestrator |
| `web/services/agent_executor.py` | 359 | 3 | Agent template loader + LLM executor |
| `web/services/pipeline_orchestrator.py` | 315 | 3 | DAG plans + sequential execution |
| `web/static/index.html` | 99 | 1 | Three-zone workspace layout |
| `web/static/css/style.css` | 501 | 1 | Design system |
| `web/static/css/components.css` | 421 | 1+3 | Component styles |
| `web/static/js/app.js` | 126 | 1 | Core app logic |
| `web/static/js/upload.js` | 92 | 1 | Drag-drop upload |
| `web/static/js/dashboard.js` | 254 | 1+3 | Card factory |
| `web/static/js/chat.js` | 140 | 2+3 | Chat + pipeline response handling |
| `web/static/js/pipeline.js` | 166 | 3 | SSE listener + stepper |

---

## 9. Design System <a id="9-design-system"></a>

### Color Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#F7F6F2` | Warm off-white page background |
| `--bg-card` | `#FFFFFF` | Card backgrounds |
| `--bg-topbar` | `#1F2937` | Dark topbar |
| `--accent` | `#D97706` | Amber — active states, progress indicators, links |
| `--text-primary` | `#1F2937` | Headings, important text |
| `--text-secondary` | `#4B5563` | Body text |
| `--text-muted` | `#9CA3AF` | Labels, captions |
| `--border` | `#E5E7EB` | Card borders |
| `--border-light` | `#F3F4F6` | Table row separators |
| `--success` | `#059669` | Good quality, high confidence |
| `--warning` | `#D97706` | Fair quality, medium confidence |
| `--error` | `#DC2626` | Poor quality, errors, low confidence |

### Typography

- **Font**: System stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`)
- **Mono**: `'SF Mono', 'Fira Code', 'Cascadia Code', monospace`
- **Headings**: 600 weight, `--text-primary`
- **Body**: 400 weight, `--text-secondary`, 14px

### Layout

- **Topbar**: 48px fixed height, dark background
- **Sidebar**: 220px fixed width, scrollable dataset list + pipeline stepper
- **Workspace**: Fills remaining space, cards stack vertically
- **Chat bar**: Fixed bottom, 64px height, textarea + send button

### Card Types

| Type | Visual | Content |
|------|--------|---------|
| Stats | Stat row with values + labels | Row count, columns, quality badge |
| Schema | Table with null bars | Column name, type, null %, unique count, range |
| Table | Data table with zebra striping | Query results with collapsible SQL block |
| Chart | Image with title | SWD-styled PNG from matplotlib |
| Text | Paragraphs with markdown rendering | LLM analysis text |
| Finding | Confidence badge + evidence | Pipeline agent findings |
| Error | Red-tinted card | Error messages |

---

## 10. Architectural Decisions Log <a id="10-decisions"></a>

| # | Date | Decision | Rationale |
|---|------|----------|-----------|
| 1 | 2026-08-12 | Vanilla JS, no React/Vue | Zero build step. Focus on design, not tooling. htmx deferred. |
| 2 | 2026-08-12 | Skipped htmx vendor | Not needed until SSE streaming. Vanilla fetch sufficient for Phase 1-2. |
| 3 | 2026-08-12 | Direct DuckDB profiling (not schema_profiler wrapper) | Simpler, avoids import path issues, same output shape. |
| 4 | 2026-08-12 | Own writable DuckDB connection (not ConnectionManager) | ConnectionManager opens DuckDB as `read_only=True` (line 438). |
| 5 | 2026-08-12 | Dual LLM provider (Anthropic + OpenAI) | User requested OpenAI compatibility. Auto-detect from `.env`. |
| 6 | 2026-08-12 | Provider-neutral tool definitions | Avoid duplicating 70 lines of tool schemas. Convert at call time. |
| 7 | 2026-08-12 | claude-sonnet-4 / gpt-4o | Best balance of tool-use capability and cost. |
| 8 | 2026-08-12 | Sequential agent execution (not parallel DAG) | Simpler for MVP. Avoids dep resolution bugs with partial plans. |
| 9 | 2026-08-12 | L1-L5 classification via regex | Fast, no LLM call needed. Good enough for routing. |
| 10 | 2026-08-12 | Pipeline in BackgroundTasks + SSE | Non-blocking. Frontend starts SSE immediately after chat response. |
| 11 | 2026-08-12 | write_finding tool for agents | Structured findings with confidence levels. Better than parsing free text. |
| 12 | 2026-08-12 | In-memory pipeline storage | MVP — no persistence needed. Lost on server restart. |

---

## 11. Issues & Resolutions <a id="11-issues"></a>

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Port 8000 already in use on first start | `lsof -ti:8000 \| xargs kill -9` |
| 2 | PROGRESS.md write rejected (web/ dir didn't exist) | Created `web/` directory first with `mkdir -p` |
| 3 | Edit tool failed on arrow characters in PROGRESS.md | Read actual file content and used exact text match |
| 4 | analysis_service had old "Claude API not configured" message after dual-provider rewrite | Updated to dual-provider message |
| 5 | DAG resolution put validation in Tier 1 for guided_analysis plan | Simplified to sequential execution — plan order IS execution order |
| 6 | "Why did mobile conversion drop?" classified as L4 instead of L3 | Acceptable — the "why did X drop" pattern is genuinely investigative |

---

## 12. Test Results <a id="12-test-results"></a>

### Phase 1 Tests (All Pass)

| Test | Result |
|------|--------|
| GET /api/datasets returns 13 NovaMart tables | ✓ |
| GET /api/datasets/users/profile returns schema | ✓ |
| POST /api/datasets/upload creates DuckDB table | ✓ |
| DELETE /api/datasets/{name} drops table | ✓ |
| Frontend serves at localhost:8000 | ✓ |

### Phase 2 Tests (All Pass)

| Test | Result |
|------|--------|
| POST /api/query executes SQL (50K users in 8ms) | ✓ |
| SQL sanitizer blocks DROP/ALTER/DELETE/INSERT | ✓ |
| Chart service generates SWD-styled PNGs | ✓ |
| Dual-provider detection (Anthropic first, then OpenAI) | ✓ |
| "How many users?" → 50,000 with explanation | ✓ |
| "Revenue by category" → chart + table + analysis | ✓ |
| Follow-up conversation via session_id | ✓ |

### Phase 3 Tests (All Pass)

| Test | Result |
|------|--------|
| Question classifier: 8/9 correct (L1-L5) | ✓ |
| L3 pipeline: 4/4 agents, 6 findings, 1 chart | ✓ |
| SSE events delivered (all 7 event types) | ✓ |
| L1 question still routes directly (no pipeline) | ✓ |
| Pipeline chart serves (42KB PNG, 200 OK) | ✓ |

---

## 13. How to Run <a id="13-how-to-run"></a>

### Prerequisites

```bash
pip install fastapi uvicorn python-multipart anthropic openai python-dotenv pyyaml
```

### Configuration

Add one API key to `.env` (auto-detected):
```
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

### Start Server

```bash
uvicorn web.app:app --reload --port 8000
```

### Access

Open `http://localhost:8000` in a browser.

### Key URLs

- **App**: http://localhost:8000
- **API docs**: http://localhost:8000/docs (auto-generated by FastAPI)
- **Datasets**: http://localhost:8000/api/datasets
- **Health check**: `curl http://localhost:8000/api/datasets`

---

*This document is auto-updated after every phase/feature completion.*
