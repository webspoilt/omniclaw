#!/usr/bin/env python3
"""
OmniClaw Echo Chambers
Spawns lightweight shadow agents to explore alternative solutions 
in parallel. Returns the best path, not just the first one.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("OmniClaw.EchoChambers")


# Exploration strategies — each biases the shadow agent differently
EXPLORATION_STRATEGIES = {
    "speed": {
        "name": "Speed Optimizer",
        "bias": "Optimize for execution speed and performance. Prefer O(1) lookups, "
                "caching, and minimal allocations. Accept trade-offs in readability.",
        "temperature": 0.3,
    },
    "readability": {
        "name": "Readability Champion",
        "bias": "Optimize for code readability and maintainability. Prefer clear naming, "
                "small functions, comprehensive documentation. Accept minor performance costs.",
        "temperature": 0.4,
    },
    "maintainability": {
        "name": "Maintainability Architect",
        "bias": "Optimize for long-term maintainability. Prefer SOLID principles, "
                "loose coupling, comprehensive tests. Think about future developers.",
        "temperature": 0.3,
    },
    "minimal": {
        "name": "Minimalist",
        "bias": "Use the absolute minimum code to solve the problem correctly. "
                "Remove all unnecessary abstractions. YAGNI principle strictly.",
        "temperature": 0.2,
    },
    "robust": {
        "name": "Robustness Engineer",
        "bias": "Optimize for robustness and error handling. Consider every edge case, "
                "add comprehensive validation, graceful degradation, retry logic.",
        "temperature": 0.3,
    },
    "creative": {
        "name": "Creative Explorer",
        "bias": "Think outside the box. Consider unconventional approaches, novel patterns, "
                "and creative solutions that others might not think of.",
        "temperature": 0.7,
    },
    "security": {
        "name": "Security Analyst",
        "bias": "Optimize for security. Consider attack vectors, input validation, "
                "principle of least privilege, and defense in depth.",
        "temperature": 0.2,
    },
}


@dataclass
class ShadowSolution:
    """A solution proposed by a shadow agent"""
    strategy: str
    strategy_name: str
    solution: str
    reasoning: str
    trade_offs: str = ""
    confidence: float = 0.5
    execution_time: float = 0.0
    rank: int = 0
    score: float = 0.0


@dataclass
class ExplorationResult:
    """Complete result of an exploration session"""
    task: str
    solutions: List[ShadowSolution] = field(default_factory=list)
    best_solution: Optional[ShadowSolution] = None
    judge_reasoning: str = ""
    total_time: float = 0.0
    strategies_used: List[str] = field(default_factory=list)


class EchoChamber:
    """
    Spawns shadow agents to explore alternative solutions in parallel.
    
    Each shadow agent approaches the same task with a different bias
    (speed, readability, security, etc.), and a judge evaluates all
    solutions to select the best one.
    """
    
    def __init__(self, llm_call: Optional[Callable] = None,
                 default_strategies: List[str] = None):
        """
        Args:
            llm_call: Async function that takes (prompt, temperature) and returns response
            default_strategies: List of strategy keys to use by default
        """
        self.llm_call = llm_call
        self.default_strategies = default_strategies or ["speed", "readability", "robust"]
        self.exploration_history: List[ExplorationResult] = []
        
        logger.info(f"EchoChamber initialized with strategies: {self.default_strategies}")
    
    async def explore_alternatives(self, task: str, 
                                     strategies: List[str] = None,
                                     context: str = "",
                                     parallel: bool = True) -> ExplorationResult:
        """
        Explore alternative solutions using shadow agents.
        
        Args:
            task: The task/problem to solve
            strategies: Which strategies to use (defaults to self.default_strategies)
            context: Additional context for the task
            parallel: Whether to run shadow agents in parallel
            
        Returns:
            ExplorationResult with all solutions and the best one
        """
        strategies = strategies or self.default_strategies
        start_time = time.time()
        
        logger.info(f"Exploring {len(strategies)} alternative solutions for: {task[:100]}...")
        
        result = ExplorationResult(
            task=task,
            strategies_used=strategies,
        )
        
        if not self.llm_call:
            logger.warning("No LLM configured for Echo Chambers")
            return result
        
        # Spawn shadow agents
        if parallel:
            tasks = [
                self._run_shadow_agent(task, strategy, context)
                for strategy in strategies
                if strategy in EXPLORATION_STRATEGIES
            ]
            solutions = await asyncio.gather(*tasks, return_exceptions=True)
            result.solutions = [s for s in solutions if isinstance(s, ShadowSolution)]
        else:
            for strategy in strategies:
                if strategy in EXPLORATION_STRATEGIES:
                    solution = await self._run_shadow_agent(task, strategy, context)
                    if solution:
                        result.solutions.append(solution)
        
        # Judge the solutions
        if len(result.solutions) > 1:
            result.best_solution, result.judge_reasoning = await self._judge_solutions(
                task, result.solutions
            )
        elif result.solutions:
            result.best_solution = result.solutions[0]
            result.best_solution.rank = 1
            result.judge_reasoning = "Only one solution was generated."
        
        result.total_time = time.time() - start_time
        self.exploration_history.append(result)
        
        logger.info(
            f"Exploration complete in {result.total_time:.1f}s — "
            f"Best: {result.best_solution.strategy_name if result.best_solution else 'none'}"
        )
        
        return result
    
    async def _run_shadow_agent(self, task: str, strategy: str,
                                  context: str) -> Optional[ShadowSolution]:
        """Run a single shadow agent with a specific strategy"""
        strat = EXPLORATION_STRATEGIES.get(strategy)
        if not strat:
            return None
        
        start = time.time()
        
        prompt = f"""You are the "{strat['name']}" agent.

YOUR BIAS: {strat['bias']}

TASK: {task}

{f"CONTEXT: {context}" if context else ""}

Provide your solution with this exact format:

SOLUTION:
[Your complete solution]

REASONING:
[Why you chose this approach, considering your bias]

TRADE_OFFS:
[What trade-offs this approach makes]

CONFIDENCE: [0-100]%"""

        try:
            response = await self.llm_call(prompt)
            
            # Parse the response
            solution_text = self._extract_section(response, "SOLUTION:")
            reasoning = self._extract_section(response, "REASONING:")
            trade_offs = self._extract_section(response, "TRADE_OFFS:")
            confidence = self._extract_confidence(response)
            
            return ShadowSolution(
                strategy=strategy,
                strategy_name=strat["name"],
                solution=solution_text or response,
                reasoning=reasoning or "",
                trade_offs=trade_offs or "",
                confidence=confidence,
                execution_time=time.time() - start,
            )
        except Exception as e:
            logger.error(f"Shadow agent '{strategy}' failed: {e}")
            return None
    
    async def _judge_solutions(self, task: str,
                                 solutions: List[ShadowSolution]) -> tuple:
        """
        Judge and rank all solutions.
        
        Returns:
            Tuple of (best_solution, judge_reasoning)
        """
        solutions_text = ""
        for i, s in enumerate(solutions, 1):
            solutions_text += f"""
--- Solution {i}: {s.strategy_name} ---
{s.solution[:2000]}

Reasoning: {s.reasoning[:500]}
Trade-offs: {s.trade_offs[:500]}
Self-confidence: {s.confidence:.0%}
"""
        
        judge_prompt = f"""You are an impartial judge evaluating multiple solutions to the same problem.

ORIGINAL TASK: {task}

{solutions_text}

Evaluate each solution on:
1. CORRECTNESS: Does it solve the problem correctly?
2. QUALITY: How well-crafted is the solution?
3. TRADE-OFFS: Are the trade-offs acceptable?
4. PRACTICALITY: How practical is this for real-world use?

Rank the solutions from best to worst. Respond with:

RANKING:
1. [Solution number] - [Score 0-100] - [One-line reason]
2. [Solution number] - [Score 0-100] - [One-line reason]
...

BEST_SOLUTION: [Solution number]
REASONING: [Why this solution is the best overall choice]"""

        try:
            response = await self.llm_call(judge_prompt)
            
            # Parse rankings
            best_idx = self._extract_best_solution_index(response, len(solutions))
            reasoning = self._extract_section(response, "REASONING:")
            
            # Assign ranks and scores
            for i, sol in enumerate(solutions):
                sol.rank = i + 1  # Default rank
            
            if 0 <= best_idx < len(solutions):
                solutions[best_idx].rank = 1
                solutions[best_idx].score = 1.0
                return solutions[best_idx], reasoning or "Selected by judge."
            
            # Fallback: return highest self-confidence
            best = max(solutions, key=lambda s: s.confidence)
            best.rank = 1
            return best, reasoning or "Selected by highest confidence."
            
        except Exception as e:
            logger.error(f"Judging failed: {e}")
            best = max(solutions, key=lambda s: s.confidence)
            best.rank = 1
            return best, f"Judging failed ({e}), selected by confidence."
    
    def get_available_strategies(self) -> Dict[str, str]:
        """Get all available exploration strategies"""
        return {k: v["name"] for k, v in EXPLORATION_STRATEGIES.items()}
    
    def format_result(self, result: ExplorationResult) -> str:
        """Format an exploration result for display"""
        lines = []
        lines.append(f"═══ Echo Chamber Results ═══")
        lines.append(f"Task: {result.task[:100]}")
        lines.append(f"Strategies: {', '.join(result.strategies_used)}")
        lines.append(f"Time: {result.total_time:.1f}s")
        lines.append("")
        
        for sol in sorted(result.solutions, key=lambda s: s.rank):
            marker = "★" if sol == result.best_solution else " "
            lines.append(f"{marker} [{sol.rank}] {sol.strategy_name} "
                        f"(confidence: {sol.confidence:.0%})")
            if sol == result.best_solution:
                lines.append(f"   Solution: {sol.solution[:200]}...")
        
        if result.judge_reasoning:
            lines.append(f"\nJudge: {result.judge_reasoning}")
        
        return "\n".join(lines)
    
    # --- Parsing helpers ---
    
    @staticmethod
    def _extract_section(text: str, header: str) -> Optional[str]:
        """Extract a section from formatted text"""
        if header not in text:
            return None
        
        start = text.index(header) + len(header)
        
        # Find the next section header or end of text
        next_headers = ["SOLUTION:", "REASONING:", "TRADE_OFFS:", "CONFIDENCE:", 
                       "RANKING:", "BEST_SOLUTION:"]
        end = len(text)
        for h in next_headers:
            if h != header and h in text[start:]:
                pos = text.index(h, start)
                if pos < end:
                    end = pos
        
        return text[start:end].strip()
    
    @staticmethod
    def _extract_confidence(text: str) -> float:
        """Extract confidence from text"""
        import re
        match = re.search(r'CONFIDENCE:\s*(\d+)', text)
        if match:
            return int(match.group(1)) / 100.0
        return 0.5
    
    @staticmethod
    def _extract_best_solution_index(text: str, count: int) -> int:
        """Extract the best solution index from judge response"""
        import re
        match = re.search(r'BEST_SOLUTION:\s*(\d+)', text)
        if match:
            idx = int(match.group(1)) - 1  # Convert to 0-indexed
            if 0 <= idx < count:
                return idx
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get echo chamber statistics"""
        return {
            "total_explorations": len(self.exploration_history),
            "available_strategies": list(EXPLORATION_STRATEGIES.keys()),
            "default_strategies": self.default_strategies,
        }
