"""
Multi-backend worker pool orchestration skill for the OmniClaw research agent.

Loads worker definitions from config/workers.yaml, expands environment
variables in api_key fields, and provides async call_worker() and
auto_route() functions to dispatch prompts across different LLM backends.

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
_default_worker: str | None = None


def _expand_env(value: str) -> str:
    """Expand ${VAR} or $VAR environment variable references in a string."""
    def _replacer(m: re.Match) -> str:
        var = m.group(1) or m.group(2) or ""
        return os.environ.get(var, "")
    return re.sub(r"\$\{(\w+)\}|\$(\w+)", _replacer, value)


def _load_worker_config() -> None:
    """Read config/workers.yaml and populate the _workers dict."""
    candidates = [
        Path(os.getcwd(), "config", "workers.yaml"),
        Path("/opt/omniclaw/config/workers.yaml"),
        Path(__file__).parent.parent / "config" / "workers.yaml",
    ]
    for path in candidates:
        if path.exists():
            break
    else:
        return  # no config file found; workers remain empty

    try:
        import yaml
    except ImportError:
        return  # pyyaml not installed; workers remain empty

    with open(path) as f:
        data = yaml.safe_load(f)

    global _default_worker
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
        }
        _workers[name] = worker
        if _default_worker is None:
            _default_worker = name


def get_worker(name: str) -> dict | None:
    """Return the worker dict for *name*, or None."""
    if not _workers:
        _load_worker_config()
    return _workers.get(name)


def list_workers() -> list[str]:
    """Return the names of all configured workers."""
    if not _workers:
        _load_worker_config()
    return sorted(_workers.keys())


# ---------------------------------------------------------------------------
# Internal async HTTP helpers
# ---------------------------------------------------------------------------

async def _call_ollama(worker: dict, prompt: str) -> str:
    """Call an Ollama‑type worker (generate endpoint)."""
    import aiohttp
    payload = {
        "model": worker["model"],
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.8},
    }
    headers = {}
    if worker.get("api_key"):
        headers["Authorization"] = f"Bearer {worker['api_key']}"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            worker["url"], json=payload, timeout=worker["timeout"]
        ) as resp:
            if resp.status != 200:
                return ""
            data = await resp.json()
            return data.get("response", "")


async def _call_openrouter(worker: dict, prompt: str) -> str:
    """Call an OpenRouter‑type worker (chat/completions endpoint)."""
    import aiohttp
    payload = {
        "model": worker["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 4096,
    }
    headers = {"Authorization": f"Bearer {worker['api_key']}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            worker["url"], json=payload, timeout=worker["timeout"]
        ) as resp:
            if resp.status != 200:
                return ""
            data = await resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            return choices[0].get("message", {}).get("content", "")


# ---------------------------------------------------------------------------
# Public skill API (auto-discovered by SkillLoader)
# ---------------------------------------------------------------------------


@tool()
async def call_worker(worker_name: str, prompt: str) -> str:
    """Dispatch a prompt to a specific worker by name. Returns the response text."""
    worker = get_worker(worker_name)
    if not worker:
        available = ", ".join(list_workers())
        return f"Unknown worker '{worker_name}'. Available workers: {available}"
    try:
        if worker["type"] == "openrouter":
            return await _call_openrouter(worker, prompt)
        return await _call_ollama(worker, prompt)
    except ImportError:
        return "aiohttp not available. Install with: pip install aiohttp"
    except Exception as e:
        return f"Worker error: {e}"


@tool()
async def auto_route(prompt: str) -> str:
    """Auto-route a prompt to the local model; returns response text."""
    worker = get_worker("local_uncensored")
    if not worker:
        return "No local_uncensored worker configured."
    try:
        return await _call_ollama(worker, prompt)
    except ImportError:
        return "aiohttp not available. Install with: pip install aiohttp"
    except Exception as e:
        return f"Auto-route error: {e}"


@tool()
async def list_worker_backends() -> str:
    """List all configured LLM backends with their type and model."""
    backends = list_workers()
    if not backends:
        return "No workers configured (check config/workers.yaml and pyyaml installation)."
    lines = ["=== Configured LLM Backends ==="]
    for name in backends:
        w = _workers[name]
        lines.append(f"  {name}: type={w['type']}, model={w['model']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Eager‑load config on import so the planner can use it immediately
# ---------------------------------------------------------------------------
_load_worker_config()
