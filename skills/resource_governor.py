"""Read and control system resources: CPU affinity, memory, I/O."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from core.skills.registry import tool


@tool(
    name="get_cpu_affinity",
    description="Get the CPU affinity of the current process or a given PID.",
    parameters={
        "pid": {"type": "integer", "description": "Process ID (default: self)"},
    },
    required=[],
)
async def get_cpu_affinity(pid: Optional[int] = None) -> dict[str, Any]:
    target = pid if pid is not None else os.getpid()
    try:
        proc = subprocess.run(["taskset", "-p", str(target)], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            return {"pid": target, "affinity": proc.stdout.strip()}
        return {"pid": target, "error": proc.stderr.strip()}
    except FileNotFoundError:
        return {"error": "taskset not available"}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="set_cpu_affinity",
    description="Set CPU affinity for a process using taskset.",
    parameters={
        "pid": {"type": "integer", "description": "Process ID"},
        "cpu_mask": {"type": "string", "description": "Hex mask or CPU list, e.g. '0x0f' or '0-3'"},
    },
    required=["pid", "cpu_mask"],
)
async def set_cpu_affinity(pid: int, cpu_mask: str) -> str:
    try:
        proc = subprocess.run(["taskset", "-p", cpu_mask, str(pid)], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            return f"Affinity set: {proc.stdout.strip()}"
        return f"Error: {proc.stderr.strip()}"
    except FileNotFoundError:
        return "Error: taskset not available"
    except Exception as e:
        return f"Error: {e}"


@tool(
    name="get_process_memory",
    description="Get memory usage of a process via /proc/[pid]/status or ps.",
    parameters={
        "pid": {"type": "integer", "description": "Process ID (default: self)"},
    },
    required=[],
)
async def get_process_memory(pid: Optional[int] = None) -> dict[str, Any]:
    target = pid if pid is not None else os.getpid()
    try:
        status_path = Path(f"/proc/{target}/status")
        if status_path.exists():
            vm_rss = ""
            vm_size = ""
            for line in status_path.read_text().splitlines():
                if line.startswith("VmRSS:"):
                    vm_rss = line.split(":")[1].strip()
                if line.startswith("VmSize:"):
                    vm_size = line.split(":")[1].strip()
            return {"pid": target, "vm_rss": vm_rss, "vm_size": vm_size}

        proc = subprocess.run(["ps", "-o", "rss=", "-p", str(target)], capture_output=True, text=True, timeout=5)
        return {"pid": target, "rss_kb": proc.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="monitor_io",
    description="Read I/O stats for a process from /proc/[pid]/io.",
    parameters={
        "pid": {"type": "integer", "description": "Process ID (default: self)"},
    },
    required=[],
)
async def monitor_io(pid: Optional[int] = None) -> dict[str, Any]:
    target = pid if pid is not None else os.getpid()
    try:
        io_path = Path(f"/proc/{target}/io")
        if not io_path.exists():
            return {"error": "/proc/[pid]/io not available"}
        io_info = {}
        for line in io_path.read_text().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                io_info[key.strip()] = val.strip()
        return {"pid": target, **io_info}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="set_niceness",
    description="Change the priority (niceness) of a process. Lower = more priority.",
    parameters={
        "pid": {"type": "integer", "description": "Process ID"},
        "nice_value": {"type": "integer", "description": "Nice value (-20 to 19). -20 = highest priority"},
    },
    required=["pid", "nice_value"],
)
async def set_niceness(pid: int, nice_value: int) -> str:
    nice_value = max(-20, min(19, nice_value))
    try:
        proc = subprocess.run(["renice", str(nice_value), "-p", str(pid)], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            return f"Niceness set to {nice_value} for PID {pid}"
        return f"Error: {proc.stderr.strip()}"
    except FileNotFoundError:
        return "Error: renice not available"
    except Exception as e:
        return f"Error: {e}"


@tool(
    name="get_uptime",
    description="Get system uptime and load averages from /proc/uptime and /proc/loadavg.",
    parameters={},
)
async def get_uptime() -> dict[str, Any]:
    try:
        uptime_text = Path("/proc/uptime").read_text().strip()
        parts = uptime_text.split()
        uptime_secs = float(parts[0])
        idle_secs = float(parts[1])
        load_text = Path("/proc/loadavg").read_text().strip()
        load_parts = load_text.split()
        return {
            "uptime_seconds": uptime_secs,
            "uptime_hours": round(uptime_secs / 3600, 2),
            "idle_seconds": idle_secs,
            "load_1min": load_parts[0],
            "load_5min": load_parts[1],
            "load_15min": load_parts[2],
            "running_processes": load_parts[3] if len(load_parts) > 3 else "",
        }
    except Exception as e:
        return {"error": str(e)}
