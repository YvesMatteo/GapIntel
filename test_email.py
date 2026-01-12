import os
from dotenv import load_dotenv
import sys

# Add railway-api to path
sys.path.append(os.path.join(os.getcwd(), "railway-api"))

from email_service import send_analysis_start_email

load_dotenv(".env")

email = "yves.matro@gmail.com"
access_key = "TEST-KEY-123"
channel_name = "TestChannel"

print(f"Testing email to {email}...")
success = send_analysis_start_email(email, access_key, channel_name)

if success:
    print("✅ Test email sent!")
else:
    print("❌ Test email failed!")
