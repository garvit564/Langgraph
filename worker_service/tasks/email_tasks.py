import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from worker_service.celery_app import celery_app
from worker_service.config import get_worker_settings

logger = logging.getLogger(__name__)
settings = get_worker_settings()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_email_task(self, to_email: str, subject: str, body: str) -> dict:
    """Dispatches an email asynchronously via SMTP with automatic retry logic.
    Supports both plain text and HTML content formatting.
    """
    logger.info("Background Worker: Processing email dispatch to: %s (Subject: '%s')", to_email, subject)

    if not settings.smtp_user or not settings.smtp_password:
        err_msg = "SMTP credentials not configured in Worker service."
        logger.error(err_msg)
        return {"status": "failed", "error": err_msg}

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from_email or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject

    text_part = MIMEText(body, "plain", "utf-8")
    html_content = f"""<!DOCTYPE html>
<html>
  <head><meta charset="utf-8"></head>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 24px;">
      <h2 style="color: #2b6cb0; margin-top: 0;">Agent Desk Notification</h2>
      <div style="white-space: pre-wrap; font-size: 15px; color: #2d3748;">{body}</div>
      <hr style="margin-top: 32px; border: none; border-top: 1px solid #edf2f7;">
      <p style="font-size: 12px; color: #a0aec0; margin-bottom: 0;">Dispatched by Agent Desk Worker Microservice (Port 8001).</p>
    </div>
  </body>
</html>"""
    html_part = MIMEText(html_content, "html", "utf-8")

    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        logger.info("Background Worker: Email successfully delivered to: %s", to_email)
        return {
            "status": "delivered",
            "to": to_email,
            "subject": subject,
        }

    except smtplib.SMTPException as exc:
        logger.warning("SMTP transmission error sending to %s: %s. Retrying...", to_email, exc)
        raise self.retry(exc=exc)

    except Exception as exc:
        logger.exception("Unexpected exception occurred during email dispatch to %s: %s", to_email, exc)
        return {
            "status": "failed",
            "error": str(exc),
        }
