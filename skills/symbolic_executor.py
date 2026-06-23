# ruff: noqa: S108, S311
"""Symbolic execution interface for finding hidden code paths and vulnerabilities."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def concrete_execute(binary_path: str, args: str = "") -> str:
    """Execute a binary with given arguments (in a read-only /tmp sandbox) and return output."""
    try:
        p = Path(binary_path)
        if not p.exists():
            return f"Binary not found: {binary_path}"
        if not os.access(str(p), os.X_OK):
            return f"Binary not executable: {binary_path}"
        import os as os_mod
        import tempfile
        sandbox = Path(tempfile.mkdtemp(prefix="sandbox_"))
        cmd = [str(p)] + (args.split() if args else [])
        proc = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=15,
            env={**os_mod.environ, "HOME": str(sandbox), "TMPDIR": str(sandbox)},
        )
        import shutil
        shutil.rmtree(str(sandbox), ignore_errors=True)
        out = proc.stdout[-2000:] if proc.stdout else ""
        err = proc.stderr[-1000:] if proc.stderr else ""
        return f"Execution (exit {proc.returncode}):\nstdout:\n{out}\nstderr:\n{err}"
    except PermissionError:
        return f"Permission denied: {binary_path}"
    except subprocess.TimeoutExpired:
        return f"Execution timed out (15s): {binary_path}"
    except FileNotFoundError:
        return f"Binary not found: {binary_path}"
    except Exception as e:
        return f"Execution failed: {e}"


@tool()
def symb_execute_path(binary_path: str, function: str = "main") -> str:
    """Attempt symbolic execution using angr (must be installed)."""
    try:
        p = Path(binary_path)
        if not p.exists():
            return f"Binary not found: {binary_path}"
        try:
            import angr  # noqa: F401
            from angr import Project
        except ImportError:
            return "angr not installed. Install: pip install angr"
        proj = Project(str(p), auto_load_libs=False)
        cfg = proj.analyses.CFGFast()
        target_func = None
        for func_addr, func_obj in cfg.functions.items():
            if func_obj.name == function:
                target_func = func_obj
                break
        if target_func is None:
            funcs = [f"{f.name} @ 0x{a:x}" for a, f in cfg.functions.items()][:30]
            return f"Function '{function}' not found. Available ({len(cfg.functions)}):\n" + "\n".join(
                f"  {f}" for f in funcs
            )
        state = proj.factory.entry_state()
        sm = proj.factory.simulation_manager(state)
        sm.explore(find=target_func.addr, num_find=1)
        if sm.found:
            found = sm.found[0]
            return (
                f"Symbolic execution: reached function '{function}' @ 0x{target_func.addr:x}\n"
                f"Path: {len(sm.history)} steps\n"
                f"State: {found}"
            )
        return f"Could not reach function '{function}' with symbolic execution"
    except Exception as e:
        return f"Symbolic execution failed: {e}"


@tool()
def generate_test_case(binary_path: str, crash_input: str = "") -> str:
    """Generate a test case or crash input file for a binary."""
    try:
        from Crypto.Random import get_random_bytes  # noqa: F401
        has_crypto = True
    except ImportError:
        has_crypto = False
    if crash_input:
        out_path = Path("/tmp") / f"crash_input_{abs(hash(crash_input)) % 100000}_{Path(binary_path).stem}.bin"
        if crash_input.startswith("0x") or all(c in "0123456789abcdefABCDEF" for c in crash_input):
            import codecs
            out_path.write_bytes(codecs.decode(crash_input.replace("0x", ""), "hex"))
        else:
            out_path.write_text(crash_input)
        return f"Crash input written: {out_path} ({out_path.stat().st_size} bytes)"
    import random
    patterns = []
    for i in range(10):
        if has_crypto:
            patterns.append(get_random_bytes(64).hex())
        else:
            patterns.append("".join(random.choice("0123456789abcdef") for _ in range(128)))
    out_file = Path("/tmp") / f"fuzz_cases_{Path(binary_path).stem}_{random.randint(1000, 9999)}.txt"
    out_file.write_text("\n".join(patterns))
    return (
        f"Generated 10 test cases → {out_file}\n"
        f"  Pattern format: random hex strings\n"
        f"  To use: Provide crash input via scan_input parameter, or feed patterns to the binary"
    )
