from app.mailing.send_email import send_email
from app.core.secuirity import create_access_token


async def send_verification_email(email: str):
    registration_token = create_access_token({"email": email})
    activation_url = f"/api/auth/confirm-email?token={registration_token}"
    await send_email(
        recipient_email=email,
        subject="Подтверждение регистрации",
        plain_content=activation_url,
    )
