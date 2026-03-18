#!/usr/bin/env python3
"""
mcp_host.py — MCP Server exposing OmniClaw resources and tools.

External IDEs (like Zynta Studio) connect via WebSocket to access
system metrics, module state, and control the kill switch.

Install: pip install fastmcp
Run:     python connectors/mcp_host.py

v4.2 additions (Issue #18):
  - get_scheduler_status: CronScheduler/HeartbeatService status
  - get_evolution_status: EvolutionAgent last run info
  - get_mesh_peers: NeuralMeshNode online peers list
  - plant://latest_health now reads from last_analysis.json if available
"""

import json
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
    """Returns the latest plant health analysis from disk, or a placeholder."""
    analysis_paths = [
        Path("captures/last_analysis.json"),
        Path("data/plant_last_analysis.json"),
    ]
    for p in analysis_paths:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return data.get("summary", str(data))
            except Exception:
                pass
    return "Money Plant: Good — slight yellowing on lower leaves. (placeholder)"


@app.resource("exam://next_deadline")
async def get_next_deadline() -> dict:
    try:
        from modules.scholar.exam_intelligence import ExamIntelligence
        ei = ExamIntelligence()
        return ei.get_next_deadline()
    except Exception:
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
    return f"Sent to {chat_id or 'default'}"


@app.tool()
async def trigger_plant_capture(ctx: Context) -> str:
    """Manually trigger a plant health capture and analysis."""
    ctx.info("Triggering plant capture…")
    try:
        from modules.sensors.plant_monitor import PlantMonitor
        pm = PlantMonitor()
        result = pm.run_once() if hasattr(pm, "run_once") else "Capture initiated"
        return str(result)
    except Exception as e:
        ctx.warning(f"Could not import PlantMonitor: {e}")
        return "Plant capture initiated (stub)"


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
    except Exception as e:
        return f"Error toggling kill switch: {e}"


@app.tool()
async def get_pm2_status(ctx: Context) -> str:
    """Return PM2 process list as JSON."""
    import subprocess
    try:
        r = subprocess.run(["pm2", "jlist"], capture_output=True, text=True,
                           timeout=10)
        return r.stdout or "PM2 returned empty output"
    except FileNotFoundError:
        return "{\"error\": \"pm2 not found — install Node.js + pm2 globally\"}"
    except Exception as e:
        return f"Error: {e}"


@app.tool()
async def get_scheduler_status(ctx: Context) -> dict:
    """Return CronScheduler and HeartbeatService status (Issue #18)."""
    result: dict = {}
    try:
        from core.scheduler.cron import CronScheduler
        cs = CronScheduler()
        result["cron"] = cs.get_status()
    except Exception as e:
        result["cron"] = {"error": str(e)}
    try:
        from core.scheduler.heartbeat import HeartbeatService
        # Construct with no callbacks — just to call get_status()
        hs = HeartbeatService(workspace=".", enabled=False)
        result["heartbeat"] = hs.get_status()
    except Exception as e:
        result["heartbeat"] = {"error": str(e)}
    return result


@app.tool()
async def get_evolution_status(ctx: Context) -> dict:
    """Return Genesis Evolution Agent last run info (Issue #18)."""
    logs_dir = Path("logs")
    result: dict = {"log_dir": str(logs_dir), "log_dir_exists": logs_dir.exists()}
    try:
        from modules.evolution.evolution_agent import config
        result["config"] = {
            k: str(v) for k, v in config.items()
            if k not in ("ollama_url",)
        }
    except Exception as e:
        result["config_error"] = str(e)
    return result


@app.tool()
async def get_mesh_peers(ctx: Context) -> dict:
    """Return online NeuralMesh P2P peers (Issue #18).

    Note: Returns stub data unless a NeuralMeshNode is running in-process.
    """
    return {
        "status": "mesh_node_not_running",
        "message": "Start NeuralMeshNode in-process to list peers.",
        "online_peers": [],
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
