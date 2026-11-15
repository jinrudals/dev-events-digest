import os
import smtplib
from email.message import EmailMessage


def send_email(html: str, subject: str) -> None:
    msg = EmailMessage()
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["MAIL_TO"]
    msg["Subject"] = subject
    msg.set_content("HTML 메일을 지원하는 클라이언트에서 확인해 주세요.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg)
