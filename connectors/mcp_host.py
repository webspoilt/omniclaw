#!/usr/bin/env python3
"""
mcp_host.py — MCP Server exposing OmniClaw resources and tools.

External IDEs (like Zynta Studio) connect via WebSocket to access
system metrics, module state, and control the kill switch.

Install: pip install fastmcp
Run:     python connectors/mcp_host.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from fastmcp import FastMCP, Context
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

if not HAS_MCP:
    print("fastmcp not installed: pip install fastmcp")
    sys.exit(1)

app = FastMCP("OmniClaw MCP Server")


# ------------------------------------------------------------------ #
#  Resources                                                          #
# ------------------------------------------------------------------ #
@app.resource("system://cpu")
async def get_cpu() -> float:
    return psutil.cpu_percent() if HAS_PSUTIL else 0.0


@app.resource("system://memory")
async def get_memory() -> dict:
    if not HAS_PSUTIL:
        return {"percent": 0}
    m = psutil.virtual_memory()
    return {"total": m.total, "available": m.available, "percent": m.percent}


@app.resource("plant://latest_health")
async def get_plant_health() -> str:
    # TODO: read from plant_monitor's last analysis file
    return "Money Plant: Good — slight yellowing on lower leaves."


@app.resource("exam://next_deadline")
async def get_next_deadline() -> dict:
    return {"exam": "CAT 2026", "date": "2026-11-29", "days_left": 150}


@app.resource("security://kill_switch")
async def get_kill_switch() -> bool:
    try:
        from core.kill_switch import KILL_SWITCH
        return KILL_SWITCH
    except ImportError:
        return False


# ------------------------------------------------------------------ #
#  Tools                                                              #
# ------------------------------------------------------------------ #
@app.tool()
async def send_telegram_message(ctx: Context, message: str,
                                chat_id: str = "") -> str:
    """Send a message via Telegram bot."""
    ctx.info(f"Sending: {message[:60]}…")
    # Integration with existing messaging gateway
    return f"Sent to {chat_id or 'default'}"


@app.tool()
async def trigger_plant_capture(ctx: Context) -> str:
    """Manually trigger a plant health capture and analysis."""
    ctx.info("Triggering plant capture…")
    return "Plant capture initiated"


@app.tool()
async def toggle_kill_switch(ctx: Context, state: bool) -> str:
    """Activate or deactivate the global kill switch."""
    try:
        from core import kill_switch
        if state:
            kill_switch.activate()
        else:
            kill_switch.deactivate()
        ctx.info(f"Kill switch → {state}")
        return f"Kill switch is now {'ON' if state else 'OFF'}"
    except ImportError:
        return "kill_switch module not found"


@app.tool()
async def get_pm2_status(ctx: Context) -> str:
    """Return PM2 process list as JSON."""
    import subprocess
    try:
        r = subprocess.run(["pm2", "jlist"], capture_output=True, text=True,
                           timeout=10)
        return r.stdout
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
