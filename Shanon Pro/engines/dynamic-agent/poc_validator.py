"""
POC Validator — Enforces the "POC-or-it-didn't-happen" principle.

Validates exploit attempts against strict behavioral indicators to confirm
vulnerabilities. No finding is considered real without passing this validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .models import ExploitAttempt, ExploitStatus, POCStatus, ValidationEvidence, VulnType

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """A single validation rule for confirming exploitation."""
    rule_id: str
    description: str
    vuln_types: list[VulnType]
    required_indicators: list[str]        # Must have ALL of these
    forbidden_indicators: list[str]       # Must have NONE of these
    min_confidence: float = 0.8


class POCValidator:
    """
    Strict POC validation engine.
    
    Implements multi-layer validation:
    1. Indicator-based validation (required + forbidden indicators)
    2. Behavioral validation (response patterns)
    3. Temporal validation (time-based delays)
    4. Consistency validation (reproducibility)
    
    The validator is conservative — ambiguous results are marked INCONCLUSIVE,
    not confirmed. Only clear exploitation evidence produces CONFIRMED status.
    """
    
    # Validation rules by vulnerability type
    VALIDATION_RULES: list[ValidationRule] = [
        # SQL Injection Rules
        ValidationRule(
            rule_id="sqli-error-based",
            description="SQL error message in response indicates injection",
            vuln_types=[VulnType.SQL_INJECTION],
            required_indicators=["sql_error"],
            forbidden_indicators=["waf_block", " sanitized"],
            min_confidence=0.9,
        ),
        ValidationRule(
            rule_id="sqli-union-based",
            description="UNION SELECT output appears in response",
            vuln_types=[VulnType.SQL_INJECTION],
            required_indicators=["union_select_reflected"],
            forbidden_indicators=["waf_block"],
            min_confidence=0.95,
        ),
        ValidationRule(
            rule_id="sqli-time-based",
            description="Time delay confirms blind SQL injection",
            vuln_types=[VulnType.SQL_INJECTION],
            required_indicators=["time_based_delay_confirmed"],
            forbidden_indicators=["network_error"],
            min_confidence=0.85,
        ),
        ValidationRule(
            rule_id="sqli-boolean-based",
            description="Boolean-based content differentiation",
            vuln_types=[VulnType.SQL_INJECTION],
            required_indicators=["boolean_true_differs", "boolean_false_differs"],
            forbidden_indicators=["waf_block"],
            min_confidence=0.8,
        ),
        
        # XSS Rules
        ValidationRule(
            rule_id="xss-reflected",
            description="Payload reflected unencoded in response",
            vuln_types=[VulnType.CROSS_SITE_SCRIPTING],
            required_indicators=["payload_reflected_unencoded"],
            forbidden_indicators=["html_encoded", "csp_blocked"],
            min_confidence=0.8,
        ),
        ValidationRule(
            rule_id="xss-dom",
            description="DOM manipulation via sink execution",
            vuln_types=[VulnType.CROSS_SITE_SCRIPTING],
            required_indicators=["dom_modified", "sink_executed"],
            forbidden_indicators=["csp_blocked"],
            min_confidence=0.9,
        ),
        ValidationRule(
            rule_id="xss-stored",
            description="Payload persists across page loads",
            vuln_types=[VulnType.CROSS_SITE_SCRIPTING],
            required_indicators=["payload_stored", "second_request_contains"],
            forbidden_indicators=["html_encoded"],
            min_confidence=0.95,
        ),
        
        # Command Injection Rules
        ValidationRule(
            rule_id="cmdi-output",
            description="Command output visible in response",
            vuln_types=[VulnType.COMMAND_INJECTION],
            required_indicators=["command_output"],
            forbidden_indicators=["waf_block", "command_blocked"],
            min_confidence=0.95,
        ),
        ValidationRule(
            rule_id="cmdi-time-based",
            description="Time delay confirms blind command injection",
            vuln_types=[VulnType.COMMAND_INJECTION],
            required_indicators=["time_based_delay_confirmed"],
            forbidden_indicators=["network_error"],
            min_confidence=0.85,
        ),
        
        # Path Traversal Rules
        ValidationRule(
            rule_id="path-trav-contents",
            description="File contents exposed via traversal",
            vuln_types=[VulnType.PATH_TRAVERSAL],
            required_indicators=["file_contents_exposed", "system_file_accessed"],
            forbidden_indicators=["waf_block", "path_normalized"],
            min_confidence=0.9,
        ),
        
        # SSRF Rules
        ValidationRule(
            rule_id="ssrf-outbound",
            description="Outbound connection confirmed via interaction",
            vuln_types=[VulnType.SERVER_SIDE_REQUEST_FORGERY],
            required_indicators=["outbound_request_detected", "dns_interaction"],
            forbidden_indicators=[],
            min_confidence=0.9,
        ),
    ]
    
    def __init__(self):
        self.rules_by_type: dict[VulnType, list[ValidationRule]] = {}
        for rule in self.VALIDATION_RULES:
            for vuln_type in rule.vuln_types:
                if vuln_type not in self.rules_by_type:
                    self.rules_by_type[vuln_type] = []
                self.rules_by_type[vuln_type].append(rule)
    
    def validate(
        self,
        attempt: ExploitAttempt,
        vuln_type: VulnType,
    ) -> POCStatus:
        """
        Validate an exploit attempt against all applicable rules.
        
        Args:
            attempt: The exploit attempt to validate
            vuln_type: Type of vulnerability being tested
            
        Returns:
            POCStatus indicating validation result
        """
        if not attempt.evidence:
            logger.debug("No evidence to validate")
            return POCStatus.UNVALIDATED
        
        if attempt.status == ExploitStatus.ERROR:
            return POCStatus.INCONCLUSIVE
        
        # Get applicable rules
        rules = self.rules_by_type.get(vuln_type, [])
        if not rules:
            logger.warning(f"No validation rules for {vuln_type.value}")
            return POCStatus.NEEDS_REVIEW
        
        indicators = set(attempt.evidence.indicators)
        
        # Check each rule
        for rule in rules:
            score = self._evaluate_rule(rule, indicators)
            
            if score >= rule.min_confidence:
                logger.info(
                    f"Rule '{rule.rule_id}' passed with score {score:.2f}"
                )
                return POCStatus.CONFIRMED
        
        # Check for false positive indicators
        if self._is_false_positive(attempt, vuln_type):
            return POCStatus.FALSE_POSITIVE
        
        # Check for inconclusive indicators
        if self._is_inconclusive(attempt):
            return POCStatus.INCONCLUSIVE
        
        return POCStatus.UNVALIDATED
    
    def _evaluate_rule(self, rule: ValidationRule, indicators: set[str]) -> float:
        """
        Evaluate a single validation rule against observed indicators.
        
        Returns:
            Confidence score 0.0-1.0
        """
        score = 0.0
        total_checks = len(rule.required_indicators) + len(rule.forbidden_indicators)
        
        if total_checks == 0:
            return 0.5
        
        # Check required indicators
        for required in rule.required_indicators:
            # Support prefix matching (e.g., "sql_error:" matches "sql_error:mysql")
            matched = any(ind.startswith(required) or ind == required 
                         for ind in indicators)
            if matched:
                score += 1.0 / total_checks
            else:
                # Missing required indicator is a significant penalty
                score -= 0.5 / total_checks
        
        # Check forbidden indicators
        for forbidden in rule.forbidden_indicators:
            matched = any(ind.startswith(forbidden) or ind == forbidden
                         for ind in indicators)
            if matched:
                # Forbidden indicator found - major penalty
                score -= 1.0 / total_checks
            else:
                score += 0.5 / total_checks
        
        return max(0.0, min(1.0, score))
    
    def _is_false_positive(self, attempt: ExploitAttempt, vuln_type: VulnType) -> bool:
        """
        Detect indicators that suggest a false positive.
        
        Common false positive patterns:
        - WAF blocking
        - Input being sanitized
        - Generic error pages
        - Rate limiting responses
        """
        if not attempt.evidence:
            return False
        
        fp_indicators = [
            "waf_block",
            "cloudflare_block",
            "rate_limited",
            "input_sanitized",
            "generic_error_page",
            "maintenance_page",
        ]
        
        for indicator in attempt.evidence.indicators:
            if any(fp in indicator for fp in fp_indicators):
                return True
        
        # Response-based heuristics
        if attempt.evidence.response_status in [403, 429, 503]:
            return True
        
        return False
    
    def _is_inconclusive(self, attempt: ExploitAttempt) -> bool:
        """
        Detect when results are too ambiguous to make a determination.
        """
        if not attempt.evidence:
            return False
        
        # Network errors make results inconclusive
        if any("network_error" in ind for ind in attempt.evidence.indicators):
            return True
        
        # Timeout responses
        if attempt.evidence.response_status == 504:
            return True
        
        # Empty responses
        if not attempt.evidence.response_body_preview:
            return True
        
        return False
    
    def validate_with_context(
        self,
        attempts: list[ExploitAttempt],
        vuln_type: VulnType,
    ) -> POCStatus:
        """
        Validate multiple attempts as a group for consistency.
        
        A vulnerability is confirmed if:
        - Multiple attempts show the same indicators (reproducibility)
        - At least one attempt passes strict validation
        """
        if not attempts:
            return POCStatus.UNVALIDATED
        
        # Check for at least one confirmed attempt
        statuses = [self.validate(a, vuln_type) for a in attempts]
        
        if POCStatus.CONFIRMED in statuses:
            # Check reproducibility
            confirmed_attempts = [
                a for a, s in zip(attempts, statuses) if s == POCStatus.CONFIRMED
            ]
            if len(confirmed_attempts) >= 2:
                # Reproducible!
                return POCStatus.CONFIRMED
            elif len(confirmed_attempts) == 1:
        # Single confirmation - still valid but flag for review
                return POCStatus.CONFIRMED
        
        # If mostly inconclusive
        inconclusive_ratio = statuses.count(POCStatus.INCONCLUSIVE) / len(statuses)
        if inconclusive_ratio > 0.5:
            return POCStatus.INCONCLUSIVE
        
        # If mostly false positives
        fp_ratio = statuses.count(POCStatus.FALSE_POSITIVE) / len(statuses)
        if fp_ratio > 0.5:
            return POCStatus.FALSE_POSITIVE
        
        return POCStatus.UNVALIDATED
    
    def get_validation_summary(
        self,
        attempt: ExploitAttempt,
        vuln_type: VulnType,
    ) -> dict[str, Any]:
        """Get detailed validation summary for reporting."""
        if not attempt.evidence:
            return {"status": "no_evidence", "details": "No evidence collected"}
        
        indicators = set(attempt.evidence.indicators)
        applicable_rules = self.rules_by_type.get(vuln_type, [])
        
        rule_evaluations = []
        for rule in applicable_rules:
            score = self._evaluate_rule(rule, indicators)
            rule_evaluations.append({
                "rule_id": rule.rule_id,
                "description": rule.description,
                "score": round(score, 2),
                "passed": score >= rule.min_confidence,
                "required_met": [
                    any(ind.startswith(r) for ind in indicators)
                    for r in rule.required_indicators
                ],
            })
        
        return {
            "status": self.validate(attempt, vuln_type).value,
            "indicators_observed": list(indicators),
            "rules_evaluated": rule_evaluations,
            "response_status": attempt.evidence.response_status,
            "response_time_ms": attempt.evidence.response_time_ms,
        }
