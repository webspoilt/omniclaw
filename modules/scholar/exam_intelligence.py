#!/usr/bin/env python3
"""
exam_intelligence.py — Exam War-Room Scholar

Scrapes CAT/OSSC CGL notifications, tracks admit cards,
generates daily Physics/Quant problems based on weak areas,
and sends briefings via Telegram.
"""

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
