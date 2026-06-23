"""Dead man's switch: cascading triggers, graduated response, persistence across restarts, self-revive."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from threading import Thread

from core.skills.registry import tool

_SWITCH_FILE = Path("/tmp/agent_deadman_switches.json")
_HEARTBEAT_FILE = Path("/tmp/agent_heartbeat.log")


def _load_switches() -> dict[str, dict]:
    if _SWITCH_FILE.exists():
        try:
            return json.loads(_SWITCH_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_switches(switches: dict[str, dict]):
    _SWITCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SWITCH_FILE.write_text(json.dumps(switches, indent=2))


@tool()
def set_switch(name: str, timeout_sec: int = 60, action: str = "", escalate: str = "") -> str:
    """Set a dead man's switch. If heartbeat not received within timeout, triggers action + optional cascading escalate (name of next switch)."""
    try:
        switches = _load_switches()
        switches[name] = {
            "last_heartbeat": time.time(),
            "timeout": timeout_sec,
            "action": action or f"log:switch_expired:{name}",
            "escalate": escalate,
            "triggered": False,
            "created": time.time(),
            "revive_count": 0,
        }
        _save_switches(switches)
        parts = [f"Switch '{name}' set (timeout: {timeout_sec}s)"]
        if action:
            parts.append(f"action: {action}")
        if escalate:
            parts.append(f"→ cascades to: '{escalate}'")
        return ", ".join(parts)
    except Exception as e:
        return f"Setting switch failed: {e}"


@tool()
def trigger_on_no_contact(name: str = "", execute_action: bool = False) -> str:
    """Check if a dead man's switch has expired. Set execute_action=True to actually run the configured action."""
    try:
        switches = _load_switches()
        if not switches:
            return "No dead man's switches set. Use set_switch() first."
        to_check = {k: v for k, v in switches.items()} if not name else {name: switches.get(name)} if name in switches else {}
        if not to_check:
            return f"Switch '{name}' not found"
        triggered = []
        for sname, sw in to_check.items():
            if sw is None:
                continue
            elapsed = time.time() - sw["last_heartbeat"]
            if elapsed > sw["timeout"] and not sw["triggered"]:
                sw["triggered"] = True
                action = sw.get("action", "")
                if execute_action and action:
                    _execute_action(action)
                trigger_msg = f"  '{sname}' EXPIRED after {elapsed:.0f}s → {action or 'log'}"
                escalate = sw.get("escalate", "")
                if escalate and escalate in switches:
                    switches[escalate]["last_heartbeat"] = time.time() - switches[escalate]["timeout"] - 1
                    trigger_msg += f" [cascaded to '{escalate}']"
                triggered.append(trigger_msg)
            elif not sw["triggered"]:
                remaining = sw["timeout"] - elapsed
                triggered.append(f"  '{sname}' OK ({remaining:.0f}s remaining / {sw['timeout']}s timeout)")
            else:
                triggered.append(f"  '{sname}' already triggered")
        _save_switches(switches)
        return "Dead man's switch status:\n" + "\n".join(triggered)
    except Exception as e:
        return f"Switch check failed: {e}"


def _execute_action(action: str):
    try:
        if action.startswith("log:"):
            logpath = Path("/var/log/agent_deadman.log")
            logpath.parent.mkdir(parents=True, exist_ok=True)
            with open(logpath, "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {action}\n")
        elif action.startswith("cmd:"):
            cmd = action[4:]
            subprocess.Popen(cmd, shell=True, start_new_session=True)  # noqa: S602, S607
        elif action.startswith("file:"):
            path = action[5:]
            Path(path).touch()
        elif action.startswith("broadcast:"):
            msg = action[10:]
            try:
                subprocess.run(["wall", msg], capture_output=True, timeout=5)  # noqa: S603, S607
            except FileNotFoundError:
                pass
    except Exception:
        pass


@tool()
def heartbeat(name: str) -> str:
    """Send a heartbeat to keep a dead man's switch alive. A switch that was triggered can be revived if revive() is called first."""
    try:
        switches = _load_switches()
        if name not in switches:
            return f"No switch named '{name}'. Use set_switch() to create one."
        if switches[name]["triggered"]:
            return f"Switch '{name}' already triggered. Use revive_switch() to reactivate."
        switches[name]["last_heartbeat"] = time.time()
        age = time.time() - switches[name]["created"]
        _save_switches(switches)
        _HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_HEARTBEAT_FILE, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] heartbeat:{name}\n")
        return f"Heartbeat for '{name}' OK (alive for {age:.0f}s)"
    except Exception as e:
        return f"Heartbeat failed: {e}"


@tool()
def revive_switch(name: str) -> str:
    """Revive a previously triggered dead man's switch, resetting it to active."""
    try:
        switches = _load_switches()
        if name not in switches:
            return f"No switch named '{name}'"
        switches[name]["triggered"] = False
        switches[name]["last_heartbeat"] = time.time()
        switches[name]["revive_count"] = switches[name].get("revive_count", 0) + 1
        _save_switches(switches)
        return f"Switch '{name}' revived (revive #{switches[name]['revive_count']})"
    except Exception as e:
        return f"Revive failed: {e}"


@tool()
def broadcast_warning(message: str) -> str:
    """Broadcast a warning message to all terminals and to the agent's own log."""
    try:
        results = []
        try:
            proc = subprocess.run(["wall", message[:200]], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            if proc.returncode == 0:
                results.append("wall sent to all terminals")
        except FileNotFoundError:
            pass
        log_path = Path("/var/log/agent_warnings.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        results.append(f"logged to {log_path}")
        return f"Warning broadcast: '{(message[:100])}' — {'; '.join(results)}"
    except Exception as e:
        return f"Broadcast failed: {e}"


@tool()
def start_background_watchdog(interval_sec: int = 10) -> str:
    """Start a background thread that periodically checks all switches and triggers expired ones."""
    try:
        def _watchdog_loop():
            while True:
                try:
                    switches = _load_switches()
                    for sname, sw in list(switches.items()):
                        if sw.get("triggered"):
                            continue
                        elapsed = time.time() - sw["last_heartbeat"]
                        if elapsed > sw["timeout"]:
                            sw["triggered"] = True
                            action = sw.get("action", "")
                            if action:
                                _execute_action(action)
                            escalate = sw.get("escalate", "")
                            if escalate and escalate in switches:
                                switches[escalate]["last_heartbeat"] = time.time() - switches[escalate]["timeout"] - 1
                    _save_switches(switches)
                except Exception:
                    pass
                time.sleep(interval_sec)

        t = Thread(target=_watchdog_loop, daemon=True)
        t.start()
        return f"Background watchdog started (checking every {interval_sec}s)"
    except Exception as e:
        return f"Watchdog start failed: {e}"


@tool()
def list_switches() -> str:
    """List all configured dead man's switches with their status."""
    try:
        switches = _load_switches()
        if not switches:
            return "No switches configured"
        lines = [f"Dead man's switches ({len(switches)}):"]
        for name, sw in sorted(switches.items()):
            elapsed = time.time() - sw["last_heartbeat"]
            status = "TRIGGERED" if sw["triggered"] else "ACTIVE" if elapsed <= sw["timeout"] else "EXPIRED"
            lines.append(f"  {name:<20} {status:<12} {elapsed:>6.0f}s / {sw['timeout']}s  revives:{sw.get('revive_count',0)}  action:{sw.get('action','')[:30]}")
        return "\n".join(lines)
    except Exception as e:
        return f"List failed: {e}"


@tool()
def self_destruct() -> str:
    """Trigger a self-destruct sequence: broadcast warning, log, escalate all switches."""
    try:
        switches = _load_switches()
        for name, sw in switches.items():
            sw["last_heartbeat"] = time.time() - sw["timeout"] - 1
        _save_switches(switches)
        result = trigger_on_no_contact(execute_action=True)
        broadcast_warning("SELF-DESTRUCT INITIATED — all dead man's switches expired")
        return f"SELF-DESTRUCT SEQUENCE ACTIVATED:\n{result}"
    except Exception as e:
        return f"Self-destruct failed: {e}"
