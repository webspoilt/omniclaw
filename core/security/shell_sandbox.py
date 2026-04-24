"""
ShellSandbox — Three-tier shell command filtering.

Ported from NanoClaw's security/sandbox.py.
Commands pass through: BLOCKED → CONFIRM → ALLOW pipeline.
Executes in workspace directory with stripped environment.
"""

from __future__ import annotations

import asyncio
import os
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from core.security.risk_engine import RiskEngine

logger = logging.getLogger("OmniClaw.Security.ShellSandbox")


@dataclass
class ShellResult:
    """Result of shell command execution."""
    output: str
    exit_code: int


class ShellSandbox:
    """Sandboxed shell execution with three-tier filtering."""

    # === TIER 1: BLOCKED - Never executed, instant reject ===
    BLOCKED_PATTERNS = [
        r"rm\s+(-[a-zA-Z]*)?rf\s+[/~]",       # rm -rf / or ~
        r"mkfs\.",                               # format disk
        r"dd\s+if=",                             # disk destroy
        r">\s*/dev/sd",                           # overwrite disk
        r"chmod\s+(-R\s+)?777\s+/",              # permissions nuke
        r"curl.*\|\s*(ba)?sh",                    # pipe to shell
        r"wget.*\|\s*(ba)?sh",                    # pipe to shell
        r"python.*-c.*import\s+os",              # python os escape
        r"nc\s+-[le]",                            # netcat listener
        r"ncat\s",                                # ncat
        r"/etc/(passwd|shadow|sudoers)",          # system files
        r"~/.ssh",                                # SSH keys
        r"~/.omniclaw/config",                    # our config
        r"iptables",                              # firewall
        r"ufw\s",                                 # firewall
        r"ssh-keygen",                            # key generation
        r"crontab\s+-[re]",                       # system cron
        r"eval\s*\(",                             # eval injection
        r"exec\s*\(",                             # exec injection
        r"base64.*\|\s*(ba)?sh",                  # encoded execution
        r"history\s",                             # command history
        r"printenv",                              # environment variables
        r"\benv\b",                               # environment variables
        r"set\s*$",                               # shell variables
        r"export\s+.*=",                          # setting env vars
        r"source\s+",                             # sourcing scripts
        r"\.\s+/",                                # dot sourcing
        r"ln\s+(-[a-zA-Z]*)?s\s",                # symlink creation
        r"/proc/",                                # proc filesystem access
        r"/sys/",                                 # sys filesystem access
        r"\bstrace\b",                            # process tracing
        r"\bltrace\b",                            # library tracing
        r"\bgdb\b",                               # debugger
        r"\blldb\b",                              # debugger
        r"\bperf\b",                              # performance tracing
        r"\bdeclare\s+-p",                        # dump shell variables
        r"\bcompgen\b",                           # shell internals
        r"\$\{",                                  # variable expansion
        r"\$\(",                                  # command substitution
        r"`[^`]+`",                               # backtick command substitution
        r"powershell.*-enc",                      # encoded PowerShell
        r"reg\s+(add|delete)",                    # Windows registry
        r"net\s+user",                            # Windows user management
        r"format\s+[a-zA-Z]:",                    # Windows disk format
    ]

    # === TIER 2: CONFIRM - Executed only after user approval ===
    CONFIRM_PATTERNS = [
        r"\brm\s",                    # any delete
        r"\bmv\s",                    # any move/rename
        r"pip\s+install",             # installing packages
        r"apt(-get)?\s+install",      # installing packages
        r"brew\s+install",            # installing packages
        r"npm\s+install",             # installing packages
        r"sudo\s",                    # elevated privileges
        r"kill\s",                    # killing processes
        r"pkill\s",                   # killing processes
        r"systemctl",                 # service management
        r"docker\s",                  # container operations
        r"git\s+push",               # pushing code
        r"git\s+reset.*--hard",       # destructive git
        r"chmod\s",                   # changing permissions
        r"chown\s",                   # changing ownership
        r">\s",                       # output redirection (overwrite)
        r"del\s+/[fqs]",             # Windows delete
        r"rmdir\s+/s",               # Windows rmdir
    ]

    def __init__(self, workspace_dir: str | Path, risk_engine: Optional[RiskEngine] = None):
        self.workspace = Path(workspace_dir).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.risk_engine = risk_engine

        # Pre-compile patterns for performance
        self._blocked_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS
        ]
        self._confirm_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.CONFIRM_PATTERNS
        ]

    _CHAIN_SPLIT = re.compile(r"\s*(?:;|&&|\|\||\|)\s*")

    def _split_commands(self, command: str) -> list[str]:
        """Split a chained command string into individual commands."""
        return [part.strip() for part in self._CHAIN_SPLIT.split(command) if part.strip()]

    def is_blocked(self, command: str) -> tuple[bool, str]:
        """
        Check if command matches blocked patterns.

        Returns:
            (is_blocked, matched_pattern)
        """
        for pattern in self._blocked_compiled:
            if pattern.search(command):
                return True, pattern.pattern
        parts = self._split_commands(command)
        for part in parts:
            for pattern in self._blocked_compiled:
                if pattern.search(part):
                    return True, pattern.pattern
        return False, ""

    def needs_confirmation(self, command: str) -> bool:
        """Check if command needs user confirmation."""
        for pattern in self._confirm_compiled:
            if pattern.search(command):
                return True
        parts = self._split_commands(command)
        for part in parts:
            for pattern in self._confirm_compiled:
                if pattern.search(part):
                    return True
        return False

    async def execute(
        self,
        command: str,
        timeout: int = 30,
        confirm_callback: Optional[Callable] = None,
    ) -> ShellResult:
        """
        Execute command through three-tier filter.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            confirm_callback: Async function for user confirmation

        Returns:
            ShellResult with output and exit code

        Raises:
            SecurityError: If command is blocked
        """
        from core.security.file_guard import SecurityError

        # 1. Check BLOCKED
        is_blocked, pattern = self.is_blocked(command)
        if is_blocked:
            logger.warning(f"BLOCKED command: {command} (pattern: {pattern})")
            if self.risk_engine:
                self.risk_engine.evaluate_action("default", "bash_execute", f"[BLOCKED] {command}")
            raise SecurityError("BLOCKED: dangerous command detected")

        # 1b. Evaluate Risk (Tirreno-style)
        if self.risk_engine:
            risk_result = self.risk_engine.evaluate_action("default", "bash_execute", command)
            if risk_result["status"] == "TERMINATE":
                logger.critical(f"RISK TERMINATE: {command} (Score: {risk_result['score']})")
                raise SecurityError(f"RISK LIMIT EXCEEDED: Command terminated for safety. Score: {risk_result['score']}")
            elif risk_result["status"] == "LOCK" and confirm_callback:
                logger.warning(f"RISK LOCK: {command} (Score: {risk_result['score']})")
                approved = await confirm_callback(
                    f"⚠️ HIGH RISK DETECTED (Score: {risk_result['score']})\n"
                    f"Agent wants to run: `{command}`\n"
                    "Manual override required. Allow?"
                )
                if not approved:
                    return ShellResult(output="Risk Lock: User denied execution", exit_code=-1)

        # 2. Check CONFIRM
        if self.needs_confirmation(command):
            if confirm_callback is None:
                logger.warning(f"DENIED command (no confirmation callback): {command}")
                return ShellResult(
                    output="DENIED: command requires confirmation but no callback available",
                    exit_code=-1,
                )
            approved = await confirm_callback(
                f"Agent wants to run:\n`{command}`\n\nAllow?"
            )
            if not approved:
                return ShellResult(output="User denied execution", exit_code=-1)

        # 3. Execute with sandbox constraints
        try:
            # Use appropriate shell for OS with safe environment
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
                env=self._safe_env(),
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            return ShellResult(
                output=f"TIMEOUT: command exceeded {timeout}s", exit_code=-1
            )
        except Exception as e:
            return ShellResult(output=f"ERROR: {e}", exit_code=-1)

        output = (stdout.decode(errors="replace") + stderr.decode(errors="replace")).strip()

        # Truncate huge outputs
        if len(output) > 10000:
            output = output[:10000] + "\n...[truncated]"

        return ShellResult(output=output, exit_code=process.returncode or 0)

    def _safe_env(self) -> dict[str, str]:
        """Create stripped environment without sensitive variables.

        Returns a minimal, sanitized environment for subprocess execution.
        On Unix: restricts PATH to system dirs and sets SHELL=/bin/sh.
        On Windows: uses System32 PATH and sets COMSPEC to cmd.exe.
        NOTE: This method is only called on Unix systems (inside the
        ``else`` branch of the execute() method), but is kept
        cross-platform-safe so class introspection and future refactors
        do not accidentally surface Unix-only constants on Windows.
        """
        if os.name == "nt":
            # Windows-safe minimal environment
            sys_root = os.environ.get("SystemRoot", r"C:\Windows")
            safe: dict[str, str] = {
                "PATH": (
                    f"{sys_root}\\System32;"
                    f"{sys_root};"
                    f"{sys_root}\\System32\\Wbem"
                ),
                "SYSTEMROOT": sys_root,
                "TEMP": str(self.workspace),
                "TMP": str(self.workspace),
                "USERPROFILE": str(self.workspace),
                "COMSPEC": os.environ.get(
                    "COMSPEC", f"{sys_root}\\System32\\cmd.exe"
                ),
            }
            # Pass through non-sensitive vars if present
            for var in ("LANG", "LC_ALL"):
                if var in os.environ:
                    safe[var] = os.environ[var]
        else:
            # Unix: restrict to minimal safe PATH
            ALLOWED_VARS = ["USER", "LANG", "LC_ALL", "TERM"]
            safe = {}
            for var in ALLOWED_VARS:
                if var in os.environ:
                    safe[var] = os.environ[var]
            safe["PATH"] = "/usr/local/bin:/usr/bin:/bin"
            safe["HOME"] = str(self.workspace)
            safe["SHELL"] = "/bin/sh"
        return safe
