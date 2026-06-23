# ruff: noqa: S108, S110, UP031
import json
import os
import subprocess

from core.skills.registry import tool


@tool()
def prepare_training_config(
    model_name: str = "llama-2-7b",
    dataset_path: str = "",
    output_dir: str = "/tmp/training",
    learning_rate: float = 2e-5,
    num_epochs: int = 3,
    batch_size: int = 4,
) -> str:
    """Generate a training configuration JSON file for fine-tuning."""
    config = {
        "model": model_name,
        "dataset": dataset_path or "/tmp/dataset_train.json",
        "output_dir": output_dir,
        "learning_rate": learning_rate,
        "num_epochs": num_epochs,
        "batch_size": batch_size,
        "optimizer": "adamw",
        "scheduler": "cosine",
        "warmup_ratio": 0.1,
        "fp16": True,
        "gradient_checkpointing": True,
        "logging_steps": 10,
        "save_steps": 500,
    }
    os.makedirs(output_dir, exist_ok=True)
    config_path = os.path.join(output_dir, "training_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return f"Config saved to {config_path}\n{json.dumps(config, indent=2)}"


@tool()
def run_fine_tune(config_path: str) -> str:
    """Run a fine-tuning job using available frameworks (torch/llama.cpp/transformers)."""
    if not os.path.exists(config_path):
        return f"Config not found: {config_path}"
    with open(config_path) as f:
        config = json.load(f)
    frameworks = []
    for name, code in [
        ("torch", "import torch; print(torch.__version__)"),
        ("llama-train", None),
        ("transformers", "import transformers; print(transformers.__version__)"),
    ]:
        try:
            if code is None:
                proc = subprocess.run([name, "--help"], capture_output=True, text=True, timeout=10)  # noqa: S603,S607
                if proc.returncode < 2:
                    frameworks.append(name)
            else:
                proc = subprocess.run(  # noqa: S603
                    ["python", "-c", code], capture_output=True, text=True, timeout=10  # noqa: S607
                )
                if proc.returncode == 0:
                    frameworks.append(proc.stdout.strip())
        except Exception:  # noqa: S110
            pass
    if not frameworks:
        return ("No training frameworks available. "
                "Install with: pip install torch transformers")
    report = "=== Fine-Tuning Run ===\nAvailable frameworks: {}\n".format(", ".join(frameworks))
    report += "Model: {}\n".format(config.get("model", "unknown"))
    report += "Dataset: {}\n".format(config.get("dataset", "unknown"))
    report += "Epochs: %d\n" % config.get("num_epochs", 3)
    report += "Batch size: %d\n" % config.get("batch_size", 4)
    report += "Learning rate: {}\n".format(config.get("learning_rate", "2e-5"))
    report += f"\nTo execute: python -m transformers.trainer --config {config_path}\n"
    report += "Note: Actual training requires GPU and significant time."
    return report


@tool()
def evaluate_model(model_path: str, test_dataset: str = "") -> str:
    """Evaluate a trained model against a test dataset using available frameworks."""
    if not os.path.exists(model_path):
        return f"Model not found: {model_path}"
    available = []
    for name, code in [
        ("torch", "import torch; print('torch ok')"),
        ("evaluate", "import evaluate; print('evaluate ok')"),
    ]:
        try:
            proc = subprocess.run(  # noqa: S603
                ["python", "-c", code], capture_output=True, text=True, timeout=5  # noqa: S607
            )
            if proc.returncode == 0:
                available.append(name)
        except Exception:  # noqa: S110
            pass
    if not available:
        return "No evaluation frameworks available. Install with: pip install torch evaluate"
    if not test_dataset or not os.path.exists(test_dataset):
        test_dataset = os.path.join(os.path.dirname(model_path), "dataset_test.json")
    if not os.path.exists(test_dataset):
        test_dataset = "/tmp/dataset_test.json"
    num = 0
    if os.path.exists(test_dataset):
        try:
            with open(test_dataset) as f:
                test_data = json.load(f)
            num = len(test_data.get("samples", []))
        except Exception:
            pass
    result = "=== Model Evaluation ===\n"
    result += f"Model: {model_path}\n"
    result += "Test dataset: %s (%d samples)\n" % (test_dataset, num)
    result += "Available frameworks: {}\n".format(", ".join(available))
    result += "\nMetrics (placeholder):\n"
    result += "  accuracy:  0.00 (requires execution)\n"
    result += "  f1:        0.00 (requires execution)\n"
    result += "  loss:      0.00 (requires execution)\n"
    result += "\nTo evaluate: python -c \"from transformers import AutoModel; ...\"\n"
    return result
