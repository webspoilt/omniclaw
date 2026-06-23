import json
import os
import random
from datetime import datetime

from core.skills.registry import tool

_dataset_index = {}

@tool()
def collect_samples(input_dir: str, output_path: str = "") -> str:
    """Collect text/code samples from a directory into a JSON dataset."""
    samples = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            if not f.endswith((".py", ".txt", ".json", ".yaml", ".yml", ".log", ".md", ".csv")):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                samples.append({
                    "file": os.path.relpath(path, input_dir),
                    "content": content,
                    "size": len(content),
                })
            except Exception:  # noqa: S112
                continue
    if not samples:
        return f"No suitable samples found in {input_dir}"
    out_path = output_path or "/tmp/dataset_{}.json".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    with open(out_path, "w") as f:
        json.dump({"samples": samples, "count": len(samples), "source": input_dir}, f, indent=2)
    return "Collected %d samples from %s to %s" % (len(samples), input_dir, out_path)


@tool()
def label_data(dataset_path: str, label_key: str = "target", rules: str = "") -> str:
    """Apply heuristic labels to dataset samples based on keyword rules."""
    try:
        with open(dataset_path) as f:
            data = json.load(f)
    except Exception as e:
        return f"Error loading dataset: {e}"
    rules_dict = {}
    if rules:
        for rule in rules.split(","):
            if ":" in rule:
                kw, label = rule.split(":", 1)
                rules_dict[kw.strip().lower()] = label.strip()
    if not rules_dict:
        rules_dict = {
            "error": "negative", "fail": "negative", "bug": "negative",
            "success": "positive", "pass": "positive", "valid": "positive",
            "warning": "neutral", "info": "neutral",
        }
    labeled = 0
    for sample in data.get("samples", []):
        content_lower = sample.get("content", "").lower()
        for kw, label in rules_dict.items():
            if kw in content_lower:
                sample[label_key] = label
                labeled += 1
                break
        if label_key not in sample:
            sample[label_key] = "unlabeled"
    with open(dataset_path, "w") as f:
        json.dump(data, f, indent=2)
    label_counts = {}
    for s in data.get("samples", []):
        lbl = s.get(label_key, "unlabeled")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
    return "Labeled %d samples. Labels: %s" % (labeled, label_counts)


@tool()
def split_train_test(dataset_path: str, train_ratio: float = 0.8, seed: int = 42) -> str:
    """Split a labeled dataset into train/test JSON files."""
    try:
        with open(dataset_path) as f:
            data = json.load(f)
    except Exception as e:
        return f"Error loading dataset: {e}"
    samples = data.get("samples", [])
    if not samples:
        return "Dataset is empty"
    random.seed(seed)
    shuffled = list(samples)
    random.shuffle(shuffled)
    split_idx = max(1, int(len(shuffled) * train_ratio))
    train = shuffled[:split_idx]
    test = shuffled[split_idx:]
    base = dataset_path.replace(".json", "")
    train_path = f"{base}_train.json"
    test_path = f"{base}_test.json"
    with open(train_path, "w") as f:
        json.dump({"samples": train, "count": len(train), "split": "train"}, f, indent=2)
    with open(test_path, "w") as f:
        json.dump({"samples": test, "count": len(test), "split": "test"}, f, indent=2)
    return ("Split %d samples: %d train -> %s, %d test -> %s" %
            (len(samples), len(train), train_path, len(test), test_path))
