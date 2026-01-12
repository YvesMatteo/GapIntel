#!/bin/bash

# Generates a fake Stripe signature and sends a payload to the application webhook

PAYLOAD='{
  "id": "evt_test_webhook",
  "object": "event",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_simulated",
      "object": "checkout.session",
      "amount_total": 7900,
      "customer_email": "yves.matro@gmail.com",
      "metadata": {
        "channelName": "TestChannelSimulated"
      },
      "payment_status": "paid"
    }
  }
}'

# Note: The Next.js API might reject this due to invalid signature because we can't easily sign it without the secret key logic here.
# So we might need to Temporarily Bypass signature check in route.ts OR hit the Railway API directly.

# Plan B: Hit the Railway Backend directly as if the Next.js API called it.
# This validates the "Reporting Engine" part, which is what failed for the user.

curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "channel_name": "TestChannelSimulated",
       "access_key": "GAP-TestKeySimulated",
       "email": "yves.matro@gmail.com"
     }'

echo ""
echo "✅ Request sent to Backend API directly."
