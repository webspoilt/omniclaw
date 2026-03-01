#!/usr/bin/env python3
"""
scout_agent.py - Automated Security Reconnaissance for OmniClaw

Integrates subfinder, nmap, nuclei (and extensible tools) with
LLM-powered vulnerability analysis and instant alerting.

Features:
  - Target validation (blocklist: IPs, domains, CIDRs)
  - Modular tool integration (standard interface, easy to extend)
  - LLM analysis (Ollama or OpenAI) — identifies low-hanging fruit
  - Markdown vulnerability report generation
  - Instant alerts (Telegram / Discord) for HIGH/CRITICAL findings
  - Safety-first: exits immediately on blocklisted targets
"""

import os
import sys
import re
import json
import time
import ipaddress
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ------------------------------------------------------------------ #
#  Logging                                                            #
# ------------------------------------------------------------------ #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ScoutAgent")

# ------------------------------------------------------------------ #
#  Configuration                                                      #
# ------------------------------------------------------------------ #
CONFIG_FILE = os.environ.get("SCOUT_CONFIG", "scout_config.yaml")

_DEFAULT_CONFIG = {
    "blocklist": ["127.0.0.1", "192.168.0.0/16", "10.0.0.0/8", "localhost"],
    "tools": {},
    "llm": {"provider": "ollama", "model": "llama2:latest",
            "ollama_url": "http://localhost:11434", "openai_api_key": ""},
    "notification": {},
    "report": {"output_dir": "./reports"},
}


def load_config() -> dict:
    if HAS_YAML and os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return {**_DEFAULT_CONFIG, **yaml.safe_load(f)}
    return dict(_DEFAULT_CONFIG)


config = load_config()
BLOCKLIST           = config.get("blocklist", [])
TOOLS_CONFIG        = config.get("tools", {})
LLM_CONFIG          = config.get("llm", {})
NOTIFICATION_WH     = config.get("notification", {})
REPORT_DIR          = Path(config.get("report", {}).get("output_dir", "./reports"))
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ #
#  Blocklist Validation                                               #
# ------------------------------------------------------------------ #
def is_blocked(target: str) -> bool:
    """Check if target overlaps any blocklist entry (IP, CIDR, or domain)."""
    # Try IP / CIDR match
    try:
        tnet = ipaddress.ip_network(target, strict=False)
        for bl in BLOCKLIST:
            try:
                bnet = ipaddress.ip_network(bl, strict=False)
                if tnet.overlaps(bnet):
                    return True
            except ValueError:
                continue
    except ValueError:
        # target is a domain
        for bl in BLOCKLIST:
            if bl.lower() in target.lower():
                return True
    return False


# ------------------------------------------------------------------ #
#  LLM Interaction                                                    #
# ------------------------------------------------------------------ #
def query_llm(prompt: str) -> Optional[str]:
    if not HAS_REQUESTS:
        logger.error("requests not installed")
        return None

    provider = LLM_CONFIG.get("provider", "ollama")
    model = LLM_CONFIG.get("model", "llama2:latest")

    if provider == "ollama":
        url = LLM_CONFIG.get("ollama_url", "http://localhost:11434") + "/api/generate"
        try:
            r = requests.post(url, json={"model": model, "prompt": prompt,
                                          "stream": False}, timeout=120)
            r.raise_for_status()
            return r.json().get("response")
        except Exception as e:
            logger.error(f"Ollama: {e}")
            return None

    elif provider == "openai":
        try:
            import openai
            openai.api_key = LLM_CONFIG.get("openai_api_key")
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000, temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI: {e}")
            return None
    return None


def analyze_with_llm(tool_outputs: Dict[str, str],
                     target: str) -> Dict[str, Any]:
    """
    Send all tool outputs to LLM for vulnerability analysis.
    Expects JSON: { summary, findings: [{title, severity, description, remediation}] }
    """
    prompt = (
        f"You are a security expert analyzing recon results for: {target}\n\n"
        "Identify low-hanging-fruit vulnerabilities. For each finding provide:\n"
        "- title\n- severity (LOW, MEDIUM, HIGH, CRITICAL)\n"
        "- description\n- remediation\n\n"
        "Output as JSON: {\"summary\": \"...\", \"findings\": [...]}\n\n"
        "Tool outputs:\n"
    )
    for name, out in tool_outputs.items():
        prompt += f"\n--- {name} ---\n{out}\n"
    prompt += "\nJSON response:"

    resp = query_llm(prompt)
    if not resp:
        return {"summary": "LLM analysis failed", "findings": []}

    # Extract JSON block
    m = re.search(r"```json\n(.*?)\n```", resp, re.DOTALL)
    raw = m.group(1) if m else resp.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM output is not valid JSON")
        return {"summary": "Parse error", "findings": []}


# ------------------------------------------------------------------ #
#  Tool Base                                                          #
# ------------------------------------------------------------------ #
class SecurityTool:
    """Base class — all tools share this run() interface."""

    def __init__(self, name: str, cfg: dict):
        self.name = name
        self.cmd = cfg.get("cmd", name)
        self.timeout = cfg.get("timeout", 60)
        self.args = cfg.get("args", [])
        self.enabled = cfg.get("enabled", True)

    def run(self, target: str) -> Optional[str]:
        if not self.enabled:
            logger.info(f"{self.name} disabled, skipping")
            return None
        cmd = [self.cmd] + self.args + [target]
        logger.info(f"Running: {' '.join(cmd)}")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=self.timeout, check=False)
            out = r.stdout
            if r.stderr:
                out += f"\n[stderr]\n{r.stderr}"
            return out
        except subprocess.TimeoutExpired:
            return f"[ERROR] Timeout ({self.timeout}s)"
        except FileNotFoundError:
            return f"[ERROR] {self.cmd} not found"
        except Exception as e:
            return f"[ERROR] {e}"


class SubfinderTool(SecurityTool):
    """Subdomain discovery."""
    pass


class NmapTool(SecurityTool):
    """Port scanner."""
    pass


class NucleiTool(SecurityTool):
    """Vulnerability scanner."""
    pass


# ------------------------------------------------------------------ #
#  Scout Agent                                                        #
# ------------------------------------------------------------------ #
class ScoutAgent:
    TOOL_MAP = {
        "subfinder": SubfinderTool,
        "nmap": NmapTool,
        "nuclei": NucleiTool,
    }

    def __init__(self, cfg: dict):
        self.target: Optional[str] = None
        self.results: Dict[str, str] = {}
        self.tools: Dict[str, SecurityTool] = {}

        for name, tcfg in cfg.get("tools", {}).items():
            cls = self.TOOL_MAP.get(name, SecurityTool)
            if tcfg.get("enabled", True):
                self.tools[name] = cls(name, tcfg)

    def validate_target(self, target: str) -> bool:
        if is_blocked(target):
            logger.error(f"BLOCKED: {target}")
            return False
        if not target or " " in target:
            logger.error(f"Invalid target: {target}")
            return False
        return True

    def run_scan(self, target: str):
        self.target = target
        self.results = {}
        for name, tool in self.tools.items():
            logger.info(f"▶ {name}")
            out = tool.run(target)
            if out:
                self.results[name] = out
            logger.info(f"✓ {name}")

    def analyze(self) -> Dict[str, Any]:
        if not self.results:
            return {"summary": "No data", "findings": []}
        return analyze_with_llm(self.results, self.target or "unknown")

    def generate_report(self, analysis: Dict[str, Any]) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rpt = REPORT_DIR / f"vulnerability_report_{ts}.md"

        with open(rpt, "w") as f:
            f.write(f"# Vulnerability Scan Report — {self.target}\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n\n")
            f.write(analysis.get("summary", "N/A") + "\n\n")

            f.write("## Findings\n\n")
            findings = analysis.get("findings", [])
            if findings:
                for i, fd in enumerate(findings, 1):
                    sev = fd.get("severity", "UNKNOWN").upper()
                    f.write(f"### {i}. {fd.get('title', 'Untitled')} ({sev})\n\n")
                    f.write(f"**Description:** {fd.get('description', '')}\n\n")
                    f.write(f"**Remediation:** {fd.get('remediation', '')}\n\n")
            else:
                f.write("No vulnerabilities identified.\n\n")

            f.write("## Raw Tool Outputs\n\n")
            for name, out in self.results.items():
                f.write(f"### {name}\n\n```\n{out}\n```\n\n")

        logger.info(f"Report → {rpt}")
        return rpt

    def send_alerts(self, analysis: Dict[str, Any], report: Path):
        """Alert on HIGH/CRITICAL findings via Telegram/Discord."""
        if not HAS_REQUESTS:
            return
        critical = [f for f in analysis.get("findings", [])
                     if f.get("severity", "").upper() in ("HIGH", "CRITICAL")]
        if not critical:
            logger.info("No critical findings — skipping alert")
            return

        msg = f"🚨 *Scout Alert for {self.target}*\n\n"
        msg += f"Found {len(critical)} HIGH/CRITICAL issue(s):\n"
        for fd in critical:
            msg += f"- *{fd.get('title')}* ({fd.get('severity')})\n"
        msg += f"\nReport: {report.name}"

        for svc, url in NOTIFICATION_WH.items():
            try:
                if svc == "telegram":
                    requests.post(url, json={"text": msg,
                                              "parse_mode": "Markdown"}, timeout=10)
                elif svc == "discord":
                    requests.post(url, json={"content": msg}, timeout=10)
                else:
                    requests.post(url, json={"text": msg}, timeout=10)
            except Exception as e:
                logger.error(f"Alert to {svc}: {e}")


# ------------------------------------------------------------------ #
#  Main                                                               #
# ------------------------------------------------------------------ #
def main(target: str):
    agent = ScoutAgent(config)

    if not agent.validate_target(target):
        sys.exit(1)

    agent.run_scan(target)
    analysis = agent.analyze()
    report = agent.generate_report(analysis)
    agent.send_alerts(analysis, report)
    logger.info("Scout agent finished")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: scout_agent.py <target_domain_or_ip>")
        sys.exit(1)
    main(sys.argv[1])
