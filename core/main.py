#!/usr/bin/env python3
"""
main.py — OmniClaw v4.2 Orchestrator Daemon

Unified event loop that starts all workers:
  - P2P neural mesh
  - Shadow shell honeypot (Issue #24 / #27)
  - Computer vision / Termux camera
  - MCP server (Issue #18 / #27)
  - Health check HTTP server (Issue #19 / #27)
  - Genesis self-evolution
  - Knowledge graph

CLI flags:
  --health    Start the health server on port 8080 (configurable)
  --mcp       Start the MCP server on port 8000 (configurable)
  --no-mesh   Skip P2P neural mesh startup

Conditional startup based on node type (desktop vs mobile).
"""

import asyncio
import os
import sys
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.resource_utils import resource_check
from core.kill_switch import check_kill_switch
from core.knowledge_graph import KnowledgeGraph

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OmniClaw")

# ---- Config ----
CONFIG_PATH = Path(__file__).parent / "config.yaml"

_DEFAULTS = {
    "node_id": "desktop",
    "p2p_port": 5555,
    "peers": [],
    "knowledge_path": "./data/knowledge",
    "llm": {"primary": "ollama", "model": "llama3:latest",
            "ollama_url": "http://localhost:11434"},
}


def _load_config() -> dict:
    if HAS_YAML and CONFIG_PATH.is_file():
        with open(CONFIG_PATH) as f:
            return {**_DEFAULTS, **yaml.safe_load(f)}
    return dict(_DEFAULTS)


# ---- Daemon ----
class OmniClawDaemon:
    def __init__(self):
        self.config = _load_config()
        self.node_id = self.config.get("node_id", "desktop")
        self.is_mobile = self.node_id == "mobile"
        self.running = False
        self.workers: list = []

        # Knowledge graph
        self.knowledge = KnowledgeGraph(
            self.config.get("knowledge_path", "./data/knowledge"))

        # LLM config
        llm_cfg = self.config.get("llm", {})
        self.llm_model = llm_cfg.get("model", "llama3:latest")
        self.ollama_url = llm_cfg.get("ollama_url", "http://localhost:11434")

    def llm_inference(self, prompt: str) -> str:
        """Local LLM inference via Ollama."""
        try:
            import requests
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.llm_model, "prompt": prompt,
                      "stream": False},
                timeout=120,
            )
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM: {e}")
            return ""

    def _handle_task(self, task: dict) -> dict:
        """Handle task requests from P2P mesh."""
        t = task.get("type", "")
        if t == "llm_inference":
            return {"result": self.llm_inference(task.get("prompt", ""))}
        elif t == "knowledge_query":
            return self.knowledge.query(task.get("query", {}))
        return {"error": f"Unknown task type: {t}"}

    def _start_mesh(self):
        try:
            import base64
            from modules.p2p.mesh import NeuralMeshNode
            key = base64.b64decode(os.getenv("AES_KEY", ""))
            if len(key) != 32:
                logger.warning("AES_KEY not set or wrong length — mesh disabled")
                return
            mesh = NeuralMeshNode(
                self.node_id,
                self.config.get("p2p_port", 5555),
                self.config.get("peers", []),
                key,
            )
            mesh.task_handler = self._handle_task
            mesh.knowledge_handler = self.knowledge.query
            mesh.start()
            self.workers.append(mesh)
            logger.info("P2P mesh started")
        except Exception as e:
            logger.warning(f"Mesh init failed: {e}")

    def _start_desktop_modules(self, enable_honeypot: bool = True):
        # Shadow shell honeypot (Issue #24 — uses proper ShadowShellHoneypot)
        if enable_honeypot:
            try:
                from modules.security.honeypot import ShadowShellHoneypot

                def _run_honeypot():
                    asyncio.run(ShadowShellHoneypot(port=2222).start())

                t = threading.Thread(target=_run_honeypot, daemon=True)
                t.start()
                logger.info("Shadow shell honeypot started on :2222")
            except Exception as e:
                logger.warning(f"Honeypot: {e}")

        # Computer vision
        try:
            from modules.vision.computer_use import ComputerUse
            t = threading.Thread(target=ComputerUse().run, daemon=True)
            t.start()
            logger.info("ComputerUse started")
        except Exception as e:
            logger.warning(f"ComputerUse: {e}")

        # Genesis
        try:
            from modules.evolution.genesis import Genesis
            g = Genesis(daemon=self)
            t = threading.Thread(target=g.run, daemon=True)
            t.start()
            logger.info("Genesis started")
        except Exception as e:
            logger.warning(f"Genesis: {e}")

    def _start_mobile_modules(self):
        # Termux camera
        try:
            from modules.vision.termux_camera import TermuxCamera
            t = threading.Thread(target=TermuxCamera().run, daemon=True)
            t.start()
            logger.info("TermuxCamera started")
        except Exception as e:
            logger.warning(f"TermuxCamera: {e}")

    def _start_mcp(self, port: int = 8000):
        """Start MCP server in a background thread (Issue #18 / #27)."""
        try:
            from connectors.mcp_host import app
            t = threading.Thread(
                target=lambda: app.run(host="0.0.0.0", port=port),
                daemon=True,
            )
            t.start()
            logger.info(f"MCP server on :{port}")
        except Exception as e:
            logger.warning(f"MCP: {e}")

    def _start_health_server(self, port: int = 8080):
        """Start the health check HTTP server in a background thread (Issue #19 / #27)."""
        try:
            from core.health_server import HealthServer

            def _run_health():
                hs = HealthServer(host="0.0.0.0", port=port)
                asyncio.run(hs.start())

            t = threading.Thread(target=_run_health, daemon=True)
            t.start()
            logger.info(f"Health server on http://0.0.0.0:{port}/health")
        except Exception as e:
            logger.warning(f"HealthServer: {e}")

    def start(self, enable_mcp: bool = True, enable_health: bool = True,
              enable_mesh: bool = True):
        self.running = True
        logger.info(f"OmniClaw v4.2.0 starting (node={self.node_id})")

        if not self.is_mobile:
            # Validate Secure Enclave via YubiKey Challenge-Response
            try:
                from core.security.secure_config import SecureConfigLoader
                loader = SecureConfigLoader()
                if loader.unlock_vault('config/vault_key.enc'):
                    self.secure_config = loader.load_secure_config('config/offensive_config.yaml.aes')
                    logger.info("YubiKey authenticated. Secure Enclave active.")
                else:
                    logger.warning("YubiKey not present - secure modules disabled.")
            except Exception as e:
                logger.warning(f"Secure Enclave bypassed (Hardware missing/unconfigured): {e}")

        if enable_mesh:
            self._start_mesh()

        if self.is_mobile:
            self._start_mobile_modules()
        else:
            self._start_desktop_modules()

        if enable_mcp:
            self._start_mcp(port=self.config.get("mcp_port", 8000))

        if enable_health:
            self._start_health_server(port=self.config.get("health_port", 8080))

        # Main loop
        try:
            while self.running:
                check_kill_switch()
                resource_check(is_mobile=self.is_mobile)
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop()
        except RuntimeError as e:
            ts = datetime.utcnow().isoformat(timespec='seconds')
            logger.error(f"Kill switch triggered at {ts}: {e}")
            self.stop()

    def stop(self):
        logger.info("Shutting down…")
        self.running = False
        for w in self.workers:
            if hasattr(w, "stop"):
                w.stop()
        self.knowledge.save()
        logger.info("OmniClaw stopped")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OmniClaw v4.2 Orchestrator Daemon")
    parser.add_argument("--no-mcp", action="store_true", help="Disable MCP server")
    parser.add_argument("--no-health", action="store_true", help="Disable health server")
    parser.add_argument("--no-mesh", action="store_true", help="Disable P2P mesh")
    args = parser.parse_args()

    OmniClawDaemon().start(
        enable_mcp=not args.no_mcp,
        enable_health=not args.no_health,
        enable_mesh=not args.no_mesh,
    )
