import ast
import os
import re

from core.skills.registry import tool


@tool()
def detect_race_conditions(project_path: str) -> str:
    """Find potential race conditions: shared mutable state without locks."""
    findings = []
    try:
        for root, _, files in os.walk(project_path):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, encoding="utf-8") as fh:
                        tree = ast.parse(fh.read())
                    shared = set()
                    locked = set()
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for t in node.targets:
                                if isinstance(t, ast.Name):
                                    if t.id.startswith("_") and not t.id.startswith("__"):
                                        shared.add(t.id)
                        if isinstance(node, (ast.With, ast.AsyncWith)):
                            for item in node.items:
                                expr = item.context_expr
                                if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
                                    if expr.func.id in ("Lock", "RLock", "Semaphore", "lock"):
                                        locked.add(ast.dump(item.optional_vars))
                    unprotected = shared - locked
                    if unprotected:
                        rel = os.path.relpath(path, project_path)
                        findings.append(f"{rel}: unprotected shared state: {', '.join(unprotected)}")
                except SyntaxError:
                    continue
        if not findings:
            return "No race condition patterns detected."
        return "Potential Race Conditions:\n" + "\n".join(findings[:50])
    except Exception as e:
        return f"Error: {e}"


@tool()
def detect_replay_attacks(project_path: str) -> str:
    """Find patterns vulnerable to replay attacks: missing nonces/timestamps in auth."""
    findings = []
    try:
        for root, _, files in os.walk(project_path):
            for f in files:
                if not f.endswith((".py", ".yaml", ".yml", ".json")):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"(hmac|sign|verify|signature)", content, re.IGNORECASE):
                    has_nonce = re.search(r"(nonce|timestamp|expiry|exp|iat|nbf)", content, re.IGNORECASE)
                    if not has_nonce:
                        rel = os.path.relpath(path, project_path)
                        findings.append(f"{rel}: signing without nonce/timestamp")
                if re.search(r"(session_id|token)", content, re.IGNORECASE):
                    has_rotation = re.search(r"(rotate|refresh|renew|expir)", content, re.IGNORECASE)
                    if not has_rotation:
                        rel = os.path.relpath(path, project_path)
                        findings.append(f"{rel}: session/token without rotation mechanism")
        if not findings:
            return "No replay attack patterns detected."
        return "Replay Attack Concerns:\n" + "\n".join(findings[:50])
    except Exception as e:
        return f"Error: {e}"


@tool()
def detect_stale_cache(project_path: str) -> str:
    """Find caching without TTL or invalidation logic."""
    findings = []
    try:
        for root, _, files in os.walk(project_path):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"(cache|memoize|lru_cache|cached)", content, re.IGNORECASE):
                    has_ttl = re.search(r"(ttl|timeout|expire|invalidate|clear|fresh)", content, re.IGNORECASE)
                    if not has_ttl:
                        rel = os.path.relpath(path, project_path)
                        findings.append(f"{rel}: caching without TTL or invalidation")
        if not findings:
            return "No stale cache patterns detected."
        return "Stale Cache Concerns:\n" + "\n".join(findings[:50])
    except Exception as e:
        return f"Error: {e}"
