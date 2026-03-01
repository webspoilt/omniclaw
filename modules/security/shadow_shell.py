#!/usr/bin/env python3
"""
shadow_shell.py — Sandboxed honeypot terminal.

Listens on port 2222, presents a fake shell to attackers,
logs every command, and uses an LLM to classify attacker intent.
"""

import socket
import threading
import logging
import time
import json
from pathlib import Path
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from core.kill_switch import check_kill_switch
    from core.resource_utils import resource_check
except ImportError:
    def check_kill_switch(): pass
    def resource_check(**kw): return True

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ShadowShell")


class ShadowShell:
    """Honeypot that logs attacker sessions and analyzes intent with LLM."""

    BANNER = (
        b"Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\n"
        b"Last login: Mon Feb 28 03:14:07 2026 from 10.0.0.1\n\n"
    )
    FAKE_FS = {
        "ls": "Desktop  Documents  Downloads  .bashrc  .ssh\n",
        "ls -la": "total 28\ndrwxr-xr-x 5 root root 4096 Feb 28 03:14 .\n",
        "whoami": "root\n",
        "id": "uid=0(root) gid=0(root) groups=0(root)\n",
        "pwd": "/root\n",
        "uname -a": "Linux prod-web01 5.15.0-91-generic x86_64 GNU/Linux\n",
        "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33::/var/www\n",
        "ifconfig": "eth0: inet 192.168.1.100  netmask 255.255.255.0\n",
        "cat /etc/shadow": "Permission denied\n",
    }

    def __init__(self, port: int = 2222, llm_model: str = "llama3:latest"):
        self.port = port
        self.llm_model = llm_model
        self.ollama_url = "http://localhost:11434"
        self.log_dir = Path("./logs/honeypot")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        check_kill_switch()
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", self.port))
        srv.listen(5)
        logger.info(f"Shadow shell listening on :{self.port}")

        while True:
            client, addr = srv.accept()
            logger.info(f"Attacker connected: {addr}")
            threading.Thread(target=self._session, args=(client, addr),
                             daemon=True).start()

    def _session(self, client: socket.socket, addr):
        session_cmds = []
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            client.sendall(self.BANNER)
            client.sendall(b"root@prod-web01:~# ")
            buf = b""
            while True:
                data = client.recv(1024)
                if not data:
                    break
                buf += data
                if b"\n" in data:
                    cmd = buf.decode("utf-8", errors="ignore").strip()
                    buf = b""
                    logger.info(f"[{addr[0]}] $ {cmd}")
                    session_cmds.append(cmd)

                    if cmd in ("exit", "logout", "quit"):
                        client.sendall(b"logout\n")
                        break

                    resp = self.FAKE_FS.get(cmd, f"bash: {cmd}: command not found\n")
                    client.sendall(resp.encode())
                    client.sendall(b"root@prod-web01:~# ")
        except Exception as e:
            logger.error(f"Session error: {e}")
        finally:
            client.close()

        # Save session log
        log_file = self.log_dir / f"session_{addr[0]}_{ts}.json"
        log_file.write_text(json.dumps({
            "ip": addr[0], "port": addr[1],
            "timestamp": ts, "commands": session_cmds,
        }, indent=2))

        # Analyze intent
        if session_cmds:
            self._analyze(addr[0], session_cmds)

    def _analyze(self, ip: str, cmds: list):
        if not HAS_REQUESTS:
            return
        prompt = (
            "Analyze these commands from a honeypot session. Classify "
            "attacker intent (recon, privesc, exfiltration, crypto-mining, "
            "botnet) and threat level (LOW/MEDIUM/HIGH).\n\n"
            f"IP: {ip}\nCommands:\n" + "\n".join(cmds)
        )
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.llm_model, "prompt": prompt, "stream": False},
                timeout=30,
            )
            analysis = r.json().get("response", "")
            logger.info(f"Intent analysis [{ip}]: {analysis}")
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")


def main():
    if not resource_check(is_mobile=False):
        logger.warning("Insufficient resources")
        return
    ShadowShell().start()


if __name__ == "__main__":
    main()
