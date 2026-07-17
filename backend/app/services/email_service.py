import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("gotot.email")


BASE_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
.container { max-width: 600px; margin: 0 auto; padding: 24px; }
.header { background: linear-gradient(135deg, #6366f1, #a855f7); padding: 32px; text-align: center; border-radius: 16px 16px 0 0; }
.header h1 { color: white; margin: 0; font-size: 24px; }
.content { background: white; padding: 32px; border-radius: 0 0 16px 16px; }
.content p { color: #374151; line-height: 1.6; margin: 0 0 16px; }
.btn { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; }
.footer { text-align: center; padding: 24px; color: #9ca3af; font-size: 12px; }
.footer a { color: #6366f1; text-decoration: none; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>{title}</h1></div>
<div class="content">{body}</div>
<div class="footer">
<p>GoTot - Universal Video Downloader</p>
<p><a href="https://gotot.app">gotot.app</a> &middot; <a href="mailto:support@gotot.app">support@gotot.app</a></p>
<p style="font-size:11px;color:#d1d5db">If you no longer wish to receive these emails, <a href="{unsubscribe_url}">unsubscribe here</a>.</p>
</div>
</div>
</body>
</html>"""


async def send_email(to: str, subject: str, body_text: str, html: Optional[str] = None) -> bool:
    if not settings.smtp_host or not settings.smtp_user:
        logger.warning("SMTP not configured — skipping email send")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [to], msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def _render(title: str, body_html: str, unsubscribe: str = "") -> str:
    return BASE_TEMPLATE.replace("{title}", title).replace("{body}", body_html).replace(
        "{unsubscribe_url}", unsubscribe or "https://gotot.app/settings"
    )


async def send_welcome_email(to: str, username: str) -> bool:
    body_text = f"Welcome to GoTot, {username}! Start downloading videos from 11+ platforms for free."
    html = _render(
        "Welcome to GoTot!",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Welcome to <strong>GoTot</strong> — your universal video downloader.</p>
<p>You can now download videos from YouTube, TikTok, Instagram, Twitter, Facebook, Reddit, Vimeo, Twitch, Dailymotion, LinkedIn, and Pinterest.</p>
<p>Here are some tips to get started:</p>
<ul>
<li>Copy any video URL and paste it in the download box</li>
<li>Choose your preferred format and quality</li>
<li>Upgrade to Pro or Unlimited for more daily downloads</li>
</ul>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app">Start Downloading</a></p>"""
    )
    return await send_email(to, "Welcome to GoTot!", body_text, html)


async def send_verify_email(to: str, username: str, token: str) -> bool:
    verify_url = f"https://gotot.app/verify?token={token}"
    body_text = f"Verify your email address: {verify_url}"
    html = _render(
        "Verify Your Email",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Please verify your email address to activate your GoTot account.</p>
<p style="text-align:center;margin:24px 0"><a class="btn" href="{verify_url}">Verify Email</a></p>
<p>Or copy this link: <br/><small>{verify_url}</small></p>
<p>This link expires in 24 hours.</p>"""
    )
    return await send_email(to, "Verify your email - GoTot", body_text, html)


async def send_password_reset_email(to: str, username: str, token: str) -> bool:
    reset_url = f"https://gotot.app/reset-password?token={token}"
    body_text = f"Reset your password: {reset_url}"
    html = _render(
        "Reset Your Password",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>We received a request to reset your GoTot password.</p>
<p style="text-align:center;margin:24px 0"><a class="btn" href="{reset_url}">Reset Password</a></p>
<p>Or copy this link: <br/><small>{reset_url}</small></p>
<p>If you didn't request this, you can safely ignore this email.</p>
<p>This link expires in 1 hour.</p>"""
    )
    return await send_email(to, "Reset your password - GoTot", body_text, html)


async def send_password_changed_email(to: str, username: str) -> bool:
    body_text = f"Your GoTot password was changed successfully."
    html = _render(
        "Password Changed",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Your GoTot password was changed successfully.</p>
<p>If you did not make this change, please contact support immediately at <a href="mailto:support@gotot.app">support@gotot.app</a>.</p>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app/settings">Account Settings</a></p>""",
        unsubscribe="https://gotot.app/settings"
    )
    return await send_email(to, "Password changed - GoTot", body_text, html)


async def send_premium_purchase_email(to: str, username: str, plan: str, amount: str) -> bool:
    body_text = f"Thank you for upgrading to GoTot {plan}!"
    html = _render(
        "Welcome to Premium!",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Thank you for upgrading to <strong>GoTot {plan}</strong>!</p>
<p>Your plan costs <strong>{amount}</strong> and includes:</p>
<ul>
<li>{'Unlimited daily downloads' if plan == 'Unlimited' else 'More daily downloads'}</li>
<li>Priority processing</li>
<li>Higher quality options</li>
{'<li>API access</li>' if plan == 'Pro' or plan == 'Unlimited' else ''}
</ul>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app/dashboard">View Dashboard</a></p>"""
    )
    return await send_email(to, f"Welcome to GoTot {plan}!", body_text, html)


async def send_subscription_renewal_email(to: str, username: str, plan: str, amount: str, next_billing: str) -> bool:
    body_text = f"Your GoTot {plan} subscription has been renewed."
    html = _render(
        "Subscription Renewed",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Your <strong>GoTot {plan}</strong> subscription has been renewed.</p>
<p><strong>Amount:</strong> {amount}<br/>
<strong>Next billing date:</strong> {next_billing}</p>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app/dashboard">Manage Subscription</a></p>"""
    )
    return await send_email(to, f"GoTot {plan} subscription renewed", body_text, html)


async def send_referral_reward_email(to: str, username: str, bonus: int) -> bool:
    body_text = f"Someone used your referral link! You earned {bonus} bonus downloads."
    html = _render(
        "You Earned a Referral Reward!",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Someone used your referral link and created a GoTot account!</p>
<p>You earned <strong>+{bonus} bonus downloads</strong> as a reward.</p>
<p>Share your referral link with more friends to earn even more!</p>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app/referrals">View Referrals</a></p>"""
    )
    return await send_email(to, "You earned a referral reward!", body_text, html)


async def send_weekly_summary_email(to: str, username: str, downloads: int, platforms: list[str], credits: int) -> bool:
    platforms_str = ", ".join(platforms[:5])
    body_text = f"Your GoTot weekly summary: {downloads} downloads from {platforms_str}."
    html = _render(
        "Your Weekly Summary",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p>Here's your GoTot activity for the past week:</p>
<table style="width:100%;border-collapse:collapse;margin:16px 0">
<tr><td style="padding:8px;border:1px solid #e5e7eb"><strong>Downloads</strong></td><td style="padding:8px;border:1px solid #e5e7eb">{downloads}</td></tr>
<tr><td style="padding:8px;border:1px solid #e5e7eb"><strong>Platforms used</strong></td><td style="padding:8px;border:1px solid #e5e7eb">{platforms_str}</td></tr>
<tr><td style="padding:8px;border:1px solid #e5e7eb"><strong>Credits remaining</strong></td><td style="padding:8px;border:1px solid #e5e7eb">{credits}</td></tr>
</table>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app/dashboard">View Full Stats</a></p>"""
    )
    return await send_email(to, "Your GoTot Weekly Summary", body_text, html)


async def send_security_alert_email(to: str, username: str, alert_type: str, details: str) -> bool:
    body_text = f"Security alert: {alert_type} - {details}"
    html = _render(
        "Security Alert",
        f"""<p>Hi <strong>{username}</strong>,</p>
<p><strong>Alert type:</strong> {alert_type}</p>
<p><strong>Details:</strong> {details}</p>
<p>If this was you, no action is needed. If you don't recognize this activity, please secure your account immediately.</p>
<p style="text-align:center;margin:24px 0"><a class="btn" href="https://gotot.app/settings">Review Account</a></p>"""
    )
    return await send_email(to, f"Security Alert - {alert_type}", body_text, html)


async def send_contact_notification(name: str, email: str, message: str) -> bool:
    subject = f"New Contact Form Message from {name}"
    body_text = f"Name: {name}\nEmail: {email}\nMessage:\n{message}"
    html = _render(
        "New Contact Message",
        f"""<p><strong>From:</strong> {name} ({email})</p>
<p><strong>Message:</strong></p>
<blockquote style="padding:12px;border-left:4px solid #6366f1;background:#f9fafb;color:#374151">{message}</blockquote>
<p><a class="btn" href="mailto:{email}">Reply to {name}</a></p>"""
    )
    return await send_email(settings.admin_email, subject, body_text, html)
