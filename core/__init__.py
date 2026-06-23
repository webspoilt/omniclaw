"""
OmniClaw: The Hybrid Hive AI Agent System
Core Module - Multi-API Orchestrator with Manager-Worker Architecture
"""

__version__ = "3.2.0"
__author__ = "Me"
__license__ = "MIT"

from .api_pool import APIPool
from .audit_diff import AuditDiff
from .autonomous_fix import AutonomousFix, ErrorParser
from .context_mapper import ContextMapper
from .decision_archaeology import DecisionArchaeologist
from .echo_chambers import EchoChamber
from .living_docs import LivingDocumentation
from .manager import ManagerAgent
from .memory import VectorMemory
from .orchestrator import HybridHiveOrchestrator
from .pattern_sentinel import PatternSentinel

# Advanced Features
from .reasoning_config import ReasoningConfig, ReasoningLock, ThinkingLevel
from .semantic_diff import SemanticDiff
from .temporal_memory import TemporalContext
from .worker import WorkerAgent

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
        AutonomousProductManager,
        CodeDNAInterpreter,
        ConsciousnessCollision,
        ContractEnforcer,
        LivingArchitectureDiagram,
        MemoryGraphNetwork,
        NaturalLanguageInfra,
        OmniClawLauncher,
        ParadigmTranslator,
        PredictorEngine,
        SecurityResearchHub,
        SelfEvolvingIntelligenceCore,
        TimeMachineDebugger,
    )
except ImportError:
    pass  # Advanced features are optional
