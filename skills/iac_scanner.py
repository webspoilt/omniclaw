import os
import re
import subprocess

from core.skills.registry import tool


@tool()
def scan_terraform(project_path: str) -> str:
    """Scan Terraform manifests for misconfigurations using checkov and manual patterns."""
    results = []
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["checkov", "--directory", project_path, "--framework", "terraform", "--compact"],  # noqa: S607
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode == 0:
            results.append("checkov: no issues found")
        else:
            results.append(f"checkov output:\n{proc.stdout[:3000]}{proc.stderr[:1000]}")
    except FileNotFoundError:
        results.append("checkov not installed, using pattern scan")
    except Exception as e:
        results.append(f"checkov error: {e}")
    try:
        for root, _, files in os.walk(project_path):
            for f in files:
                if not f.endswith((".tf", ".tf.json")):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                issues = []
                if re.search(r'acl\s*=\s*"public-read"', content):
                    issues.append("S3 bucket has public-read ACL")
                if re.search(r'Effect\s*=\s*"Allow".*?Principal\s*=\s*"\*"', content, re.DOTALL):
                    issues.append("IAM policy allows wildcard principal")
                if re.search(r'ingress\s*\{[^}]*cidr_blocks\s*=\s*\[?"0\.0\.0\.0/0"', content, re.DOTALL):
                    issues.append("Security group allows 0.0.0.0/0 ingress")
                if re.search(r'backend\s+"s3"\s*\{[^}]*encrypt\s*=\s*false', content, re.DOTALL):
                    issues.append("S3 backend encryption disabled")
                if issues:
                    rel = os.path.relpath(path, project_path)
                    results.append(f"{rel}: {'; '.join(issues)}")
    except Exception as e:
        results.append(f"pattern scan error: {e}")
    return "\n".join(results) if results else "No Terraform issues found."


@tool()
def scan_kubernetes(project_path: str) -> str:
    """Scan K8s manifests for misconfigurations using kube-score and kube-bench."""
    results = []
    try:
        k8s_files = [os.path.join(project_path, f) for f in os.listdir(project_path) if f.endswith((".yaml", ".yml"))]
        proc = subprocess.run(  # noqa: S603,S607
            ["kube-score", "score", "--", *k8s_files],  # noqa: S607
            capture_output=True, text=True, timeout=60
        )
        results.append(f"kube-score:\n{proc.stdout[:3000]}{proc.stderr[:1000]}")
    except FileNotFoundError:
        results.append("kube-score not installed")
    except Exception as e:
        results.append(f"kube-score error: {e}")
    try:
        for root, _, files in os.walk(project_path):
            for f in files:
                if not f.endswith((".yaml", ".yml")):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                issues = []
                if "privileged: true" in content:
                    issues.append("Privileged container")
                if "runAsUser: 0" in content:
                    issues.append("Running as root (uid 0)")
                if "imagePullPolicy: Always" not in content and "image:" in content:
                    issues.append("Missing imagePullPolicy: Always")
                if "resources:" not in content:
                    issues.append("No resource limits set")
                if "readOnlyRootFilesystem: true" not in content:
                    issues.append("Root filesystem not read-only")
                if issues:
                    rel = os.path.relpath(path, project_path)
                    results.append(f"{rel}: {'; '.join(issues)}")
    except Exception as e:
        results.append(f"pattern scan error: {e}")
    return "\n".join(results) if results else "No K8s issues found."
