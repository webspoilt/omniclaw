import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

class RiskLevel:
    INFO = 0
    LOW = 10
    MEDIUM = 30
    HIGH = 70
    CRITICAL = 100

class RiskEngine:
    """
    Sovereign Risk Engine (Inspired by Tirreno)
    Calculates real-time risk scores for agent actions and system events.
    """
    def __init__(self, threshold_lock: int = 150, threshold_kill: int = 300):
        self.threshold_lock = threshold_lock
        self.threshold_kill = threshold_kill
        self.session_scores: Dict[str, int] = {}
        self.event_history: List[Dict] = []
        
        # Action sensitivity mapping
        self.sensitivity = {
            "bash_execute": RiskLevel.MEDIUM,
            "file_write": RiskLevel.LOW,
            "file_delete": RiskLevel.HIGH,
            "network_connect": RiskLevel.MEDIUM,
            "env_read": RiskLevel.LOW,
            "privileged_escalation": RiskLevel.CRITICAL
        }

    def evaluate_action(self, session_id: str, action_type: str, details: str) -> Dict:
        """
        Evaluate a single action and update the session risk score.
        """
        base_risk = self.sensitivity.get(action_type, RiskLevel.INFO)
        
        # Contextual modifiers
        modifier = 1.0
        if "rm " in details or "sudo" in details:
            modifier = 2.5
        if "curl" in details or "wget" in details:
            modifier = 1.5
            
        points = int(base_risk * modifier)
        
        # Update session score
        current_score = self.session_scores.get(session_id, 0)
        new_score = current_score + points
        self.session_scores[session_id] = new_score
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "action": action_type,
            "points": points,
            "total_score": new_score,
            "details": details[:100] + "..." if len(details) > 100 else details
        }
        self.event_history.append(event)
        
        # Determine status
        status = "safe"
        if new_score >= self.threshold_kill:
            status = "TERMINATE"
        elif new_score >= self.threshold_lock:
            status = "LOCK"
            
        return {
            "status": status,
            "score": new_score,
            "delta": points,
            "event": event
        }

    def get_session_report(self, session_id: str) -> Dict:
        return {
            "session_id": session_id,
            "current_score": self.session_scores.get(session_id, 0),
            "events": [e for e in self.event_history if e["session_id"] == session_id]
        }

    def reset_session(self, session_id: str):
        if session_id in self.session_scores:
            del self.session_scores[session_id]
