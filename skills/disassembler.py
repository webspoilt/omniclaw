"""Binary disassembly and function extraction via objdump/radare2."""
from __future__ import annotations

import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def disassemble_function(path: str, function: str = "", arch: str = "") -> str:
    """Disassemble a specific function (or entire file) from a binary using objdump."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        data = p.read_bytes()
        if data[:4] != b"\x7fELF":
            return "Not a valid ELF file"
        cmd = ["objdump", "-d", "--no-show-raw-insn"]
        if function:
            cmd.extend(["--disassemble", function])
        if arch:
            cmd.extend(["-m", arch])
        cmd.append(str(p))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # noqa: S603, S607
        if proc.returncode != 0:
            error = proc.stderr.strip()[:500]
            if "objdump" in error.lower() or "not found" in error.lower():
                return "objdump not available on this system"
            return f"objdump failed: {error}"
        output = proc.stdout
        if function:
            lines = [line for line in output.splitlines() if line.strip()]
            if not lines:
                return f"Function '{function}' not found in {path}"
            return f"=== {function} in {path} ===\n" + "\n".join(lines[:200])
        return output[:5000]
    except FileNotFoundError:
        return "objdump not available on this system"
    except Exception as e:
        return f"Disassembly failed: {e}"


@tool()
def list_functions(path: str) -> str:
    """List all defined functions in a binary via nm or objdump."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        for cmd_base in [["nm", "-C"], ["objdump", "-t"]]:
            try:
                proc = subprocess.run(  # noqa: S603
                    [*cmd_base, str(p)],  # noqa: S607
                    capture_output=True, text=True, timeout=15,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    functions = []
                    for line in proc.stdout.splitlines():
                        parts = line.split()
                        if len(parts) >= 3 and parts[2] in ("T", "t", "W", "w"):
                            name = parts[-1]
                            addr = parts[0]
                            functions.append(f"  0x{addr}  {name}")
                    if functions:
                        return f"Functions in {path} ({len(functions)}):\n" + "\n".join(functions[:150])
                    return f"No text symbols found in {path}"
            except FileNotFoundError:
                continue
        return "nm/objdump not available on this system"
    except Exception as e:
        return f"Function listing failed: {e}"


@tool()
def find_pattern_in_binary(path: str, pattern_hex: str) -> str:
    """Search for a hex pattern in a binary and return offsets."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        pattern = bytes.fromhex(pattern_hex.replace(" ", "").replace("\\x", ""))
        data = p.read_bytes()
        offsets = []
        start = 0
        while True:
            pos = data.find(pattern, start)
            if pos == -1:
                break
            offsets.append(pos)
            start = pos + 1
        if not offsets:
            return f"Pattern '{pattern_hex}' not found in {path}"
        return f"Pattern '{pattern_hex}' found at {len(offsets)} offset(s):\n" + "\n".join(
            f"  0x{off:x} ({off})" for off in offsets[:50]
        )
    except ValueError:
        return "Invalid hex pattern"
    except Exception as e:
        return f"Pattern search failed: {e}"
