# ruff: noqa: S108, S112
"""Operational security auditing: traces left behind, log cleanliness, timestamp analysis."""
from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from pathlib import Path

from core.skills.registry import tool


@tool()
def audit_logs(directory: str = "/var/log") -> str:
    """Audit log files for suspicious entries that might indicate the agent's traces."""
    try:
        log_dir = Path(directory)
        if not log_dir.exists():
            return f"Directory not found: {directory}"
        recent = time.time() - 3600
        suspicious = []
        for fpath in sorted(log_dir.rglob("*")):
            if not fpath.is_file() or fpath.stat().st_size == 0:
                continue
            try:
                mtime = fpath.stat().st_mtime
                if mtime > recent:
                    entries = len(fpath.read_text(errors="replace").splitlines())
                    modified = datetime.fromtimestamp(mtime, tz=UTC)
                    suspicious.append(
                        f"  {fpath.relative_to(log_dir)} ({entries} lines, modified {modified.strftime('%H:%M')})"
                    )
            except Exception:  # noqa: S110
                continue
        if not suspicious:
            return f"No recently modified log files in {directory}"
        return f"Recently modified logs in {directory} ({len(suspicious)}):\n" + "\n".join(suspicious[:50])
    except Exception as e:
        return f"Log audit failed: {e}"


@tool()
def check_timestamps(path: str) -> str:
    """Check access/modification/change timestamps of a file for inconsistencies."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        stat = p.stat()
        atime = datetime.fromtimestamp(stat.st_atime, tz=UTC)
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
        ctime = datetime.fromtimestamp(stat.st_ctime, tz=UTC)
        now = datetime.now(UTC)
        results = [
            f"File: {path}",
            f"  Access: {atime.strftime('%Y-%m-%d %H:%M:%S')} ({(now - atime).total_seconds() / 3600:.1f}h ago)",
            f"  Modify: {mtime.strftime('%Y-%m-%d %H:%M:%S')} ({(now - mtime).total_seconds() / 3600:.1f}h ago)",
            f"  Change: {ctime.strftime('%Y-%m-%d %H:%M:%S')} ({(now - ctime).total_seconds() / 3600:.1f}h ago)",
            f"  Size: {stat.st_size} bytes",
        ]
        time_diff = abs((mtime - ctime).total_seconds())
        if time_diff > 60:
            results.append(f"  WARNING: Modify/Change time differ by {time_diff:.0f}s — possible tampering")
        return "\n".join(results)
    except Exception as e:
        return f"Timestamp check failed: {e}"


@tool()
def find_evidence_left_behind(keywords: str = "password,token,key,secret,credential") -> str:
    """Search common locations for files containing sensitive keywords the agent may have created."""
    try:
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        search_paths = [
            Path("/tmp"), Path("/root"), Path(os.path.expanduser("~")),
            Path("/var/tmp"), Path("/dev/shm"),
        ]
        findings = []
        for base in search_paths:
            if not base.exists():
                continue
            for fpath in base.iterdir():
                if not fpath.is_file() or fpath.stat().st_size > 1024 * 1024:
                    continue
                try:
                    content = fpath.read_text(errors="replace").lower()
                    for kw in kw_list:
                        if kw.lower() in content:
                            age = time.time() - fpath.stat().st_mtime
                            findings.append(
                                f"  {fpath} (contains '{kw}', {fpath.stat().st_size}b, {age:.0f}s old)"
                            )
                            break
                except Exception:  # noqa: S110
                    continue
        if not findings:
            return "No files with sensitive keywords found in common locations"
        return f"Potential evidence left behind ({len(findings)} files):\n" + "\n".join(findings[:50])
    except Exception as e:
        return f"Evidence search failed: {e}"
