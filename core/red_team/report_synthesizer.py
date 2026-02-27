import datetime
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ReportSynthesizer:
    """
    Creates a Markdown disclosure report from vulnerability findings.
    """

    REPORT_TEMPLATE = """# Security Disclosure Report

**Title:** {title}  
**Date:** {date}  
**Researcher:** {researcher}  
**Affected Component:** {component}  
**CVSS Severity:** {severity} (CVSS:{cvss_vector})

---

## 1. Executive Summary
{executive_summary}

---

## 2. Technical Breakdown
{technical_breakdown}

---

## 3. Impact
{impact}

---

## 4. Remediation Steps
{remediation}

---

## 5. Proof of Concept
{poc_references}

---

{disclaimer}
"""

    DISCLAIMER = (
        "*This report is confidential and intended solely for the authorised recipient. "
        "The findings described herein were obtained during authorised security testing conducted with "
        "explicit permission. Unauthorised distribution or use is prohibited.*"
    )

    def __init__(self, researcher_name: str = "OmniClaw Auditor"):
        self.researcher = researcher_name

    def generate(self, title: str, component: str, severity: str, cvss_vector: str,
                 executive_summary: str, technical_breakdown: str, impact: str,
                 remediation: str, poc_files: List[str]) -> str:
        """
        Generate the full Markdown report.
        """
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        poc_refs = "\n".join(f"- `{f}`" for f in poc_files) if poc_files else "No PoC files attached."

        return self.REPORT_TEMPLATE.format(
            title=title,
            date=date,
            researcher=self.researcher,
            component=component,
            severity=severity,
            cvss_vector=cvss_vector,
            executive_summary=executive_summary,
            technical_breakdown=technical_breakdown,
            impact=impact,
            remediation=remediation,
            poc_references=poc_refs,
            disclaimer=self.DISCLAIMER
        )

    def save(self, content: str, output_path: str) -> str:
        """Save the report to a file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report saved: {output_path}")
        return output_path
