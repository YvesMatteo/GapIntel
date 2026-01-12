import os
import sys
from dotenv import load_dotenv

# Add railway-api to path
sys.path.append(os.path.join(os.getcwd(), 'railway-api'))

import email_service

load_dotenv()

def test_completion_email():
    email = "yves.matro@outlook.com"
    access_key = "TEST-COMPLETION-CHECK"
    channel_name = "Trymacs"
    
    print(f"📧 Testing completion email to {email}...")
    success = email_service.send_access_key_email(email, access_key, channel_name)
    if success:
        print("✅ Completion email sent successfully (according to SMTP)")
    else:
        print("❌ Completion email failed")

if __name__ == "__main__":
    test_completion_email()
