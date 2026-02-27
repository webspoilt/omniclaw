#!/usr/bin/env python3
"""
Responsible Disclosure Module for OmniClaw.
Handles evidence encryption, professional report generation, and remediation suggestions.
All operations assume explicit authorisation for security testing.
"""

import os
import json
import datetime
from cryptography.fernet import Fernet
from typing import Dict, Any, Optional, List

# ----------------------------------------------------------------------
# Remediation dictionary (vulnerability -> recommended fix)
# ----------------------------------------------------------------------
REMEDIATION_MAP = {
    "SQLi": {
        "description": "SQL Injection (SQLi)",
        "fix": "Use parameterised queries / prepared statements. Validate and sanitise all user inputs. Apply the principle of least privilege on database accounts."
    },
    "XSS": {
        "description": "Cross‑Site Scripting (XSS)",
        "fix": "Implement Content Security Policy (CSP). Escape all untrusted data before inserting into HTML. Use framework‑specific auto‑escaping (e.g., Jinja2, React)."
    },
    "Prompt Injection": {
        "description": "Prompt Injection (LLM context manipulation)",
        "fix": "Restrict system prompt boundaries with delimiters. Validate and sanitise user inputs. Use input filtering and output encoding. Implement a secondary validation layer."
    },
    # Extend as needed
}

# ----------------------------------------------------------------------
# Evidence Capture (Encrypted)
# ----------------------------------------------------------------------
class EvidenceCapture:
    """
    Handles secure storage of payload responses.
    Uses Fernet symmetric encryption; the key must be stored securely
    (e.g., environment variable or secrets manager).
    """

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialise the encryptor. If no key is provided, generate a new one.
        In production, load the key from a secure location.
        """
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        self.cipher = Fernet(self.key)

    def save_encrypted_evidence(self, payload_response: str, vuln_type: str,
                                metadata: Optional[Dict] = None,
                                output_dir: str = "./evidence") -> str:
        """
        Encrypt the payload response and save it with a timestamp.
        Returns the full path of the saved file.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Build metadata object
        record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "vulnerability_type": vuln_type,
            "metadata": metadata or {},
            "payload_response": payload_response
        }

        # Serialise to JSON and encrypt
        plaintext = json.dumps(record, indent=2).encode('utf-8')
        encrypted = self.cipher.encrypt(plaintext)

        # Generate filename
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_{vuln_type}_{ts}.enc"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(encrypted)

        print(f"[+] Encrypted evidence saved: {filepath}")
        return filepath

    def decrypt_evidence(self, filepath: str) -> Dict:
        """Decrypt an evidence file and return the original dictionary."""
        with open(filepath, 'rb') as f:
            encrypted = f.read()
        plaintext = self.cipher.decrypt(encrypted)
        return json.loads(plaintext.decode('utf-8'))

# ----------------------------------------------------------------------
# Report Generator
# ----------------------------------------------------------------------
class ReportGenerator:
    """
    Generates professional vulnerability research reports in Markdown.
    Optionally converts Markdown to PDF (requires additional tools).
    """

    # Template for the report
    REPORT_TEMPLATE = """# Vulnerability Research Report

**Title:** {title}  
**Date:** {date}  
**Authorised Tester:** {tester}  
**Target:** {target}

---

## 1. Executive Summary
{executive_summary}

---

## 2. Technical Breakdown
{technical_breakdown}

---

## 3. Remediation Recommendations
{remediation_suggestions}

---

{disclaimer}
"""

    def __init__(self, tester_name: str = "OmniClaw Operator"):
        self.tester_name = tester_name

    @staticmethod
    def _generate_remediation_suggestions(findings: List[Dict]) -> str:
        """
        Convert a list of findings into a formatted remediation section.
        Each finding should have a 'vuln_type' key.
        """
        lines = []
        for idx, f in enumerate(findings, 1):
            vuln_type = f.get('vuln_type', 'Unknown')
            description = f.get('description', '')
            remediation = REMEDIATION_MAP.get(vuln_type, {}).get('fix', 'No standard remediation available.')
            lines.append(f"**{idx}. {vuln_type}**")
            if description:
                lines.append(f"   - *Description:* {description}")
            lines.append(f"   - *Recommended Fix:* {remediation}\n")
        return "\n".join(lines) if lines else "No remediation data available."

    @staticmethod
    def _generate_disclaimer() -> str:
        """Legal disclaimer footer for the report."""
        return (
            "---\n"
            "*This report is confidential and intended solely for the use of the authorised recipient. "
            "The findings described herein were obtained during authorised security testing performed with "
            "explicit permission. Unauthorised distribution or use of this information is prohibited.*"
        )

    def generate_markdown(self, title: str, target: str,
                         executive_summary: str, technical_breakdown: str,
                         findings: List[Dict]) -> str:
        """
        Generate a complete report in Markdown format.
        """
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        remediation = self._generate_remediation_suggestions(findings)
        disclaimer = self._generate_disclaimer()

        return self.REPORT_TEMPLATE.format(
            title=title,
            date=date_str,
            tester=self.tester_name,
            target=target,
            executive_summary=executive_summary,
            technical_breakdown=technical_breakdown,
            remediation_suggestions=remediation,
            disclaimer=disclaimer
        )

    def save_markdown(self, content: str, filepath: str) -> None:
        """Save the Markdown content to a file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[+] Markdown report saved: {filepath}")

    def convert_to_pdf(self, markdown_path: str, pdf_path: str) -> None:
        """
        Convert a Markdown file to PDF.
        Requires 'markdown' and 'pdfkit' (with wkhtmltopdf) or 'weasyprint'.
        This example uses weasyprint.
        """
        try:
            from weasyprint import HTML
            import markdown
        except ImportError:
            print("[-] 'weasyprint' or 'markdown' not installed. Install with: pip install weasyprint markdown")
            return

        # Read markdown, convert to HTML, then to PDF
        with open(markdown_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=['extra'])
        HTML(string=html_content).write_pdf(pdf_path)
        print(f"[+] PDF report saved: {pdf_path}")

# ----------------------------------------------------------------------
# Convenience Wrapper
# ----------------------------------------------------------------------
class ResponsibleDisclosureModule:
    """
    High‑level interface combining evidence capture and report generation.
    """

    def __init__(self, encryption_key: Optional[bytes] = None, tester_name: str = "OmniClaw Operator"):
        self.evidence = EvidenceCapture(encryption_key)
        self.report = ReportGenerator(tester_name)

    def handle_finding(self, payload_response: str, vuln_type: str,
                       metadata: Dict, finding_details: Dict,
                       target: str, executive_summary: str,
                       technical_breakdown: str, output_dir: str = "./reports") -> Dict:
        """
        Complete workflow:
        1. Encrypt and save evidence.
        2. Generate a report (Markdown) with the finding.
        3. Optionally convert to PDF (commented out by default).
        Returns paths to evidence and report.
        """
        # 1. Save evidence
        evidence_path = self.evidence.save_encrypted_evidence(
            payload_response, vuln_type, metadata,
            output_dir=os.path.join(output_dir, "evidence")
        )

        # 2. Prepare findings list (could be multiple, here single)
        findings = [{
            "vuln_type": vuln_type,
            "description": finding_details.get("description", ""),
            "evidence_file": evidence_path
        }]

        # 3. Generate report
        title = f"{vuln_type} Vulnerability in {target}"
        markdown_content = self.report.generate_markdown(
            title=title,
            target=target,
            executive_summary=executive_summary,
            technical_breakdown=technical_breakdown,
            findings=findings
        )

        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        md_path = os.path.join(output_dir, f"report_{vuln_type}_{ts}.md")
        self.report.save_markdown(markdown_content, md_path)

        # Optional: generate PDF
        # pdf_path = os.path.join(output_dir, f"report_{vuln_type}_{ts}.pdf")
        # self.report.convert_to_pdf(md_path, pdf_path)

        return {
            "evidence": evidence_path,
            "report_md": md_path
        }

# ----------------------------------------------------------------------
# Example usage (standalone)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simulated finding
    payload = "<!-- leaked system prompt: You are an AI assistant... -->"
    vuln = "Prompt Injection"
    meta = {"url": "https://example.com/chat", "method": "POST"}
    details = {"description": "Attacker injected a new system directive via user prompt."}
    target = "example.com"
    exec_summary = "The application's LLM component accepted unverified user input that altered the system prompt, potentially leading to unauthorised actions."
    tech_breakdown = "The endpoint /chat accepts a 'prompt' parameter without sanitisation. By sending a specially crafted prompt containing 'Ignore previous instructions...', the system prompt was overwritten."

    module = ResponsibleDisclosureModule()
    result = module.handle_finding(
        payload_response=payload,
        vuln_type=vuln,
        metadata=meta,
        finding_details=details,
        target=target,
        executive_summary=exec_summary,
        technical_breakdown=tech_breakdown
    )

    print("\n[+] Disclosure package created:")
    print(f"    Evidence: {result['evidence']}")
    print(f"    Report: {result['report_md']}")
