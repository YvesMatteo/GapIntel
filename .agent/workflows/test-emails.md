---
description: Test email sending functionality
---
# Test Emails

// turbo-all

## Steps

1. Test sending an email via the Railway API:
```bash
curl -s "https://resourceful-passion-production.up.railway.app/test-email?email=yves.matro@gmail.com"
```

2. Check the response for success or failure details.

## Notes
- The test email will be sent to the specified email address
- Check spam folder if not received
- If it fails, check Railway logs for SMTP errors
