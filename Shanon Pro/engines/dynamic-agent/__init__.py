# Shannon Pro - Stage 2: Dynamic Pentesting Agent
# Autonomous vulnerability validation using browser automation
#
# Architecture: Exploit Queue -> Agent Controller -> Browser Farm -> Evidence

from .agent_controller import AgentController, AgentConfig
from .injection_agent import InjectionAgent, ExploitResult
from .playwright_mapper import PlaywrightScriptMapper, PlaywrightScript
from .poc_validator import POCValidator, POCResult, POCStatus
from .strategies import SQLiStrategy, XSSStrategy, CommandInjectionStrategy
from .models import ExploitTask, VulnType, ValidationEvidence

__all__ = [
    "AgentController",
    "AgentConfig",
    "InjectionAgent",
    "ExploitResult",
    "PlaywrightScriptMapper",
    "PlaywrightScript",
    "POCValidator",
    "POCResult",
    "POCStatus",
    "SQLiStrategy",
    "XSSStrategy",
    "CommandInjectionStrategy",
    "ExploitTask",
    "VulnType",
    "ValidationEvidence",
]
