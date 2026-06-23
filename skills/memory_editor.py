# ruff: noqa: S108, UP031
import os

from core.skills.registry import tool


@tool()
def read_process_memory(pid: int, address: int, size: int = 256) -> str:
    """Read memory from a process at a given virtual address via /proc/pid/mem."""
    try:
        mem_path = "/proc/%d/mem" % pid
        if not os.path.exists(mem_path):
            maps_path = "/proc/%d/maps" % pid
            if not os.path.exists(maps_path):
                return "Process %d not found" % pid
            return "/proc/%d/mem not accessible (try root)" % pid
        with open(mem_path, "rb") as f:
            f.seek(address)
            data = f.read(min(size, 4096))
        hex_repr = " ".join(f"{b:02x}" for b in data[:64])
        ascii_repr = "".join(chr(b) if 32 <= b < 127 else "." for b in data[:128])
        return "Hex (%d bytes):\n%s\n\nASCII:\n%s" % (len(data), hex_repr, ascii_repr)
    except PermissionError:
        return "Permission denied reading PID %d memory (need root or same user)" % pid
    except Exception as e:
        return f"Error: {e}"


@tool()
def write_process_memory(pid: int, address: int, data_hex: str) -> str:
    """Write hex-encoded bytes to a process via /proc/pid/mem."""
    try:
        data = bytes.fromhex(data_hex)
        mem_path = "/proc/%d/mem" % pid
        if not os.path.exists(mem_path):
            return "/proc/%d/mem not accessible" % pid
        with open(mem_path, "r+b") as f:
            f.seek(address)
            written = f.write(data)
        return "Wrote %d bytes to PID %d at address 0x%x" % (written, pid, address)
    except PermissionError:
        return "Permission denied (need root or same user)"
    except ValueError:
        return "Invalid hex data provided"
    except Exception as e:
        return f"Error: {e}"


@tool()
def dump_heap(pid: int, output_path: str = "") -> str:
    """Dump the heap region of a process using /proc/pid/maps + /proc/pid/mem."""
    try:
        pid = int(pid)
        maps_path = "/proc/%d/maps" % pid
        if not os.path.exists(maps_path):
            return "Process %d not found" % pid
        heap_regions = []
        with open(maps_path) as f:
            for line in f:
                if "[heap]" in line:
                    parts = line.split()[0].split("-")
                    heap_regions.append((int(parts[0], 16), int(parts[1], 16)))
        if not heap_regions:
            return "No heap region found for PID %d" % pid
        out_path = "/tmp/heap_%d_%d.dump" % (pid, os.getpid())
        if output_path:
            out_path = output_path
        total = 0
        with open("/proc/%d/mem" % pid, "rb") as mem:
            with open(out_path, "wb") as out:
                for start, end in heap_regions:
                    size = min(end - start, 64 * 1024 * 1024)
                    mem.seek(start)
                    data = mem.read(size)
                    out.write(data)
                    total += len(data)
        return "Dumped %d bytes of heap from PID %d to %s" % (total, pid, out_path)
    except PermissionError:
        return "Permission denied (need root)"
    except Exception as e:
        return f"Error: {e}"
