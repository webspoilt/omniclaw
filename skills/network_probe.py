"""Network probing tools for external analysis. All actions are logged."""
from __future__ import annotations

from core.skills.registry import tool


@tool(
    name="http_get",
    description="Make an HTTP GET request to a URL. Returns response body (first 2000 chars).",
    parameters={
        "url": {"type": "string", "description": "Target URL"},
        "timeout_sec": {"type": "integer", "description": "Request timeout in seconds"},
    },
    required=["url"],
)
async def http_get(url: str, timeout_sec: int = 10) -> str:
    import requests
    try:
        resp = requests.get(url, timeout=timeout_sec, headers={"User-Agent": "OmniClaw/4.5"})
        return f"HTTP {resp.status_code} ({len(resp.content)} bytes)\n{resp.text[:2000]}"
    except Exception as e:
        return f"GET failed: {e}"


@tool(
    name="http_post",
    description="Make an HTTP POST request with a JSON body.",
    parameters={
        "url": {"type": "string", "description": "Target URL"},
        "body_json": {"type": "string", "description": "JSON body as a string"},
        "timeout_sec": {"type": "integer", "description": "Request timeout in seconds"},
    },
    required=["url"],
)
async def http_post(url: str, body_json: str = "{}", timeout_sec: int = 10) -> str:
    import json

    import requests
    try:
        body = json.loads(body_json)
        resp = requests.post(
            url, json=body, timeout=timeout_sec,
            headers={"User-Agent": "OmniClaw/4.5", "Content-Type": "application/json"},
        )
        return f"HTTP {resp.status_code} ({len(resp.content)} bytes)\n{resp.text[:2000]}"
    except Exception as e:
        return f"POST failed: {e}"


@tool(
    name="download_file",
    description="Download a file from a URL and save it to a local path.",
    parameters={
        "url": {"type": "string", "description": "File URL to download"},
        "save_path": {"type": "string", "description": "Local path to save the file"},
        "timeout_sec": {"type": "integer", "description": "Download timeout in seconds"},
    },
    required=["url", "save_path"],
)
async def download_file(url: str, save_path: str, timeout_sec: int = 30) -> str:
    from pathlib import Path

    import requests
    try:
        resp = requests.get(url, timeout=timeout_sec, stream=True)
        resp.raise_for_status()
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"Downloaded {len(resp.content)} bytes to {path}"
    except Exception as e:
        return f"Download failed: {e}"


@tool(
    name="dns_lookup",
    description="Resolve a hostname to IP addresses (A records).",
    parameters={
        "hostname": {"type": "string", "description": "Hostname to resolve"},
    },
    required=["hostname"],
)
async def dns_lookup(hostname: str) -> str:
    import socket
    try:
        results = socket.getaddrinfo(hostname, 0)
        ips = sorted(set(r[4][0] for r in results))
        return f"DNS records for {hostname}:\n" + "\n".join(ips)
    except Exception as e:
        return f"DNS lookup failed: {e}"


@tool(
    name="tcp_port_check",
    description="Check if a TCP port is open on a remote host.",
    parameters={
        "host": {"type": "string", "description": "Hostname or IP"},
        "port": {"type": "integer", "description": "TCP port number"},
        "timeout_sec": {"type": "number", "description": "Connection timeout in seconds"},
    },
    required=["host", "port"],
)
async def tcp_port_check(host: str, port: int, timeout_sec: float = 3.0) -> str:
    import socket
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


@tool(
    name="ping_host",
    description="Ping a host to check reachability. Sends 3 ICMP packets.",
    parameters={
        "host": {"type": "string", "description": "Hostname or IP to ping"},
    },
    required=["host"],
)
async def ping_host(host: str) -> str:
    import subprocess
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["ping", "-c", "3", "-W", "5", host],  # noqa: S607
            capture_output=True, text=True, timeout=20,
        )
        return proc.stdout[-1500:] or proc.stderr[-1500:]
    except FileNotFoundError:
        return "ping command not available on this system"
    except Exception as e:
        return f"Ping failed: {e}"


@tool(
    name="curl_request",
    description="Execute an arbitrary curl command with custom arguments.",
    parameters={
        "args": {"type": "string", "description": "Curl arguments, e.g. '-X POST -d \"key=val\" https://example.com'"},
        "timeout_sec": {"type": "integer", "description": "Timeout in seconds"},
    },
    required=["args"],
)
async def curl_request(args: str, timeout_sec: int = 30) -> str:
    import shlex
    import subprocess
    try:
        cmd = ["curl"] + shlex.split(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)  # noqa: S603,S607
        return f"Exit: {proc.returncode}\nstdout:\n{proc.stdout[:2000]}\nstderr:\n{proc.stderr[:1000]}"
    except FileNotFoundError:
        return "curl not available on this system"
    except Exception as e:
        return f"curl failed: {e}"
