"""
OmniClaw: The Hybrid Hive AI Agent System
Core Module - Multi-API Orchestrator with Manager-Worker Architecture
"""

__version__ = "1.0.0"
__author__ = "Me"
__license__ = "MIT"

from .orchestrator import HybridHiveOrchestrator
from .worker import WorkerAgent
from .manager import ManagerAgent
from .memory import VectorMemory
from .api_pool import APIPool

__all__ = [
    "HybridHiveOrchestrator",
    "WorkerAgent", 
    "ManagerAgent",
    "VectorMemory",
    "APIPool"
]
