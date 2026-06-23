"""Design and run small experiments to test hypotheses about system behaviour."""
from __future__ import annotations

import subprocess
import time
from typing import Any

from core.skills.registry import tool


@tool(
    name="measure_execution_time",
    description="Run a shell command multiple times and measure min/mean/max execution time.",
    parameters={
        "command": {"type": "string", "description": "Shell command to benchmark"},
        "iterations": {"type": "integer", "description": "Number of times to run"},
        "description": {"type": "string", "description": "Label for this benchmark"},
    },
    required=["command"],
)
async def measure_execution_time(command: str, iterations: int = 5, description: str | None = None) -> dict[str, Any]:
    timings: list[float] = []
    errors: list[str] = []

    for i in range(iterations):
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60
            )
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)
            if proc.returncode != 0:
                errors.append(f"run {i}: exit {proc.returncode}")
        except subprocess.TimeoutExpired:
            errors.append(f"run {i}: timed out")
        except Exception as e:
            errors.append(f"run {i}: {e}")

    result: dict[str, Any] = {
        "description": description or command[:60],
        "iterations": iterations,
        "completed": len(timings),
    }

    if timings:
        timings.sort()
        result["min_ms"] = round(timings[0], 2)
        result["max_ms"] = round(timings[-1], 2)
        result["mean_ms"] = round(sum(timings) / len(timings), 2)
        result["median_ms"] = round(timings[len(timings) // 2], 2)

    if errors:
        result["errors"] = errors[:5]

    return result


@tool(
    name="run_experiment",
    description="Run a controlled experiment: run two different commands (control vs variant) and compare timing.",
    parameters={
        "control_command": {"type": "string", "description": "Baseline command"},
        "variant_command": {"type": "string", "description": "Experimental command"},
        "iterations": {"type": "integer", "description": "Runs per variant"},
        "label": {"type": "string", "description": "Experiment label"},
    },
    required=["control_command", "variant_command"],
)
async def run_experiment(control_command: str, variant_command: str, iterations: int = 5, label: str | None = None) -> dict[str, Any]:
    control = await measure_execution_time(control_command, iterations, "control")
    variant = await measure_execution_time(variant_command, iterations, "variant")

    result: dict[str, Any] = {
        "experiment": label or "control vs variant",
        "control": control,
        "variant": variant,
    }

    if control.get("mean_ms") and variant.get("mean_ms"):
        diff = variant["mean_ms"] - control["mean_ms"]
        pct = (diff / control["mean_ms"]) * 100
        result["delta_ms"] = round(diff, 2)
        result["delta_percent"] = round(pct, 2)
        result["faster"] = "control" if diff > 0 else "variant"
        result["speedup"] = round(abs(100 / (100 + pct) - 1) * 100, 1) if pct != 0 else 0

    return result


@tool(
    name="statistical_test",
    description="Perform a simple statistical comparison of two lists of measurements.",
    parameters={
        "values_a_json": {"type": "string", "description": "JSON array of numbers, e.g. '[1.2, 1.5, 1.3]'"},
        "values_b_json": {"type": "string", "description": "JSON array of numbers to compare"},
    },
    required=["values_a_json", "values_b_json"],
)
async def statistical_test(values_a_json: str, values_b_json: str) -> dict[str, Any]:
    import json
    import math
    try:
        a = json.loads(values_a_json)
        b = json.loads(values_b_json)
    except json.JSONDecodeError as e:
        return {"error": f"invalid JSON: {e}"}

    if not isinstance(a, list) or not isinstance(b, list):
        return {"error": "inputs must be JSON arrays"}
    if not a or not b:
        return {"error": "arrays must not be empty"}

    def describe(vals: list[float]) -> dict:
        s = sorted(vals)
        n = len(s)
        mean = sum(s) / n
        variance = sum((x - mean) ** 2 for x in s) / n
        return {
            "n": n,
            "mean": round(mean, 4),
            "median": round(s[n // 2], 4),
            "min": round(s[0], 4),
            "max": round(s[-1], 4),
            "stddev": round(math.sqrt(variance), 4),
        }

    desc_a = describe(a)
    desc_b = describe(b)

    # Welch's t-test approximation
    import math as m
    n1, n2 = len(a), len(b)
    m1, v1 = desc_a["mean"], desc_a["stddev"] ** 2
    m2, v2 = desc_b["mean"], desc_b["stddev"] ** 2
    t_stat = (m1 - m2) / m.sqrt(v1 / n1 + v2 / n2) if (v1 + v2) > 0 else 0

    return {
        "group_a": desc_a,
        "group_b": desc_b,
        "t_statistic": round(t_stat, 4),
        "mean_difference": round(m1 - m2, 4),
        "interpretation": "significant" if abs(t_stat) > 2 else "not significant",
    }


@tool(
    name="check_file_change_timing",
    description="Quickly write and delete a temp file to test filesystem latency.",
    parameters={
        "iterations": {"type": "integer", "description": "Number of write-delete cycles"},
    },
    required=[],
)
async def check_file_change_timing(iterations: int = 10) -> dict[str, Any]:
    import os
    import tempfile
    writes: list[float] = []
    reads: list[float] = []
    deletes: list[float] = []

    for _ in range(iterations):
        fd, path = tempfile.mkstemp(prefix="omniclaw_bench_")
        os.close(fd)

        t0 = time.perf_counter()
        with open(path, "w") as f:
            f.write("benchmark" * 1000)
        writes.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        with open(path) as f:
            f.read()
        reads.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        os.unlink(path)
        deletes.append((time.perf_counter() - t0) * 1000)

    def stats(vals: list[float]) -> dict:
        s = sorted(vals)
        return {
            "min_ms": round(s[0], 2),
            "mean_ms": round(sum(s) / len(s), 2),
            "max_ms": round(s[-1], 2),
        }

    return {
        "write": stats(writes),
        "read": stats(reads),
        "delete": stats(deletes),
    }
