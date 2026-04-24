"""
OmniClaw Skill System
=====================
Decorator-based tool registry with auto-loading from user skill directories.
Ported from NanoClaw's tools/registry.py.
"""

from core.skills.registry import ToolRegistry, ToolInfo, tool
from core.skills.loader import SkillLoader

# Core Internal Skills
import core.skills.wifi_recon
import core.skills.osint_reputation
import core.skills.injection_auditor
import core.skills.osint_sentiment
import core.skills.social_spider

__all__ = ["ToolRegistry", "ToolInfo", "tool", "SkillLoader"]
