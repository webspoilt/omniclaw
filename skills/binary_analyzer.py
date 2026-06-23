"""Binary analysis tools: ELF parsing, strings extraction, packing detection, shared libs."""
from __future__ import annotations

import os
import re
import struct
import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def analyze_elf(path: str) -> str:
    """Parse ELF headers and return architecture, entry point, sections, and segments."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        data = p.read_bytes()
        if len(data) < 64:
            return f"File too small to be ELF: {len(data)} bytes"
        if data[:4] != b"\x7fELF":
            return "Not a valid ELF file"
        elf_class = data[4]
        ei_data = data[5]
        bits = 64 if elf_class == 2 else 32
        little = "Little Endian" if ei_data == 1 else "Big Endian"
        endian = "<" if ei_data == 1 else ">"
        e_type_map = {0: "NONE", 1: "REL", 2: "EXEC", 3: "DYN", 4: "CORE"}
        e_machine_map = {
            0x02: "SPARC", 0x03: "x86", 0x08: "MIPS", 0x14: "PowerPC",
            0x16: "S390", 0x28: "ARM", 0x3E: "x86_64", 0xB7: "AArch64",
            0xF3: "RISC-V",
        }
        if bits == 64:
            ehdr = struct.unpack_from(endian + "16sHHIQQQIHHHHHH", data, 0)
            e_type = ehdr[1]
            e_machine = ehdr[2]
            e_entry = ehdr[4]
            e_phoff = ehdr[5]
            e_shoff = ehdr[6]
            e_phnum = ehdr[9]
            e_shnum = ehdr[11]
        else:
            ehdr = struct.unpack_from(endian + "16sHHI IIIIHHHH", data, 0)
            e_type = ehdr[1]
            e_machine = ehdr[2]
            e_entry = ehdr[4]
            e_phoff = ehdr[5]
            e_shoff = ehdr[6]
            e_phnum = ehdr[9]
            e_shnum = ehdr[11]
        lines = [
            f"ELF {bits}-bit {little}",
            f"Type: {e_type_map.get(e_type, f'Unknown ({e_type})')}",
            f"Machine: {e_machine_map.get(e_machine, f'Unknown (0x{e_machine:x})')}",
            f"Entry point: 0x{e_entry:x}",
            f"Program headers: {e_phnum} (offset 0x{e_phoff:x})",
            f"Section headers: {e_shnum} (offset 0x{e_shoff:x})",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"ELF analysis failed: {e}"


@tool()
def extract_strings(
    path: str,
    min_length: int = 4,
    entropy_threshold: float = 0.0,
    max_results: int = 100,
) -> str:
    """Extract printable strings from a file, optionally filtering by entropy."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        data = p.read_bytes()
        pattern = re.compile(rb"[ -~]{%d,}" % min_length)
        matches = pattern.findall(data)
        results = []
        for m in matches:
            s = m.decode("ascii", errors="replace")
            if entropy_threshold > 0.0:
                if len(s) < 2:
                    continue
                freq = {}
                for c in s:
                    freq[c] = freq.get(c, 0) + 1
                ent = -sum((c / len(s)) * __import__("math").log2(c / len(s)) for c in freq.values())
                if ent < entropy_threshold:
                    continue
            results.append(s)
            if len(results) >= max_results:
                break
        return f"Extracted {len(results)} strings from {path}:\n" + "\n".join(results[:max_results])
    except Exception as e:
        return f"String extraction failed: {e}"


@tool()
def detect_packed(path: str) -> str:
    """Detect if a binary is packed/obfuscated using entropy and section heuristics."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        data = p.read_bytes()
        if data[:4] != b"\x7fELF":
            return "Not a valid ELF file"
        total_bytes = len(data)
        if total_bytes < 4096:
            return "File too small for meaningful analysis"
        entropies = []
        chunk_size = 4096
        for i in range(0, total_bytes, chunk_size):
            chunk = data[i : i + chunk_size]
            if len(chunk) < 64:
                continue
            freq = {}
            for b in chunk:
                freq[b] = freq.get(b, 0) + 1
            ent = -sum(
                (c / len(chunk)) * __import__("math").log2(c / len(chunk))
                for c in freq.values()
            )
            entropies.append(ent)
        avg_entropy = sum(entropies) / len(entropies) if entropies else 0.0
        max_entropy = max(entropies) if entropies else 0.0
        high_entropy_chunks = sum(1 for e in entropies if e > 7.0)
        section_count = 0
        if total_bytes > 64:
            ei_class = data[4]
            bits = 64 if ei_class == 2 else 32
            ei_data = data[5]
            endian = "<" if ei_data == 1 else ">"
            if bits == 64:
                e_shnum = struct.unpack_from(endian + "H", data, 0x3C)[0]
            else:
                e_shnum = struct.unpack_from(endian + "H", data, 0x30)[0]
            section_count = e_shnum
        indicators = []
        if avg_entropy > 6.5:
            indicators.append(f"High average entropy ({avg_entropy:.2f})")
        if max_entropy > 7.5:
            indicators.append(f"Very high max entropy ({max_entropy:.2f})")
        if high_entropy_chunks > len(entropies) * 0.3:
            indicators.append(f"{high_entropy_chunks}/{len(entropies)} chunks above 7.0 entropy")
        if section_count == 0:
            indicators.append("No section headers (stripped)")
        if section_count < 5 and section_count > 0:
            indicators.append(f"Very few sections ({section_count})")
        if not indicators:
            return f"Binary appears normal (avg entropy {avg_entropy:.2f}, {section_count} sections)"
        return "PACKING INDICATORS:\n" + "\n".join(indicators)
    except Exception as e:
        return f"Packing detection failed: {e}"


@tool()
def shared_libraries(path: str) -> str:
    """List shared library dependencies of a binary using readelf or ldd."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        data = p.read_bytes()
        if data[:4] != b"\x7fELF":
            return "Not a valid ELF file"
        if os.name == "nt":
            return "Shared library analysis not supported on Windows"
        proc = subprocess.run(  # noqa: S603
            ["readelf", "-d", str(p)],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            proc = subprocess.run(  # noqa: S603
                ["ldd", str(p)],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode == 0:
                return proc.stdout.strip()
            return f"readelf/ldd not available: {proc.stderr.strip()[:200]}"
        needed = []
        for line in proc.stdout.splitlines():
            if "NEEDED" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "NEEDED" and i + 1 < len(parts):
                        needed.append(parts[i + 1].strip("[]"))
        if needed:
            return f"Shared library dependencies ({len(needed)}):\n" + "\n".join(needed)
        return "No shared library dependencies (statically linked)"
    except FileNotFoundError:
        paths_result = subprocess.run(
            ["which", "readelf", "ldd"],  # noqa: S603, S607
            capture_output=True,
            text=True,
            timeout=10,
        )
        found = [x for x in paths_result.stdout.splitlines() if x.strip()]
        if not found:
            return "readelf/ldd not available on this system"
        return f"Tool error with {found}"
    except Exception as e:
        return f"Shared library analysis failed: {e}"
