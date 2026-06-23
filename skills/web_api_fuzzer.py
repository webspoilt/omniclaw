"""Web API fuzzing: endpoint discovery, parameter injection, response analysis."""
from __future__ import annotations

import json as jsonlib
from typing import Any

import requests

from core.skills.registry import tool

_COMMON_ENDPOINTS: list[str] = [
    "api", "api/v1", "api/v2", "graphql", "rest", "admin", "login",
    "signup", "register", "auth", "token", "oauth", "callback",
    "user", "users", "profile", "account", "settings", "config",
    "health", "healthcheck", "status", "metrics", "info", "version",
    "search", "query", "upload", "download", "export", "import",
    "webhook", "webhooks", "callback", "hook", "notify",
    "debug", "test", "dev", "staging", "internal", "private",
    ".env", ".git/config", "swagger.json", "openapi.json",
    "robots.txt", "sitemap.xml", "crossdomain.xml",
]

_FUZZ_PAYLOADS: list[str] = [
    "", "'", "\"", "`", ";", "||", "&&", "|",
    "' OR '1'='1", "\" OR \"1\"=\"1",
    "admin' --", "admin\" --",
    "<script>alert(1)</script>",
    "{{7*7}}", "${7*7}",
    "../../../etc/passwd",
    "..\\..\\..\\windows\\win.ini",
    "%00", "null", "undefined", "NaN",
    "-1", "0", "1e308", "1e-308",
    "../", "..\\",
]

_STATUS_CATEGORIES: dict[str, list[int]] = {
    "success": [200, 201, 204],
    "redirect": [301, 302, 303, 307, 308],
    "client_error": [400, 401, 403, 404, 405, 409, 422, 429],
    "server_error": [500, 502, 503, 504],
}


def _classify_status(code: int) -> str:
    for category, codes in _STATUS_CATEGORIES.items():
        if code in codes:
            return category
    if 200 <= code < 300:
        return "success"
    if 300 <= code < 400:
        return "redirect"
    if 400 <= code < 500:
        return "client_error"
    if 500 <= code < 600:
        return "server_error"
    return f"other ({code})"


@tool()
def discover_endpoints(
    base_url: str,
    custom_wordlist: str = "",
    timeout_sec: int = 5,
) -> str:
    """Probe common API endpoint paths on a base URL to discover hidden endpoints."""
    try:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        base_url = base_url.rstrip("/")
        endpoints = _COMMON_ENDPOINTS.copy()
        if custom_wordlist.strip():
            endpoints.extend(
                w.strip() for w in custom_wordlist.split(",") if w.strip()
            )
        found: list[tuple[int, str, str]] = []
        not_found = 0
        errors = 0
        for ep in endpoints:
            url = f"{base_url}/{ep}"
            try:
                resp = requests.get(
                    url,
                    timeout=timeout_sec,
                    headers={"User-Agent": "OmniClaw/4.5"},
                    allow_redirects=False,
                )
                cat = _classify_status(resp.status_code)
                if cat not in ("client_error", "redirect"):
                    found.append((resp.status_code, ep, f"{len(resp.content)}b"))
                else:
                    not_found += 1
            except requests.exceptions.Timeout:
                errors += 1
            except Exception:
                errors += 1
        if not found:
            return f"No endpoints discovered at {base_url} ({not_found} not found, {errors} errors)"
        lines = [f"Discovered {len(found)} endpoints at {base_url}:"]
        for code, ep, size in sorted(found):
            lines.append(f"  {code} {ep} ({size})")
        lines.append(f"  ({not_found} not found, {errors} errors)")
        return "\n".join(lines)
    except requests.exceptions.ConnectionError as e:
        return f"Connection failed: {e}"
    except Exception as e:
        return f"Endpoint discovery failed: {e}"


@tool()
def fuzz_parameter(
    base_url: str,
    param_name: str,
    method: str = "GET",
    custom_payloads: str = "",
    timeout_sec: int = 5,
) -> str:
    """Inject fuzz payloads into a URL parameter and analyze responses."""
    try:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        payloads = _FUZZ_PAYLOADS.copy()
        if custom_payloads.strip():
            payloads.extend(p.strip() for p in custom_payloads.split(",") if p.strip())
        results: list[dict[str, Any]] = []
        method_upper = method.upper()
        for payload in payloads:
            url = f"{base_url}?{param_name}={requests.utils.quote(payload)}"
            try:
                if method_upper == "GET":
                    resp = requests.get(
                        url,
                        timeout=timeout_sec,
                        headers={"User-Agent": "OmniClaw/4.5"},
                        allow_redirects=False,
                    )
                else:
                    resp = requests.post(
                        url,
                        timeout=timeout_sec,
                        headers={"User-Agent": "OmniClaw/4.5"},
                        allow_redirects=False,
                    )
                results.append({
                    "payload": payload[:80],
                    "code": resp.status_code,
                    "size": len(resp.content),
                    "time": resp.elapsed.total_seconds(),
                    "category": _classify_status(resp.status_code),
                })
            except Exception:
                results.append({
                    "payload": payload[:80],
                    "code": 0,
                    "size": 0,
                    "time": 0.0,
                    "category": "error",
                })
        interesting = [r for r in results if r["code"] in (200, 201, 500, 502, 503) or r["time"] > 2.0]
        lines = [f"Fuzzed {len(payloads)} payloads on ?{param_name}= ({method_upper})"]
        if interesting:
            lines.append(f"Interesting results ({len(interesting)}):")
            for r in interesting[:20]:
                lines.append(
                    f"  {r['code']} | {r['size']:>6}b | {r['time']:.2f}s | payload: {r['payload']}"
                )
        status_counts: dict[str, int] = {}
        for r in results:
            status_counts[r["category"]] = status_counts.get(r["category"], 0) + 1
        lines.append("Status summary: " + ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items())))
        return "\n".join(lines)
    except requests.exceptions.ConnectionError as e:
        return f"Connection failed: {e}"
    except Exception as e:
        return f"Parameter fuzzing failed: {e}"


@tool()
def fuzz_json_field(
    base_url: str,
    field_name: str,
    custom_payloads: str = "",
    timeout_sec: int = 5,
) -> str:
    """Inject fuzz payloads into a JSON API field."""
    try:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        payloads = _FUZZ_PAYLOADS.copy()
        if custom_payloads.strip():
            payloads.extend(p.strip() for p in custom_payloads.split(",") if p.strip())
        results: list[dict[str, Any]] = []
        for payload in payloads:
            try:
                body = {field_name: payload}
                resp = requests.post(
                    base_url,
                    json=body,
                    timeout=timeout_sec,
                    headers={"User-Agent": "OmniClaw/4.5"},
                    allow_redirects=False,
                )
                results.append({
                    "payload": payload[:80],
                    "code": resp.status_code,
                    "size": len(resp.content),
                    "time": resp.elapsed.total_seconds(),
                    "category": _classify_status(resp.status_code),
                })
            except Exception:
                results.append({
                    "payload": payload[:80],
                    "code": 0,
                    "size": 0,
                    "time": 0.0,
                    "category": "error",
                })
        interesting = [r for r in results if r["code"] in (200, 201, 500, 502, 503) or r["time"] > 2.0]
        lines = [f"Fuzzed {len(payloads)} payloads on JSON field '{field_name}'"]
        if interesting:
            lines.append(f"Interesting results ({len(interesting)}):")
            for r in interesting[:20]:
                lines.append(
                    f"  {r['code']} | {r['size']:>6}b | {r['time']:.2f}s | payload: {r['payload']}"
                )
        status_counts: dict[str, int] = {}
        for r in results:
            status_counts[r["category"]] = status_counts.get(r["category"], 0) + 1
        lines.append("Status summary: " + ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items())))
        return "\n".join(lines)
    except requests.exceptions.ConnectionError as e:
        return f"Connection failed: {e}"
    except Exception as e:
        return f"JSON field fuzzing failed: {e}"


@tool()
def analyze_response(responses_json: str) -> str:
    """Analyze a batch of HTTP responses (JSON array) and produce a summary report."""
    try:
        data = jsonlib.loads(responses_json)
        if not isinstance(data, list):
            return "Input must be a JSON array of response objects"
        total = len(data)
        codes: dict[int, int] = {}
        sizes: list[int] = []
        times: list[float] = []
        interesting: list[dict[str, Any]] = []
        for item in data:
            code = item.get("code", 0)
            codes[code] = codes.get(code, 0) + 1
            sizes.append(item.get("size", 0))
            times.append(item.get("time", 0.0))
            if code in (200, 201, 500, 502, 503) or item.get("time", 0.0) > 2.0:
                interesting.append(item)
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        avg_time = sum(times) / len(times) if times else 0
        lines = [
            f"Response analysis for {total} requests:",
            f"Status codes: {dict(sorted(codes.items()))}",
        ]
        if interesting:
            lines.append(f"Interesting entries ({len(interesting)}):")
            for item in interesting[:15]:
                pld = str(item.get("payload", ""))[:50]
                c = item.get("code", "?")
                s = item.get("size", 0)
                t = item.get("time", 0)
                lines.append(f"  {c} | {s:>6}b | {t:.2f}s | {pld}")
        lines.append(f"Avg response size: {avg_size:.0f} bytes")
        lines.append(f"Avg response time: {avg_time:.3f}s")
        return "\n".join(lines)
    except jsonlib.JSONDecodeError:
        return "Invalid JSON input"
    except Exception as e:
        return f"Response analysis failed: {e}"
