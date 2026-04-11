import resend

from app.config import RESEND_API_KEY, EMAIL_FROM, APP_URL


resend.api_key = RESEND_API_KEY


async def send_verification_email(email: str, token: str) -> None:
    """Send a verification email via Resend."""
    verification_url = f"{APP_URL}/auth/verify-email?token={token}"

    try:
        resend.Emails.send({
            "from": EMAIL_FROM,
            "to": [email],
            "subject": "Verify your email address",
            "html": (
                f"<h2>Email Verification</h2>"
                f"<p>Click the link below to verify your email address:</p>"
                f'<a href="{verification_url}">Verify Email</a>'
                f"<p>This link expires in 24 hours.</p>"
            ),
        })
        print(f"[email] Verification email sent to {email}")
    except Exception as e:
        print(f"[email] Failed to send verification email to {email}: {e}")
        raise
