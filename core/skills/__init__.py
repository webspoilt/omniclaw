"""
OmniClaw Skill System
=====================
Decorator-based tool registry with auto-loading from user skill directories.
Ported from NanoClaw's tools/registry.py.
"""

import logging
from pathlib import Path

from core.skills.loader import SkillLoader
from core.skills.registry import ToolInfo, ToolRegistry, tool

logger = logging.getLogger("OmniClaw.Skills")

# Core Internal Skills
import core.skills.injection_auditor
import core.skills.osint_reputation
import core.skills.osint_sentiment
import core.skills.social_spider
import core.skills.wifi_recon  # noqa: F401

# Auto-load all .py skills from the project skills/ directory (unconditional)
_project_skills = Path(__file__).resolve().parent.parent.parent / "skills"
if _project_skills.is_dir():
    _loader = SkillLoader(skills_dir=str(_project_skills))
    _loaded = _loader.load_all()
    if _loaded:
        logger.info(f"Auto-loaded {_loaded} skill(s) from {_project_skills}")

    # Discover SKILL.md-based skill definitions
    _discovered = 0
    for _entry in sorted(_project_skills.iterdir()):
        if _entry.is_dir():
            _skill_md = _entry / "SKILL.md"
            if _skill_md.exists():
                _discovered += 1
                logger.debug(f"Discovered skill definition: {_entry.name}")
    if _discovered:
        logger.info(f"Discovered {_discovered} SKILL.md skill definition(s) in {_project_skills}")

__all__ = ["ToolRegistry", "ToolInfo", "tool", "SkillLoader"]
