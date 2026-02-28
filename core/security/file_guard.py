"""
FileGuard — Workspace-scoped file access control.

Ported from NanoClaw's security/sandbox.py.
All file operations are restricted to the workspace directory.
Blocks access to sensitive files (.env, .ssh, private keys, etc.)
and detects symlink escape attacks.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("OmniClaw.Security.FileGuard")


class SecurityError(Exception):
    """Security violation error."""
    pass


class FileGuard:
    """All file operations restricted to workspace directory only."""

    # Blocked path component names (matched case-insensitively)
    BLOCKED_COMPONENTS = [
        ".env", ".git", ".ssh", ".gnupg", ".aws", ".kube", ".docker",
        ".config", "__pycache__",
    ]

    # Blocked file name patterns (matched case-insensitively)
    BLOCKED_FILENAMES = [
        "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
        "private_key", "config.json", "credentials",
        "token.json", "secrets.yaml", "secrets.json",
    ]

    # Blocked file name prefixes (matched case-insensitively)
    BLOCKED_PREFIXES = [
        ".env.",  # .env.local, .env.production, etc.
    ]

    def __init__(self, workspace_dir: str | Path):
        """
        Initialize FileGuard.

        Args:
            workspace_dir: Path to the workspace directory
        """
        self.workspace = Path(workspace_dir).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        logger.debug(f"FileGuard workspace: {self.workspace}")

    def validate_path(self, path: str) -> Path:
        """
        Validate and resolve a path within workspace.

        Args:
            path: Relative path to validate

        Returns:
            Resolved absolute path within workspace

        Raises:
            SecurityError: If path escapes workspace
        """
        if not path or path == ".":
            return self.workspace

        # Reject null bytes (filesystem truncation attack)
        if "\x00" in path:
            raise SecurityError("ACCESS DENIED: null byte in path")

        # Resolve the path relative to workspace
        resolved = (self.workspace / path).resolve()

        # Check if resolved path is within workspace
        try:
            resolved.relative_to(self.workspace)
        except ValueError:
            raise SecurityError(f"ACCESS DENIED: path outside workspace: {path}")

        return resolved

    def is_symlink_safe(self, path: Path) -> bool:
        """
        Check if a path is a symlink pointing outside the workspace.

        Returns:
            True if safe (not a symlink, or symlink within workspace)
        """
        if not path.is_symlink():
            return True
        try:
            target = path.resolve()
            target.relative_to(self.workspace)
            return True
        except ValueError:
            return False

    def is_safe_to_read(self, path: Path) -> bool:
        """Check if a file is safe to read."""
        if not self.is_symlink_safe(path):
            return False

        resolved = path.resolve()
        parts = [p.lower() for p in resolved.parts]
        filename = resolved.name.lower()

        for component in parts:
            if component in self.BLOCKED_COMPONENTS:
                return False

        if filename in self.BLOCKED_FILENAMES:
            return False

        for prefix in self.BLOCKED_PREFIXES:
            if filename.startswith(prefix):
                return False

        return True

    def is_safe_to_write(self, path: Path) -> bool:
        """Check if a file path is safe to write to."""
        if path.exists() and not self.is_symlink_safe(path):
            return False

        resolved = path.resolve() if path.exists() else path
        parts = [p.lower() for p in resolved.parts]
        filename = resolved.name.lower()

        for component in parts:
            if component in self.BLOCKED_COMPONENTS:
                return False

        if filename in self.BLOCKED_FILENAMES:
            return False

        for prefix in self.BLOCKED_PREFIXES:
            if filename.startswith(prefix):
                return False

        return True

    def safe_read(self, relative_path: str) -> str:
        """
        Safely read a file within workspace.

        Args:
            relative_path: Path relative to workspace

        Returns:
            File contents

        Raises:
            SecurityError: If path is blocked
        """
        path = self.validate_path(relative_path)
        if not self.is_safe_to_read(path):
            raise SecurityError(f"ACCESS DENIED: blocked file: {relative_path}")
        if not path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return path.read_text(encoding="utf-8", errors="replace")

    def safe_write(self, relative_path: str, content: str) -> Path:
        """
        Safely write a file within workspace.

        Args:
            relative_path: Path relative to workspace
            content: Content to write

        Returns:
            Written file path

        Raises:
            SecurityError: If path is blocked
        """
        path = self.validate_path(relative_path)
        if not self.is_safe_to_write(path):
            raise SecurityError(f"ACCESS DENIED: blocked file: {relative_path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def safe_list(self, relative_path: str = ".") -> list[dict]:
        """
        Safely list directory contents within workspace.

        Returns:
            List of {name, type, size} dicts
        """
        path = self.validate_path(relative_path)
        if not path.is_dir():
            raise SecurityError(f"Not a directory: {relative_path}")

        entries = []
        for item in sorted(path.iterdir()):
            if not self.is_safe_to_read(item):
                continue
            entries.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return entries
