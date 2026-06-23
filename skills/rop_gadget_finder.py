"""ROP gadget finder: write-what-where search, ret2libc resolver, stack pivot finder, NOP sled prediction, exploitability scoring."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def find_rop_gadgets(binary_path: str, search_pattern: str = "", limit: int = 30) -> str:
    """Search for ROP gadgets in a binary using ROPgadget or ropper. If search_pattern provided, filters gadgets by regex."""
    try:
        if Path(binary_path).exists() and binary_path.startswith("/") and not os.access(binary_path, os.R_OK):
            return f"Permission denied: {binary_path}"
        if search_pattern:
            if Path("ROPgadget").exists():
                result = subprocess.run(  # noqa: S603, S607
                    ["python3", "-m", "ROPgadget", "--binary", binary_path, "--re", search_pattern],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode == 0:
                    lines = [ln for ln in result.stdout.splitlines() if "0x" in ln]
                    if lines:
                        displayed = lines[:limit]
                        return f"ROP gadgets matching '{search_pattern}' ({len(lines)} found, showing {len(displayed)}):\n" + "\n".join(displayed)
            result = subprocess.run(  # noqa: S603, S607
                ["ropper", "--file", binary_path, "--search", search_pattern],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                lines = [ln for ln in result.stdout.splitlines() if ln.strip() and "0x" in ln]
                if lines:
                    displayed = lines[:limit]
                    return f"ROP gadgets (ropper) matching '{search_pattern}' ({len(lines)} found):\n" + "\n".join(displayed)
            return f"No gadgets found matching '{search_pattern}' in {binary_path}"
        if Path("ROPgadget").exists():
            result = subprocess.run(["python3", "-m", "ROPgadget", "--binary", binary_path], capture_output=True, text=True, timeout=120)  # noqa: S603, S607
            if result.returncode == 0:
                lines = [ln for ln in result.stdout.splitlines() if "0x" in ln]
                displayed = lines[:limit]
                return f"ROP gadgets in {binary_path} ({len(lines)} total, showing {len(displayed)}):\n" + "\n".join(displayed)
        result = subprocess.run(["ropper", "--file", binary_path], capture_output=True, text=True, timeout=120)  # noqa: S603, S607
        if result.returncode == 0:
            lines = [ln for ln in result.stdout.splitlines() if ln.strip() and "0x" in ln]
            displayed = lines[:limit]
            return f"ROP gadgets (ropper) in {binary_path} ({len(lines)} total):\n" + "\n".join(displayed)
        return f"Unable to extract ROP gadgets from {binary_path}"
    except FileNotFoundError:
        return "ROPgadget/ropper not available. Install with: pip install ROPgadget ropper"
    except subprocess.TimeoutExpired:
        return f"Gadget search timed out for {binary_path}"
    except Exception as e:
        return f"ROP gadget search failed: {e}"


@tool()
def find_writable_sections(binary_path: str) -> str:
    """Find writable memory sections (e.g., .bss, .data) in a binary using readelf."""
    try:
        result = subprocess.run(["readelf", "-S", binary_path], capture_output=True, text=True, timeout=30)  # noqa: S603, S607
        if result.returncode != 0:
            return f"readelf failed: {result.stderr.strip()}"
        writable = []
        for line in result.stdout.splitlines():
            if "W" in line and "A" not in line.split("W")[1][:1]:
                parts = line.split()
                if len(parts) >= 3:
                    writable.append(f"  {line.strip()}")
        if not writable:
            writable = [ln.strip() for ln in result.stdout.splitlines() if "W" in ln]
        if not writable:
            return f"No writable sections found in {binary_path}"
        return f"Writable sections in {binary_path}:\n" + "\n".join(writable[:15])
    except FileNotFoundError:
        return "readelf not available"
    except Exception as e:
        return f"Section search failed: {e}"


@tool()
def check_aslr_status() -> str:
    """Check ASLR, PIE, and NX status for a process or system-wide."""
    try:
        indicators = []
        try:
            proc_randomize = Path("/proc/sys/kernel/randomize_va_space")
            if proc_randomize.exists():
                val = proc_randomize.read_text().strip()
                status = {0: "disabled", 1: "(partial) randomize mmap/stack", 2: "(full) randomize mmap/stack/brk"}.get(int(val), "unknown")
                indicators.append(f"ASLR: {val} {status}")
        except Exception:
            pass
        try:
            nx_proc = Path("/proc/sys/kernel/exec-shield")
            if nx_proc.exists():
                indicators.append(f"NX/exec-shield: {nx_proc.read_text().strip()}")
        except Exception:
            pass
        try:
            cpu_flags = Path("/proc/cpuinfo")
            if cpu_flags.exists():
                if "nx\n" in cpu_flags.read_text().lower():
                    indicators.append("NX: CPU supports NX bit")
        except Exception:
            pass
        try:
            result = subprocess.run(["sysctl", "kernel.randomize_va_space"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            if result.returncode == 0:
                indicators.append(f"sysctl: {result.stdout.strip()}")
        except FileNotFoundError:
            pass
        if not indicators:
            return "ASLR information unavailable—not on a standard Linux system"
        return "ASLR/PIE/NX status:\n" + "\n".join(indicators)
    except Exception as e:
        return f"ASLR check failed: {e}"


@tool()
def search_write_what_where(binary_path: str) -> str:
    """Search for write-what-where primitives (gadgets that allow controlled write to arbitrary address)."""
    try:
        patterns = ["mov.*\\[.*\\].*,", "st.*\\[", "xchg.*\\[", "pop.*;.*pop.*;.*mov", "pop.*\\["]
        results = []
        for pattern in patterns:
            result = find_rop_gadgets(binary_path, search_pattern=pattern, limit=10)
            if "matching" in result or "gadgets" in result.lower():
                results.append(result)
        if not results:
            return f"No write-what-where primitives found in {binary_path}"
        return "Write-what-where primitives:\n" + "\n---\n".join(results)
    except Exception as e:
        return f"WWW search failed: {e}"


@tool()
def find_ret2libc(binary_path: str = "/bin/sh", libc_path: str = "") -> str:
    """Attempt to resolve ret2libc gadgets: find libc base, system(), execve(), /bin/sh offset. Provide libc_path if known."""
    try:
        results = []
        if not libc_path:
            try:
                with open(f"/proc/{os.getpid()}/maps") as f:
                    for line in f:
                        if "libc" in line and "r-xp" in line:
                            base = line.split("-")[0]
                            libc_path = "/usr/lib/libc.so.6" if Path("/usr/lib/libc.so.6").exists() else ""
                            results.append(f"libc base (from /proc/self/maps): 0x{base}")
                            break
            except Exception:
                pass
        if not libc_path:
            cands = ["/usr/lib/libc.so.6", "/usr/lib/x86_64-linux-gnu/libc.so.6", "/lib/x86_64-linux-gnu/libc.so.6", "/usr/lib/aarch64-linux-gnu/libc.so.6"]
            for c in cands:
                if Path(c).exists():
                    libc_path = c
                    break
        if not libc_path:
            return "Cannot locate libc on this system"
        results.append(f"libc path: {libc_path}")
        try:
            result = subprocess.run(["strings", "-t", "x", libc_path], capture_output=True, text=True, timeout=60)  # noqa: S603, S607
            strings_out = result.stdout
            for target in ["system", "execve", "/bin/sh"]:
                for line in strings_out.splitlines():
                    if line.endswith(target) and len(line.split()) == 2:
                        offset = line.split()[0]
                        results.append(f"  {target}: 0x{offset}")
                        break
                else:
                    results.append(f"  {target}: not found")
        except FileNotFoundError:
            results.append("strings not available")
        return "ret2libc analysis:\n" + "\n".join(results)
    except Exception as e:
        return f"ret2libc analysis failed: {e}"


@tool()
def find_stack_pivots(binary_path: str) -> str:
    """Find stack pivot gadgets (xchg with rsp, add rsp, pop rsp)."""
    try:
        patterns = [
            "xchg.*rsp",
            "xchg.*esp",
            "add rsp",
            "add esp",
            "pop rsp",
            "pop esp",
            "leave; ret",
            "leave.*ret",
        ]
        results = []
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ["python3", "-m", "ROPgadget", "--binary", binary_path, "--re", pattern],
                    capture_output=True, text=True, timeout=30,
                )
                lines = [ln for ln in result.stdout.splitlines() if "0x" in ln]
                if lines:
                    results.append(f"  {pattern}: {len(lines)} gadgets (showing first 5):\n    " + "\n    ".join(lines[:5]))
            except Exception:
                try:
                    result = subprocess.run(
                        ["ropper", "--file", binary_path, "--search", pattern],
                        capture_output=True, text=True, timeout=30,
                    )
                    lines = [ln for ln in result.stdout.splitlines() if "0x" in ln]
                    if lines:
                        results.append(f"  {pattern} (ropper): {len(lines)} gadgets (showing first 5):\n    " + "\n    ".join(lines[:5]))
                except Exception:
                    pass
        if not results:
            return f"No stack pivot gadgets found in {binary_path}"
        return "Stack pivot gadgets:\n" + "\n".join(results)
    except Exception as e:
        return f"Stack pivot search failed: {e}"


@tool()
def predict_nop_sled(architecture: str = "x86_64") -> str:
    """Predict useful NOP sled bytes for a given architecture."""
    nops = {
        "x86": ["\\x90 (NOP)", "\\x90\\x90\\x90 (3-byte NOP)", "\\xeb\\xfd (jmp $)", "\\xe8\\xff\\xff\\xff\\xff\\xc0 (call/pop)"],
        "x86_64": ["\\x90 (NOP)", "\\x90\\x90\\x90 (3-byte NOP)", "\\xeb\\xfd (jmp $)", "\\x48\\x31\\xc0\\x90 (xor rax, rax + NOP)"],
        "arm": ["\\x00\\xf0\\x20\\xe3 (NOP-equivalent mov r0, r0)", "\\x01\\x10\\xa0\\xe1 (mov r1, r1)", "\\x1e\\xff\\x2f\\xe1 (bx lr — return)"],
        "arm64": ["\\x1f\\x20\\x03\\xd5 (NOP)", "\\xc0\\x03\\x5f\\xd6 (ret)", "\\x00\\x00\\x80\\xd2 (mov x0, #0)"],
        "mips": ["\\x00\\x00\\x00\\x00 (sll r0, r0, 0 — NOP)", "\\x00\\x00\\x08\\x00 (jr r0)"],
        "powerpc": ["\\x60\\x00\\x00\\x00 (NOP)", "\\x4e\\x80\\x00\\x20 (blr — return)"],
        "riscv32": ["\\x00\\x00\\x00\\x13 (nop = addi x0, x0, 0)", "\\x00\\x00\\x00\\x33 (NOP-equivalent)"],
        "riscv64": ["\\x00\\x00\\x00\\x13 (nop = addi x0, x0, 0)", "\\x00\\x00\\x00\\x33 (NOP-equivalent)"],
    }
    selected = nops.get(architecture.lower(), nops.get("x86_64"))
    return f"NOP sled bytes for {architecture}:\n" + "\n".join(f"  {n}" for n in selected)


@tool()
def exploitability_score(binary_path: str) -> str:
    """Calculate an exploitability score (0–100) for a given binary by checking ASLR/PIE/NX/writable sections/gadgets."""
    try:
        score = 0
        details = []
        try:
            aslr_path = Path("/proc/sys/kernel/randomize_va_space")
            if aslr_path.exists():
                aslr_val = int(aslr_path.read_text().strip())
                if aslr_val == 0:
                    score += 20
                    details.append("ASLR disabled +20")
                else:
                    details.append(f"ASLR enabled ({aslr_val}) no points")
        except Exception:
            pass
        try:
            result = subprocess.run(["readelf", "-h", binary_path], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            if "DYN (Shared object file)" in result.stdout:
                details.append("PIE enabled, no points")
            elif "EXEC (Executable file)" in result.stdout:
                score += 20
                details.append("No PIE +20")
        except Exception:
            pass
        try:
            result = subprocess.run(["readelf", "-l", binary_path], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            if "GNU_STACK" in result.stdout:
                for line in result.stdout.splitlines():
                    if "GNU_STACK" in line and "RWE" in line:
                        score += 10
                        details.append("NX disabled (executable stack) +10")
                        break
                else:
                    details.append("NX enabled, no points")
        except Exception:
            pass
        try:
            result = subprocess.run(["readelf", "-S", binary_path], capture_output=True, text=True, timeout=10)  # noqa: S603, S607
            writable_sections = sum(1 for line in result.stdout.splitlines() if "W" in line and ".text" not in line)
            if writable_sections > 2:
                score += 15
                details.append(f"Writable sections ({writable_sections}) +15")
        except Exception:
            pass
        try:
            libc_result = find_ret2libc(binary_path)
            if "libc base" in libc_result:
                score += 10
                details.append("Known libc base +10")
        except Exception:
            pass
        try:
            pivot_result = find_stack_pivots(binary_path)
            if len([x for x in pivot_result.splitlines() if "0x" in x]) > 0:
                score += 15
                details.append("Stack pivot found +15")
        except Exception:
            pass
        try:
            www_result = search_write_what_where(binary_path)
            if "Write-what-where" in www_result and len([x for x in www_result.splitlines() if "0x" in x]) > 1:
                score += 10
                details.append("Write-what-where gadget +10")
        except Exception:
            pass
        score = min(score, 100)
        return f"Exploitability score: {score}/100\nBreakdown:\n" + "\n".join(f"  {d}" for d in details)
    except Exception as e:
        return f"Exploitability scoring failed: {e}"
