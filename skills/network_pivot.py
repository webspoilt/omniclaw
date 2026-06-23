# ruff: noqa: S104
"""Network pivoting: proxy setup, tunneling, reverse connections for lateral movement."""
from __future__ import annotations

import subprocess

from core.skills.registry import tool


@tool()
def start_proxy(listen_port: int = 9050, proxy_type: str = "socks5") -> str:
    """Start a SOCKS5 or HTTP proxy on the specified port."""
    try:
        if proxy_type == "socks5":
            cmd = ["socat", f"TCP-LISTEN:{listen_port},reuseaddr,fork", "SOCKS4A:localhost:,,"]
            proc = subprocess.Popen(cmd, start_new_session=True)  # noqa: S603, S607
            return f"SOCKS5 proxy started on port {listen_port} (PID {proc.pid})"
        elif proxy_type == "http":
            try:
                import http.server
                import socketserver
                handler = http.server.SimpleHTTPRequestHandler
                httpd = socketserver.TCPServer(("0.0.0.0", listen_port), handler)
                import threading
                t = threading.Thread(target=httpd.serve_forever, daemon=True)
                t.start()
                return f"HTTP proxy started on port {listen_port}"
            except Exception as e:
                return f"HTTP proxy failed: {e}"
        else:
            return f"Unsupported proxy type: {proxy_type}. Use socks5 or http"
    except FileNotFoundError:
        return "socat not available. Install: apt install socat"
    except Exception as e:
        return f"Proxy start failed: {e}"


@tool()
def tunnel_connection(target_host: str, target_port: int, listen_port: int = 8888) -> str:
    """Create a tunnel forwarding a local port to a remote target via socat or ssh."""
    try:
        try:
            cmd = ["socat", f"TCP-LISTEN:{listen_port},reuseaddr,fork", f"TCP:{target_host}:{target_port}"]
            proc = subprocess.Popen(cmd, start_new_session=True)  # noqa: S603, S607
            return f"Tunnel: localhost:{listen_port} → {target_host}:{target_port} (PID {proc.pid})"
        except FileNotFoundError:
            pass
        cmd = ["ssh", "-L", f"{listen_port}:{target_host}:{target_port}", "-N", "-f", target_host]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)  # noqa: S603, S607
        if proc.returncode == 0:
            return f"SSH tunnel: localhost:{listen_port} → {target_host}:{target_port}"
        return f"SSH tunnel failed: {proc.stderr.strip()[:300]}"
    except Exception as e:
        return f"Tunnel creation failed: {e}"


@tool()
def pivot_through(target: str, command: str) -> str:
    """Execute a command through a SOCKS proxy or tunnel using proxychains."""
    try:
        cmd = ["proxychains4", "-q"] + command.split()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # noqa: S603, S607
        if proc.returncode == 0:
            return f"Pivot command executed via {target}:\n{proc.stdout[-2000:]}"
        return f"Pivot command failed (exit {proc.returncode}):\n{proc.stderr[-500:]}"
    except FileNotFoundError:
        return "proxychains4 not available. Install: apt install proxychains4"
    except Exception as e:
        return f"Pivot failed: {e}"
