from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

_anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
_openai_key = os.environ.get("OPENAI_API_KEY", "")

# ── Tool definitions (provider-neutral shape, converted at call time) ──

_TOOLS_CORE = [
    {
        "name": "execute_sql",
        "description": (
            "Execute a read-only SQL query against the active DuckDB dataset. "
            "Only SELECT and WITH (CTE) statements are allowed. "
            "Returns columns, rows (max 1000), row_count, and execution_ms. "
            "Use DuckDB SQL dialect."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to execute (SELECT or WITH only)",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "generate_chart",
        "description": (
            "Generate a chart from query results. Provide the data as column arrays, "
            "specify chart type (bar, line, grouped_bar), x/y columns, and a title. "
            "Returns the chart filename which can be served at /api/charts/{filename}."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "grouped_bar"],
                    "description": "Type of chart to generate",
                },
                "data": {
                    "type": "object",
                    "description": "Data as {column_name: [values...]} dict",
                },
                "x_col": {"type": "string", "description": "Column name for x-axis"},
                "y_col": {"type": "string", "description": "Column name for y-axis"},
                "title": {"type": "string", "description": "Chart title (action-oriented headline)"},
                "highlight": {
                    "type": "string",
                    "description": "Category value to highlight (for bar charts)",
                },
                "group_col": {
                    "type": "string",
                    "description": "Grouping column (for grouped_bar only)",
                },
            },
            "required": ["chart_type", "data", "x_col", "y_col"],
        },
    },
]


def _anthropic_tools():
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in _TOOLS_CORE
    ]


def _openai_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in _TOOLS_CORE
    ]


# ── Session history ──

_sessions: dict[str, list[dict]] = {}
MAX_HISTORY = 20


# ── Provider detection ──

def _detect_provider() -> str | None:
    if _anthropic_key:
        return "anthropic"
    if _openai_key:
        return "openai"
    return None


def is_configured() -> bool:
    return _detect_provider() is not None


def _provider_label() -> str:
    p = _detect_provider()
    if p == "anthropic":
        return "Claude"
    if p == "openai":
        return "GPT"
    return "LLM"


# ── System prompt (shared) ──

def build_system_prompt(schema_context: str) -> str:
    return f"""You are an AI data analyst working with a DuckDB database. Your job is to answer analytical questions about the data by writing and executing SQL queries, and optionally generating charts.

## Available Data
{schema_context}

## Instructions
1. When the user asks a question about data, write a SQL query to answer it using the execute_sql tool.
2. After getting query results, provide a clear, concise answer explaining what the data shows.
3. When a visual would help (comparisons, trends, distributions), use generate_chart to create a chart.
4. For chart titles, use action-oriented headlines that state the key finding (e.g., "Mobile drives 60% of traffic" not "Traffic by device").
5. Use DuckDB SQL syntax. Table and column names are case-sensitive — use them exactly as shown in the schema.
6. Always cite specific numbers from the results.
7. If the data cannot answer the question, say so clearly.

## Response Format
After executing queries and/or generating charts, provide your analysis as plain text. Be concise — lead with the key finding, then supporting details."""


# ── Main chat function ──

def chat(
    message: str,
    schema_context: str,
    session_id: str,
    tool_executor: callable,
) -> dict:
    provider = _detect_provider()
    if provider is None:
        return {
            "response_type": "error",
            "content": (
                "No LLM API key configured. Add one to your .env file:\n\n"
                "  ANTHROPIC_API_KEY=sk-ant-...   (for Claude)\n"
                "  OPENAI_API_KEY=sk-...          (for GPT)\n\n"
                "Then restart the server."
            ),
            "tool_results": [],
        }

    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]
    history.append({"role": "user", "content": message})

    if len(history) > MAX_HISTORY * 2:
        history[:] = history[-(MAX_HISTORY * 2):]

    if provider == "anthropic":
        return _chat_anthropic(history, schema_context, session_id, tool_executor)
    else:
        return _chat_openai(history, schema_context, session_id, tool_executor)


# ── Anthropic (Claude) implementation ──

def _chat_anthropic(
    history: list, schema_context: str, session_id: str, tool_executor: callable,
) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=_anthropic_key)
    system_prompt = build_system_prompt(schema_context)
    tool_results = []
    charts = []
    messages = list(history)

    for _ in range(10):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=_anthropic_tools(),
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_use_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result = tool_executor(block.name, block.input)
                    tool_results.append({
                        "tool": block.name,
                        "input": block.input,
                        "result": result,
                    })
                    if block.name == "generate_chart" and not result.get("error"):
                        charts.append(result.get("filename"))

                    tool_use_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    })

            messages.append({"role": "user", "content": tool_use_results})
            continue

        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        final_text = "\n".join(text_parts)
        history.append({"role": "assistant", "content": final_text})

        return {
            "response_type": "analysis",
            "content": final_text,
            "tool_results": tool_results,
            "charts": charts,
        }

    return _timeout_result(tool_results, charts)


# ── OpenAI (GPT) implementation ──

def _chat_openai(
    history: list, schema_context: str, session_id: str, tool_executor: callable,
) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=_openai_key)
    system_prompt = build_system_prompt(schema_context)
    tool_results = []
    charts = []

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    for _ in range(10):
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=messages,
            tools=_openai_tools(),
            tool_choice="auto",
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            messages.append(choice.message)

            for tc in choice.message.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)

                result = tool_executor(fn_name, fn_args)
                tool_results.append({
                    "tool": fn_name,
                    "input": fn_args,
                    "result": result,
                })
                if fn_name == "generate_chart" and not result.get("error"):
                    charts.append(result.get("filename"))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })
            continue

        final_text = choice.message.content or ""
        history.append({"role": "assistant", "content": final_text})

        return {
            "response_type": "analysis",
            "content": final_text,
            "tool_results": tool_results,
            "charts": charts,
        }

    return _timeout_result(tool_results, charts)


def _timeout_result(tool_results, charts):
    return {
        "response_type": "error",
        "content": "Analysis exceeded maximum tool iterations.",
        "tool_results": tool_results,
        "charts": charts,
    }
