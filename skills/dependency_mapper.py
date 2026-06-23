import subprocess

from core.skills.registry import tool


@tool()
def map_dependencies(project_path: str) -> str:
    """Generate a dependency graph of a Python project using pipdeptree."""
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["pipdeptree", "--json-tree"], cwd=project_path,  # noqa: S607
            capture_output=True, text=True, timeout=30
        )
        return proc.stdout[:5000] if proc.returncode == 0 else proc.stderr[:2000]
    except Exception as e:
        return f"Error: {e}"
