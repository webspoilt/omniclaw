import datetime
import json
from typing import Dict, List, Optional

class RemediationPipeline:
    """
    Maps vulnerability types to OWASP fixes and generates a Markdown report.
    """

    # OWASP-based remediation dictionary (extend as needed)
    REMEDIATIONS = {
        "SQLi": {
            "name": "SQL Injection",
            "fix": "Use parameterised queries / prepared statements. Apply strict input validation and least privilege database accounts.",
            "owasp": "https://owasp.org/www-community/attacks/SQL_Injection"
        },
        "IDOR": {
            "name": "Insecure Direct Object Reference",
            "fix": "Implement proper access control checks. Use indirect object references (e.g., random IDs) and validate user permissions on every request.",
            "owasp": "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References"
        },
        "XSS": {
            "name": "Cross-Site Scripting",
            "fix": "Escape all untrusted data before insertion. Use Content Security Policy (CSP) and framework auto-escaping.",
            "owasp": "https://owasp.org/www-community/attacks/xss/"
        },
        "Prompt Injection": {
            "name": "LLM Prompt Injection",
            "fix": "Restrict system prompts with strong delimiters; validate and sanitise user inputs; use output encoding; implement a secondary validation layer.",
            "owasp": "https://owasp.org/www-project-top-10-for-large-language-model-applications/"
        }
    }

    REPORT_TEMPLATE = """# Vulnerability Disclosure Report

**Title:** {title}  
**Date:** {date}  
**Researcher:** {researcher}  
**Affected Component:** {component}  
**CVSS Score:** {cvss} (if available)

---

## 1. Technical Description
{technical_description}

---

## 2. Impact
{impact}

---

## 3. Remediation Steps
{remediation}

**Reference:** {reference}

---

*This report is based on authorised security testing and is intended for the system owner only.*
"""

    def __init__(self, researcher_name: str = "OmniClaw Auditor"):
        self.researcher = researcher_name

    def generate_report(self, vuln_type: str, component: str,
                        technical_description: str, impact: str,
                        cvss: str = "N/A") -> str:
        """
        Generate a complete report for a given vulnerability type.
        """
        vuln_info = self.REMEDIATIONS.get(vuln_type, {
            "name": vuln_type,
            "fix": "No standard remediation available. Consult OWASP guidelines.",
            "owasp": "#"
        })
        title = f"{vuln_info['name']} in {component}"
        remediation = vuln_info['fix']
        reference = vuln_info['owasp']
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        return self.REPORT_TEMPLATE.format(
            title=title,
            date=date,
            researcher=self.researcher,
            component=component,
            cvss=cvss,
            technical_description=technical_description,
            impact=impact,
            remediation=remediation,
            reference=reference
        )

    def save_report(self, content: str, output_path: str) -> str:
        """Save the Markdown report to a file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_path

# Example usage
if __name__ == "__main__":
    pipeline = RemediationPipeline()
    report = pipeline.generate_report(
        vuln_type="IDOR",
        component="/api/user/{id}",
        technical_description="Authenticated user A could access user B's profile by changing the ID parameter.",
        impact="Unauthorised access to personal data of other users."
    )
    print(report)
