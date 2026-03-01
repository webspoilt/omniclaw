#!/usr/bin/env python3
"""
computer_use.py — Screen Parsing & Interaction

Captures screenshots on X11, Wayland, or Android (Termux)
and sends them to a multimodal LLM for UI understanding.
"""

import subprocess
import base64
import logging
import time
import platform
from pathlib import Path

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
logger = logging.getLogger("ComputerUse")


class ComputerUse:
    """Screen capture and LLM-based UI understanding."""

    def __init__(self, llm_model: str = "llava:latest",
                 ollama_url: str = "http://localhost:11434"):
        self.model = llm_model
        self.ollama_url = ollama_url
        self.tmp = Path("/tmp/omniclaw_screenshots")
        self.tmp.mkdir(parents=True, exist_ok=True)

    def capture_screen(self) -> Path | None:
        """Platform-adaptive screenshot."""
        fp = self.tmp / f"screen_{int(time.time())}.png"
        system = platform.system()
        try:
            if system == "Linux":
                # Try Wayland (grim) first, then X11 (scrot)
                for cmd in [["grim", str(fp)], ["scrot", str(fp)]]:
                    try:
                        subprocess.run(cmd, check=True, capture_output=True,
                                       timeout=5)
                        return fp
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
                # Termux fallback
                subprocess.run(["termux-screenshot", str(fp)], check=True,
                               capture_output=True, timeout=5)
                return fp
            elif system == "Darwin":
                subprocess.run(["screencapture", "-x", str(fp)], check=True,
                               timeout=5)
                return fp
            elif system == "Windows":
                # PowerShell screenshot
                ps = (f"Add-Type -AssemblyName System.Windows.Forms;"
                      f"[System.Windows.Forms.Screen]::PrimaryScreen | "
                      f"ForEach-Object {{ $b = New-Object Drawing.Bitmap($_.Bounds.Width,$_.Bounds.Height);"
                      f"[Drawing.Graphics]::FromImage($b).CopyFromScreen(0,0,0,0,$b.Size);"
                      f"$b.Save('{fp}') }}")
                subprocess.run(["powershell", "-Command", ps], check=True,
                               timeout=10)
                return fp
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
        return None

    def analyze_screen(self, img: Path, prompt: str = "") -> str | None:
        """Send screenshot to multimodal LLM."""
        if not HAS_REQUESTS or not img.exists():
            return None
        b64 = base64.b64encode(img.read_bytes()).decode()
        if not prompt:
            prompt = ("Describe what's on screen. Identify any UI elements, "
                      "error messages, or actionable items.")
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

    def run(self, interval: int = 300):
        """Periodic screen monitoring loop."""
        logger.info("ComputerUse monitor starting")
        while True:
            if resource_check(is_mobile=False):
                check_kill_switch()
                img = self.capture_screen()
                if img:
                    analysis = self.analyze_screen(img)
                    if analysis:
                        logger.info(f"Screen: {analysis[:150]}…")
            time.sleep(interval)


if __name__ == "__main__":
    ComputerUse().run()
