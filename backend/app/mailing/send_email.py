from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib

host = "smtp.gmail.com"
email = "skorpion0521@gmail.com"
password = "fmsvprcclmpvcxzt"


async def send_email(
    recipient_email: str, subject: str, plain_content: str, html_content: str = ""
):
    message = MIMEMultipart("alternative")
    message["From"] = email
    message["To"] = recipient_email
    message["Subject"] = subject

    plain_text_message = MIMEText(plain_content, "plain", "utf-8")
    message.attach(plain_text_message)

    if html_content:
        html_message = MIMEText(html_content, "html", "utf-8")
        message.attach(html_message)

    await aiosmtplib.send(
        message, hostname=host, port=587, username=email, password=password
    )
