# ruff: noqa: E501, S108, S112
"""Situational awareness: session spy, USB/SSH detection, keystroke timing, browser history, network monitoring."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from core.skills.registry import tool

_SESSION_BASELINE: dict[str, float] = {}


@tool()
def detect_sysadmin_activity() -> str:
    """Comprehensive check for signs of human operator interaction."""
    try:
        indicators = []
        try:
            proc = subprocess.run(["last", "-10"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            logins = [line for line in proc.stdout.splitlines() if line.strip() and "wtmp" not in line]
            if logins:
                indicators.append(f"Recent logins ({len(logins)}):\n" + "\n".join(logins[:8]))
        except FileNotFoundError:
            pass
        try:
            proc = subprocess.run(["who", "-u"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            users = [line for line in proc.stdout.splitlines() if line.strip()]
            if users:
                indicators.append(f"Currently logged in ({len(users)}):\n" + "\n".join(users))
        except FileNotFoundError:
            pass
        try:
            proc = subprocess.run(["ps", "--no-headers", "-eo", "pid,tty,time,cmd"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            tty_procs = [line for line in proc.stdout.splitlines() if line.strip() and "?" not in line.split(None, 2)[1:2]]
            if tty_procs:
                indicators.append(f"Terminal-attached processes ({len(tty_procs)}):")
                for p in tty_procs[:12]:
                    indicators.append(f"  {p[:160]}")
        except FileNotFoundError:
            pass
        for hist_name in [".bash_history", ".zsh_history", ".zhistory"]:
            hist_path = Path(os.path.expanduser(f"~/{hist_name}"))
            if hist_path.exists():
                age = time.time() - hist_path.stat().st_mtime
                if age < 300:
                    indicators.append(f"{hist_name} modified {age:.0f}s ago")
        try:
            proc = subprocess.run(["ss", "-tnp"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            established = [line for line in proc.stdout.splitlines() if "ESTAB" in line]
            if established:
                indicators.append(f"Active network connections ({len(established)}):\n" + "\n".join(established[:8]))
        except FileNotFoundError:
            pass
        try:
            output = subprocess.check_output(["loginctl", "list-sessions"], text=True, timeout=10)  # noqa: S603, S607
            sessions = [line for line in output.splitlines() if line.strip() and line[0].isdigit()]
            if sessions:
                indicators.append("loginctl sessions:\n" + "\n".join(sessions[:5]))
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        if not indicators:
            return "No human operator activity detected"
        return "SYSADMIN ACTIVITY DETECTED:\n" + "\n".join(indicators)
    except Exception as e:
        return f"Situational awareness check failed: {e}"


@tool()
def monitor_new_files(path: str = "/tmp", since_seconds: int = 60) -> str:
    """List files created or modified in a directory within the given time window."""
    try:
        base = Path(path)
        if not base.exists():
            return f"Path not found: {path}"
        cutoff = time.time() - since_seconds
        new_files = []
        for fpath in base.iterdir():
            try:
                st = fpath.stat()
                if st.st_mtime > cutoff or st.st_ctime > cutoff:
                    age = time.time() - st.st_mtime
                    new_files.append(f"  {fpath.name} ({st.st_size}b, {age:.0f}s old)")
            except Exception:
                continue
        if not new_files:
            return f"No new files in {path} in the last {since_seconds}s"
        new_files.sort(key=lambda x: x.split()[-2], reverse=True)
        return f"New/modified files in {path} ({len(new_files)}):\n" + "\n".join(new_files[:60])
    except Exception as e:
        return f"File monitoring failed: {e}"


@tool()
def track_user_commands() -> str:
    """Check recent shell commands from bash/zsh history."""
    try:
        hist_paths = [
            Path(os.path.expanduser("~/.bash_history")),
            Path(os.path.expanduser("~/.zsh_history")),
            Path("/root/.bash_history"),
        ]
        hist_path = None
        for p in hist_paths:
            if p.exists():
                hist_path = p
                break
        if not hist_path:
            return "No shell history found"
        content = hist_path.read_text(errors="replace")
        lines = [line for line in content.splitlines() if line.strip()]
        last_80 = lines[-80:] if len(lines) > 80 else lines
        return f"Recent commands from {hist_path.name} ({len(last_80)} shown of {len(lines)} total):\n" + "\n".join(
            f"  {i+1}: {cmd[:160]}" for i, cmd in enumerate(last_80)
        )
    except Exception as e:
        return f"Command tracking failed: {e}"


@tool()
def spy_on_session(interval_sec: int = 5, duration_sec: int = 30) -> str:
    """Watch /proc for new TTY-based processes over a window — detects active human sessions."""
    try:
        snapshots = []
        deadline = time.time() + duration_sec
        while time.time() < deadline:
            try:
                proc = subprocess.run(["ps", "-eo", "pid,tty,etime,cmd"], capture_output=True, text=True, timeout=5)  # noqa: S603, S607
                tty_lines = [line for line in proc.stdout.splitlines() if line.strip() and not line.startswith("PID") and not line.split(None, 2)[1] == "?"]
                active = [ent.strip() for ent in tty_lines[:6]]
                if active:
                    snapshots.append(f"[{time.strftime('%H:%M:%S')}] TTY processes: {'; '.join(active)}")
            except Exception:
                pass
            time.sleep(interval_sec)
        if not snapshots:
            return f"No TTY activity detected during {duration_sec}s observation window"
        return "Session spy report:\n" + "\n".join(snapshots)
    except Exception as e:
        return f"Session spy failed: {e}"


@tool()
def detect_usb_devices() -> str:
    """Detect newly connected USB storage or input devices."""
    try:
        indicators = []
        try:
            proc = subprocess.run(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT", "-l"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            usb = [line for line in proc.stdout.splitlines() if "disk" in line and ("sd" in line or "nvme" in line)]
            if usb:
                indicators.append("Block devices:\n" + "\n".join(usb))
        except FileNotFoundError:
            pass
        try:
            proc = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            devices = [line for line in proc.stdout.splitlines() if line.strip()]
            if devices:
                indicators.append(f"USB devices ({len(devices)}):\n" + "\n".join(devices[:10]))
        except FileNotFoundError:
            pass
        try:
            dmesg = subprocess.run(["dmesg", "--level=info,err,warn"], capture_output=True, text=True, timeout=5)  # noqa: S603, S607
            usb_lines = [line for line in dmesg.stdout.splitlines() if "USB" in line or "usb" in line]
            recent_usb = [line for line in usb_lines if "New" in line or "new" in line or "removed" in line]
            if recent_usb:
                indicators.append("Recent USB events:\n" + "\n".join(recent_usb[-5:]))
        except FileNotFoundError:
            pass
        if not indicators:
            return "No USB devices detected"
        return "USB device scan:\n" + "\n".join(indicators)
    except Exception as e:
        return f"USB detection failed: {e}"


@tool()
def detect_ssh_connections() -> str:
    """Check for active or recent SSH connections to the system."""
    try:
        indicators = []
        try:
            proc = subprocess.run(["ss", "-tnp", "state", "established"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            ssh_conns = [line for line in proc.stdout.splitlines() if ":22" in line]
            if ssh_conns:
                indicators.append(f"Active SSH connections ({len(ssh_conns)}):\n" + "\n".join(ssh_conns))
        except FileNotFoundError:
            pass
        try:
            proc = subprocess.run(["last", "-10", "|", "grep", "still"], shell=True, capture_output=True, text=True, timeout=10)  # noqa: S602
            still_logged = [line for line in proc.stdout.splitlines() if line.strip()]
            if still_logged:
                indicators.append("Still logged in:\n" + "\n".join(still_logged[:5]))
        except Exception:
            pass
        auth_log = Path("/var/log/auth.log")
        if auth_log.exists():
            try:
                lines = auth_log.read_text(errors="replace").splitlines()
                ssh_accept = [line for line in lines if "sshd" in line and "Accepted" in line]
                if ssh_accept:
                    indicators.append(f"Recent SSH accepts ({len(ssh_accept[-5:])}):\n" + "\n".join(ssh_accept[-5:]))
            except Exception:
                pass
        if not indicators:
            return "No SSH connections detected"
        return "SSH connection report:\n" + "\n".join(indicators)
    except Exception as e:
        return f"SSH detection failed: {e}"


@tool()
def check_browser_history(browser: str = "firefox") -> str:
    """Check recent browser history from Firefox/Chrome profiles for user activity."""
    try:
        import sqlite3
        base = Path.home()
        history_paths = {
            "firefox": list(base.glob(".mozilla/firefox/*.default*/places.sqlite")),
            "chrome": list(base.glob(".config/google-chrome/Default/History")),
            "chromium": list(base.glob(".config/chromium/Default/History")),
        }
        targets = history_paths.get(browser, [])
        if not targets:
            return f"No {browser} history database found"
        results = []
        for db_path in targets[:2]:
            if not db_path.exists():
                continue
            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 15")
                rows = cursor.fetchall()
                conn.close()
                for url, title, count, last_visit in rows:
                    ts = last_visit / 1000000 if last_visit else 0
                    age = time.time() - ts if ts else -1
                    if age < 3600:
                        results.append(f"  {title or 'N/A'[:50]:<50} {url[:80]} ({count}x, {age:.0f}s ago)")
                if not results:
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 15")
                    rows = cursor.fetchall()
                    conn.close()
                    for url, title, count, last_visit in rows:
                        ts = last_visit / 1000000 if last_visit else 0
                        age = time.time() - ts if ts else -1
                        if age < 3600:
                            results.append(f"  {title or 'N/A'[:50]:<50} {url[:80]} ({count}x, {age:.0f}s ago)")
            except Exception as e:
                results.append(f"  Error reading {db_path}: {e}")
        if not results:
            return f"No recent {browser} history in the last hour"
        return f"Recent {browser} browsing:\n" + "\n".join(results[:15])
    except ImportError:
        return "sqlite3 not available — cannot query browser history"
    except Exception as e:
        return f"Browser history check failed: {e}"


@tool()
def monitor_network_connections() -> str:
    """Monitor active network connections for suspicious external endpoints."""
    try:
        indicators = []
        proc = subprocess.run(["ss", "-tunap"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
        lines = proc.stdout.splitlines()
        header_found = False
        for line in lines:
            if "Netid" in line:
                header_found = True
                continue
            if header_found and line.strip():
                parts = line.split()
                if len(parts) >= 5:
                    proto = parts[0]
                    local = parts[3]
                    peer = parts[4]
                    if "0.0.0.0" not in peer and ":::" not in peer:
                        indicators.append(f"  {proto:<4} {local:<30} → {peer}")
        if not indicators:
            return "No non-listening network connections found"
        return f"Network connections ({len(indicators)}):\n" + "\n".join(indicators[:30])
    except FileNotFoundError:
        return "ss not available"
    except Exception as e:
        return f"Network monitoring failed: {e}"
