#!/usr/bin/env python3
"""
YouTuber Outreach Automation Script

Finds YouTuber business emails, generates personalized AI pitches,
and sends cold outreach emails to sell Content Gap Intelligence service.

Usage:
    python outreach.py @ChannelHandle1 @ChannelHandle2 ...
    python outreach.py --file channels.txt
    python outreach.py --test  # Send test email to yourself
"""

import argparse
import json
import os
import re
import smtplib
import time
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================
PROSPECTS_FILE = Path("data/prospects.json")
GMAIL_SENDER = os.getenv("GMAIL_SENDER_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Rate limiting
SECONDS_BETWEEN_EMAILS = 30  # Avoid spam flags

# Custom template file (optional)
TEMPLATE_FILE = Path("data/email_template.txt")
ATTACHMENTS_DIR = Path("data/attachments")

# ============================================
# YOUTUBE EMAIL EXTRACTION
# ============================================
def get_channel_info(channel_handle: str) -> dict:
    """
    Get channel info and business email using YouTube Data API.
    """
    from googleapiclient.discovery import build
    
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("   ⚠️ YOUTUBE_API_KEY not set")
        return {}
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # Clean handle
    handle = channel_handle.lstrip('@')
    
    try:
        # Search for channel by handle
        search_resp = youtube.search().list(
            part='snippet',
            q=handle,
            type='channel',
            maxResults=1
        ).execute()
        
        if not search_resp.get('items'):
            print(f"   ⚠️ Channel not found: {handle}")
            return {}
        
        channel_id = search_resp['items'][0]['snippet']['channelId']
        channel_title = search_resp['items'][0]['snippet']['title']
        
        # Get channel details
        channel_resp = youtube.channels().list(
            part='snippet,statistics,brandingSettings',
            id=channel_id
        ).execute()
        
        if not channel_resp.get('items'):
            return {}
        
        channel = channel_resp['items'][0]
        stats = channel.get('statistics', {})
        snippet = channel.get('snippet', {})
        
        # Extract email from description (business inquiries)
        description = snippet.get('description', '')
        email = extract_email_from_text(description)
        
        return {
            'handle': handle,
            'channel_id': channel_id,
            'title': channel_title,
            'subscribers': int(stats.get('subscriberCount', 0)),
            'video_count': int(stats.get('videoCount', 0)),
            'view_count': int(stats.get('viewCount', 0)),
            'description': description[:500],
            'email': email,
            'country': snippet.get('country', 'Unknown'),
        }
        
    except Exception as e:
        print(f"   ⚠️ Error fetching channel: {e}")
        return {}


def extract_email_from_text(text: str) -> str:
    """Extract email address from text using regex."""
    # Common patterns for business emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(email_pattern, text)
    
    # Filter out common non-business emails
    excluded = ['example.com', 'gmail.com', 'yahoo.com', 'hotmail.com']
    
    for email in matches:
        # Prefer business emails
        domain = email.split('@')[1].lower()
        if domain not in excluded:
            return email
    
    # Fall back to any email found
    return matches[0] if matches else ""


def search_email_online(channel_name: str, channel_handle: str) -> str:
    """
    Use Gemini AI with web search to find YouTuber business email.
    Searches across social media, websites, and business directories.
    """
    import google.generativeai as genai
    
    if not GEMINI_API_KEY:
        return ""
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    print(f"   🔍 Searching web for email...")
    
    prompt = f"""Find the business/contact email for this YouTuber:

Channel Name: {channel_name}
YouTube Handle: @{channel_handle}

Search for their email on:
1. Their personal website or link in bio
2. Twitter/X profile
3. Instagram bio
4. LinkedIn
5. Business directories
6. Press/media kits

IMPORTANT: Only return a REAL email you can verify from actual sources.
Do NOT make up or guess an email address.

If you find a real email, respond with ONLY the email address (nothing else).
If you cannot find a real email, respond with: NOT_FOUND
"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Validate it looks like an email
        if result and result != "NOT_FOUND" and "@" in result and "." in result:
            # Clean up any extra text
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', result)
            if email_match:
                found_email = email_match.group(0)
                print(f"   ✓ Found via web search: {found_email}")
                return found_email
        
        print("   ⚠️ No email found via web search")
        return ""
        
    except Exception as e:
        print(f"   ⚠️ Web search failed: {e}")
        return ""



# ============================================
# AI PITCH GENERATION (GEMINI)
# ============================================
# Ollama configuration
OLLAMA_MODEL = "llama3.2"  # Default local model
OLLAMA_URL = "http://localhost:11434/api/generate"


def generate_pitch(channel_data: dict, use_local: bool = True) -> dict:
    """
    Generate a personalized outreach email.
    Uses Ollama (local) by default, falls back to Gemini if unavailable.
    Returns: {'subject': '...', 'body': '...'}
    """
    prompt = f"""You are a professional cold email copywriter. Write a personalized outreach email to a YouTuber.

CHANNEL INFO:
- Name: {channel_data.get('title', 'Unknown')}
- Subscribers: {channel_data.get('subscribers', 0):,}
- Total Views: {channel_data.get('view_count', 0):,}
- Videos: {channel_data.get('video_count', 0)}
- Niche: {channel_data.get('description', '')[:200]}

WHAT WE'RE SELLING:
"Content Gap Intelligence" - An AI-powered tool that:
1. Analyzes their audience comments to find EXACTLY what viewers are asking for
2. Cross-references against their existing content to find TRUE gaps
3. Generates viral title ideas for verified opportunities
4. Checks Google Trends for timing
5. Analyzes competitors to find "traffic stealing" opportunities

VALUE PROPOSITION:
- Stop guessing what to make next
- Get data-backed content ideas
- Increase views by creating what their audience actually wants

PRICING:
- One-time deep analysis: $297
- Monthly reports: $97/month

RULES:
1. Keep it SHORT (under 150 words)
2. Personalize based on their channel
3. Show you understand their niche
4. Include a clear call-to-action (reply to learn more)
5. Be professional but friendly, not salesy

OUTPUT JSON ONLY (no other text):
{{"subject": "Short subject line", "body": "Email body here"}}
"""

    # Try Ollama first (local, free)
    if use_local:
        try:
            import requests
            print("   🏠 Using local Ollama model...")
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result_text = response.json().get('response', '{}')
                result = json.loads(result_text)
                if result.get('subject') and result.get('body'):
                    return result
                    
        except Exception as e:
            print(f"   ⚠️ Ollama failed ({e}), trying Gemini...")
    
    # Fallback to Gemini
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            print("   ☁️ Using Gemini API...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"   ⚠️ Gemini failed: {e}")
    
    return {'subject': '', 'body': ''}


# ============================================
# CUSTOM TEMPLATE LOADING
# ============================================
def load_custom_template() -> dict:
    """
    Load custom email template from file.
    Template format:
        SUBJECT: Your subject line here
        ---
        Your email body here...
        Use {channel_name} and {subscriber_count} as placeholders.
    """
    if not TEMPLATE_FILE.exists():
        return None
    
    try:
        with open(TEMPLATE_FILE, 'r') as f:
            content = f.read()
        
        if '---' not in content:
            return None
        
        parts = content.split('---', 1)
        subject_line = parts[0].replace('SUBJECT:', '').strip()
        body = parts[1].strip()
        
        return {'subject': subject_line, 'body': body}
    except:
        return None


def apply_template(template: dict, channel_data: dict) -> dict:
    """Apply channel data to template placeholders."""
    subject = template['subject']
    body = template['body']
    
    replacements = {
        '{channel_name}': channel_data.get('title', 'there'),
        '{subscriber_count}': f"{channel_data.get('subscribers', 0):,}",
        '{video_count}': str(channel_data.get('video_count', 0)),
        '{view_count}': f"{channel_data.get('view_count', 0):,}",
    }
    
    for placeholder, value in replacements.items():
        subject = subject.replace(placeholder, value)
        body = body.replace(placeholder, value)
    
    return {'subject': subject, 'body': body}


# ============================================
# EMAIL SENDING (SMTP) with ATTACHMENTS
# ============================================
def send_email(to_email: str, subject: str, body: str, attachments: list = None) -> bool:
    """
    Send email via Gmail SMTP with App Password.
    Supports image/PDF attachments.
    """
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        print("   ⚠️ Gmail credentials not set (GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD)")
        return False
    
    try:
        msg = MIMEMultipart('mixed')
        msg['From'] = GMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create alternative part for text/html
        alt_part = MIMEMultipart('alternative')
        
        # Plain text version
        alt_part.attach(MIMEText(body, 'plain'))
        
        # HTML version (nicer formatting)
        html_body = body.replace('\n', '<br>')
        alt_part.attach(MIMEText(f"<html><body style='font-family: Arial, sans-serif;'>{html_body}</body></html>", 'html'))
        
        msg.attach(alt_part)
        
        # Add attachments
        if attachments:
            for filepath in attachments:
                path = Path(filepath)
                if not path.exists():
                    print(f"   ⚠️ Attachment not found: {filepath}")
                    continue
                
                mime_type, _ = mimetypes.guess_type(str(path))
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                
                main_type, sub_type = mime_type.split('/', 1)
                
                with open(path, 'rb') as f:
                    part = MIMEBase(main_type, sub_type)
                    part.set_payload(f.read())
                
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=path.name)
                msg.attach(part)
                print(f"   📎 Attached: {path.name}")
        
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, to_email, msg.as_string())
        
        return True
        
    except Exception as e:
        print(f"   ⚠️ Email send failed: {e}")
        return False


# ============================================
# PROSPECT MANAGEMENT
# ============================================
def load_prospects() -> dict:
    """Load prospects database."""
    if PROSPECTS_FILE.exists():
        with open(PROSPECTS_FILE, 'r') as f:
            return json.load(f)
    return {'prospects': []}


def save_prospects(data: dict):
    """Save prospects database."""
    PROSPECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def add_prospect(channel_data: dict, pitch: dict, status: str = 'pending'):
    """Add or update a prospect."""
    db = load_prospects()
    
    # Check if already exists
    for i, p in enumerate(db['prospects']):
        if p.get('handle') == channel_data.get('handle'):
            db['prospects'][i].update({
                **channel_data,
                'pitch_subject': pitch.get('subject', ''),
                'pitch_body': pitch.get('body', ''),
                'status': status,
                'updated_at': datetime.now().isoformat()
            })
            save_prospects(db)
            return
    
    # Add new
    db['prospects'].append({
        **channel_data,
        'pitch_subject': pitch.get('subject', ''),
        'pitch_body': pitch.get('body', ''),
        'status': status,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    })
    save_prospects(db)


# ============================================
# MAIN OUTREACH FLOW
# ============================================
def process_channel(handle: str, dry_run: bool = False, use_template: bool = False, attachments: list = None, provided_email: str = None, provided_name: str = None, preview_mode: bool = False) -> dict:
    """
    Full outreach pipeline for a single channel.
    If provided_email is set, skips email search and uses that email directly.
    If preview_mode is True, sends email to yourself instead of the prospect.
    """
    print(f"\n🎯 Processing: {handle}")
    
    # Step 1: Get channel info
    print("   📺 Fetching channel info...")
    channel_data = get_channel_info(handle)
    
    # Hande API failure/Quota limits
    if not channel_data:
        if provided_email and provided_name:
             print(f"   ⚠️ API Lookup failed (likely Quota), but have manual details for: {provided_name}")
             channel_data = {
                 'handle': handle,
                 'title': provided_name,
                 'subscribers': 0, # Unknown
                 'video_count': 0, # Unknown
                 'view_count': 0,
                 'description': '',
                 'email': provided_email,
                 'country': 'Unknown'
             }
        else:
             return {'status': 'failed', 'reason': 'Channel not found'}
    
    print(f"   ✓ {channel_data['title']} ({channel_data['subscribers']:,} subs)")
    
    # Step 2: Check for email (pre-provided, YouTube description, or web search)
    email = provided_email or channel_data.get('email', '')
    
    if provided_email:
        print(f"   ✓ Using provided email: {email}")
        channel_data['email'] = email
        channel_data['email_source'] = 'provided'
    elif email:
        print(f"   ✓ Email from YouTube: {email}")
        channel_data['email_source'] = 'youtube_description'
    else:
        print("   ⚠️ No email in YouTube description, searching web...")
        email = search_email_online(channel_data['title'], channel_data['handle'])
        channel_data['email'] = email
        channel_data['email_source'] = 'web_search' if email else 'not_found'
    
    if not email:
        print("   ❌ No business email found anywhere")
        add_prospect(channel_data, {}, 'no_email')
        return {'status': 'no_email', 'channel': channel_data}
    
    print(f"   ✓ Email found: {email}")
    
    # Step 3: Generate personalized pitch (template or AI)
    custom_template = load_custom_template() if use_template else None
    
    if custom_template:
        print("   📝 Using custom template...")
        pitch = apply_template(custom_template, channel_data)
    else:
        print("   ✍️ Generating AI pitch...")
        pitch = generate_pitch(channel_data)
    
    if not pitch.get('subject') or not pitch.get('body'):
        print("   ⚠️ Pitch generation failed")
        add_prospect(channel_data, pitch, 'pitch_failed')
        return {'status': 'pitch_failed', 'channel': channel_data}
    
    print(f"   ✓ Subject: {pitch['subject'][:50]}...")
    
    # Step 4: Send email (or dry run)
    target_email = email
    
    if preview_mode:
        print(f"   🧪 PREVIEW MODE: Sending to {GMAIL_SENDER} instead of {email}")
        target_email = GMAIL_SENDER
        pitch['subject'] = f"[PREVIEW for {handle}] {pitch['subject']}"
    
    if dry_run and not preview_mode:
        print("   📧 DRY RUN - Email NOT sent")
        print(f"\n   --- PREVIEW ---")
        print(f"   Subject: {pitch['subject']}")
        print(f"   Body: {pitch['body'][:200]}...")
        add_prospect(channel_data, pitch, 'dry_run')
        return {'status': 'dry_run', 'channel': channel_data, 'pitch': pitch}
    
    print(f"   📧 Sending email to {target_email}...")
    success = send_email(target_email, pitch['subject'], pitch['body'], attachments=attachments)
    
    if success:
        print("   ✓ Email sent successfully!")
        if not preview_mode:
            add_prospect(channel_data, pitch, 'sent')
        return {'status': 'sent', 'channel': channel_data, 'pitch': pitch}
    else:
        if not preview_mode:
            add_prospect(channel_data, pitch, 'send_failed')
        return {'status': 'send_failed', 'channel': channel_data, 'pitch': pitch}


def main():
    parser = argparse.ArgumentParser(
        description="YouTuber Outreach Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python outreach.py @MrBeast @MKBHD --dry-run
    python outreach.py --file channels.txt
    python outreach.py --contacts data/contacts.json --template
    python outreach.py --test
    python outreach.py --status
    python outreach.py @Channel --template --preview
    python outreach.py @Channel --template --attach screenshot.png
        """
    )
    parser.add_argument('channels', nargs='*', help='YouTube channel handles')
    parser.add_argument('--file', '-f', help='File with channel handles (one per line)')
    parser.add_argument('--contacts', '-c', help='JSON file with channel+email pairs (skips email search)')
    parser.add_argument('--dry-run', action='store_true', help='Generate pitches but don\'t send emails')
    parser.add_argument('--test', action='store_true', help='Send test email to yourself')
    parser.add_argument('--status', action='store_true', help='Show outreach status/stats')
    parser.add_argument('--template', '-t', action='store_true', help='Use custom template from data/email_template.txt')
    parser.add_argument('--attach', '-a', nargs='+', help='Attach files (images, PDFs)')
    parser.add_argument('--preview', '-p', action='store_true', help='Send email to YOURSELF instead of prospect for testing')
    
    args = parser.parse_args()
    
    print("📧 YouTuber Outreach Automation")
    print("=" * 50)
    
    # Show status
    if args.status:
        db = load_prospects()
        prospects = db.get('prospects', [])
        
        print(f"\n📊 Outreach Statistics:")
        print(f"   Total prospects: {len(prospects)}")
        
        status_counts = {}
        for p in prospects:
            s = p.get('status', 'unknown')
            status_counts[s] = status_counts.get(s, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            print(f"   • {status}: {count}")
        
        return
    
    # Test mode
    if args.test:
        if not GMAIL_SENDER:
            print("❌ Set GMAIL_SENDER_EMAIL in .env first")
            return
        
        print(f"\n🧪 Sending test email to: {GMAIL_SENDER}")
        success = send_email(
            GMAIL_SENDER,
            "Test: Content Gap Intelligence Outreach",
            "This is a test email from your outreach script.\n\nIf you received this, email sending is working!"
        )
        print("✅ Test email sent!" if success else "❌ Test failed")
        return
    
    # Get channels list (or contacts with pre-provided emails)
    channels = args.channels or []
    contacts_map = {}  # Map of handle -> email (for pre-provided emails)
    
    # Load contacts file (channel + email pairs)
    if args.contacts:
        contacts_path = Path(args.contacts)
        if contacts_path.exists():
            with open(contacts_path, 'r') as f:
                contacts = json.load(f)
            for c in contacts:
                handle = c.get('channel', '').lstrip('@')
                email = c.get('email', '')
                name = c.get('name', '')
                if handle and email:
                    channels.append(f"@{handle}")
                    contacts_map[handle.lower()] = {'email': email, 'name': name}
            print(f"📋 Loaded {len(contacts_map)} contacts with pre-provided emails")
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            with open(file_path, 'r') as f:
                channels.extend([line.strip() for line in f if line.strip()])
    
    if not channels:
        print("❌ No channels provided. Use: python outreach.py @Channel1 @Channel2")
        print("   Or use: python outreach.py --contacts data/contacts.json")
        return
    
    # Process each channel
    results = {'sent': 0, 'no_email': 0, 'failed': 0, 'dry_run': 0}
    
    for i, handle in enumerate(channels):
        if i > 0:
            print(f"\n   ⏳ Waiting {SECONDS_BETWEEN_EMAILS}s (rate limit)...")
            time.sleep(SECONDS_BETWEEN_EMAILS)
        
        # Get pre-provided email if available
        clean_handle = handle.lstrip('@').lower()
        contact_info = contacts_map.get(clean_handle, {})
        
        # Handle both old format (string email) and new format (dict with email/name)
        if isinstance(contact_info, str):
             provided_email = contact_info
             provided_name = None
        else:
             provided_email = contact_info.get('email')
             provided_name = contact_info.get('name')

        result = process_channel(
            handle, 
            dry_run=args.dry_run, 
            use_template=args.template, 
            attachments=args.attach,
            provided_email=provided_email,
            provided_name=provided_name,
            preview_mode=args.preview
        )
        status = result.get('status', 'failed')
        
        if status == 'sent':
            results['sent'] += 1
        elif status == 'no_email':
            results['no_email'] += 1
        elif status == 'dry_run':
            results['dry_run'] += 1
        else:
            results['failed'] += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"   ✓ Emails sent: {results['sent']}")
    print(f"   ⚠️ No email found: {results['no_email']}")
    print(f"   ❌ Failed: {results['failed']}")
    if args.dry_run:
        print(f"   📝 Dry run (not sent): {results['dry_run']}")


if __name__ == "__main__":
    main()
