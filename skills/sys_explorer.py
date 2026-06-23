"""Enumerate system hardware, kernel, capabilities, and security posture."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from core.skills.registry import tool


@tool(
    name="list_kernel_modules",
    description="List all loaded kernel modules with their sizes and used-by counts.",
    parameters={},
)
async def list_kernel_modules() -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return [{"error": "lsmod unavailable"}]
        lines = proc.stdout.strip().splitlines()
        if not lines:
            return []
        header = lines[0].split()
        modules = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                modules.append({
                    "module": parts[0],
                    "size": parts[1],
                    "used_by": parts[2] if len(parts) > 2 else "",
                })
        return modules
    except FileNotFoundError:
        return [{"error": "lsmod not found on this system"}]


@tool(
    name="check_seccomp",
    description="Check if seccomp is enabled and in what mode (via /proc/self/status or prctl).",
    parameters={},
)
async def check_seccomp() -> dict[str, Any]:
    try:
        status_path = Path("/proc/self/status")
        if status_path.exists():
            for line in status_path.read_text().splitlines():
                if line.startswith("Seccomp:"):
                    mode = line.split(":")[1].strip()
                    modes = {"0": "disabled", "1": "strict", "2": "filtered"}
                    return {"seccomp_mode": modes.get(mode, mode)}
        proc = subprocess.run(["python3", "-c", "import ctypes; libc=ctypes.CDLL('libc.so.6'); print(libc.prctl(22))"], capture_output=True, text=True, timeout=5)
        return {"seccomp_mode": proc.stdout.strip()}
    except Exception as e:
        return {"error": str(e), "seccomp_mode": "unknown"}


@tool(
    name="list_capabilities",
    description="List effective capabilities of the current process via /proc/self/status.",
    parameters={},
)
async def list_capabilities() -> dict[str, Any]:
    try:
        status_path = Path("/proc/self/status")
        if not status_path.exists():
            return {"error": "/proc/self/status not available (non-Linux?)"}
        caps = {}
        for line in status_path.read_text().splitlines():
            if line.startswith("Cap") and ":" in line:
                parts = line.split(":", 1)
                caps[parts[0].strip()] = parts[1].strip()
        return caps
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_cpu_info",
    description="Return CPU model, core count, architecture, and flags from /proc/cpuinfo.",
    parameters={},
)
async def get_cpu_info() -> dict[str, Any]:
    try:
        cpuinfo = Path("/proc/cpuinfo")
        if not cpuinfo.exists():
            return {"error": "not available on this system"}
        text = cpuinfo.read_text()
        model = ""
        flags = []
        cores = 0
        for line in text.splitlines():
            if line.startswith("model name"):
                model = line.split(":")[1].strip()
            if line.startswith("flags"):
                flags = line.split(":")[1].strip().split()
            if line.startswith("processor"):
                cores += 1
        return {
            "model": model,
            "cores": cores,
            "flags_count": len(flags),
            "flags_sample": flags[:20],
        }
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_memory_info",
    description="Return total and available memory from /proc/meminfo.",
    parameters={},
)
async def get_memory_info() -> dict[str, Any]:
    try:
        meminfo = Path("/proc/meminfo")
        if not meminfo.exists():
            return {"error": "not available"}
        info = {}
        for line in meminfo.read_text().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                info[key.strip()] = val.strip()
        return {
            "total_kb": info.get("MemTotal"),
            "available_kb": info.get("MemAvailable"),
            "free_kb": info.get("MemFree"),
        }
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="list_available_syscalls",
    description="List available syscalls by reading /usr/include/asm/unistd*.h or ausyscall.",
    parameters={
        "search": {"type": "string", "description": "Optional filter string, e.g. 'exec'"},
    },
    required=[],
)
async def list_available_syscalls(search: Optional[str] = None) -> list[str]:
    try:
        proc = subprocess.run(["ausyscall", "--dump"], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            lines = proc.stdout.strip().splitlines()
            result = [l for l in lines if l.strip()]
            if search:
                result = [l for l in result if search.lower() in l.lower()]
            return result[:200]
    except FileNotFoundError:
        pass
    return [{"error": "ausyscall not available"}]


@tool(
    name="get_disk_usage",
    description="Return disk usage statistics for all mounted filesystems.",
    parameters={},
)
async def get_disk_usage() -> list[dict[str, Any]]:
    try:
        proc = subprocess.run(["df", "-h", "--exclude-type=tmpfs", "--exclude-type=devtmpfs"], capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return [{"error": "df command failed"}]
        lines = proc.stdout.strip().splitlines()
        if not lines:
            return []
        result = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 6:
                result.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "avail": parts[3],
                    "use_percent": parts[4],
                    "mounted": parts[5],
                })
        return result
    except FileNotFoundError:
        return [{"error": "df not found"}]
