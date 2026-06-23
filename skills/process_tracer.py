import subprocess
import time

from core.skills.registry import tool

_tracer_pids = {}

@tool()
def attach_strace(pid: int, output_path: str = "") -> str:
    """Attach strace to a running process by PID."""
    try:
        out = output_path or "/tmp/strace_%d_%d.log" % (pid, int(time.time()))
        cmd = ["strace", "-p", str(pid), "-o", out, "-f", "-tt"]
        proc = subprocess.Popen(cmd, start_new_session=True)  # noqa: S603
        _tracer_pids[pid] = {"proc": proc, "type": "strace", "output": out, "started": time.time()}
        return "strace attached to PID %d, logging to %s (tracer PID %d)" % (pid, out, proc.pid)
    except FileNotFoundError:
        return "strace not available"
    except Exception as e:
        return f"Error: {e}"


@tool()
def attach_ltrace(pid: int, output_path: str = "") -> str:
    """Attach ltrace to a running process by PID."""
    try:
        out = output_path or "/tmp/ltrace_%d_%d.log" % (pid, int(time.time()))
        cmd = ["ltrace", "-p", str(pid), "-o", out]
        proc = subprocess.Popen(cmd, start_new_session=True)  # noqa: S603
        _tracer_pids[pid] = {"proc": proc, "type": "ltrace", "output": out, "started": time.time()}
        return "ltrace attached to PID %d, logging to %s (tracer PID %d)" % (pid, out, proc.pid)
    except FileNotFoundError:
        return "ltrace not available"
    except Exception as e:
        return f"Error: {e}"


@tool()
def detach_tracer(pid: int) -> str:
    """Detach strace/ltrace from a process by its PID."""
    entry = _tracer_pids.pop(pid, None)
    if not entry:
        return "No tracer found for PID %d" % pid
    try:
        entry["proc"].terminate()
        entry["proc"].wait(timeout=5)
        return "Detached %s from PID %d (ran for %ds)" % (entry["type"], pid, int(time.time() - entry["started"]))
    except Exception as e:
        return f"Error detaching: {e}"


@tool()
def get_trace_log(pid: int, tail_lines: int = 50) -> str:
    """Read the trace log for a given PID."""
    entry = _tracer_pids.get(pid)
    if not entry:
        return "No trace log found for PID %d" % pid
    try:
        proc = subprocess.run(  # noqa: S603
            ["tail", "-n", str(tail_lines), entry["output"]],  # noqa: S607
            capture_output=True, text=True, timeout=10,
        )
        return "=== %s log for PID %d (last %d lines) ===\n%s" % (entry["type"], pid, tail_lines, proc.stdout)
    except FileNotFoundError:
        return "tail not available"
    except Exception as e:
        return f"Error: {e}"
