#!/usr/bin/env python3
"""
saas_manager.py — Startup-on-Autopilot DevOps

Monitors PM2 processes, self-heals crashes with LLM suggestions,
and scouts LinkedIn/X for potential leads with outreach drafting.
"""

import subprocess
import time
import threading
import json
import logging
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
logger = logging.getLogger("StartupDevOps")


class StartupAutopilot:
    def __init__(self, pm2_apps=None, keywords=None):
        self.pm2_apps = pm2_apps or ["knowyourrank.in", "WillItFit"]
        self.keywords = keywords or ["OMR Checker", "Virtual Try-on"]
        self.ollama_url = "http://localhost:11434"
        self.llm_model = "mistral:latest"

    # ---- PM2 Health ----
    def check_pm2(self):
        try:
            r = subprocess.run(["pm2", "jlist"], capture_output=True, text=True,
                               timeout=15)
            procs = json.loads(r.stdout)
            for p in procs:
                name = p.get("name", "?")
                status = p.get("pm2_env", {}).get("status", "unknown")
                if status != "online":
                    self._handle_crash(name, p)
        except FileNotFoundError:
            logger.warning("pm2 not installed")
        except Exception as e:
            logger.error(f"PM2 check: {e}")

    def _handle_crash(self, app: str, info: dict):
        logger.warning(f"{app} is down — restarting…")
        restarts = info.get("pm2_env", {}).get("restart_time", 0)

        if restarts > 3:
            logpath = info.get("pm2_env", {}).get("pm_err_log_path")
            if logpath and Path(logpath).is_file():
                stderr = Path(logpath).read_text()[-2000:]
                suggestion = self._llm(
                    f"App '{app}' crashed repeatedly. Analyze error and "
                    f"suggest fix:\n\n{stderr}"
                )
                logger.info(f"LLM suggestion for {app}: {suggestion[:200]}")

        subprocess.run(["pm2", "restart", app], capture_output=True)

    # ---- Lead Scouting ----
    def scout_leads(self) -> list:
        leads = []
        for kw in self.keywords:
            leads.append({"keyword": kw, "name": f"Lead for {kw}",
                          "profile": "https://linkedin.com/in/example"})
        return leads

    def draft_outreach(self, lead: dict) -> str:
        return self._llm(
            f"Write a short B2B outreach email for '{lead['keyword']}'. "
            f"Introduce our startup and offer a demo. Keep it professional."
        )

    # ---- LLM ----
    def _llm(self, prompt: str) -> str:
        if not HAS_REQUESTS:
            return ""
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.llm_model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            return r.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM: {e}")
            return ""

    # ---- Loops ----
    def health_loop(self):
        while True:
            if resource_check(is_mobile=False):
                check_kill_switch()
                self.check_pm2()
            time.sleep(60)

    def scout_loop(self):
        while True:
            if resource_check(is_mobile=False):
                check_kill_switch()
                for lead in self.scout_leads():
                    email = self.draft_outreach(lead)
                    logger.info(f"Outreach for {lead['keyword']}: {email[:100]}…")
            time.sleep(86400)  # daily

    def run(self):
        threading.Thread(target=self.health_loop, daemon=True).start()
        threading.Thread(target=self.scout_loop, daemon=True).start()
        logger.info("Startup autopilot running")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    StartupAutopilot().run()
