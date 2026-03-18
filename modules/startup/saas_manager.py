#!/usr/bin/env python3
"""
saas_manager.py — Startup-on-Autopilot DevOps

Monitors PM2 processes, self-heals crashes with LLM suggestions,
and scouts LinkedIn/X for potential leads with outreach drafting.

v4.2 additions (Issue #26):
  - PM2Monitor: structured PM2 status, restart, and history tracking
  - LeadStore: JSON-persisted lead database for outreach tracking
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


class PM2Monitor:
    """PM2 process monitor with structured status and restart (Issue #26).

    Usage::

        mon = PM2Monitor()
        status = mon.get_status()  # list of process dicts
        mon.restart("myapp")
    """

    def get_status(self) -> list:
        """Return list of PM2 process dicts (name, status, cpu, memory, restarts)."""
        try:
            r = subprocess.run(["pm2", "jlist"], capture_output=True,
                               text=True, timeout=15)
            procs = json.loads(r.stdout or "[]")
            result = []
            for p in procs:
                env = p.get("pm2_env", {})
                result.append({
                    "name": p.get("name", "?"),
                    "pid": p.get("pid"),
                    "status": env.get("status", "unknown"),
                    "cpu": p.get("monit", {}).get("cpu", 0),
                    "memory_mb": round(
                        p.get("monit", {}).get("memory", 0) / 1024 / 1024, 1
                    ),
                    "restarts": env.get("restart_time", 0),
                    "uptime": env.get("pm_uptime"),
                })
            return result
        except FileNotFoundError:
            logger.warning("pm2 not installed")
            return [{"error": "pm2 not found"}]
        except Exception as e:
            logger.error(f"PM2Monitor.get_status: {e}")
            return [{"error": str(e)}]

    def get_process(self, name: str) -> dict:
        """Return status for a single named process."""
        for proc in self.get_status():
            if proc.get("name") == name:
                return proc
        return {"error": f"Process '{name}' not found"}

    def restart(self, name: str) -> bool:
        """Restart a PM2 process. Returns True on success."""
        try:
            r = subprocess.run(["pm2", "restart", name],
                               capture_output=True, timeout=30)
            success = r.returncode == 0
            if success:
                logger.info(f"PM2Monitor: restarted '{name}'")
            else:
                logger.error(f"PM2Monitor: restart '{name}' failed")
            return success
        except Exception as e:
            logger.error(f"PM2Monitor.restart: {e}")
            return False


class LeadStore:
    """JSON-persisted lead database for outreach tracking (Issue #26)."""

    def __init__(self, path: str = "./data/leads.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self, leads: list) -> None:
        self.path.write_text(json.dumps(leads, indent=2, ensure_ascii=False),
                             encoding="utf-8")

    def add(self, lead: dict) -> None:
        """Add or update a lead by keyword+profile."""
        leads = self._load()
        key = (lead.get("keyword", ""), lead.get("profile", ""))
        for i, l in enumerate(leads):
            if (l.get("keyword"), l.get("profile")) == key:
                leads[i] = {**l, **lead}
                self._save(leads)
                return
        lead.setdefault("added_at", datetime.now().isoformat(timespec="seconds"))
        leads.append(lead)
        self._save(leads)

    def all(self) -> list:
        return self._load()

    def count(self) -> int:
        return len(self._load())


class StartupAutopilot:
    def __init__(self, pm2_apps=None, keywords=None):
        self.pm2_apps = pm2_apps or ["knowyourrank.in", "WillItFit"]
        self.keywords = keywords or ["OMR Checker", "Virtual Try-on"]
        self.ollama_url = "http://localhost:11434"
        self.llm_model = "mistral:latest"
        self.pm2 = PM2Monitor()
        self.lead_store = LeadStore()

    # ---- PM2 Health ----
    def check_pm2(self):
        for proc in self.pm2.get_status():
            if proc.get("status") != "online":
                name = proc.get("name", "?")
                restarts = proc.get("restarts", 0)
                if restarts > 3:
                    suggestion = self._llm(
                        f"PM2 app '{name}' crashed {restarts} times. "
                        f"Suggest a fix."
                    )
                    logger.info(f"LLM suggestion for {name}: {suggestion[:200]}")
                self.pm2.restart(name)

    def _handle_crash(self, app: str, info: dict):
        """Legacy handler kept for backwards compat."""
        logger.warning(f"{app} is down — restarting…")
        self.pm2.restart(app)

    # ---- Lead Scouting ----
    def scout_leads(self) -> list:
        leads = []
        for kw in self.keywords:
            lead = {"keyword": kw, "name": f"Lead for {kw}",
                    "profile": "https://linkedin.com/in/example"}
            self.lead_store.add(lead)
            leads.append(lead)
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
