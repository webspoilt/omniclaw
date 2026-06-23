"""Create and manage structured long-term memory via SQLite and JSON knowledge bases."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from core.skills.registry import tool


MEMORY_DIR = Path(__file__).resolve().parent.parent / "data" / "agent_memory"


def _ensure_db(db_name: str) -> sqlite3.Connection:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(MEMORY_DIR / f"{db_name}.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    return conn


@tool(
    name="create_memory_table",
    description="Create a new SQLite table for structured long-term memory.",
    parameters={
        "table_name": {"type": "string", "description": "Table name (e.g. 'experiments', 'observations')"},
        "schema_sql": {"type": "string", "description": "Column definitions after CREATE TABLE, e.g. 'id INTEGER PRIMARY KEY, name TEXT, value REAL'"}
    },
    required=["table_name", "schema_sql"],
)
async def create_memory_table(table_name: str, schema_sql: str) -> str:
    conn = _ensure_db("agent_memory")
    try:
        conn.execute(f"CREATE TABLE IF NOT EXISTS [{table_name}] ({schema_sql})")
        conn.commit()
        return f"Table '{table_name}' ready"
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


@tool(
    name="store_knowledge",
    description="Store a key-value knowledge entry in the knowledge_json table.",
    parameters={
        "key": {"type": "string", "description": "Unique knowledge key"},
        "value": {"type": "string", "description": "Knowledge content (stringified JSON or text)"},
        "tags": {"type": "string", "description": "Comma-separated tags for grouping"},
    },
    required=["key", "value"],
)
async def store_knowledge(key: str, value: str, tags: Optional[str] = None) -> str:
    conn = _ensure_db("agent_memory")
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS knowledge (key TEXT PRIMARY KEY, value TEXT, tags TEXT, created_at REAL, updated_at REAL)"
        )
        now = __import__("time").time()
        conn.execute(
            "INSERT INTO knowledge (key, value, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, tags=excluded.tags, updated_at=excluded.updated_at",
            (key, value, tags or "", now, now),
        )
        conn.commit()
        return f"Stored knowledge: {key}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


@tool(
    name="query_memory",
    description="Query the SQLite memory database with a raw SQL SELECT.",
    parameters={
        "sql": {"type": "string", "description": "SELECT statement to execute"},
    },
    required=["sql"],
)
async def query_memory(sql: str) -> list[dict[str, Any]]:
    if not sql.strip().upper().startswith("SELECT"):
        return [{"error": "only SELECT queries allowed"}]
    conn = _ensure_db("agent_memory")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


@tool(
    name="save_json_knowledge_base",
    description="Write a JSON file to the agent memory directory for structured knowledge.",
    parameters={
        "filename": {"type": "string", "description": "Filename (e.g. 'observed_patterns.json')"},
        "data_json": {"type": "string", "description": "JSON-encodable data as a string"},
    },
    required=["filename", "data_json"],
)
async def save_json_knowledge_base(filename: str, data_json: str) -> str:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / filename
    try:
        data = json.loads(data_json)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return f"Saved {len(data_json)} bytes to {path}"
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON — {e}"


@tool(
    name="list_memory_tables",
    description="List all tables in the agent memory database with row counts.",
    parameters={},
)
async def list_memory_tables() -> list[dict[str, Any]]:
    conn = _ensure_db("agent_memory")
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = []
        for row in cursor.fetchall():
            name = row["name"]
            count = conn.execute(f"SELECT COUNT(*) as cnt FROM [{name}]").fetchone()["cnt"]
            tables.append({"name": name, "row_count": count})
        return tables
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        conn.close()
