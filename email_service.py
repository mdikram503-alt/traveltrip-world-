"""
TravelTrip World — Enterprise Email Service
Automated delivery for eSIM QR Profiles, Email Verification, and Password Recovery.
Supports SMTP (Hostinger, Zoho, Google Workspace, AWS SES) and Resend API.
"""

import os
import smtplib
import ssl
import json
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration loaded from Environment
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "TravelTrip World <support@traveltrip.world>")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SITE_URL = os.environ.get("SITE_URL", "https://traveltrip.world")

# In-memory recent email log for development & test inspection
RECENT_DISPATCHES = []

def is_smtp_configured() -> bool:
    """Returns True if live SMTP credentials are set."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

def is_resend_configured() -> bool:
    """Returns True if Resend API key is set."""
    return bool(RESEND_API_KEY)

def send_email(to_email: str, subject: str, html_content: str, text_content: str = None) -> dict:
    """
    Sends email via live SMTP, Resend API, or falls back gracefully to Mock mode with visual log.
    """
    to_clean = to_email.strip().lower()
    text_content = text_content or "TravelTrip World Notification"

    # 1. Try Resend API if configured
    if is_resend_configured():
        try:
            req_data = json.dumps({
                "from": SMTP_FROM,
                "to": [to_clean],
                "subject": subject,
                "html": html_content,
                "text": text_content
            }).encode("utf-8")
            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request("https://api.resend.com/emails", data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                record = {"status": "sent", "mode": "resend", "to": to_clean, "subject": subject, "id": data.get("id")}
                RECENT_DISPATCHES.append(record)
                return {"success": True, "mode": "resend", "id": data.get("id")}
        except Exception as e:
            print(f"[EMAIL RESEND ERROR] {e}")

    # 2. Try Standard SMTP
    if is_smtp_configured():
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM
            msg["To"] = to_clean

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            if SMTP_PORT == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, to_clean, msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                    server.starttls(context=ssl.create_default_context())
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_USER, to_clean, msg.as_string())

            record = {"status": "sent", "mode": "smtp", "to": to_clean, "subject": subject}
            RECENT_DISPATCHES.append(record)
            print(f"[EMAIL SENT VIA SMTP] To: {to_clean} | Subject: {subject}")
            return {"success": True, "mode": "smtp"}
        except Exception as e:
            print(f"[EMAIL SMTP ERROR] {e}")
            return {"success": False, "error": str(e)}

    # 3. Graceful Mock / Development Mode
    print(f"[MOCK EMAIL DISPATCH] (Configure SMTP_HOST in .env for live sending)")
    print(f" -> TO: {to_clean}")
    print(f" -> SUBJECT: {subject}")
    record = {"status": "mock_delivered", "mode": "mock", "to": to_clean, "subject": subject}
    RECENT_DISPATCHES.append(record)
    return {
        "success": True,
        "mode": "mock",
        "message": "Email logged in server console. To send live emails, configure SMTP_HOST/SMTP_USER/SMTP_PASSWORD in .env."
    }

# ==============================================================================
# EMAIL TEMPLATES
# ==============================================================================

def send_verification_email(to_email: str, name: str, token: str, base_url: str = None) -> dict:
    """Dispatches a branded email verification link to new signups."""
    base = base_url or SITE_URL
    verify_url = f"{base}/verify-email.html?token={token}&email={urllib.parse.quote(to_email)}"
    subject = "Verify your TravelTrip World Account 🌍"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#F8FAFC; margin:0; padding:30px 15px; color:#0E131F;">
      <div style="max-width:540px; margin:0 auto; background:#ffffff; border:1px solid #E2E8F0; border-radius:16px; padding:36px; box-shadow:0 4px 12px rgba(0,0,0,0.04);">
        <div style="text-align:center; margin-bottom:24px;">
          <h2 style="margin:0; font-size:24px; color:#3D38D0; letter-spacing:-0.02em;">traveltrip<span style="color:#F59E0B;">.world</span></h2>
          <p style="margin:4px 0 0; font-size:12px; font-weight:700; color:#64748B; letter-spacing:0.05em; text-transform:uppercase;">One eSIM. The Whole World.</p>
        </div>
        
        <h3 style="font-size:20px; font-weight:700; margin-bottom:12px; color:#0E131F;">Welcome aboard, {name or 'Traveler'}! ✈️</h3>
        <p style="font-size:15px; line-height:1.6; color:#475569; margin-bottom:24px;">
          Thank you for signing up with TravelTrip World. Please confirm your email address to activate your account, protect your purchases, and access your instant eSIM downloads anytime.
        </p>

        <div style="text-align:center; margin:32px 0;">
          <a href="{verify_url}" style="background:#3D38D0; color:#ffffff; padding:14px 28px; font-size:15px; font-weight:700; text-decoration:none; border-radius:10px; display:inline-block; box-shadow:0 2px 8px rgba(61,56,208,0.3);">
            Verify My Email Address
          </a>
        </div>

        <p style="font-size:13px; color:#94A3B8; line-height:1.5; margin-top:28px; word-break:break-all;">
          Or copy and paste this verification URL into your browser:<br>
          <a href="{verify_url}" style="color:#3D38D0;">{verify_url}</a>
        </p>

        <hr style="border:none; border-top:1px solid #E2E8F0; margin:28px 0 20px;">
        <p style="font-size:12px; color:#94A3B8; text-align:center; margin:0;">
          TravelTrip World &middot; Ajman Free Zone, UAE &middot; Need help? <a href="mailto:support@traveltrip.world" style="color:#3D38D0;">support@traveltrip.world</a>
        </p>
      </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, f"Verify your email: {verify_url}")

def send_password_reset_email(to_email: str, name: str, reset_code: str, token: str, base_url: str = None) -> dict:
    """Dispatches a password reset code and direct link."""
    base = base_url or SITE_URL
    reset_url = f"{base}/reset-password.html?token={token}&email={urllib.parse.quote(to_email)}"
    subject = "Reset your TravelTrip World Password 🔐"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#F8FAFC; margin:0; padding:30px 15px; color:#0E131F;">
      <div style="max-width:540px; margin:0 auto; background:#ffffff; border:1px solid #E2E8F0; border-radius:16px; padding:36px; box-shadow:0 4px 12px rgba(0,0,0,0.04);">
        <div style="text-align:center; margin-bottom:24px;">
          <h2 style="margin:0; font-size:24px; color:#3D38D0;">traveltrip<span style="color:#F59E0B;">.world</span></h2>
          <p style="margin:4px 0 0; font-size:12px; font-weight:700; color:#64748B; text-transform:uppercase;">Password Security Recovery</p>
        </div>
        
        <h3 style="font-size:19px; font-weight:700; margin-bottom:12px; color:#0E131F;">Hello {name or 'Traveler'},</h3>
        <p style="font-size:14.5px; line-height:1.6; color:#475569; margin-bottom:20px;">
          We received a request to reset the password for your TravelTrip World account. Use the 6-digit recovery code below or click the direct reset button.
        </p>

        <div style="background:#EEF2FF; border:1px solid #CDCAF6; border-radius:12px; padding:20px; text-align:center; margin:24px 0;">
          <div style="font-size:12px; font-weight:700; color:#3D38D0; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">Your 6-Digit Recovery Code</div>
          <div style="font-size:32px; font-weight:800; letter-spacing:6px; color:#1E1B4B; font-family:monospace;">{reset_code}</div>
          <div style="font-size:12px; color:#64748B; margin-top:6px;">Valid for 15 minutes</div>
        </div>

        <div style="text-align:center; margin:28px 0;">
          <a href="{reset_url}" style="background:#3D38D0; color:#ffffff; padding:13px 26px; font-size:14.5px; font-weight:700; text-decoration:none; border-radius:10px; display:inline-block;">
            Reset Password Directly
          </a>
        </div>

        <p style="font-size:12.5px; color:#94A3B8; line-height:1.5;">
          If you did not request a password reset, please ignore this email or contact <a href="mailto:support@traveltrip.world" style="color:#3D38D0;">support@traveltrip.world</a> immediately.
        </p>
      </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, f"Password reset code: {reset_code}. Link: {reset_url}")

def send_esim_delivery_email(to_email: str, buyer_name: str, order_id: str,
                             package_name: str, qr_code_url: str, lpa_string: str,
                             iccid: str, smdp_address: str = None, activation_code: str = None,
                             base_url: str = None) -> dict:
    """Dispatches the customer's active eSIM QR code, LPA string, and setup guide."""
    base = base_url or SITE_URL
    account_url = f"{base}/account"
    subject = f"Your eSIM is Ready! 📲 Order #{order_id} &middot; TravelTrip World"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#F8FAFC; margin:0; padding:24px 12px; color:#0E131F;">
      <div style="max-width:580px; margin:0 auto; background:#ffffff; border:1px solid #E2E8F0; border-radius:16px; padding:32px; box-shadow:0 4px 16px rgba(0,0,0,0.05);">
        
        <div style="text-align:center; margin-bottom:20px;">
          <h2 style="margin:0; font-size:24px; color:#3D38D0;">traveltrip<span style="color:#F59E0B;">.world</span></h2>
          <div style="display:inline-block; background:#E6F9F1; color:#00875A; font-weight:700; font-size:11.5px; padding:4px 12px; border-radius:20px; margin-top:8px;">
            eSIM ORDER DELIVERED & ACTIVATED
          </div>
        </div>

        <h3 style="font-size:19px; font-weight:700; margin:16px 0 8px; color:#0E131F;">Thank you, {buyer_name or 'Traveler'}! ✈️</h3>
        <p style="font-size:14.5px; line-height:1.6; color:#475569; margin:0 0 20px;">
          Your high-speed international eSIM for <strong>{package_name}</strong> is ready for instant installation. Follow the steps below to connect.
        </p>

        <!-- QR Code Box -->
        <div style="background:#F1F5F9; border:2px dashed #CBD5E1; border-radius:16px; padding:24px; text-align:center; margin-bottom:24px;">
          <div style="font-size:12px; font-weight:800; color:#475569; text-transform:uppercase; margin-bottom:12px; letter-spacing:0.04em;">
            Scan with iPhone or Android Camera
          </div>
          <img src="{qr_code_url}" alt="eSIM QR Code" style="width:210px; height:210px; border-radius:12px; background:#ffffff; padding:10px; box-shadow:0 2px 8px rgba(0,0,0,0.06); display:block; margin:0 auto;">
          <div style="font-size:12px; color:#64748B; margin-top:12px;">Make sure your device is connected to stable Wi-Fi during scan.</div>
        </div>

        <!-- Manual Activation Details -->
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:18px; margin-bottom:24px;">
          <div style="font-size:13px; font-weight:700; color:#0E131F; margin-bottom:12px;">Manual Activation Details (if camera cannot scan):</div>
          
          <table style="width:100%; font-size:13px; border-collapse:collapse;">
            <tr>
              <td style="padding:6px 0; color:#64748B; width:110px;"><strong>Order ID:</strong></td>
              <td style="padding:6px 0; font-family:monospace; font-weight:700; color:#3D38D0;">{order_id}</td>
            </tr>
            <tr>
              <td style="padding:6px 0; color:#64748B;"><strong>ICCID:</strong></td>
              <td style="padding:6px 0; font-family:monospace;">{iccid or 'Auto-assigned'}</td>
            </tr>
            <tr>
              <td style="padding:6px 0; color:#64748B;"><strong>SM-DP+ Host:</strong></td>
              <td style="padding:6px 0; font-family:monospace;">{smdp_address or 'rsp.esimaccess.com'}</td>
            </tr>
            <tr>
              <td style="padding:6px 0; color:#64748B;"><strong>Activation Code:</strong></td>
              <td style="padding:6px 0; font-family:monospace; font-weight:700;">{activation_code or '-'}</td>
            </tr>
          </table>

          <div style="margin-top:12px; padding-top:12px; border-top:1px solid #F1F5F9;">
            <div style="font-size:11.5px; font-weight:700; color:#64748B; margin-bottom:4px;">Universal LPA String:</div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:8px; font-family:monospace; font-size:11.5px; word-break:break-all; color:#1E293B;">
              {lpa_string or 'N/A'}
            </div>
          </div>
        </div>

        <!-- Installation Instructions -->
        <div style="font-size:13.5px; line-height:1.6; color:#475569; margin-bottom:24px;">
          <strong style="color:#0E131F;">Quick Setup Guide:</strong>
          <ol style="padding-left:20px; margin:8px 0 0;">
            <li><strong>iPhone:</strong> Settings &gt; Cellular (Mobile Data) &gt; Add eSIM &gt; Use QR Code.</li>
            <li><strong>Samsung/Android:</strong> Settings &gt; Connections &gt; SIM Manager &gt; Add eSIM &gt; Scan QR.</li>
            <li><strong>When Landing:</strong> Set Cellular Data to your TravelTrip eSIM and turn <strong>Data Roaming ON</strong>.</li>
          </ol>
        </div>

        <div style="text-align:center; margin:28px 0 16px;">
          <a href="{account_url}" style="background:#3D38D0; color:#ffffff; padding:13px 26px; font-size:14px; font-weight:700; text-decoration:none; border-radius:10px; display:inline-block;">
            View in My eSIM Portal
          </a>
        </div>

        <hr style="border:none; border-top:1px solid #E2E8F0; margin:24px 0 16px;">
        <div style="text-align:center; font-size:12px; color:#94A3B8; line-height:1.6;">
          24/7 WhatsApp Support: <a href="https://wa.me/971524413931" style="color:#25D366; font-weight:700;">+971 52 441 3931</a><br>
          Official Support Email: <a href="mailto:support@traveltrip.world" style="color:#3D38D0;">support@traveltrip.world</a><br>
          &copy; 2026 TravelTrip World. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, f"Your eSIM for {package_name} is ready. Order: {order_id}. LPA: {lpa_string}")

def send_test_email(to_email: str) -> dict:
    """Dispatches a diagnostic test email to verify live production email routing."""
    subject = "Production Email Delivery Test &middot; TravelTrip World"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:sans-serif; background:#F8FAFC; padding:24px;">
      <div style="max-width:500px; margin:0 auto; background:#fff; padding:28px; border-radius:12px; border:1px solid #E2E8F0;">
        <h2 style="color:#3D38D0; margin:0 0 12px;">✅ TravelTrip World Email Test Successful</h2>
        <p style="color:#475569; font-size:14.5px; line-height:1.5;">
          This confirms that your mail delivery pipeline (SMTP / Resend) is active and routing emails correctly.
        </p>
        <p style="font-size:12px; color:#94A3B8;">Sent at {urllib.parse.quote(str(os.environ.get('PORT', 8000)))} from TravelTrip Cloud Backend.</p>
      </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html, "TravelTrip World Email Test Passed.")
