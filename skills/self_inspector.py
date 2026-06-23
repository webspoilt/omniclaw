"""Inspect own source code, imports, and tool registry."""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Any

from core.skills.registry import get_tool_registry, tool


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@tool(
    name="read_own_source",
    description="Read and return the full source code of any Python file in the project.",
    parameters={
        "relative_path": {
            "type": "string",
            "description": "Path relative to project root, e.g. 'core/skills/registry.py'",
        },
    },
    required=["relative_path"],
)
async def read_own_source(relative_path: str) -> str:
    target = _project_root() / relative_path
    target = target.resolve()
    if not str(target).startswith(str(_project_root())):
        return f"Error: path escapes project root: {target}"
    if not target.is_file() or target.suffix != ".py":
        return f"Error: not a Python file: {target}"
    return target.read_text(encoding="utf-8")


@tool(
    name="find_own_imports",
    description="Parse a Python file and return all its import statements (stdlib, local, third-party).",
    parameters={
        "relative_path": {
            "type": "string",
            "description": "Path relative to project root, e.g. 'planner_service/main.py'",
        },
    },
    required=["relative_path"],
)
async def find_own_imports(relative_path: str) -> dict[str, list[str]]:
    target = _project_root() / relative_path
    target = target.resolve()
    if not str(target).startswith(str(_project_root())):
        return {"error": "path escapes project root"}
    if not target.is_file():
        return {"error": "file not found"}

    tree = ast.parse(target.read_text(encoding="utf-8"))
    stdlib: list[str] = []
    local: list[str] = []
    third_party: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in sys.stdlib_module_names:
                    stdlib.append(alias.name)
                else:
                    third_party.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                if mod.startswith("core") or mod.startswith("skills") or mod.startswith("modules"):
                    local.append(node.module)
                elif mod in sys.stdlib_module_names:
                    stdlib.append(node.module)
                else:
                    third_party.append(node.module)

    return {"stdlib": sorted(set(stdlib)), "local": sorted(set(local)), "third_party": sorted(set(third_party))}


@tool(
    name="list_own_tools",
    description="Return all registered tool names and their descriptions.",
    parameters={},
)
async def list_own_tools() -> list[dict[str, Any]]:
    reg = get_tool_registry()
    return [
        {"name": name, "description": info.description}
        for name, info in reg.tools.items()
    ]


@tool(
    name="get_file_metadata",
    description="Return size, line count, and last modified time for a project file.",
    parameters={
        "relative_path": {
            "type": "string",
            "description": "Path relative to project root",
        },
    },
    required=["relative_path"],
)
async def get_file_metadata(relative_path: str) -> dict[str, Any]:
    target = _project_root() / relative_path
    target = target.resolve()
    if not str(target).startswith(str(_project_root())):
        return {"error": "path escapes project root"}
    if not target.exists():
        return {"error": "not found"}
    stat = target.stat()
    return {
        "path": str(target.relative_to(_project_root())),
        "size_bytes": stat.st_size,
        "lines": len(target.read_text(encoding="utf-8").splitlines()) if target.is_file() else None,
        "modified": stat.st_mtime,
        "is_file": target.is_file(),
        "is_dir": target.is_dir(),
    }


@tool(
    name="get_project_tree",
    description="Return a recursive listing of the project directory tree (depth-limited).",
    parameters={
        "max_depth": {
            "type": "integer",
            "description": "Maximum directory depth to traverse (default 3)",
        },
    },
    required=[],
)
async def get_project_tree(max_depth: int = 3) -> list[str]:
    root = _project_root()
    entries: list[str] = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", ".next", ".mypy_cache", "legacy", "data"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        indent = "  " * depth
        entries.append(f"{indent}{rel.name}/")
        for f in sorted(filenames):
            if f.endswith(".py"):
                entries.append(f"{indent}  {f}")
    return entries
