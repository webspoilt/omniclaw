"""Interface with compilers (gcc, clang, rustc) to build binaries."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from core.skills.registry import tool


@tool(
    name="check_compiler_available",
    description="Check which compilers are installed on the system.",
    parameters={},
)
async def check_compiler_available() -> dict[str, bool]:
    compilers = ["gcc", "g++", "clang", "clang++", "rustc", "go", "nim", "zig"]
    result = {}
    for c in compilers:
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=5)
            result[c] = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            result[c] = False
    return result


@tool(
    name="compile_c_source",
    description="Write a C source file to a temp dir and compile it with gcc. Returns binary path or errors.",
    parameters={
        "source": {"type": "string", "description": "Complete C source code"},
        "output_name": {"type": "string", "description": "Desired output binary name"},
        "flags": {"type": "string", "description": "Extra compiler flags, e.g. '-O2 -Wall'"},
    },
    required=["source", "output_name"],
)
async def compile_c_source(source: str, output_name: str, flags: str | None = None) -> str:
    with tempfile.TemporaryDirectory(prefix="omniclaw_compile_") as tmp:
        src_path = Path(tmp) / "source.c"
        src_path.write_text(source, encoding="utf-8")
        bin_path = Path(tmp) / output_name

        cmd = ["gcc", str(src_path), "-o", str(bin_path)]
        if flags:
            cmd.extend(flags.split())

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            return "Error: gcc not found on system"
        except subprocess.TimeoutExpired:
            return "Error: compilation timed out after 120s"

        if proc.returncode != 0:
            return f"Compilation failed:\n{proc.stderr}"

        bin_path.chmod(0o755)
        return f"Compiled successfully:\n  binary: {bin_path}\n  size: {bin_path.stat().st_size} bytes\n  run with: {bin_path}"


@tool(
    name="compile_rust_source",
    description="Write Rust source and compile with rustc. Returns binary path or errors.",
    parameters={
        "source": {"type": "string", "description": "Complete Rust source code"},
        "output_name": {"type": "string", "description": "Desired output binary name"},
    },
    required=["source", "output_name"],
)
async def compile_rust_source(source: str, output_name: str) -> str:
    with tempfile.TemporaryDirectory(prefix="omniclaw_rust_") as tmp:
        src_path = Path(tmp) / "source.rs"
        src_path.write_text(source, encoding="utf-8")
        bin_path = Path(tmp) / output_name

        cmd = ["rustc", str(src_path), "-o", str(bin_path)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except FileNotFoundError:
            return "Error: rustc not found on system"
        except subprocess.TimeoutExpired:
            return "Error: compilation timed out after 180s"

        if proc.returncode != 0:
            return f"Compilation failed:\n{proc.stderr}"

        bin_path.chmod(0o755)
        return f"Compiled successfully:\n  binary: {bin_path}\n  size: {bin_path.stat().st_size} bytes"


@tool(
    name="run_binary",
    description="Execute a compiled binary in a temp directory with given args. Returns stdout/stderr.",
    parameters={
        "binary_path": {"type": "string", "description": "Full path to executable"},
        "args": {"type": "string", "description": "Command-line arguments as a single string"},
        "timeout_sec": {"type": "integer", "description": "Timeout in seconds (default 30)"},
    },
    required=["binary_path"],
)
async def run_binary(binary_path: str, args: str | None = None, timeout_sec: int = 30) -> str:
    bp = Path(binary_path).resolve()
    if not bp.is_file():
        return "Error: binary not found"
    if not os.access(str(bp), os.X_OK):
        return "Error: binary not executable"

    cmd = [str(bp)]
    if args:
        cmd.extend(args.split())

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        return "Error: execution timed out"
    except Exception as e:
        return f"Error: {e}"

    return f"Exit code: {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
