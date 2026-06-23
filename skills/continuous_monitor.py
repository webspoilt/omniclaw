import subprocess

from core.skills.registry import tool


@tool()
def tail_logs(log_path: str, lines: int = 50) -> str:
    """Tail a log file and highlight anomalies (ERROR, WARN, traceback)."""
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["tail", "-n", str(lines), log_path],  # noqa: S607
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode != 0:
            return f"tail failed: {proc.stderr[:500]}"
        content = proc.stdout
        anomalies = []
        normal = []
        for line in content.splitlines():
            low = line.lower()
            critical_kw = ["error", "traceback", "exception", "critical", "fail", "oom", "segfault", "panic"]
            if any(kw in low for kw in critical_kw):
                anomalies.append(f"[!] {line}")
            elif any(kw in low for kw in ["warn", "timeout", "retry", "slow"]):
                anomalies.append(f"[~] {line}")
            else:
                normal.append(line)
        result = f"=== Log tail: {log_path} ({len(content)} chars, {len(anomalies)} anomalies) ===\n"
        if anomalies:
            result += "\n".join(anomalies[:30])
            if len(anomalies) > 30:
                result += f"\n... and {len(anomalies) - 30} more anomalies"
            result += "\n\n--- Last 10 normal lines ---\n"
            result += "\n".join(normal[-10:])
        else:
            result += "\n".join(normal)
        return result
    except Exception as e:
        return f"Error: {e}"


@tool()
def watch_file_changes(directory: str, since_minutes: int = 60) -> str:
    """Report files changed within the last N minutes."""
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["find", directory, "-type", "f", "-mmin", f"-{since_minutes}"],  # noqa: S607
            capture_output=True, text=True, timeout=30
        )
        files = [f for f in proc.stdout.splitlines() if f.strip()]
        if not files:
            return f"No files changed in {directory} in the last {since_minutes} minutes."
        result = f"=== Files changed (last {since_minutes} min) ===\n"
        for f in sorted(files)[:100]:
            result += f"{f}\n"
        if len(files) > 100:
            result += f"... and {len(files) - 100} more"
        return result
    except Exception as e:
        return f"Error: {e}"


@tool()
def check_process_anomalies() -> str:
    """List suspicious processes (high CPU, root shells, crypto miners)."""
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["ps", "aux", "--sort=-%cpu"],  # noqa: S607
            capture_output=True, text=True, timeout=10
        )
        lines = proc.stdout.splitlines()
        header = lines[0] if lines else ""
        suspicious = [header]
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 11:
                continue
            cpu = parts[2]
            cmd = " ".join(parts[10:]).lower()
            try:
                high_cpu = float(cpu) > 50.0
            except ValueError:
                high_cpu = False
            suspicious_keywords = ["stratum", "minerd", "xmrig", "cryptonight", "ethminer",
                                   "nc -e", "bash -i", "sh -i", "perl -e", "python -c"]
            is_suspicious = any(kw in cmd for kw in suspicious_keywords)
            if high_cpu:
                suspicious.append(f"[HIGH CPU] {line}")
            elif is_suspicious:
                suspicious.append(f"[!] {line}")
        if len(suspicious) <= 1:
            return "No suspicious processes detected."
        return "\n".join(suspicious[:30])
    except Exception as e:
        return f"Error: {e}"
