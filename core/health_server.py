#!/usr/bin/env python3
"""
health_server.py — Lightweight HTTP health check endpoint for OmniClaw.

Resolves GitHub Issue #19: Add health check endpoint and process watchdog.

Exposes GET /health returning JSON with system status, uptime, and
module health summaries. Uses aiohttp if available, otherwise falls
back to a minimal asyncio socket server.

Usage:
    python -m core.health_server            # standalone
    from core.health_server import HealthServer   # embed in main
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("OmniClaw.HealthServer")

_START_TIME = time.time()


def _collect_health() -> Dict[str, Any]:
    """Collect health data from available modules."""
    health: Dict[str, Any] = {
        "status": "ok",
        "uptime_s": round(time.time() - _START_TIME, 1),
        "modules": {},
    }

    # System metrics (psutil optional)
    try:
        import psutil
        health["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except ImportError:
        health["system"] = {"error": "psutil not installed"}

    # Kill switch state
    try:
        from core.kill_switch import KILL_SWITCH
        health["modules"]["kill_switch"] = {"active": KILL_SWITCH}
    except Exception as e:
        health["modules"]["kill_switch"] = {"error": str(e)}

    # Scheduler status
    try:
        from core.scheduler.cron import CronScheduler
        cs = CronScheduler()
        health["modules"]["cron_scheduler"] = cs.get_status()
    except Exception as e:
        health["modules"]["cron_scheduler"] = {"error": str(e)}

    # Heartbeat status
    try:
        from core.scheduler.heartbeat import HeartbeatService
        hs = HeartbeatService(workspace=".", enabled=False)
        health["modules"]["heartbeat"] = hs.get_status()
    except Exception as e:
        health["modules"]["heartbeat"] = {"error": str(e)}

    # SkillLoader status
    try:
        from core.skills.loader import SkillLoader
        sl = SkillLoader()
        health["modules"]["skill_loader"] = sl.get_status()
    except Exception as e:
        health["modules"]["skill_loader"] = {"error": str(e)}

    return health


# ------------------------------------------------------------------ #
#  aiohttp server (preferred)                                         #
# ------------------------------------------------------------------ #

try:
    from aiohttp import web as _aiohttp_web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


async def _aiohttp_handler(request) -> Any:
    data = _collect_health()
    return _aiohttp_web.Response(
        content_type="application/json",
        text=json.dumps(data, indent=2),
    )


async def _run_aiohttp(host: str, port: int) -> None:
    app = _aiohttp_web.Application()
    app.router.add_get("/health", _aiohttp_handler)
    app.router.add_get("/", _aiohttp_handler)
    runner = _aiohttp_web.AppRunner(app)
    await runner.setup()
    site = _aiohttp_web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Health server (aiohttp) listening on http://{host}:{port}/health")
    # Run forever
    while True:
        await asyncio.sleep(3600)


# ------------------------------------------------------------------ #
#  Fallback: minimal asyncio socket server                           #
# ------------------------------------------------------------------ #

async def _handle_connection(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    try:
        await reader.readuntil(b"\r\n\r\n")
        data = _collect_health()
        body = json.dumps(data, indent=2)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{body}"
        )
        writer.write(response.encode())
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()


async def _run_socket(host: str, port: int) -> None:
    server = await asyncio.start_server(_handle_connection, host, port)
    logger.info(f"Health server (socket) listening on http://{host}:{port}/health")
    async with server:
        await server.serve_forever()


# ------------------------------------------------------------------ #
#  Public API                                                         #
# ------------------------------------------------------------------ #

class HealthServer:
    """Lightweight HTTP health check server (Issue #19).

    Starts an async HTTP server that exposes GET /health returning
    JSON with system status, uptime, and module health summaries.

    Example::

        server = HealthServer(host="0.0.0.0", port=8080)
        await server.start()   # non-blocking; runs as asyncio background task
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the health server as a background asyncio task."""
        if HAS_AIOHTTP:
            coro = _run_aiohttp(self.host, self.port)
        else:
            logger.warning(
                "aiohttp not installed — using minimal socket health server. "
                "Install with: pip install aiohttp"
            )
            coro = _run_socket(self.host, self.port)

        self._task = asyncio.create_task(coro)
        logger.info(f"HealthServer started on http://{self.host}:{self.port}/health")

    def stop(self) -> None:
        """Cancel the background health server task."""
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("HealthServer stopped")


# ------------------------------------------------------------------ #
#  Standalone entry point                                             #
# ------------------------------------------------------------------ #

async def _main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="OmniClaw Health Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if HAS_AIOHTTP:
        await _run_aiohttp(args.host, args.port)
    else:
        await _run_socket(args.host, args.port)


if __name__ == "__main__":
    asyncio.run(_main())
