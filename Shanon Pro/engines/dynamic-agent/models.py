"""
Core data models for the Dynamic Pentesting Agent.
Defines exploit tasks, evidence structures, and agent state machines.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional


class VulnType(Enum):
    """Types of vulnerabilities the agent can test."""
    SQL_INJECTION = "sqli"
    CROSS_SITE_SCRIPTING = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    LDAP_INJECTION = "ldap_injection"
    XML_EXTERNAL_ENTITY = "xxe"
    SERVER_SIDE_REQUEST_FORGERY = "ssrf"
    INSECURE_DESERIALIZATION = "deserialization"
    IDOR = "idor"
    BROKEN_AUTH = "broken_auth"


class ExploitStatus(Enum):
    """Lifecycle status of an exploit attempt."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    VALIDATED = "validated"       # POC confirmed vulnerability
    FAILED = "failed"             # Could not exploit
    ERROR = "error"               # Infrastructure/tooling error
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class POCStatus(Enum):
    """Validation status of a Proof of Concept."""
    UNVALIDATED = "unvalidated"
    CONFIRMED = "confirmed"       # Observable behavior confirms vulnerability
    INCONCLUSIVE = "inconclusive" # Ambiguous results
    FALSE_POSITIVE = "false_positive"
    NEEDS_REVIEW = "needs_review"


@dataclass
class InjectionPoint:
    """A discovered injection point for dynamic testing."""
    point_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parameter_name: str = ""          # Form field, query param, header name
    parameter_location: str = ""      # query, body, header, path, cookie
    parameter_type: str = ""          # string, integer, json, xml
    current_value: str = ""           # Default/sample value
    source_finding_id: Optional[str] = None  # Links to static finding
    context: dict[str, Any] = field(default_factory=dict)
    
    # Discovered during reconnaissance
    reflected: bool = False           # Value appears in response
    stored: bool = False              # Value persists across requests
    filtered_chars: list[str] = field(default_factory=list)
    max_length: Optional[int] = None
    encoding_detected: Optional[str] = None


@dataclass
class ExploitTask:
    """
    Task definition for dynamic exploitation.
    Produced by the Correlation Engine, consumed by the Agent Controller.
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    finding_id: str = ""              # Links to static finding
    scan_id: str = ""
    vuln_type: VulnType = VulnType.SQL_INJECTION
    target_url: str = ""
    target_method: str = "GET"        # HTTP method
    
    # Injection points discovered during static analysis
    injection_points: list[InjectionPoint] = field(default_factory=list)
    
    # LLM-recommended validation strategies
    validation_strategies: list[str] = field(default_factory=list)
    
    # Context from static analysis
    static_context: dict[str, Any] = field(default_factory=dict)
    
    # Execution parameters
    max_attempts: int = 10
    timeout_seconds: int = 300
    delay_ms: int = 100               # Between requests
    follow_redirects: bool = True
    
    # Priority
    priority: int = 5                 # 1-10, lower = higher priority
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    attempts_made: int = 0
    status: ExploitStatus = ExploitStatus.PENDING
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "finding_id": self.finding_id,
            "vuln_type": self.vuln_type.value,
            "target_url": self.target_url,
            "target_method": self.target_method,
            "injection_points": [
                {
                    "parameter_name": p.parameter_name,
                    "parameter_location": p.parameter_location,
                    "parameter_type": p.parameter_type,
                }
                for p in self.injection_points
            ],
            "validation_strategies": self.validation_strategies,
            "max_attempts": self.max_attempts,
            "priority": self.priority,
            "status": self.status.value,
        }


@dataclass
class ValidationEvidence:
    """Immutable evidence package from an exploit attempt."""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attempt_id: str = ""
    
    # Request evidence
    request_url: str = ""
    request_method: str = ""
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: str = ""
    
    # Response evidence
    response_status: int = 0
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body_preview: str = ""   # First 2000 chars
    response_time_ms: int = 0
    
    # Artifacts
    screenshot_path: Optional[str] = None    # Path to PNG screenshot
    har_path: Optional[str] = None           # Path to HAR file
    video_path: Optional[str] = None         # Path to screen recording
    
    # Indicators observed
    indicators: list[str] = field(default_factory=list)
    
    # Cryptographic integrity
    evidence_hash: str = ""
    
    def __post_init__(self):
        if not self.evidence_hash:
            self.evidence_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of evidence for tamper detection."""
        content = f"{self.request_url}:{self.request_method}:{self.response_status}:"
        content += f"{self.response_body_preview}:{','.join(sorted(self.indicators))}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "attempt_id": self.attempt_id,
            "request_url": self.request_url,
            "request_method": self.request_method,
            "response_status": self.response_status,
            "response_time_ms": self.response_time_ms,
            "indicators": self.indicators,
            "screenshot_path": self.screenshot_path,
            "har_path": self.har_path,
            "evidence_hash": self.evidence_hash,
        }


@dataclass
class ExploitAttempt:
    """Record of a single exploit attempt."""
    attempt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    
    # What was tested
    strategy_used: str = ""           # Name of validation strategy
    payload: str = ""                 # The actual payload sent
    injection_point: Optional[InjectionPoint] = None
    
    # Results
    status: ExploitStatus = ExploitStatus.PENDING
    evidence: Optional[ValidationEvidence] = None
    error_message: Optional[str] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> int:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return 0


@dataclass
class ExploitResult:
    """
    Final result of exploit task execution.
    Implements the "POC-or-it-didn't-happen" principle.
    """
    task_id: str = ""
    finding_id: str = ""
    
    # Validation status
    status: ExploitStatus = ExploitStatus.PENDING
    poc_status: POCStatus = POCStatus.UNVALIDATED
    
    # Evidence
    attempts: list[ExploitAttempt] = field(default_factory=list)
    confirmed_evidence: Optional[ValidationEvidence] = None
    
    # Summary
    confidence_score: float = 0.0     # 0.0-1.0 exploit confidence
    summary: str = ""
    reproduction_steps: str = ""      # Human-readable steps to reproduce
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @property
    def is_validated(self) -> bool:
        """True only if vulnerability was dynamically confirmed."""
        return self.poc_status == POCStatus.CONFIRMED and self.confirmed_evidence is not None
    
    @property
    def duration_ms(self) -> int:
        if self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "finding_id": self.finding_id,
            "status": self.status.value,
            "poc_status": self.poc_status.value,
            "is_validated": self.is_validated,
            "confidence_score": self.confidence_score,
            "summary": self.summary,
            "reproduction_steps": self.reproduction_steps,
            "attempts_count": len(self.attempts),
            "duration_ms": self.duration_ms,
            "confirmed_evidence": self.confirmed_evidence.to_dict() if self.confirmed_evidence else None,
        }
