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
    Premium dark theme design with visual progress steps.
    """
    subject = f"🚀 Analysis Started for @{channel_name}"
    
    report_url = f"https://www.gapintel.online/report/{report_id}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
                line-height: 1.6; 
                color: #e2e8f0; 
                background-color: #0f172a; 
                margin: 0; 
                padding: 40px 20px; 
            }}
            .container {{ 
                max-width: 560px; 
                margin: 0 auto; 
                background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); 
                border-radius: 24px; 
                overflow: hidden; 
                border: 1px solid #334155;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }}
            .header {{ 
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); 
                padding: 48px 32px; 
                text-align: center; 
                position: relative;
            }}
            .header::after {{
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            }}
            .logo {{ 
                font-size: 32px; 
                font-weight: 800; 
                color: white; 
                letter-spacing: -1px; 
                margin: 0;
                text-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }}
            .tagline {{ 
                color: rgba(255,255,255,0.85); 
                font-size: 14px; 
                margin-top: 8px;
                font-weight: 500;
            }}
            .content {{ 
                padding: 40px 32px; 
            }}
            .channel-card {{
                background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%);
                border: 1px solid #3b82f6;
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                margin-bottom: 32px;
                position: relative;
                overflow: hidden;
            }}
            .channel-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
            }}
            .pulse-dot {{
                display: inline-block;
                width: 10px;
                height: 10px;
                background: #22c55e;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.2);
            }}
            .status-label {{
                font-size: 12px;
                color: #22c55e;
                text-transform: uppercase;
                letter-spacing: 2px;
                font-weight: 600;
                margin-bottom: 12px;
            }}
            .channel-name {{
                font-size: 24px;
                font-weight: 700;
                color: #ffffff;
                margin: 0;
            }}
            .message {{ 
                color: #94a3b8; 
                font-size: 15px; 
                margin-bottom: 24px; 
            }}
            .progress-section {{
                margin: 32px 0;
            }}
            .progress-title {{
                font-size: 13px;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            .step {{
                display: flex;
                align-items: flex-start;
                margin-bottom: 16px;
                padding: 16px;
                background: rgba(30, 41, 59, 0.5);
                border-radius: 12px;
                border: 1px solid #334155;
            }}
            .step-icon {{
                width: 36px;
                height: 36px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                margin-right: 16px;
                flex-shrink: 0;
            }}
            .step-icon.active {{
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            }}
            .step-icon.pending {{
                background: #334155;
            }}
            .step-content {{
                flex: 1;
            }}
            .step-title {{
                font-size: 14px;
                font-weight: 600;
                color: #e2e8f0;
                margin: 0 0 4px 0;
            }}
            .step-desc {{
                font-size: 13px;
                color: #64748b;
                margin: 0;
            }}
            .time-estimate {{
                background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                padding: 16px 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 24px 0;
            }}
            .time-icon {{
                font-size: 20px;
                margin-right: 12px;
            }}
            .time-text {{
                font-size: 14px;
                color: #c4b5fd;
            }}
            .time-text strong {{
                color: #ffffff;
            }}
            .cta-button {{ 
                display: inline-block; 
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                color: white !important; 
                padding: 16px 40px; 
                border-radius: 12px; 
                text-decoration: none; 
                font-weight: 600; 
                font-size: 15px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
            }}
            .footer {{ 
                background: #0f172a; 
                padding: 32px; 
                text-align: center; 
                border-top: 1px solid #1e293b; 
            }}
            .footer p {{ 
                color: #475569; 
                font-size: 13px; 
                margin: 6px 0; 
            }}
            .footer a {{ 
                color: #3b82f6; 
                text-decoration: none; 
            }}
            .social-links {{
                margin-top: 16px;
            }}
            .social-links a {{
                display: inline-block;
                margin: 0 8px;
                color: #64748b;
                text-decoration: none;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="logo">GAP Intel</h1>
                <p class="tagline">AI-Powered Content Intelligence</p>
            </div>
            
            <div class="content">
                <div class="channel-card">
                    <div class="status-label">
                        <span class="pulse-dot"></span>
                        Analysis in Progress
                    </div>
                    <h2 class="channel-name">@{channel_name}</h2>
                </div>
                
                <p class="message">
                    Your content gap analysis has started! Our AI is now diving deep into your channel to uncover growth opportunities and actionable insights.
                </p>
                
                <div class="progress-section">
                    <div class="progress-title">What We're Analyzing</div>
                    
                    <div class="step">
                        <div class="step-icon active">📊</div>
                        <div class="step-content">
                            <p class="step-title">Performance Metrics</p>
                            <p class="step-desc">Views, engagement rates, and growth patterns</p>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-icon active">🎨</div>
                        <div class="step-content">
                            <p class="step-title">Thumbnail Analysis</p>
                            <p class="step-desc">Visual elements, colors, and click-through optimization</p>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-icon active">🎯</div>
                        <div class="step-content">
                            <p class="step-title">Content Gaps</p>
                            <p class="step-desc">Untapped topics your audience wants to see</p>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-icon active">🏆</div>
                        <div class="step-content">
                            <p class="step-title">Competitor Insights</p>
                            <p class="step-desc">What's working for top performers in your niche</p>
                        </div>
                    </div>
                </div>
                
                <div class="time-estimate">
                    <span class="time-icon">⏱️</span>
                    <span class="time-text">Estimated time: <strong>5-15 minutes</strong></span>
                </div>
                
                <p class="message" style="text-align: center; margin-bottom: 8px;">
                    We'll email you the moment your report is ready.
                </p>
                
                <div style="text-align: center; margin-top: 24px;">
                    <a href="https://www.gapintel.online/dashboard" class="cta-button">Track Progress →</a>
                </div>
            </div>
            
            <div class="footer">
                <p><strong style="color: #94a3b8;">GAP Intel</strong></p>
                <p>AI-Powered YouTube Analytics</p>
                <p style="margin-top: 16px;">
                    Questions? Reply to this email or visit 
                    <a href="https://www.gapintel.online">gapintel.online</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""🚀 Analysis Started for @{channel_name}

Your content gap analysis has started! Our AI is now diving deep into your channel.

WHAT WE'RE ANALYZING:
• Performance Metrics - Views, engagement rates, and growth patterns
• Thumbnail Analysis - Visual elements, colors, and CTR optimization  
• Content Gaps - Untapped topics your audience wants to see
• Competitor Insights - What's working for top performers

⏱️ Estimated time: 5-15 minutes

We'll email you the moment your report is ready.

Track progress: https://www.gapintel.online/dashboard

---
GAP Intel - AI-Powered YouTube Analytics
Questions? Reply to this email or visit gapintel.online
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
