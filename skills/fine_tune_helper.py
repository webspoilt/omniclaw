"""Export training datasets and launch fine-tuning scripts for local LLMs."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Optional

from core.skills.registry import tool


_TRAIN_DIR = Path(__file__).resolve().parent.parent / "data" / "training"


@tool(
    name="export_chat_dataset",
    description="Export a JSONL chat dataset from the agent memory for fine-tuning. Uses conversation pairs format: {'instruction': ..., 'output': ...}.",
    parameters={
        "entries": {"type": "string", "description": "JSON array of {instruction, output} objects"},
        "filename": {"type": "string", "description": "Output filename (default 'train_dataset.jsonl')"},
        "split_ratio": {"type": "number", "description": "Train/validation split ratio (default 0.9)"},
    },
    required=["entries"],
)
async def export_chat_dataset(entries: str, filename: Optional[str] = None, split_ratio: float = 0.9) -> dict[str, Any]:
    _TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(entries)
    except json.JSONDecodeError as e:
        return {"error": f"invalid JSON: {e}"}

    if not isinstance(data, list):
        return {"error": "entries must be a JSON array"}

    validated = []
    for i, entry in enumerate(data):
        if isinstance(entry, dict) and "instruction" in entry and "output" in entry:
            validated.append(entry)

    if not validated:
        return {"error": "no valid entries found (need 'instruction' and 'output' keys)"}

    name = filename or "train_dataset.jsonl"
    path = _TRAIN_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        for entry in validated:
            f.write(json.dumps(entry) + "\n")

    split_idx = int(len(validated) * split_ratio)
    train_path = _TRAIN_DIR / f"train_{name}"
    val_path = _TRAIN_DIR / f"val_{name}"
    with open(train_path, "w", encoding="utf-8") as f:
        for entry in validated[:split_idx]:
            f.write(json.dumps(entry) + "\n")
    with open(val_path, "w", encoding="utf-8") as f:
        for entry in validated[split_idx:]:
            f.write(json.dumps(entry) + "\n")

    return {
        "total_entries": len(validated),
        "train_entries": split_idx,
        "val_entries": len(validated) - split_idx,
        "dataset_path": str(path),
        "train_path": str(train_path),
        "val_path": str(val_path),
    }


@tool(
    name="run_loratune",
    description="Run a LoRA fine-tuning script using mlx or llama.cpp. Expects scripts at project/backend/tools/.",
    parameters={
        "model_path": {"type": "string", "description": "Path to base model (GGUF or MLX format)"},
        "train_file": {"type": "string", "description": "Path to training JSONL file"},
        "val_file": {"type": "string", "description": "Path to validation JSONL file"},
        "framework": {"type": "string", "description": "mlx or llama.cpp"},
        "lora_rank": {"type": "integer", "description": "LoRA rank (default 8)"},
    },
    required=["model_path", "train_file"],
)
async def run_loratune(model_path: str, train_file: str, val_file: Optional[str] = None, framework: str = "mlx", lora_rank: int = 8) -> str:
    train_path = Path(train_file)
    if not train_path.is_file():
        return f"Error: training file not found: {train_file}"

    project_root = Path(__file__).resolve().parent.parent

    if framework == "mlx":
        script = project_root / "project" / "backend" / "tools" / "mlx_lora.py"
        if not script.exists():
            return "Error: mlx_lora.py not found at project/backend/tools/"
        cmd = [
            "python3", str(script),
            "--model", model_path,
            "--train-file", train_file,
            "--lora-rank", str(lora_rank),
        ]
        if val_file and Path(val_file).is_file():
            cmd.extend(["--val-file", val_file])
    elif framework == "llama.cpp":
        script = project_root / "project" / "backend" / "tools" / "llama_finetune"
        if not script.exists():
            return "Error: llama_finetune binary not found"
        cmd = [
            str(script),
            "--model", model_path,
            "--train-data", train_file,
        ]
        if val_file and Path(val_file).is_file():
            cmd.extend(["--val-data", val_file])
    else:
        return f"Error: unknown framework '{framework}'"

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        return "Fine-tuning timed out after 3600s"
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"

    if proc.returncode == 0:
        return f"Fine-tuning started successfully.\n{proc.stdout[-2000:]}"
    else:
        return f"Fine-tuning failed (exit {proc.returncode}):\n{proc.stderr[-2000:]}"


@tool(
    name="check_training_status",
    description="Check if GPU and training libraries are available for fine-tuning.",
    parameters={},
)
async def check_training_status() -> dict[str, Any]:
    status: dict[str, Any] = {}

    try:
        proc = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            gpus = [g.strip() for g in proc.stdout.strip().splitlines() if g.strip()]
            status["gpu"] = {"available": True, "devices": gpus}
        else:
            status["gpu"] = {"available": False}
    except FileNotFoundError:
        status["gpu"] = {"available": False}

    try:
        import torch
        status["torch"] = {
            "available": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
        }
    except ImportError:
        status["torch"] = {"available": False}

    import importlib
    status["mlx"] = {"available": importlib.util.find_spec("mlx.core") is not None}

    _TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    datasets = list(_TRAIN_DIR.glob("*.jsonl"))
    status["datasets_available"] = [d.name for d in datasets]

    return status


@tool(
    name="export_memory_as_dataset",
    description="Convert the agent's memory file into a fine-tuning dataset.",
    parameters={
        "memory_file": {"type": "string", "description": "Path to memory file (default: /root/agent_memory.txt)"},
        "output_filename": {"type": "string", "description": "Output JSONL filename"},
    },
    required=[],
)
async def export_memory_as_dataset(memory_file: str = "/root/agent_memory.txt", output_filename: Optional[str] = None) -> dict[str, Any]:
    mem_path = Path(memory_file)
    if not mem_path.is_file():
        return {"error": f"memory file not found: {memory_file}"}

    text = mem_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("Command:"):
            cmd = lines[i][len("Command:"):].strip()
            if i + 1 < len(lines) and lines[i + 1].startswith("Result:"):
                result = lines[i + 1][len("Result:"):].strip()
                entries.append({"instruction": f"Execute: {cmd}", "output": result})
                i += 2
            else:
                i += 1
        else:
            i += 1

    if not entries:
        return {"error": "no Command/Result pairs found in memory file"}

    result = await export_chat_dataset(json.dumps(entries), output_filename)
    return result
