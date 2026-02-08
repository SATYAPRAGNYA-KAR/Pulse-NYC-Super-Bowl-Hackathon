import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load credentials
load_dotenv()
EMAIL = os.getenv("GMAIL_USER")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Recipient
recipient = "nilarnabdebnath@gmail.com"

# Create message container
msg = MIMEMultipart("alternative")
msg["Subject"] = "Score Big with Free Delivery at Morning Brew!"
msg["From"] = EMAIL
msg["To"] = recipient

# Plain text fallback
text = """Hey there,

Celebrate your game day successes with Morning Brew! Enjoy FREE delivery on all orders until halftime. Whether you’re cheering for your team or just enjoying a cozy drink, we’re here to help you score big.

Order now and let’s make this event a win together!

Cheers,
The Morning Brew Team
Order Now: [Insert link here]
"""

# HTML version
html = """
<html>
  <body>
    <p>Hey there,</p>
    <p>Celebrate your <b>game day successes</b> with Morning Brew! Enjoy <b>FREE delivery</b> on all orders until halftime. Whether you’re cheering for your team or just enjoying a cozy drink, we’re here to help you <b>score big</b>.</p>
    <p>Order now and let’s make this event a <b>win</b> together!</p>
    <p>Cheers,<br>The Morning Brew Team</p>
    <p><a href="https://morningbrew.com/order" style="padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">Order Now</a></p>
  </body>
</html>
"""

# Attach both plain text and HTML
msg.attach(MIMEText(text, "plain"))
msg.attach(MIMEText(html, "html"))

# Send email
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, recipient, msg.as_string())

print(f"Email sent to {recipient} ✅")
