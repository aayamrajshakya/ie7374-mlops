import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

from src.config import CHANGE_THRESHOLD

load_dotenv()

sender_email = os.getenv("SENDER_EMAIL")
gmail_app_pwd = os.getenv("GMAIL_PASSWORD_ASSIGNMENT3")
receiver_email = os.getenv("RECEIVER_EMAIL")


def calculate_percentage_change(curr_price, prev_price):
    if prev_price <= 0:
        raise ValueError("Previous price must be greater than 0")
    return ((curr_price - prev_price) / prev_price) * 100.0


def check_alert_condition(curr_price, prev_price, threshold_pct=CHANGE_THRESHOLD):
    pct_change = calculate_percentage_change(curr_price, prev_price)
    alert_bool = abs(pct_change) >= threshold_pct
    return alert_bool, pct_change


def send_email_alert(
    sender,
    sender_password,
    receiver,
    curr_price,
    prev_price,
    pct_change,
):
    subject_line = f"Bitcoin price alert: {pct_change:+.2f}% change in the last hour!"
    body = f"""Summary:
                - Current price: ${curr_price:,.2f}
                - Price one hr ago: ${prev_price:,.2f}
                - Change: {pct_change:+.2f}%"""

    msg = MIMEText(body)
    msg["Subject"] = subject_line
    msg["From"] = sender
    msg["To"] = receiver

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender, sender_password)
        server.sendmail(sender, receiver, msg.as_string())
