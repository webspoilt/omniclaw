"""Text compression and key-fact extraction for keeping memory lean."""
from __future__ import annotations

import math
import re

from core.skills.registry import tool


@tool(
    name="compress_by_truncation",
    description="Truncate text to a target char count, preserving the most informative parts (first 20% + last 80% of budget).",
    parameters={
        "text": {"type": "string", "description": "Text to compress"},
        "max_chars": {"type": "integer", "description": "Maximum characters in output"},
    },
    required=["text", "max_chars"],
)
async def compress_by_truncation(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head_budget = max_chars // 5
    tail_budget = max_chars - head_budget - 3
    return text[:head_budget] + "\n...\n" + text[-tail_budget:]


@tool(
    name="extract_key_facts",
    description="Extract lines containing key indicators (numbers, results, conclusions) from text.",
    parameters={
        "text": {"type": "string", "description": "Text to analyse"},
        "max_lines": {"type": "integer", "description": "Maximum lines to return"},
    },
    required=["text", "max_lines"],
)
async def extract_key_facts(text: str, max_lines: int = 30) -> str:
    lines = text.splitlines()
    scored: list[tuple[float, str]] = []

    key_indicators = [
        r"\b\d+\.?\d*%", r"error", r"fail", r"success", r"result", r"exit code",
        r"exit \d+", r"returned", r"compil", r"warn", r"traceback", r"exception",
        r"memory", r"cpu", r"timeout", r"duration", r"ms\b", r"bytes",
        r"installed", r"created", r"wrote", r"patched", r"modified",
    ]
    patterns = [re.compile(p, re.IGNORECASE) for p in key_indicators]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        score = 0.0
        for pat in patterns:
            if pat.search(stripped):
                score += 1.0
        if score > 0:
            scored.append((score, stripped))

    scored.sort(key=lambda x: -x[0])
    return "\n".join(line for _, line in scored[:max_lines])


@tool(
    name="rank_importance",
    description="Rank lines or paragraphs by estimated importance heuristics (length, digits, key terms).",
    parameters={
        "text": {"type": "string", "description": "Text to analyse"},
        "top_n": {"type": "integer", "description": "Number of top items to return"},
    },
    required=["text"],
)
async def rank_importance(text: str, top_n: int = 20) -> list[dict]:
    items = text.split("\n\n") if "\n\n" in text else text.splitlines()
    scored: list[tuple[float, str]] = []
    for item in items:
        stripped = item.strip()
        if not stripped or len(stripped) < 10:
            continue
        score = 0.0
        score += min(len(stripped) / 200, 3.0)
        score += sum(c.isdigit() for c in stripped) * 0.1
        for kw in ["error", "fail", "success", "result", "exit", "key", "found", "changed", "new", "best"]:
            if kw in stripped.lower():
                score += 1.0
        scored.append((score, stripped))

    scored.sort(key=lambda x: -x[0])
    return [{"rank": i + 1, "score": round(s, 1), "text": t[:200]} for i, (s, t) in enumerate(scored[:top_n])]


@tool(
    name="count_tokens_estimate",
    description="Estimate token count for a string using a rough 4-char-per-token rule.",
    parameters={
        "text": {"type": "string", "description": "Text to estimate"},
    },
    required=["text"],
)
async def count_tokens_estimate(text: str) -> dict:
    chars = len(text)
    est_tokens = math.ceil(chars / 4)
    return {
        "characters": chars,
        "estimated_tokens": est_tokens,
        "lines": text.count("\n") + 1,
        "words": len(text.split()),
    }
