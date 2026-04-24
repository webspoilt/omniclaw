"""
CPG Slicer — extracts program slices relevant to specific vulnerability patterns.
Implements taint analysis via CPG traversal for multiple vulnerability categories.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

from .cpg_generator import CPGGenerator
from .models import (
    CodeLocation,
    CPGContext,
    DataflowNode,
    DataflowPath,
    FindingStatus,
    Severity,
    StaticFinding,
)

logger = logging.getLogger(__name__)


@dataclass
class SliceConfig:
    """Configuration for program slicing."""
    max_path_length: int = 50           # Maximum taint path depth
    max_slices_per_sink: int = 10       # Limit slices for performance
    include_interprocedural: bool = True # Cross-method analysis
    track_string_operations: bool = True # Track concatenation, formatting
    min_confidence_threshold: float = 0.3


@dataclass
class SliceContext:
    """Context extracted from a program slice for LLM analysis."""
    slice_id: str
    vuln_category: str                  # sqli, cmdi, path_traversal, ssrf
    sink_type: str                      # sql_execute, shell_exec, file_read, etc.
    source_type: str                    # http_param, file_read, env_var, etc.
    dataflow_path: DataflowPath
    method_ast: str
    relevant_code_snippet: str
    cypher_query: str
    
    def to_llm_prompt(self) -> str:
        """Format slice context for LLM consumption."""
        return f"""
=== VULNERABILITY SLICE: {self.slice_id} ===
Category: {self.vuln_category.upper()}
Sink Type: {self.sink_type}
Source Type: {self.source_type}
Path Length: {self.dataflow_path.path_length}
Has Sanitizer: {self.dataflow_path.has_sanitizer}
Sanitizers Found: {[s.code for s in self.dataflow_path.sanitizers]}

=== RELEVANT CODE ===
{self.relevant_code_snippet}

=== DATAFLOW PATH ===
Source: {self.dataflow_path.source.code} ({self.dataflow_path.source.node_type})
{self._format_intermediate_nodes()}
Sink: {self.dataflow_path.sink.code} ({self.dataflow_path.sink.node_type})
"""
    
    def _format_intermediate_nodes(self) -> str:
        lines = []
        for i, node in enumerate(self.dataflow_path.intermediate_nodes[:15], 1):
            marker = f" [{node.semantic_type}]" if node.semantic_type else ""
            lines.append(f"  [{i}] {node.code}{marker}")
        if len(self.dataflow_path.intermediate_nodes) > 15:
            lines.append(f"  ... [{len(self.dataflow_path.intermediate_nodes) - 15} more nodes]")
        return "\n".join(lines)


class TaintSlicer:
    """Base class for CPG-based taint analysis slicing."""
    
    COMMON_SOURCES = [
        r"@RequestParam", r"@PathVariable", r"@QueryParam",
        r"req\.body", r"req\.params", r"req\.query", r"req\.headers",
        r"request\.getParameter", r"request\.json", r"request\.form",
        r"c\.PostForm", r"c\.Query", r"c\.Param",
        r"params\[", r"args\[", r"sys\.argv", r"os\.getenv", r"input\s*\(",
    ]

    COMMON_SANITIZERS = [
        r"escape_string", r"mysqli_real_escape", r"\.sanitize", 
        r"\.validate", r"validator", r"check_allowed", r"whitelist",
        r"int\s*\(", r"float\s*\(", r"Boolean\.valueOf"
    ]

    def __init__(self, cpg_generator: CPGGenerator, config: Optional[SliceConfig] = None):
        self.cpg = cpg_generator
        self.config = config or SliceConfig()

    async def _find_sinks(self, cpg_file: Path, language: str, sink_patterns: List[str]) -> List[Dict]:
        if not sink_patterns: return []
        pattern_union = "|".join(sink_patterns)
        
        cypher = f"""
        MATCH (sink:CALL)
        WHERE sink.NAME =~ '.*({pattern_union}).*'
          OR sink.CODE =~ '.*({pattern_union}).*'
        WITH sink
        MATCH (sink)-[:AST]->(arg:IDENTIFIER|LITERAL|CALL)
        RETURN 
            sink.NAME as method_name,
            sink.CODE as code,
            sink.LINE_NUMBER as line,
            sink.FULL_NAME as full_name,
            collect(DISTINCT arg.CODE) as arguments,
            id(sink) as node_id
        LIMIT 200
        """
        return await self.cpg.query_cpg(cpg_file, cypher)

    async def _slice_from_sink(self, cpg_file: Path, sink: Dict, language: str, vuln_category: str) -> List[SliceContext]:
        slices = []
        node_id = sink.get("node_id", "")
        
        cypher = f"""
        MATCH (sink:CALL)
        WHERE id(sink) = {node_id}
        MATCH path = (source)-[:REACHING_DEF|DATAFLOW*1..{self.config.max_path_length}]->(sink)
        WHERE source:IDENTIFIER OR source:CALL OR source:LITERAL
        WITH source, sink, path
        ORDER BY length(path) ASC
        LIMIT {self.config.max_slices_per_sink}
        RETURN 
            id(source) as source_id,
            source.CODE as source_code,
            source.NAME as source_name,
            source.NODE_TYPE as source_type,
            id(sink) as sink_id,
            sink.CODE as sink_code,
            [node in nodes(path) | {{
                id: id(node),
                code: node.CODE,
                type: node.NODE_TYPE,
                line: node.LINE_NUMBER,
                name: node.NAME,
                file: node.FILE
            }}] as path_nodes,
            length(path) as path_length
        """
        
        results = await self.cpg.query_cpg(cpg_file, cypher)
        for result in results:
            try:
                slice_ctx = self._build_slice_context(result, sink, language, vuln_category)
                if slice_ctx:
                    slices.append(slice_ctx)
            except Exception as e:
                logger.debug(f"Skipping invalid slice: {e}")
        return slices

    def _build_slice_context(self, query_result: Dict, sink_info: Dict, language: str, vuln_category: str) -> Optional[SliceContext]:
        path_nodes = query_result.get("path_nodes", [])
        if len(path_nodes) < 2: return None
        
        nodes = []
        for node_data in path_nodes:
            location = CodeLocation(
                file_path=node_data.get("file", "unknown"),
                line_start=node_data.get("line", 0),
                line_end=node_data.get("line", 0),
            )
            nodes.append(DataflowNode(
                node_id=str(node_data.get("id", "")),
                node_type=node_data.get("type", "UNKNOWN"),
                code=node_data.get("code", ""),
                location=location,
                semantic_type=self._classify_node(node_data),
            ))
        
        source, sink = nodes[0], nodes[-1]
        dataflow = DataflowPath(
            source=source,
            sink=sink,
            intermediate_nodes=nodes[1:-1],
            path_length=query_result.get("path_length", 0),
        )
        
        return SliceContext(
            slice_id=f"{vuln_category}-{source.node_id}-{sink.node_id}",
            vuln_category=vuln_category,
            sink_type=sink.code, # Simplified
            source_type=self._classify_source(source.code),
            dataflow_path=dataflow,
            method_ast=f"Method context around line {sink.location.line_start}",
            relevant_code_snippet=self._extract_snippet(nodes),
            cypher_query=f"MATCH p=(n1)-[*]->(n2) WHERE id(n1)={source.node_id} AND id(n2)={sink.node_id} RETURN p"
        )

    def _classify_node(self, node_data: Dict) -> Optional[str]:
        code = node_data.get("code", "")
        if any(re.search(p, code, re.I) for p in self.COMMON_SOURCES): return "SOURCE"
        if any(re.search(p, code, re.I) for p in self.COMMON_SANITIZERS): return "SANITIZER"
        return "PROPAGATOR"

    def _classify_source(self, code: str) -> str:
        if any(re.search(p, code, re.I) for p in [r"req\.", r"request", r"@Request", r"c\."]): return "http_input"
        if any(re.search(p, code, re.I) for p in [r"getenv", r"env\[", r"process\.env"]): return "environment"
        return "generic_source"

    def _extract_snippet(self, nodes: List[DataflowNode]) -> str:
        lines = []
        seen = set()
        for n in nodes:
            line = f"L{n.location.line_start}: {n.code}"
            if line not in seen:
                seen.add(line)
                lines.append(line)
        return "\n".join(lines[:20])

    def slices_to_findings(self, slices: List[SliceContext], scan_id: str) -> List[StaticFinding]:
        findings = []
        for ctx in slices:
            confidence = self._calculate_confidence(ctx)
            if confidence < self.config.min_confidence_threshold: continue
            
            findings.append(StaticFinding(
                scan_id=scan_id,
                rule_id=f"{ctx.vuln_category}-taint",
                vuln_category=ctx.vuln_category,
                severity=Severity.HIGH if not ctx.dataflow_path.has_sanitizer else Severity.MEDIUM,
                confidence_score=confidence,
                location=ctx.dataflow_path.sink.location,
                cpg_context=CPGContext(
                    method_ast=ctx.method_ast,
                    dataflow_path=ctx.dataflow_path,
                    cypher_query=ctx.cypher_query,
                    method_signature=ctx.dataflow_path.sink.location.method_name,
                ),
                tags=[ctx.vuln_category, "taint-analysis"]
            ))
        return findings

    def _calculate_confidence(self, ctx: SliceContext) -> float:
        score = 0.6
        if not ctx.dataflow_path.has_sanitizer: score += 0.2
        if ctx.dataflow_path.path_length > 25: score -= 0.1
        return max(0.0, min(1.0, score))


class SQLiSlicer(TaintSlicer):
    SINK_PATTERNS = {
        "java": [r"executeQuery", r"executeUpdate", r"prepareStatement", r"createNativeQuery"],
        "python": [r"execute", r"executemany", r"cursor\.", r"db\.execute"],
        "js": [r"query", r"execute", r"prisma\.\$queryRaw", r"knex\.raw"]
    }

    async def extract(self, cpg_file: Path, language: str) -> List[SliceContext]:
        patterns = self.SINK_PATTERNS.get(language, [])
        sinks = await self._find_sinks(cpg_file, language, patterns)
        slices = []
        for sink in sinks:
            slices.extend(await self._slice_from_sink(cpg_file, sink, language, "sqli"))
        return slices


class CommandInjectionSlicer(TaintSlicer):
    SINK_PATTERNS = {
        "java": [r"Runtime\.exec", r"ProcessBuilder"],
        "python": [r"os\.system", r"subprocess\.", r"popen"],
        "js": [r"child_process\.", r"exec\s*\(", r"spawn\s*\("]
    }

    async def extract(self, cpg_file: Path, language: str) -> List[SliceContext]:
        patterns = self.SINK_PATTERNS.get(language, [])
        sinks = await self._find_sinks(cpg_file, language, patterns)
        slices = []
        for sink in sinks:
            slices.extend(await self._slice_from_sink(cpg_file, sink, language, "cmdi"))
        return slices


class PathTraversalSlicer(TaintSlicer):
    SINK_PATTERNS = {
        "java": [r"FileInputStream", r"FileOutputStream", r"File\s*\(", r"Paths\.get"],
        "python": [r"open\s*\(", r"os\.path\.", r"send_file", r"Path\s*\("],
        "js": [r"fs\.", r"readFileSync", r"writeFile", r"res\.sendFile"]
    }

    async def extract(self, cpg_file: Path, language: str) -> List[SliceContext]:
        patterns = self.SINK_PATTERNS.get(language, [])
        sinks = await self._find_sinks(cpg_file, language, patterns)
        slices = []
        for sink in sinks:
            slices.extend(await self._slice_from_sink(cpg_file, sink, language, "path_traversal"))
        return slices


class SSRFSlicer(TaintSlicer):
    SINK_PATTERNS = {
        "java": [r"HttpURLConnection", r"HttpClient", r"RestTemplate", r"WebClient"],
        "python": [r"requests\.", r"urllib\.", r"aiohttp\."],
        "js": [r"axios", r"fetch", r"http\.request", r"https\.request"]
    }

    async def extract(self, cpg_file: Path, language: str) -> List[SliceContext]:
        patterns = self.SINK_PATTERNS.get(language, [])
        sinks = await self._find_sinks(cpg_file, language, patterns)
        slices = []
        for sink in sinks:
            slices.extend(await self._slice_from_sink(cpg_file, sink, language, "ssrf"))
        return slices


class SlicerPipeline:
    """Orchestrates all slicers to perform full static analysis."""
    
    def __init__(self, cpg_generator: CPGGenerator, config: Optional[SliceConfig] = None):
        self.slicers = [
            SQLiSlicer(cpg_generator, config),
            CommandInjectionSlicer(cpg_generator, config),
            PathTraversalSlicer(cpg_generator, config),
            SSRFSlicer(cpg_generator, config),
        ]

    async def run_all(self, cpg_file: Path, language: str, scan_id: str) -> List[StaticFinding]:
        all_findings = []
        for slicer in self.slicers:
            try:
                slices = await slicer.extract(cpg_file, language)
                all_findings.extend(slicer.slices_to_findings(slices, scan_id))
            except Exception as e:
                logger.error(f"Slicer {slicer.__class__.__name__} failed: {e}")
        return all_findings
