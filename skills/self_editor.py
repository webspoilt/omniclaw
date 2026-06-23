"""Modify own source code and restart the agent process."""
from __future__ import annotations

import os
import sys
import signal
from pathlib import Path
from typing import Optional

from core.skills.registry import tool


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@tool(
    name="patch_own_file",
    description="Apply a string replacement to a Python file in the project. Returns diff.",
    parameters={
        "relative_path": {"type": "string", "description": "Path relative to project root"},
        "old_string": {"type": "string", "description": "Text to replace (must be unique in file)"},
        "new_string": {"type": "string", "description": "Replacement text"},
        "create_backup": {"type": "boolean", "description": "Save .bak before modifying"},
    },
    required=["relative_path", "old_string", "new_string"],
)
async def patch_own_file(relative_path: str, old_string: str, new_string: str, create_backup: bool = True) -> str:
    target = _project_root() / relative_path
    target = target.resolve()
    if not str(target).startswith(str(_project_root())):
        return "Error: path escapes project root"
    if not target.is_file():
        return "Error: file not found"
    if target.suffix not in (".py", ".sh", ".yaml", ".yml", ".json", ".toml", ".md", ".cfg", ".txt", ".c", ".h", ".rs"):
        return f"Error: unsupported extension {target.suffix}"

    original = target.read_text(encoding="utf-8")
    count = original.count(old_string)
    if count == 0:
        return "Error: old_string not found in file"
    if count > 1:
        return "Error: old_string appears multiple times — provide more context"

    if create_backup:
        backup = target.with_suffix(target.suffix + ".bak")
        backup.write_text(original, encoding="utf-8")

    modified = original.replace(old_string, new_string)
    target.write_text(modified, encoding="utf-8")

    return f"Patched {target.name}. {len(modified)} chars written."


@tool(
    name="replace_method_in_file",
    description="Replace an entire function/method body in a Python file by matching its signature.",
    parameters={
        "relative_path": {"type": "string", "description": "Path relative to project root"},
        "function_name": {"type": "string", "description": "Exact function name to replace"},
        "new_body": {"type": "string", "description": "Full new function body (including def line)"},
    },
    required=["relative_path", "function_name", "new_body"],
)
async def replace_method_in_file(relative_path: str, function_name: str, new_body: str) -> str:
    import ast
    target = _project_root() / relative_path
    target = target.resolve()
    if not str(target).startswith(str(_project_root())):
        return "Error: path escapes project root"
    if not target.is_file():
        return "Error: file not found"

    source = target.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"Error: syntax error in file: {e}"

    found = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            found = node
            break

    if found is None:
        return f"Error: function '{function_name}' not found"

    orig_start = found.lineno - 1
    orig_end = found.end_lineno if hasattr(found, 'end_lineno') else orig_start + 1
    source_lines = source.splitlines(keepends=True)
    new_lines = new_body.splitlines(keepends=True)
    result = source_lines[:orig_start] + new_lines + source_lines[orig_end:]

    target.write_text("".join(result), encoding="utf-8")
    return f"Replaced function '{function_name}' ({len(new_lines)} lines)"


@tool(
    name="restart_self",
    description="Restart the current Python process by exec()-ing a new interpreter. Use with care.",
    parameters={
        "target_script": {
            "type": "string",
            "description": "Script to exec (relative to project root). Default: current __main__",
        },
    },
    required=[],
)
async def restart_self(target_script: Optional[str] = None) -> str:
    if target_script:
        script = _project_root() / target_script
        script = script.resolve()
        if not str(script).startswith(str(_project_root())):
            return "Error: path escapes project root"
    else:
        script = Path(sys.argv[0]).resolve()

    os.execv(sys.executable, [sys.executable, str(script)])
    return "Restart initiated (should not reach this line)"


@tool(
    name="write_new_module",
    description="Create a new Python module file in the project. Overwrites if exists.",
    parameters={
        "relative_path": {"type": "string", "description": "Path relative to project root, e.g. 'skills/my_skill.py'"},
        "source_code": {"type": "string", "description": "Complete Python source text"},
    },
    required=["relative_path", "source_code"],
)
async def write_new_module(relative_path: str, source_code: str) -> str:
    target = _project_root() / relative_path
    target = target.resolve()
    if not str(target).startswith(str(_project_root())):
        return "Error: path escapes project root"
    if not target.suffix == ".py":
        return "Error: only .py files can be created"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source_code, encoding="utf-8")
    return f"Created {target.name} ({len(source_code)} chars)"
