"""
SessionBudget — Rate limiting and session budget management.

Ported from NanoClaw's security/budget.py.
Prevents runaway loops, excessive API costs, and abuse.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("OmniClaw.Security.SessionBudget")


@dataclass
class SessionTracker:
    """Tracks resource usage for a single session."""

    session_id: str
    start_time: float = field(default_factory=time.time)
    iterations: int = 0
    total_tokens: int = 0
    tool_calls_this_minute: int = 0
    shell_calls: int = 0
    last_minute_reset: float = field(default_factory=time.time)

    def add_tokens(self, tokens: int) -> None:
        """Add tokens to session total."""
        self.total_tokens += tokens

    def increment_iterations(self) -> None:
        """Increment iteration count."""
        self.iterations += 1

    def increment_tool_calls(self) -> None:
        """Increment tool call count with per-minute reset."""
        now = time.time()
        if now - self.last_minute_reset > 60:
            self.tool_calls_this_minute = 0
            self.last_minute_reset = now
        self.tool_calls_this_minute += 1

    def increment_shell_calls(self) -> None:
        """Increment shell call count."""
        self.shell_calls += 1

    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def elapsed_ms(self) -> int:
        """Elapsed time in milliseconds."""
        return int(self.elapsed * 1000)


class SessionBudget:
    """Prevent runaway loops and excessive API costs."""

    def __init__(
        self,
        max_iterations: int = 15,
        max_tokens_per_session: int = 50000,
        max_tool_calls_per_minute: int = 20,
        max_shell_per_message: int = 5,
        session_timeout: int = 300,
    ):
        self.max_iterations = max_iterations
        self.max_tokens_per_session = max_tokens_per_session
        self.max_tool_calls_per_minute = max_tool_calls_per_minute
        self.max_shell_per_message = max_shell_per_message
        self.session_timeout = session_timeout

    def check_iteration(self, session: SessionTracker) -> tuple[bool, str]:
        """
        Check if session is within budget.

        Returns:
            (allowed, reason) tuple
        """
        if session.iterations >= self.max_iterations:
            return False, f"Max iterations ({self.max_iterations}) reached"

        if session.total_tokens >= self.max_tokens_per_session:
            return False, f"Token budget ({self.max_tokens_per_session}) exceeded"

        if session.tool_calls_this_minute >= self.max_tool_calls_per_minute:
            return False, f"Rate limit: {self.max_tool_calls_per_minute} tools/min"

        if session.shell_calls >= self.max_shell_per_message:
            return False, f"Shell limit: max {self.max_shell_per_message} per message"

        if session.elapsed > self.session_timeout:
            return False, f"Session timeout: {self.session_timeout}s"

        return True, ""

    def get_cost_estimate(self, session: SessionTracker) -> dict:
        """Estimate cost based on token usage."""
        cost_per_million = 3.0  # Conservative estimate
        cost_per_token = cost_per_million / 1_000_000

        return {
            "tokens_used": session.total_tokens,
            "estimated_cost_usd": round(session.total_tokens * cost_per_token, 4),
            "budget_remaining_pct": max(
                0,
                (1 - session.total_tokens / self.max_tokens_per_session) * 100,
            ),
        }
