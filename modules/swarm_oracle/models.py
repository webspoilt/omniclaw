from typing import Any

from pydantic import BaseModel


class SimulationRequest(BaseModel):
    context: str


class AuditResultModel(BaseModel):
    passed: bool
    reason: str | None = None
    score: float = 0.0


class SimulationResult(BaseModel):
    context: str
    output: dict[str, Any]  # e.g., aggregated, individual
    audit: AuditResultModel
