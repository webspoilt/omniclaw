#!/usr/bin/env python3
"""
exam_intelligence.py — Exam War-Room Scholar

Scrapes CAT/OSSC CGL notifications, tracks admit cards,
generates daily Physics/Quant problems based on weak areas,
and sends briefings via Telegram.

v4.2 additions (Issue #25):
  - schedule_reminders(): registers CronScheduler jobs for daily study reminders
  - generate_practice_question(topic): structured practice Q&A
  - get_next_deadline(): returns closest exam deadline as dict (used by MCP)
"""

import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

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
logger = logging.getLogger("Scholar")

CONFIG_PATH = Path(__file__).parent / "scholar_config.json"
_DEFAULTS = {
    "weak_areas": ["kinematics", "work-energy", "rotational motion"],
    "exam_sources": [],
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "llm_model": "phi3:latest",
    "ollama_url": "http://localhost:11434",
    # Issue #25 additions
    "exams": [
        {"name": "CAT 2026", "date": "2026-11-29"},
        {"name": "OSSC CGL 2026", "date": "2026-08-15"},
    ],
}


def _load_config() -> dict:
    if CONFIG_PATH.is_file():
        with open(CONFIG_PATH) as f:
            return {**_DEFAULTS, **json.load(f)}
    return dict(_DEFAULTS)


class ExamIntelligence:
    """Thin wrapper used by MCP host (Issue #25)."""

    def __init__(self):
        self._cfg = _load_config()

    def get_next_deadline(self) -> dict:
        """Return the closest upcoming exam deadline."""
        today = date.today()
        upcoming = []
        for exam in self._cfg.get("exams", []):
            try:
                d = date.fromisoformat(exam["date"])
                days_left = (d - today).days
                if days_left >= 0:
                    upcoming.append({"exam": exam["name"], "date": exam["date"],
                                     "days_left": days_left})
            except Exception:
                pass
        if not upcoming:
            return {"exam": "None scheduled", "date": "", "days_left": -1}
        upcoming.sort(key=lambda x: x["days_left"])
        return upcoming[0]


class ExamScholar:
    def __init__(self):
        cfg = _load_config()
        self.weak_areas = cfg["weak_areas"]
        self.exam_sources = cfg["exam_sources"]
        self.tg_token = cfg["telegram_bot_token"]
        self.tg_chat = cfg["telegram_chat_id"]
        self.llm_model = cfg["llm_model"]
        self.ollama_url = cfg["ollama_url"]
        self.exams = cfg.get("exams", [])

    # ---- Scraping ----
    def fetch_notifications(self) -> list:
        if not HAS_REQUESTS or not HAS_BS4:
            return []
        items = []
        for url in self.exam_sources:
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.select(".notification-item, .news-item, li"):
                    text = el.get_text(strip=True)
                    if text:
                        items.append(text)
            except Exception as e:
                logger.error(f"Scrape {url}: {e}")
        return items[:20]

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

    def generate_question(self, subject: str = "Physics") -> str:
        topic = random.choice(self.weak_areas) if self.weak_areas else "mechanics"
        return self._llm(
            f"Generate a challenging {subject} problem on '{topic}' for "
            f"competitive exam prep. Include question and step-by-step solution."
        )

    def generate_practice_question(self, topic: str = "") -> dict:
        """Generate a structured practice Q&A for the given topic (Issue #25).

        Returns:
            dict with keys: topic, question, answer, difficulty
        """
        if not topic:
            topic = random.choice(self.weak_areas) if self.weak_areas else "mechanics"
        result = self._llm(
            f"Generate a competitive exam practice question on '{topic}'. "
            f"Output JSON with keys: question, answer, difficulty (easy/medium/hard)."
        )
        try:
            import re
            m = re.search(r"\{.*\}", result, re.DOTALL)
            data = json.loads(m.group()) if m else {}
        except Exception:
            data = {}
        return {"topic": topic, **data}

    def schedule_reminders(self, cron_scheduler=None) -> None:
        """Register study reminders with CronScheduler (Issue #25).

        Args:
            cron_scheduler: Instance of ``core.scheduler.cron.CronScheduler``.
                If None, falls back to the ``schedule`` library if available.
        """
        if cron_scheduler is not None:
            # Register async cron jobs via CronScheduler
            import asyncio

            async def _register():
                # Daily briefing at 07:00
                await cron_scheduler.add_job(
                    name="ExamScholar Daily Briefing",
                    message="Run ExamScholar daily briefing and send Telegram",
                    cron_expr="0 7 * * *",
                    channel="telegram",
                )
                # Countdown every Monday 08:00
                await cron_scheduler.add_job(
                    name="Exam Countdown Reminder",
                    message="Send exam countdown reminder",
                    cron_expr="0 8 * * 1",
                    channel="telegram",
                )
                logger.info("ExamScholar: registered 2 cron reminders")

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_register())
                else:
                    loop.run_until_complete(_register())
            except Exception as e:
                logger.error(f"Failed to register cron reminders: {e}")
        elif HAS_SCHEDULE:
            schedule.every().day.at("07:00").do(self.daily_briefing)
            logger.info("ExamScholar: schedule library reminders set")
        else:
            logger.warning(
                "ExamScholar.schedule_reminders: no scheduler available. "
                "Pass a CronScheduler instance or install: pip install schedule"
            )

    # ---- Telegram ----
    def _send_tg(self, msg: str):
        if not self.tg_token or not HAS_REQUESTS:
            logger.info(f"[Telegram] {msg[:100]}…")
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.tg_token}/sendMessage",
                json={"chat_id": self.tg_chat, "text": msg,
                      "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Telegram: {e}")

    # ---- Daily Briefing ----
    def daily_briefing(self):
        if not resource_check(is_mobile=False):
            return
        check_kill_switch()

        notifs = self.fetch_notifications()
        question = self.generate_question()

        # Exam countdown
        ei = ExamIntelligence()
        deadline = ei.get_next_deadline()
        countdown = (
            f"*📅 Next Exam:* {deadline['exam']} — {deadline['days_left']} days left\n\n"
            if deadline["days_left"] >= 0 else ""
        )

        msg = f"*📚 Exam War-Room — {datetime.now():%Y-%m-%d}*\n\n"
        msg += countdown
        if notifs:
            msg += "*Notifications:*\n" + "\n".join(f"• {n}" for n in notifs[:5]) + "\n\n"
        msg += f"*Daily Problem:*\n{question}"

        self._send_tg(msg)
        logger.info("Briefing sent")

    def run(self):
        if not HAS_SCHEDULE:
            logger.error("schedule not installed")
            return
        schedule.every().day.at("07:00").do(self.daily_briefing)
        logger.info("Scholar running — briefing at 07:00 daily")
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    ExamScholar().run()


import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

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
logger = logging.getLogger("Scholar")

CONFIG_PATH = Path(__file__).parent / "scholar_config.json"
_DEFAULTS = {
    "weak_areas": ["kinematics", "work-energy", "rotational motion"],
    "exam_sources": [],
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "llm_model": "phi3:latest",
    "ollama_url": "http://localhost:11434",
}


def _load_config() -> dict:
    if CONFIG_PATH.is_file():
        with open(CONFIG_PATH) as f:
            return {**_DEFAULTS, **json.load(f)}
    return dict(_DEFAULTS)


class ExamScholar:
    def __init__(self):
        cfg = _load_config()
        self.weak_areas = cfg["weak_areas"]
        self.exam_sources = cfg["exam_sources"]
        self.tg_token = cfg["telegram_bot_token"]
        self.tg_chat = cfg["telegram_chat_id"]
        self.llm_model = cfg["llm_model"]
        self.ollama_url = cfg["ollama_url"]

    # ---- Scraping ----
    def fetch_notifications(self) -> list:
        if not HAS_REQUESTS or not HAS_BS4:
            return []
        items = []
        for url in self.exam_sources:
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.select(".notification-item, .news-item, li"):
                    text = el.get_text(strip=True)
                    if text:
                        items.append(text)
            except Exception as e:
                logger.error(f"Scrape {url}: {e}")
        return items[:20]

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

    def generate_question(self, subject: str = "Physics") -> str:
        topic = random.choice(self.weak_areas) if self.weak_areas else "mechanics"
        return self._llm(
            f"Generate a challenging {subject} problem on '{topic}' for "
            f"competitive exam prep. Include question and step-by-step solution."
        )

    # ---- Telegram ----
    def _send_tg(self, msg: str):
        if not self.tg_token or not HAS_REQUESTS:
            logger.info(f"[Telegram] {msg[:100]}…")
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.tg_token}/sendMessage",
                json={"chat_id": self.tg_chat, "text": msg,
                      "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Telegram: {e}")

    # ---- Daily Briefing ----
    def daily_briefing(self):
        if not resource_check(is_mobile=False):
            return
        check_kill_switch()

        notifs = self.fetch_notifications()
        question = self.generate_question()

        msg = f"*📚 Exam War-Room — {datetime.now():%Y-%m-%d}*\n\n"
        if notifs:
            msg += "*Notifications:*\n" + "\n".join(f"• {n}" for n in notifs[:5]) + "\n\n"
        msg += f"*Daily Problem:*\n{question}"

        self._send_tg(msg)
        logger.info("Briefing sent")

    def run(self):
        if not HAS_SCHEDULE:
            logger.error("schedule not installed")
            return
        schedule.every().day.at("07:00").do(self.daily_briefing)
        logger.info("Scholar running — briefing at 07:00 daily")
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    ExamScholar().run()
