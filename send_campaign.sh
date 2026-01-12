#!/bin/bash

# Campaign Launch Script
# Sends emails to all contacts in data/contacts.json using the template

echo "=================================================="
echo "🚀 STARTING OUTREACH CAMPAIGN"
echo "=================================================="
echo "🎯 Targets: 20 Creators (from data/contacts.json)"
echo "📧 Template: data/email_template.txt"
echo "⏱️  Delay: 30 seconds between emails"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This will send REAL EMAILS to the list."
echo "    The script is set effectively to 'Live' mode."
echo ""
echo "Press ENTER to confirm and start sending..."
echo "Or press Ctrl+C to cancel."
read -r

# Run the outreach script
python3 outreach.py --contacts data/contacts.json --template

echo ""
echo "✅ Campaign cycle complete."
