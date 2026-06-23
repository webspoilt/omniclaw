"""
State Store – Unrestricted Local Persistence (Sealed Research VM)
Provides a simple SQLite-backed store for agent tasks, logs, and memory.
No authentication, no network dependency, full root access.
"""
import asyncio
import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/agent_state.db")


def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            inputs TEXT,
            outputs TEXT,
            worker_id TEXT
        );
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            ip_address TEXT NOT NULL,
            port INTEGER NOT NULL,
            active INTEGER DEFAULT 1,
            capabilities TEXT DEFAULT '[]',
            last_heartbeat TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            stdout TEXT,
            stderr TEXT,
            exit_code INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        );
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL,
            cpu_usage REAL NOT NULL,
            memory_usage REAL NOT NULL,
            gpu_temperature REAL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS agent_memory (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


async def main():
    print("State Store: Local SQLite initialized – unrestricted access.")
    init_db()
    # Keep the service alive so the agent can query it via the database file directly,
    # or via any future HTTP endpoint if you choose to add one later.
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
