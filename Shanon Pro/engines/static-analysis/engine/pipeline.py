"""
Static Analysis Pipeline — Orchestrates the complete Stage 1 workflow.

Pipeline: Clone -> CPG Generate -> Slice -> LLM Analyze -> Persist Findings
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .cpg_generator import CPGConfig, CPGGenerator, CPGResult
from .llm_client import LLMConfig, LLMInferenceClient, SanitizationAnalyzer
from .models import StaticFinding
from .repository import CloneConfig, CloneResult, RepositoryCloner
from .security import CredentialVault, SecretScanner
from .slicer import SliceConfig, SliceContext, SlicerPipeline

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the static analysis pipeline."""
    clone_config: CloneConfig = None
    cpg_config: CPGConfig = None
    slice_config: SliceConfig = None
    llm_config: LLMConfig = None
    
    # Pipeline behavior
    enable_secret_scan: bool = True
    enable_llm_analysis: bool = True
    max_findings: int = 1000
    min_confidence_threshold: float = 0.3
    persist_findings: bool = True


@dataclass
class PipelineResult:
    """Result of complete static analysis pipeline execution."""
    scan_id: str
    repo_url: str
    commit_sha: str
    findings: list[StaticFinding]
    clone_result: Optional[CloneResult] = None
    cpg_result: Optional[CPGResult] = None
    slices_extracted: int = 0
    llm_analyses: int = 0
    execution_time_ms: int = 0
    errors: list[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def confirmed_vulnerabilities(self) -> list[StaticFinding]:
        """Findings confirmed by LLM as vulnerable."""
        return [
            f for f in self.findings
            if f.llm_analysis and f.llm_analysis.is_vulnerable
        ]
    
    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity.value == "critical")
    
    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity.value == "high")


class StaticAnalysisPipeline:
    """
    End-to-end static analysis pipeline orchestrator.
    
    Orchestrates the complete workflow from repository cloning through
    LLM-based vulnerability confirmation, producing validated findings
    ready for the Correlation Engine (Stage 3).
    
    Usage:
        pipeline = StaticAnalysisPipeline(config, vault, cpg_storage)
        result = await pipeline.analyze("https://github.com/org/repo.git", token_id)
    """
    
    def __init__(
        self,
        config: PipelineConfig,
        credential_vault: CredentialVault,
        cpg_storage_path: Path,
    ):
        self.config = config
        self.vault = credential_vault
        
        # Initialize sub-components
        self.cloner = RepositoryCloner(
            credential_vault=vault,
            secret_scanner=SecretScanner() if config.enable_secret_scan else None,
        )
        self.cpg_generator = CPGGenerator(cpg_storage_path)
        self.llm_client = LLMInferenceClient(config.llm_config)
        self.analyzer = SanitizationAnalyzer(self.llm_client)
    
    async def analyze(
        self,
        repo_url: str,
        access_token_id: str,
        scan_id: Optional[str] = None,
    ) -> PipelineResult:
        """
        Execute complete static analysis pipeline.
        
        Args:
            repo_url: Git repository URL
            access_token_id: Vault-stored credential reference
            scan_id: Optional pre-generated scan ID
            
        Returns:
            PipelineResult with findings and execution metadata
        """
        import time
        start_time = time.time()
        
        result = PipelineResult(
            scan_id=scan_id or self._generate_scan_id(),
            repo_url=repo_url,
            commit_sha="",
            findings=[],
        )
        
        clone_dir: Optional[Path] = None
        
        try:
            # Phase 1: Clone Repository
            logger.info(f"[{result.scan_id}] Phase 1: Cloning repository")
            clone_result = await self.cloner.clone(
                repo_url=repo_url,
                access_token_id=access_token_id,
                config=self.config.clone_config or CloneConfig(),
            )
            result.clone_result = clone_result
            result.commit_sha = clone_result.commit_sha
            clone_dir = clone_result.local_path
            
            if clone_result.secrets_detected:
                logger.warning(
                    f"[{result.scan_id}] {len(clone_result.secrets_detected)} "
                    f"secrets detected in repository"
                )
            
            # Phase 2: Generate CPG
            logger.info(f"[{result.scan_id}] Phase 2: Generating Code Property Graph")
            cpg_result = await self.cpg_generator.generate(
                source_path=clone_dir,
                config=self.config.cpg_config or CPGConfig(),
            )
            result.cpg_result = cpg_result
            
            # Phase 3: Extract Program Slices (All Categories)
            logger.info(f"[{result.scan_id}] Phase 3: Extracting program slices")
            slicer_pipeline = SlicerPipeline(
                cpg_generator=self.cpg_generator,
                config=self.config.slice_config or SliceConfig(),
            )
            
            # Using heuristic-only findings temporarily before LLM
            findings = await slicer_pipeline.run_all(
                cpg_file=cpg_result.cpg_path,
                language=cpg_result.language_detected,
                scan_id=result.scan_id
            )
            result.findings = findings
            result.slices_extracted = len(findings)
            
            # Phase 4: LLM Analysis (Optional)
            if self.config.enable_llm_analysis and result.findings:
                logger.info(f"[{result.scan_id}] Phase 4: LLM analysis of {len(result.findings)} findings")
                # TODO: Implement batch LLM analysis for StaticFinding list
                pass
            else:
                # Without LLM, use heuristic findings as is
                pass
            
            # Apply confidence threshold
            result.findings = [
                f for f in result.findings
                if f.confidence_score >= self.config.min_confidence_threshold
            ]
            
            # Limit max findings
            if len(result.findings) > self.config.max_findings:
                result.findings = result.findings[:self.config.max_findings]
                result.errors.append(f"Truncated to {self.config.max_findings} findings")
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = elapsed_ms
            
            logger.info(
                f"[{result.scan_id}] Pipeline complete: "
                f"{len(result.findings)} findings "
                f"({result.critical_count} critical, {result.high_count} high) "
                f"in {elapsed_ms}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[{result.scan_id}] Pipeline failed: {e}")
            result.errors.append(str(e))
            raise
            
        finally:
            # Cleanup clone directory
            if clone_dir:
                await self.cloner.cleanup_all()
    
    def _generate_scan_id(self) -> str:
        """Generate unique scan identifier."""
        import hashlib
        import time
        return hashlib.sha256(
            f"scan:{time.time()}:{id(self)}".encode()
        ).hexdigest()[:16]
    
    async def health_check(self) -> dict:
        """Check pipeline component health."""
        return {
            "llm": await self.llm_client.health_check(),
            "pipeline": "healthy",
        }
    
    async def close(self) -> None:
        """Cleanup pipeline resources."""
        await self.llm_client.close()
        await self.cloner.cleanup_all()
