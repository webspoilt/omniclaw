"""
OmniClaw Swarm Oracle Module
Integrates MiroFish swarm intelligence (Ollama + ChromaDB) into OmniClaw.
"""

from .auditor import Auditor
from .knowledge import KnowledgeGraph
from .manager import Manager
from .models import AuditResultModel, SimulationRequest, SimulationResult
from .swarm_engine import SwarmSimulator

__all__ = [
    "SimulationRequest",
    "SimulationResult",
    "AuditResultModel",
    "SwarmSimulator",
    "Manager",
    "Auditor",
    "KnowledgeGraph"
]
