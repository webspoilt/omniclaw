#!/usr/bin/env python3
"""
genesis_local.py - Nightly self-refactor engine (runs only on Asus TUF).
Performs fuzzing and LLM-based patching of core code.
"""

import ast
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

# Force local-only check
ASUS_TUF_ONLY = os.environ.get('OMNICLAW_NODE') == 'desktop' or Path('/proc/device-tree/model').read_text().find('TUF') != -1
if not ASUS_TUF_ONLY:
    if os.name == 'nt' and os.environ.get('OMNICLAW_NODE') != 'desktop':
        logger = logging.getLogger("LocalGenesis")
        logger.critical("Genesis runs only on Asus TUF node. Set OMNICLAW_NODE=desktop to override.")
        sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LocalGenesis")

class LocalGenesis:
    def __init__(self, config):
        self.core_dir = Path(config.get('core_dir', 'core'))
        self.modules_dir = Path(config.get('modules_dir', 'modules'))
        self.ollama_url = config.get('ollama_url', 'http://localhost:11434')
        self.llm_model = config.get('llm_model', 'codellama:latest')
        self.fuzz_iterations = config.get('fuzz_iterations', 100)

    def run_nightly(self):
        """Main entry point - called by cron."""
        logger.info("Starting nightly self-evolution cycle")

        # 1. Find Python files to analyze
        python_files = list(self.core_dir.rglob('*.py')) + list(self.modules_dir.rglob('*.py'))

        # 2. Perform simple static analysis (AST-based)
        for py_file in random.sample(python_files, min(5, len(python_files))):
            self._analyze_and_patch(py_file)

        # 3. Run fuzzing on critical modules
        self._fuzz_core_modules()

        logger.info("Nightly self-evolution complete")

    def _analyze_and_patch(self, file_path):
        """Analyze a Python file for potential improvements using LLM."""
        logger.info(f"Analyzing {file_path}")

        code = file_path.read_text(encoding="utf-8")

        prompt = f"""You are a code optimization expert. Analyze this Python code for:
1. Performance bottlenecks
2. Security vulnerabilities
3. Code style improvements
4. Potential bugs

Provide a corrected version of the ENTIRE file with improvements.
Output only the code inside ```python ... ```.

```python
{code}
```"""

        try:
            resp = requests.post(f"{self.ollama_url}/api/generate",
                               json={"model": self.llm_model, "prompt": prompt, "stream": False},
                               timeout=120)
            response = resp.json().get('response', '')

            import re
            match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
            if match:
                improved_code = match.group(1)

                try:
                    ast.parse(improved_code)
                    backup = file_path.with_suffix(file_path.suffix + '.genesis.bak')
                    shutil.copy2(file_path, backup)
                    file_path.write_text(improved_code, encoding="utf-8")
                    logger.info(f"Applied improvements to {file_path} (backup at {backup})")
                except SyntaxError as e:
                    logger.error(f"LLM produced invalid syntax for {file_path}: {e}")
        except Exception as e:
            logger.error(f"LLM analysis failed for {file_path}: {e}")

    def _fuzz_core_modules(self):
        """Simple fuzzing by running modules with random inputs."""
        for module in self.core_dir.glob('*.py'):
            if module.name.startswith('__'):
                continue

            logger.info(f"Fuzzing {module}")

            for _ in range(self.fuzz_iterations):
                try:
                    args = ['--' + str(random.randint(1,1000)) for _ in range(random.randint(0,3))]
                    result = subprocess.run([sys.executable, str(module)] + args,
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode != 0 and result.stderr:
                        crash_log = Path('logs/fuzz_crashes.log')
                        crash_log.parent.mkdir(parents=True, exist_ok=True)
                        with open(crash_log, 'a') as f:
                            f.write(f"{time.ctime()}: {module} crashed with args {args}\n")
                            f.write(result.stderr + "\n---\n")
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    logger.error(f"Fuzzing {module} failed: {e}")

def schedule_nightly(config_path='config/genesis_config.yaml'):
    """Schedule to run daily at 2 AM."""
    try:
        import schedule
    except ImportError:
        logger.error("Please install 'schedule' module to run the daemon (pip install schedule).")
        logger.info("Running once immediately...")
        genesis = LocalGenesis({})
        genesis.run_nightly()
        return

    import yaml
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}

    genesis = LocalGenesis(config)
    schedule.every().day.at("02:00").do(genesis.run_nightly)
    logger.info("Nightly schedule registered (02:00 AM).")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Can run immediate cycle with args, else schedules
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        LocalGenesis({}).run_nightly()
    else:
        schedule_nightly()
