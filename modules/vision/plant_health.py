#!/usr/bin/env python3
"""
plant_health.py — Plant Health Analysis via Multimodal LLM.

Takes an image (from termux_camera or any source) and analyzes
leaf health, diseases, pests, and provides care recommendations.
"""

import base64
import logging
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PlantHealth")


class PlantHealthAnalyzer:
    """Analyzes plant images for leaf health using a multimodal LLM."""

    def __init__(self, plant_name: str = "Money Plant",
                 llm_model: str = "llava:latest",
                 ollama_url: str = "http://localhost:11434"):
        self.plant = plant_name
        self.model = llm_model
        self.ollama_url = ollama_url

    def analyze(self, image_path: Path) -> dict:
        """
        Returns:
            {"rating": "Good|Fair|Poor", "analysis": "...",
             "recommendations": "..."}
        """
        if not HAS_REQUESTS or not image_path.exists():
            return {"rating": "Unknown", "analysis": "No image",
                    "recommendations": ""}

        b64 = base64.b64encode(image_path.read_bytes()).decode()
        prompt = (
            f"You are a plant pathologist. Analyze this image of a "
            f"{self.plant}.\n\n"
            f"1. Rate overall health: Good, Fair, or Poor.\n"
            f"2. Identify any diseases, discoloration, wilting, or pests.\n"
            f"3. Provide specific care recommendations.\n\n"
            f"Format your response as:\n"
            f"Rating: <rating>\nAnalysis: <analysis>\nRecommendations: <recs>"
        )
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt,
                      "images": [b64], "stream": False},
                timeout=60,
            )
            text = r.json().get("response", "")
            return self._parse(text)
        except Exception as e:
            logger.error(f"LLM: {e}")
            return {"rating": "Error", "analysis": str(e),
                    "recommendations": ""}

    def _parse(self, text: str) -> dict:
        result = {"rating": "Unknown", "analysis": "", "recommendations": ""}
        for line in text.split("\n"):
            low = line.lower()
            if low.startswith("rating:"):
                result["rating"] = line.split(":", 1)[1].strip()
            elif low.startswith("analysis:"):
                result["analysis"] = line.split(":", 1)[1].strip()
            elif low.startswith("recommendations:"):
                result["recommendations"] = line.split(":", 1)[1].strip()
        if not result["analysis"]:
            result["analysis"] = text
        return result
