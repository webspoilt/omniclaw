# ruff: noqa: S108
"""Program synthesis: generate code from specifications, verify correctness, apply templates."""
from __future__ import annotations

import subprocess
from pathlib import Path

from core.skills.registry import tool

_TEMPLATES: dict[str, str] = {
    "python_cli": """#!/usr/bin/env python3
\"\"\"{description}\"\"\"
import sys

def main():
    {body}

if __name__ == "__main__":
    main()
""",
    "bash_script": """#!/bin/bash
# {description}
{body}
""",
    "c_program": """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {{
    {body}
    return 0;
}}
""",
    "rust_program": """fn main() {{
    {body}
}}
""",
    "python_module": """\"\"\"{description}\"\"\"
from __future__ import annotations

{body}
""",
}


@tool()
def generate_program_spec(description: str, language: str = "python") -> str:
    """Generate a program skeleton from a specification and available templates."""
    try:
        template_key = {
            "python": "python_cli", "py": "python_cli",
            "bash": "bash_script", "sh": "bash_script",
            "c": "c_program", "rust": "rust_program", "rs": "rust_program",
        }.get(language.lower())
        if not template_key:
            return f"Unsupported language '{language}'. Available: python, bash, c, rust"
        template = _TEMPLATES.get(template_key)
        if not template:
            return f"No template for language '{language}'"
        body = f"print('{description}')" if "python" in language.lower() else f'printf("{description}\\n");'
        if language.lower() == "bash":
            body = f'echo "{description}"'
        if language.lower() == "rust":
            body = f'println!("{description}");'
        code = template.format(description=description, body=body)
        return f"Generated {language} program skeleton:\n\n{code}"
    except Exception as e:
        return f"Program generation failed: {e}"


@tool()
def synthesize_code(spec_json: str) -> str:
    """Synthesize code from a structured specification (JSON with name, inputs, outputs, behavior)."""
    try:
        import json as jsonlib
        spec = jsonlib.loads(spec_json)
        if not isinstance(spec, dict):
            return "Spec must be a JSON object with 'name', 'inputs', 'outputs', 'behavior' fields"
        name = spec.get("name", "generated_function")
        inputs = spec.get("inputs", [])
        outputs = spec.get("outputs", ["result"])
        behavior = spec.get("behavior", "")
        returns = ", ".join(outputs)
        params = ", ".join(f"{i}" for i in inputs)
        docstring = f'Auto-synthesized function: {behavior}' if behavior else f'Generated {name}'
        code = (
            f"def {name}({params}):\n"
            f'    """{docstring}"""\n'
            f"    # TODO: Implement based on specification\n"
            f"    # inputs: {', '.join(inputs) if inputs else 'none'}\n"
            f"    # outputs: {returns}\n"
            f"    # behavior: {behavior}\n"
            f"    pass\n"
        )
        return f"Synthesized function:\n\n{code}"
    except jsonlib.JSONDecodeError:
        return "Invalid JSON specification"
    except Exception as e:
        return f"Synthesis failed: {e}"


@tool()
def verify_correctness(path: str, test_input: str = "") -> str:
    """Basic correctness verification: compile or syntax-check a source file."""
    try:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        ext = p.suffix.lower()
        if ext == ".py":
            proc = subprocess.run(  # noqa: S603
                [__import__("sys").executable, "-m", "py_compile", str(p)],  # noqa: S607
                capture_output=True, text=True, timeout=15,
            )
            if proc.returncode == 0:
                return f"Python syntax: VALID — {path}"
            return f"Python syntax: INVALID\n{proc.stderr.strip()[:500]}"
        elif ext in (".c", ".cpp"):
            compiler = "g++" if ext == ".cpp" else "gcc"
            proc = subprocess.run(  # noqa: S603
                [compiler, "-fsyntax-only", str(p)],  # noqa: S607
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode == 0:
                return f"{compiler} syntax: VALID — {path}"
            return f"{compiler} syntax: INVALID\n{proc.stderr.strip()[:500]}"
        elif ext == ".rs":
            proc = subprocess.run(  # noqa: S603
                ["rustc", "--edition", "2021", "--crate-type", "lib", "--out-dir", "/tmp", str(p)],  # noqa: S607
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode == 0:
                return f"Rust syntax: VALID — {path}"
            return f"Rust syntax: INVALID\n{proc.stderr.strip()[:500]}"
        elif ext == ".sh":
            proc = subprocess.run(  # noqa: S603
                ["bash", "-n", str(p)], capture_output=True, text=True, timeout=15,  # noqa: S607
            )
            if proc.returncode == 0:
                return f"Bash syntax: VALID — {path}"
            return f"Bash syntax: INVALID\n{proc.stderr.strip()[:500]}"
        else:
            return f"Unsupported file type: {ext}. Supported: .py, .c, .cpp, .rs, .sh"
    except FileNotFoundError as e:
        return f"Required tool not found: {e}"
    except Exception as e:
        return f"Verification failed: {e}"
