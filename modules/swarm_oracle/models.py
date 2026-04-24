from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class SimulationRequest(BaseModel):
    context: str


class AuditResultModel(BaseModel):
    passed: bool
    reason: Optional[str] = None
    score: float = 0.0


class SimulationResult(BaseModel):
    context: str
    output: Dict[str, Any]  # e.g., aggregated, individual
    audit: AuditResultModel
