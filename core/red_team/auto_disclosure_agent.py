import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

class AutoDisclosureAgent:
    """
    Sends vulnerability reports via SMTP with a legal disclaimer.
    """

    # Default disclaimer appended to email body
    EMAIL_DISCLAIMER = """
---
IMPORTANT: This email and any attachments are confidential and intended solely for the use of the individual or entity to whom they are addressed. If you are not the intended recipient, you are hereby notified that any dissemination, distribution, or copying of this communication is strictly prohibited. This communication is from a security researcher performing authorized testing. If you have received this in error, please notify the sender immediately.
"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str,
                 use_tls: bool = True, from_addr: str = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_addr = from_addr or username

    def send_report(self, to_addr: str, subject: str, body: str,
                    attachments: Optional[List[str]] = None) -> bool:
        """
        Send the report email with attachments.
        """
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject

        # Attach body with disclaimer
        full_body = body + self.EMAIL_DISCLAIMER
        msg.attach(MIMEText(full_body, 'plain'))

        # Attach files
        if attachments:
            for file_path in attachments:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{os.path.basename(file_path)}"'
                        )
                        msg.attach(part)

        # Send email
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Report sent to {to_addr}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
