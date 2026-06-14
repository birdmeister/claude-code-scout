"""
E-mailmodule — verstuurt het weekrapport per e-mail via Resend of SMTP.
"""

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _send_via_resend(
    from_address: str,
    to_address: str,
    subject: str,
    body: str,
    api_key: str,
) -> bool:
    import resend

    resend.api_key = api_key
    resend.Emails.send({
        "from": from_address,
        "to": [to_address],
        "subject": subject,
        "text": body,
    })
    return True


def _send_via_smtp(
    from_address: str,
    to_address: str,
    subject: str,
    body: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> bool:
    msg = EmailMessage()
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    return True


def send_report(
    from_address: str,
    to_address: str,
    subject_prefix: str,
    report_markdown: str,
    provider: str = "resend",
    api_key: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int = 587,
    smtp_user: str | None = None,
    smtp_password: str | None = None,
) -> bool:
    """
    Verstuur het rapport per e-mail als plain text (Markdown).

    provider: "resend" of "smtp"
    Returns True als het versturen gelukt is.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"{subject_prefix} Weekrapport {date_str}"

    try:
        if provider == "smtp":
            _send_via_smtp(
                from_address=from_address,
                to_address=to_address,
                subject=subject,
                body=report_markdown,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_user=smtp_user,
                smtp_password=smtp_password,
            )
        else:
            _send_via_resend(
                from_address=from_address,
                to_address=to_address,
                subject=subject,
                body=report_markdown,
                api_key=api_key,
            )
        logger.info(f"Rapport verstuurd naar {to_address} via {provider}")
        return True
    except Exception as e:
        logger.error(f"E-mail versturen mislukt: {e}")
        return False
