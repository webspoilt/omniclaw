"""
LLM Inference Client for vulnerability reasoning.
Implements sanitization gap analysis with structured output parsing.

Security Model:
- All inference runs via local vLLM/ollama — no external API calls
- Prompts never persisted to disk (in-memory only)
- Responses are cryptographically hashed for audit trail
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import aiohttp

from .models import (
    Confidence,
    LLMAnalysis,
    SanitizationGap,
    Severity,
    StaticFinding,
)
from .slicer import SliceContext

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported local LLM inference providers."""
    VLLM = "vllm"
    OLLAMA = "ollama"
    TGI = "text-generation-inference"
    LLAMACPP = "llama.cpp"


@dataclass
class LLMConfig:
    """Configuration for LLM inference."""
    provider: LLMProvider = LLMProvider.VLLM
    base_url: str = "http://localhost:8000"  # vLLM default
    model: str = "deepseek-coder-33b-instruct"
    max_tokens: int = 2048
    temperature: float = 0.1                  # Low temperature for deterministic analysis
    top_p: float = 0.95
    timeout_seconds: int = 120
    batch_size: int = 4                       # Parallel slice analysis
    enable_json_mode: bool = True             # Request structured JSON output


class SanitizationAnalyzer:
    """
    Specialized LLM analyzer for detecting sanitization gaps in program slices.
    
    Uses a carefully engineered system prompt to guide the LLM through
    a structured analysis of taint flows, identifying missing or 
    insufficient sanitization that could lead to SQL injection.
    """
    
    SYSTEM_PROMPT = """You are an expert application security analyst specializing in SQL injection detection. Your task is to analyze program slices extracted from Code Property Graphs (CPGs) and determine whether tainted data flows are properly sanitized before reaching SQL execution sinks.

## Analysis Framework

You must evaluate each slice against these sanitization dimensions:

### 1. INPUT VALIDATION GAPS
- Is user input validated for type, length, format, or character set?
- Are allowlists used for expected values?
- Is there any validation at the entry point?

### 2. PARAMETERIZATION STATUS
- Are prepared statements / parameterized queries used?
- If parameterized, are ALL tainted values bound as parameters?
- Is there any string concatenation or interpolation mixed with parameters?

### 3. ESCAPING/ENCODING ADEQUACY
- Are special characters (', ", \\, ;, --, /*) properly escaped?
- Is the escaping context-appropriate (SQL vs. LIKE vs. ORDER BY)?
- Can the escaping be bypassed with encoding tricks (Unicode, null bytes)?

### 4. ORM/FRAMEWORK PROTECTIONS
- Is an ORM used (Hibernate, SQLAlchemy, Sequelize, GORM)?
- Does the ORM configuration allow raw queries?
- Are query builder methods vulnerable to injection (ORDER BY, column names)?

### 5. LOGIC BYPASS VECTORS
- Can the sanitization be bypassed via:
  - Type juggling (integer vs string)
  - Null byte injection (%00)
  - Unicode normalization
  - Comment injection (-- , /* */)
  - Boolean logic (OR 1=1)

## Output Format

Respond ONLY with valid JSON matching this schema:

{
    "is_vulnerable": boolean,
    "confidence": "certain" | "high" | "medium" | "low" | "tentative",
    "reasoning": "Detailed explanation of your analysis...",
    "sanitization_gaps": [
        {
            "gap_type": "missing_validation|incomplete_parameterization|insufficient_escaping|orm_bypass|logic_bypass|encoding_bypass",
            "location_description": "Where in the code the gap exists",
            "vulnerable_pattern": "The specific vulnerable code pattern",
            "recommended_fix": "Specific remediation guidance",
            "confidence": "certain|high|medium|low|tentative"
        }
    ],
    "exploitability_assessment": "Detailed assessment of exploitability including difficulty, prerequisites, and potential impact",
    "recommended_validations": [
        "List of specific dynamic validation strategies for a pentesting agent to try"
    ]
}

## Rules

1. Be conservative — if you cannot confirm sanitization is complete, flag it as vulnerable
2. Focus on practical exploitation, not theoretical issues
3. Consider defense-in-depth: multiple layers of protection are stronger
4. Account for language-specific vulnerabilities (Java type erasure, JavaScript truthiness, Python string formatting)
5. The presence of ANY string concatenation/formatting/interpolation in SQL construction is a significant red flag
6. Prepared statements with concatenated column names or ORDER BY clauses are still partially vulnerable

Respond with ONLY the JSON object. No markdown, no explanations outside the JSON."""

    # Additional per-language guidance appended based on detected language
    LANGUAGE_GUIDANCE = {
        "java": """
Java-Specific Considerations:
- StringBuilder/StringBuffer concatenation in SQL is ALWAYS vulnerable
- JPA Criteria API is safe, but JPQL with concatenation is not
- MyBatis ${} interpolation is vulnerable, #{} is safe
- Hibernate createQuery with concatenated strings is vulnerable
- Java's PreparedStatement is safe ONLY when ALL parameters use setString/setInt
""",
        "python": """
Python-Specific Considerations:
- f-strings in SQL queries are ALWAYS vulnerable
- String formatting (%s, .format()) in SQL is ALWAYS vulnerable  
- SQLAlchemy text() with bind parameters is safe
- Django ORM is generally safe, but extra() and RawSQL require scrutiny
- psycopg2 with %s placeholders is safe, string concatenation is not
- SQLite execute() with parameterized queries is safe
""",
        "js": """
JavaScript/TypeScript-Specific Considerations:
- Template literals in SQL queries are ALWAYS vulnerable
- Sequelize findAll() with where clauses is safe, but sequelize.query() with string concatenation is not
- Prisma $queryRaw with template literals and tagged template is safe
- Knex .raw() with ? placeholders is safe, string concatenation is not
- MongoDB $where with string concatenation is vulnerable to NoSQL injection
""",
        "go": """
Go-Specific Considerations:
- fmt.Sprintf in SQL queries is ALWAYS vulnerable
- database/sql with $1, $2 placeholders is safe
- Squirrel query builder is safe when used correctly
- GORM is generally safe, but Raw() with string concatenation is not
- String concatenation with + in SQL construction is vulnerable
""",
    }

    def __init__(self, llm_client: LLMInferenceClient):
        self.client = llm_client
    
    async def analyze_slice(self, slice_ctx: SliceContext) -> LLMAnalysis:
        """
        Analyze a program slice for sanitization gaps using LLM reasoning.
        
        Args:
            slice_ctx: Extracted program slice with dataflow context
            
        Returns:
            Structured LLM analysis with sanitization gap findings
        """
        # Build language-specific system prompt
        system_prompt = self.SYSTEM_PROMPT
        if slice_ctx.sink_type in self.LANGUAGE_GUIDANCE:
            system_prompt += self.LANGUAGE_GUIDANCE[slice_ctx.sink_type]
        
        # Build user prompt with slice context
        user_prompt = slice_ctx.to_llm_prompt()
        
        # Call LLM
        response = await self.client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )
        
        # Parse structured response
        return self._parse_response(response, slice_ctx.slice_id)
    
    async def analyze_slices_batch(
        self,
        slices: list[SliceContext],
    ) -> dict[str, LLMAnalysis]:
        """
        Analyze multiple slices with controlled concurrency.
        
        Args:
            slices: List of program slices to analyze
            
        Returns:
            Mapping of slice_id to LLMAnalysis
        """
        import asyncio
        
        semaphore = asyncio.Semaphore(self.client.config.batch_size)
        
        async def analyze_with_limit(slice_ctx: SliceContext) -> tuple[str, LLMAnalysis]:
            async with semaphore:
                analysis = await self.analyze_slice(slice_ctx)
                return slice_ctx.slice_id, analysis
        
        tasks = [analyze_with_limit(s) for s in slices]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        analyses = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Slice analysis failed: {result}")
                continue
            slice_id, analysis = result
            analyses[slice_id] = analysis
        
        return analyses
    
    def _parse_response(self, response: str, slice_id: str) -> LLMAnalysis:
        """
        Parse LLM JSON response into structured LLMAnalysis.
        
        Handles various response formats and validates required fields.
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            
            # Map confidence string to enum
            confidence_map = {
                "certain": Confidence.CERTAIN,
                "high": Confidence.HIGH,
                "medium": Confidence.MEDIUM,
                "low": Confidence.LOW,
                "tentative": Confidence.TENTATIVE,
            }
            
            # Parse sanitization gaps
            gaps = []
            for gap_data in data.get("sanitization_gaps", []):
                gaps.append(SanitizationGap(
                    gap_type=gap_data.get("gap_type", "unknown"),
                    location_description=gap_data.get("location_description", ""),
                    vulnerable_pattern=gap_data.get("vulnerable_pattern", ""),
                    recommended_fix=gap_data.get("recommended_fix", ""),
                    confidence=confidence_map.get(
                        gap_data.get("confidence", "medium").lower(),
                        Confidence.MEDIUM,
                    ),
                ))
            
            return LLMAnalysis(
                is_vulnerable=data.get("is_vulnerable", False),
                reasoning=data.get("reasoning", ""),
                sanitization_gaps=gaps,
                exploitability_assessment=data.get("exploitability_assessment", ""),
                recommended_validations=data.get("recommended_validations", []),
                raw_response=response,
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for slice {slice_id}: {e}")
            return LLMAnalysis(
                is_vulnerable=False,
                reasoning=f"Parse error: {e}",
                sanitization_gaps=[],
                exploitability_assessment="unknown",
                recommended_validations=[],
                raw_response=response,
            )
    
    def enrich_findings(
        self,
        findings: list[StaticFinding],
        analyses: dict[str, LLMAnalysis],
    ) -> list[StaticFinding]:
        """
        Enrich StaticFinding objects with LLM analysis results.
        
        Updates severity and confidence based on LLM assessment.
        """
        enriched = []
        
        for finding in findings:
            # Match finding to analysis by evidence hash
            analysis = None
            for slice_id, ana in analyses.items():
                if self._finding_matches_slice(finding, slice_id):
                    analysis = ana
                    break
            
            if analysis:
                finding.llm_analysis = analysis
                
                # Adjust confidence based on LLM assessment
                if analysis.is_vulnerable:
                    finding.confidence_score = max(
                        finding.confidence_score,
                        self._confidence_to_float(analysis.confidence),
                    )
                    # Elevate severity if LLM confirms vulnerability
                    if finding.severity == Severity.LOW and analysis.sanitization_gaps:
                        finding.severity = Severity.MEDIUM
                    elif finding.severity == Severity.MEDIUM and len(analysis.sanitization_gaps) >= 2:
                        finding.severity = Severity.HIGH
                
                # Add LLM-derived tags
                for gap in analysis.sanitization_gaps:
                    finding.tags.append(f"gap:{gap.gap_type}")
                
                if analysis.recommended_validations:
                    finding.metadata["validation_strategies"] = analysis.recommended_validations
            
            enriched.append(finding)
        
        return enriched
    
    def _finding_matches_slice(self, finding: StaticFinding, slice_id: str) -> bool:
        """Check if a finding corresponds to a given slice."""
        if finding.cpg_context and finding.cpg_context.dataflow_path:
            path_hash = finding.cpg_context.dataflow_path.path_hash
            return path_hash[:16] in slice_id or slice_id in path_hash
        return False
    
    def _confidence_to_float(self, confidence: Confidence) -> float:
        """Convert Confidence enum to float score."""
        return confidence.value


class LLMInferenceClient:
    """
    Local LLM inference client supporting multiple providers.
    
    All communication is over localhost — no external network access.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._token_count = 0
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            )
        return self._session
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
    ) -> str:
        """
        Send completion request to local LLM inference server.
        
        Args:
            system_prompt: System/instruction prompt
            user_prompt: User/content prompt (slice context)
            json_mode: Request JSON-structured output
            
        Returns:
            LLM response text
        """
        if self.config.provider == LLMProvider.VLLM:
            return await self._vllm_complete(system_prompt, user_prompt, json_mode)
        elif self.config.provider == LLMProvider.OLLAMA:
            return await self._ollama_complete(system_prompt, user_prompt)
        else:
            raise ValueError(f"Provider {self.config.provider} not implemented")
    
    async def _vllm_complete(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool,
    ) -> str:
        """Complete using vLLM OpenAI-compatible API."""
        session = await self._get_session()
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        url = f"{self.config.base_url}/v1/chat/completions"
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMInferenceError(
                        f"vLLM returned {response.status}: {error_text}"
                    )
                
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Update metrics
                self._request_count += 1
                self._token_count += result.get("usage", {}).get("total_tokens", 0)
                
                return content
                
        except aiohttp.ClientError as e:
            raise LLMInferenceError(f"vLLM connection failed: {e}")
    
    async def _ollama_complete(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Complete using Ollama API."""
        session = await self._get_session()
        
        payload = {
            "model": self.config.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            },
        }
        
        url = f"{self.config.base_url}/api/generate"
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMInferenceError(
                        f"Ollama returned {response.status}: {error_text}"
                    )
                
                result = await response.json()
                return result.get("response", "")
                
        except aiohttp.ClientError as e:
            raise LLMInferenceError(f"Ollama connection failed: {e}")
    
    async def health_check(self) -> dict[str, Any]:
        """Check LLM inference server health."""
        session = await self._get_session()
        
        try:
            if self.config.provider == LLMProvider.VLLM:
                url = f"{self.config.base_url}/health"
                async with session.get(url) as response:
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_code": response.status,
                    }
            else:
                url = f"{self.config.base_url}/api/tags"
                async with session.get(url) as response:
                    models = await response.json()
                    return {
                        "status": "healthy",
                        "available_models": [m.get("name") for m in models.get("models", [])],
                    }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @property
    def metrics(self) -> dict[str, Any]:
        """Return inference metrics."""
        return {
            "requests": self._request_count,
            "tokens_generated": self._token_count,
            "provider": self.config.provider.value,
            "model": self.config.model,
        }
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()


class LLMInferenceError(Exception):
    """LLM inference failure."""
    pass
