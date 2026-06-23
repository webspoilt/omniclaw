"""
Fugu-style multi-backend orchestrator for the OmniClaw research agent.

Loads worker definitions and an allow-list from config/workers.yaml,
expands environment variables, and provides:

  - fugu_task()         – capability-based auto-routing to the best worker.
  - fugu_complex_task() – multi-step strategies: debate, aggregation,
                          build-debug cycles across multiple workers.
  - list_available_workers() – list workers with their capabilities.

OPENROUTER_API_KEY must be set in the environment before starting the
agent.  The firewall must restrict outbound traffic to only the
OpenRouter IP addresses (https://openrouter.ai/docs#ip-addresses).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from core.skills.registry import tool

# ---------------------------------------------------------------------------
# Worker configuration loader
# ---------------------------------------------------------------------------

_workers: dict[str, dict] = {}
_allowed: list[str] = []


def _expand_env(value: str) -> str:
    """Expand ${VAR} references in a string."""
    def _replacer(m: re.Match) -> str:
        var = m.group(1) or m.group(2) or ""
        return os.environ.get(var, "")
    return re.sub(r"\$\{(\w+)\}|\$(\w+)", _replacer, value)


def _load_worker_config() -> None:
    """Read config/workers.yaml and populate _workers and _allowed."""
    candidates = [
        Path(os.getcwd(), "config", "workers.yaml"),
        Path("/opt/omniclaw/config/workers.yaml"),
        Path(__file__).parent.parent / "config" / "workers.yaml",
    ]
    for path in candidates:
        if path.exists():
            break
    else:
        return

    try:
        import yaml
    except ImportError:
        return

    with open(path) as f:
        data = yaml.safe_load(f)

    global _allowed
    _allowed = data.get("allowed_workers", [])

    for entry in data.get("workers", []):
        name = entry.get("name", "")
        if not name:
            continue
        worker = {
            "name": name,
            "type": entry.get("type", "ollama"),
            "url": entry.get("url", ""),
            "model": entry.get("model", ""),
            "timeout": entry.get("timeout", 300),
            "api_key": _expand_env(entry.get("api_key", "")),
            "capabilities": entry.get("capabilities", []),
        }
        _workers[name] = worker


def get_worker(name: str) -> dict | None:
    """Return the worker dict for *name*, or None."""
    if not _workers:
        _load_worker_config()
    return _workers.get(name)


def _is_allowed(name: str) -> bool:
    """Check whether *name* is in the allowed_workers list."""
    if not _allowed:
        return True  # no allow-list means all are allowed
    return name in _allowed


# ---------------------------------------------------------------------------
# Internal async HTTP helpers
# ---------------------------------------------------------------------------

async def _call_ollama(worker: dict, prompt: str, **overrides) -> str:
    """Call an Ollama-type worker (generate endpoint)."""
    import aiohttp
    payload = {
        "model": worker["model"],
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": overrides.get("temperature", 0.8)},
    }
    headers = {}
    if worker.get("api_key"):
        headers["Authorization"] = f"Bearer {worker['api_key']}"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            worker["url"], json=payload, timeout=overrides.get("timeout", worker["timeout"])
        ) as resp:
            if resp.status != 200:
                return ""
            data = await resp.json()
            return data.get("response", "")


async def _call_openrouter(worker: dict, prompt: str, **overrides) -> str:
    """Call an OpenRouter-type worker (chat/completions endpoint)."""
    import aiohttp
    payload = {
        "model": worker["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": overrides.get("temperature", 0.8),
        "max_tokens": overrides.get("max_tokens", 4096),
    }
    headers = {"Authorization": f"Bearer {worker['api_key']}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            worker["url"], json=payload, timeout=overrides.get("timeout", worker["timeout"])
        ) as resp:
            if resp.status != 200:
                return ""
            data = await resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            return choices[0].get("message", {}).get("content", "")


async def _call_worker(worker_name: str, prompt: str, **overrides) -> str:
    """Internal dispatch to a single worker by name."""
    worker = get_worker(worker_name)
    if not worker:
        return f"Unknown worker '{worker_name}'."
    if not _is_allowed(worker_name):
        return f"Worker '{worker_name}' is not in the allowed_workers list."
    try:
        if worker["type"] == "openrouter":
            return await _call_openrouter(worker, prompt, **overrides)
        return await _call_ollama(worker, prompt, **overrides)
    except ImportError:
        return "aiohttp not available. Install with: pip install aiohttp"
    except Exception as e:
        return f"Worker error: {e}"


# ---------------------------------------------------------------------------
# Capability-based routing
# ---------------------------------------------------------------------------

def _best_worker_for(capabilities: list[str]) -> str | None:
    """Score each allowed worker and return the name with the most matching capabilities."""
    best_name = None
    best_score = -1
    for name in sorted(_workers):
        if not _is_allowed(name):
            continue
        w = _workers[name]
        score = sum(1 for c in capabilities if c in w.get("capabilities", []))
        if score > best_score:
            best_score = score
            best_name = name
    return best_name


# ---------------------------------------------------------------------------
# Public skill API
# ---------------------------------------------------------------------------


@tool()
async def list_available_workers() -> str:
    """List all configured LLM backends with type, model, capabilities, and allow-list status."""
    if not _workers:
        _load_worker_config()
    if not _workers:
        return "No workers configured (check config/workers.yaml and pyyaml installation)."
    lines = ["=== Available LLM Workers ==="]
    if _allowed:
        lines.append(f"Allow-list: {', '.join(_allowed)}")
    for name in sorted(_workers):
        w = _workers[name]
        status = "allowed" if _is_allowed(name) else "DENIED"
        caps = ", ".join(w.get("capabilities", []))
        lines.append(f"  {name} [{status}]: type={w['type']}, model={w['model']}")
        if caps:
            lines.append(f"    capabilities: {caps}")
    return "\n".join(lines)


@tool()
async def fugu_task(prompt: str, required_capabilities: str = "general") -> str:
    """
    Auto-route a prompt to the best-matched worker based on required capabilities.

    Parameters:
      prompt: The input prompt to send.
      required_capabilities: Comma-separated list, e.g. "math,coding".
    """
    caps = [c.strip() for c in required_capabilities.split(",")]
    best = _best_worker_for(caps)
    if not best:
        return "No allowed worker found matching the required capabilities."
    result = await _call_worker(best, prompt)
    return f"[routed to: {best}]\n{result}"


@tool()
async def fugu_complex_task(
    prompt: str,
    strategy: str = "debate",
    workers: str = "",
    rounds: int = 2,
) -> str:
    """
    Execute a complex multi-worker task using one of several strategies.

    Strategies:
      debate      – Workers exchange arguments and counter-arguments.
      aggregate   – Each worker answers independently; results are merged.
      build_debug – Worker 1 builds, Worker 2 debugs; cycles for *rounds* iterations.

    Parameters:
      prompt:  The task description.
      strategy: "debate", "aggregate", or "build_debug".
      workers:  Comma-separated worker names (defaults to all allowed).
      rounds:   Number of debate rounds or build-debug cycles.
    """
    if not _workers:
        _load_worker_config()

    worker_names = [w.strip() for w in workers.split(",") if w.strip()]
    if not worker_names:
        worker_names = [n for n in sorted(_workers) if _is_allowed(n)]
    worker_names = [n for n in worker_names if _is_allowed(n) and n in _workers]

    if len(worker_names) < 1:
        return "No allowed workers available for the complex task."

    strategy = strategy.strip().lower()

    if strategy == "debate":
        return await _run_debate(prompt, worker_names, rounds)

    if strategy == "aggregate":
        return await _run_aggregate(prompt, worker_names)

    if strategy == "build_debug":
        if len(worker_names) < 2:
            return "build_debug requires at least 2 workers (builder + debugger)."
        return await _run_build_debug(prompt, worker_names, rounds)

    return f"Unknown strategy '{strategy}'. Supported: debate, aggregate, build_debug."


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------

async def _run_debate(prompt: str, workers: list[str], rounds: int) -> str:
    """Workers debate the prompt, building on each other's responses."""
    log = []
    context = prompt
    for r in range(rounds):
        round_log = []
        for name in workers:
            instruction = (
                f"Round {r + 1}/{rounds} of a debate.\n"
                f"Task: {prompt}\n\n"
                f"Previous discussion:\n{context}\n\n"
                f"You are {name}. Argue your position, rebut counter-points, "
                "and provide evidence for your claims."
            )
            resp = await _call_worker(name, instruction)
            resp = resp[:2000] if resp else "(no response)"
            round_log.append(f"[{name} (round {r+1})]\n{resp}\n")
        context = "\n".join(round_log)
        log.append(f"--- Round {r + 1} ---\n{context}")

    # Final synthesis
    synthesis = await _call_worker(
        workers[0],
        f"Synthesise the debate into a final answer.\nTask: {prompt}\n\n"
        f"Debate transcript:\n{context}\n\nFinal answer:"
    )
    log.append(f"--- Synthesis by {workers[0]} ---\n{synthesis}")
    return "\n\n".join(log)


async def _run_aggregate(prompt: str, workers: list[str]) -> str:
    """Each worker answers independently; results are compiled."""
    from asyncio import create_task, gather

    async def _ask(name: str) -> tuple[str, str]:
        resp = await _call_worker(name, prompt)
        return name, resp[:2000] if resp else "(no response)"

    tasks = [create_task(_ask(n)) for n in workers]
    results = await gather(*tasks)

    lines = [f"=== Aggregated Results ({len(results)} workers) ==="]
    for name, resp in results:
        lines.append(f"\n--- {name} ---\n{resp}")

    # Merge via first worker
    combined = "\n".join(f"=== {n} ===\n{r}" for n, r in results)
    merge_prompt = (
        f"Task: {prompt}\n\nIndividual worker responses:\n{combined}\n\n"
        "Merge these into a single coherent answer. Resolve conflicts, "
        "preserve unique insights, and produce a final consolidated response."
    )
    merged = await _call_worker(workers[0], merge_prompt)
    lines.append(f"\n--- Merged by {workers[0]} ---\n{merged}")
    return "\n".join(lines)


async def _run_build_debug(prompt: str, workers: list[str], rounds: int) -> str:
    """Worker 1 builds, Worker 2 debugs; repeat for N rounds."""
    builder = workers[0]
    debugger = workers[1]
    log = []
    artifact = prompt

    for r in range(rounds):
        build_prompt = (
            f"Build iteration {r + 1}/{rounds}.\n"
            f"Task: {prompt}\n\nPrevious state:\n{artifact}\n\n"
            "Produce an improved solution or implementation."
        )
        artifact = await _call_worker(builder, build_prompt)
        artifact = artifact[:4000] if artifact else "(empty)"
        log.append(f"[BUILD by {builder} r{r+1}]\n{artifact}")

        debug_prompt = (
            f"Debug iteration {r + 1}/{rounds}.\n"
            f"Task: {prompt}\n\nCurrent build:\n{artifact}\n\n"
            "Identify bugs, flaws, or improvements. Output a detailed critique."
        )
        critique = await _call_worker(debugger, debug_prompt)
        critique = critique[:2000] if critique else "(no critique)"
        log.append(f"[DEBUG by {debugger} r{r+1}]\n{critique}")
        artifact = f"Build:\n{artifact}\n\nCritique:\n{critique}"

    # Final polish
    final_prompt = (
        f"Task: {prompt}\n\nBuild-debug transcript:\n" + "\n".join(log) +
        "\n\nProduce the final polished solution."
    )
    final = await _call_worker(builder, final_prompt)
    log.append(f"[FINAL by {builder}]\n{final}")
    return "\n\n".join(log)


# ---------------------------------------------------------------------------
# Eager-load config on import
# ---------------------------------------------------------------------------
_load_worker_config()
