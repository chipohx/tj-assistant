import aiosmtplib, os
from dotenv import load_dotenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


load_dotenv()
host = "smtp.gmail.com"
email = os.getenv("EMAIL_LOGIN")
password = os.getenv("EMAIL_PASSWORD")


async def send_email(
    recipient_email: str, subject: str, plain_content: str = "", html_content: str = ""
):
    """Отправляет письмо на почту указанную в recipient_email
    subject - заголовок письма
    plain_content - текст письма
    html_content - html документ"""

    if not email or not password:
        raise Exception("Email or password not specified in .env")

    message = MIMEMultipart("alternative")
    message["From"] = email
    message["To"] = recipient_email
    message["Subject"] = subject

    plain_text_message = MIMEText(plain_content, "plain", "utf-8")
    message.attach(plain_text_message)

    if html_content:
        html_message = MIMEText(html_content, "html", "utf-8")
        message.attach(html_message)

    try:
        await aiosmtplib.send(
            message, hostname=host, port=587, username=email, password=password
        )
    except aiosmtplib.SMTPConnectError:
        print("Authentication error")
    except aiosmtplib.SMTPAuthenticationError:
        print("Authentication error")
    except aiosmtplib.SMTPTimeoutError:
        print("Timeout error")
    except aiosmtplib.SMTPException as e:
        print(f"Email sending error: {e}")
