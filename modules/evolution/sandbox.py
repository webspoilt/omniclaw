#!/usr/bin/env python3
"""
sandbox.py — Isolated test runner for the evolution agent.
Creates a temporary directory, writes the fixed module and test,
runs the test in a subprocess, and cleans up.
"""

import sys
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Tuple


def run_isolated_test(
    module_name: str,
    fixed_code: str,
    test_code: str,
    timeout: int = 30,
) -> Tuple[bool, str]:
    """
    Run a test in an isolated sandbox directory.

    Args:
        module_name: base name of the module file (e.g. 'utils.py')
        fixed_code: the corrected source code
        test_code: LLM-generated test script
        timeout: max seconds for the test subprocess

    Returns:
        (passed, output) — True if test passed and printed TEST PASSED
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="omniclaw_sandbox_"))
    try:
        # Write module
        (tmpdir / module_name).write_text(fixed_code, encoding="utf-8")

        # Write test
        test_path = tmpdir / "test_fix.py"
        test_path.write_text(test_code, encoding="utf-8")

        # Run
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0 and "TEST PASSED" in result.stdout
        return passed, output

    except subprocess.TimeoutExpired:
        return False, f"Test timed out after {timeout}s"
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
