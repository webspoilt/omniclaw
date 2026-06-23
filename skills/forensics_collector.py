"""Forensic artifact collection: processes, network, logs, browser data, cron."""
from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from core.skills.registry import tool


@tool()
def collect_process_info() -> str:
    """Snapshot all running processes with PID, name, state, memory, and open files."""
    try:
        proc_path = Path("/proc")
        if not proc_path.exists():
            return "Process info not available on this system (not a Linux /proc filesystem)"
        processes: list[dict[str, str]] = []
        for entry in proc_path.iterdir():
            if not entry.name.isdigit():
                continue
            pid = entry.name
            try:
                status_data = (entry / "status").read_text()
                stat = {}
                for line in status_data.splitlines():
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        stat[parts[0].strip()] = parts[1].strip()
                cmdline = (entry / "cmdline").read_text().replace("\0", " ").strip()
                if not cmdline:
                    cmdline = stat.get("Name", "unknown")
                processes.append({
                    "pid": pid,
                    "name": stat.get("Name", "?"),
                    "state": stat.get("State", "?"),
                    "vm_rss": stat.get("VmRSS", "?"),
                    "uid": stat.get("Uid", "?").split("\t")[0] if "\t" in stat.get("Uid", "") else stat.get("Uid", "?"),
                    "cmdline": cmdline[:200],
                })
            except Exception:  # noqa: S110, S112
                continue
        lines = [f"Running processes ({len(processes)}):"]
        lines.append(f"{'PID':>6} {'NAME':<20} {'STATE':<10} {'RSS':>8} {'CMD':<60}")
        lines.append("-" * 110)
        for p in sorted(processes, key=lambda x: int(x["pid"]))[:150]:
            lines.append(
                f"{p['pid']:>6} {p['name'][:20]:<20} {p['state'][:10]:<10} "
                f"{p['vm_rss'][:8]:>8} {p['cmdline'][:60]:<60}"
            )
        if len(processes) > 150:
            lines.append(f"... and {len(processes) - 150} more")
        return "\n".join(lines)
    except Exception as e:
        return f"Process info collection failed: {e}"


@tool()
def collect_network_connections() -> str:
    """Collect active network connections via /proc/net/tcp, udp, or ss."""
    try:
        if os.name == "nt":
            return "Network connection collection not implemented on Windows"
        proc = subprocess.run(
            ["ss", "-tuanp"],  # noqa: S603, S607
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            lines = proc.stdout.splitlines()
            entries = lines[1:]
            return f"Network connections ({len(entries)}):\n{proc.stdout[:3000]}"
        proc = subprocess.run(
            ["netstat", "-tuanp"],  # noqa: S603, S607
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            lines = proc.stdout.splitlines()
            entries = [ln for ln in lines if ln.strip()]
            return f"Network connections ({len(entries)}):\n{proc.stdout[:3000]}"
        tcp_path = Path("/proc/net/tcp")
        udp_path = Path("/proc/net/udp")
        if tcp_path.exists():
            result_parts = []
            for p, label in [(tcp_path, "TCP"), (udp_path, "UDP")]:
                if p.exists():
                    content = p.read_text()
                    lines = content.splitlines()
                    result_parts.append(f"{label} connections ({len(lines) - 1}):\n{content[:2000]}")
            return "\n\n".join(result_parts) if result_parts else "No network info available"
        return "No network connection tools available (ss, netstat, /proc/net)"
    except FileNotFoundError:
        return "ss/netstat not available"
    except Exception as e:
        return f"Network connection collection failed: {e}"


@tool()
def collect_system_logs(log_source: str = "syslog", lines: int = 100) -> str:
    """Collect recent system log entries from journald, syslog, or dmesg."""
    try:
        if os.name == "nt":
            return "System log collection not implemented on Windows"
        if log_source == "dmesg":
            proc = subprocess.run(
                ["dmesg", "--level", "err,warn", "--read-clear"],  # noqa: S603, S607
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode != 0:
                proc = subprocess.run(
                    ["dmesg"],  # noqa: S603, S607
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            if proc.returncode == 0:
                entries = [ln for ln in proc.stdout.splitlines() if ln.strip()]
                count = min(lines, len(entries))
                return f"Kernel log ({len(entries)} lines, last {count}):\n" + "\n".join(entries[-count:])
            return "dmesg not available"
        if log_source == "journal":
            proc = subprocess.run(  # noqa: S603
                ["journalctl", "-n", str(lines), "--no-pager"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode == 0:
                out = proc.stdout.strip()
                return f"journalctl ({len(out.splitlines())} lines):\n{out[-3000:]}"
            return "journalctl not available"
        syslog_paths = [
            Path("/var/log/syslog"),
            Path("/var/log/messages"),
            Path("/var/log/system.log"),
        ]
        for p in syslog_paths:
            if p.exists():
                content = p.read_text(errors="replace")
                all_lines = content.splitlines()
                return f"{p.name} ({len(all_lines)} lines, last {lines}):\n" + "\n".join(all_lines[-lines:])
        return "No system log files found"
    except Exception as e:
        return f"Log collection failed: {e}"


@tool()
def collect_cron_jobs() -> str:
    """List all cron jobs from system crontabs, user crontabs, and cron directories."""
    try:
        if os.name == "nt":
            return "Cron job collection not implemented on Windows"
        entries: list[tuple[str, str]] = []
        cron_dirs = [
            Path("/etc/cron.d"),
            Path("/etc/cron.hourly"),
            Path("/etc/cron.daily"),
            Path("/etc/cron.weekly"),
            Path("/etc/cron.monthly"),
        ]
        for cron_dir in cron_dirs:
            if cron_dir.exists():
                for fpath in sorted(cron_dir.iterdir()):
                    if fpath.is_file() and not fpath.name.startswith("."):
                        try:
                            content = fpath.read_text().strip()
                            if content:
                                entries.append((fpath.name, content[:500]))
                        except Exception:  # noqa: S110, S112
                            continue
        crontab_path = Path("/etc/crontab")
        if crontab_path.exists():
            try:
                content = crontab_path.read_text().strip()
                if content:
                    entries.append(("crontab (system)", content[:1000]))
            except Exception:  # noqa: S110
                pass
        user_crontabs = Path("/var/spool/cron/crontabs")
        if user_crontabs.exists():
            for fpath in sorted(user_crontabs.iterdir()):
                if fpath.is_file() and not fpath.name.startswith("."):
                    try:
                        content = fpath.read_text().strip()
                        if content:
                            entries.append((f"crontab ({fpath.name})", content[:500]))
                    except Exception:  # noqa: S110, S112
                        continue
        if not entries:
            return "No cron jobs found on this system"
        lines = [f"Found {len(entries)} cron sources:"]
        for name, content in entries:
            lines.append(f"\n=== {name} ===")
            lines.append(content)
        return "\n".join(lines)
    except Exception as e:
        return f"Cron collection failed: {e}"


@tool()
def collect_browser_artifacts() -> str:
    """Check for browser history, cookies, and login data databases."""
    try:
        home = Path.home()
        browser_paths = {
            "Chrome": home / ".config" / "google-chrome" / "Default",
            "Chromium": home / ".config" / "chromium" / "Default",
            "Firefox": home / ".mozilla" / "firefox",
            "Brave": home / ".config" / "BraveSoftware" / "Brave-Browser" / "Default",
            "Edge": home / ".config" / "microsoft-edge" / "Default",
        }
        artifacts: list[dict[str, str]] = []
        for browser, path in browser_paths.items():
            if not path.exists():
                continue
            dbs = []
            for db_name in ["History", "Cookies", "Login Data", "Web Data"]:
                db_path = path / db_name
                if db_path.exists():
                    size = db_path.stat().st_size
                    modified = datetime.fromtimestamp(db_path.stat().st_mtime, tz=UTC)
                    dbs.append(f"{db_name} ({size / 1024:.0f} KB, modified {modified.strftime('%Y-%m-%d')})")
            if dbs:
                artifacts.append({"browser": browser, "artifacts": dbs, "path": str(path)})
        if not artifacts:
            return "No browser artifacts found"
        lines = [f"Browser artifacts found ({len(artifacts)} browsers):"]
        for a in artifacts:
            lines.append(f"\n  {a['browser']} ({a['path']}):")
            for db in a["artifacts"]:
                lines.append(f"    - {db}")
        return "\n".join(lines)
    except Exception as e:
        return f"Browser artifact collection failed: {e}"


@tool()
def collect_ssh_artifacts() -> str:
    """List SSH authorized_keys, known_hosts, and config files."""
    try:
        home = Path.home()
        ssh_dir = home / ".ssh"
        if not ssh_dir.exists():
            return "No .ssh directory found"
        artifacts: list[str] = []
        for fname in ["authorized_keys", "known_hosts", "config", "id_rsa", "id_ed25519", "id_ecdsa"]:
            fpath = ssh_dir / fname
            if fpath.exists():
                stat = fpath.stat()
                modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
                artifacts.append(
                    f"  {fname} ({stat.st_size} bytes, modified {modified.strftime('%Y-%m-%d %H:%M')})"
                )
        if not artifacts:
            return "SSH directory exists but no common files found"
        return f"SSH artifacts in {ssh_dir}:\n" + "\n".join(artifacts)
    except Exception as e:
        return f"SSH artifact collection failed: {e}"
