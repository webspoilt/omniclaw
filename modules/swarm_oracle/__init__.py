"""
OmniClaw Swarm Oracle Module
Integrates MiroFish swarm intelligence (Ollama + ChromaDB) into OmniClaw.
"""

from .models import SimulationRequest, SimulationResult, AuditResultModel
from .swarm_engine import SwarmSimulator
from .manager import Manager
from .auditor import Auditor
from .knowledge import KnowledgeGraph

__all__ = [
    "SimulationRequest",
    "SimulationResult", 
    "AuditResultModel",
    "SwarmSimulator",
    "Manager",
    "Auditor",
    "KnowledgeGraph"
]
