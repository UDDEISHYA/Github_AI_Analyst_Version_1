from __future__ import annotations

import json
import re
import uuid

from web.services import llm_service, query_service, chart_service


def classify_question(message: str) -> int:
    msg = message.lower().strip()

    l1_patterns = [
        r"^how many\b",
        r"^how much\b",
        r"^what is the (average|mean|median|total|count|sum|min|max)\b",
        r"^what('s| is) the .{0,20} (rate|count|total|number)\b",
        r"^count\b",
    ]
    for pat in l1_patterns:
        if re.search(pat, msg):
            return 1

    l2_patterns = [
        r"\bcompare\b",
        r"\bby (device|channel|category|segment|region|country|platform)\b",
        r"\bbreakdown\b",
        r"\bsplit\b",
        r"\btop \d+\b",
        r"\bshow me .{0,30} by\b",
        r"\btrend\b",
        r"\bover time\b",
    ]
    for pat in l2_patterns:
        if re.search(pat, msg):
            return 2

    l4_patterns = [
        r"\binvestigat\w*\b",
        r"\broot cause\b",
        r"\bwhy did .+ (drop|decline|fall|decrease|spike|jump|increase)\b",
        r"\bsize the opportunity\b",
        r"\bdesign .+ (experiment|test|a\/b)\b",
        r"\bwhat caused\b",
        r"\bwhat's driving\b",
        r"\bdiagnos\w*\b",
    ]
    for pat in l4_patterns:
        if re.search(pat, msg):
            return 4

    l5_patterns = [
        r"\bfull pipeline\b",
        r"\brun.pipeline\b",
        r"\bbuild .+ deck\b",
        r"\bpresentation\b",
        r"\bend.to.end\b",
        r"\bboard.ready\b",
    ]
    for pat in l5_patterns:
        if re.search(pat, msg):
            return 5

    l3_patterns = [
        r"\bwhy\b",
        r"\banalyze\b",
        r"\banalysis\b",
        r"\bwhich .+ (has|have|is|are) the (high|low|best|worst)\b",
        r"\bwhat (factor|driver|variable)\b",
        r"\bsegment\b",
        r"\bfunnel\b",
        r"\bcohort\b",
        r"\bretention\b",
    ]
    for pat in l3_patterns:
        if re.search(pat, msg):
            return 3

    return 2


def handle_chat(message: str, source: str, session_id: str | None = None) -> dict:
    if not session_id:
        session_id = uuid.uuid4().hex

    if not llm_service.is_configured():
        return {
            "session_id": session_id,
            "blocks": [{
                "type": "error",
                "content": (
                    "No LLM API key configured. Add one to your .env file:\n\n"
                    "  ANTHROPIC_API_KEY=sk-ant-...   (for Claude)\n"
                    "  OPENAI_API_KEY=sk-...          (for GPT)\n\n"
                    "Then restart the server."
                ),
            }],
        }

    level = classify_question(message)

    schema_context = query_service.get_schema_context(source)

    if level >= 3:
        from web.services import pipeline_orchestrator
        run_id = pipeline_orchestrator.create_run(
            question=message,
            source=source,
            level=level,
            schema_context=schema_context,
        )
        return {
            "session_id": session_id,
            "pipeline": True,
            "run_id": run_id,
            "level": level,
            "plan": pipeline_orchestrator.LEVEL_TO_PLAN.get(level, "guided_analysis"),
            "agents": pipeline_orchestrator.get_run(run_id)["agents"],
            "blocks": [{
                "type": "text",
                "content": (
                    f"This is an L{level} question — launching the "
                    f"**{pipeline_orchestrator.LEVEL_TO_PLAN.get(level, 'guided_analysis').replace('_', ' ').title()}** "
                    f"pipeline with {len(pipeline_orchestrator.get_run(run_id)['agents'])} agents. "
                    f"Watch the sidebar for real-time progress."
                ),
            }],
        }

    result = llm_service.chat(
        message=message,
        schema_context=schema_context,
        session_id=session_id,
        tool_executor=lambda name, inp: _execute_tool(name, inp, source),
    )

    blocks = _build_response_blocks(result)

    return {
        "session_id": session_id,
        "blocks": blocks,
    }


def _execute_tool(tool_name: str, tool_input: dict, source: str) -> dict:
    if tool_name == "execute_sql":
        return query_service.execute_sql(tool_input["sql"], source)

    elif tool_name == "generate_chart":
        try:
            filename = chart_service.generate_chart_from_spec(
                chart_type=tool_input.get("chart_type", "bar"),
                data=tool_input["data"],
                x_col=tool_input["x_col"],
                y_col=tool_input["y_col"],
                title=tool_input.get("title"),
                highlight=tool_input.get("highlight"),
                group_col=tool_input.get("group_col"),
            )
            return {"error": False, "filename": filename}
        except Exception as e:
            return {"error": True, "message": str(e)}

    return {"error": True, "message": f"Unknown tool: {tool_name}"}


def _build_response_blocks(result: dict) -> list[dict]:
    blocks = []

    if result["response_type"] == "error":
        blocks.append({"type": "error", "content": result["content"]})
        return blocks

    for tr in result.get("tool_results", []):
        if tr["tool"] == "execute_sql" and not tr["result"].get("error"):
            r = tr["result"]
            if r["row_count"] > 0:
                blocks.append({
                    "type": "table",
                    "columns": r["columns"],
                    "rows": r["rows"],
                    "row_count": r["row_count"],
                    "execution_ms": r["execution_ms"],
                    "sql": tr["input"].get("sql", ""),
                })

        elif tr["tool"] == "generate_chart" and not tr["result"].get("error"):
            blocks.append({
                "type": "chart",
                "filename": tr["result"]["filename"],
                "title": tr["input"].get("title", ""),
            })

    if result.get("content"):
        blocks.append({
            "type": "text",
            "content": result["content"],
        })

    return blocks
