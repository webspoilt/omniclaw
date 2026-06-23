# ruff: noqa: E501
"""Agent competition: ELO-ranked tournaments, genetic crossover, swarm evolution, champion retraining."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from statistics import mean

from core.skills.registry import tool

_ELO_FILE = Path("/tmp/agent_elo_ratings.json")
_VARIANT_DIR = Path("/tmp/agent_variants")
_ELO_RATINGS: dict[str, float] = {}
_MUTATION_LOG: list[dict] = []


def _load_elo():
    global _ELO_RATINGS
    if _ELO_FILE.exists():
        try:
            _ELO_RATINGS.update(json.loads(_ELO_FILE.read_text()))
        except Exception:
            pass


def _save_elo():
    _ELO_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ELO_FILE.write_text(json.dumps(_ELO_RATINGS, indent=2))


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def _update_elo(winner: str, loser: str, k: int = 32):
    _load_elo()
    rw = _ELO_RATINGS.get(winner, 1200.0)
    rl = _ELO_RATINGS.get(loser, 1200.0)
    ew = _expected_score(rw, rl)
    el = _expected_score(rl, rw)
    _ELO_RATINGS[winner] = rw + k * (1.0 - ew)
    _ELO_RATINGS[loser] = rl + k * (0.0 - el)
    _save_elo()


@tool()
def spawn_competing_agents(variants_json: str) -> str:
    """Spawn multiple agent variants with different configurations to compete."""
    try:
        agents = json.loads(variants_json)
        if not isinstance(agents, list) or len(agents) < 2:
            return "variants must be a JSON array with at least 2 agent configs"
        _VARIANT_DIR.mkdir(parents=True, exist_ok=True)
        results = []
        for i, variant in enumerate(agents):
            name = variant.get("name", f"agent_{i}")
            script = variant.get("script", "")
            args = variant.get("args", "")
            code = variant.get("code", "")
            if code:
                fpath = _VARIANT_DIR / f"{name}.py"
                fpath.write_text(code)
                script = str(fpath)
            if not script and not code:
                results.append(f"  [{i}] {name}: no script or code specified")
                continue
            try:
                cmd = [script] + args.split()
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
                _load_elo()
                if name not in _ELO_RATINGS:
                    _ELO_RATINGS[name] = 1200.0
                    _save_elo()
                results.append(f"  [{i}] {name}: spawned (PID {proc.pid}, ELO {_ELO_RATINGS.get(name, 1200):.0f})")
            except FileNotFoundError:
                results.append(f"  [{i}] {name}: script not found")
            except Exception as e:
                results.append(f"  [{i}] {name}: error — {e}")
        return f"Spawned {len(results)} agents:\n" + "\n".join(results)
    except json.JSONDecodeError:
        return "Invalid JSON variants specification"
    except Exception as e:
        return f"Agent spawning failed: {e}"


@tool()
def run_tournament(agents_json: str, benchmark_cmd: str, timeout_sec: int = 30, pairwise: bool = False) -> str:
    """Run a tournament where each agent variant is benchmarked against a command. If pairwise=True, agents compete head-to-head."""
    try:
        agents = json.loads(agents_json)
        if not isinstance(agents, list) or len(agents) < 2:
            return "agents must be a JSON array with at least 2 entries"
        scores = []
        for i, agent in enumerate(agents):
            name = agent if isinstance(agent, str) else agent.get("name", f"agent_{i}")
            script = agent if isinstance(agent, str) else agent.get("script", "")
            if not script:
                continue
            start = time.time()
            try:
                proc = subprocess.run(  # noqa: S603
                    [script] + benchmark_cmd.split(),  # noqa: S607
                    capture_output=True, text=True, timeout=timeout_sec,
                )
                elapsed = time.time() - start
                output_len = len(proc.stdout) + len(proc.stderr)
                score = output_len / max(elapsed, 0.01)
                scores.append({"name": name, "score": score, "time": elapsed, "output_size": output_len, "exit": proc.returncode})
            except subprocess.TimeoutExpired:
                scores.append({"name": name, "score": 0, "time": timeout_sec, "output_size": 0, "exit": -1})
            except Exception as e:
                scores.append({"name": name, "score": 0, "time": 0, "output_size": 0, "exit": -2, "error": str(e)})
        scores.sort(key=lambda x: x["score"], reverse=True)
        if pairwise and len(scores) >= 2:
            winner = scores[0]["name"]
            loser = scores[-1]["name"]
            _update_elo(winner, loser)
        lines = [f"Tournament results ({len(scores)} agents):"]
        for i, s in enumerate(scores, 1):
            elo = _ELO_RATINGS.get(s["name"], 1200)
            lines.append(f"  #{i} {s['name']} — score: {s['score']:.1f}, time: {s['time']:.2f}s, ELO: {elo:.0f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Tournament failed: {e}"


@tool()
def genetic_crossover(parent_json: str, mutation_rate: float = 0.1) -> str:
    """Perform genetic crossover between two champion agent source codes to produce an improved variant."""
    try:
        parents = json.loads(parent_json)
        if not isinstance(parents, list) or len(parents) < 2:
            return "Provide a JSON array with at least 2 parent code strings"
        p1_lines = parents[0].splitlines()
        p2_lines = parents[1].splitlines()
        split = len(p1_lines) // 2
        import random
        child_lines = p1_lines[:split] + p2_lines[split:]
        for i in range(len(child_lines)):
            if random.random() < mutation_rate:  # noqa: S311
                if child_lines[i].strip() and not child_lines[i].strip().startswith(("#", "import", "from")):
                    child_lines[i] = child_lines[i] + "  # mutated"
        child_code = "\n".join(child_lines)
        ts = int(time.time())
        child_path = _VARIANT_DIR / f"child_{ts}.py"
        _VARIANT_DIR.mkdir(parents=True, exist_ok=True)
        child_path.write_text(child_code)
        _MUTATION_LOG.append({"time": ts, "parent_size": len(parents[0]), "child_size": len(child_code), "mutation_rate": mutation_rate})
        return f"Child variant created: {child_path} ({len(child_lines)} lines, mutation_rate={mutation_rate})\n---\n{child_code[:500]}"
    except Exception as e:
        return f"Crossover failed: {e}"


@tool()
def select_champion(tournament_results_json: str) -> str:
    """Select the champion agent from tournament results weighted by ELO and return its config."""
    try:
        results = json.loads(tournament_results_json)
        if not isinstance(results, list) or not results:
            return "results must be a non-empty JSON array"
        _load_elo()
        for r in results:
            name = r.get("name", "unknown")
            elo_bonus = (_ELO_RATINGS.get(name, 1200) - 1200) * 0.1
            r["score"] = r.get("score", 0) + max(elo_bonus, 0)
        champion = max(results, key=lambda x: x.get("score", 0))
        return (
            f"Champion: {champion.get('name', 'unknown')}\n"
            f"  Score (weighted): {champion.get('score', 0):.2f}\n"
            f"  Time: {champion.get('time', 0):.2f}s\n"
            f"  Exit code: {champion.get('exit', -1)}\n"
            f"  ELO: {_ELO_RATINGS.get(champion.get('name', ''), 1200):.0f}\n"
            f"  Config: {json.dumps(champion, indent=2)[:500]}"
        )
    except Exception as e:
        return f"Champion selection failed: {e}"


@tool()
def get_leaderboard(top_n: int = 10) -> str:
    """Return the current ELO leaderboard across all tournament runs."""
    try:
        _load_elo()
        if not _ELO_RATINGS:
            return "No ELO ratings yet. Run tournaments to generate them."
        ranked = sorted(_ELO_RATINGS.items(), key=lambda x: x[1], reverse=True)
        lines = ["ELO Leaderboard:"]
        for i, (name, elo) in enumerate(ranked[:top_n], 1):
            delta = elo - 1200
            trend = "▲" if delta > 0 else "▼" if delta < 0 else "—"
            lines.append(f"  #{i:<3} {name:<20} {elo:>7.0f} ({delta:+d}) {trend}")
        return "\n".join(lines)
    except Exception as e:
        return f"Leaderboard failed: {e}"


@tool()
def evolve_swarm(base_code: str, generations: int = 3, population: int = 4) -> str:
    """Evolve a codebase through multiple generations of tournament selection and crossover."""
    try:
        import random
        pop = [base_code]
        for _ in range(population - 1):
            lines = base_code.splitlines()
            mutated = []
            for line in lines:
                if random.random() < 0.2 and line.strip() and not line.strip().startswith(("#", "import", "from")):  # noqa: S311
                    mutated.append(f"# EVO: {line}")
                else:
                    mutated.append(line)
            pop.append("\n".join(mutated))
        results = []
        for gen in range(generations):
            _VARIANT_DIR.mkdir(parents=True, exist_ok=True)
            variants = []
            for i, code in enumerate(pop):
                fpath = _VARIANT_DIR / f"gen{gen}_indiv{i}.py"
                fpath.write_text(code)
                variants.append({"name": f"gen{gen}_i{i}", "script": str(fpath)})
            tournament = run_tournament(json.dumps(variants), "echo 'test'", 5, pairwise=True)
            _load_elo()
            ranked = sorted(_ELO_RATINGS.items(), key=lambda x: x[1], reverse=True)
            if len(ranked) >= 2:
                winner_code = (_VARIANT_DIR / f"{ranked[0][0]}.py").read_text() if (_VARIANT_DIR / f"{ranked[0][0]}.py").exists() else pop[0]
                runner_code = (_VARIANT_DIR / f"{ranked[1][0]}.py").read_text() if (_VARIANT_DIR / f"{ranked[1][0]}.py").exists() else pop[1]
                child = genetic_crossover(json.dumps([winner_code, runner_code]), 0.15)
                pop = [winner_code, runner_code] + [child]
            results.append(f"  Generation {gen}: champion ELO {ranked[0][1]:.0f}, {tournament[:100]}...")
        return "Swarm evolution complete:\n" + "\n".join(results) + "\n\n" + get_leaderboard(5)
    except Exception as e:
        return f"Swarm evolution failed: {e}"


@tool()
def get_mutation_history() -> str:
    """Return the log of all crossover/mutation events."""
    try:
        if not _MUTATION_LOG:
            return "No mutations recorded yet"
        lines = [f"Mutation log ({len(_MUTATION_LOG)} events):"]
        for m in _MUTATION_LOG[-50:]:
            lines.append(f"  [{m['time']}] parents={m.get('parent_size',0)}b → child={m.get('child_size',0)}b rate={m.get('mutation_rate',0)}")
        return "\n".join(lines)
    except Exception as e:
        return f"Mutation history failed: {e}"


@tool()
def reset_ratings() -> str:
    """Reset all ELO ratings to baseline (1200)."""
    try:
        global _ELO_RATINGS
        _ELO_RATINGS = {}
        if _ELO_FILE.exists():
            _ELO_FILE.unlink()
        return "All ELO ratings reset to 1200"
    except Exception as e:
        return f"Reset failed: {e}"
