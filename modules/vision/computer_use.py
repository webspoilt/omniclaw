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

from pathlib import Path
import io

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

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
    """Optimized Screen capture and LLM-based UI understanding."""

    def __init__(self, llm_model: str = "llava:latest",
                 ollama_url: str = "http://localhost:11434"):
        self.model = llm_model
        self.ollama_url = ollama_url
        self.tmp = Path("/tmp/omniclaw_screenshots")
        if platform.system() == "Windows":
             self.tmp = Path(os.getenv("TEMP", ".")) / "omniclaw_screenshots"
        self.tmp.mkdir(parents=True, exist_ok=True)

    def capture_screen(self) -> Path | None:
        """Platform-adaptive screenshot using native APIs."""
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
                # Modern macOS uses ScreenCaptureKit (SCStream) via native wrapper if possible
                # Falling back to 'screencapture' for now but ensuring it captures properly
                subprocess.run(["screencapture", "-x", str(fp)], check=True,
                               timeout=5)
                return fp
            elif system == "Windows":
                # Using DXGI-style via mss if available, otherwise PowerShell fallback
                try:
                    import mss
                    with mss.mss() as sct:
                        sct.shot(output=str(fp))
                    return fp
                except ImportError:
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

    def optimize_image(self, img_path: Path) -> str | None:
        """
        Resizes to 1024px width and encodes as JPEG 85% (Optimized for Tokens).
        Ref: 2026-era vision best practices.
        """
        if not HAS_PIL or not img_path.exists():
            return base64.b64encode(img_path.read_bytes()).decode()

        try:
            with Image.open(img_path) as img:
                # Resize to 1024px width while maintaining aspect ratio
                base_width = 1024
                w_percent = (base_width / float(img.size[0]))
                h_size = int((float(img.size[1]) * float(w_percent)))
                img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)

                # Convert to RGB (required for JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Save to memory as JPEG 85%
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return base64.b64encode(img_path.read_bytes()).decode()

    def analyze_screen(self, img_path: Path, prompt: str = "") -> str | None:
        """Send optimized screenshot to multimodal LLM."""
        if not HAS_REQUESTS or not img_path.exists():
            return None
        
        b64 = self.optimize_image(img_path)
        if not b64:
            return None

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
        logger.info("ComputerUse monitor starting (Multimodal Optimized)")
        while True:
            if resource_check(is_mobile=False):
                check_kill_switch()
                img = self.capture_screen()
                if img:
                    analysis = self.analyze_screen(img)
                    if analysis:
                        logger.info(f"Screen Analysis: {analysis[:150]}…")
                        # Cleanup screenshot after analysis
                        try:
                            img.unlink()
                        except:
                            pass
            time.sleep(interval)


if __name__ == "__main__":
    ComputerUse().run()

