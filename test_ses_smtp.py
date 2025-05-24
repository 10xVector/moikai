import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

MAIL_SERVER = os.getenv('MAIL_SERVER', 'email-smtp.us-east-2.amazonaws.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

try:
    print(f"Connecting to {MAIL_SERVER}:{MAIL_PORT} ...")
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10)
    server.starttls()
    print("Starting TLS...")
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    print("Login successful!")
    server.quit()
except Exception as e:
    print(f"SMTP connection failed: {e}") 