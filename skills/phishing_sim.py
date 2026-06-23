# ruff: noqa: E741
"""Phishing simulation: email template crafting, sender spoofing, click rate analysis."""
from __future__ import annotations

import subprocess
from pathlib import Path

from core.skills.registry import tool


@tool()
def craft_email_template(target_name: str, pretext: str = "security_update") -> str:
    """Generate a phishing email template for testing internal awareness."""
    try:
        pretexts = {
            "security_update": {
                "subject": "Action Required: Security Update for Your Account",
                "body": (
                    f"Dear {target_name},\n\n"
                    "Our security team has detected unusual activity on your account. "
                    "Please click the link below to verify your credentials and secure your account:\n\n"
                    "https://secure-update-portal.com/verify\n\n"
                    "This request will expire in 24 hours.\n\n"
                    "Thank you,\nIT Security Team"
                ),
            },
            "password_expiry": {
                "subject": "Your Password Will Expire in 24 Hours",
                "body": (
                    f"Hi {target_name},\n\n"
                    "Your network password is scheduled to expire tomorrow. "
                    "Please keep your current credentials or reset them here:\n\n"
                    "https://mail-portal-reset.com/renew\n\n"
                    "If you do nothing, your access will be suspended.\n\n"
                    "Regards,\nIT Support"
                ),
            },
            "invoice": {
                "subject": "Overdue Invoice — Immediate Payment Required",
                "body": (
                    f"Dear {target_name},\n\n"
                    "Our records indicate that invoice #INV-{int(time.time()) % 100000} "
                    "is overdue. Please review and process payment at your earliest convenience:\n\n"
                    "https://billing-portal-view.com/invoice\n\n"
                    "Late payment may result in service interruption.\n\n"
                    "Best regards,\nAccounts Department"
                ),
            },
            "package_delivery": {
                "subject": "Package Delivery Notification — Action Required",
                "body": (
                    f"Hello {target_name},\n\n"
                    "A package addressed to you is awaiting delivery confirmation. "
                    "Please confirm your delivery details:\n\n"
                    "https://package-delivery-portal.com/confirm\n\n"
                    "If not claimed within 48 hours, the package will be returned.\n\n"
                    "Sincerely,\nLogistics Team"
                ),
            },
        }
        if pretext not in pretexts:
            return f"Unknown pretext '{pretext}'. Available: {', '.join(pretexts)}"
        template = pretexts[pretext]
        return (
            f"Phishing email template ({pretext}):\n"
            f"  To: {target_name}\n"
            f"  Subject: {template['subject']}\n"
            f"  Body:\n{template['body']}\n"
        )
    except Exception as e:
        return f"Template crafting failed: {e}"


@tool()
def spoof_sender(email_content: str, sender: str = "admin@company.com") -> str:
    """Attempt to send an email with a spoofed sender using sendmail or mail (local MTA only)."""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".eml", delete=False) as f:
            f.write(f"From: {sender}\n")
            f.write(email_content)
            msg_path = f.name
        proc = subprocess.run(  # noqa: S603
            ["sendmail", "-t"], input=email_content.encode(), capture_output=True,  # noqa: S607
            text=True, timeout=15,
        )
        Path(msg_path).unlink(missing_ok=True)
        if proc.returncode == 0:
            return f"Email sent from '{sender}' via sendmail"
        try:
            proc = subprocess.run(  # noqa: S603
                ["mail", "-s", "Test", "-a", f"From: {sender}"],  # noqa: S607
                input=email_content, capture_output=True, text=True, timeout=15,
            )
            if proc.returncode == 0:
                return f"Email sent from '{sender}' via mail command"
        except FileNotFoundError:
            pass
        return f"Sendmail failed: {proc.stderr.strip()[:300]}"
    except FileNotFoundError:
        return "sendmail/mail not available on this system"
    except Exception as e:
        return f"Spoofing failed: {e}"


@tool()
def analyze_click_rate(log_path: str = "") -> str:
    """Analyze a simulated phishing campaign log for click-through rates."""
    try:
        if log_path:
            p = Path(log_path)
            if not p.exists():
                return f"Log file not found: {log_path}"
            content = p.read_text()
        else:
            content = ""
        total_sent = sum(1 for l in content.splitlines() if "SENT" in l) if content else 0
        total_clicked = sum(1 for l in content.splitlines() if "CLICKED" in l) if content else 0
        if not content:
            return (
                "No log provided. To analyze, provide a log file path with lines containing "
                "'SENT' and 'CLICKED' markers.\n"
                "Example log format:\n"
                "  [2024-01-01] SENT target@company.com\n"
                "  [2024-01-02] CLICKED target@company.com"
            )
        rate = total_clicked / total_sent * 100 if total_sent > 0 else 0
        return (
            f"Phishing campaign analysis:\n"
            f"  Total sent: {total_sent}\n"
            f"  Total clicked: {total_clicked}\n"
            f"  Click rate: {rate:.1f}%\n"
            f"  Risk level: {'HIGH' if rate > 30 else 'MEDIUM' if rate > 10 else 'LOW'}"
        )
    except Exception as e:
        return f"Click rate analysis failed: {e}"
