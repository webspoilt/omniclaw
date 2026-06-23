# ruff: noqa: E741, S112
"""Privilege escalation enumeration: SUID, capabilities, writable paths, docker socket."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def check_suid() -> str:
    """Find all SUID/SGID binaries on the system."""
    try:
        proc = subprocess.run(  # noqa: S603
            ["find", "/", "-perm", "-4000", "-o", "-perm", "-2000"],  # noqa: S607
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return f"find failed: {proc.stderr.strip()[:200]}"
        binaries = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if not binaries:
            return "No SUID/SGID binaries found"
        interesting = [b for b in binaries if any(
            x in b.lower() for x in ["pkexec", "sudo", "su", "polkit", "gpasswd",
                                       "chsh", "mount", "umount", "cve", "CVE", "nmap"]
        )]
        lines = [f"SUID/SGID binaries ({len(binaries)} total):"]
        for b in binaries:
            marker = "  *** INTERESTING ***" if b in interesting else ""
            lines.append(f"  {b}{marker}")
        return "\n".join(lines[:100])
    except FileNotFoundError:
        return "find not available on this system"
    except Exception as e:
        return f"SUID check failed: {e}"


@tool()
def find_writable_etc() -> str:
    """Check for world-writable files in /etc that could enable privilege escalation."""
    try:
        proc = subprocess.run(  # noqa: S603
            ["find", "/etc", "-writable", "-type", "f"],  # noqa: S607
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return f"find failed: {proc.stderr.strip()[:200]}"
        files = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if not files:
            return "No writable files in /etc"
        return f"Writable files in /etc ({len(files)}):\n" + "\n".join(files[:50])
    except FileNotFoundError:
        return "find not available"
    except Exception as e:
        return f"Writable /etc check failed: {e}"


@tool()
def check_capabilities() -> str:
    """List processes running with elevated capabilities."""
    try:
        proc = subprocess.run(  # noqa: S603
            ["getcap", "-r", "/"],  # noqa: S607
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            return "getcap not available or failed"
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if not lines:
            return "No files with file capabilities found"
        return f"Files with capabilities ({len(lines)}):\n" + "\n".join(lines[:100])
    except FileNotFoundError:
        return "getcap not available (install libcap2-bin)"
    except Exception as e:
        return f"Capability check failed: {e}"


@tool()
def check_docker_socket() -> str:
    """Check if the Docker socket is accessible (common container escape vector)."""
    try:
        sock = Path("/var/run/docker.sock")
        if sock.exists():
            import stat as st
            mode = sock.stat().st_mode
            writable = bool(mode & st.S_IWGRP) or bool(mode & st.S_IWOTH)
            return f"Docker socket exists at {sock}" + (" — writable! Potential escape vector." if writable else "")
        docker_dir = Path("/var/run/docker")
        if docker_dir.exists():
            return f"Docker directory exists at {docker_dir} but socket not found"
        return "No Docker socket found"
    except Exception as e:
        return f"Docker socket check failed: {e}"


@tool()
def check_writable_paths() -> str:
    """Check for world-writable directories in PATH that could enable DLL/preload hijacking."""
    try:
        path_env = os.environ.get("PATH", "")
        writable = []
        for p in path_env.split(":"):
            p = p.strip()
            if not p:
                continue
            pp = Path(p)
            if pp.exists():
                try:
                    mode = pp.stat().st_mode
                    import stat as st
                    if bool(mode & st.S_IWOTH):
                        writable.append(f"{p} (world-writable)")
                except Exception:  # noqa: S110
                    continue
        if not writable:
            return "No world-writable directories in PATH"
        return f"World-writable PATH directories ({len(writable)}):\n" + "\n".join(writable)
    except Exception as e:
        return f"PATH writable check failed: {e}"
