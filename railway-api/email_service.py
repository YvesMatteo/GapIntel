"""
Email Service for GAP Intel
Uses Resend API for transactional emails from help@gapintel.online
Modern, premium email templates matching the website design.
"""

import os
import requests
from datetime import datetime

RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "GAP Intel <help@gapintel.online>"

# Modern email styles matching website aesthetic
EMAIL_STYLES = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.7; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }
    .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 32px; text-align: center; }
    .header h1 { color: white; margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px; }
    .header .subtitle { color: #94a3b8; font-size: 14px; margin-top: 8px; }
    .content { padding: 32px; }
    .greeting { font-size: 18px; color: #1e293b; margin-bottom: 16px; }
    .message { color: #475569; font-size: 15px; margin-bottom: 24px; }
    .highlight-box { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #bae6fd; border-radius: 12px; padding: 20px; margin: 24px 0; text-align: center; }
    .highlight-label { font-size: 12px; color: #0369a1; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .highlight-value { font-size: 20px; color: #0c4a6e; font-weight: 600; }
    .cta-button { display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white !important; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; margin: 16px 0; }
    .cta-button:hover { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); }
    .success-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1px solid #86efac; border-radius: 12px; padding: 20px; margin: 24px 0; text-align: center; }
    .success-icon { font-size: 48px; margin-bottom: 12px; }
    .footer { background: #f8fafc; padding: 24px; text-align: center; border-top: 1px solid #e2e8f0; }
    .footer p { color: #64748b; font-size: 13px; margin: 4px 0; }
    .footer a { color: #3b82f6; text-decoration: none; }
    .divider { height: 1px; background: #e2e8f0; margin: 24px 0; }
    .stats-grid { display: flex; justify-content: space-around; margin: 24px 0; }
    .stat-item { text-align: center; }
    .stat-value { font-size: 24px; font-weight: 700; color: #1e293b; }
    .stat-label { font-size: 12px; color: #64748b; text-transform: uppercase; }
</style>
"""


def send_email(to: str, subject: str, html: str, text: str = None) -> bool:
    """
    Send an email using Resend API.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    
    if not api_key:
        print("❌ Error: RESEND_API_KEY not set in environment")
        return False
    
    payload = {
        "from": SENDER_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    
    if text:
        payload["text"] = text
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(RESEND_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Email sent successfully to {to}")
            return True
        else:
            print(f"❌ Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_analysis_started_email(user_email: str, channel_name: str, report_id: str):
    """
    Sends a confirmation email when analysis begins.
    No access key shown - user accesses via their account dashboard.
    """
    subject = f"🚀 Analysis Started for @{channel_name}"
    
    report_url = f"https://www.gapintel.online/report/{report_id}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>{EMAIL_STYLES}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>GAP Intel</h1>
                <div class="subtitle">AI-Powered Content Strategy</div>
            </div>
            
            <div class="content">
                <p class="greeting">Hi there! 👋</p>
                
                <p class="message">
                    Great news! We've started analyzing <strong>@{channel_name}</strong>. 
                    Our AI is now crunching the data to find your best content opportunities.
                </p>
                
                <div class="highlight-box">
                    <div class="highlight-label">Analyzing Channel</div>
                    <div class="highlight-value">@{channel_name}</div>
                </div>
                
                <p class="message">
                    <strong>What happens next?</strong><br>
                    We'll analyze your recent videos, thumbnails, engagement patterns, and compare them against top performers in your niche. This typically takes <strong>5-15 minutes</strong>.
                </p>
                
                <p class="message">
                    You'll receive another email as soon as your report is ready. In the meantime, you can track progress from your dashboard.
                </p>
                
                <div style="text-align: center;">
                    <a href="https://www.gapintel.online/dashboard" class="cta-button">View Dashboard →</a>
                </div>
                
                <div class="divider"></div>
                
                <p class="message" style="font-size: 13px; color: #94a3b8;">
                    💡 <strong>Tip:</strong> While you wait, check out our analysis guide to get the most value from your report.
                </p>
            </div>
            
            <div class="footer">
                <p>GAP Intel - AI-Powered YouTube Analytics</p>
                <p>Questions? Reply to this email or visit <a href="https://www.gapintel.online">gapintel.online</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""Hi there!

Great news! We've started analyzing @{channel_name}.

Our AI is now crunching the data to find your best content opportunities. This typically takes 5-15 minutes.

You'll receive another email as soon as your report is ready.

Track progress: https://www.gapintel.online/dashboard

GAP Intel - AI-Powered Content Strategy
"""

    return send_email(user_email, subject, html_content, text_content)


def send_report_complete_email(user_email: str, channel_name: str, report_id: str, stats: dict = None):
    """
    Sends a beautiful email when the report is finished.
    Includes key metrics preview to entice clicking through.
    """
    subject = f"✅ Your Analysis for @{channel_name} is Ready!"
    
    report_url = f"https://www.gapintel.online/report/{report_id}"
    
    # Default stats if none provided
    if not stats:
        stats = {
            "videos_analyzed": 20,
            "content_gaps": 5,
            "thumbnail_score": 85
        }

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>{EMAIL_STYLES}</head>
    <body>
        <div class="container">
            <div class="header">
                <h1>GAP Intel</h1>
                <div class="subtitle">Your Report is Ready!</div>
            </div>
            
            <div class="content">
                <div class="success-box">
                    <div class="success-icon">🎉</div>
                    <div class="highlight-value">Analysis Complete!</div>
                    <p style="color: #166534; margin: 8px 0 0 0; font-size: 14px;">@{channel_name}</p>
                </div>
                
                <p class="message">
                    Your comprehensive content gap analysis is ready. Here's a quick preview of what we found:
                </p>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{stats.get('videos_analyzed', 20)}</div>
                        <div class="stat-label">Videos Analyzed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats.get('content_gaps', 5)}</div>
                        <div class="stat-label">Gaps Found</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{stats.get('thumbnail_score', 85)}%</div>
                        <div class="stat-label">Thumbnail Score</div>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{report_url}" class="cta-button">View Full Report →</a>
                </div>
                
                <div class="divider"></div>
                
                <p class="message">
                    <strong>What's in your report:</strong>
                </p>
                <ul style="color: #475569; font-size: 14px; line-height: 2;">
                    <li>📊 Content gap analysis with trending topics</li>
                    <li>🎨 Thumbnail optimization recommendations</li>
                    <li>📈 Views forecast for recommended topics</li>
                    <li>🎣 Hook analysis from your top-performing videos</li>
                    <li>🏆 Competitor insights and benchmarks</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>GAP Intel - AI-Powered YouTube Analytics</p>
                <p>Questions? Reply to this email or visit <a href="https://www.gapintel.online">gapintel.online</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""Your Analysis for @{channel_name} is Ready!

Great news! Your comprehensive content gap analysis is complete.

Quick Preview:
- Videos Analyzed: {stats.get('videos_analyzed', 20)}
- Content Gaps Found: {stats.get('content_gaps', 5)}
- Thumbnail Score: {stats.get('thumbnail_score', 85)}%

View your full report: {report_url}

What's included:
- Content gap analysis with trending topics
- Thumbnail optimization recommendations
- Views forecast for recommended topics
- Hook analysis from top-performing videos
- Competitor insights and benchmarks

GAP Intel - AI-Powered Content Strategy
"""

    return send_email(user_email, subject, html_content, text_content)


def send_analysis_failed_email(user_email: str, channel_name: str, error_reason: str = ""):
    """
    Sends an email notifying the user that their analysis failed.
    """
    subject = f"⚠️ Issue with Your Analysis for @{channel_name}"

    safe_error = error_reason[:200] if error_reason else "An unexpected error occurred"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>{EMAIL_STYLES}</head>
    <body>
        <div class="container">
            <div class="header" style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);">
                <h1>GAP Intel</h1>
                <div class="subtitle">We Hit a Snag</div>
            </div>
            
            <div class="content">
                <p class="greeting">Hi there,</p>
                
                <p class="message">
                    Unfortunately, we encountered an issue while analyzing <strong>@{channel_name}</strong>.
                </p>
                
                <div class="highlight-box" style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border-color: #fca5a5;">
                    <div class="highlight-label" style="color: #dc2626;">Error Details</div>
                    <div class="highlight-value" style="color: #991b1b; font-size: 14px;">{safe_error}</div>
                </div>
                
                <p class="message">
                    <strong>What can you do?</strong>
                </p>
                <ul style="color: #475569; font-size: 14px; line-height: 2;">
                    <li>Make sure the channel URL is correct and public</li>
                    <li>Try again in a few minutes</li>
                    <li>Contact us if the problem persists</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="https://www.gapintel.online/dashboard" class="cta-button" style="background: linear-gradient(135deg, #475569 0%, #334155 100%);">Try Again →</a>
                </div>
            </div>
            
            <div class="footer">
                <p>GAP Intel - AI-Powered YouTube Analytics</p>
                <p>Need help? Reply to this email directly.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""Hi there,

Unfortunately, we encountered an issue while analyzing @{channel_name}.

Error: {safe_error}

What can you do?
- Make sure the channel URL is correct and public
- Try again in a few minutes
- Contact us if the problem persists

Try again: https://www.gapintel.online/dashboard

GAP Intel - AI-Powered Content Strategy
"""

    return send_email(user_email, subject, html_content, text_content)


def send_admin_failure_notification(user_email: str, report_id: str, channel_name: str, error_reason: str = "", failure_count: int = 1):
    """
    Sends an admin notification when a report fails.
    """
    subject = f"🚨 Report Failure #{failure_count}: {channel_name}"

    html_content = f"""
    <html>
    <body style="font-family: monospace; padding: 20px; background: #1e1e1e; color: #e0e0e0;">
        <h2 style="color: #ff6b6b;">Report Failure Alert</h2>
        <p><strong>User:</strong> {user_email}</p>
        <p><strong>Report ID:</strong> {report_id}</p>
        <p><strong>Channel:</strong> {channel_name}</p>
        <p><strong>Failure Count:</strong> {failure_count}</p>
        <p><strong>Error:</strong></p>
        <pre style="background: #2d2d2d; padding: 15px; border-radius: 5px; overflow: auto;">{error_reason[:500]}</pre>
        <p><strong>Time:</strong> {datetime.now().isoformat()}</p>
    </body>
    </html>
    """

    return send_email("help@gapintel.online", subject, html_content)


def send_admin_timeout_notification(user_email: str, failure_count: int, timeout_until: str):
    """
    Sends an admin notification when a user is timed out.
    """
    subject = f"⏸️ User Timeout: {user_email}"

    html_content = f"""
    <html>
    <body style="font-family: monospace; padding: 20px; background: #1e1e1e; color: #e0e0e0;">
        <h2 style="color: #ffa500;">User Timeout Notification</h2>
        <p><strong>User:</strong> {user_email}</p>
        <p><strong>Total Failures:</strong> {failure_count}</p>
        <p><strong>Timeout Until:</strong> {timeout_until}</p>
        <p><strong>Time:</strong> {datetime.now().isoformat()}</p>
    </body>
    </html>
    """

    return send_email("help@gapintel.online", subject, html_content)


def send_user_timeout_email(user_email: str, timeout_until: str, failure_count: int):
    """
    Notifies user they have been temporarily timed out.
    """
    subject = "⏸️ Your GAP Intel Account is Temporarily Paused"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>{EMAIL_STYLES}</head>
    <body>
        <div class="container">
            <div class="header" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                <h1>GAP Intel</h1>
                <div class="subtitle">Account Temporarily Paused</div>
            </div>
            
            <div class="content">
                <p class="greeting">Hi there,</p>
                
                <p class="message">
                    We've noticed multiple failed analysis attempts on your account. To protect our systems and ensure quality for all users, we've temporarily paused new analyses.
                </p>
                
                <div class="highlight-box" style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border-color: #fcd34d;">
                    <div class="highlight-label" style="color: #b45309;">Paused Until</div>
                    <div class="highlight-value" style="color: #92400e;">{timeout_until}</div>
                </div>
                
                <p class="message">
                    This is usually caused by:
                </p>
                <ul style="color: #475569; font-size: 14px; line-height: 2;">
                    <li>Private or restricted channels</li>
                    <li>Channels with very few videos</li>
                    <li>Temporary YouTube API issues</li>
                </ul>
                
                <p class="message">
                    After the pause period, you can try again. If you believe this is a mistake, please reply to this email.
                </p>
            </div>
            
            <div class="footer">
                <p>GAP Intel - AI-Powered YouTube Analytics</p>
                <p>Questions? Reply to this email directly.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""Hi there,

We've noticed multiple failed analysis attempts on your account. To protect our systems, we've temporarily paused new analyses.

Paused Until: {timeout_until}

This is usually caused by:
- Private or restricted channels
- Channels with very few videos
- Temporary YouTube API issues

After the pause period, you can try again. If you believe this is a mistake, please reply to this email.

GAP Intel
"""

    return send_email(user_email, subject, html_content, text_content)


# Legacy function aliases for backward compatibility
def send_access_key_email(user_email: str, access_key: str, channel_name: str):
    """Legacy alias - redirects to send_report_complete_email"""
    return send_report_complete_email(user_email, channel_name, access_key)


def send_analysis_start_email(user_email: str, access_key: str, channel_name: str):
    """Legacy alias - redirects to send_analysis_started_email"""
    return send_analysis_started_email(user_email, channel_name, access_key)
