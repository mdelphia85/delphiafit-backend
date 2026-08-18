"""Minimal SMTP delivery helpers used by password-reset and invitation flows.

All SMTP settings are environment-driven. If SMTP is not configured the helper
returns False; callers still return generic responses so account existence is not
leaked. Production should configure SMTP_HOST/SMTP_PORT/SMTP_FROM and credentials.
"""

from email.message import EmailMessage
import os
import smtplib
import ssl


def _send_email(to_address: str, subject: str, text: str) -> bool:
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        return False

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_ssl = os.getenv("SMTP_SSL", "false").lower() in {"1", "true", "yes"}

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(text)

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as client:
            if username:
                client.login(username, password or "")
            client.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.ehlo()
            if os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes"}:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            if username:
                client.login(username, password or "")
            client.send_message(message)
    return True


def send_user_password_reset(email: str, token: str) -> bool:
    base = os.getenv("FRONTEND_URL", "https://delphiafit.com").rstrip("/")
    link = f"{base}/reset-password?email={email}&token={token}"
    return _send_email(
        email,
        "Reset your DelphiaFit password",
        f"Use this link to reset your DelphiaFit password:\n\n{link}\n\nIf you did not request this, ignore this email.",
    )


def send_coach_password_reset(email: str, token: str) -> bool:
    base = os.getenv("FRONTEND_URL", "https://delphiafit.com").rstrip("/")
    link = f"{base}/coach/password-reset?email={email}&token={token}"
    return _send_email(
        email,
        "Reset your DelphiaFit Coach password",
        f"Use this link to reset your coach password:\n\n{link}\n\nIf you did not request this, ignore this email.",
    )


def send_client_invitation(email: str, token: str) -> bool:
    base = os.getenv("FRONTEND_URL", "https://delphiafit.com").rstrip("/")
    link = f"{base}/invite?token={token}"
    return _send_email(email, "Your DelphiaFit invitation", f"You have been invited to DelphiaFit:\n\n{link}")
