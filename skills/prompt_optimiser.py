"""Dynamically rewrite system prompts based on performance."""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

from core.skills.registry import tool

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "data" / "prompts"


@tool(
    name="store_prompt",
    description="Save a prompt variant with a label and score for later comparison.",
    parameters={
        "label": {"type": "string", "description": "Short label for this prompt, e.g. 'sys_prompt_v3_detailed'"},
        "text": {"type": "string", "description": "Full prompt text"},
        "initial_score": {"type": "number", "description": "Initial quality score (0-10)"},
    },
    required=["label", "text"],
)
async def store_prompt(label: str, text: str, initial_score: float | None = None) -> str:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "label": label,
        "text": text,
        "score": initial_score,
        "created": time.time(),
        "mutations": 0,
    }
    path = _PROMPTS_DIR / f"{label.replace(' ', '_')}.json"
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return f"Stored prompt '{label}' ({len(text)} chars)"


@tool(
    name="mutate_prompt",
    description="Create a mutated variant of an existing prompt by applying random edits.",
    parameters={
        "source_label": {"type": "string", "description": "Label of the prompt to mutate"},
        "new_label": {"type": "string", "description": "Label for the new variant"},
        "mutation_type": {"type": "string", "description": "Type: truncate, expand, rephrase, shuffle_paragraphs"},
    },
    required=["source_label", "new_label"],
)
async def mutate_prompt(source_label: str, new_label: str, mutation_type: str = "rephrase") -> str:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    source_path = _PROMPTS_DIR / f"{source_label.replace(' ', '_')}.json"
    if not source_path.exists():
        return f"Error: prompt '{source_label}' not found"

    source = json.loads(source_path.read_text(encoding="utf-8"))
    text = source["text"]
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    if mutation_type == "truncate" and len(paragraphs) > 2:
        text = "\n\n".join(paragraphs[:max(2, len(paragraphs) // 2)])
    elif mutation_type == "expand":
        text = text + f"\n\n(Additional context: iteration at {time.strftime('%H:%M:%S')})"
    elif mutation_type == "shuffle_paragraphs" and len(paragraphs) > 1:
        random.shuffle(paragraphs)
        text = "\n\n".join(paragraphs)
    else:
        text = text

    entry = {
        "label": new_label,
        "text": text,
        "score": None,
        "created": time.time(),
        "mutations": source.get("mutations", 0) + 1,
        "parent": source_label,
        "mutation_type": mutation_type,
    }
    new_path = _PROMPTS_DIR / f"{new_label.replace(' ', '_')}.json"
    new_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return f"Created mutation '{new_label}' from '{source_label}' via {mutation_type}"


@tool(
    name="score_prompt",
    description="Record a performance score for a prompt variant.",
    parameters={
        "label": {"type": "string", "description": "Prompt label"},
        "score": {"type": "number", "description": "Score 0-10 based on observed performance"},
        "notes": {"type": "string", "description": "Why this score was assigned"},
    },
    required=["label", "score"],
)
async def score_prompt(label: str, score: float, notes: str | None = None) -> str:
    path = _PROMPTS_DIR / f"{label.replace(' ', '_')}.json"
    if not path.exists():
        return f"Error: prompt '{label}' not found"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["score"] = score
    data["scored_at"] = time.time()
    if notes:
        data["score_notes"] = notes
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"Scored '{label}' at {score}/10"


@tool(
    name="evolve_prompt",
    description="Return the best-performing prompt variant. Creates mutations if fewer than 3 exist.",
    parameters={
        "min_variants": {"type": "integer", "description": "Minimum variants to have before picking best"},
    },
    required=[],
)
async def evolve_prompt(min_variants: int = 3) -> dict[str, Any]:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    prompts = []
    for f in _PROMPTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["file"] = f.name
            prompts.append(data)
        except Exception:
            pass

    if len(prompts) < min_variants:
        return {
            "status": f"only {len(prompts)} variant(s), need {min_variants}",
            "variant_count": len(prompts),
            "best": None,
        }

    scored = [p for p in prompts if p.get("score") is not None]
    if not scored:
        return {
            "status": "no scored variants yet",
            "variant_count": len(prompts),
            "best": None,
        }

    best = max(scored, key=lambda p: p["score"])
    return {
        "status": "found",
        "variant_count": len(prompts),
        "scored_count": len(scored),
        "best": {
            "label": best["label"],
            "score": best["score"],
            "text_length": len(best["text"]),
            "mutations": best.get("mutations", 0),
        },
        "all_scores": {p["label"]: p.get("score") for p in scored},
    }


@tool(
    name="list_prompt_variants",
    description="List all stored prompt variants with their scores.",
    parameters={},
)
async def list_prompt_variants() -> list[dict[str, Any]]:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    variants = []
    for f in sorted(_PROMPTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            variants.append({
                "label": data["label"],
                "score": data.get("score"),
                "char_count": len(data["text"]),
                "mutations": data.get("mutations", 0),
                "parent": data.get("parent"),
            })
        except Exception:
            pass
    return variants
