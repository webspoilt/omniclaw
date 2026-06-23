# ruff: noqa: UP031
import ast
import os
import random

from core.skills.registry import tool

_mutation_counter = 0

@tool()
def mutate_source_file(file_path: str) -> str:
    """Apply random semantics-preserving mutations to a Python source file."""
    global _mutation_counter
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
        try:
            ast.parse(source)
        except SyntaxError as e:
            return f"Syntax error in {file_path}: {e}"
        mutations = []
        new_source = source
        pairs = [
            ("==", "!="), ("!=", "=="), ("True", "False"), ("False", "True"),
            (" and ", " or "), (" or ", " and "), (">", "<"), ("<", ">"),
            (" + ", " - "), (" - ", " + "),
        ]
        for old, new in pairs:
            if old in new_source:
                new_source = new_source.replace(old, new, 1)
                mutations.append(f"replaced {old.strip()} with {new.strip()}")
                break
        if not mutations:
            return f"No suitable mutation targets found in {file_path}"
        _mutation_counter += 1
        mutated_path = file_path.replace(".py", "_mutated_%d.py" % _mutation_counter)
        if mutated_path == file_path:
            mutated_path = "%s.mutated_%d" % (file_path, _mutation_counter)
        with open(mutated_path, "w") as f:
            f.write(new_source)
        return "Created %s with %d mutation(s): %s" % (mutated_path, len(mutations), ", ".join(mutations))
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error: {e}"


@tool()
def apply_code_template(template_path: str, output_path: str, replacements: str = "") -> str:
    """Apply template replacement (replace {{KEY}} with values)."""
    try:
        replacements_dict = {}
        if replacements:
            for pair in replacements.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    replacements_dict[k.strip()] = v.strip()
        with open(template_path, encoding="utf-8") as f:
            content = f.read()
        for key, value in replacements_dict.items():
            content = content.replace("{{" + key + "}}", value)
        with open(output_path, "w") as f:
            f.write(content)
        used = list(replacements_dict.keys())
        return ("Generated %s from %s with %d replacements: %s" %
                (output_path, template_path, len(used), ", ".join(used)))
    except FileNotFoundError:
        return f"Template not found: {template_path}"
    except Exception as e:
        return f"Error: {e}"


@tool()
def generate_variant(source_path: str, output_dir: str = "", count: int = 3) -> str:
    """Generate multiple mutated variants of a source file."""
    try:
        with open(source_path, encoding="utf-8") as f:
            base = f.read()
        out_dir = output_dir or os.path.dirname(source_path)
        os.makedirs(out_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        variants = []
        for i in range(count):
            lines = base.splitlines()
            if len(lines) > 5:
                idx = random.randint(1, len(lines) - 1)  # noqa: S311
                orig = lines[idx]
                if orig.strip().startswith("#"):
                    lines[idx] = ""
                elif "=" in orig:
                    lhs, rhs = orig.split("=", 1)
                    if rhs.strip().isdigit():
                        val = int(rhs.strip())
                        lines[idx] = "%s= %d" % (lhs, val + random.randint(-10, 10))  # noqa: S311
            out_name = "%s_variant_%d.py" % (base_name, i + 1)
            out_path = os.path.join(out_dir, out_name)
            with open(out_path, "w") as f:
                f.write("\n".join(lines))
            variants.append(out_name)
        return "Generated %d variants in %s: %s" % (len(variants), out_dir, ", ".join(variants))
    except FileNotFoundError:
        return f"Source not found: {source_path}"
    except Exception as e:
        return f"Error: {e}"
