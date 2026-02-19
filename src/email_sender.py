"""
E-mailmodule — verstuurt het weekrapport per e-mail via Resend.
"""

import logging
from datetime import datetime

import resend

logger = logging.getLogger(__name__)


def send_report(
    api_key: str,
    from_address: str,
    to_address: str,
    subject_prefix: str,
    report_markdown: str,
) -> bool:
    """
    Verstuur het rapport per e-mail als plain text (Markdown) via Resend.

    Returns True als het versturen gelukt is.
    """
    resend.api_key = api_key
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"{subject_prefix} Weekrapport {date_str}"

    try:
        resend.Emails.send({
            "from": from_address,
            "to": [to_address],
            "subject": subject,
            "text": report_markdown,
        })
        logger.info(f"Rapport verstuurd naar {to_address}")
        return True
    except Exception as e:
        logger.error(f"E-mail versturen mislukt: {e}")
        return False
