"""Container escape detection: capability checking, cgroup analysis, host filesystem access."""
from __future__ import annotations

import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def check_container_caps() -> str:
    """Check Linux capabilities of the current process to detect container escape potential."""
    try:
        proc_caps = Path("/proc/self/status")
        if not proc_caps.exists():
            return "Cannot determine capabilities (not on Linux /proc)"
        status = proc_caps.read_text()
        lines = []
        for prefix in ["CapInh:", "CapPrm:", "CapEff:", "CapBnd:", "CapAmb:"]:
            for line in status.splitlines():
                if line.startswith(prefix):
                    lines.append(line.strip())
        cap_names = {
            0: "CAP_CHOWN", 1: "CAP_DAC_OVERRIDE", 2: "CAP_DAC_READ_SEARCH",
            3: "CAP_FOWNER", 4: "CAP_FSETID", 5: "CAP_KILL",
            6: "CAP_SETGID", 7: "CAP_SETUID", 8: "CAP_SETPCAP",
            9: "CAP_LINUX_IMMUTABLE", 10: "CAP_NET_BIND_SERVICE",
            11: "CAP_NET_BROADCAST", 12: "CAP_NET_ADMIN", 13: "CAP_NET_RAW",
            14: "CAP_IPC_LOCK", 15: "CAP_IPC_OWNER", 16: "CAP_SYS_MODULE",
            17: "CAP_SYS_RAWIO", 18: "CAP_SYS_CHROOT", 19: "CAP_SYS_PTRACE",
            20: "CAP_SYS_PACCT", 21: "CAP_SYS_ADMIN", 22: "CAP_SYS_BOOT",
            23: "CAP_SYS_NICE", 24: "CAP_SYS_RESOURCE", 25: "CAP_SYS_TIME",
            26: "CAP_SYS_TTY_CONFIG", 27: "CAP_MKNOD", 28: "CAP_LEASE",
            29: "CAP_AUDIT_WRITE", 30: "CAP_AUDIT_CONTROL", 31: "CAP_SETFCAP",
            32: "CAP_MAC_OVERRIDE", 33: "CAP_MAC_ADMIN", 34: "CAP_SYSLOG",
            35: "CAP_WAKE_ALARM", 36: "CAP_BLOCK_SUSPEND", 37: "CAP_AUDIT_READ",
        }
        dangerous_caps = [16, 17, 18, 19, 21, 24, 27, 32, 33]
        effective_hex = ""
        for ln in lines:
            if ln.startswith("CapEff:"):
                effective_hex = ln.split()[1]
        if effective_hex:
            effective_int = int(effective_hex, 16)
            dangerous_found = []
            for bit in dangerous_caps:
                if effective_int & (1 << bit):
                    dangerous_found.append(cap_names.get(bit, f"CAP_{bit}"))
            if dangerous_found:
                return f"Dangerous capabilities: {', '.join(dangerous_found)}\nCapabilities:\n" + "\n".join(lines)
            return "No dangerous capabilities found.\nCapabilities:\n" + "\n".join(lines)
        return "\n".join(lines)
    except Exception as e:
        return f"Capability check failed: {e}"


@tool()
def mount_host_fs(host_path: str = "/host", target_path: str = "") -> str:
    """Attempt to mount host filesystem if /dev devices or bind mounts are accessible."""
    try:
        target = target_path or f"/mnt/container_escape_{abs(hash(host_path)) % 10000}"
        Path(target).mkdir(parents=True, exist_ok=True)
        for device, fstype in [("/dev/sda1", "ext4"), ("/dev/vda1", "ext4"),
                                ("/dev/nvme0n1p1", "ext4"), ("/dev/mmcblk0p1", "ext4")]:
            dev = Path(device)
            if dev.exists():
                proc = subprocess.run(  # noqa: S603
                    ["mount", device, target],  # noqa: S607
                    capture_output=True, text=True, timeout=15,
                )
                if proc.returncode == 0:
                    files = list(Path(target).iterdir())[:20]
                    return f"Mounted {device} → {target}\nContents: {', '.join(f.name for f in files)}"
        return "No host devices accessible for mounting"
    except PermissionError:
        return "Permission denied — need root or CAP_SYS_ADMIN"
    except FileNotFoundError:
        return "mount not available"
    except Exception as e:
        return f"Mount attempt failed: {e}"


@tool()
def cgroup_release_agent() -> str:
    """Check for cgroup release_agent container escape vector."""
    try:
        cgroup_path = Path("/proc/1/cgroup")
        if not cgroup_path.exists():
            return "No cgroup info available"
        content = cgroup_path.read_text()
        if "docker" in content or "kubepods" in content or "lxc" in content:
            release_agent_paths = [
                Path("/sys/fs/cgroup/release_agent"),
                Path("/sys/fs/cgroup/memory/release_agent"),
            ]
            for ra in release_agent_paths:
                if ra.exists():
                    try:
                        ra_content = ra.read_text().strip()
                        if ra_content:
                            return f"Release agent found: {ra} = {ra_content}"
                    except PermissionError:
                        return f"Release agent at {ra} but not readable (need root)"
            return "In container but no release_agent found — standard Docker"
        return "Not running in a container (or cgroup format not recognized)"
    except Exception as e:
        return f"Cgroup check failed: {e}"
