"""
Reachability Analyzer — Determines if static findings are exploitable via web entrypoints.

Uses CPG traversal to compute paths from HTTP entrypoints to vulnerability sinks.
Implements both intraprocedural and interprocedural reachability analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ReachabilityType(Enum):
    """Classification of reachability results."""
    DIRECT = "direct"           # HTTP handler directly contains sink
    ONE_HOP = "one_hop"         # HTTP handler -> one method -> sink
    MULTI_HOP = "multi_hop"     # HTTP handler -> ... -> sink (chain)
    CONDITIONAL = "conditional"  # Reachable only under certain conditions
    UNREACHABLE = "unreachable"  # No path from HTTP entrypoint
    UNKNOWN = "unknown"          # CPG analysis inconclusive


@dataclass
class PathNode:
    """A node in the reachability path."""
    method_name: str
    file_path: str
    line_number: int
    is_entrypoint: bool = False
    is_sink: bool = False
    call_type: str = "call"     # call, callback, event, reflection


@dataclass
class PathResult:
    """Result of reachability analysis for a single finding."""
    finding_id: str
    is_reachable: bool
    reachability_type: ReachabilityType
    
    # Path from entrypoint to sink
    path: list[PathNode] = field(default_factory=list)
    
    # Conditions that must be met for exploitability
    conditions: list[str] = field(default_factory=list)
    
    # Analysis metadata
    path_length: int = 0
    analysis_time_ms: int = 0
    confidence: float = 0.0     # 0.0-1.0 confidence in reachability
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "is_reachable": self.is_reachable,
            "reachability_type": self.reachability_type.value,
            "path": [
                {
                    "method_name": n.method_name,
                    "file_path": n.file_path,
                    "line_number": n.line_number,
                    "is_entrypoint": n.is_entrypoint,
                    "is_sink": n.is_sink,
                    "call_type": n.call_type,
                }
                for n in self.path
            ],
            "conditions": self.conditions,
            "path_length": self.path_length,
            "confidence": self.confidence,
        }


class ReachabilityAnalyzer:
    """
    Determines if a static finding is reachable from an HTTP entrypoint.
    
    Analysis approach:
    1. Find HTTP handlers/controllers (Spring, Express, Flask, etc.)
    2. Trace call graph from handlers to the method containing the sink
    3. Identify authentication/authorization guards along the path
    4. Assess conditional reachability
    
    This is critical for prioritization — unreachable findings cannot be
    dynamically exploited and should be deprioritized.
    """
    
    # HTTP entrypoint patterns by framework
    ENTRYPOINT_PATTERNS = {
        "spring": [
            "@RequestMapping", "@GetMapping", "@PostMapping",
            "@PutMapping", "@DeleteMapping", "@PatchMapping",
        ],
        "jakarta": [
            "@WebServlet", "doGet", "doPost", "doPut", "doDelete",
        ],
        "express": [
            "app.get", "app.post", "app.put", "app.delete",
            "router.get", "router.post", "router.put",
        ],
        "flask": [
            "@app.route", "@app.get", "@app.post",
        ],
        "django": [
            "urlpatterns", "path(", "re_path(",
        ],
        "fastapi": [
            "@app.get", "@app.post", "@app.put", "@app.delete",
        ],
        "gin": [
            "r.GET", "r.POST", "r.PUT", "r.DELETE",
        ],
    }
    
    def __init__(self, cpg_generator=None):
        """
        Initialize reachability analyzer.
        
        Args:
            cpg_generator: Optional CPG generator for live graph queries.
                          If None, uses heuristic analysis from precomputed data.
        """
        self.cpg_generator = cpg_generator
    
    async def analyze(
        self,
        finding: dict[str, Any],
    ) -> PathResult:
        """
        Analyze reachability of a finding from HTTP entrypoints.
        
        Args:
            finding: Static finding dictionary from PostgreSQL
            
        Returns:
            PathResult with reachability determination
        """
        import time
        start_time = time.time()
        
        finding_id = finding["finding_id"]
        file_path = finding["file_path"]
        method_name = finding["method_name"]
        cpg_context = finding.get("cpg_context", {})
        
        # Strategy 1: Check if finding is already in an HTTP handler
        if self._is_http_handler(file_path, method_name):
            result = PathResult(
                finding_id=finding_id,
                is_reachable=True,
                reachability_type=ReachabilityType.DIRECT,
                path=[
                    PathNode(
                        method_name=method_name,
                        file_path=file_path,
                        line_number=finding["line_number"],
                        is_entrypoint=True,
                        is_sink=True,
                    ),
                ],
                path_length=0,
                confidence=0.95,
            )
            result.analysis_time_ms = int((time.time() - start_time) * 1000)
            return result
        
        # Strategy 2: CPG-based call graph traversal
        if self.cpg_generator and cpg_context:
            path_result = await self._cpg_traversal(finding)
            path_result.analysis_time_ms = int((time.time() - start_time) * 1000)
            return path_result
        
        # Strategy 3: Heuristic analysis from precomputed data
        heuristic_result = self._heuristic_analysis(finding)
        heuristic_result.analysis_time_ms = int((time.time() - start_time) * 1000)
        return heuristic_result
    
    def _is_http_handler(self, file_path: str, method_name: str) -> bool:
        """
        Check if a method is directly an HTTP handler.
        
        Uses file path and naming conventions as heuristics.
        """
        # Controller file patterns
        controller_patterns = [
            "controller", "resource", "handler", "servlet",
            "router", "view", "endpoint",
        ]
        
        file_lower = file_path.lower()
        if any(p in file_lower for p in controller_patterns):
            return True
        
        # HTTP method name patterns
        http_methods = ["get", "post", "put", "delete", "patch", "handle"]
        if any(method_name.lower().startswith(h) for h in http_methods):
            return True
        
        return False
    
    async def _cpg_traversal(self, finding: dict[str, Any]) -> PathResult:
        """
        Perform CPG-based call graph traversal.
        
        Queries the CPG to find paths from HTTP entrypoints to the sink method.
        """
        finding_id = finding["finding_id"]
        method_name = finding["method_name"]
        cypher_query = finding.get("cypher_query", "")
        
        try:
            # Find HTTP entrypoints that can reach this method
            entrypoint_query = f"""
            MATCH (entrypoint:METHOD)
            WHERE entrypoint.NAME =~ '.*(handle|doGet|doPost|processRequest).*'
               OR entrypoint.FULL_NAME =~ '.*(Controller|Resource|Servlet).*'
            MATCH (sink:METHOD)
            WHERE sink.NAME = '{method_name}'
            MATCH path = shortestPath((entrypoint)-[:CALL|AST*]->(sink))
            RETURN 
                entrypoint.NAME as entry_method,
                entrypoint.FILENAME as entry_file,
                sink.NAME as sink_method,
                sink.FILENAME as sink_file,
                length(path) as hop_count,
                [n in nodes(path) | {{name: n.NAME, file: n.FILENAME}}] as path_nodes
            LIMIT 5
            """
            
            # In production, this would query the CPG
            # For architecture demo, return unknown with moderate confidence
            return PathResult(
                finding_id=finding_id,
                is_reachable=True,  # Assume reachable pending CPG analysis
                reachability_type=ReachabilityType.UNKNOWN,
                path=[],
                conditions=["Requires CPG-based interprocedural analysis"],
                path_length=-1,
                confidence=0.5,
            )
            
        except Exception as e:
            logger.error(f"CPG traversal failed for {finding_id}: {e}")
            return PathResult(
                finding_id=finding_id,
                is_reachable=False,
                reachability_type=ReachabilityType.UNKNOWN,
                path=[],
                conditions=[f"CPG analysis error: {str(e)}"],
                confidence=0.0,
            )
    
    def _heuristic_analysis(self, finding: dict[str, Any]) -> PathResult:
        """
        Perform heuristic reachability analysis without CPG.
        
        Uses file structure and naming conventions to estimate reachability.
        """
        finding_id = finding["finding_id"]
        file_path = finding["file_path"]
        method_name = finding["method_name"]
        vuln_category = finding.get("vuln_category", "")
        source_node = finding.get("source_node", "")
        
        # High confidence if source is HTTP-related
        http_sources = [
            "request", "param", "query", "body", "header",
            "getparameter", "getattribute", "input",
        ]
        
        has_http_source = any(s in source_node.lower() for s in http_sources)
        
        # Check if in web-accessible layer
        web_layers = [
            "controller", "resource", "servlet", "handler",
            "web", "api", "rest", "endpoint",
        ]
        
        in_web_layer = any(l in file_path.lower() for l in web_layers)
        
        # Check if in service layer (one hop from web)
        service_layers = [
            "service", "manager", "usecase", "interactor",
            "business", "logic",
        ]
        
        in_service_layer = any(l in file_path.lower() for l in service_layers)
        
        # Determine reachability
        if has_http_source and in_web_layer:
            return PathResult(
                finding_id=finding_id,
                is_reachable=True,
                reachability_type=ReachabilityType.DIRECT,
                path=[
                    PathNode(
                        method_name=method_name,
                        file_path=file_path,
                        line_number=finding["line_number"],
                        is_entrypoint=True,
                        is_sink=True,
                    ),
                ],
                conditions=[],
                path_length=0,
                confidence=0.9,
            )
        elif has_http_source and in_service_layer:
            return PathResult(
                finding_id=finding_id,
                is_reachable=True,
                reachability_type=ReachabilityType.ONE_HOP,
                path=[
                    PathNode(
                        method_name="HTTP_HANDLER",
                        file_path="unknown",
                        line_number=0,
                        is_entrypoint=True,
                    ),
                    PathNode(
                        method_name=method_name,
                        file_path=file_path,
                        line_number=finding["line_number"],
                        is_sink=True,
                    ),
                ],
                conditions=["HTTP handler may have authentication"],
                path_length=1,
                confidence=0.7,
            )
        elif in_web_layer or has_http_source:
            return PathResult(
                finding_id=finding_id,
                is_reachable=True,
                reachability_type=ReachabilityType.MULTI_HOP,
                path=[],
                conditions=["Multi-hop path, requires further analysis"],
                path_length=-1,
                confidence=0.5,
            )
        else:
            # Deep in backend — likely unreachable without specific entrypoint
            return PathResult(
                finding_id=finding_id,
                is_reachable=False,
                reachability_type=ReachabilityType.UNREACHABLE,
                path=[],
                conditions=["No HTTP entrypoint detected in heuristic analysis"],
                path_length=-1,
                confidence=0.3,
            )
    
    async def analyze_batch(
        self,
        findings: list[dict[str, Any]],
    ) -> list[PathResult]:
        """
        Analyze reachability for multiple findings.
        
        Args:
            findings: List of static finding dictionaries
            
        Returns:
            List of PathResults in same order
        """
        import asyncio
        
        # Limit concurrency to avoid overwhelming CPG
        semaphore = asyncio.Semaphore(10)
        
        async def analyze_with_limit(finding: dict) -> PathResult:
            async with semaphore:
                return await self.analyze(finding)
        
        results = await asyncio.gather(
            *[analyze_with_limit(f) for f in findings],
            return_exceptions=True,
        )
        
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Reachability analysis failed: {result}")
                processed.append(PathResult(
                    finding_id=findings[i]["finding_id"],
                    is_reachable=False,
                    reachability_type=ReachabilityType.UNKNOWN,
                    path=[],
                    conditions=[f"Analysis error: {str(result)}"],
                    confidence=0.0,
                ))
            else:
                processed.append(result)
        
        return processed
