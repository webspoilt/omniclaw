#!/usr/bin/env python3
"""
OmniClaw Reasoning Lock
Forces deep reasoning on all LLM calls with configurable depth,
minimum response validation, and full reasoning trace.
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("OmniClaw.ReasoningLock")


class ThinkingLevel(Enum):
    """Reasoning depth levels"""
    MAX = "max"
    HIGH = "high"
    STANDARD = "standard"
    QUICK = "quick"


@dataclass
class ReasoningTrace:
    """A single reasoning trace entry"""
    step: int
    thought: str
    action: str
    observation: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReasoningConfig:
    """Configuration for reasoning enforcement"""
    thinking_level: ThinkingLevel = ThinkingLevel.MAX
    trace_depth: str = "full"           # "full", "summary", "none"
    min_tokens_per_response: int = 500
    enforce_chain_of_thought: bool = True
    require_self_verification: bool = True
    max_reasoning_steps: int = 10
    temperature_override: Optional[float] = None  # None = use provider default


class ReasoningLock:
    """
    Enforces deep reasoning on all agent LLM calls.
    
    Wraps prompts with chain-of-thought instructions,
    validates response depth, and maintains reasoning traces.
    """
    
    def __init__(self, config: Optional[ReasoningConfig] = None):
        self.config = config or ReasoningConfig()
        self.traces: Dict[str, list] = {}  # task_id -> list of ReasoningTrace
        self._call_count = 0
        self._rejection_count = 0
        
        logger.info(
            f"ReasoningLock initialized: level={self.config.thinking_level.value}, "
            f"min_tokens={self.config.min_tokens_per_response}"
        )
    
    def enhance_prompt(self, prompt: str, task_id: Optional[str] = None) -> str:
        """
        Inject deep reasoning instructions into a prompt.
        
        Args:
            prompt: The original prompt
            task_id: Optional task ID for trace tracking
            
        Returns:
            Enhanced prompt with reasoning instructions
        """
        if self.config.thinking_level == ThinkingLevel.QUICK:
            return prompt
        
        level = self.config.thinking_level
        
        # Build reasoning preamble based on depth
        preamble_map = {
            ThinkingLevel.MAX: self._max_reasoning_preamble(),
            ThinkingLevel.HIGH: self._high_reasoning_preamble(),
            ThinkingLevel.STANDARD: self._standard_reasoning_preamble(),
        }
        
        preamble = preamble_map.get(level, "")
        
        verification = ""
        if self.config.require_self_verification:
            verification = """

VERIFICATION (required):
After your answer, verify your work:
1. Re-read the original task
2. Check each claim for accuracy
3. Identify any assumptions you made
4. Rate your confidence (0-100%)
5. Note anything you're uncertain about
"""
        
        trace_instruction = ""
        if self.config.trace_depth == "full":
            trace_instruction = """

REASONING TRACE FORMAT:
For each reasoning step, use:
  STEP N:
    THOUGHT: [What you're considering]
    ACTION: [What you decide to do]
    OBSERVATION: [What you learn from that action]
"""
        
        enhanced = f"""{preamble}

---
ORIGINAL TASK:
{prompt}
---
{trace_instruction}{verification}

Provide a thorough, well-reasoned response. Do NOT give shallow or surface-level answers."""
        
        self._call_count += 1
        return enhanced
    
    def validate_response(self, response: str) -> Dict[str, Any]:
        """
        Validate that a response meets reasoning depth requirements.
        
        Args:
            response: The LLM response to validate
            
        Returns:
            Validation result dict with 'valid', 'reason', and 'token_estimate'
        """
        # Rough token estimate (1 token ≈ 4 chars for English)
        estimated_tokens = len(response) / 4
        
        result = {
            "valid": True,
            "reason": "passes",
            "token_estimate": int(estimated_tokens),
            "has_reasoning_steps": False,
            "has_verification": False,
            "depth_score": 0.0
        }
        
        # Check minimum token count
        if estimated_tokens < self.config.min_tokens_per_response:
            result["valid"] = False
            result["reason"] = (
                f"Response too shallow: ~{int(estimated_tokens)} tokens "
                f"(minimum: {self.config.min_tokens_per_response})"
            )
            self._rejection_count += 1
            return result
        
        # Check for reasoning steps
        reasoning_markers = ["STEP", "THOUGHT:", "REASONING:", "ANALYSIS:", "THEREFORE:"]
        result["has_reasoning_steps"] = any(m in response.upper() for m in reasoning_markers)
        
        # Check for self-verification
        verification_markers = ["VERIFICATION:", "CONFIDENCE:", "ASSUMPTION"]
        result["has_verification"] = any(m in response.upper() for m in verification_markers)
        
        # Calculate depth score
        depth = 0.0
        if result["has_reasoning_steps"]:
            depth += 0.4
        if result["has_verification"]:
            depth += 0.3
        if estimated_tokens > self.config.min_tokens_per_response * 2:
            depth += 0.3
        result["depth_score"] = round(depth, 2)
        
        return result
    
    def record_trace(self, task_id: str, step: int, thought: str, 
                     action: str, observation: str):
        """Record a reasoning trace step"""
        if task_id not in self.traces:
            self.traces[task_id] = []
        
        trace = ReasoningTrace(
            step=step,
            thought=thought,
            action=action,
            observation=observation
        )
        self.traces[task_id].append(trace)
    
    def get_trace(self, task_id: str) -> list:
        """Get the full reasoning trace for a task"""
        return self.traces.get(task_id, [])
    
    def get_llm_params(self) -> Dict[str, Any]:
        """
        Get LLM call parameters that enforce deep reasoning.
        
        Returns:
            Dict of parameters to merge into LLM API calls
        """
        params = {}
        
        # Temperature: lower = more focused reasoning
        temp_map = {
            ThinkingLevel.MAX: 0.1,
            ThinkingLevel.HIGH: 0.2,
            ThinkingLevel.STANDARD: 0.3,
            ThinkingLevel.QUICK: 0.5,
        }
        
        if self.config.temperature_override is not None:
            params["temperature"] = self.config.temperature_override
        else:
            params["temperature"] = temp_map.get(self.config.thinking_level, 0.3)
        
        # Higher max_tokens for deeper reasoning
        token_map = {
            ThinkingLevel.MAX: 8192,
            ThinkingLevel.HIGH: 4096,
            ThinkingLevel.STANDARD: 2048,
            ThinkingLevel.QUICK: 1024,
        }
        params["max_tokens"] = token_map.get(self.config.thinking_level, 2048)
        
        return params
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reasoning lock statistics"""
        return {
            "thinking_level": self.config.thinking_level.value,
            "total_calls": self._call_count,
            "rejections": self._rejection_count,
            "rejection_rate": (
                round(self._rejection_count / self._call_count, 3)
                if self._call_count > 0 else 0
            ),
            "active_traces": len(self.traces),
            "min_tokens": self.config.min_tokens_per_response,
        }
    
    # --- Private preamble builders ---
    
    def _max_reasoning_preamble(self) -> str:
        return """DEEP REASONING MODE (MAXIMUM):
You MUST think through this problem exhaustively before answering.

Required reasoning process:
1. UNDERSTAND: Restate the problem in your own words
2. DECOMPOSE: Break it into sub-problems
3. ANALYZE: Consider each sub-problem from multiple angles
4. SYNTHESIZE: Combine insights into a coherent solution
5. VALIDATE: Check your solution against the original requirements
6. EDGE CASES: Consider what could go wrong
7. ALTERNATIVES: Briefly note approaches you considered but rejected, and why"""
    
    def _high_reasoning_preamble(self) -> str:
        return """DEEP REASONING MODE (HIGH):
Think carefully before answering.

Required:
1. UNDERSTAND the problem fully
2. ANALYZE from multiple angles
3. VALIDATE your solution
4. Consider EDGE CASES"""
    
    def _standard_reasoning_preamble(self) -> str:
        return """Think step-by-step through this problem before providing your answer.
Show your reasoning clearly."""
