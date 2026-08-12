from __future__ import annotations

import re
import time

import duckdb
import pandas as pd

from web.config import WEB_DUCKDB_PATH, NOVAMART_DUCKDB_PATH

_FORBIDDEN = re.compile(
    r"\b(DROP|ALTER|DELETE|UPDATE|INSERT|CREATE|TRUNCATE|GRANT|REVOKE|EXEC)\b",
    re.IGNORECASE,
)


def _resolve_db(source: str):
    if source == "novamart_demo":
        return NOVAMART_DUCKDB_PATH
    return WEB_DUCKDB_PATH


def execute_sql(sql: str, source: str = "upload", max_rows: int = 1000) -> dict:
    sql = sql.strip().rstrip(";")

    if _FORBIDDEN.search(sql):
        return {
            "error": True,
            "message": "Only SELECT and WITH (CTE) queries are allowed.",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_ms": 0,
        }

    db_path = _resolve_db(source)
    if not db_path.exists():
        return {
            "error": True,
            "message": f"Database not found at {db_path}",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_ms": 0,
        }

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        t0 = time.perf_counter()
        df = conn.execute(sql).fetchdf()
        elapsed = (time.perf_counter() - t0) * 1000

        total_rows = len(df)
        df_display = df.head(max_rows)

        columns = df_display.columns.tolist()
        rows = []
        for _, row in df_display.iterrows():
            row_vals = []
            for v in row:
                if pd.isna(v):
                    row_vals.append(None)
                elif hasattr(v, "isoformat"):
                    row_vals.append(v.isoformat())
                elif hasattr(v, "item"):
                    row_vals.append(v.item())
                else:
                    row_vals.append(v)
            rows.append(row_vals)

        return {
            "error": False,
            "columns": columns,
            "rows": rows,
            "row_count": total_rows,
            "execution_ms": round(elapsed, 1),
        }
    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_ms": 0,
        }
    finally:
        conn.close()


def get_schema_context(source: str = "upload") -> str:
    db_path = _resolve_db(source)
    if not db_path.exists():
        return "No database available."

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
        lines = []
        for tbl in tables:
            cols = conn.execute(f"DESCRIBE {tbl}").fetchall()
            row_count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            col_defs = ", ".join(f"{c[0]} {c[1]}" for c in cols)
            lines.append(f"  {tbl} ({row_count:,} rows): {col_defs}")
        return "Tables:\n" + "\n".join(lines)
    finally:
        conn.close()
