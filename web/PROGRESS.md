# AI Analyst Web App — Implementation Progress

> **Purpose**: Session-resumption tracker. Read this file first if picking up work in a new session.
> **Plan**: `~/.claude/plans/lets-build-a-simple-starry-babbage.md`

---

## Current Status

**Phase**: Phase 3 COMPLETE — Full Agent Pipeline Execution. Phase 4 (Polish) pending.
**Last updated**: 2026-08-12
**Blocked on**: Nothing

---

## Phase 1: Backend Skeleton + Data Upload + Overview

### 1a. FastAPI app skeleton
- [x] `web/__init__.py`
- [x] `web/app.py` — FastAPI app, CORS, static mount, startup
- [x] `web/config.py` — UPLOAD_DIR, WEB_DUCKDB_PATH, CHART_OUTPUT_DIR, MAX_UPLOAD_SIZE_MB
- [x] Add `data/uploads/` to `.gitignore`

### 1b. Dataset service
- [x] `web/services/__init__.py`
- [x] `web/services/dataset_service.py` — ingest_csv, list_datasets, get_dataset_info, delete_dataset, _make_connection_config

### 1c. Profiling service
- [x] `web/services/profiling_service.py` — direct DuckDB profiling (null rates, unique counts, min/max, samples, quality assessment)

### 1d. API endpoints
- [x] `web/routers/__init__.py`
- [x] `web/routers/datasets.py` — POST /api/datasets/upload, GET /api/datasets, GET /api/datasets/{name}, DELETE /api/datasets/{name}
- [x] `web/routers/schema.py` — GET /api/datasets/{name}/profile, GET /api/datasets/{source}/profile-all
- [x] `web/models/__init__.py`
- [x] `web/models/schemas.py` — Pydantic request/response models

### 1e. Frontend shell + upload + overview
- [x] `web/static/index.html` — three-zone layout (sidebar, workspace, chat input)
- [x] `web/static/css/style.css` — full design system (typography, colors, cards, sidebar, pipeline stepper)
- [x] `web/static/css/components.css` — result cards, schema table, data table, stats row, quality badges, skeleton loader
- [x] `web/static/js/app.js` — core logic, dataset list rendering, dataset selection, chat input wiring
- [x] `web/static/js/upload.js` — drag-and-drop + file picker, progress bar, auto-refresh
- [x] `web/static/js/dashboard.js` — profile rendering (stats/schema/sample cards), card factory
- [ ] Vendor htmx into `web/static/js/htmx.min.js` — SKIPPED: not needed yet, using vanilla fetch

### 1f. Demo data
- [x] On startup, NovaMart auto-detected at `data/practice/novamart_practice.duckdb` — all 13 tables listed as `novamart_demo` source

### Phase 1 verification
- [x] API: GET /api/datasets returns 13 NovaMart tables with row counts and columns
- [x] API: GET /api/datasets/users/profile returns full schema with null rates, unique counts, min/max, samples
- [x] API: POST /api/datasets/upload accepts CSV, creates DuckDB table, returns metadata
- [x] API: DELETE /api/datasets/{name} drops uploaded tables
- [x] Frontend: serves at http://localhost:8000, shows three-zone layout
- [ ] Full browser test: upload CSV → sidebar → click → workspace cards (needs user verification)

---

## Phase 2: Claude/OpenAI API Integration + Chat

### 2a. LLM service
- [x] `web/services/llm_service.py` — Dual-provider: auto-detects ANTHROPIC_API_KEY or OPENAI_API_KEY
  - Anthropic path: claude-sonnet-4, Anthropic tool_use format
  - OpenAI path: gpt-4o, OpenAI function calling format
  - Shared: tool definitions, system prompt, session history, agentic tool-use loop (max 10 iterations)

### 2b. Query service
- [x] `web/services/query_service.py` — execute_sql (SELECT/WITH only, rejects mutations), get_schema_context for LLM prompt

### 2c. Chart service
- [x] `web/services/chart_service.py` — matplotlib Agg backend, thread lock, swd_style + chart_helpers wrappers (bar, line, grouped_bar)
- [x] `web/routers/charts.py` — GET /api/charts/{filename} serves PNGs

### 2d. Analysis service
- [x] `web/services/analysis_service.py` — orchestrates: message → schema context → LLM chat → tool execution → response blocks

### 2e. Chat + query endpoints
- [x] `web/routers/query.py` — POST /api/chat (LLM-powered), POST /api/query (raw SQL)

### 2f. Frontend chat + results
- [x] `web/static/js/chat.js` — send messages, render structured blocks (text, table, chart, error), session persistence via localStorage
- [x] Updated `index.html` with chat.js script
- [x] Result card types: insight (text), table with collapsible SQL, chart (PNG), error
- [x] Loading skeleton animation (from Phase 1)

### Phase 2 backend verification
- [x] POST /api/query — executes SQL, returns 50K user count in 8ms
- [x] SQL sanitizer blocks DROP/ALTER/DELETE/INSERT
- [x] Chart service generates SWD-styled PNGs
- [x] GET /api/charts/{filename} serves PNGs (200, image/png)
- [x] POST /api/chat — returns clear setup message when no API key configured
- [x] Dual-provider detection works (checks ANTHROPIC_API_KEY first, then OPENAI_API_KEY)

### Phase 2 end-to-end verification (requires API key)
- [x] "How many users?" → 50,000 users returned with SQL and explanation (OpenAI GPT-4o)
- [x] "Revenue by category" → bar chart PNG (chart_595d7dd4b8.png, 49KB) + table + analysis
- [x] Follow-up conversation works via session_id
- [x] OpenAI API key added to `.env`, auto-detected by llm_service

---

## Phase 3: Full Agent Pipeline Execution

### 3a. Agent executor
- [x] `web/services/agent_executor.py` — load_agent_template, substitute_variables, execute_agent
  - Dual-provider (Anthropic + OpenAI), 15 iteration tool-use loop
  - Tools: execute_sql, generate_chart, write_finding
  - Strips CONTRACT block from agent templates, substitutes {{VARIABLES}}

### 3b. Pipeline orchestrator
- [x] `web/services/pipeline_orchestrator.py` — load_registry, resolve_execution_plan, execute_pipeline
  - Plans: guided_analysis (L3, 4 agents), deep_investigation (L4, 8), full_presentation (L5, 15)
  - Sequential execution with SSE event emission
  - In-memory run storage, progress callbacks, error handling (critical vs non-critical agents)

### 3c. Pipeline SSE endpoint
- [x] `web/routers/pipeline.py` — POST /api/pipeline/start, GET /api/pipeline/{run_id}/events (SSE), GET /status, GET /results

### 3d. Integration
- [x] `web/services/analysis_service.py` — question classifier (L1-L5 regex), L3+ routes to pipeline
- [x] `web/routers/query.py` — POST /api/chat starts pipeline in background when L3+
- [x] `web/app.py` — pipeline router registered

### 3e. Frontend pipeline experience
- [x] `web/static/js/pipeline.js` — SSE listener, stepper updates, finding/chart/completion cards
- [x] Pipeline stepper component in sidebar (vertical timeline with pulse animation)
- [x] CSS: stepper-step, finding-card, confidence badges in components.css
- [x] index.html: pipeline.js loaded before chat.js
- [x] chat.js: pipeline response handling (auto-start SSE on L3+ response)

### Phase 3 backend verification
- [x] Question classifier: L1 → direct, L2 → direct, L3+ → pipeline
- [x] POST /api/chat L3 question returns run_id + agent list
- [x] Pipeline executes agents sequentially (question-framing → data-explorer → ...)
- [x] GET /api/pipeline/{run_id}/status tracks progress

### Phase 3 end-to-end verification
- [x] L3 pipeline completes: 4/4 agents, 6 findings, 1 chart (chart_07d995bb87.png, 42KB)
- [x] Agent outputs chain: question-framing → data-explorer → descriptive-analytics → validation
- [x] Findings include confidence levels (high/medium/low)
- [x] Chart generated via pipeline (SWD-styled bar chart of order counts by category)
- [x] SSE endpoint delivers events (pipeline_start, phase_start, finding, chart, phase_complete, pipeline_complete)
- [x] L1 questions still route directly (no pipeline): "How many products?" → 500 products
- [ ] Browser UI: sidebar stepper updates in real-time (needs manual browser test)
- [ ] Browser UI: findings + charts appear as cards during pipeline (needs manual browser test)

---

## Phase 4: Polish + Demo Mode

- [ ] Pre-compute NovaMart profile for instant first-load
- [ ] Suggested questions on workspace when NovaMart selected
- [ ] Error handling: bad CSV, bad SQL, API failure, agent failure
- [ ] Responsive design: sidebar collapse, mobile stacking, fixed chat input

---

## Decisions Made During Implementation

| Date | Decision | Reason |
|------|----------|--------|
| 2026-08-12 | Skipped htmx vendor — using vanilla fetch | htmx not needed until SSE streaming in Phase 3 |
| 2026-08-12 | Profiling service uses direct DuckDB queries instead of wrapping schema_profiler | Simpler, avoids import path issues with helpers/, produces same output shape |
| 2026-08-12 | ConnectionManager NOT used for write path | It opens DuckDB as read_only=True; dataset_service uses its own writable connection with thread lock |
| 2026-08-12 | Dual LLM provider support (Anthropic + OpenAI) | User requested OpenAI compatibility; llm_service auto-detects which key is in .env |
| 2026-08-12 | Tool definitions stored in provider-neutral format | Converted to Anthropic `input_schema` or OpenAI `function.parameters` at call time |
| 2026-08-12 | Claude uses claude-sonnet-4, OpenAI uses gpt-4o | Best balance of tool-use capability and cost for both providers |
| 2026-08-12 | Sequential agent execution (not parallel DAG) | Simpler for MVP; avoids dependency resolution bugs when plan agents don't include all deps |
| 2026-08-12 | L1-L5 classification via regex patterns | Fast, no LLM call needed; good enough for routing. L3+ triggers pipeline, L1-L2 goes direct |
| 2026-08-12 | Pipeline runs in BackgroundTasks, SSE for progress | Non-blocking; frontend starts SSE listener immediately after chat response |
| 2026-08-12 | Agent executor has write_finding tool | Agents record structured findings with confidence levels; displayed as cards in frontend |

## Issues Encountered

| Date | Issue | Resolution |
|------|-------|------------|
| 2026-08-12 | Port 8000 already in use on first start | Kill existing process with `lsof -ti:8000 \| xargs kill -9` |

## Files Created/Modified

| File | Status | Notes |
|------|--------|-------|
| web/__init__.py | created | Package init |
| web/app.py | created | FastAPI app, CORS, static mount |
| web/config.py | created | Paths and limits |
| web/routers/__init__.py | created | Package init |
| web/routers/datasets.py | created | Upload, list, get, delete endpoints |
| web/routers/schema.py | created | Profile endpoints |
| web/services/__init__.py | created | Package init |
| web/services/dataset_service.py | created | CSV ingestion, dataset registry, writable DuckDB |
| web/services/profiling_service.py | created | Schema profiling with quality assessment |
| web/models/__init__.py | created | Package init |
| web/models/schemas.py | created | Pydantic models |
| web/static/index.html | created | Three-zone workspace layout |
| web/static/css/style.css | created | Design system (tokens, topbar, sidebar, workspace, chat bar) |
| web/static/css/components.css | created | Cards, tables, stats, quality badges, skeleton loader |
| web/static/js/app.js | created | Core app, dataset list, selection, chat input |
| web/static/js/upload.js | created | Drag-drop upload with progress |
| web/static/js/dashboard.js | created | Profile rendering, card factory |
| .gitignore | modified | Added `data/uploads/` |
| web/PROGRESS.md | created | This file |
| web/services/query_service.py | created | SQL execution with sanitizer + schema context builder |
| web/services/chart_service.py | created | matplotlib Agg + thread lock + SWD chart wrappers |
| web/services/llm_service.py | created → rewritten | Dual-provider: Anthropic (Claude) + OpenAI (GPT) |
| web/services/analysis_service.py | created | Orchestrator: message → LLM → tool execution → response blocks |
| web/routers/query.py | created | POST /api/chat + POST /api/query |
| web/routers/charts.py | created | GET /api/charts/{filename} |
| web/static/js/chat.js | created | Chat send/receive, block rendering, session management |
| web/static/js/app.js | modified | Replaced placeholder sendMessage with Chat.send() |
| web/static/js/dashboard.js | modified | Added collapsible SQL blocks, improved escaping |
| web/static/index.html | modified | Added chat.js script, reordered script loading |
| web/app.py | modified | Registered query + charts + pipeline routers |
| web/services/agent_executor.py | created | Load agent templates, substitute vars, execute via LLM API |
| web/services/pipeline_orchestrator.py | created | DAG walker, plan resolution, sequential execution with SSE events |
| web/routers/pipeline.py | created | POST /api/pipeline/start, GET events (SSE), GET status, GET results |
| web/services/analysis_service.py | modified | Added L1-L5 question classifier, L3+ routes to pipeline |
| web/routers/query.py | modified | Pipeline background task on L3+ chat |
| web/static/js/pipeline.js | created | SSE listener, stepper updates, finding/chart/completion cards |
| web/static/js/chat.js | modified | Pipeline response handling (auto-start SSE) |
| web/static/js/dashboard.js | modified | Added text/finding card types, chart filename fallback |
| web/static/css/components.css | modified | Stepper steps, finding badges, confidence badges |
| web/static/index.html | modified | Added pipeline.js script |

---

## Key Context for Session Resumption

- **Tech stack**: FastAPI + vanilla JS (no build step, no htmx yet)
- **Existing helpers are NOT modified** — web layer wraps them via public APIs
- **ConnectionManager(config=dict)** at `helpers/connection_manager.py:68` bypasses `.knowledge/active.yaml`
- **profile_source(connection_info=dict)** at `helpers/schema_profiler.py:306` bypasses `get_connection_for_profiling()`
- **Web DuckDB** is separate writable file at `data/web_analyst.duckdb`; NovaMart is read-only demo
- **Claude API** powers chat (L1-L2 direct answers) and pipeline agents (L3-L5 DAG execution)
- **Charts** are server-side matplotlib PNGs via `chart_helpers.py` — frontend displays `<img>` tags
- **UI design**: "Analyst Workspace" not chatbot — content cards, not chat bubbles. Warm off-white `#F7F6F2`, amber accent `#D97706`
- **Agent pipeline**: each agent .md template → Claude API call with tools → outputs feed next agent via DAG in `agents/registry.yaml`
- **Dependencies installed**: `fastapi uvicorn python-multipart anthropic openai python-dotenv`
- **LLM setup**: Add `OPENAI_API_KEY=sk-...` or `ANTHROPIC_API_KEY=sk-ant-...` to `.env` (auto-detected)
- **Start server**: `uvicorn web.app:app --reload --port 8000`
- **Server is currently running** on port 8000 with hot-reload
