#!/usr/bin/env python3
"""
evolution_agent.py - Self-Evolving Code Janitor for OmniClaw

Monitors logs for critical errors, uses an LLM to propose fixes,
tests them in isolation, and commits the change to a Git branch if successful.

Features:
  - Log monitoring with watchdog (detects ERROR/CRITICAL tracebacks)
  - Traceback parsing (extracts faulty source file and line number)
  - LLM fix proposal (Ollama or OpenAI)
  - Isolated testing (temporary copy, LLM-generated test)
  - Git integration (fix/<error-type> branches)
  - Notifications (Telegram / Discord webhooks)
  - Manual approval mode
  - Safe file I/O (atomic writes, .bak backups)
  - Duplicate prevention (hash store)
"""

import os
import re
import sys
import time
import hashlib
import shutil
import tempfile
import subprocess
import json
import logging
import traceback as tb
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# ------------------------------------------------------------------ #
#  Configuration                                                      #
# ------------------------------------------------------------------ #
CONFIG_FILE = os.environ.get("EVOLUTION_CONFIG", "evolution_config.yaml")

_DEFAULT_CONFIG = {
    "log_dir": "./logs",
    "source_dirs": ["./core", "./kernel_bridge"],
    "llm_provider": "ollama",
    "llm_model": "codellama:latest",
    "ollama_url": "http://localhost:11434",
    "openai_api_key": "",
    "manual_approval": True,
    "git_repo_path": ".",
    "test_command": "pytest tests/",
    "notification": {},
}


def load_config() -> dict:
    """Load YAML config; fall back to defaults if file or yaml missing."""
    if yaml and os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return {**_DEFAULT_CONFIG, **yaml.safe_load(f)}
    return dict(_DEFAULT_CONFIG)


config = load_config()

LOG_DIR          = config["log_dir"]
SOURCE_DIRS      = [Path(d).resolve() for d in config["source_dirs"]]
LLM_PROVIDER     = config.get("llm_provider", "ollama")
LLM_MODEL        = config["llm_model"]
OLLAMA_URL       = config.get("ollama_url", "http://localhost:11434")
OPENAI_API_KEY   = config.get("openai_api_key")
MANUAL_APPROVAL  = config.get("manual_approval", False)
GIT_REPO_PATH    = Path(config.get("git_repo_path", ".")).resolve()
TEST_COMMAND     = config.get("test_command", "pytest tests/")
NOTIFICATION_WH  = config.get("notification", {})

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("EvolutionAgent")


# ------------------------------------------------------------------ #
#  Helper Functions                                                   #
# ------------------------------------------------------------------ #
def notify(message: Dict[str, Any]):
    """Send JSON payload to configured Telegram / Discord webhooks."""
    if not requests:
        logger.warning("requests not installed — skipping notification")
        return
    payload = json.dumps(message, indent=2)
    for service, url in NOTIFICATION_WH.items():
        try:
            if service == "telegram":
                requests.post(url, json={"text": f"```json\n{payload}\n```"}, timeout=10)
            elif service == "discord":
                requests.post(url, json={"content": f"```json\n{payload}\n```"}, timeout=10)
            else:
                requests.post(url, json=message, timeout=10)
        except Exception as e:
            logger.error(f"Notification to {service} failed: {e}")


def run_git(args: List[str], cwd: Path = GIT_REPO_PATH) -> str:
    """Run a git command; raise RuntimeError on failure."""
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"Git error: {result.stderr}")
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def get_error_type(tb_lines: List[str]) -> str:
    """Extract short error type from traceback lines (e.g. 'AttributeError')."""
    for line in reversed(tb_lines):
        m = re.search(r"(\w+Error):", line)
        if m:
            return m.group(1)
    return "UnknownError"


def extract_source_file(tb_lines: List[str]) -> Optional[Path]:
    """
    Find the first source file inside SOURCE_DIRS from traceback lines.
    Typical line:  '  File "/path/to/file.py", line 123, in func'
    """
    pattern = re.compile(r'  File "([^"]+)"')
    for line in tb_lines:
        m = pattern.search(line)
        if m:
            fp = Path(m.group(1)).resolve()
            for src in SOURCE_DIRS:
                try:
                    fp.relative_to(src)
                    return fp
                except ValueError:
                    continue
    return None


def read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Read failed {path}: {e}")
        return ""


def write_safe(path: Path, content: str, *, backup: bool = True) -> bool:
    """Atomic write with optional .bak backup."""
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        try:
            shutil.copy2(path, bak)
            logger.info(f"Backup → {bak}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
        logger.info(f"Wrote {path}")
        return True
    except Exception as e:
        logger.error(f"Write failed {path}: {e}")
        if tmp.exists():
            tmp.unlink()
        return False


def error_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ------------------------------------------------------------------ #
#  LLM Interaction                                                    #
# ------------------------------------------------------------------ #
def query_llm(prompt: str) -> Optional[str]:
    """Send prompt to Ollama or OpenAI; return text or None."""
    if not requests:
        logger.error("requests package not installed")
        return None

    if LLM_PROVIDER == "ollama":
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
                timeout=120,
            )
            r.raise_for_status()
            return r.json().get("response")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    elif LLM_PROVIDER == "openai":
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            resp = openai.ChatCompletion.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None
    else:
        logger.error(f"Unknown LLM provider: {LLM_PROVIDER}")
        return None


def _extract_code_block(response: str) -> str:
    """Pull the first ```python``` block from an LLM response."""
    m = re.search(r"```python\n(.*?)```", response, re.DOTALL)
    return m.group(1).strip() if m else response.strip()


def ask_fix(error_msg: str, tb_lines: List[str], source: str) -> Optional[str]:
    """Ask LLM for a corrected version of the source code."""
    prompt = (
        "You are an expert Python developer. The following error occurred.\n\n"
        f"Error message:\n{error_msg}\n\n"
        f"Traceback:\n" + "\n".join(tb_lines) + "\n\n"
        f"Current source code:\n```python\n{source}\n```\n\n"
        "Provide a corrected version of the ENTIRE source file inside a single "
        "```python block. No explanations outside the block."
    )
    resp = query_llm(prompt)
    return _extract_code_block(resp) if resp else None


def ask_test(source: str, fixed: str, error_ctx: str) -> Optional[str]:
    """Ask LLM for a minimal test that verifies the fix."""
    prompt = (
        "You are an expert Python tester.\n\n"
        f"Original (buggy) code:\n```python\n{source}\n```\n\n"
        f"Fixed code:\n```python\n{fixed}\n```\n\n"
        f"Error context: {error_ctx}\n\n"
        "Write a short Python test script that imports the fixed module "
        "(saved as 'module.py' in the same directory) and runs a simple "
        "assertion. Print 'TEST PASSED' on success. Output ONLY the code "
        "inside a ```python block."
    )
    resp = query_llm(prompt)
    return _extract_code_block(resp) if resp else None


# ------------------------------------------------------------------ #
#  Isolated Testing                                                   #
# ------------------------------------------------------------------ #
def run_isolated_test(
    original_file: Path, fixed_code: str, test_code: str
) -> Tuple[bool, str]:
    """
    Create a temp dir, write fixed code as module.py, write test_fix.py,
    run the test. Returns (passed, output).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "module.py").write_text(fixed_code, encoding="utf-8")
        test_file = tmp / "test_fix.py"
        test_file.write_text(test_code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr
            passed = result.returncode == 0 and "TEST PASSED" in result.stdout
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "Test timed out"
        except Exception as e:
            return False, str(e)


# ------------------------------------------------------------------ #
#  Git Operations                                                     #
# ------------------------------------------------------------------ #
def commit_fix(file_path: Path, fixed_content: str, error_type: str) -> str:
    """Create fix/ branch, write file, commit. Returns branch name."""
    branch = f"fix/{error_type.lower()}-{int(time.time())}"
    try:
        run_git(["checkout", "main"])
        run_git(["checkout", "-b", branch])

        if not write_safe(file_path, fixed_content, backup=True):
            raise RuntimeError("Failed to write fixed file")

        run_git(["add", str(file_path)])
        run_git(["commit", "-m", f"Auto-fix: {error_type}\n\nGenerated by evolution_agent"])
        logger.info(f"Committed to branch {branch}")
        return branch
    except Exception:
        try:
            run_git(["checkout", "main"])
            run_git(["branch", "-D", branch])
        except Exception:
            pass
        raise


# ------------------------------------------------------------------ #
#  Error Handler                                                      #
# ------------------------------------------------------------------ #
class ErrorHandler:
    """Stateful handler that deduplicates and processes tracebacks."""

    def __init__(self):
        self.seen: set = set()

    def handle(self, tb_lines: List[str]):
        etype = get_error_type(tb_lines)
        h = error_hash("\n".join(tb_lines))

        if h in self.seen:
            logger.info(f"Skipping duplicate: {etype}")
            return
        logger.info(f"Processing: {etype}")

        src_file = extract_source_file(tb_lines)
        if not src_file:
            logger.warning("Source file not found in traceback")
            notify({"event": "error_skipped", "reason": "source_not_found",
                     "traceback": tb_lines})
            return

        source = read_safe(src_file)
        if not source:
            return

        # --- LLM fix ---
        err_msg = tb_lines[-1] if tb_lines else "Unknown"
        fixed = ask_fix(err_msg, tb_lines, source)
        if not fixed:
            notify({"event": "fix_failed", "reason": "llm_no_response",
                     "file": str(src_file), "error_type": etype})
            return

        # --- Manual approval ---
        if MANUAL_APPROVAL:
            print("\n--- Proposed Fix ---\n", fixed)
            print("\n--- Original ---\n", source)
            ans = input("Apply? (y/n): ").strip().lower()
            if ans != "y":
                notify({"event": "fix_rejected", "file": str(src_file),
                         "error_type": etype})
                return

        # --- LLM test ---
        test_code = ask_test(source, fixed, err_msg)
        if not test_code:
            notify({"event": "fix_failed", "reason": "llm_no_test",
                     "file": str(src_file), "error_type": etype})
            return

        # --- Isolated test ---
        passed, test_out = run_isolated_test(src_file, fixed, test_code)
        if not passed:
            logger.error(f"Test failed:\n{test_out}")
            notify({"event": "fix_failed", "reason": "test_failed",
                     "file": str(src_file), "error_type": etype,
                     "test_output": test_out})
            return

        logger.info("Test passed — committing fix")

        # --- Git commit ---
        try:
            branch = commit_fix(src_file, fixed, etype)
            notify({"event": "fix_committed", "file": str(src_file),
                     "error_type": etype, "branch": branch,
                     "test_output": test_out})
            self.seen.add(h)
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            notify({"event": "fix_failed", "reason": "git_error",
                     "file": str(src_file), "error_type": etype,
                     "error": str(e)})


# ------------------------------------------------------------------ #
#  Log Monitoring                                                     #
# ------------------------------------------------------------------ #
if HAS_WATCHDOG:
    class LogEventHandler(FileSystemEventHandler):
        """Watch log directory for .log file changes and parse tracebacks."""

        def __init__(self, handler: ErrorHandler):
            super().__init__()
            self.handler = handler
            self.positions: Dict[Path, int] = {}

        def on_modified(self, event):
            if not isinstance(event, FileModifiedEvent):
                return
            if not event.src_path.endswith(".log"):
                return
            self._process(Path(event.src_path))

        def _process(self, path: Path):
            try:
                with open(path, "r") as f:
                    f.seek(self.positions.get(path, 0))
                    lines = f.readlines()
                    self.positions[path] = f.tell()
            except Exception as e:
                logger.error(f"Read {path}: {e}")
                return

            i = 0
            while i < len(lines):
                line = lines[i]
                if line.startswith("Traceback (most recent call last):"):
                    tb_lines = [line.strip()]
                    i += 1
                    while i < len(lines):
                        nl = lines[i].rstrip()
                        if nl and not nl.startswith((" ", "\t")):
                            tb_lines.append(nl)
                            break
                        tb_lines.append(nl)
                        i += 1
                    # Check if it contains ERROR/CRITICAL or looks like a real traceback
                    if any("ERROR" in l or "CRITICAL" in l for l in tb_lines) or \
                       any(l.startswith(("Traceback", "  File")) for l in tb_lines):
                        self.handler.handle(tb_lines)
                i += 1


def start_monitoring():
    """Launch watchdog observer on LOG_DIR."""
    if not HAS_WATCHDOG:
        logger.error("watchdog not installed — cannot monitor logs")
        return

    handler = LogEventHandler(ErrorHandler())
    observer = Observer()
    observer.schedule(handler, path=LOG_DIR, recursive=False)
    observer.start()
    logger.info(f"Monitoring {LOG_DIR} for tracebacks…")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


# ------------------------------------------------------------------ #
#  Main                                                               #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    if not os.path.isdir(LOG_DIR):
        logger.error(f"Log directory {LOG_DIR} does not exist")
        sys.exit(1)
    if not SOURCE_DIRS:
        logger.error("No source directories configured")
        sys.exit(1)
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        logger.error("OpenAI provider requires an API key")
        sys.exit(1)

    start_monitoring()
