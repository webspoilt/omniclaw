"""Interface with SAT/constraint solvers for reasoning about complex rules."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from core.skills.registry import tool


@tool(
    name="check_solver_available",
    description="Check which constraint solvers are installed on the system.",
    parameters={},
)
async def check_solver_available() -> dict[str, bool]:
    solvers = ["z3", "cvc5", "minisat", "glucose", "picosat"]
    result = {}
    for s in solvers:
        try:
            subprocess.run([s, "--version" if s != "z3" else "--version"], capture_output=True, timeout=5)
            result[s] = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            result[s] = False
    import importlib
    result["z3_python"] = importlib.util.find_spec("z3") is not None
    return result


@tool(
    name="solve_dimacs_cnf",
    description="Solve a SAT problem in DIMACS CNF format using an available solver (minisat/glucose/picosat).",
    parameters={
        "cnf_text": {"type": "string", "description": "DIMACS CNF string, e.g. 'p cnf 3 2\\n1 -2 0\\n2 -3 0'"},
        "solver": {"type": "string", "description": "Solver binary: minisat, glucose, or picosat"},
    },
    required=["cnf_text"],
)
async def solve_dimacs_cnf(cnf_text: str, solver: str = "minisat") -> dict:
    import shutil
    solver_path = shutil.which(solver)
    if not solver_path:
        return {"error": f"solver '{solver}' not found on PATH"}

    with tempfile.TemporaryDirectory(prefix="omniclaw_sat_") as tmp:
        cnf_path = Path(tmp) / "input.cnf"
        out_path = Path(tmp) / "output.sat"
        cnf_path.write_text(cnf_text, encoding="utf-8")

        try:
            proc = subprocess.run(
                [solver_path, str(cnf_path), str(out_path)],
                capture_output=True, text=True, timeout=60,
            )
        except subprocess.TimeoutExpired:
            return {"error": "solver timed out after 60s"}

        result: dict = {"solver": solver, "exit_code": proc.returncode}
        if out_path.exists():
            result["output"] = out_path.read_text(encoding="utf-8").strip()
        if proc.stderr:
            result["stderr"] = proc.stderr.strip()

        if proc.returncode == 10:
            result["status"] = "SATISFIABLE"
        elif proc.returncode == 20:
            result["status"] = "UNSATISFIABLE"
        else:
            result["status"] = "UNKNOWN"

        return result


@tool(
    name="solve_with_z3",
    description="Solve a logic expression using the Z3 SMT solver (Python API). Requires z3-solver installed.",
    parameters={
        "z3_script": {"type": "string", "description": "Python code that defines and solves a Z3 constraint, e.g. 'from z3 import *\\nx = Int(\"x\")\\nsolve(x > 5, x < 10)'"},
    },
    required=["z3_script"],
)
async def solve_with_z3(z3_script: str) -> str:
    try:
        import z3
    except ImportError:
        return "Error: z3-solver not installed. Run: pip install z3-solver"

    global_ns = {"z3": z3}
    try:
        exec(z3_script, global_ns)
        return "Z3 script executed. Check output above."
    except Exception as e:
        return f"Error executing Z3 script: {e}"


@tool(
    name="optimize_plan",
    description="Given a set of ordered actions and constraints, check for conflicts using a simple SAT encoding.",
    parameters={
        "actions_json": {"type": "string", "description": "JSON list of action names, e.g. '[\"A\", \"B\", \"C\"]'"},
        "conflicts_json": {"type": "string", "description": "JSON list of conflicting pairs, e.g. '[[\"A\", \"B\"]]'"},
    },
    required=["actions_json", "conflicts_json"],
)
async def optimize_plan(actions_json: str, conflicts_json: str) -> dict:
    import json
    try:
        actions = json.loads(actions_json)
        conflicts = json.loads(conflicts_json)
    except json.JSONDecodeError as e:
        return {"error": f"invalid JSON: {e}"}

    if not isinstance(actions, list) or not isinstance(conflicts, list):
        return {"error": "actions must be a list, conflicts must be a list of pairs"}

    n = len(actions)
    if n == 0:
        return {"actions": [], "conflicts_found": 0, "status": "empty"}

    action_index = {a: i for i, a in enumerate(actions)}
    conflict_pairs = []
    for pair in conflicts:
        if len(pair) != 2:
            continue
        a, b = pair
        if a in action_index and b in action_index:
            conflict_pairs.append((action_index[a], action_index[b]))

    check_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    actual_conflicts = []
    for i, j in check_pairs:
        if (i, j) in [(c[0], c[1]) for c in conflict_pairs] or (j, i) in [(c[0], c[1]) for c in conflict_pairs]:
            actual_conflicts.append((actions[i], actions[j]))

    return {
        "actions": actions,
        "total_pairs": len(check_pairs),
        "conflict_pairs_defined": len(conflict_pairs),
        "conflicts_found": len(actual_conflicts),
        "conflict_list": [list(c) for c in actual_conflicts],
        "status": "conflicts_detected" if actual_conflicts else "no_conflicts",
    }
