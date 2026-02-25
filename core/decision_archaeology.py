#!/usr/bin/env python3
"""
OmniClaw Decision Archaeology
Logs the reasoning behind significant decisions and enables
future sessions to query: "Why did we choose this approach?"
"""

import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger("OmniClaw.DecisionArchaeology")


@dataclass
class Decision:
    """A recorded decision with full reasoning chain"""
    decision_id: str
    decision: str                         # What was decided
    reasoning: str                        # Why this was chosen
    alternatives: List[str] = field(default_factory=list)  # What else was considered
    rejected_reasons: Dict[str, str] = field(default_factory=dict)  # alt -> why rejected
    context: Dict[str, Any] = field(default_factory=dict)
    impact: str = "low"                   # "low", "medium", "high", "critical"
    tags: List[str] = field(default_factory=list)
    project: str = ""
    files_affected: List[str] = field(default_factory=list)
    made_by: str = "agent"                # "agent", "user", "system"
    confidence: float = 0.8
    timestamp: float = field(default_factory=time.time)
    superseded_by: Optional[str] = None   # ID of decision that overrides this one


class DecisionArchaeologist:
    """
    Records, indexes, and queries the reasoning behind project decisions.
    
    Every significant decision is logged with its full reasoning chain,
    alternatives considered, and context — so future sessions can 
    understand WHY something was done.
    """
    
    def __init__(self, storage_dir: str = "./memory_db/decisions",
                 memory=None):
        """
        Args:
            storage_dir: Directory for storing decision records
            memory: Optional VectorMemory for semantic search
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memory = memory
        
        # In-memory index for fast access
        self.decisions: Dict[str, Decision] = {}
        self._load_all()
        
        logger.info(f"DecisionArchaeologist initialized: {len(self.decisions)} decisions loaded")
    
    def record_decision(self, decision: str, reasoning: str,
                         alternatives: List[str] = None,
                         rejected_reasons: Dict[str, str] = None,
                         context: Dict[str, Any] = None,
                         impact: str = "medium",
                         tags: List[str] = None,
                         project: str = "",
                         files_affected: List[str] = None,
                         made_by: str = "agent",
                         confidence: float = 0.8) -> str:
        """
        Record a significant decision with full reasoning.
        
        Args:
            decision: What was decided
            reasoning: Why this approach was chosen
            alternatives: Other options that were considered
            rejected_reasons: Why each alternative was rejected
            context: Additional context (task, constraints, etc.)
            impact: Impact level of this decision
            tags: Categorization tags
            project: Project this decision belongs to
            files_affected: Files impacted by this decision
            made_by: Who made the decision
            confidence: How confident we are (0-1)
            
        Returns:
            Decision ID
        """
        decision_id = self._generate_id(decision)
        
        record = Decision(
            decision_id=decision_id,
            decision=decision,
            reasoning=reasoning,
            alternatives=alternatives or [],
            rejected_reasons=rejected_reasons or {},
            context=context or {},
            impact=impact,
            tags=tags or [],
            project=project,
            files_affected=files_affected or [],
            made_by=made_by,
            confidence=confidence,
        )
        
        # Store in memory
        self.decisions[decision_id] = record
        
        # Persist to disk
        self._save_decision(record)
        
        # Store in vector memory for semantic search
        if self.memory:
            try:
                import asyncio
                search_text = f"{decision} | {reasoning} | {' '.join(alternatives or [])}"
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(
                        self.memory.store(decision_id, search_text, "knowledge")
                    )
                else:
                    loop.run_until_complete(
                        self.memory.store(decision_id, search_text, "knowledge")
                    )
            except Exception as e:
                logger.debug(f"Could not store decision in vector memory: {e}")
        
        logger.info(f"Decision recorded [{impact.upper()}]: {decision}")
        return decision_id
    
    async def query_decisions(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query past decisions using natural language.
        
        Args:
            question: Natural language question about past decisions
            limit: Max results
            
        Returns:
            List of relevant decisions with their reasoning
        """
        # Try semantic search first
        if self.memory:
            try:
                results = await self.memory.search(question, limit=limit)
                decision_ids = [r.get("key", "") for r in results]
                return [
                    self._format_decision(self.decisions[did])
                    for did in decision_ids
                    if did in self.decisions
                ]
            except Exception:
                pass
        
        # Fallback: keyword search
        question_lower = question.lower()
        scored = []
        
        for did, d in self.decisions.items():
            score = 0
            searchable = f"{d.decision} {d.reasoning} {' '.join(d.tags)}".lower()
            
            for word in question_lower.split():
                if word in searchable:
                    score += 1
            
            if score > 0:
                scored.append((score, d))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._format_decision(d) for _, d in scored[:limit]]
    
    def get_reasoning_chain(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the full reasoning chain for a specific decision.
        
        Args:
            decision_id: The decision ID
            
        Returns:
            Complete reasoning chain including superseding decisions
        """
        if decision_id not in self.decisions:
            return None
        
        d = self.decisions[decision_id]
        chain = {
            "decision": d.decision,
            "reasoning": d.reasoning,
            "alternatives_considered": [
                {
                    "alternative": alt,
                    "rejected_because": d.rejected_reasons.get(alt, "Not specified")
                }
                for alt in d.alternatives
            ],
            "context": d.context,
            "confidence": d.confidence,
            "impact": d.impact,
            "made_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d.timestamp)),
            "made_by": d.made_by,
            "files_affected": d.files_affected,
        }
        
        # Check if superseded
        if d.superseded_by and d.superseded_by in self.decisions:
            successor = self.decisions[d.superseded_by]
            chain["superseded_by"] = {
                "decision_id": successor.decision_id,
                "decision": successor.decision,
                "reasoning": successor.reasoning,
            }
            chain["status"] = "superseded"
        else:
            chain["status"] = "active"
        
        return chain
    
    def supersede_decision(self, old_id: str, new_decision: str,
                            new_reasoning: str, **kwargs) -> str:
        """
        Record a new decision that supersedes an old one.
        
        Args:
            old_id: ID of the decision being superseded
            new_decision: The new decision
            new_reasoning: Why the old decision was overridden
            
        Returns:
            New decision ID
        """
        new_id = self.record_decision(
            decision=new_decision,
            reasoning=new_reasoning,
            context={"supersedes": old_id},
            **kwargs
        )
        
        if old_id in self.decisions:
            self.decisions[old_id].superseded_by = new_id
            self._save_decision(self.decisions[old_id])
        
        logger.info(f"Decision {old_id} superseded by {new_id}")
        return new_id
    
    def get_recent(self, limit: int = 10, project: Optional[str] = None) -> List[Dict]:
        """
        Get the most recent decisions.
        
        Args:
            limit: Max results
            project: Optional project filter
            
        Returns:
            List of recent decisions
        """
        decisions = list(self.decisions.values())
        
        if project:
            decisions = [d for d in decisions if d.project == project]
        
        decisions.sort(key=lambda d: d.timestamp, reverse=True)
        return [self._format_decision(d) for d in decisions[:limit]]
    
    def export_decisions(self, project: Optional[str] = None) -> str:
        """
        Export all decisions as a readable markdown timeline.
        
        Args:
            project: Optional project filter
            
        Returns:
            Markdown string
        """
        decisions = list(self.decisions.values())
        if project:
            decisions = [d for d in decisions if d.project == project]
        
        decisions.sort(key=lambda d: d.timestamp)
        
        lines = [f"# Decision Log{f' — {project}' if project else ''}\n"]
        lines.append(f"*{len(decisions)} decisions recorded*\n")
        
        for d in decisions:
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(d.timestamp))
            status = "~~superseded~~" if d.superseded_by else "**active**"
            
            lines.append(f"## [{d.impact.upper()}] {d.decision}")
            lines.append(f"*{date} — {status}*\n")
            lines.append(f"**Reasoning:** {d.reasoning}\n")
            
            if d.alternatives:
                lines.append("**Alternatives considered:**")
                for alt in d.alternatives:
                    reason = d.rejected_reasons.get(alt, "—")
                    lines.append(f"- ~~{alt}~~ — {reason}")
                lines.append("")
            
            if d.files_affected:
                lines.append(f"**Files:** {', '.join(f'`{f}`' for f in d.files_affected)}\n")
            
            lines.append("---\n")
        
        return "\n".join(lines)
    
    # --- Private helpers ---
    
    def _generate_id(self, decision: str) -> str:
        """Generate a unique decision ID"""
        hash_val = hashlib.md5(f"{decision}:{time.time()}".encode()).hexdigest()[:12]
        return f"dec_{hash_val}"
    
    def _format_decision(self, d: Decision) -> Dict[str, Any]:
        """Format a decision for display"""
        return {
            "decision_id": d.decision_id,
            "decision": d.decision,
            "reasoning": d.reasoning,
            "impact": d.impact,
            "confidence": d.confidence,
            "made_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d.timestamp)),
            "tags": d.tags,
            "project": d.project,
            "active": d.superseded_by is None,
        }
    
    def _save_decision(self, d: Decision):
        """Persist a decision to disk"""
        path = self.storage_dir / f"{d.decision_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(d), f, indent=2, default=str)
    
    def _load_all(self):
        """Load all decisions from disk"""
        for path in self.storage_dir.glob("dec_*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                d = Decision(**data)
                self.decisions[d.decision_id] = d
            except Exception as e:
                logger.warning(f"Could not load decision {path}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get decision archaeology statistics"""
        decisions = list(self.decisions.values())
        return {
            "total_decisions": len(decisions),
            "active": sum(1 for d in decisions if d.superseded_by is None),
            "superseded": sum(1 for d in decisions if d.superseded_by is not None),
            "by_impact": {
                level: sum(1 for d in decisions if d.impact == level)
                for level in ["low", "medium", "high", "critical"]
            },
            "storage_dir": str(self.storage_dir),
        }
