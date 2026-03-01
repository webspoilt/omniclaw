#!/usr/bin/env python3
"""
OmniClaw IPS Agent — Autonomous Intrusion Prevention
=====================================================
Listens for eBPF ring-buffer alerts from monitor.bpf.c, uses LLM-based
threat classification, and autonomously blocks malicious IPs via iptables
or nftables.  Includes dry-run safety, admin whitelist, simulation mode
for non-Linux/Termux, and JSON action logging for the Manager agent.

Designed for 2-watt mobile servers and low-end VPS.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import re
import shutil
import socket
import struct
import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("OmniClaw.Security.IPS")


# ═══════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════

# Alert type constants (must match monitor.bpf.c)
ALERT_TCP_CONNECT   = 1
ALERT_SSH_ATTEMPT   = 2
ALERT_BRUTE_FORCE   = 3
ALERT_SSH_AUTH_FAIL  = 4

ALERT_NAMES = {
    ALERT_TCP_CONNECT:  "tcp_connect",
    ALERT_SSH_ATTEMPT:  "ssh_attempt",
    ALERT_BRUTE_FORCE:  "brute_force",
    ALERT_SSH_AUTH_FAIL: "ssh_auth_fail",
}


@dataclass
class IPSEvent:
    """A single IPS alert, either from eBPF or simulation."""
    src_ip: str
    dst_ip: str = "0.0.0.0"
    src_port: int = 0
    dst_port: int = 22
    pid: int = 0
    fail_count: int = 0
    first_seen: float = 0.0  # Unix timestamp
    last_seen: float = 0.0
    alert_type: int = ALERT_SSH_AUTH_FAIL
    comm: str = ""

    @property
    def alert_name(self) -> str:
        return ALERT_NAMES.get(self.alert_type, f"unknown({self.alert_type})")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["alert_name"] = self.alert_name
        return d


@dataclass
class IPSAction:
    """Record of an autonomous action taken by the IPS agent."""
    timestamp: str
    event: dict
    analysis: str       # LLM classification or heuristic result
    verdict: str        # "block", "monitor", "ignore"
    command: str        # Shell command (or "[DRY-RUN] ..." prefix)
    executed: bool      # Whether the command was actually run
    dry_run: bool
    blocked_ip: str
    reason: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class IPSConfig:
    """Runtime configuration for the IPS agent."""
    enabled: bool = True
    dry_run: bool = True          # SAFETY DEFAULT: never block for real
    admin_whitelist: List[str] = field(default_factory=lambda: ["127.0.0.1"])
    fail_threshold: int = 5
    time_window_sec: int = 300
    block_tool: str = "iptables"  # "iptables" or "nftables"
    log_file: str = "./logs/ips_actions.jsonl"
    llm_analysis: bool = True
    auth_log_path: str = "/var/log/auth.log"
    poll_interval: float = 1.0    # Ring-buffer poll interval (seconds)

    @classmethod
    def from_dict(cls, d: dict) -> "IPSConfig":
        """Create config from a dict (e.g. parsed YAML section)."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


# ═══════════════════════════════════════════════════════════════
# Threat classifier (LLM-backed with heuristic fallback)
# ═══════════════════════════════════════════════════════════════

class ThreatClassifier:
    """
    Classifies IPS events using a lightweight LLM prompt or a
    pure-heuristic fallback when LLM is unavailable.
    """

    # Pre-built classification prompt (kept small for low-end LLMs)
    _PROMPT_TEMPLATE = (
        "You are a cybersecurity IDS analyst. Classify the following "
        "network event in ONE word: 'brute_force', 'credential_stuffing', "
        "'forgotten_password', or 'benign'.\n\n"
        "Event:\n"
        "- Source IP: {src_ip}\n"
        "- Failed SSH logins from this IP: {fail_count}\n"
        "- Time window: {window_sec}s (first seen → last seen)\n"
        "- Process: {comm}\n"
        "- Alert type: {alert_name}\n\n"
        "Reply with ONLY the classification word."
    )

    def __init__(self, use_llm: bool = True, llm_caller: Optional[Callable] = None):
        self.use_llm = use_llm
        self._llm_caller = llm_caller

    async def classify(self, event: IPSEvent) -> str:
        """Return one of: brute_force, credential_stuffing, forgotten_password, benign."""
        if self.use_llm and self._llm_caller:
            try:
                return await self._llm_classify(event)
            except Exception as e:
                logger.warning(f"LLM classification failed, falling back to heuristic: {e}")

        return self._heuristic_classify(event)

    async def _llm_classify(self, event: IPSEvent) -> str:
        window_sec = event.last_seen - event.first_seen if event.last_seen > event.first_seen else 0
        prompt = self._PROMPT_TEMPLATE.format(
            src_ip=event.src_ip,
            fail_count=event.fail_count,
            window_sec=f"{window_sec:.0f}",
            comm=event.comm,
            alert_name=event.alert_name,
        )
        raw = await asyncio.to_thread(self._llm_caller, prompt)
        raw = raw.strip().lower().replace("'", "").replace('"', '')
        for label in ("brute_force", "credential_stuffing", "forgotten_password", "benign"):
            if label in raw:
                return label
        return "unknown"

    @staticmethod
    def _heuristic_classify(event: IPSEvent) -> str:
        """Fast heuristic — no LLM needed."""
        if event.alert_type == ALERT_BRUTE_FORCE:
            return "brute_force"
        if event.fail_count >= 10:
            return "brute_force"
        if event.fail_count >= 3:
            window = event.last_seen - event.first_seen
            if window > 0 and event.fail_count / window > 0.5:
                return "brute_force"
            return "credential_stuffing"
        if event.fail_count <= 2:
            return "forgotten_password"
        return "benign"


# ═══════════════════════════════════════════════════════════════
# IP Blocker (iptables / nftables)
# ═══════════════════════════════════════════════════════════════

class IPBlocker:
    """Executes firewall rules to block malicious IPs."""

    def __init__(self, tool: str = "iptables", dry_run: bool = True,
                 admin_whitelist: Optional[List[str]] = None):
        self.tool = tool
        self.dry_run = dry_run
        self.whitelist = set(admin_whitelist or ["127.0.0.1"])
        self._blocked: set[str] = set()

    def _build_command(self, ip: str) -> str:
        if self.tool == "nftables":
            return f"nft add rule inet filter input ip saddr {ip} drop"
        return f"iptables -A INPUT -s {ip} -j DROP"

    def block(self, ip: str) -> tuple[str, bool]:
        """
        Block an IP.  Returns (command_string, was_executed).
        Never blocks whitelisted IPs.  Skips already-blocked IPs.
        """
        if ip in self.whitelist:
            logger.info(f"IP {ip} is admin-whitelisted — skipping block")
            return f"[WHITELISTED] {ip}", False

        if ip in self._blocked:
            logger.debug(f"IP {ip} already blocked — skipping")
            return f"[ALREADY-BLOCKED] {ip}", False

        cmd = self._build_command(ip)

        if self.dry_run:
            logger.warning(f"[DRY-RUN] Would execute: {cmd}")
            return f"[DRY-RUN] {cmd}", False

        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                self._blocked.add(ip)
                logger.info(f"Blocked IP {ip} via {self.tool}")
                return cmd, True
            else:
                logger.error(f"Failed to block {ip}: {result.stderr}")
                return cmd, False
        except Exception as e:
            logger.error(f"Exception blocking {ip}: {e}")
            return cmd, False

    @property
    def blocked_ips(self) -> set[str]:
        return self._blocked.copy()


# ═══════════════════════════════════════════════════════════════
# Action Logger (JSONL for Manager agent)
# ═══════════════════════════════════════════════════════════════

class ActionLogger:
    """Appends structured JSON actions to a JSONL file."""

    def __init__(self, log_path: str = "./logs/ips_actions.jsonl"):
        self.path = Path(log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log(self, action: IPSAction) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(action.to_json() + "\n")

    def recent(self, count: int = 20) -> List[dict]:
        """Read the last N actions (for Manager review)."""
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        results = []
        for line in lines[-count:]:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return results


# ═══════════════════════════════════════════════════════════════
# Simulation / Fallback — auth.log parser
# ═══════════════════════════════════════════════════════════════

class AuthLogParser:
    """
    Fallback event source: parses /var/log/auth.log for SSH failures.
    Used when eBPF is unavailable (non-root, Termux, non-Linux).
    """

    _FAIL_PATTERN = re.compile(
        r"Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+) port (\d+)"
    )
    _ACCEPT_PATTERN = re.compile(
        r"Accepted password for (\S+) from (\d+\.\d+\.\d+\.\d+) port (\d+)"
    )

    def __init__(self, log_path: str = "/var/log/auth.log"):
        self.log_path = Path(log_path)
        self._last_pos: int = 0
        self._ip_counts: Dict[str, int] = {}  # ip → fail count
        self._ip_first:  Dict[str, float] = {}

    def poll(self) -> List[IPSEvent]:
        """Read new lines from auth.log and return IPSEvents."""
        events: List[IPSEvent] = []
        if not self.log_path.exists():
            return events

        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._last_pos)
                for line in f:
                    ev = self._parse_line(line)
                    if ev:
                        events.append(ev)
                self._last_pos = f.tell()
        except PermissionError:
            logger.debug("Cannot read auth.log — insufficient permissions")
        except Exception as e:
            logger.debug(f"Auth log read error: {e}")

        return events

    def _parse_line(self, line: str) -> Optional[IPSEvent]:
        m = self._FAIL_PATTERN.search(line)
        if m:
            ip = m.group(2)
            port = int(m.group(3))
            now = time.time()

            self._ip_counts[ip] = self._ip_counts.get(ip, 0) + 1
            if ip not in self._ip_first:
                self._ip_first[ip] = now

            count = self._ip_counts[ip]
            alert = ALERT_BRUTE_FORCE if count >= 5 else ALERT_SSH_AUTH_FAIL

            return IPSEvent(
                src_ip=ip,
                dst_port=22,
                src_port=port,
                fail_count=count,
                first_seen=self._ip_first[ip],
                last_seen=now,
                alert_type=alert,
                comm="sshd",
            )

        m = self._ACCEPT_PATTERN.search(line)
        if m:
            ip = m.group(2)
            # Successful login — reset counter
            self._ip_counts.pop(ip, None)
            self._ip_first.pop(ip, None)

        return None


class MockEventSource:
    """
    Generates mock IPS events for testing on any platform.
    Simulates a brute-force attack cycle every ~60 seconds.
    """

    def __init__(self):
        import random
        self._rng = random
        self._cycle = 0

    def poll(self) -> List[IPSEvent]:
        import random
        self._cycle += 1

        if self._cycle % 10 != 0:
            return []

        # Simulate a burst from a random attacker IP
        attacker = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        count = random.choice([1, 2, 3, 5, 8, 12])
        now = time.time()

        alert = ALERT_BRUTE_FORCE if count >= 5 else ALERT_SSH_AUTH_FAIL

        return [IPSEvent(
            src_ip=attacker,
            dst_port=22,
            fail_count=count,
            first_seen=now - count * 5,
            last_seen=now,
            alert_type=alert,
            comm="sshd",
        )]


# ═══════════════════════════════════════════════════════════════
# Main IPS Agent
# ═══════════════════════════════════════════════════════════════

class IPSAgent:
    """
    Autonomous Intrusion Prevention System agent for OmniClaw.

    Lifecycle:
        agent = IPSAgent(config)
        agent.start()           # Background thread
        ...
        agent.stop()

    Integration:
        Registered as Layer 6 in core.security.SecurityLayer.
        Actions are logged to ips_actions.jsonl for Manager review.
    """

    def __init__(self, config: Optional[IPSConfig] = None,
                 llm_caller: Optional[Callable] = None):
        self.config = config or IPSConfig()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Components
        self.blocker = IPBlocker(
            tool=self.config.block_tool,
            dry_run=self.config.dry_run,
            admin_whitelist=self.config.admin_whitelist,
        )
        self.classifier = ThreatClassifier(
            use_llm=self.config.llm_analysis,
            llm_caller=llm_caller,
        )
        self.action_logger = ActionLogger(log_path=self.config.log_file)

        # Event source (eBPF or fallback)
        self._ebpf_available = False
        self._event_source = None
        self._bpf = None
        self._init_event_source()

        # Statistics
        self.stats = {
            "events_processed": 0,
            "blocks_executed": 0,
            "blocks_dry_run": 0,
            "alerts_total": 0,
        }

        mode = "eBPF" if self._ebpf_available else "simulation"
        dry = "DRY-RUN" if self.config.dry_run else "LIVE"
        logger.info(f"IPSAgent initialized — mode={mode}, blocking={dry}, "
                     f"tool={self.config.block_tool}, threshold={self.config.fail_threshold}")

    def _init_event_source(self) -> None:
        """Try eBPF first, then auth.log, then mock events."""
        if platform.system() != "Linux":
            logger.info("Non-Linux OS detected — using simulation mode")
            self._event_source = MockEventSource()
            return

        if os.geteuid() != 0:
            logger.info("Not running as root — falling back to auth.log parser")
            self._event_source = AuthLogParser(self.config.auth_log_path)
            return

        # Try to load eBPF ring buffer via BCC
        try:
            from bcc import BPF
            # We need the compiled monitor.bpf.o; BCC can also inline-compile
            # but for CO-RE we use the pre-compiled object.
            # For simplicity, also support BCC inline mode:
            self._bpf = self._try_bcc_ringbuf()
            if self._bpf:
                self._ebpf_available = True
                logger.info("eBPF IPS monitor attached successfully")
                return
        except ImportError:
            logger.info("BCC not installed — falling back to auth.log parser")
        except Exception as e:
            logger.warning(f"eBPF init failed: {e} — falling back to auth.log")

        self._event_source = AuthLogParser(self.config.auth_log_path)

    def _try_bcc_ringbuf(self):
        """
        Attempt to attach to the eBPF ring buffer from monitor.bpf.c.
        Returns a BCC BPF object if successful, None otherwise.
        """
        try:
            from bcc import BPF

            # Try to find the pre-compiled BPF object
            bpf_obj = Path(__file__).parent.parent.parent / "kernel_bridge" / "build" / "monitor.bpf.o"

            if bpf_obj.exists():
                # Load pre-compiled skeleton
                b = BPF(src_file=str(bpf_obj))
                logger.info(f"Loaded pre-compiled BPF from {bpf_obj}")
                return b

            # Fallback: load the source directly via BCC in-kernel compile
            bpf_src = Path(__file__).parent.parent.parent / "kernel_bridge" / "src" / "bpf" / "monitor.bpf.c"
            if bpf_src.exists():
                logger.info("Pre-compiled BPF not found; BCC inline compile not supported for CO-RE. "
                           "Please compile monitor.bpf.c first (see IPS_README.md).")

            return None

        except Exception as e:
            logger.debug(f"BCC ringbuf setup failed: {e}")
            return None

    # ─────────────────── Lifecycle ───────────────────

    def start(self) -> None:
        """Start the IPS agent in a background daemon thread."""
        if not self.config.enabled:
            logger.info("IPSAgent is disabled in config — not starting")
            return

        if self.running:
            logger.warning("IPSAgent already running")
            return

        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="IPSAgent")
        self._thread.start()
        logger.info("IPSAgent background thread started")

    def stop(self) -> None:
        """Stop the IPS agent gracefully."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("IPSAgent stopped")

    # ─────────────────── Main loop ───────────────────

    def _run_loop(self) -> None:
        """Background polling loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        while self.running:
            try:
                events = self._poll_events()
                if events:
                    self._loop.run_until_complete(self._process_events(events))
            except Exception as e:
                logger.error(f"IPS loop error: {e}")

            time.sleep(self.config.poll_interval)

        self._loop.close()

    def _poll_events(self) -> List[IPSEvent]:
        """Poll the active event source for new IPS alerts."""
        if self._ebpf_available and self._bpf:
            return self._poll_ebpf()
        elif self._event_source:
            return self._event_source.poll()
        return []

    def _poll_ebpf(self) -> List[IPSEvent]:
        """Poll eBPF ring buffer and convert to IPSEvent objects."""
        events: List[IPSEvent] = []
        try:
            self._bpf.ring_buffer_poll(timeout=100)
            # Events are delivered via callback; this is a simplified path.
            # In production, we'd register a callback during init.
        except Exception as e:
            logger.debug(f"eBPF poll error: {e}")
        return events

    async def _process_events(self, events: List[IPSEvent]) -> None:
        """Process a batch of IPS events: classify and act."""
        for event in events:
            self.stats["events_processed"] += 1
            self.stats["alerts_total"] += 1

            # Skip non-actionable alerts
            if event.alert_type == ALERT_TCP_CONNECT:
                continue

            # Classify the threat
            classification = await self.classifier.classify(event)
            logger.debug(f"Event from {event.src_ip}: {event.alert_name} → {classification}")

            # Decide action
            verdict, reason = self._decide_action(event, classification)

            # Execute action
            cmd_str = ""
            executed = False
            if verdict == "block":
                cmd_str, executed = self.blocker.block(event.src_ip)
                if executed:
                    self.stats["blocks_executed"] += 1
                elif self.config.dry_run and event.src_ip not in self.blocker.whitelist:
                    self.stats["blocks_dry_run"] += 1

            # Log structured action
            action = IPSAction(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event=event.to_dict(),
                analysis=classification,
                verdict=verdict,
                command=cmd_str,
                executed=executed,
                dry_run=self.config.dry_run,
                blocked_ip=event.src_ip if verdict == "block" else "",
                reason=reason,
            )
            self.action_logger.log(action)

            if verdict == "block":
                logger.warning(
                    f"IPS {'BLOCKED' if executed else 'WOULD BLOCK'} "
                    f"{event.src_ip} — {reason}"
                )

    def _decide_action(self, event: IPSEvent, classification: str) -> tuple[str, str]:
        """
        Decision matrix:
          brute_force / credential_stuffing → block
          forgotten_password               → monitor (don't block)
          benign / unknown                 → ignore
        """
        if event.alert_type == ALERT_BRUTE_FORCE:
            return "block", f"eBPF brute-force alert: {event.fail_count} failures"

        if classification in ("brute_force", "credential_stuffing"):
            return "block", f"LLM classified as {classification} ({event.fail_count} failures)"

        if classification == "forgotten_password":
            return "monitor", f"Likely forgotten password ({event.fail_count} failures)"

        return "ignore", f"Classification: {classification}"

    # ─────────────────── Public API ───────────────────

    def get_status(self) -> dict:
        """Return current IPS status for dashboard / Manager agent."""
        return {
            "running": self.running,
            "mode": "ebpf" if self._ebpf_available else "simulation",
            "dry_run": self.config.dry_run,
            "block_tool": self.config.block_tool,
            "blocked_ips": list(self.blocker.blocked_ips),
            "admin_whitelist": list(self.blocker.whitelist),
            "stats": dict(self.stats),
        }

    def get_recent_actions(self, count: int = 20) -> List[dict]:
        """Return recent IPS actions for Manager review."""
        return self.action_logger.recent(count)

    def add_to_whitelist(self, ip: str) -> None:
        """Dynamically whitelist an IP (e.g. admin's current IP)."""
        self.blocker.whitelist.add(ip)
        self.config.admin_whitelist.append(ip)
        logger.info(f"Added {ip} to IPS whitelist")

    def set_dry_run(self, enabled: bool) -> None:
        """Toggle dry-run mode at runtime."""
        self.config.dry_run = enabled
        self.blocker.dry_run = enabled
        logger.info(f"IPS dry-run mode {'enabled' if enabled else 'disabled'}")


# ═══════════════════════════════════════════════════════════════
# Module-level convenience — singleton pattern
# ═══════════════════════════════════════════════════════════════

_ips_agent: Optional[IPSAgent] = None


def get_ips_agent(config: Optional[dict] = None,
                  llm_caller: Optional[Callable] = None) -> IPSAgent:
    """Get or create the singleton IPS agent."""
    global _ips_agent
    if _ips_agent is None:
        cfg = IPSConfig.from_dict(config) if config else IPSConfig()
        _ips_agent = IPSAgent(config=cfg, llm_caller=llm_caller)
    return _ips_agent


def ip_to_str(ip_int: int) -> str:
    """Convert a 32-bit integer (network byte order) to dotted-quad string."""
    return socket.inet_ntoa(struct.pack("!I", ip_int))


def str_to_ip(ip_str: str) -> int:
    """Convert dotted-quad string to 32-bit integer (network byte order)."""
    return struct.unpack("!I", socket.inet_aton(ip_str))[0]
