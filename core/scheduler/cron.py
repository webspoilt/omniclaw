"""
CronScheduler — Persistent cron scheduler with SQLite storage.

Ported from NanoClaw's cron/scheduler.py.
Jobs survive restarts. Supports cron expressions and simple interval-based scheduling.
"""

from __future__ import annotations

import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Coroutine, Any, Optional

logger = logging.getLogger("OmniClaw.Scheduler.Cron")


class CronScheduler:
    """Persistent cron jobs stored in SQLite."""

    def __init__(
        self,
        db_path: str | Path = "./data/omniclaw.db",
        on_execute: Optional[Callable[[str], Coroutine[Any, Any, str]]] = None,
        on_notify: Optional[Callable[[str, str], Coroutine[Any, Any, None]]] = None,
    ):
        """
        Initialize CronScheduler.

        Args:
            db_path: Path to SQLite database
            on_execute: Async callback to execute a job's message (returns response)
            on_notify: Async callback to notify user (job_name, response)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.on_execute = on_execute
        self.on_notify = on_notify
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._init_db()

    def _init_db(self):
        """Create the cron_jobs table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cron_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                cron_expr TEXT,
                interval_seconds INTEGER,
                channel TEXT DEFAULT 'telegram',
                enabled INTEGER DEFAULT 1,
                last_run TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()
        logger.debug("CronScheduler DB initialized")

    async def start(self) -> None:
        """Start checking jobs every 60 seconds."""
        self.running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("CronScheduler started")

    async def _loop(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_and_run()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)

    async def _check_and_run(self) -> None:
        """Check all jobs, run those that are due."""
        jobs = await self._get_enabled_jobs()
        now = datetime.utcnow()

        for job in jobs:
            should_run = False

            if job["cron_expr"]:
                try:
                    from croniter import croniter

                    last_run = (
                        datetime.fromisoformat(job["last_run"])
                        if job["last_run"]
                        else now - timedelta(days=1)
                    )
                    cron = croniter(job["cron_expr"], last_run)
                    next_run = cron.get_next(datetime)
                    should_run = next_run <= now
                except ImportError:
                    logger.warning("croniter not installed — skipping cron expression jobs. Install with: pip install croniter")
                except Exception as e:
                    logger.error(f"Cron parse error for job {job['id']}: {e}")

            elif job["interval_seconds"]:
                if job["last_run"]:
                    last = datetime.fromisoformat(job["last_run"])
                    should_run = (now - last).total_seconds() >= job["interval_seconds"]
                else:
                    should_run = True

            if should_run:
                asyncio.create_task(self._execute_job(job))
                await self._update_last_run(job["id"])

    async def _execute_job(self, job: dict) -> None:
        """Run a cron job through the agent loop."""
        try:
            # Check for prompt injection in job message
            try:
                from core.security.prompt_guard import PromptGuard
                guard = PromptGuard()
                detected, matched = guard.check_injection(job["message"])
                if detected:
                    logger.warning(f"Cron job '{job['name']}' message contains injection: {matched}")
                    return
            except ImportError:
                pass

            if self.on_execute:
                response = await self.on_execute(job["message"])
                if response and self.on_notify:
                    await self.on_notify(
                        f"**⏰ {job['name']}**\n\n{response}",
                        job.get("channel", "telegram"),
                    )
        except Exception as e:
            logger.error(f"Cron job '{job['name']}' failed: {e}")

    async def _get_enabled_jobs(self) -> list[dict]:
        """Get all enabled jobs."""
        def _query() -> list[dict]:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM cron_jobs WHERE enabled = 1")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        return await asyncio.to_thread(_query)

    async def _update_last_run(self, job_id: int) -> None:
        """Update job's last_run timestamp."""
        def _update() -> None:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE cron_jobs SET last_run = datetime('now') WHERE id = ?",
                (job_id,),
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(_update)

    async def add_job(
        self,
        name: str,
        message: str,
        cron_expr: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        channel: str = "telegram",
    ) -> int:
        """
        Add a new cron job.

        Args:
            name: Job name
            message: Message/prompt to send to agent
            cron_expr: Cron expression (e.g., '0 9 * * *')
            interval_seconds: Interval in seconds (alternative to cron_expr)
            channel: Target notification channel

        Returns:
            Job ID
        """
        def _insert() -> int:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                """
                INSERT INTO cron_jobs (name, message, cron_expr, interval_seconds, channel)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, message, cron_expr, interval_seconds, channel),
            )
            conn.commit()
            job_id = cursor.lastrowid
            conn.close()
            return job_id or 0

        job_id = await asyncio.to_thread(_insert)
        logger.info(f"Added cron job #{job_id}: {name}")
        return job_id

    async def remove_job(self, job_id: int) -> None:
        """Remove a cron job."""
        def _delete() -> None:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM cron_jobs WHERE id = ?", (job_id,))
            conn.commit()
            conn.close()

        await asyncio.to_thread(_delete)
        logger.info(f"Removed cron job #{job_id}")

    async def list_jobs(self) -> list[dict]:
        """List all cron jobs."""
        def _query() -> list[dict]:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM cron_jobs ORDER BY id")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        return await asyncio.to_thread(_query)

    async def toggle_job(self, job_id: int, enabled: bool) -> None:
        """Enable or disable a job."""
        def _update() -> None:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE cron_jobs SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, job_id),
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(_update)

    async def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def get_status(self) -> dict:
        """Get scheduler status."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c FROM cron_jobs").fetchone()["c"]
        enabled = conn.execute("SELECT COUNT(*) as c FROM cron_jobs WHERE enabled = 1").fetchone()["c"]
        conn.close()
        return {
            "running": self.running,
            "total_jobs": total,
            "enabled_jobs": enabled,
            "db_path": str(self.db_path),
        }
