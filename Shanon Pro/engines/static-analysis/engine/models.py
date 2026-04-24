"""
Core data models for the Static Analysis Engine.
Defines the finding schema, severity levels, and CPG context structures.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional


class Severity(Enum):
    """Vulnerability severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(Enum):
    """Confidence level in the finding's validity."""
    CERTAIN = 1.0
    HIGH = 0.85
    MEDIUM = 0.6
    LOW = 0.35
    TENTATIVE = 0.15


class FindingStatus(Enum):
    """Lifecycle status of a finding."""
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True)
class CodeLocation:
    """Precise location of code in the repository."""
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    method_name: Optional[str] = None
    class_name: Optional[str] = None
    
    def to_cpg_coordinates(self) -> dict[str, Any]:
        """Convert to Joern CPG coordinate format."""
        return {
            "filename": self.file_path,
            "linenumber": self.line_start,
            "columnNumber": self.column_start,
            "methodName": self.method_name,
            "className": self.class_name,
        }


@dataclass
class DataflowNode:
    """A single node in a taint/dataflow path."""
    node_id: str                          # CPG internal node ID
    node_type: str                        # CALL, IDENTIFIER, LITERAL, etc.
    code: str                             # Source code snippet
    location: CodeLocation
    semantic_type: Optional[str] = None   # SOURCE, SINK, SANITIZER, PROPAGATOR
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "code": self.code,
            "location": asdict(self.location),
            "semantic_type": self.semantic_type,
        }


@dataclass
class DataflowPath:
    """Complete taint path from source to sink."""
    source: DataflowNode
    sink: DataflowNode
    intermediate_nodes: list[DataflowNode] = field(default_factory=list)
    path_length: int = 0
    
    @property
    def sanitizers(self) -> list[DataflowNode]:
        """Extract all sanitizer nodes from the path."""
        return [n for n in self.intermediate_nodes 
                if n.semantic_type == "SANITIZER"]
    
    @property
    def has_sanitizer(self) -> bool:
        return len(self.sanitizers) > 0
    
    def serialize(self) -> str:
        """Serialize to deterministic string for hashing."""
        nodes = [self.source] + self.intermediate_nodes + [self.sink]
        return json.dumps([n.to_dict() for n in nodes], sort_keys=True)
    
    @property
    def path_hash(self) -> str:
        return hashlib.sha256(self.serialize().encode()).hexdigest()[:32]


@dataclass
class CPGContext:
    """Complete CPG context for a finding — enables reproduction and LLM reasoning."""
    method_ast: str                         # Pretty-printed AST of containing method
    dataflow_path: DataflowPath
    cypher_query: str                       # Query to regenerate this subgraph
    method_signature: Optional[str] = None
    call_site_context: list[str] = field(default_factory=list)
    
    def to_llm_context(self, max_length: int = 8000) -> str:
        """
        Convert CPG context to LLM-optimized text representation.
        Truncates intelligently if exceeding max_length.
        """
        lines = [
            "=== METHOD CONTEXT ===",
            f"Method: {self.method_signature or 'unknown'}",
            "",
            "=== AST SNIPPET ===",
            self.method_ast[:3000],  # Truncate AST if needed
            "",
            "=== DATAFLOW PATH ===",
            f"Source: {self.dataflow_path.source.code}",
            f"  [Type: {self.dataflow_path.source.node_type}]",
            "",
        ]
        
        if self.dataflow_path.intermediate_nodes:
            lines.append("Intermediate nodes:")
            for node in self.dataflow_path.intermediate_nodes[-10:]:  # Last 10
                sanitizer_marker = " [SANITIZER]" if node.semantic_type == "SANITIZER" else ""
                lines.append(f"  -> {node.code}{sanitizer_marker}")
            lines.append("")
        
        lines.extend([
            f"Sink: {self.dataflow_path.sink.code}",
            f"  [Type: {self.dataflow_path.sink.node_type}]",
            "",
            f"Path length: {self.dataflow_path.path_length}",
            f"Has sanitizer: {self.dataflow_path.has_sanitizer}",
            "",
            "=== CYPHER QUERY ===",
            self.cypher_query,
        ])
        
        context = "\n".join(lines)
        if len(context) > max_length:
            # Truncate AST but preserve dataflow path
            context = context[:max_length - 100] + "\n... [truncated]"
        
        return context


@dataclass
class StaticFinding:
    """
    Core finding entity produced by the Static Analysis Engine.
    Designed to be consumed by the Correlation Engine (Stage 3).
    """
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scan_id: Optional[str] = None
    rule_id: str = ""
    vuln_category: str = ""           # sqli, xss, command_injection, etc.
    severity: Severity = Severity.MEDIUM
    confidence: Confidence = Confidence.MEDIUM
    confidence_score: float = 0.0     # Normalized 0.0-1.0
    
    # Location
    location: Optional[CodeLocation] = None
    
    # CPG-derived context
    cpg_context: Optional[CPGContext] = None
    
    # Analysis metadata
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # LLM reasoning output
    llm_analysis: Optional[LLMAnalysis] = None
    
    # Timestamps
    detected_at: datetime = field(default_factory=datetime.utcnow)
    status: FindingStatus = FindingStatus.OPEN
    
    @property
    def evidence_hash(self) -> str:
        """Deterministic hash of finding evidence for integrity verification."""
        content = f"{self.rule_id}:{self.location.file_path if self.location else ''}:"
        content += f"{self.location.line_start if self.location else 0}:"
        content += self.cpg_context.dataflow_path.path_hash if self.cpg_context else ""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON/Protobuf transmission."""
        return {
            "finding_id": self.finding_id,
            "scan_id": self.scan_id,
            "rule_id": self.rule_id,
            "vuln_category": self.vuln_category,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "location": asdict(self.location) if self.location else None,
            "cpg_context": {
                "dataflow_path_hash": self.cpg_context.dataflow_path.path_hash 
                    if self.cpg_context else None,
                "has_sanitizer": self.cpg_context.dataflow_path.has_sanitizer 
                    if self.cpg_context else None,
            },
            "evidence_hash": self.evidence_hash,
            "tags": self.tags,
            "detected_at": self.detected_at.isoformat(),
            "status": self.status.value,
        }
    
    def to_exploitation_queue_item(self) -> dict[str, Any]:
        """Convert to exploitation queue format for Stage 2."""
        return {
            "finding_id": self.finding_id,
            "vuln_type": self.vuln_category,
            "injection_points": {
                "source": self.cpg_context.dataflow_path.source.code 
                    if self.cpg_context else None,
                "sink": self.cpg_context.dataflow_path.sink.code 
                    if self.cpg_context else None,
                "method": self.location.method_name if self.location else None,
                "file": self.location.file_path if self.location else None,
                "line": self.location.line_start if self.location else None,
            },
            "confidence_score": self.confidence_score,
            "llm_assessment": self.llm_analysis.to_dict() if self.llm_analysis else None,
        }


@dataclass
class LLMAnalysis:
    """Structured output from LLM vulnerability reasoning."""
    is_vulnerable: bool
    reasoning: str
    sanitization_gaps: list[SanitizationGap]
    exploitability_assessment: str
    recommended_validations: list[str]  # Strategies for dynamic testing
    raw_response: Optional[str] = None   # Full LLM output for audit
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "is_vulnerable": self.is_vulnerable,
            "reasoning": self.reasoning,
            "sanitization_gaps": [asdict(g) for g in self.sanitization_gaps],
            "exploitability_assessment": self.exploitability_assessment,
            "recommended_validations": self.recommended_validations,
        }


@dataclass
class SanitizationGap:
    """Identified gap in input sanitization."""
    gap_type: str                        # missing_validation, incomplete_escaping, 
                                         # type_juggling, logic_bypass, etc.
    location_description: str
    vulnerable_pattern: str
    recommended_fix: str
    confidence: Confidence = Confidence.MEDIUM
