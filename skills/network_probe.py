# skills/network_probe.py
"""Network reconnaissance and download tools for the research agent."""
import shlex
import socket
import subprocess
from pathlib import Path

import requests

from core.skills.registry import tool


@tool()
def http_get(url: str, timeout_sec: int = 10) -> str:
    """Perform an HTTP GET request and return the response body (first 2000 chars)."""
    try:
        resp = requests.get(
            url,
            timeout=timeout_sec,
            headers={"User-Agent": "OmniClaw/4.5"},
        )
        return f"HTTP {resp.status_code} ({len(resp.content)} bytes)\n{resp.text[:2000]}"
    except Exception as e:
        return f"GET failed: {e}"


@tool()
def http_post(url: str, body: str, timeout_sec: int = 10) -> str:
    """Perform an HTTP POST request with a JSON body and return the response."""
    try:
        import json
        data = json.loads(body)
        resp = requests.post(
            url,
            json=data,
            timeout=timeout_sec,
            headers={"User-Agent": "OmniClaw/4.5", "Content-Type": "application/json"},
        )
        return f"HTTP {resp.status_code} ({len(resp.content)} bytes)\n{resp.text[:2000]}"
    except Exception as e:
        return f"POST failed: {e}"


@tool()
def download_file(url: str, save_path: str, timeout_sec: int = 30) -> str:
    """Download a file from a URL and save it to a local path."""
    try:
        resp = requests.get(
            url,
            stream=True,
            timeout=timeout_sec,
            headers={"User-Agent": "OmniClaw/4.5"},
        )
        resp.raise_for_status()
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        total_bytes = 0
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                total_bytes += len(chunk)
        return f"Downloaded {total_bytes} bytes to {path}"
    except Exception as e:
        return f"Download failed: {e}"


@tool()
def dns_lookup(hostname: str) -> str:
    """Resolve a hostname to IP addresses (A records)."""
    try:
        results = socket.getaddrinfo(hostname, 0)
        ips = sorted(set(r[4][0] for r in results))
        return f"DNS records for {hostname}:\n" + "\n".join(ips)
    except Exception as e:
        return f"DNS lookup failed: {e}"


@tool()
def tcp_port_check(host: str, port: int, timeout_sec: float = 3.0) -> str:
    """Check if a TCP port is open on a remote host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout_sec)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return f"Port {port} on {host} is OPEN"
        return f"Port {port} on {host} is CLOSED (code {result})"
    except Exception as e:
        return f"Port check failed: {e}"


@tool()
def ping_host(host: str) -> str:
    """Ping a host to check reachability. Sends 3 ICMP packets."""
    try:
        proc = subprocess.run(  # noqa: S603
            ["ping", "-c", "3", "-W", "5", host],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=20,
        )
        return proc.stdout[-1500:] or proc.stderr[-1500:]
    except FileNotFoundError:
        return "ping command not available on this system"
    except Exception as e:
        return f"Ping failed: {e}"


@tool()
def curl_request(args: str, timeout_sec: int = 30) -> str:
    """Execute an arbitrary curl command with custom arguments.
    Example args: '-X POST -d \"key=val\" https://example.com'
    """
    try:
        cmd = ["curl"] + shlex.split(args)
        proc = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return (
            f"Exit: {proc.returncode}\n"
            f"stdout:\n{proc.stdout[:2000]}\n"
            f"stderr:\n{proc.stderr[:1000]}"
        )
    except FileNotFoundError:
        return "curl not available on this system"
    except Exception as e:
        return f"curl failed: {e}"
