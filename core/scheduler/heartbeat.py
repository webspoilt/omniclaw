"""
HeartbeatService — Periodic agent wake-up driven by HEARTBEAT.md.

Ported from Nanobot's heartbeat/service.py.
Phase 1 (decision): reads HEARTBEAT.md and asks LLM via tool-call whether there are tasks.
Phase 2 (execution): runs tasks through agent loop only when Phase 1 returns 'run'.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger("OmniClaw.Scheduler.Heartbeat")

# Tool schema for the heartbeat decision
_HEARTBEAT_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "heartbeat",
            "description": "Report heartbeat decision after reviewing tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["skip", "run"],
                        "description": "skip = nothing to do, run = has active tasks",
                    },
                    "tasks": {
                        "type": "string",
                        "description": "Natural-language summary of active tasks (required for run)",
                    },
                },
                "required": ["action"],
            },
        },
    }
]


class HeartbeatService:
    """
    Periodic heartbeat service that wakes the agent to check for tasks.

    Reads HEARTBEAT.md from workspace and uses LLM tool-call to decide
    whether there are active tasks. Only executes when decision is 'run'.
    """

    def __init__(
        self,
        workspace: str | Path,
        llm_callback: Optional[Callable] = None,
        on_execute: Optional[Callable[[str], Coroutine[Any, Any, str]]] = None,
        on_notify: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
        interval_s: int = 30 * 60,
        enabled: bool = True,
    ):
        """
        Initialize HeartbeatService.

        Args:
            workspace: Path to workspace directory
            llm_callback: Async function to call LLM with messages and tools
            on_execute: Async callback to execute tasks through agent loop
            on_notify: Async callback to deliver results to user
            interval_s: Heartbeat interval in seconds (default 30 min)
            enabled: Whether heartbeat is enabled
        """
        self.workspace = Path(workspace)
        self.llm_callback = llm_callback
        self.on_execute = on_execute
        self.on_notify = on_notify
        self.interval_s = interval_s
        self.enabled = enabled
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tick_count = 0
        self._last_action = "none"

    @property
    def heartbeat_file(self) -> Path:
        """Path to HEARTBEAT.md."""
        return self.workspace / "HEARTBEAT.md"

    def _read_heartbeat_file(self) -> Optional[str]:
        """Read HEARTBEAT.md content."""
        if self.heartbeat_file.exists():
            try:
                return self.heartbeat_file.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    async def _decide(self, content: str) -> tuple[str, str]:
        """
        Phase 1: ask LLM to decide skip/run via virtual tool call.

        Returns:
            (action, tasks) where action is 'skip' or 'run'
        """
        if not self.llm_callback:
            # Fallback: simple keyword detection
            keywords = ["TODO", "TASK", "ACTIVE", "PENDING", "IN PROGRESS"]
            for kw in keywords:
                if kw.lower() in content.lower():
                    return "run", content[:500]
            return "skip", ""

        try:
            response = await self.llm_callback(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a heartbeat agent. Call the heartbeat tool to report your decision.",
                    },
                    {
                        "role": "user",
                        "content": (
                            "Review the following HEARTBEAT.md and decide whether there are active tasks.\n\n"
                            f"{content}"
                        ),
                    },
                ],
                tools=_HEARTBEAT_TOOL,
            )

            if hasattr(response, "has_tool_calls") and response.has_tool_calls:
                args = response.tool_calls[0].arguments
                return args.get("action", "skip"), args.get("tasks", "")
            return "skip", ""
        except Exception as e:
            logger.error(f"Heartbeat LLM decision failed: {e}")
            return "skip", ""

    async def start(self) -> None:
        """Start the heartbeat service."""
        if not self.enabled:
            logger.info("Heartbeat disabled")
            return
        if self._running:
            logger.warning("Heartbeat already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Heartbeat started (every {self.interval_s}s)")

    def stop(self) -> None:
        """Stop the heartbeat service."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_s)
                if self._running:
                    await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _tick(self) -> None:
        """Execute a single heartbeat tick."""
        self._tick_count += 1
        content = self._read_heartbeat_file()
        if not content:
            logger.debug("Heartbeat: HEARTBEAT.md missing or empty")
            self._last_action = "skip"
            return

        logger.info("Heartbeat: checking for tasks...")

        try:
            action, tasks = await self._decide(content)
            self._last_action = action

            if action != "run":
                logger.info("Heartbeat: OK (nothing to report)")
                return

            logger.info("Heartbeat: tasks found, executing...")
            if self.on_execute:
                response = await self.on_execute(tasks)
                if response and self.on_notify:
                    logger.info("Heartbeat: completed, delivering response")
                    await self.on_notify(f"🫀 **Heartbeat Report**\n\n{response}")
        except Exception:
            logger.exception("Heartbeat execution failed")

    async def trigger_now(self) -> Optional[str]:
        """Manually trigger a heartbeat check."""
        content = self._read_heartbeat_file()
        if not content:
            return None
        action, tasks = await self._decide(content)
        if action != "run" or not self.on_execute:
            return None
        return await self.on_execute(tasks)

    def get_status(self) -> dict:
        """Get heartbeat status."""
        return {
            "enabled": self.enabled,
            "running": self._running,
            "interval_s": self.interval_s,
            "tick_count": self._tick_count,
            "last_action": self._last_action,
            "heartbeat_file": str(self.heartbeat_file),
            "heartbeat_file_exists": self.heartbeat_file.exists(),
        }
