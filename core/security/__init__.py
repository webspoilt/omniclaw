"""
OmniClaw Security Module
========================
Multi-layered security system inspired by NanoClaw's defense-in-depth approach.

Layers:
1. FileGuard      - Workspace-scoped file access
2. ShellSandbox   - 3-tier command filtering (blocked/confirm/allow)
3. PromptGuard    - Prompt injection detection & output sanitization
4. SessionBudget  - Rate limiting, cost tracking, runaway prevention
5. SecurityDoctor - Installation security audit
"""

from core.security.file_guard import FileGuard
from core.security.shell_sandbox import ShellSandbox, ShellResult
from core.security.prompt_guard import PromptGuard
from core.security.session_budget import SessionBudget, SessionTracker

import logging

logger = logging.getLogger("OmniClaw.Security")


class SecurityLayer:
    """Unified security layer combining all guards."""

    def __init__(self, workspace_dir: str = "./workspace"):
        self.file_guard = FileGuard(workspace_dir)
        self.shell_sandbox = ShellSandbox(workspace_dir)
        self.prompt_guard = PromptGuard()
        self.session_budget = SessionBudget()
        self._sessions: dict[str, SessionTracker] = {}
        logger.info("SecurityLayer initialized (5 layers active)")

    def get_session(self, session_id: str) -> SessionTracker:
        """Get or create a session tracker."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionTracker(session_id=session_id)
        return self._sessions[session_id]

    def check_budget(self, session_id: str) -> tuple[bool, str]:
        """Check if session is within budget."""
        session = self.get_session(session_id)
        return self.session_budget.check_iteration(session)

    def get_status(self) -> dict:
        """Get security status summary."""
        return {
            "layers_active": 5,
            "workspace": str(self.file_guard.workspace),
            "active_sessions": len(self._sessions),
            "blocked_patterns": len(self.shell_sandbox.BLOCKED_PATTERNS),
            "confirm_patterns": len(self.shell_sandbox.CONFIRM_PATTERNS),
            "injection_patterns": len(self.prompt_guard.INJECTION_PATTERNS),
        }


__all__ = [
    "SecurityLayer",
    "FileGuard",
    "ShellSandbox",
    "ShellResult",
    "PromptGuard",
    "SessionBudget",
    "SessionTracker",
]
