import os

from core.skills.registry import tool


@tool()
def find_trust_boundaries(project_path: str) -> str:
    """Identify trust boundaries in code and config. Detects missing auth checks."""
    results = []
    auth_keywords = ["authenticate", "authorize", "login", "token", "jwt", "session", "permission", "acl", "rbac"]
    boundary_keywords = ["network", "firewall", "vpc", "subnet", "security_group", "ingress", "egress"]
    try:
        for root, _, files in os.walk(project_path):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml", ".json", ".tf", ".hcl")):
                    path = os.path.join(root, f)
                    try:
                        with open(path, encoding="utf-8", errors="ignore") as fh:
                            lines = fh.readlines()
                        missing = []
                        for i, line in enumerate(lines, 1):
                            low = line.lower()
                            if any(kw in low for kw in boundary_keywords):
                                has_auth = any(
                                    kw in low for kw in auth_keywords
                                )
                                if not has_auth:
                                    missing.append(f"  L{i}: {line.rstrip()[:120]}")
                        if missing:
                            rel = os.path.relpath(path, project_path)
                            results.append(f"\n! {rel} (boundary without auth check):")
                            results.extend(missing)
                    except Exception:  # noqa: S112
                        continue
        if not results:
            return "No trust boundary issues found."
        return "Trust Boundary Analysis:\n" + "\n".join(results[:200])
    except Exception as e:
        return f"Error: {e}"


@tool()
def check_missing_auth(endpoint_dir: str) -> str:
    """Scan API route files for endpoints missing authentication decorators."""
    import ast
    findings = []
    try:
        for root, _, files in os.walk(endpoint_dir):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, encoding="utf-8") as fh:
                        tree = ast.parse(fh.read())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            has_auth = any(
                                d.id == "login_required" or d.id == "require_auth"
                                for d in node.decorator_list if isinstance(d, ast.Name)
                            )
                            if not has_auth and node.name.startswith(("get_", "post_", "put_", "delete_", "api_")):
                                findings.append(f"{os.path.relpath(path, endpoint_dir)}:{node.lineno} {node.name}")
                except SyntaxError:
                    continue
        if not findings:
            return "No missing auth decorators detected."
        return "Missing Auth Checks:\n" + "\n".join(findings[:100])
    except Exception as e:
        return f"Error: {e}"
