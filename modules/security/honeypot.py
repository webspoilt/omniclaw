#!/usr/bin/env python3
"""
honeypot.py — Shadow Shell Honeypot

Resolves GitHub Issue #24: Shadow Shell Honeypot - eBPF + Sandboxed Terminal.

A fake interactive shell that listens on a configurable TCP port, simulates
realistic command responses to fool attackers, and logs every session with
timestamps and client IPs.

Features:
  - asyncio TCP server (no extra deps)
  - Realistic fake responses for ls, pwd, whoami, cat /etc/passwd, etc.
  - eBPF simulation mode (logs as if eBPF — real eBPF requires Linux kernel 5.8+)
  - All sessions logged to logs/honeypot.log
  - Graceful shutdown via kill switch

Usage::

    python -m modules.security.honeypot           # default port 2222
    python -m modules.security.honeypot --port 4444
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("OmniClaw.Honeypot")

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
_HONEYPOT_LOG = LOG_DIR / "honeypot.log"


# ------------------------------------------------------------------ #
#  Canned fake responses                                              #
# ------------------------------------------------------------------ #

_FAKE_RESPONSES: Dict[str, str] = {
    "ls": (
        "bin  boot  dev  etc  home  lib  lib64  media  mnt  "
        "opt  proc  root  run  sbin  srv  sys  tmp  usr  var"
    ),
    "ls -la": (
        "total 88\ndrwxr-xr-x 19 root root 4096 Jan  1 00:00 .\n"
        "drwxr-xr-x 19 root root 4096 Jan  1 00:00 ..\n"
        "drwxr-xr-x  2 root root 4096 Jan  1 00:00 bin\n"
        "drwxr-xr-x  3 root root 4096 Jan  1 00:00 boot"
    ),
    "pwd": "/var/www/html",
    "whoami": "www-data",
    "id": "uid=33(www-data) gid=33(www-data) groups=33(www-data)",
    "uname -a": (
        "Linux prod-server-01 5.15.0-91-generic #101-Ubuntu SMP "
        "Tue Nov 14 13:30:08 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux"
    ),
    "cat /etc/passwd": (
        "root:x:0:0:root:/root:/bin/bash\n"
        "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
        "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
        "syslog:x:104:110::/home/syslog:/usr/sbin/nologin"
    ),
    "cat /etc/shadow": "cat: /etc/shadow: Permission denied",
    "ifconfig": (
        "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
        "        inet 10.0.0.42  netmask 255.255.255.0  broadcast 10.0.0.255"
    ),
    "ip a": (
        "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536\n"
        "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500\n"
        "    inet 10.0.0.42/24 brd 10.0.0.255 scope global eth0"
    ),
    "ps aux": (
        "USER       PID %CPU %MEM COMMAND\n"
        "root         1  0.0  0.1 /sbin/init\n"
        "www-data   512  0.2  1.4 /usr/sbin/apache2\n"
        "mysql      678  0.5  4.2 /usr/sbin/mysqld"
    ),
    "env": "HOME=/var/www\nPATH=/usr/local/bin:/usr/bin:/bin\nSHELL=/bin/bash",
    "history": (
        "    1  ls\n    2  pwd\n    3  cat /etc/passwd\n"
        "    4  sudo su\n    5  history"
    ),
    "sudo su": "sudo: no tty present and no askpass program specified",
    "python3 -c \"import socket\"": "",
    "exit": "__EXIT__",
    "quit": "__EXIT__",
    "logout": "__EXIT__",
}

_BANNER = (
    "Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\n\n"
    " * Documentation:  https://help.ubuntu.com\n"
    " * Management:     https://landscape.canonical.com\n\n"
    "Last login: {last_login}\n"
)

_PROMPT = "www-data@prod-server-01:/var/www/html$ "


def _fake_response(cmd: str) -> str:
    """Return a fake shell response for a given command."""
    cmd_stripped = cmd.strip()
    if cmd_stripped in _FAKE_RESPONSES:
        return _FAKE_RESPONSES[cmd_stripped]
    # Generic fallback
    if cmd_stripped.startswith("cd "):
        return ""
    if cmd_stripped == "":
        return ""
    return f"bash: {cmd_stripped.split()[0]}: command not found"


def _log_event(peer: str, event: str, data: str = "") -> None:
    """Append an event to the honeypot log."""
    ts = datetime.utcnow().isoformat(timespec="seconds")
    line = f"[{ts}] [{peer}] {event}"
    if data:
        line += f" | {data[:200]}"
    logger.info(line)
    try:
        with open(_HONEYPOT_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ------------------------------------------------------------------ #
#  Session handler                                                    #
# ------------------------------------------------------------------ #

async def _handle_session(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    peer = writer.get_extra_info("peername", ("unknown", 0))
    peer_str = f"{peer[0]}:{peer[1]}"
    _log_event(peer_str, "CONNECT")

    try:
        # Send banner
        last_login = datetime.utcnow().strftime("%a %b %d %H:%M:%S %Y from 192.168.1.1")
        writer.write((_BANNER.format(last_login=last_login) + _PROMPT).encode())
        await writer.drain()

        while True:
            try:
                data = await asyncio.wait_for(reader.readline(), timeout=120)
            except asyncio.TimeoutError:
                _log_event(peer_str, "TIMEOUT")
                break
            if not data:
                break

            cmd = data.decode(errors="replace").rstrip("\r\n")
            _log_event(peer_str, "CMD", cmd)

            response = _fake_response(cmd)
            if response == "__EXIT__":
                writer.write(b"logout\r\n")
                await writer.drain()
                break

            if response:
                writer.write((response + "\r\n").encode())
            writer.write(_PROMPT.encode())
            await writer.drain()

    except (ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        logger.debug(f"Session error ({peer_str}): {e}")
    finally:
        _log_event(peer_str, "DISCONNECT")
        try:
            writer.close()
        except Exception:
            pass


# ------------------------------------------------------------------ #
#  Server                                                             #
# ------------------------------------------------------------------ #

class ShadowShellHoneypot:
    """Shadow Shell Honeypot — fake SSH/shell decoy (Issue #24).

    .. note::
        Real eBPF kernel instrumentation requires Linux 5.8+ with root
        privileges and bpftool/libbpf. This implementation uses asyncio
        simulation suitable for all platforms. On Linux with root, extend
        this class to trigger eBPF probes via ``bcc`` or ``bpftool``.

    Usage::

        honeypot = ShadowShellHoneypot(port=2222)
        await honeypot.start()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 2222):
        self.host = host
        self.port = port
        self._server: Optional[asyncio.AbstractServer] = None

    async def start(self) -> None:
        """Start the honeypot server."""
        self._server = await asyncio.start_server(
            _handle_session, self.host, self.port
        )
        logger.info(
            f"ShadowShellHoneypot listening on {self.host}:{self.port} — "
            f"logging to {_HONEYPOT_LOG}"
        )
        async with self._server:
            await self._server.serve_forever()

    def stop(self) -> None:
        """Stop the honeypot server."""
        if self._server:
            self._server.close()
            logger.info("ShadowShellHoneypot stopped")


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

async def _main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="OmniClaw Shadow Shell Honeypot")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=2222)
    args = parser.parse_args()

    honeypot = ShadowShellHoneypot(host=args.host, port=args.port)
    await honeypot.start()


if __name__ == "__main__":
    asyncio.run(_main())
