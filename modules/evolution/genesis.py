#!/usr/bin/env python3
"""
genesis.py — Self-Evolution & Refactoring Agent

Collects performance telemetry, asks LLM for optimization suggestions,
and can apply refactoring with safety checks (kill switch, backups, manual approval).
"""

import time
import logging
import shutil
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from core.kill_switch import check_kill_switch, KILL_SWITCH
    from core.resource_utils import resource_check
except ImportError:
    KILL_SWITCH = False
    def check_kill_switch(): pass
    def resource_check(**kw): return True

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Genesis")


class Genesis:
    """Self-evolution agent that analyzes performance and suggests refactoring."""

    def __init__(self, daemon=None, llm_model: str = "codellama:latest",
                 ollama_url: str = "http://localhost:11434"):
        self.daemon = daemon
        self.model = llm_model
        self.ollama_url = ollama_url
        self.telemetry: list = []
        self.max_telemetry = 100

    def collect_telemetry(self, entry: dict):
        """Add a telemetry entry {timestamp, module, cpu, memory, latency, errors}."""
        self.telemetry.append(entry)
        if len(self.telemetry) > self.max_telemetry:
            self.telemetry = self.telemetry[-self.max_telemetry:]

    def _llm(self, prompt: str) -> Optional[str]:
        if self.daemon and hasattr(self.daemon, "llm_inference"):
            return self.daemon.llm_inference(prompt)
        if not HAS_REQUESTS:
            return None
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM: {e}")
            return None

    def analyze_performance(self) -> Optional[str]:
        """Ask LLM to analyze telemetry and suggest optimizations."""
        if len(self.telemetry) < 10:
            logger.info("Not enough telemetry yet")
            return None

        recent = self.telemetry[-20:]
        prompt = (
            "You are a performance engineer. Analyze the following "
            "telemetry data from a Python agent system and suggest "
            "specific code optimizations. Focus on bottlenecks, "
            "memory leaks, and latency patterns.\n\n"
            f"Telemetry:\n{recent}\n\n"
            "Provide actionable suggestions with code snippets."
        )
        return self._llm(prompt)

    def suggest_refactor(self, module_path: Path) -> Optional[str]:
        """Read a module and ask LLM for refactoring suggestions."""
        if not module_path.exists():
            return None
        code = module_path.read_text(encoding="utf-8")
        prompt = (
            "Refactor the following Python module for better performance, "
            "readability, and maintainability. Output the complete "
            "refactored code in a ```python``` block.\n\n"
            f"Module: {module_path.name}\n```python\n{code}\n```"
        )
        return self._llm(prompt)

    def apply_refactor(self, module_path: Path, new_code: str,
                       require_approval: bool = True) -> bool:
        """Apply refactored code with safety checks."""
        if KILL_SWITCH:
            logger.warning("Kill switch active — aborting refactor")
            return False
        check_kill_switch()

        if require_approval:
            print(f"\n--- Genesis Refactor: {module_path.name} ---")
            print(new_code[:500], "…" if len(new_code) > 500 else "")
            if input("Apply? (y/n): ").strip().lower() != "y":
                logger.info("Refactor rejected by user")
                return False

        # Backup
        bak = module_path.with_suffix(module_path.suffix + ".genesis.bak")
        try:
            shutil.copy2(module_path, bak)
            logger.info(f"Backup → {bak}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

        # Write
        try:
            module_path.write_text(new_code, encoding="utf-8")
            logger.info(f"Refactored: {module_path}")
            return True
        except Exception as e:
            logger.error(f"Write failed: {e}")
            # Restore backup
            shutil.copy2(bak, module_path)
            return False

    def run(self, interval: int = 3600):
        """Hourly analysis loop."""
        logger.info("Genesis evolution agent running")
        while True:
            if resource_check(is_mobile=False):
                check_kill_switch()
                suggestion = self.analyze_performance()
                if suggestion:
                    logger.info(f"Evolution suggestion: {suggestion[:200]}…")
            time.sleep(interval)


if __name__ == "__main__":
    g = Genesis()
    g.run()
