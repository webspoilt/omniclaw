"""
OmniClaw: The Hybrid Hive AI Agent System
Core Module - Multi-API Orchestrator with Manager-Worker Architecture
"""

__version__ = "3.2.0"
__author__ = "Me"
__license__ = "MIT"

from .orchestrator import HybridHiveOrchestrator
from .worker import WorkerAgent
from .manager import ManagerAgent
from .memory import VectorMemory
from .api_pool import APIPool

# Advanced Features
from .reasoning_config import ReasoningLock, ReasoningConfig, ThinkingLevel
from .context_mapper import ContextMapper
from .autonomous_fix import AutonomousFix, ErrorParser
from .audit_diff import AuditDiff
from .temporal_memory import TemporalContext
from .decision_archaeology import DecisionArchaeologist
from .pattern_sentinel import PatternSentinel
from .echo_chambers import EchoChamber
from .living_docs import LivingDocumentation
from .semantic_diff import SemanticDiff

__all__ = [
    # Core
    "HybridHiveOrchestrator",
    "WorkerAgent", 
    "ManagerAgent",
    "VectorMemory",
    "APIPool",
    # Advanced Features
    "ReasoningLock",
    "ReasoningConfig",
    "ThinkingLevel",
    "ContextMapper",
    "AutonomousFix",
    "ErrorParser",
    "AuditDiff",
    "TemporalContext",
    "DecisionArchaeologist",
    "PatternSentinel",
    "EchoChamber",
    "LivingDocumentation",
    "SemanticDiff",
    # Advanced Features Package
    "ConsciousnessCollision",
    "CodeDNAInterpreter",
    "TimeMachineDebugger",
    "MemoryGraphNetwork",
    "PredictorEngine",
    "ContractEnforcer",
    "ParadigmTranslator",
    "NaturalLanguageInfra",
    "LivingArchitectureDiagram",
    "AutonomousProductManager",
    "SelfEvolvingIntelligenceCore",
    "SecurityResearchHub",
    "OmniClawLauncher",
]

# Advanced Features Package
try:
    from .advanced_features import (
        ConsciousnessCollision,
        CodeDNAInterpreter,
        TimeMachineDebugger,
        MemoryGraphNetwork,
        PredictorEngine,
        ContractEnforcer,
        ParadigmTranslator,
        NaturalLanguageInfra,
        LivingArchitectureDiagram,
        AutonomousProductManager,
        SelfEvolvingIntelligenceCore,
        SecurityResearchHub,
        OmniClawLauncher,
    )
except ImportError:
    pass  # Advanced features are optional
