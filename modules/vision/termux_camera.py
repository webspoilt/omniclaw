#!/usr/bin/env python3
"""
termux_camera.py — Camera capture via Termux:API.

Wraps termux-camera-photo for front/back camera shots
and provides helpers for base64 encoding and LLM analysis.
"""

import subprocess
import base64
import logging
import time
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
    from core.resource_utils import resource_check
except ImportError:
    def resource_check(**kw): return True

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TermuxCamera")


class TermuxCamera:
    """Termux:API camera wrapper with LLM integration."""

    def __init__(self, output_dir: str = "./captures",
                 llm_model: str = "llava:latest"):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.model = llm_model
        self.ollama_url = "http://localhost:11434"

    def capture(self, camera_id: int = 0) -> Path | None:
        """Take a photo. camera_id: 0=back, 1=front."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = self.out / f"cam{camera_id}_{ts}.jpg"
        try:
            subprocess.run(
                ["termux-camera-photo", "-c", str(camera_id), str(fp)],
                check=True, timeout=15,
            )
            logger.info(f"Captured → {fp}")
            return fp
        except FileNotFoundError:
            logger.error("termux-camera-photo not found (install termux-api)")
            return None
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            return None

    def to_base64(self, img: Path) -> str | None:
        if not img.exists():
            return None
        return base64.b64encode(img.read_bytes()).decode()

    def analyze(self, img: Path, prompt: str = "") -> str | None:
        if not HAS_REQUESTS:
            return None
        b64 = self.to_base64(img)
        if not b64:
            return None
        if not prompt:
            prompt = "Describe what you see in this photo in detail."
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

    def run(self, interval: int = 3600):
        """Periodic capture loop (default: hourly)."""
        logger.info("TermuxCamera running")
        while True:
            if resource_check(is_mobile=True):
                img = self.capture()
                if img:
                    analysis = self.analyze(img)
                    if analysis:
                        logger.info(f"Analysis: {analysis[:150]}…")
            time.sleep(interval)


if __name__ == "__main__":
    TermuxCamera().run()
