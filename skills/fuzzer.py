"""Fuzz tool inputs and agent parsers to find edge cases and crashes."""
from __future__ import annotations

import random
import string
from typing import Any

from core.skills.registry import tool

_CHARSET = string.ascii_letters + string.digits + string.punctuation + " \t\n\r"


def _mutate(base: str, rate: float = 0.1) -> str:
    chars = list(base)
    for i in range(len(chars)):
        if random.random() < rate:
            chars[i] = random.choice(_CHARSET)
    return "".join(chars)


@tool(
    name="fuzz_tool_input",
    description="Generate fuzzed variants of a known good input string for testing.",
    parameters={
        "base_input": {"type": "string", "description": "Known good input to mutate"},
        "count": {"type": "integer", "description": "Number of variants to generate"},
        "mutation_rate": {"type": "number", "description": "Per-character mutation probability (0-1)"},
    },
    required=["base_input"],
)
async def fuzz_tool_input(base_input: str, count: int = 10, mutation_rate: float = 0.1) -> list[str]:
    variants: set[str] = set()
    max_attempts = count * 5
    attempts = 0
    while len(variants) < count and attempts < max_attempts:
        variant = _mutate(base_input, mutation_rate)
        if variant != base_input:
            variants.add(variant)
        attempts += 1
    return list(variants)[:count]


@tool(
    name="generate_variations",
    description="Generate systematic input variations (empty, very long, unicode, control chars, etc).",
    parameters={
        "base_value": {"type": "string", "description": "Base value to generate variations of"},
    },
    required=["base_value"],
)
async def generate_variations(base_value: str) -> dict[str, str]:
    return {
        "empty": "",
        "whitespace": "   ",
        "newlines": "\n\n\n",
        "null_byte": "\x00",
        "control_chars": "\x01\x02\x03\x04",
        "unicode": "你好世界ñññ😀🔥💀",
        "very_long": base_value * 100,
        "sql_injection": "'; DROP TABLE skills; --",
        "shell_injection": "`rm -rf /`",
        "path_traversal": "../../etc/passwd",
        "base_value": base_value,
    }


@tool(
    name="record_crash",
    description="Record a crash/error signature for later analysis.",
    parameters={
        "tool_name": {"type": "string", "description": "Name of the tool that crashed"},
        "input_summary": {"type": "string", "description": "What input caused the crash"},
        "error_message": {"type": "string", "description": "Error message or traceback"},
        "severity": {"type": "string", "description": "crash, hang, wrong_output"},
    },
    required=["tool_name", "input_summary", "error_message"],
)
async def record_crash(tool_name: str, input_summary: str, error_message: str, severity: str = "crash") -> str:
    import json
    import time
    from pathlib import Path
    crash_dir = Path(__file__).resolve().parent.parent / "data" / "crashes"
    crash_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.time(),
        "tool": tool_name,
        "input": input_summary[:500],
        "error": error_message[:2000],
        "severity": severity,
    }
    path = crash_dir / f"crash_{int(time.time())}.json"
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return f"Crash recorded to {path}"


@tool(
    name="list_recorded_crashes",
    description="List all recorded crash signatures from the crash log directory.",
    parameters={},
)
async def list_recorded_crashes() -> list[dict[str, Any]]:
    import json
    from pathlib import Path
    crash_dir = Path(__file__).resolve().parent.parent / "data" / "crashes"
    if not crash_dir.exists():
        return []
    crashes = []
    for f in sorted(crash_dir.glob("crash_*.json"))[-50:]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["file"] = f.name
            crashes.append(data)
        except Exception:
            pass
    return crashes
