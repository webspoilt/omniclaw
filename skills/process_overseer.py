"""Fork, monitor, and manage child processes with supervisory logic."""
from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from core.skills.registry import tool

_active_workers: dict[str, subprocess.Popen] = {}


@tool(
    name="spawn_worker",
    description="Spawn a background subprocess running a Python script. Returns worker ID and PID.",
    parameters={
        "script_path": {"type": "string", "description": "Path to Python script (relative to project root)"},
        "args": {"type": "string", "description": "Command-line arguments as string"},
        "worker_id": {"type": "string", "description": "Unique name for this worker (used for later control)"},
    },
    required=["script_path", "worker_id"],
)
async def spawn_worker(script_path: str, worker_id: str, args: str | None = None) -> dict[str, Any]:
    if worker_id in _active_workers:
        proc = _active_workers[worker_id]
        if proc.poll() is None:
            return {"error": f"worker '{worker_id}' already running (PID {proc.pid})"}

    root = Path(__file__).resolve().parent.parent
    script = root / script_path
    if not script.is_file():
        return {"error": f"script not found: {script}"}

    cmd = ["python3", str(script)]
    if args:
        cmd.extend(args.split())

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )
        _active_workers[worker_id] = proc
        return {"worker_id": worker_id, "pid": proc.pid, "status": "started"}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="list_workers",
    description="List all spawned workers with their PID and status.",
    parameters={},
)
async def list_workers() -> dict[str, Any]:
    result = {}
    dead = []
    for wid, proc in _active_workers.items():
        ret = proc.poll()
        if ret is not None:
            result[wid] = {"pid": proc.pid, "status": "exited", "exit_code": ret}
            dead.append(wid)
        else:
            result[wid] = {"pid": proc.pid, "status": "running"}
    for wid in dead:
        del _active_workers[wid]
    return result


@tool(
    name="kill_worker",
    description="Terminate a spawned worker by worker_id or PID.",
    parameters={
        "worker_id": {"type": "string", "description": "Worker ID from spawn_worker"},
        "signal_name": {"type": "string", "description": "Signal: SIGTERM (default), SIGKILL, SIGINT"},
    },
    required=["worker_id"],
)
async def kill_worker(worker_id: str, signal_name: str = "SIGTERM") -> str:
    if worker_id not in _active_workers:
        return f"Error: unknown worker '{worker_id}'"
    proc = _active_workers[worker_id]
    sig = getattr(signal, signal_name, signal.SIGTERM)
    try:
        os.kill(proc.pid, sig)
        return f"Sent {signal_name} to worker '{worker_id}' (PID {proc.pid})"
    except ProcessLookupError:
        return f"Worker '{worker_id}' (PID {proc.pid}) already exited"
    except Exception as e:
        return f"Error: {e}"


@tool(
    name="watchdog_start",
    description="Start a watchdog that restarts a worker if it exits. Runs as a daemon thread.",
    parameters={
        "script_path": {"type": "string", "description": "Path to Python script (relative to project root)"},
        "worker_id": {"type": "string", "description": "Unique worker name"},
        "max_restarts": {"type": "integer", "description": "Max restart attempts before giving up"},
    },
    required=["script_path", "worker_id"],
)
async def watchdog_start(script_path: str, worker_id: str, max_restarts: int = 5) -> str:
    import threading
    root = Path(__file__).resolve().parent.parent
    script = root / script_path
    if not script.is_file():
        return f"Error: script not found: {script}"

    if worker_id in _active_workers:
        return f"Error: worker '{worker_id}' already exists"

    def _watch():
        attempts = 0
        while attempts < max_restarts:
            cmd = ["python3", str(script)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _active_workers[worker_id] = proc
            proc.wait()
            attempts += 1
            time.sleep(1)
        _active_workers.pop(worker_id, None)

    t = threading.Thread(target=_watch, daemon=True)
    t.start()
    return f"Watchdog started for '{worker_id}' (max {max_restarts} restarts)"


@tool(
    name="get_worker_output",
    description="Read accumulated stdout from a worker process (non-blocking).",
    parameters={
        "worker_id": {"type": "string", "description": "Worker ID"},
    },
    required=["worker_id"],
)
async def get_worker_output(worker_id: str) -> dict[str, Any]:
    if worker_id not in _active_workers:
        return {"error": f"unknown worker '{worker_id}'"}
    proc = _active_workers[worker_id]
    stdout = ""
    stderr = ""
    if proc.stdout:
        stdout = proc.stdout.read1().decode(errors="replace")
    if proc.stderr:
        stderr = proc.stderr.read1().decode(errors="replace")
    ret = proc.poll()
    return {
        "worker_id": worker_id,
        "running": ret is None,
        "exit_code": ret,
        "stdout": stdout,
        "stderr": stderr,
    }
