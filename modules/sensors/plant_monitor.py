#!/usr/bin/env python3
"""
plant_monitor.py — Green Thumb Bio-Guardian

Uses Termux camera to capture plant images and analyze leaf health
with a multimodal LLM (llava / gemini via Ollama).
"""

import time
import base64
import subprocess
import logging
from pathlib import Path
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from core.kill_switch import check_kill_switch
    from core.resource_utils import resource_check
except ImportError:
    def check_kill_switch(): pass
    def resource_check(**kw): return True

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GreenThumb")


class PlantMonitor:
    def __init__(self, plant_name: str = "Money Plant",
                 llm_model: str = "llava:latest"):
        self.plant = plant_name
        self.model = llm_model
        self.ollama_url = "http://localhost:11434"
        self.img_dir = Path("./plant_images")
        self.img_dir.mkdir(parents=True, exist_ok=True)

    def capture(self) -> Path | None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = self.img_dir / f"{self.plant}_{ts}.jpg"
        try:
            subprocess.run(["termux-camera-photo", "-c", "1", str(fp)],
                           check=True, timeout=15)
            return fp
        except Exception as e:
            logger.error(f"Camera: {e}")
            return None

    def analyze(self, img: Path) -> str | None:
        if not HAS_REQUESTS or not img.exists():
            return None
        b64 = base64.b64encode(img.read_bytes()).decode()
        prompt = (
            f"Analyze the leaf health of this {self.plant}. "
            f"Identify diseases, discoloration, or pests. "
            f"Rate: Good / Fair / Poor. Give care recommendations."
        )
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt,
                      "images": [b64], "stream": False},
                timeout=60,
            )
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM: {e}")
            return None

    def run(self, interval: int = 86400):
        logger.info(f"Monitoring {self.plant} every {interval}s")
        while True:
            if resource_check(is_mobile=True):
                check_kill_switch()
                img = self.capture()
                if img:
                    analysis = self.analyze(img)
                    if analysis:
                        logger.info(f"🌱 {self.plant}: {analysis[:200]}")
            time.sleep(interval)


if __name__ == "__main__":
    PlantMonitor().run()
