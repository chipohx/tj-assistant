import os

from app.mailing.send_email import send_email
from app.core.secuirity import create_token

email_subject = "Подтверждение регистрации"
email_message = "Пожалуйста, перейдите по ссылке ниже для подтверждения регистрации:"
verification_url_text = "Подтвердить регистрацию"


async def send_verification_email(email: str):
    """Отправляет письмо для подтверждения аккаунта
    на почту указанную email"""

    try:
        verification_token = create_token({"sub": email})
    except Exception as e:
        print(f"Couldn't create verification_token: {e}")

    print(verification_token)
    verification_url = (
        f"http://localhost:8000/api/auth/verify-email?token={verification_token}"
    )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "..", "templates", "mail.html")

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            template = file.read()
    except FileNotFoundError as e:
        print(f"Couldn't find template for email verifying: {e}")

    data = {}
    data["email_subject"] = email_subject
    data["email_message"] = email_message
    data["verification_url"] = verification_url
    data["verification_url_text"] = verification_url_text
    html_content = template.format(**data)

    try:
        await send_email(
            recipient_email=email,
            subject=email_subject,
            html_content=html_content,
        )
    except Exception as e:
        print(f"Email sending error: {e}")
