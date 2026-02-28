"""
SkillLoader — Auto-discover and load custom skills from user directory.

Ported from NanoClaw's tools/registry.py load_skills method.
Loads .py files from a skills directory, validating ownership and permissions.
"""

from __future__ import annotations

import importlib.util
import os
import logging
from pathlib import Path
from typing import Optional

from core.skills.registry import ToolRegistry, _registry

logger = logging.getLogger("OmniClaw.Skills.Loader")


class SkillLoader:
    """Auto-discover and load custom skill files."""

    def __init__(self, skills_dir: str | Path = "~/.omniclaw/skills"):
        """
        Initialize SkillLoader.

        Args:
            skills_dir: Path to skills directory (supports ~ expansion)
        """
        self.skills_dir = Path(os.path.expanduser(str(skills_dir)))
        self.loaded_skills: list[str] = []
        self.failed_skills: list[dict] = []

    def load_all(self, registry: Optional[ToolRegistry] = None) -> int:
        """
        Load all skill files from the skills directory.

        Args:
            registry: Optional ToolRegistry to update

        Returns:
            Number of skills loaded
        """
        if not self.skills_dir.exists():
            logger.debug(f"Skills directory not found: {self.skills_dir}")
            return 0

        # Validate directory safety on Unix
        if os.name != "nt":
            try:
                import stat
                dir_stat = self.skills_dir.stat()
                if dir_stat.st_uid != os.getuid():
                    logger.warning(f"Skills directory not owned by current user: {self.skills_dir}")
                    return 0
                if dir_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                    logger.warning(f"Skills directory writable by others: {self.skills_dir}")
                    return 0
            except (OSError, AttributeError):
                pass

        count = 0
        for py_file in sorted(self.skills_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue

            # Validate file safety on Unix
            if os.name != "nt":
                try:
                    import stat
                    file_stat = py_file.stat()
                    if file_stat.st_uid != os.getuid():
                        logger.warning(f"Skipping skill {py_file.name}: not owned by current user")
                        continue
                    if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                        logger.warning(f"Skipping skill {py_file.name}: writable by group/others")
                        continue
                except (OSError, AttributeError):
                    continue

            if self._load_skill_file(py_file):
                count += 1

        # Merge newly loaded tools into registry
        if registry is not None:
            registry.tools.update(_registry)

        logger.info(f"Loaded {count} skill(s) from {self.skills_dir}")
        return count

    def _load_skill_file(self, py_file: Path) -> bool:
        """
        Load a single skill .py file.

        Returns:
            True if loaded successfully
        """
        try:
            spec = importlib.util.spec_from_file_location(
                f"omniclaw_skill_{py_file.stem}", py_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_skills.append(py_file.name)
                logger.debug(f"Loaded skill: {py_file.name}")
                return True
        except Exception as e:
            self.failed_skills.append({
                "file": py_file.name,
                "error": str(e),
            })
            logger.error(f"Failed to load skill {py_file.name}: {e}")
        return False

    def get_status(self) -> dict:
        """Get loader status."""
        return {
            "skills_dir": str(self.skills_dir),
            "dir_exists": self.skills_dir.exists(),
            "loaded": self.loaded_skills,
            "failed": self.failed_skills,
        }
