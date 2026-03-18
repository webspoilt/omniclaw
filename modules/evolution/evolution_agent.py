#!/usr/bin/env python3
"""
evolution_agent.py – Self-Healing Code Janitor

Monitors logs for ERROR/CRITICAL tracebacks, uses an LLM to propose fixes,
tests them in an isolated sandbox, and commits to a fix/ Git branch.
"""

import os
import re
import time
import hashlib
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# Import resource check
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from core.resource_utils import resource_check
except ImportError:
    def resource_check(**kw):
        return True

# ---------- Configuration ----------
CONFIG_PATH = Path(__file__).parent / "config.yaml"

_DEFAULTS = {
    "log_dir": "logs",
    "source_dirs": ["core", "kernel_bridge"],
    "sandbox_dir": "/tmp/omniclaw_sandbox",
    "git_repo": ".",
    "llm_model": "codellama:latest",
    "ollama_url": "http://localhost:11434",
    "manual_approval": True,
    # Issue #23: auto-fix confidence threshold.
    # Fixes below this score ALWAYS require manual approval regardless of
    # the `manual_approval` config setting, preventing risky low-confidence
    # patches from being applied automatically.
    "confidence_threshold": 0.7,
}


def _load_config() -> dict:
    if HAS_YAML and CONFIG_PATH.is_file():
        with open(CONFIG_PATH) as f:
            return {**_DEFAULTS, **yaml.safe_load(f)}
    return dict(_DEFAULTS)


config = _load_config()
LOG_DIR     = Path(config["log_dir"])
SOURCE_DIRS = [Path(d) for d in config["source_dirs"]]
SANDBOX_DIR = Path(config["sandbox_dir"])
GIT_REPO    = Path(config["git_repo"])
LLM_MODEL   = config["llm_model"]
OLLAMA_URL  = config.get("ollama_url", "http://localhost:11434")
MANUAL_APPROVAL = config.get("manual_approval", True)
CONFIDENCE_THRESHOLD = float(config.get("confidence_threshold", 0.7))


def _estimate_confidence(original_code: str, fixed_code: str) -> float:
    """Estimate fix confidence as ratio of meaningful changed lines.

    Heuristic: if too many lines changed (>50%) or the fix is very short,
    the LLM may be hallucinating. Returns a score in [0, 1].
    High score = small, targeted change = higher confidence.

    Args:
        original_code: The original source code.
        fixed_code: The LLM-proposed fixed code.

    Returns:
        float in [0.0, 1.0]
    """
    orig_lines = [l.strip() for l in original_code.splitlines() if l.strip()]
    fixed_lines = [l.strip() for l in fixed_code.splitlines() if l.strip()]
    if not orig_lines or not fixed_lines:
        return 0.1  # empty = very low confidence
    # How similar in length are they?
    len_ratio = min(len(fixed_lines), len(orig_lines)) / max(len(orig_lines), len(fixed_lines))
    # How many lines are identical?
    orig_set = set(orig_lines)
    fixed_set = set(fixed_lines)
    shared = len(orig_set & fixed_set)
    total = max(len(orig_set | fixed_set), 1)
    similarity = shared / total
    # Confidence: weighted average
    score = 0.4 * len_ratio + 0.6 * similarity
    return round(max(0.0, min(1.0, score)), 3)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("EvolutionAgent")


# ---------- LLM ----------
def query_llm(prompt: str) -> Optional[str]:
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate",
                          json={"model": LLM_MODEL, "prompt": prompt,
                                "stream": False},
                          timeout=120)
        return r.json().get("response")
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return None


def _extract_code(response: str) -> str:
    m = re.search(r"```python\n(.*?)```", response, re.DOTALL)
    return m.group(1).strip() if m else response.strip()


# ---------- Traceback Helpers ----------
def extract_traceback(lines: List[str]) -> Optional[str]:
    tb: List[str] = []
    in_tb = False
    for line in lines:
        if line.startswith("Traceback (most recent call last):"):
            in_tb = True
            tb = [line.strip()]
        elif in_tb:
            tb.append(line.strip())
            if not line.startswith((" ", "\t", "  File")):
                in_tb = False
    return "\n".join(tb) if tb else None


def find_source_file(traceback: str) -> Optional[Path]:
    for m in re.finditer(r'File "([^"]+)"', traceback):
        p = Path(m.group(1))
        for src in SOURCE_DIRS:
            try:
                p.relative_to(src)
                return p
            except ValueError:
                continue
    return None


# ---------- Safe I/O ----------
def read_safe(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def write_safe(path: Path, content: str) -> bool:
    bak = path.with_suffix(path.suffix + ".bak")
    try:
        if path.exists():
            shutil.copy2(path, bak)
        path.write_text(content)
        return True
    except Exception as e:
        logger.error(f"Write failed: {e}")
        return False


# ---------- Sandbox Runner ----------
def run_test_in_sandbox(original: Path, fixed_code: str,
                        test_code: str) -> Tuple[bool, str]:
    sandbox = SANDBOX_DIR / f"test_{int(time.time())}"
    sandbox.mkdir(parents=True, exist_ok=True)
    try:
        (sandbox / original.name).write_text(fixed_code)
        test_path = sandbox / "test.py"
        test_path.write_text(test_code)
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=sandbox, capture_output=True, text=True, timeout=30,
        )
        out = result.stdout + result.stderr
        return (result.returncode == 0 and "TEST PASSED" in result.stdout), out
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ---------- Git ----------
def git_commit(file_path: Path, branch: str) -> bool:
    try:
        subprocess.run(["git", "checkout", "-b", branch],
                       cwd=GIT_REPO, check=True, capture_output=True)
        subprocess.run(["git", "add", str(file_path)],
                       cwd=GIT_REPO, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Auto-fix: {branch}"],
                       cwd=GIT_REPO, check=True, capture_output=True)
        logger.info(f"Committed → {branch}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git error: {e}")
        return False


# ---------- Log Handler ----------
if HAS_WATCHDOG:
    class LogHandler(FileSystemEventHandler):
        def __init__(self):
            self.processed: set = set()

        def on_modified(self, event):
            if not event.src_path.endswith(".log"):
                return
            if not resource_check(is_mobile=True):
                return
            time.sleep(1)
            with open(event.src_path) as f:
                lines = f.readlines()
            tb = extract_traceback(lines)
            if not tb:
                return
            h = hashlib.sha256(tb.encode()).hexdigest()
            if h in self.processed:
                return
            self.processed.add(h)
            logger.info("Crash detected — processing…")
            self._handle(tb)

        def _handle(self, traceback: str):
            src = find_source_file(traceback)
            if not src:
                return
            code = read_safe(src)
            if not code:
                return

            # Fix
            prompt = (f"Fix the error. Output only corrected code in "
                      f"```python```.\n\nTraceback:\n{traceback}\n\n"
                      f"Source:\n{code}")
            resp = query_llm(prompt)
            if not resp:
                return
            fixed = _extract_code(resp)

            # Confidence gate (Issue #23)
            code = read_safe(src)
            confidence = _estimate_confidence(code, fixed)
            require_approval = MANUAL_APPROVAL
            if confidence < CONFIDENCE_THRESHOLD:
                require_approval = True
                logger.warning(
                    f"Confidence {confidence:.2f} < threshold {CONFIDENCE_THRESHOLD:.2f} "
                    f"— forcing manual approval for fix on {src.name}"
                )

            # Manual approval
            if require_approval:
                print("\n--- Proposed Fix ---\n", fixed)
                print(f"[Confidence estimate: {confidence:.2f} / threshold: {CONFIDENCE_THRESHOLD:.2f}]")
                if input("Apply? (y/n): ").strip().lower() != "y":
                    return

            # Test
            test_prompt = (f"Write a short test that imports module and prints "
                           f"'TEST PASSED'.\nError:\n{traceback}\nFixed:\n{fixed}")
            tcode = query_llm(test_prompt)
            if not tcode:
                return
            tcode = _extract_code(tcode)

            ok, out = run_test_in_sandbox(src, fixed, tcode)
            if not ok:
                logger.error(f"Test failed: {out}")
                return

            branch = f"fix/{src.stem}-{int(time.time())}"
            write_safe(src, fixed)
            git_commit(src, branch)


# ---------- Main ----------
def main():
    if not HAS_WATCHDOG:
        logger.error("watchdog not installed")
        return
    if not resource_check(is_mobile=True):
        logger.warning("Insufficient resources")
        return
    observer = Observer()
    observer.schedule(LogHandler(), str(LOG_DIR), recursive=False)
    observer.start()
    logger.info(f"Monitoring {LOG_DIR} for crashes…")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
