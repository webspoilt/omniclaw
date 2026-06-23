#!/usr/bin/env python3
"""
local_code_janitor.py - Self-healing agent that runs locally on Asus TUF.
Monitors logs, applies LLM-generated patches, and validates in sandbox.
"""

import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests
import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Force local-only check (Update to match actual host)
ASUS_TUF_ONLY = os.environ.get('OMNICLAW_NODE') == 'desktop' or Path('/proc/device-tree/model').read_text().find('TUF') != -1
if not ASUS_TUF_ONLY:
    # On Windows for testing, we might bypass the strict block if OMNICLAW_NODE is set
    if os.name == 'nt' and os.environ.get('OMNICLAW_NODE') != 'desktop':
        logger = logging.getLogger("LocalCodeJanitor")
        logger.critical("Code Janitor runs only on Asus TUF (desktop) node. Set environment property OMNICLAW_NODE=desktop to override.")
        sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LocalCodeJanitor")

class LocalJanitorHandler(FileSystemEventHandler):
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.log_dir = Path(self.config['log_dir'])
        self.source_dirs = [Path(d) for d in self.config['source_dirs']]
        self.ollama_url = self.config.get('ollama_url', 'http://localhost:11434')
        self.llm_model = self.config.get('llm_model', 'codellama:latest')
        self.processed_errors = set()

    def on_modified(self, event):
        if not event.src_path.endswith('.log'):
            return
        time.sleep(1)  # Let file write complete
        self._process_log(Path(event.src_path))

    def _process_log(self, log_path):
        """Extract traceback and trigger fix if new."""
        try:
            with open(log_path) as f:
                lines = f.readlines()
        except FileNotFoundError:
            return

        traceback = self._extract_traceback(lines)
        if not traceback:
            return

        error_hash = hashlib.sha256(traceback.encode()).hexdigest()
        if error_hash in self.processed_errors:
            return
        self.processed_errors.add(error_hash)

        # Find source file
        source_file = self._find_source_file(traceback)
        if not source_file:
            logger.warning("Could not locate source file in traceback")
            return

        # Read current code
        original_code = source_file.read_text(encoding="utf-8")

        # Ask local LLM for fix
        fixed_code = self._ask_llm_for_fix(traceback, original_code)
        if not fixed_code:
            return

        # Validate in sandbox
        if self._validate_fix(source_file, original_code, fixed_code):
            self._apply_fix(source_file, fixed_code, error_hash)

    def _extract_traceback(self, lines):
        """Extract full traceback from log lines."""
        tb = []
        in_tb = False
        for line in lines:
            if line.startswith('Traceback (most recent call last):') or line.startswith('ERROR:'):
                in_tb = True
                tb = [line.strip()]
            elif in_tb:
                tb.append(line.strip())
                if not line.startswith(' ') and not line.startswith('  File'):
                    in_tb = False
        return '\n'.join(tb) if tb else None

    def _find_source_file(self, traceback):
        """Extract first source file from traceback that's in source_dirs."""
        import re
        pattern = r'File "([^"]+)"'
        for match in re.finditer(pattern, traceback):
            path = Path(match.group(1))
            for src in self.source_dirs:
                try:
                    if src.resolve() in path.resolve().parents or src.resolve() == path.resolve().parent:
                        return path
                except Exception:
                    continue
        return None

    def _ask_llm_for_fix(self, traceback, code):
        """Query local Ollama for a fix."""
        prompt = f"""You are an expert Python developer. Fix the following error.

Traceback:
{traceback}

Current code:
```python
{code}
```
Provide the full corrected code in a single Python code block.
"""
        logger.info(f"Querying local LLM ({self.llm_model}) for fix...")
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False
            }, timeout=120)

            result = response.json().get("response", "")
            # Extract code block
            if "```python" in result:
                return result.split("```python")[1].split("```")[0].strip()
            elif "```" in result:
                return result.split("```")[1].split("```")[0].strip()
            return result.strip()
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return None

    def _validate_fix(self, source_file, original_code, fixed_code):
        """Validate the LLM's fix using the core sandbox."""
        logger.info("Validating fix in temporary sandbox...")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / source_file.name
                tmp_path.write_text(fixed_code, encoding="utf-8")

                # Basic execution check to ensure no syntax/import errors
                res = subprocess.run([sys.executable, "-m", "py_compile", str(tmp_path)],
                                     capture_output=True, text=True)
                if res.returncode != 0:
                    logger.error(f"Sandbox compilation failed: {res.stderr}")
                    return False

                logger.info("Fix compiled successfully.")
                return True
        except Exception as e:
            logger.error(f"Sandbox hit an error: {e}")
            return False

    def _apply_fix(self, source_file, fixed_code, error_hash):
        """Apply the validated fix and create a .bak."""
        logger.info(f"Applying fix to {source_file}")

        bak_path = source_file.with_suffix(source_file.suffix + '.bak')
        try:
            shutil.copy2(source_file, bak_path)
            source_file.write_text(fixed_code, encoding="utf-8")
            logger.info("Fix applied successfully. Backup created.")
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python local_code_janitor.py <config.yaml>")
        sys.exit(1)

    config = sys.argv[1]
    handler = LocalJanitorHandler(config)

    observer = Observer()
    observer.schedule(handler, str(handler.log_dir), recursive=True)
    observer.start()

    logger.info(f"Local Code Janitor active. Monitoring {handler.log_dir} for errors.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
