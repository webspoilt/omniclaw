"""Memory forensics: RAM dumping, injection detection, secret recovery."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def dump_ram(output_path: str = "") -> str:
    """Capture a memory dump using avml, lime, or /proc/kcore."""
    try:
        out = output_path or f"/tmp/ram_dump_{os.getpid()}.bin"  # noqa: S108
        for tool_name, cmd_template in [
            ("avml", ["avml", out]),
            ("lime", ["insmod", "/path/to/lime.ko", f"path={out}", "format=raw"]),
        ]:
            try:
                proc = subprocess.run(cmd_template, capture_output=True, text=True, timeout=60)  # noqa: S603, S607
                if proc.returncode == 0:
                    size = Path(out).stat().st_size if Path(out).exists() else 0
                    return f"Memory dump via {tool_name}: {out} ({size / 1024 / 1024:.0f} MB)"
            except FileNotFoundError:
                continue
        kcore = Path("/proc/kcore")
        if kcore.exists() and os.access(str(kcore), os.R_OK):
            return "kcore available but too large to dump directly. Use volatility3 with kcore plugin."
        return "No memory dumping tools available (avml, lime, or kcore access required)"
    except Exception as e:
        return f"RAM dump failed: {e}"


@tool()
def find_injection(dump_path: str = "") -> str:
    """Scan a memory dump for signs of code injection (requires volatility3)."""
    try:
        if not dump_path:
            return "Provide a path to a memory dump (raw, .vmem, .mem) or use 'kcore' for live /proc/kcore"
        try:
            cmd = ["vol", "-f", dump_path, "linux.malfind.Malfind"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # noqa: S603, S607
            if proc.returncode == 0:
                lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
                if len(lines) > 2:
                    return f"Injection scan results ({len(lines)} lines):\n" + "\n".join(lines[:50])
                return "No injection indicators found in memory dump"
            return f"Volatility3 failed: {proc.stderr.strip()[:300]}"
        except FileNotFoundError:
            return "volatility3 not available. Install: pip install volatility3"
    except Exception as e:
        return f"Injection detection failed: {e}"


@tool()
def recover_keys(dump_path: str = "") -> str:
    """Search a memory dump for cryptographic keys and secrets using volatility3 or strings."""
    try:
        if not dump_path:
            return "Provide a path to a memory dump"
        patterns = ["ssh-rsa", "ssh-ed25519", "-----BEGIN", "PRIVATE KEY", "PRIVATE KEY BLOCK"]
        cmd = ["strings", dump_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # noqa: S603, S607
        if proc.returncode != 0:
            return f"strings failed: {proc.stderr.strip()[:200]}"
        findings = []
        for pattern in patterns:
            import re as re_mod
            matches = re_mod.findall(f".{{0,50}}{pattern}.{{0,50}}", proc.stdout, re_mod.IGNORECASE)
            for m in matches[:10]:
                findings.append(f"  ...{m.strip()[:120]}...")
        if not findings:
            return "No cryptographic keys found in memory dump"
        return f"Potential keys recovered from memory ({len(findings)}):\n" + "\n".join(findings[:50])
    except FileNotFoundError:
        return "strings not available"
    except Exception as e:
        return f"Key recovery failed: {e}"
