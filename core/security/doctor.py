"""
SecurityDoctor — Security audit diagnostic for OmniClaw installation.

Inspired by NanoClaw's security/doctor.py.
Checks workspace permissions, config safety, exposed secrets, etc.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("OmniClaw.Security.Doctor")


class SecurityDoctor:
    """Security audit diagnostic."""

    def __init__(self, workspace_dir: str | Path = "./workspace", config_path: Optional[str] = None):
        self.workspace = Path(workspace_dir).resolve()
        self.config_path = config_path
        self.issues: list[dict] = []
        self.warnings: list[dict] = []
        self.passed: list[str] = []

    def run_audit(self) -> dict:
        """
        Run full security audit.

        Returns:
            Audit report dict
        """
        self.issues.clear()
        self.warnings.clear()
        self.passed.clear()

        self._check_workspace()
        self._check_env_exposure()
        self._check_config_safety()
        self._check_skill_directory()

        return {
            "status": "PASS" if not self.issues else "FAIL",
            "issues": self.issues,
            "warnings": self.warnings,
            "passed": self.passed,
            "summary": self._summary(),
        }

    def _check_workspace(self):
        """Check workspace directory exists and is properly set up."""
        if not self.workspace.exists():
            self.issues.append({
                "check": "workspace_exists",
                "message": f"Workspace directory does not exist: {self.workspace}",
                "severity": "HIGH",
            })
            return

        self.passed.append("Workspace directory exists")

        # On Unix, check permissions
        if os.name != "nt":
            try:
                import stat
                mode = self.workspace.stat().st_mode
                if mode & (stat.S_IWGRP | stat.S_IWOTH):
                    self.warnings.append({
                        "check": "workspace_permissions",
                        "message": "Workspace is writable by group/others",
                        "severity": "MEDIUM",
                    })
                else:
                    self.passed.append("Workspace permissions OK")
            except Exception:
                pass

    def _check_env_exposure(self):
        """Check for exposed API keys in environment."""
        sensitive_vars = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY",
            "DEEPSEEK_API_KEY", "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN",
            "TELEGRAM_BOT_TOKEN",
        ]

        exposed = []
        for var in sensitive_vars:
            if var in os.environ:
                exposed.append(var)

        if exposed:
            self.warnings.append({
                "check": "env_exposure",
                "message": f"API keys found in environment: {', '.join(exposed)}. Consider using a config file instead.",
                "severity": "LOW",
            })
        else:
            self.passed.append("No API keys exposed in environment")

    def _check_config_safety(self):
        """Check config file permissions."""
        if not self.config_path:
            return

        config = Path(self.config_path)
        if not config.exists():
            return

        if os.name != "nt":
            try:
                import stat
                mode = config.stat().st_mode
                if mode & stat.S_IROTH:
                    self.warnings.append({
                        "check": "config_readable",
                        "message": f"Config file is world-readable: {self.config_path}",
                        "severity": "MEDIUM",
                    })
                else:
                    self.passed.append("Config file permissions OK")
            except Exception:
                pass

    def _check_skill_directory(self):
        """Check skill directory safety."""
        skills_dir = self.workspace.parent / "skills"
        if not skills_dir.exists():
            return

        if os.name != "nt":
            try:
                import stat
                mode = skills_dir.stat().st_mode
                if mode & (stat.S_IWGRP | stat.S_IWOTH):
                    self.issues.append({
                        "check": "skills_permissions",
                        "message": "Skills directory writable by group/others — risk of code injection",
                        "severity": "HIGH",
                    })
                else:
                    self.passed.append("Skills directory permissions OK")
            except Exception:
                pass

    def _summary(self) -> str:
        """Generate human-readable summary."""
        total = len(self.issues) + len(self.warnings) + len(self.passed)
        lines = [f"Security Audit: {len(self.passed)}/{total} checks passed"]

        if self.issues:
            lines.append(f"  ❌ {len(self.issues)} issue(s) found")
        if self.warnings:
            lines.append(f"  ⚠️  {len(self.warnings)} warning(s)")

        return "\n".join(lines)
