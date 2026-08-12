STATUS: REPORT ONLY — NO CHANGES MADE.

# AI Analyst — De-duplication / Drop Candidates, Round 2

**Scope:** ADDITIONAL candidates NOT covered by `docs/internal/dedupe-report.md`
(which handled knowledge subsystems, `tieout_helpers.py`, and the validation stack —
those are deliberately excluded here). This round covers: (1) skill redundancy,
(2) dead/unused helpers, (3) droppable features, (4) stale course/naming content,
(5) large/vestigial tracked files.

**Method:** Read the actual skill `description` blocks and bodies; traced helper
import/reference graphs via grep across `.py`, `.md` skill/agent docs, `scripts/`,
`tests/`, and top-level docs; `git ls-files | xargs wc -l` for size; checked
`.gitignore` for deliberately-tracked outputs. Where I did not exhaustively verify,
I say so.

**Headline:** The biggest, lowest-risk wins are stale/orphan cleanup, not merges.
`config_helpers.py` (333 lines) and `google_auth_helpers.py` (253 lines) are
truly orphaned. CLAUDE.md's skill table lists 4 skills that don't exist on disk
(Demo, Certificate, First-Run Welcome, Show Off LinkedIn) while 3 skills on disk
(`teach`, `north-star`, `skill-creator`) are missing from it. A 1.4 MB demo PDF is
force-tracked. Skill *merges* exist (export dispatcher vs standalone export skills;
two analysis-design skills; the data-inspection cluster) but carry more risk and
should be human-decided.

**Important caveat on "dead" helpers:** This codebase deliberately invokes many
helpers via **Python-in-markdown code blocks** inside skill/agent `.md` files that
Claude executes through Bash — so "zero `.py` importers" does NOT mean dead. I
classified each helper by whether it has *any* live invocation path (py import OR
documented skill/agent code block) vs. *none at all*. Only the latter are flagged
as orphans.

---

## Area 1 — Skill Redundancy

There are 66 skill directories under `.claude/skills/`. Most are genuinely distinct.
The clusters below have real overlap worth a human merge decision. I recommend
**conservative** action — none of these are slam-dunk auto-merges.

### 1A. Export cluster — dispatcher vs. standalone skills (MED confidence)
**What:** `export/skill.md` (333 ln) is a multi-format dispatcher. `/export gdoc`,
`/export notion`, `/export slides` each re-describe and delegate into the standalone
skills `google-doc-export` (472 ln), `notion-export` (201 ln), and Marp slide logic.
`google-slides-export` (458 ln) and `chart-to-drive` (176 ln) are separate again.

**Evidence:** `export/skill.md:18,20,86-274` contains full inline procedures for the
gdoc and notion paths (auth check, parse, build, upload) AND
`export/skill.md:257` says "Follows the Notion Export skill
(`.claude/skills/notion-export/skill.md`)" and `export/skill.md:263` invokes the
`notion-export` agent. So the gdoc/notion procedure is specified in *both* the
dispatcher and the standalone skill — classic prose-drift risk.

**Recommendation:** KEEP the standalone skills as the single source of truth; SLIM
the `export` dispatcher's gdoc/notion/slides sections down to a trigger + pointer
("run the `google-doc-export` skill") rather than duplicating the full procedure.
Do NOT delete any skill — the standalone skills carry deep design-system detail
(layout libraries, pre-flight checklists) the dispatcher should not absorb.
**Risk:** Low-Med (prompt drift if left; merge could lose a step — diff carefully).
**Effort:** M. **Confidence:** Med.

### 1B. analysis-design vs analysis-design-spec — overlapping triggers (MED-HIGH)
**What:** `analysis-design` (313 ln) and `analysis-design-spec` (193 ln) both fire
on the *same* trigger vocabulary.

**Evidence:** `analysis-design/skill.md:4` triggers on "analyze why", "investigate",
"look into", "what's driving". `analysis-design-spec/skill.md:4` triggers on
"analyze, investigate, look into, what happened with, compare … why did, what caused"
and says "Use this skill at the start of EVERY analytical request." These two will
collide on virtually every L3+ request. They are conceptually different (`-spec` is a
lightweight 7-field upfront contract; `analysis-design` is a heavy 6-stage agent
pipeline hunch→V2), but their descriptions don't carve a clean boundary — `-spec`
claims "EVERY analytical request" and `analysis-design` claims "any analytical
question that needs methodological rigor."

**Recommendation:** KEEP BOTH but TIGHTEN descriptions so `-spec` = the always-on
lightweight pre-query contract (referenced by CLAUDE.md Default Workflow step 2) and
`analysis-design` = the explicit `/analysis-design` heavy pipeline (invoke-on-demand
only). Remove the broad "analyze/investigate" auto-triggers from `analysis-design`
so it only fires on explicit invocation or "design an analysis for…". This prevents
double-firing.
**Risk:** Low (prompt-wording only). **Effort:** S. **Confidence:** Med-High.

### 1C. stress-test vs analysis-design's confound stage (LOW — keep)
**What:** `/stress-test` (269 ln) is a 7-point methodological review; `analysis-design`
Stage 2 is the "Confound Scanner" (`analysis-design/skill.md:127-128`).
**Evidence:** Overlap is partial (confounds) but stress-test is broader (baselines,
survivorship, kill criteria) and explicitly standalone ("works standalone — reviews
ANY plan"). analysis-design uses a dedicated `agents/confound-scanner` agent.
**Recommendation:** KEEP SEPARATE — genuinely distinct scope. Optional: have
analysis-design reference `/stress-test` as the post-V1 review step instead of any
overlap. **Risk:** n/a. **Effort:** —. **Confidence:** High (verdict: keep).

### 1D. Deck cluster: deck-critique / slide-transform / deck-rescue (LOW — keep)
**What:** `deck-critique` (288 ln, score a deck), `slide-transform` (256 ln, fix ONE
slide → variants), `deck-rescue` (231 ln, full deck rewrite pipeline).
**Evidence:** Three distinct granularities (whole-deck scoring vs single-slide
redesign vs full rewrite). `deck-rescue` chains diagnose→rebuild; the others are
narrower. All three reference the shared `deck_parser.py` fallback.
**Recommendation:** KEEP ALL THREE — distinct unit of work each. They form a
coherent suite. **Risk:** n/a. **Confidence:** High (verdict: keep).

### 1E. Data-inspection cluster — overlapping triggers (MED)
**What:** `data-inspect` (159 ln), `data-map` (232 ln), `datasets` (95 ln),
`explore` (200 ln), `data-profiling` (227 ln), `distribution-profiler` (266 ln).
**Evidence — real trigger collision:** `data-inspect:desc` fires on
"what's in this dataset?", "describe the data". `explore:desc` ALSO fires on
"what's in this dataset?", "what tables are available?". `data-map:desc` ALSO fires
on "tell me about this data" / "what's in here". All three claim the broad
first-contact question. The CLAUDE.md Rules 18/19 + the skills themselves try to
carve boundaries (table-scoped → data-quality-check; dataset-wide → data-map;
follow-up → explore) but three skills still advertise the same opening phrases.
**Recommendation:** KEEP the six (they have distinct jobs: schema dump vs health-map
vs dataset list vs interactive browse vs deep profile vs single-column stats), but
DE-OVERLAP the descriptions so only `data-map` claims the broad "what's in this
data" first-contact phrasing, `data-inspect` claims only `/data`+schema phrasing,
and `explore` claims only `/explore`+already-mapped follow-ups. This is the same
boundary CLAUDE.md Rules 18/19 already assert — the skill descriptions just haven't
been aligned to it.
**Risk:** Low (description tuning). **Effort:** M (6 files). **Confidence:** Med.

### 1F. Setup cluster (LOW — keep, all distinct)
`setup` (general interview), `setup-dev-context`, `setup-notion`, `setup-snowflake`,
`connect-data` are each connector/context-specific. No true duplication.
**Recommendation:** KEEP ALL. **Confidence:** High (verdict: keep).

---

## Area 2 — Dead / Unused Helpers

Method: counted prod-`.py` importers, test-`.py` importers, and any skill/agent
`.md` code-block references for each helper. Flagging ONLY helpers with **no live
invocation path of any kind**.

### 2A. `helpers/google_auth_helpers.py` — TRULY ORPHANED (HIGH)
**What:** 253 lines. Provides `check_auth_status`, `get_token_path`, etc. for Google
MCP auth preflight.
**Evidence:** `grep -rn "google_auth_helpers\|google_auth"` returns **zero hits**
anywhere outside the file itself — not in `.py`, not in any skill/agent `.md`, not in
`helpers/INDEX.md`. The work it would do is instead done by inline bash in
`auth-preflight/skill.md` (e.g. line 213 `ls -lh ~/.claude/mcp-servers/.../token.json`).
(Note: round-1's helper-hunt sub-agent mis-reported this as referenced at
`INDEX.md:53` — I verified it is NOT.)
**Recommendation:** DROP. Nothing imports or documents it; `auth-preflight` reimplements
it in bash. **Risk:** Low. **Effort:** S. **Confidence:** High.

### 2B. `helpers/config_helpers.py` — EFFECTIVELY ORPHANED (HIGH)
**What:** 333 lines. "centralized config management … reads `.knowledge/config.yaml`"
— `get_output_dir`, `get_analysis_path`, `get_chart_path`, etc.
**Evidence:** Zero `.py` importers. Its ONLY two references are negative/documentation:
`setup-dev-context/skill.md:212` lists it as an example of what to **"Do NOT create"**,
and `helpers/INDEX.md` lists it. No skill or agent code block ever imports it. The
path-resolution functions it offers are not wired into the output conventions the
pipeline actually uses (`outputs/{RUN_ID}/` is handled elsewhere). Also note it
references `.knowledge/config.yaml`, which does not appear to be a live config file.
**Recommendation:** DROP (or, if any path helper is genuinely wanted, re-home the one
used function). Verify no `.knowledge/config.yaml` consumer first.
**Risk:** Low-Med (333 lines; confirm nothing dynamically loads it).
**Effort:** S. **Confidence:** High.

### 2C. Helpers that LOOK dead but are NOT (keep — flagged to prevent false positives)
The following have **0 `.py` importers** but ARE live via documented skill/agent
code blocks (the Python-in-markdown execution pattern) — do **not** drop:
- `gdoc_narrative_parser.py` (755 ln) — invoked in `export/skill.md:133`.
- `gdoc_builder.py` (752 ln) — invoked in `export/skill.md:134` (and 1 test).
- `marp_export.py` (251 ln) — invoked in `run-pipeline/skill.md`.
- `marp_linter.py` (377 ln) — invoked in `run-pipeline/skill.md` + `agents/visual-design-critic.md`.
- `deck_parser.py` (217 ln) — referenced by `slide-transform`, `deck-critique`,
  `deck-rescue` skills + `agents/presentation-doctor.md` (as optional fallback).
- `forecast_helpers.py` (586 ln) — `agents/overtime-trend.md:225` imports `detect_seasonality`.
- `deep_profiler.py` (843 ln) — invoked in `data-profiling/skill.md`.
- `postgres_helpers.py` — invoked in `setup-dev-context/skill.md`, `scripts/setup_postgres.sh`.
- `reliability_stats.py` (128 ln) — CLI tool, `python3 helpers/reliability_stats.py`
  per `reliability/SKILL.md:44`. (NEW since round-1; not deprecated.)

These are tied to **Area 3** features (gdoc/marp/notion). If a feature is dropped,
its helpers become droppable too — but on their own they are live.

**Honest uncertainty:** I did not execute the skills, so "live via code block" assumes
the documented procedure runs. If a feature is never actually invoked in practice,
several of these large files (gdoc pair = 1,507 ln; marp pair = 628 ln) are dead
weight — see Area 3.

---

## Area 3 — Droppable Features (flag for human; don't assume)

### 3A. Google Workspace export stack (MED — human decision)
**What:** `google-doc-export` (472 ln) + `google-slides-export` (458 ln) +
`chart-to-drive` (176 ln) + `auth-preflight` (Google MCP) skills, plus
`gdoc_builder.py` (752), `gdoc_narrative_parser.py` (755), `google_auth_helpers.py`
(253, already orphaned per 2A). ~2,600 lines of helper+skill for Google Docs/Slides/Drive.
**Evidence:** All require a Google Workspace MCP server configured in `.mcp.json`.
Heavy integration that may be out of scope for "a focused product analyst" OSS toolkit.
But: it IS wired (export dispatcher delegates to it; CLAUDE.md steps 16b/16c document it).
**Recommendation:** KEEP if Google export is a headline feature; otherwise this is the
single largest "scope-narrowing" lever (~2.6k lines + 3 skills). FLAG for human —
do not auto-drop. Marp PDF export (`marp_export`/`marp_linter`) is the local-first
alternative and should stay regardless. **Risk:** Med (user-facing feature).
**Effort:** L if dropped. **Confidence:** Med (that it's a *candidate*, not that it should go).

### 3B. Notion export/ingest stack (MED — human decision)
**What:** `notion-export` (201 ln), `notion-ingest`, `setup-notion` (135 ln) skills.
**Evidence:** Requires Notion MCP. Same scope question as Google. Wired via export
dispatcher. **Recommendation:** Same as 3A — FLAG for human; keep-or-cut as a unit
with the Google stack based on whether external-workspace integrations are in OSS scope.
**Risk:** Med. **Effort:** M. **Confidence:** Med.

### 3C. Community / course skills (HIGH — likely drop for OSS)
**What:** `kickoff` and `show-off` skills.
**Evidence:** `kickoff/skill.md:4,12` "Introduce yourself to the **AI Analyst Lab
community** on Slack"; `kickoff/skill.md:43` hardcodes OAuth domain
`slack-auth.ai-analyst-lab.workers.dev`; `show-off/skill.md:4,13` "Share with the
**AI Analyst Lab community**" → posts to `#show-and-tell`. These are cohort/course
community features with a hardcoded private domain that will break for any external
user. (`show-off-linkedin` already removed from disk.)
**Recommendation:** DROP for open-source (or gate behind opt-in config). They are
course-community-specific, not product-analyst functionality.
**Risk:** Low (course-only). **Effort:** S. **Confidence:** High (as a candidate).

### 3D. `skill-creator` + eval-viewer (LOW — likely keep, but note size)
**What:** `skill-creator/` ships an `eval-viewer/viewer.html` (1,325 ln) and
`generate_review.py` (471 ln) + an `assets/eval_review.html`.
**Evidence:** Meta-tooling for authoring skills; not product-analyst runtime. Large
HTML artifacts tracked. **Recommendation:** KEEP if you want users authoring skills;
otherwise a candidate to move out of the shipped product. FLAG. **Confidence:** Low.

---

## Area 4 — Stale Course / Naming Content

### 4A. CLAUDE.md skill table ↔ disk MISMATCH (HIGH — fix)
**What:** CLAUDE.md's "Your Skills" table lists skills that **do not exist on disk**,
and omits skills that **do**.
**Evidence:**
- Listed in CLAUDE.md, NOT on disk: **Demo** (`/demo`), **Certificate**
  (`/certificate`), **First-Run Welcome**, **Show Off LinkedIn**. Confirmed absent:
  `ls .claude/skills/{certificate,first-run-welcome,show-off-linkedin}` → "No such
  file or directory". `v3-merge-plan.md:51-52` documents these as CUT.
- On disk, NOT in CLAUDE.md table: **`teach`**, **`north-star`**, **`skill-creator`**
  (all three dirs exist).
- CLAUDE.md Default Workflow + Quick Start still reference the Demo and Certificate flows.
**Recommendation:** Sync CLAUDE.md table to disk: remove the 4 phantom rows, add the
3 missing rows. **Risk:** Low (docs). **Effort:** S. **Confidence:** High.

### 4B. Dangling references to removed skills (MED — fix)
**What:** Other files still point at removed skills.
**Evidence:** `connect-data/skill.md:14` references "First-Run Welcome";
`.knowledge/README.md:118` references "the First-Run Welcome skill takes over."
**Recommendation:** Re-point to the live onboarding (`setup`/`connect-data`).
**Risk:** Low. **Effort:** S. **Confidence:** High.

### 4C. "AI Analyst Plus" stale naming (MED — fix, mid-rename)
**What:** Project is mid-rename to "AI Analyst"; ~16 "AI Analyst Plus" references remain.
**Evidence:** `README.md:1` title; `README.md:30-31` clone URL
`github.com/ai-analyst-lab/ai-analyst-plus.git`; `CLAUDE.md:9`; setup guides
(`POSTGRES_SETUP_GUIDE.md:3`, `SETUP_SNOWFLAKE.md:3`, `SNOWFLAKE_QUICK_REFERENCE.md:1`);
`scripts/setup_postgres.sh:13`; `scripts/validate_snowflake_setup.py:264`;
`config_helpers.py:2` docstring. `v3-merge-plan.md:114` already lists this as a TODO.
**Recommendation:** Global rename pass (verify pyproject already done). **Risk:** Low.
**Effort:** M (mechanical, many files). **Confidence:** High.

### 4D. Course/"Builders course"/student language in helper docs (MED — fix)
**What:** `helpers/chart_style_guide.md` (692 ln) self-describes as the visual guide
for a course.
**Evidence:** `chart_style_guide.md:3` "Internal reference for all **AI Analytics for
Builders course** visuals"; `:10` "Every chart in **this course**"; `:542,:677`
"banned from all **course materials**"; `agents/root-cause-investigator.md:236`
"from **the course framework**". Plus scattered "student" wording in helper docstrings
and `.gitignore:4` "student-generated".
**Recommendation:** Generalize "course/student" → "this toolkit/analyst". Cosmetic but
visible to OSS users. **Risk:** Low. **Effort:** S-M. **Confidence:** High.

### 4E. NovaMart / week / demo references — mostly already clean (LOW — no action)
**Evidence:** NovaMart traces are confined to `docs/internal/*` cleanup plans and one
intentional anti-regression test (`tests/test_data_helpers_v2.py:100`
`test_no_novamart_references`). "Week 1/2/4" hits are generic examples
(`forecast/skill.md:84`, `templates/marp_components.md:341`), not curriculum.
`data-generation/` and `agents/demo-breakout.md` already removed.
**Recommendation:** No action (verdict: already clean). **Confidence:** High.

---

## Area 5 — Large / Vestigial Tracked Files

### 5A. `docs/hawaii_root_cause_deck.pdf` — 1.4 MB one-off output (HIGH — drop)
**What:** A 1.4 MB / 6,029-line tracked PDF, the single largest tracked file.
**Evidence:** It's a demo deck output. `.gitignore:92` **force-adds** it
(`!docs/hawaii_root_cause_deck.pdf`) — i.e. someone deliberately un-ignored a
build artifact. "hawaii" otherwise appears only as a `dataset_name` *example* in
`run-pipeline/skill.md:63`. Nothing references the PDF as documentation.
**Recommendation:** DROP from tracking (remove the `.gitignore` force-add line + untrack).
If a sample deck is wanted in the repo, keep a small one, not a 1.4 MB binary.
**Risk:** Low. **Effort:** S. **Confidence:** High.

### 5B. `helpers/examples/before_after_summary.png` — 836 KB, unreferenced (MED — drop)
**What:** 836 KB PNG (2,640 "lines" by wc — the largest image).
**Evidence:** The 8 other `examples/*.png` ARE used in `chart_style_guide.md:565-568`
(the before/after table). `before_after_summary.png` is **NOT** referenced in that
table or anywhere (`grep -rln before_after_summary` → no hits outside the file).
**Recommendation:** DROP — orphaned image, not embedded in any doc.
**Risk:** Low. **Effort:** S. **Confidence:** Med-High.

### 5C. `skill-creator` eval HTML artifacts (LOW — note)
**What:** `eval-viewer/viewer.html` (1,325 ln) + `assets/eval_review.html`. Large
tracked HTML for skill-authoring meta-tooling. See 3D. **Recommendation:** keep with
skill-creator or move out of shipped product. **Confidence:** Low.

### 5D. `tests/fixtures/conversion_test.docx` — 72 KB (LOW — keep)
**Evidence:** A test fixture; presumably used by gdoc/docx tests. **Keep** unless its
test is removed. **Confidence:** Med (didn't confirm the consuming test).

---

## Prioritized Table (highest-confidence, lowest-risk first)

| # | Candidate | Area | Action | Confidence | Risk | Effort |
|---|-----------|------|--------|-----------|------|--------|
| 1 | `helpers/google_auth_helpers.py` (253 ln, zero refs) | 2A | DROP | High | Low | S |
| 2 | `docs/hawaii_root_cause_deck.pdf` (1.4 MB, force-tracked) | 5A | DROP + remove `.gitignore:92` | High | Low | S |
| 3 | CLAUDE.md skill table ↔ disk mismatch (4 phantom, 3 missing) | 4A | SYNC | High | Low | S |
| 4 | Dangling "First-Run Welcome" refs (connect-data, README) | 4B | RE-POINT | High | Low | S |
| 5 | `helpers/examples/before_after_summary.png` (836 KB, unref) | 5B | DROP | Med-High | Low | S |
| 6 | `helpers/config_helpers.py` (333 ln, only neg-ref) | 2B | DROP (verify no `.knowledge/config.yaml`) | High | Low-Med | S |
| 7 | "AI Analyst Plus" stale naming (~16 refs) | 4C | RENAME | High | Low | M |
| 8 | "Builders course"/student language in chart_style_guide etc | 4D | GENERALIZE | High | Low | S-M |
| 9 | `kickoff` + `show-off` community skills (hardcoded Lab domain) | 3C | DROP/gate for OSS | High* | Low | S |
| 10 | analysis-design vs analysis-design-spec trigger overlap | 1B | TIGHTEN descriptions | Med-High | Low | S |
| 11 | export dispatcher duplicating gdoc/notion procedure | 1A | SLIM to pointers | Med | Low-Med | M |
| 12 | data-inspection cluster trigger overlap (6 skills) | 1E | DE-OVERLAP descriptions | Med | Low | M |
| 13 | Google Workspace export stack (~2.6k ln) | 3A | KEEP-or-CUT as unit (human) | Med | Med | L |
| 14 | Notion stack (export/ingest/setup) | 3B | KEEP-or-CUT as unit (human) | Med | Med | M |
| 15 | skill-creator eval HTML artifacts | 3D/5C | move out of shipped product? | Low | Low | M |

\* Confidence is "high that it's a candidate"; the keep/cut call is the human's.

**Honest uncertainties:**
(a) Helpers reached only via Python-in-markdown code blocks (gdoc/marp/deep_profiler/
forecast) are live ONLY if those skills actually run as documented — I did not execute
them. If a feature (Area 3) is cut, re-check its helpers for drop.
(b) `config_helpers.py` — I confirmed zero `.py` importers and only a negative doc
reference, but did not grep for a dynamic/`importlib` loader or a `.knowledge/config.yaml`
consumer; do that before deleting.
(c) The skill *merge* items (1A, 1E, 3A, 3B) are description/prose risk and feature-scope
calls — flagged for human decision, not auto-merge.
(d) I did not line-by-line diff the export dispatcher vs the standalone export skills,
so confirm no unique step lives only in the dispatcher before slimming it.
