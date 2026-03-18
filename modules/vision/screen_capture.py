#!/usr/bin/env python3
"""
screen_capture.py — Cross-platform screen capture for the Vision module.

Resolves GitHub Issue #21: Vision Module - Screen Capture.

API mirrors TermuxCamera so both backends are interchangeable:
  - capture(monitor=1)  -> Path | None
  - to_base64(img)      -> str | None
  - analyze(img, prompt) -> str | None

Backends (in priority order):
  1. mss  (pip install mss)           — fastest, cross-platform
  2. PIL/Pillow ImageGrab             — Windows/macOS only
  3. scrot/gnome-screenshot           — Linux CLI fallback
  4. Mock/placeholder                 — headless / CI environments
"""

import base64
import logging
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("OmniClaw.Vision.ScreenCapture")

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import ImageGrab
    HAS_PIL_GRAB = True
except ImportError:
    HAS_PIL_GRAB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def _is_headless() -> bool:
    """Detect headless / no-display environment."""
    import os
    import sys
    if sys.platform == "linux":
        return not bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return False


class ScreenCapture:
    """Cross-platform screen capture with LLM analysis (Issue #21).

    Usage::

        sc = ScreenCapture(output_dir="./captures")
        img = sc.capture()
        if img:
            analysis = sc.analyze(img, "What is on the screen?")
    """

    def __init__(self, output_dir: str = "./captures",
                 llm_model: str = "llava:latest"):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.model = llm_model
        self.ollama_url = "http://localhost:11434"
        self._headless = _is_headless()

        if self._headless:
            logger.warning(
                "ScreenCapture: headless environment detected (no DISPLAY). "
                "capture() will return None. Set DISPLAY or run with a GUI."
            )
        elif HAS_MSS:
            logger.debug("ScreenCapture backend: mss")
        elif HAS_PIL_GRAB:
            logger.debug("ScreenCapture backend: PIL.ImageGrab")
        else:
            logger.warning(
                "ScreenCapture: no capture backend found. "
                "Install mss: pip install mss"
            )

    # ---------------------------------------------------------------- #
    #  Core capture                                                     #
    # ---------------------------------------------------------------- #

    def capture(self, monitor: int = 1) -> Optional[Path]:
        """Capture a screenshot.

        Args:
            monitor: Monitor index (1-based). 0 = combined virtual screen.

        Returns:
            Path to saved PNG file, or None on failure.
        """
        if self._headless:
            return None

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = self.out / f"screen_{ts}.png"

        if HAS_MSS:
            return self._capture_mss(fp, monitor)
        elif HAS_PIL_GRAB:
            return self._capture_pil(fp)
        else:
            return self._capture_cli(fp)

    def _capture_mss(self, fp: Path, monitor: int) -> Optional[Path]:
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                idx = monitor if monitor < len(monitors) else 1
                sct_img = sct.grab(monitors[idx])
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(fp))
            logger.info(f"Captured (mss) → {fp}")
            return fp
        except Exception as e:
            logger.error(f"mss capture failed: {e}")
            return None

    def _capture_pil(self, fp: Path) -> Optional[Path]:
        try:
            img = ImageGrab.grab()
            img.save(str(fp))
            logger.info(f"Captured (PIL) → {fp}")
            return fp
        except Exception as e:
            logger.error(f"PIL capture failed: {e}")
            return None

    def _capture_cli(self, fp: Path) -> Optional[Path]:
        """Try CLI tools: scrot (Linux), gnome-screenshot, etc."""
        cmds = [
            ["scrot", str(fp)],
            ["gnome-screenshot", "-f", str(fp)],
            ["import", "-window", "root", str(fp)],   # ImageMagick
        ]
        for cmd in cmds:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, timeout=10
                )
                if result.returncode == 0 and fp.exists():
                    logger.info(f"Captured ({cmd[0]}) → {fp}")
                    return fp
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        logger.error("Screen capture failed: no backend available (headless?)")
        return None

    # ---------------------------------------------------------------- #
    #  Base64 & LLM analysis                                           #
    # ---------------------------------------------------------------- #

    def to_base64(self, img: Path) -> Optional[str]:
        """Encode captured image to base64 string."""
        if not img or not img.exists():
            return None
        return base64.b64encode(img.read_bytes()).decode()

    def analyze(self, img: Path, prompt: str = "") -> Optional[str]:
        """Send image to local LLM (Ollama llava) for analysis."""
        if not HAS_REQUESTS:
            logger.warning("requests not installed — cannot call Ollama")
            return None
        b64 = self.to_base64(img)
        if not b64:
            return None
        if not prompt:
            prompt = "Describe what is shown on this screen in detail."
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt,
                      "images": [b64], "stream": False},
                timeout=60,
            )
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return None

    def run(self, interval: int = 300):
        """Periodic capture loop."""
        logger.info(f"ScreenCapture running (every {interval}s)")
        while True:
            img = self.capture()
            if img:
                analysis = self.analyze(img)
                if analysis:
                    logger.info(f"Analysis: {analysis[:150]}…")
            time.sleep(interval)


if __name__ == "__main__":
    ScreenCapture().run()
