"""
Correlation Engine — Central orchestrator for Stage 3.

Bridges static analysis findings to dynamic exploitation:
1. Ingests findings from PostgreSQL
2. Analyzes reachability from HTTP entrypoints
3. Scores priority for each finding
4. Generates and populates the Exploitation Queue

Implements the intelligence layer that ensures only actionable,
reachable vulnerabilities are sent for dynamic validation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .exploit_queue import ExploitQueueManager, QueueItem, QueuePriority
from .postgres_client import PostgresClient
from .priority_scorer import PriorityScorer, PriorityResult, PriorityLevel
from .reachability import PathResult, ReachabilityAnalyzer, ReachabilityType

logger = logging.getLogger(__name__)


@dataclass
class CorrelationConfig:
    """Configuration for the Correlation Engine."""
    # Ingestion
    min_confidence_threshold: float = 0.3
    vuln_categories: list[str] = field(default_factory=lambda: [
        "sqli", "xss", "command_injection", "path_traversal", "ssrf", "idor", "broken_auth"
    ])
    
    # Reachability
    skip_unreachable: bool = True       # Don't queue unreachable findings
    unknown_reachability_default: bool = True  # Assume reachable if unknown
    
    # Priority
    critical_priority_threshold: float = 80
    high_priority_threshold: float = 60
    
    # Queue
    max_queue_size: int = 1000
    enable_deduplication: bool = True


@dataclass
class CorrelationReport:
    """Comprehensive report of correlation execution."""
    scan_id: str
    
    # Ingestion stats
    total_findings: int = 0
    findings_ingested: int = 0
    findings_filtered: int = 0
    
    # Reachability stats
    reachable_count: int = 0
    unreachable_count: int = 0
    unknown_count: int = 0
    
    # Priority distribution
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    deferred_count: int = 0
    
    # Queue stats
    queued_count: int = 0
    skipped_count: int = 0
    
    # Timing
    execution_time_ms: int = 0
    
    # Details
    correlation_details: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "ingestion": {
                "total_findings": self.total_findings,
                "ingested": self.findings_ingested,
                "filtered": self.findings_filtered,
            },
            "reachability": {
                "reachable": self.reachable_count,
                "unreachable": self.unreachable_count,
                "unknown": self.unknown_count,
            },
            "priority_distribution": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "deferred": self.deferred_count,
            },
            "queue": {
                "queued": self.queued_count,
                "skipped": self.skipped_count,
            },
            "execution_time_ms": self.execution_time_ms,
            "errors": self.errors,
        }


class CorrelationEngine:
    """
    Correlation Engine — The intelligence backbone of Shannon Pro.
    
    Transforms raw static analysis findings into an ordered exploitation queue
    through reachability analysis and risk scoring.
    
    Pipeline:
    1. INGEST: Pull findings from PostgreSQL
    2. ANALYZE: Compute reachability from HTTP entrypoints
    3. SCORE: Calculate composite risk priority
    4. QUEUE: Generate and enqueue Exploitation Tasks
    
    Usage:
        engine = CorrelationEngine(config, postgres_client, queue_manager)
        report = await engine.correinate_scan(scan_id)
    """
    
    def __init__(
        self,
        config: CorrelationConfig,
        postgres_client: PostgresClient,
        queue_manager: ExploitQueueManager,
    ):
        self.config = config
        self.postgres = postgres_client
        self.queue = queue_manager
        self.reachability = ReachabilityAnalyzer()
        self.scorer = PriorityScorer()
    
    async def correlate_scan(
        self,
        scan_id: str,
        target_url: Optional[str] = None,
    ) -> CorrelationReport:
        """
        Execute full correlation pipeline for a scan.
        
        Args:
            scan_id: Scan identifier
            target_url: Base URL of application (for dynamic testing)
            
        Returns:
            CorrelationReport with full execution details
        """
        import time
        start_time = time.time()
        
        report = CorrelationReport(scan_id=scan_id)
        
        try:
            # Phase 1: INGEST — Pull findings from PostgreSQL
            logger.info(f"[{scan_id}] Phase 1: Ingesting findings")
            findings = await self._ingest_findings(scan_id)
            report.total_findings = len(findings)
            
            if not findings:
                logger.info(f"[{scan_id}] No findings to correlate")
                report.execution_time_ms = int((time.time() - start_time) * 1000)
                return report
            
            # Phase 2: ANALYZE — Compute reachability
            logger.info(f"[{scan_id}] Phase 2: Analyzing reachability for {len(findings)} findings")
            reachabilities = await self.reachability.analyze_batch(findings)
            
            for r in reachabilities:
                if r.is_reachable:
                    report.reachable_count += 1
                elif r.reachability_type == ReachabilityType.UNREACHABLE:
                    report.unreachable_count += 1
                else:
                    report.unknown_count += 1
            
            # Phase 3: SCORE — Calculate priorities
            logger.info(f"[{scan_id}] Phase 3: Scoring priorities")
            priorities = self.scorer.score_batch(findings, reachabilities)
            
            for p in priorities:
                if p.priority == PriorityLevel.CRITICAL:
                    report.critical_count += 1
                elif p.priority == PriorityLevel.HIGH:
                    report.high_count += 1
                elif p.priority == PriorityLevel.MEDIUM:
                    report.medium_count += 1
                elif p.priority == PriorityLevel.LOW:
                    report.low_count += 1
                else:
                    report.deferred_count += 1
            
            # Phase 4: QUEUE — Generate and enqueue exploitation tasks
            logger.info(f"[{scan_id}] Phase 4: Generating exploit queue")
            queued, skipped = await self._generate_queue(
                findings=findings,
                reachabilities=reachabilities,
                priorities=priorities,
                target_url=target_url,
            )
            
            report.queued_count = queued
            report.skipped_count = skipped
            
            # Build correlation details
            for finding, reach, priority in zip(findings, reachabilities, priorities):
                report.correlation_details.append({
                    "finding_id": finding["finding_id"],
                    "severity": finding.get("severity"),
                    "vuln_category": finding.get("vuln_category"),
                    "is_reachable": reach.is_reachable,
                    "reachability_type": reach.reachability_type.value,
                    "priority": priority.priority.name,
                    "score": priority.score,
                    "file": finding.get("file_path"),
                    "method": finding.get("method_name"),
                })
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            report.execution_time_ms = elapsed_ms
            
            logger.info(
                f"[{scan_id}] Correlation complete: "
                f"{report.queued_count} queued, "
                f"{report.skipped_count} skipped, "
                f"({report.critical_count} critical, {report.high_count} high) "
                f"in {elapsed_ms}ms"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"[{scan_id}] Correlation failed: {e}")
            report.errors.append(str(e))
            report.execution_time_ms = int((time.time() - start_time) * 1000)
            return report
    
    async def _ingest_findings(self, scan_id: str) -> list[dict[str, Any]]:
        """
        Ingest findings from PostgreSQL.
        
        Filters by confidence threshold and vulnerability categories.
        """
        all_findings = []
        
        for vuln_category in self.config.vuln_categories:
            findings = await self.postgres.fetch_findings_by_scan(
                scan_id=scan_id,
                min_confidence=self.config.min_confidence_threshold,
                vuln_category=vuln_category,
            )
            all_findings.extend(findings)
        
        # Deduplication by evidence hash
        if self.config.enable_deduplication:
            seen_hashes = set()
            deduplicated = []
            for f in all_findings:
                evidence_hash = f"{f['file_path']}:{f['line_number']}:{f['method_name']}"
                if evidence_hash not in seen_hashes:
                    seen_hashes.add(evidence_hash)
                    deduplicated.append(f)
            all_findings = deduplicated
        
        return all_findings
    
    async def _generate_queue(
        self,
        findings: list[dict[str, Any]],
        reachabilities: list[PathResult],
        priorities: list[PriorityResult],
        target_url: Optional[str],
    ) -> tuple[int, int]:
        """
        Generate queue items and enqueue them.
        
        Args:
            findings: Static findings
            reachabilities: Reachability results
            priorities: Priority scores
            target_url: Application URL for testing
            
        Returns:
            (queued_count, skipped_count)
        """
        queued = 0
        skipped = 0
        
        # Check queue capacity
        queue_depth = await self.queue.get_queue_depth()
        current_queued = queue_depth.get("queued", 0)
        
        available_capacity = self.config.max_queue_size - current_queued
        
        # Sort by priority (highest first)
        sorted_items = sorted(
            zip(findings, reachabilities, priorities),
            key=lambda x: x[2].score,
            reverse=True,
        )
        
        for finding, reachability, priority in sorted_items:
            # Skip if queue is full
            if queued >= available_capacity:
                logger.warning("Queue capacity reached, skipping remaining items")
                skipped += len(sorted_items) - queued - skipped
                break
            
            # Skip unreachable findings
            if self.config.skip_unreachable and not reachability.is_reachable:
                skipped += 1
                
                # Still record correlation for audit
                await self.postgres.upsert_correlation(
                    finding_id=finding["finding_id"],
                    result_id=None,
                    correlation_type="unreachable",
                    correlation_score=priority.score / 100,
                    is_reachable=False,
                    reachability_path=reachability.to_dict(),
                    priority=priority.priority.name.lower(),
                )
                continue
            
            # Extract validation strategies from LLM analysis
            validation_strategies = finding.get("metadata", {}).get(
                "validation_strategies",
                self._default_strategies(finding.get("vuln_category", ""))
            )
            
            # Build injection points from static context
            injection_points = self._extract_injection_points(finding)
            
            # Create queue item
            queue_item = QueueItem(
                queue_item_id=f"qi-{finding['finding_id'][:8]}",
                correlation_id="",  # Will be set after correlation record creation
                finding_id=finding["finding_id"],
                scan_id=finding["scan_id"],
                vuln_type=finding.get("vuln_category", "unknown"),
                target_url=target_url or finding.get("repo_url", ""),
                injection_points=injection_points,
                validation_strategies=validation_strategies,
                static_context={
                    "file_path": finding.get("file_path"),
                    "line_number": finding.get("line_number"),
                    "method_name": finding.get("method_name"),
                    "cpg_context": finding.get("cpg_context"),
                    "has_sanitizer": finding.get("has_sanitizer"),
                    "reachability": reachability.to_dict(),
                },
                priority=QueuePriority(priority.priority.value),
                composite_score=priority.score,
            )
            
            # Create correlation record
            correlation_id = await self.postgres.upsert_correlation(
                finding_id=finding["finding_id"],
                result_id=None,
                correlation_type="queued_for_exploitation",
                correlation_score=priority.score / 100,
                is_reachable=reachability.is_reachable,
                reachability_path=reachability.to_dict(),
                priority=priority.priority.name.lower(),
            )
            
            queue_item.correlation_id = correlation_id
            
            # Enqueue
            await self.queue.enqueue(queue_item)
            queued += 1
        
        return queued, skipped
    
    def _extract_injection_points(self, finding: dict[str, Any]) -> dict[str, Any]:
        """Extract injection points from finding context."""
        injection_points = {}
        
        # Source node as primary injection point
        source = finding.get("source_node", "")
        if source:
            injection_points["source"] = {
                "location": "query",  # Default assumption
                "type": "string",
                "value": source,
                "context": "taint_source",
            }
        
        # Sink node as secondary injection point
        sink = finding.get("sink_node", "")
        if sink:
            injection_points["sink"] = {
                "location": "body",
                "type": "string",
                "value": sink,
                "context": "taint_sink",
            }
        
        # Add method parameter if available
        method_name = finding.get("method_name", "")
        if method_name:
            injection_points["method_parameter"] = {
                "location": "body",
                "type": "string",
                "value": "",
                "context": f"method:{method_name}",
            }
        
        return injection_points
    
    def _default_strategies(self, vuln_category: str) -> list[str]:
        """Get default validation strategies for vulnerability type."""
        strategies = {
            "sqli": [
                "error_based_detection",
                "union_based_extraction",
                "time_based_blind",
                "boolean_based_blind",
                "stacked_queries",
            ],
            "xss": [
                "reflected_payload",
                "stored_payload",
                "dom_based_execution",
                "polyglot_bypass",
                "context_specific_encoding",
            ],
            "command_injection": [
                "direct_command_execution",
                "time_based_blind",
                "output_redirection",
                "command_chaining",
            ],
            "path_traversal": [
                "dot_dot_slash",
                "null_byte_bypass",
                "encoding_bypass",
                "absolute_path",
            ],
            "ssrf": [
                "localhost_access",
                "internal_ip_scan",
                "dns_rebinding",
                "protocol_smuggling",
            ],
            "idor": [
                "numeric_id_increment",
                "uuid_enumeration",
                "object_reference_bypass",
                "unauthorized_access_validation",
            ],
            "broken_auth": [
                "default_credentials",
                "brute_force_protection_bypass",
                "session_fixation",
                "jwt_token_manipulation",
                "auth_bypass_logic",
            ],
        }
        
        return strategies.get(vuln_category, ["generic_validation"])
    
    async def health_check(self) -> dict[str, Any]:
        """Check correlation engine health."""
        return {
            "postgres": "connected" if self.postgres else "disconnected",
            "queue": await self.queue.health_check(),
            "config": {
                "min_confidence": self.config.min_confidence_threshold,
                "vuln_categories": self.config.vuln_categories,
                "skip_unreachable": self.config.skip_unreachable,
            },
        }
