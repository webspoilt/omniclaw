"""
OmniClaw Automation Module
Financial automation, trading, and earning workflows
"""

from .trading import TradingInterface, TradingPlatform
from .bug_bounty import BugBountyHunter
from .research import ResearchAgent

__all__ = [
    "TradingInterface",
    "TradingPlatform", 
    "BugBountyHunter",
    "ResearchAgent"
]
