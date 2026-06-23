"""Record experiments, A/B test prompts, and track strategy performance."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core.skills.registry import tool

LEARN_DIR = Path(__file__).resolve().parent.parent / "data" / "learning"


def _ensure_store():
    LEARN_DIR.mkdir(parents=True, exist_ok=True)
    return LEARN_DIR / "experiments.jsonl"


@tool(
    name="log_experiment",
    description="Record an experiment result with strategy name, outcome, and metrics.",
    parameters={
        "strategy": {"type": "string", "description": "Short name for the strategy tested"},
        "outcome": {"type": "string", "description": "What happened: success, failure, partial"},
        "metrics_json": {"type": "string", "description": "JSON string of numeric metrics, e.g. '{\"duration_ms\":1500}'"},
        "notes": {"type": "string", "description": "Free-text observations"},
    },
    required=["strategy", "outcome"],
)
async def log_experiment(strategy: str, outcome: str, metrics_json: str | None = None, notes: str | None = None) -> str:
    path = _ensure_store()
    metrics = {}
    if metrics_json:
        try:
            metrics = json.loads(metrics_json)
        except json.JSONDecodeError:
            return "Error: invalid metrics_json"
    entry = {
        "timestamp": time.time(),
        "strategy": strategy,
        "outcome": outcome,
        "metrics": metrics,
        "notes": notes or "",
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return f"Logged experiment: {strategy} -> {outcome}"


@tool(
    name="compare_strategies",
    description="Compare two strategies by their average metrics across all logged experiments.",
    parameters={
        "strategy_a": {"type": "string", "description": "First strategy name"},
        "strategy_b": {"type": "string", "description": "Second strategy name"},
        "metric_key": {"type": "string", "description": "Metric to compare, e.g. 'duration_ms'"},
    },
    required=["strategy_a", "strategy_b", "metric_key"],
)
async def compare_strategies(strategy_a: str, strategy_b: str, metric_key: str) -> dict[str, Any]:
    records_a: list[float] = []
    records_b: list[float] = []
    path = _ensure_store()
    if not path.exists():
        return {"error": "no experiments logged yet"}

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            val = entry.get("metrics", {}).get(metric_key)
            if val is None:
                continue
            if entry["strategy"] == strategy_a:
                records_a.append(val)
            elif entry["strategy"] == strategy_b:
                records_b.append(val)

    def summarize(vals: list[float]) -> dict:
        if not vals:
            return {"count": 0}
        return {
            "count": len(vals),
            "mean": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
        }

    return {
        "metric": metric_key,
        "strategy_a": {"name": strategy_a, **summarize(records_a)},
        "strategy_b": {"name": strategy_b, **summarize(records_b)},
    }


@tool(
    name="get_best_strategy",
    description="Return the strategy with the best average outcome for a given metric.",
    parameters={
        "metric_key": {"type": "string", "description": "Metric to optimize, e.g. 'duration_ms'"},
        "minimize": {"type": "boolean", "description": "Lower is better? (default True)"},
    },
    required=["metric_key"],
)
async def get_best_strategy(metric_key: str, minimize: bool = True) -> dict[str, Any]:
    path = _ensure_store()
    if not path.exists():
        return {"error": "no experiments logged yet"}

    strategies: dict[str, list[float]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            val = entry.get("metrics", {}).get(metric_key)
            if val is not None:
                strategies.setdefault(entry["strategy"], []).append(val)

    if not strategies:
        return {"error": f"no data for metric '{metric_key}'"}

    best_strat = None
    best_val = None
    for strat, vals in strategies.items():
        mean = sum(vals) / len(vals)
        if best_val is None or (mean < best_val if minimize else mean > best_val):
            best_val = mean
            best_strat = strat

    return {
        "best_strategy": best_strat,
        "mean_value": best_val,
        "metric": metric_key,
        "minimize": minimize,
        "sample_sizes": {s: len(v) for s, v in strategies.items()},
    }
