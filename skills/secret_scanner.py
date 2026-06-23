"""Credential and secret scanning across files and process memory."""
from __future__ import annotations

import os
import re
from pathlib import Path

from core.skills.registry import tool

_SECRET_PATTERNS: list[tuple[str, str, str]] = [
    ("AWS Access Key", r"(?i)AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key", r"(?i)(?<![a-zA-Z0-9/+])[a-zA-Z0-9/+=]{40}(?![a-zA-Z0-9/+])"),
    ("GitHub Token", r"(?i)gh[pousr]_[a-zA-Z0-9]{36,251}"),
    ("GitLab Token", r"(?i)glpat-[a-zA-Z0-9\-_]{20,30}"),
    ("Slack Token", r"(?i)xox[baprs]-[0-9]{10,13}-[a-zA-Z0-9\-]{20,40}"),
    ("Generic API Key", r"(?i)(api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,64}"),
    ("Bearer Token", r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,250}"),
    ("JWT Token", r"eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}"),
    ("Password Assignment", r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    ("Connection String", r"(?i)(postgres|mysql|mongodb|redis)://[a-zA-Z0-9_\-]+:[^@]+@"),
    ("Private Key", r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"),
    ("SSH Key", r"(?i)ssh-(rsa|dss|ed25519|ecdsa)\s+[a-zA-Z0-9+/=]{100,}"),
    ("Heroku API Key", r"(?i)heroku[a-zA-Z0-9_\-]{10,}:[a-zA-Z0-9_\-]{30,}"),
    ("Google OAuth", r"(?i)[0-9]+-[a-zA-Z0-9_]{32,}\.apps\.googleusercontent\.com"),
    ("Slack Webhook", r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24,}"),
]


def _scan_content(content: str, source_label: str) -> list[dict[str, str]]:
    findings = []
    lines = content.splitlines()
    for name, pattern in _SECRET_PATTERNS:
        for lineno, line in enumerate(lines, 1):
            if re.search(pattern, line):
                masked = re.sub(pattern, "***REDACTED***", line).strip()
                findings.append({
                    "type": name,
                    "file": source_label,
                    "line": str(lineno),
                    "match": masked[:120],
                })
                break
    return findings


@tool()
def scan_file_for_secrets(path: str) -> str:
    """Scan a single file for credentials, API keys, tokens, and other secrets."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = p.read_bytes().decode("utf-8", errors="replace")
        findings = _scan_content(content, str(p))
        if not findings:
            return f"No secrets found in {path}"
        lines = [f"Found {len(findings)} potential secrets in {path}:"]
        for f in findings:
            lines.append(f"  [{f['type']}] line {f['line']}: {f['match']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Secret scan failed: {e}"


@tool()
def scan_directory_for_secrets(
    path: str,
    max_files: int = 200,
    skip_extensions: str = ".pyc,.o,.so,.dll,.exe,.jpg,.png,.mp3,.mp4,.zip,.tar,.gz",
) -> str:
    """Recursively scan a directory for secrets across text files."""
    try:
        base = Path(path)
        if not base.exists():
            return f"Directory not found: {path}"
        if not base.is_dir():
            return scan_file_for_secrets(path)
        skip = {ext.lower() for ext in skip_extensions.split(",") if ext.strip()}
        text_exts = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
            ".toml", ".ini", ".cfg", ".conf", ".env", ".sh", ".bash", ".zsh",
            ".ps1", ".bat", ".cmd", ".xml", ".html", ".css", ".scss", ".less",
            ".md", ".rst", ".txt", ".csv", ".sql", ".rb", ".go", ".rs", ".java",
            ".c", ".cpp", ".h", ".hpp", ".php", ".swift", ".kt", ".scala",
            ".terraform", ".tf", ".tfvars", ".dockerfile", ".nginx", ".pl",
        }
        findings: list[dict[str, str]] = []
        files_scanned = 0
        for fpath in base.rglob("*"):
            if not fpath.is_file():
                continue
            if fpath.suffix.lower() in skip:
                continue
            if fpath.suffix.lower() not in text_exts:
                continue
            if files_scanned >= max_files:
                break
            files_scanned += 1
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                findings.extend(_scan_content(content, str(fpath)))
            except Exception:  # noqa: S110, S112
                continue
        if not findings:
            return f"No secrets found in {files_scanned} files under {path}"
        grouped: dict[str, list[dict[str, str]]] = {}
        for f in findings:
            grouped.setdefault(f["type"], []).append(f)
        lines = [
            f"Scanned {files_scanned} files, found {len(findings)} potential secrets:"
        ]
        for secret_type, items in sorted(grouped.items()):
            lines.append(f"\n  {secret_type} ({len(items)}):")
            for item in items[:5]:
                lines.append(f"    {item['file']}:{item['line']} -> {item['match']}")
            if len(items) > 5:
                lines.append(f"    ... and {len(items) - 5} more")
        return "\n".join(lines)
    except Exception as e:
        return f"Directory scan failed: {e}"


@tool()
def scan_process_memory(pid: int, max_bytes: int = 65536) -> str:
    """Scan a process memory map for secrets by reading readable regions."""
    try:
        maps_path = f"/proc/{pid}/maps"
        mem_path = f"/proc/{pid}/mem"
        if not os.path.exists(maps_path):
            return f"Process {pid} not found or not accessible"
        regions: list[tuple[int, int, str]] = []
        with open(maps_path) as f:
            for line in f:
                parts = line.split()
                if len(parts) < 2:
                    continue
                perms = parts[1]
                if "r" not in perms:
                    continue
                addrs = parts[0].split("-")
                if len(addrs) != 2:
                    continue
                start = int(addrs[0], 16)
                end = int(addrs[1], 16)
                label = parts[-1] if len(parts) > 5 else ""
                regions.append((start, end, label))
        total_read = 0
        all_content = ""
        with open(mem_path, "rb") as mem:
            for start, end, label in regions:
                size = min(end - start, max_bytes // max(len(regions), 1))
                try:
                    mem.seek(start)
                    chunk = mem.read(size)
                    total_read += len(chunk)
                    all_content += chunk.decode("utf-8", errors="replace")
                except Exception:  # noqa: S110, S112
                    continue
                if total_read >= max_bytes:
                    break
        # Deduplicate by splitting and re-uniquing lines to avoid repeated noise
        unique_lines = set(all_content.splitlines())
        findings = []
        for line in unique_lines:
            for name, pattern in _SECRET_PATTERNS:
                if re.search(pattern, line):
                    masked = re.sub(pattern, "***REDACTED***", line)
                    findings.append(f"  [{name}] {masked[:120]}")
                    break
        if not findings:
            return f"Scanned {total_read} bytes from PID {pid} memory — no secrets found"
        found_str = "\n".join(findings[:50])
        return f"Scanned {total_read} bytes from PID {pid} memory — found {len(findings)} secrets:\n{found_str}"
    except PermissionError:
        return f"Permission denied reading PID {pid} memory (need root or same user)"
    except Exception as e:
        return f"Memory scan failed: {e}"
