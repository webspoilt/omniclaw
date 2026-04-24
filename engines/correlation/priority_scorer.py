"""
Priority Scorer — Multi-factor risk scoring for exploit queue ordering.

Combines multiple dimensions into a final priority score:
- Severity from static analysis
- Reachability confidence
- Exploitability assessment from LLM
- Asset criticality
- Business impact
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .reachability import PathResult, ReachabilityType

logger = logging.getLogger(__name__)


class PriorityLevel(Enum):
    """Priority levels for exploitation queue."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    DEFERRED = 5


@dataclass
class PriorityResult:
    """Result of priority scoring."""
    finding_id: str
    priority: PriorityLevel
    score: float                  # 0.0-100.0 composite score
    
    # Component scores
    severity_score: float = 0.0   # 0-25
    reachability_score: float = 0.0  # 0-25
    exploitability_score: float = 0.0  # 0-25
    confidence_score: float = 0.0  # 0-25
    
    # Justification
    rationale: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "priority": self.priority.value,
            "priority_name": self.priority.name,
            "score": round(self.score, 2),
            "component_scores": {
                "severity": round(self.severity_score, 2),
                "reachability": round(self.reachability_score, 2),
                "exploitability": round(self.exploitability_score, 2),
                "confidence": round(self.confidence_score, 2),
            },
            "rationale": self.rationale,
        }


class PriorityScorer:
    """
    Multi-factor priority scoring engine.
    
    Scoring dimensions (each 0-25, total 0-100):
    - Severity: Static analysis severity (critical=25, high=20, medium=12, low=5)
    - Reachability: Path from HTTP entrypoint (direct=25, one-hop=18, multi-hop=10)
    - Exploitability: LLM assessment of exploit difficulty
    - Confidence: Overall confidence in the finding
    
    Priority thresholds:
    - CRITICAL: score >= 80
    - HIGH: score >= 60
    - MEDIUM: score >= 40
    - LOW: score >= 20
    - DEFERRED: score < 20
    """
    
    # Severity weights
    SEVERITY_SCORES = {
        "critical": 25,
        "high": 20,
        "medium": 12,
        "low": 5,
        "info": 0,
    }
    
    # Reachability weights
    REACHABILITY_SCORES = {
        ReachabilityType.DIRECT: 25,
        ReachabilityType.ONE_HOP: 18,
        ReachabilityType.CONDITIONAL: 12,
        ReachabilityType.MULTI_HOP: 8,
        ReachabilityType.UNKNOWN: 10,
        ReachabilityType.UNREACHABLE: 0,
    }
    
    # Priority thresholds
    PRIORITY_THRESHOLDS = [
        (80, PriorityLevel.CRITICAL),
        (60, PriorityLevel.HIGH),
        (40, PriorityLevel.MEDIUM),
        (20, PriorityLevel.LOW),
        (0, PriorityLevel.DEFERRED),
    ]
    
    def score(
        self,
        finding: dict[str, Any],
        reachability: PathResult,
    ) -> PriorityResult:
        """
        Calculate priority score for a finding.
        
        Args:
            finding: Static finding from PostgreSQL
            reachability: Reachability analysis result
            
        Returns:
            PriorityResult with composite score and level
        """
        finding_id = finding["finding_id"]
        rationale = []
        
        # 1. Severity score (0-25)
        severity = finding.get("severity", "medium")
        severity_score = self.SEVERITY_SCORES.get(severity, 12)
        rationale.append(f"Severity '{severity}' = {severity_score}/25")
        
        # 2. Reachability score (0-25)
        if reachability.is_reachable:
            reachability_score = self.REACHABILITY_SCORES.get(
                reachability.reachability_type, 5
            )
            rationale.append(
                f"Reachability '{reachability.reachability_type.value}' = {reachability_score}/25"
            )
        else:
            reachability_score = 0
            rationale.append("Unreachable = 0/25")
        
        # 3. Exploitability score (0-25)
        exploitability_score = self._calculate_exploitability(
            finding, reachability
        )
        rationale.append(f"Exploitability = {exploitability_score}/25")
        
        # 4. Confidence score (0-25)
        confidence_score = self._calculate_confidence(finding, reachability)
        rationale.append(f"Confidence = {confidence_score}/25")
        
        # Composite score
        total_score = (
            severity_score +
            reachability_score +
            exploitability_score +
            confidence_score
        )
        
        # Determine priority level
        priority = self._score_to_priority(total_score)
        
        # Adjust for unreachable findings
        if not reachability.is_reachable:
            priority = PriorityLevel.DEFERRED
            rationale.append("DEPRIORITIZED: Not reachable from HTTP entrypoints")
        
        rationale.append(f"TOTAL SCORE: {total_score}/100 -> {priority.name}")
        
        return PriorityResult(
            finding_id=finding_id,
            priority=priority,
            score=total_score,
            severity_score=severity_score,
            reachability_score=reachability_score,
            exploitability_score=exploitability_score,
            confidence_score=confidence_score,
            rationale=rationale,
        )
    
    def _calculate_exploitability(
        self,
        finding: dict[str, Any],
        reachability: PathResult,
    ) -> float:
        """
        Calculate exploitability score based on finding characteristics.
        """
        score = 12.5  # Base score
        
        # Boost for findings without sanitizers
        if not finding.get("has_sanitizer", True):
            score += 7.5
        
        # Boost for known vulnerability patterns
        vuln_boosts = {
            "sqli": 5,
            "xss": 4,
            "command_injection": 5,
            "path_traversal": 3,
        }
        vuln_category = finding.get("vuln_category", "")
        score += vuln_boosts.get(vuln_category, 0)
        
        # Penalty for complex paths
        if reachability.path_length > 5:
            score -= 5
        
        # Penalty for conditional reachability
        if reachability.reachability_type == ReachabilityType.CONDITIONAL:
            score -= 3
            if reachability.conditions:
                score -= len(reachability.conditions)
        
        return max(0, min(25, score))
    
    def _calculate_confidence(
        self,
        finding: dict[str, Any],
        reachability: PathResult,
    ) -> float:
        """
        Calculate confidence score based on evidence quality.
        """
        score = 12.5  # Base score
        
        # Static analysis confidence
        static_confidence = finding.get("confidence_score", 0.5)
        score += static_confidence * 12.5
        
        # Reachability confidence
        score += reachability.confidence * 5
        
        # Penalty for unknown reachability
        if reachability.reachability_type == ReachabilityType.UNKNOWN:
            score -= 5
        
        # Boost for findings with CPG data
        if finding.get("cpg_context") and finding.get("cypher_query"):
            score += 3
        
        # Boost for findings with dataflow hash
        if finding.get("dataflow_hash"):
            score += 2
        
        return max(0, min(25, score))
    
    def _score_to_priority(self, score: float) -> PriorityLevel:
        """Convert numeric score to priority level."""
        for threshold, level in self.PRIORITY_THRESHOLDS:
            if score >= threshold:
                return level
        return PriorityLevel.DEFERRED
    
    def score_batch(
        self,
        findings: list[dict[str, Any]],
        reachabilities: list[PathResult],
    ) -> list[PriorityResult]:
        """
        Score multiple findings.
        
        Args:
            findings: List of static findings
            reachabilities: List of reachability results (same order)
            
        Returns:
            List of PriorityResults
        """
        results = []
        for finding, reachability in zip(findings, reachabilities):
            try:
                result = self.score(finding, reachability)
                results.append(result)
            except Exception as e:
                logger.error(f"Priority scoring failed for {finding['finding_id']}: {e}")
                results.append(PriorityResult(
                    finding_id=finding["finding_id"],
                    priority=PriorityLevel.MEDIUM,
                    score=40,
                    rationale=[f"Scoring error: {e}"],
                ))
        
        return results
