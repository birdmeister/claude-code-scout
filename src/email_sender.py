"""
E-mailmodule — verstuurt het weekrapport per e-mail.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_report(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    from_address: str,
    to_address: str,
    subject_prefix: str,
    report_markdown: str,
) -> bool:
    """
    Verstuur het rapport per e-mail als plain text (Markdown).

    Returns True als het versturen gelukt is.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"{subject_prefix} Weekrapport {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    # Markdown als plain text
    msg.attach(MIMEText(report_markdown, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        logger.info(f"Rapport verstuurd naar {to_address}")
        return True
    except Exception as e:
        logger.error(f"E-mail versturen mislukt: {e}")
        return False
