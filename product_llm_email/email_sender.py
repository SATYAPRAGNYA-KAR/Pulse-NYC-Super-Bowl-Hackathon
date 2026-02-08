import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_email(subject, body, recipients):
    """
    Send an email with given subject/body to a list of recipients.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials not set in .env")
        return

    for recipient in recipients:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
            print(f"Email sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email to {recipient}: {e}")
