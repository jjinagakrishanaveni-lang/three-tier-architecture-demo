import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any

from .config import settings
from .redis_client import store_simulated_email

logger = logging.getLogger("uvicorn.error")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@fastapiapp.local")

def send_verification_email(email: str, name: str, token: str) -> Dict[str, Any]:
    """
    Requirement 2: Send email verification link to user's email address.
    Generates verification URL, logs for container inspection, and records for local testability.
    """
    verification_url = f"{settings.FRONTEND_URL}/#verify?token={token}"
    
    subject = "Verify your email address"
    body_text = f"""Hello {name},

Thank you for registering! Please verify your email address by opening the following link:

{verification_url}

This verification link will expire in {settings.PENDING_REGISTRATION_TTL // 60} minutes.

If you did not register for this account, please ignore this email.
"""

    body_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #4f46e5;">Welcome to FastAPI WebApp, {name}!</h2>
        <p>Thank you for signing up. Please verify your email address to activate your account.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Verify Email Address</a>
        </div>
        <p style="color: #64748b; font-size: 14px;">Or copy and paste this URL into your browser:</p>
        <p style="background: #f8fafc; padding: 10px; border-radius: 4px; word-break: break-all; font-size: 13px; color: #334155;">{verification_url}</p>
        <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">This link will expire in {settings.PENDING_REGISTRATION_TTL // 60} minutes.</p>
    </div>
    """

    email_record = {
        "to_email": email,
        "name": name,
        "token": token,
        "verification_url": verification_url,
        "sent_at": datetime.utcnow().isoformat(),
        "subject": subject,
        "preview_text": f"Click the link to verify account for {email}",
    }

    # Record in Redis dev mailbox
    try:
        store_simulated_email(email_record)
    except Exception as e:
        logger.warning(f"Could not save simulated email to Redis: {e}")

    # Log to Docker logs
    logger.info("=" * 60)
    logger.info(f" [EMAIL DISPATCHED] To: {email} | Subject: {subject}")
    logger.info(f" Verification Link: {verification_url}")
    logger.info("=" * 60)

    # Optional real SMTP delivery if configured
    if SMTP_HOST and SMTP_USER:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM
            msg["To"] = email
            msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [email], msg.as_string())
            logger.info(f"Actual email delivered to {email} via SMTP.")
        except Exception as err:
            logger.error(f"Failed to deliver SMTP email: {err}. Simulated email link is still valid in logs.")

    return email_record
