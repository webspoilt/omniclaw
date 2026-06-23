# ruff: noqa: E741, S107, S108
"""Steganography detection, embedding, and extraction in images, audio, and text."""
from __future__ import annotations

import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def detect_stego(path: str) -> str:
    """Detect steganography in a file using available tools (steghide, zsteg, strings)."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        ext = p.suffix.lower()
        results = []
        if ext in (".jpg", ".jpeg", ".bmp"):
            try:
                proc = subprocess.run(  # noqa: S603
                    ["steghide", "info", str(p)],  # noqa: S607
                    capture_output=True, text=True, timeout=15,
                )
                if proc.returncode == 0 and "no embedded data" not in proc.stdout.lower():
                    results.append(f"steghide: possible embedded data — {proc.stdout.strip()[:200]}")
            except FileNotFoundError:
                results.append("steghide not available")
        if ext in (".png", ".bmp"):
            try:
                proc = subprocess.run(  # noqa: S603
                    ["zsteg", str(p)],  # noqa: S607
                    capture_output=True, text=True, timeout=30,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    results.append(f"zsteg: {proc.stdout.strip()[:500]}")
            except FileNotFoundError:
                pass
        try:
            proc = subprocess.run(  # noqa: S603
                ["strings", str(p)],  # noqa: S607
                capture_output=True, text=True, timeout=15,
            )
            suspicious = [l for l in proc.stdout.splitlines() if len(l) > 30 and
                          any(c.isalpha() for c in l) and any(c.isdigit() for c in l)]
            if len(suspicious) > 10:
                results.append(f"strings: {len(suspicious)} long alphanumeric strings (potential hidden data)")
        except FileNotFoundError:
            pass
        if results:
            return f"Steganography analysis for {path}:\n" + "\n".join(results)
        return f"No steganography detected in {path}"
    except Exception as e:
        return f"Stego detection failed: {e}"


@tool()
def extract_hidden_data(path: str, passphrase: str = "") -> str:
    """Extract hidden data from a file using steghide."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        out_file = f"/tmp/stego_extracted_{p.stem}"
        cmd = ["steghide", "extract", "-sf", str(p), "-xf", out_file]
        if passphrase:
            cmd.extend(["-p", passphrase])
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # noqa: S603, S607
        if proc.returncode == 0:
            extracted = Path(out_file)
            if extracted.exists():
                content = extracted.read_text(errors="replace")[:2000]
                return f"Extracted {extracted.stat().st_size} bytes from {path}:\n{content}"
            return f"Extraction succeeded but output file not found at {out_file}"
        return f"Extraction failed: {proc.stderr.strip()[:300]}"
    except FileNotFoundError:
        return "steghide not available"
    except Exception as e:
        return f"Extraction failed: {e}"


@tool()
def embed_payload(carrier_path: str, payload_path: str, passphrase: str = "secret") -> str:
    """Embed a payload file into a carrier image using steghide."""
    try:
        carrier = Path(carrier_path)
        payload = Path(payload_path)
        if not carrier.exists():
            return f"Carrier file not found: {carrier_path}"
        if not payload.exists():
            return f"Payload file not found: {payload_path}"
        proc = subprocess.run(  # noqa: S603
            ["steghide", "embed", "-cf", str(carrier), "-ef", str(payload), "-p", passphrase],  # noqa: S607
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            new_size = carrier.stat().st_size
            return f"Embedded {payload.name} ({payload.stat().st_size}b) into {carrier.name} ({new_size}b)"
        return f"Embedding failed: {proc.stderr.strip()[:300]}"
    except FileNotFoundError:
        return "steghide not available"
    except Exception as e:
        return f"Embedding failed: {e}"
