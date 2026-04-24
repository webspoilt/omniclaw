"""
Auditor Agent: Validates simulation output for hallucinations and logical consistency.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List
import re

logger = logging.getLogger(__name__)


@dataclass
class AuditResult:
    passed: bool
    reason: Optional[str] = None
    score: float = 0.0


class Auditor:
    def __init__(self):
        # Could load a small local model for validation; here we use heuristics.
        pass

    def audit(self, simulation_output: dict, context: str) -> AuditResult:
        """
        Perform validation checks:
        - Detect hallucinations (e.g., unrealistic numbers)
        - Check for self-contradictions within an agent's response
        """
        aggregated = simulation_output.get("aggregated", "")
        individual = simulation_output.get("individual", [])

        # Hallucination check
        hallucination = self._detect_hallucinations(aggregated, context)
        if hallucination:
            return AuditResult(passed=False, reason=f"Hallucination: {hallucination}")

        # Self-contradiction check
        for resp in individual:
            if self._self_contradiction(resp):
                return AuditResult(passed=False, reason=f"Self‑contradiction in: {resp[:100]}")

        return AuditResult(passed=True, score=1.0)

    def _detect_hallucinations(self, text: str, context: str) -> Optional[str]:
        """Simple pattern matching for unrealistic claims."""
        text_lower = text.lower()
        # Example: detect absurd Bitcoin prices
        if "bitcoin" in context.lower() and "price of bitcoin is $" in text_lower:
            # In a real system, you'd check against a reasonable range
            match = re.search(r"price of bitcoin is \$(\d+(?:,\d+)?(?:\.\d+)?)", text_lower)
            if match:
                price = float(match.group(1).replace(",", ""))
                if price > 1_000_000:  # arbitrary threshold
                    return "Bitcoin price > $1M"
        return None

    def _self_contradiction(self, text: str) -> bool:
        """Check for contradictory phrases within a single response."""
        text_lower = text.lower()
        if "bullish" in text_lower and "bearish" in text_lower:
            return True
        # Add more patterns as needed
        return False
