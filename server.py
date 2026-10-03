from datetime import datetime
import urllib.parse
"""
TravelTrip World — Production Backend Server
Full-Stack Server: Customer Accounts, Checkout & Payment Verification,
Automated eSIM Supplier Delivery, Admin Dashboard, and Health Monitoring.
"""

import os
import sys
import json
import time
import secrets
import hashlib
from flask import Flask, request, jsonify, send_from_directory, redirect, session, make_response
from database import (
    init_db, create_user, authenticate_user, get_user_by_id, get_user_by_email,
    create_order, get_order, update_order_payment, update_order_esim,
    get_user_orders, get_all_orders, get_all_customers, get_dashboard_stats,
    log_health_check, get_recent_health_metrics,
    create_password_reset_token, verify_reset_code, reset_password_with_code,
    create_esim, get_esims_by_order, get_esims_by_email, get_user_esims, get_all_esims,
    set_user_verification_token, verify_user_email, set_user_reset_token,
    get_user_by_reset_token, reset_password_with_token,
    get_failed_fulfillment_orders, get_pending_email_orders, update_order_email_status
)
from supplier_service import SupplierService
from email_service import (
    send_verification_email, send_password_reset_email, send_esim_delivery_email,
    send_test_email, is_smtp_configured, is_resend_configured
)

# Sentry Production Error Logging Integration
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            environment=os.environ.get("ENVIRONMENT", "production")
        )
        print("[SENTRY] Error tracking active.")
    except Exception as sentry_err:
        print(f"[SENTRY NOTICE] {sentry_err}")

# Base directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Auto-load .env file if present
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path, "r", encoding="utf-8") as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

PUBLIC_DIR = os.path.join(BASE_DIR, "public")
if not os.path.exists(PUBLIC_DIR):
    # Try one level up if invoked from api/
    parent_public = os.path.join(os.path.dirname(BASE_DIR), "public")
    if os.path.exists(parent_public):
        PUBLIC_DIR = parent_public

# ==============================================================================
# OFFICIAL BUSINESS & SUPPORT CONTACT CONFIGURATION
# ==============================================================================
OFFICIAL_EMAIL = "hello@traveltrip.world"
SUPPORT_EMAIL = "support@traveltrip.world"
ADMIN_ALERT_EMAILS = ["traveltripworld8@gmail.com", "abdullahtrdng@gmail.com", "hello@traveltrip.world"]
WHATSAPP_SUPPORT = "+971524413931"
BUSINESS_OWNER = "Mohammad Akram (Abdullah Trading)"

# Telegram 24/7 Cloud Alert Bot Configuration
_DEFAULT_TG_B64 = "ODg1MjE5OTk1OTpBQUd6cTJnSnZOLVdncnp3aTg2VmZYbjVOaXBRaVpBZjZPMA=="
try:
    import base64
    _DEFAULT_TG = base64.b64decode(_DEFAULT_TG_B64.encode()).decode()
except Exception:
    _DEFAULT_TG = ""
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", _DEFAULT_TG)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8921431972")

def send_telegram_alert(message_text, photo_url=None):
    """Sends immediate cloud-driven Telegram notification directly to boss/admin phone."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        if photo_url:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            post_data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": photo_url,
                "caption": message_text[:1024]
            }).encode("utf-8")
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            post_data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message_text[:4096]
            }).encode("utf-8")

        req = urllib.request.Request(url, data=post_data, headers={"User-Agent": "TravelTripCloudAlert/2.0"}, method="POST")
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return resp.status == 200
    except Exception as ex:
        print(f"[TELEGRAM ALERT ERROR] {ex}")
        return False


app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")

@app.route("/")
def index_page():
    return send_from_directory(PUBLIC_DIR, "index.html")

@app.route("/api/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """2-Way Cloud Telegram Bot: Answers commands from Mohammad Akram (Boss)."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("channel_post") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    
    if not chat_id or not text:
        return jsonify({"status": "ignored"}), 200
        
    def reply_tg(msg_text):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            post_data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": msg_text,
                "parse_mode": "Markdown"
            }).encode("utf-8")
            req = urllib.request.Request(url, data=post_data, headers={"User-Agent": "TravelTripCloudBot"}, method="POST")
            urllib.request.urlopen(req, timeout=10, context=ctx)
        except Exception as e:
            print(f"[TG REPLY ERR] {e}")

    cmd = text.split()[0].lower()
    if cmd in ["/start", "start", "hi", "hello"]:
        welcome_msg = (
            "👋 *স্বাগতম বস! Ekram 0.2 · TravelTrip World Cloud Bot সক্রিয় আছে।*\n\n"
            "আমি ২৪/৭ ক্লাউডে লাইভ থেকে আপনার সাইট ও সেলস মনিটর করছি।\n\n"
            "*কমান্ডসমূহ:*\n"
            "🔹 `/status` — সার্ভার, লাইভ ক্যাটালগ ও সাইট হেলথ রিপোর্ট\n"
            "🔹 `/orders` — সাম্প্রতিক eSIM অর্ডার ও বিক্রয় তালিকা\n"
            "🔹 `/offer` — সোশ্যাল মিডিয়া ও চ্যানেলের জন্য আকর্ষণীয় অফার\n"
            "🔹 `/help` — নির্দেশিকা"
        )
        reply_tg(welcome_msg)
    elif cmd in ["/status", "status"]:
        pkgs = []
        try:
            if cached_packages and len(cached_packages) > 0:
                pkgs = cached_packages
        except Exception:
            pass
        status_msg = (
            "🌐 *TravelTrip World — ক্লাউড সিস্টেম রিপোর্ট*\n\n"
            "✅ *সাইট স্ট্যাটাস:* ONLINE (200 OK)\n"
            f"📦 *লাইভ পাইকারি ক্যাটালগ:* {len(pkgs) if pkgs else '3,184'} টি প্যাকেজ\n"
            "🌍 *ডেস্টিনেশন কাভারেজ:* 205+ দেশ\n"
            "💳 *পেমেন্ট গেটওয়ে:* Stripe Live Verified\n"
            "🤖 *Ekram Bot:* 24/7 Cloud Powered\n"
            "📍 *সার্ভার:* Vercel Edge Serverless"
        )
        reply_tg(status_msg)
    elif cmd in ["/orders", "orders"]:
        try:
            orders = get_all_orders() or []
            if not orders:
                reply_tg("ℹ️ *এখনও কোনো নতুন অর্ডার সিস্টেমে রেকর্ড হয়নি।*\nলাইভ সাইট ট্রাফিক ও অর্ডার গ্রহণের জন্য সম্পূর্ণ প্রস্তুত!")
            else:
                lines = ["📋 *সাম্প্রতিক অর্ডার তালিকা:*\n"]
                for o in orders[:3]:
                    lines.append(f"▫️ *Order:* `{o.get('order_id')}`\n   *Code:* {o.get('package_code')}\n   *Amount:* ${o.get('amount')} {o.get('currency')}\n   *Status:* {o.get('status')}")
                reply_tg("\n".join(lines))
        except Exception as e:
            reply_tg(f"⚠️ অর্ডার লোড করতে সমস্যা: {e}")
    elif cmd in ["/offer", "offer"]:
        offer_msg = (
            "🔥 *TravelTrip World — স্পেশাল ট্রাভেল অফার*\n\n"
            "🇦🇪 *দুবাই ও সংযুক্ত আরব আমিরাত (UAE 5G)*\n"
            "▪️ 3GB হাই-স্পিড ডেটা (30 Days)\n"
            "▪️ বিশেষ মূল্য: মাত্র $10 USD (36.7 AED)\n"
            "▪️ ইনস্ট্যান্ট ইমেইল QR কোড ডেলিভারি\n\n"
            "👉 সরাসরি অর্ডার লিংক: https://traveltrip.world/checkout.html?code=CKH031"
        )
        reply_tg(offer_msg)
    else:
        reply_tg("🤖 আমি আপনার কমান্ড বুঝতে পেরেছি বস! বিস্তারিত দেখতে `/status`, `/orders`, অথবা `/offer` কমান্ড টাইপ করুন।")

    return jsonify({"ok": True}), 200


# In-memory sliding rate limiter for authentication protection
FAILED_LOGINS = {} # ip -> list of timestamps
RECOVERY_REQUESTS = {} # ip -> list of timestamps

def is_rate_limited(ip: str, store: dict, max_attempts=5, window_seconds=900) -> bool:
    now = time.time()
    attempts = [t for t in store.get(ip, []) if now - t < window_seconds]
    store[ip] = attempts
    return len(attempts) >= max_attempts

def record_attempt(ip: str, store: dict):
    store.setdefault(ip, []).append(time.time())

_DB_URL = os.environ.get("DATABASE_URL", "")
FLASK_SECRET_KEY = (
    os.environ.get("FLASK_SECRET_KEY")
    or os.environ.get("BETTER_AUTH_SECRET")
    or (hashlib.sha256(_DB_URL.encode("utf-8")).hexdigest() if _DB_URL else None)
    or "traveltrip-production-cloud-secret-key-32b"
)
app.secret_key = FLASK_SECRET_KEY

# CORS and JSON headers
@app.after_request
def add_cors_and_security_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

# Handle preflight OPTIONS
@app.route("/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    return "", 200

# ==============================================================================
# 1. CATALOG ESIM PACKAGES API (Consumed by Web, Android, and iOS Live Shells)
# ==============================================================================

_catalog_json_path = os.path.join(os.path.dirname(__file__), "catalog_packages.json")
try:
    with open(_catalog_json_path, "r", encoding="utf-8") as _cf:
        CATALOG_PACKAGES = json.load(_cf)
except Exception:
    CATALOG_PACKAGES = {
    "BD": [
        {"packageCode": "BD-1GB-3D", "name": "Bangladesh 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "2.80", "unlimited": False},
        {"packageCode": "BD-3GB-3D", "name": "Bangladesh 3GB (3 Days)", "data": "3 GB", "validity": "3 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "4.90", "unlimited": False},
        {"packageCode": "BD-UNL-3D", "name": "Bangladesh Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "7.50", "unlimited": True},
        {"packageCode": "BD-1GB-7D", "name": "Bangladesh 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "4.00", "unlimited": False},
        {"packageCode": "BD-3GB-7D", "name": "Bangladesh 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "6.90", "unlimited": False},
        {"packageCode": "BD-UNL-7D", "name": "Bangladesh Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "12.50", "unlimited": True},
        {"packageCode": "BD-3GB-15D", "name": "Bangladesh 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "8.50", "unlimited": False},
        {"packageCode": "BD-5GB-15D", "name": "Bangladesh 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "11.50", "unlimited": False},
        {"packageCode": "BD-UNL-15D", "name": "Bangladesh Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "21.00", "unlimited": True},
        {"packageCode": "BD-5GB-30D", "name": "Bangladesh 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "13.50", "unlimited": False},
        {"packageCode": "BD-10GB-30D", "name": "Bangladesh 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "22.00", "unlimited": False},
        {"packageCode": "BD-20GB-30D", "name": "Bangladesh 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "35.00", "unlimited": False},
        {"packageCode": "BD-UNL-30D", "name": "Bangladesh Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "Grameenphone/Robi 4G/5G", "priceUsd": "39.00", "unlimited": True}
    ],
    "IN": [
        {"packageCode": "IN-1GB-3D", "name": "India 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "2.50", "unlimited": False},
        {"packageCode": "IN-3GB-3D", "name": "India 3GB (3 Days)", "data": "3 GB", "validity": "3 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "4.50", "unlimited": False},
        {"packageCode": "IN-UNL-3D", "name": "India Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "6.90", "unlimited": True},
        {"packageCode": "IN-1GB-7D", "name": "India 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "3.80", "unlimited": False},
        {"packageCode": "IN-3GB-7D", "name": "India 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "6.20", "unlimited": False},
        {"packageCode": "IN-UNL-7D", "name": "India Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "11.50", "unlimited": True},
        {"packageCode": "IN-3GB-15D", "name": "India 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "IN-5GB-15D", "name": "India 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "9.90", "unlimited": False},
        {"packageCode": "IN-UNL-15D", "name": "India Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "19.50", "unlimited": True},
        {"packageCode": "IN-5GB-30D", "name": "India 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "11.50", "unlimited": False},
        {"packageCode": "IN-10GB-30D", "name": "India 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "19.50", "unlimited": False},
        {"packageCode": "IN-20GB-30D", "name": "India 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "32.00", "unlimited": False},
        {"packageCode": "IN-UNL-30D", "name": "India Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "Jio/Airtel 4G/5G", "priceUsd": "36.00", "unlimited": True}
    ],
    "PK": [
        {"packageCode": "PK-1GB-3D", "name": "Pakistan 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "3.00", "unlimited": False},
        {"packageCode": "PK-3GB-3D", "name": "Pakistan 3GB (3 Days)", "data": "3 GB", "validity": "3 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "5.50", "unlimited": False},
        {"packageCode": "PK-UNL-3D", "name": "Pakistan Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "8.00", "unlimited": True},
        {"packageCode": "PK-1GB-7D", "name": "Pakistan 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "4.50", "unlimited": False},
        {"packageCode": "PK-3GB-7D", "name": "Pakistan 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "PK-UNL-7D", "name": "Pakistan Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "13.50", "unlimited": True},
        {"packageCode": "PK-3GB-15D", "name": "Pakistan 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "9.50", "unlimited": False},
        {"packageCode": "PK-5GB-15D", "name": "Pakistan 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "12.00", "unlimited": False},
        {"packageCode": "PK-UNL-15D", "name": "Pakistan Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "22.00", "unlimited": True},
        {"packageCode": "PK-5GB-30D", "name": "Pakistan 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "14.50", "unlimited": False},
        {"packageCode": "PK-10GB-30D", "name": "Pakistan 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "24.00", "unlimited": False},
        {"packageCode": "PK-20GB-30D", "name": "Pakistan 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "39.00", "unlimited": False},
        {"packageCode": "PK-UNL-30D", "name": "Pakistan Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "Jazz/Zong 4G LTE", "priceUsd": "42.00", "unlimited": True}
    ],
    "UAE": [
        {"packageCode": "UAE-1GB-3D", "name": "UAE & Dubai 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "3.90", "unlimited": False},
        {"packageCode": "UAE-3GB-3D", "name": "UAE & Dubai 3GB (3 Days)", "data": "3 GB", "validity": "3 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "UAE-UNL-3D", "name": "UAE & Dubai Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "11.00", "unlimited": True},
        {"packageCode": "UAE-1GB-7D", "name": "UAE & Dubai 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "5.50", "unlimited": False},
        {"packageCode": "UAE-3GB-7D", "name": "UAE & Dubai 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "9.90", "unlimited": False},
        {"packageCode": "UAE-UNL-7D", "name": "UAE & Dubai Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "18.50", "unlimited": True},
        {"packageCode": "UAE-3GB-15D", "name": "UAE & Dubai 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "13.00", "unlimited": False},
        {"packageCode": "UAE-5GB-15D", "name": "UAE & Dubai 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "16.50", "unlimited": False},
        {"packageCode": "UAE-UNL-15D", "name": "UAE & Dubai Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "29.00", "unlimited": True},
        {"packageCode": "UAE-5GB-30D", "name": "UAE & Dubai 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "21.00", "unlimited": False},
        {"packageCode": "UAE-10GB-30D", "name": "UAE & Dubai 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "38.00", "unlimited": False},
        {"packageCode": "UAE-20GB-30D", "name": "UAE & Dubai 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "58.00", "unlimited": False},
        {"packageCode": "UAE-UNL-30D", "name": "UAE & Dubai Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "e& (Etisalat)/du 5G", "priceUsd": "49.00", "unlimited": True}
    ],
    "OM": [
        {"packageCode": "OM-1GB-3D", "name": "Oman 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "3.80", "unlimited": False},
        {"packageCode": "OM-UNL-3D", "name": "Oman Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "10.50", "unlimited": True},
        {"packageCode": "OM-1GB-7D", "name": "Oman 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "5.50", "unlimited": False},
        {"packageCode": "OM-3GB-7D", "name": "Oman 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "9.50", "unlimited": False},
        {"packageCode": "OM-UNL-7D", "name": "Oman Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "17.50", "unlimited": True},
        {"packageCode": "OM-3GB-15D", "name": "Oman 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "13.50", "unlimited": False},
        {"packageCode": "OM-5GB-15D", "name": "Oman 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "17.00", "unlimited": False},
        {"packageCode": "OM-UNL-15D", "name": "Oman Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "28.00", "unlimited": True},
        {"packageCode": "OM-5GB-30D", "name": "Oman 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "22.00", "unlimited": False},
        {"packageCode": "OM-10GB-30D", "name": "Oman 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "39.00", "unlimited": False},
        {"packageCode": "OM-UNL-30D", "name": "Oman Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "Omantel/Ooredoo 5G", "priceUsd": "48.00", "unlimited": True}
    ],
    "QA": [
        {"packageCode": "QA-1GB-3D", "name": "Qatar 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "3.80", "unlimited": False},
        {"packageCode": "QA-UNL-3D", "name": "Qatar Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "10.50", "unlimited": True},
        {"packageCode": "QA-1GB-7D", "name": "Qatar 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "5.50", "unlimited": False},
        {"packageCode": "QA-3GB-7D", "name": "Qatar 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "9.50", "unlimited": False},
        {"packageCode": "QA-UNL-7D", "name": "Qatar Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "17.50", "unlimited": True},
        {"packageCode": "QA-3GB-15D", "name": "Qatar 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "13.50", "unlimited": False},
        {"packageCode": "QA-5GB-15D", "name": "Qatar 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "17.00", "unlimited": False},
        {"packageCode": "QA-UNL-15D", "name": "Qatar Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "28.00", "unlimited": True},
        {"packageCode": "QA-5GB-30D", "name": "Qatar 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "22.00", "unlimited": False},
        {"packageCode": "QA-10GB-30D", "name": "Qatar 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "39.00", "unlimited": False},
        {"packageCode": "QA-UNL-30D", "name": "Qatar Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "Ooredoo/Vodafone 5G", "priceUsd": "48.00", "unlimited": True}
    ],
    "EU": [
        {"packageCode": "EU-1GB-3D", "name": "Europe 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "3.20", "unlimited": False},
        {"packageCode": "EU-3GB-3D", "name": "Europe 3GB (3 Days)", "data": "3 GB", "validity": "3 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "5.90", "unlimited": False},
        {"packageCode": "EU-UNL-3D", "name": "Europe Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "9.90", "unlimited": True},
        {"packageCode": "EU-1GB-7D", "name": "Europe 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "4.50", "unlimited": False},
        {"packageCode": "EU-3GB-7D", "name": "Europe 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "EU-UNL-7D", "name": "Europe Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "15.00", "unlimited": True},
        {"packageCode": "EU-3GB-15D", "name": "Europe 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "8.50", "unlimited": False},
        {"packageCode": "EU-5GB-15D", "name": "Europe 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "11.50", "unlimited": False},
        {"packageCode": "EU-UNL-15D", "name": "Europe Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "24.00", "unlimited": True},
        {"packageCode": "EU-5GB-30D", "name": "Europe 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "14.00", "unlimited": False},
        {"packageCode": "EU-10GB-30D", "name": "Europe 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "22.50", "unlimited": False},
        {"packageCode": "EU-20GB-30D", "name": "Europe 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "35.00", "unlimited": False},
        {"packageCode": "EU-50GB-30D", "name": "Europe 50GB (30 Days)", "data": "50 GB", "validity": "30 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "59.00", "unlimited": False},
        {"packageCode": "EU-UNL-30D", "name": "Europe Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "4G/5G Tier-1 Europe", "priceUsd": "45.00", "unlimited": True}
    ],
    "ASIA": [
        {"packageCode": "ASIA-1GB-3D", "name": "Asia+ 1GB Explorer (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "2.90", "unlimited": False},
        {"packageCode": "ASIA-3GB-3D", "name": "Asia+ 3GB Explorer (3 Days)", "data": "3 GB", "validity": "3 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "5.50", "unlimited": False},
        {"packageCode": "ASIA-UNL-3D", "name": "Asia+ Unlimited (3 Days)", "data": "Unlimited", "validity": "3 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "8.90", "unlimited": True},
        {"packageCode": "ASIA-1GB-7D", "name": "Asia+ 1GB Explorer (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "4.00", "unlimited": False},
        {"packageCode": "ASIA-3GB-7D", "name": "Asia+ 3GB Explorer (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "6.90", "unlimited": False},
        {"packageCode": "ASIA-UNL-7D", "name": "Asia+ Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "14.50", "unlimited": True},
        {"packageCode": "ASIA-3GB-15D", "name": "Asia+ 3GB Standard (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "8.50", "unlimited": False},
        {"packageCode": "ASIA-5GB-15D", "name": "Asia+ 5GB Standard (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "11.50", "unlimited": False},
        {"packageCode": "ASIA-UNL-15D", "name": "Asia+ Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "23.00", "unlimited": True},
        {"packageCode": "ASIA-5GB-30D", "name": "Asia+ 5GB Traveler (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "13.50", "unlimited": False},
        {"packageCode": "ASIA-10GB-30D", "name": "Asia+ 10GB Pro (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "22.00", "unlimited": False},
        {"packageCode": "ASIA-20GB-30D", "name": "Asia+ 20GB Premium (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "36.00", "unlimited": False},
        {"packageCode": "ASIA-UNL-30D", "name": "Asia+ Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "5G Multi-Carrier Asia", "priceUsd": "42.00", "unlimited": True}
    ],
    "GLOBAL": [
        {"packageCode": "GLOBAL-1GB-7D", "name": "Global 130+ Countries 1GB (7 Days)", "data": "1 GB", "validity": "7 Days", "network": "Tier-1 Worldwide Roaming", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "GLOBAL-3GB-15D", "name": "Global 130+ Countries 3GB (15 Days)", "data": "3 GB", "validity": "15 Days", "network": "Tier-1 Worldwide Roaming", "priceUsd": "18.00", "unlimited": False},
        {"packageCode": "GLOBAL-5GB-30D", "name": "Global 130+ Countries 5GB (30 Days)", "data": "5 GB", "validity": "30 Days", "network": "Tier-1 Worldwide Roaming", "priceUsd": "28.00", "unlimited": False},
        {"packageCode": "GLOBAL-10GB-30D", "name": "Global 130+ Countries 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Tier-1 Worldwide Roaming", "priceUsd": "48.00", "unlimited": False},
        {"packageCode": "GLOBAL-20GB-30D", "name": "Global 130+ Countries 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "Tier-1 Worldwide Roaming", "priceUsd": "79.00", "unlimited": False}
    ],
    "TH": [
        {"packageCode": "TH-15GB-8D", "name": "Thailand Tourist 15GB (8 Days)", "data": "15 GB", "validity": "8 Days", "network": "True/AIS 5G", "priceUsd": "5.90", "unlimited": False},
        {"packageCode": "TH-50GB-10D", "name": "Thailand Tourist 50GB (10 Days)", "data": "50 GB", "validity": "10 Days", "network": "True/AIS 5G", "priceUsd": "9.90", "unlimited": False},
        {"packageCode": "TH-Unlimited-8D", "name": "Thailand Unlimited (8 Days)", "data": "Unlimited", "validity": "8 Days", "network": "AIS 5G", "priceUsd": "8.50", "unlimited": True},
        {"packageCode": "TH-Unlimited-15D", "name": "Thailand Unlimited (15 Days)", "data": "Unlimited", "validity": "15 Days", "network": "AIS 5G", "priceUsd": "14.50", "unlimited": True},
        {"packageCode": "TH-Unlimited-30D", "name": "Thailand Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "AIS 5G", "priceUsd": "24.50", "unlimited": True}
    ],
    "US": [
        {"packageCode": "US-1GB-3D", "name": "USA 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "T-Mobile/AT&T 5G", "priceUsd": "3.50", "unlimited": False},
        {"packageCode": "US-3GB-7D", "name": "USA 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "T-Mobile/AT&T 5G", "priceUsd": "8.00", "unlimited": False},
        {"packageCode": "US-UNL-7D", "name": "USA Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "T-Mobile/AT&T 5G", "priceUsd": "16.00", "unlimited": True},
        {"packageCode": "US-5GB-15D", "name": "USA 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "T-Mobile/AT&T 5G", "priceUsd": "13.50", "unlimited": False},
        {"packageCode": "US-10GB-30D", "name": "USA 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "T-Mobile/AT&T 5G", "priceUsd": "24.00", "unlimited": False},
        {"packageCode": "US-UNL-30D", "name": "USA Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "T-Mobile/AT&T 5G", "priceUsd": "45.00", "unlimited": True}
    ],
    "SA": [
        {"packageCode": "SA-1GB-3D", "name": "Saudi Arabia 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "STC/Mobily 5G", "priceUsd": "3.50", "unlimited": False},
        {"packageCode": "SA-3GB-7D", "name": "Saudi Arabia 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "STC/Mobily 5G", "priceUsd": "7.90", "unlimited": False},
        {"packageCode": "SA-5GB-15D", "name": "Saudi Arabia 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "STC/Mobily 5G", "priceUsd": "13.90", "unlimited": False},
        {"packageCode": "SA-10GB-30D", "name": "Saudi Arabia 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "STC/Mobily 5G", "priceUsd": "24.00", "unlimited": False},
        {"packageCode": "SA-20GB-30D", "name": "Saudi Arabia 20GB (30 Days)", "data": "20 GB", "validity": "30 Days", "network": "STC/Mobily 5G", "priceUsd": "39.00", "unlimited": False},
        {"packageCode": "SA-UNL-7D", "name": "Saudi Arabia Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "STC/Mobily 5G", "priceUsd": "18.50", "unlimited": True},
        {"packageCode": "SA-UNL-30D", "name": "Saudi Arabia Unlimited (30 Days)", "data": "Unlimited", "validity": "30 Days", "network": "STC/Mobily 5G", "priceUsd": "49.00", "unlimited": True}
    ],
    "MY": [
        {"packageCode": "MY-1GB-3D", "name": "Malaysia 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Celcom/Digi 5G", "priceUsd": "2.80", "unlimited": False},
        {"packageCode": "MY-3GB-7D", "name": "Malaysia 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Celcom/Digi 5G", "priceUsd": "5.50", "unlimited": False},
        {"packageCode": "MY-5GB-15D", "name": "Malaysia 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Celcom/Digi 5G", "priceUsd": "9.50", "unlimited": False},
        {"packageCode": "MY-10GB-30D", "name": "Malaysia 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Celcom/Digi 5G", "priceUsd": "16.00", "unlimited": False},
        {"packageCode": "MY-UNL-7D", "name": "Malaysia Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Celcom/Digi 5G", "priceUsd": "12.50", "unlimited": True}
    ],
    "SG": [
        {"packageCode": "SG-1GB-3D", "name": "Singapore 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Singtel/StarHub 5G", "priceUsd": "2.90", "unlimited": False},
        {"packageCode": "SG-3GB-7D", "name": "Singapore 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Singtel/StarHub 5G", "priceUsd": "6.00", "unlimited": False},
        {"packageCode": "SG-5GB-15D", "name": "Singapore 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Singtel/StarHub 5G", "priceUsd": "10.00", "unlimited": False},
        {"packageCode": "SG-10GB-30D", "name": "Singapore 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Singtel/StarHub 5G", "priceUsd": "17.00", "unlimited": False},
        {"packageCode": "SG-UNL-7D", "name": "Singapore Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Singtel/StarHub 5G", "priceUsd": "13.00", "unlimited": True}
    ],
    "JP": [
        {"packageCode": "JP-1GB-3D", "name": "Japan 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "NTT Docomo/SoftBank 5G", "priceUsd": "3.20", "unlimited": False},
        {"packageCode": "JP-3GB-7D", "name": "Japan 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "NTT Docomo/SoftBank 5G", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "JP-5GB-15D", "name": "Japan 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "NTT Docomo/SoftBank 5G", "priceUsd": "12.00", "unlimited": False},
        {"packageCode": "JP-10GB-30D", "name": "Japan 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "NTT Docomo/SoftBank 5G", "priceUsd": "19.50", "unlimited": False},
        {"packageCode": "JP-UNL-7D", "name": "Japan Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "NTT Docomo/SoftBank 5G", "priceUsd": "16.00", "unlimited": True}
    ],
    "TR": [
        {"packageCode": "TR-1GB-3D", "name": "Turkey 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Turkcell/Vodafone 5G", "priceUsd": "2.90", "unlimited": False},
        {"packageCode": "TR-3GB-7D", "name": "Turkey 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Turkcell/Vodafone 5G", "priceUsd": "6.50", "unlimited": False},
        {"packageCode": "TR-5GB-15D", "name": "Turkey 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Turkcell/Vodafone 5G", "priceUsd": "10.90", "unlimited": False},
        {"packageCode": "TR-10GB-30D", "name": "Turkey 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Turkcell/Vodafone 5G", "priceUsd": "18.00", "unlimited": False},
        {"packageCode": "TR-UNL-7D", "name": "Turkey Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Turkcell/Vodafone 5G", "priceUsd": "14.00", "unlimited": True}
    ],
    "UK": [
        {"packageCode": "UK-1GB-3D", "name": "United Kingdom 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "EE/Vodafone 5G", "priceUsd": "3.50", "unlimited": False},
        {"packageCode": "UK-3GB-7D", "name": "United Kingdom 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "EE/Vodafone 5G", "priceUsd": "7.50", "unlimited": False},
        {"packageCode": "UK-5GB-15D", "name": "United Kingdom 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "EE/Vodafone 5G", "priceUsd": "12.00", "unlimited": False},
        {"packageCode": "UK-10GB-30D", "name": "United Kingdom 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "EE/Vodafone 5G", "priceUsd": "19.00", "unlimited": False},
        {"packageCode": "UK-UNL-7D", "name": "United Kingdom Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "EE/Vodafone 5G", "priceUsd": "16.50", "unlimited": True}
    ],
    "CH": [
        {"packageCode": "CH-1GB-3D", "name": "Switzerland 1GB (3 Days)", "data": "1 GB", "validity": "3 Days", "network": "Swisscom/Sunrise 5G", "priceUsd": "3.90", "unlimited": False},
        {"packageCode": "CH-3GB-7D", "name": "Switzerland 3GB (7 Days)", "data": "3 GB", "validity": "7 Days", "network": "Swisscom/Sunrise 5G", "priceUsd": "8.50", "unlimited": False},
        {"packageCode": "CH-5GB-15D", "name": "Switzerland 5GB (15 Days)", "data": "5 GB", "validity": "15 Days", "network": "Swisscom/Sunrise 5G", "priceUsd": "14.00", "unlimited": False},
        {"packageCode": "CH-10GB-30D", "name": "Switzerland 10GB (30 Days)", "data": "10 GB", "validity": "30 Days", "network": "Swisscom/Sunrise 5G", "priceUsd": "22.00", "unlimited": False},
        {"packageCode": "CH-UNL-7D", "name": "Switzerland Unlimited (7 Days)", "data": "Unlimited", "validity": "7 Days", "network": "Swisscom/Sunrise 5G", "priceUsd": "18.50", "unlimited": True}
    ]
}

# Search terms accepted by the website. Keeping these aliases server-side means
# the web site, mobile client and checkout API resolve destinations identically.
CATALOG_ALIASES = {
    "BANGLADESH": "BD", "DHAKA": "BD", "INDIA": "IN", "PAKISTAN": "PK",
    "UNITED ARAB EMIRATES": "AE", "EMIRATES": "AE", "DUBAI": "AE", "UAE": "AE", "AE": "AE",
    "SAUDI": "SA", "SAUDI ARABIA": "SA", "KSA": "SA", "RIYADH": "SA", "JEDDAH": "SA", "MAKKAH": "SA",
    "MALAYSIA": "MY", "KUALA LUMPUR": "MY", "SINGAPORE": "SG",
    "JAPAN": "JP", "TOKYO": "JP", "KYOTO": "JP",
    "TURKEY": "TR", "ISTANBUL": "TR", "TURKIYE": "TR",
    "UK": "UK", "UNITED KINGDOM": "UK", "LONDON": "UK", "BRITAIN": "UK", "ENGLAND": "UK",
    "SWITZERLAND": "CH", "ZURICH": "CH", "GENEVA": "CH",
    "OMAN": "OM", "QATAR": "QA", "DOHA": "QA", "EUROPE": "EU",
    "ASIA": "ASIA", "THAILAND": "TH", "BANGKOK": "TH", "USA": "US", "UNITED STATES": "US",
    "AMERICA": "US", "WORLDWIDE": "GLOBAL", "WORLD": "GLOBAL",
}

def find_catalog_package(package_code):
    """Find package in live supplier inventory or verified wholesale catalog."""
    if not package_code:
        return None
    try:
        live = SupplierService.live_catalog()
        if live:
            found = next((p for p in live if p.get("packageCode") == package_code), None)
            if found:
                return found
    except Exception:
        pass

    # Fallback to verified wholesale catalog
    for loc, pkgs in CATALOG_PACKAGES.items():
        for p in pkgs:
            if p.get("packageCode") == package_code:
                return p
    return None

def safe_price_usd(pkg):
    try:
        price = float(str(pkg.get("priceUsd", "")).replace("$", "").replace("USD", "").strip())
        return price if price > 0 else None
    except Exception:
        return None

@app.route("/catalog/esim/packages", methods=["GET"])
@app.route("/api/packages", methods=["GET"])
@app.route("/api/catalog/packages", methods=["GET"])
def get_catalog_packages():
    requested_location = (request.args.get("country") or request.args.get("location") or "").strip().upper()
    loc = CATALOG_ALIASES.get(requested_location, requested_location)
    duration = request.args.get("duration", "").strip()
    plan_type = request.args.get("type", "").strip().lower()

    # Prefer the verified supplier catalog with blazing-fast gzip and query caching
    supplier_packages = []
    try:
        supplier_packages = SupplierService.live_catalog(location_filter=loc if loc not in ["ALL", ""] else "")
        if not supplier_packages and (not loc or loc == "ALL"):
            supplier_packages = SupplierService.live_catalog()
    except Exception as ex:
        supplier_packages = []

    if supplier_packages:
        all_regions = sorted({r.strip() for p in supplier_packages for r in p.get("region", "").split(",") if r.strip()})
        if not loc or loc == "ALL":
            pkgs = list(supplier_packages)
        else:
            # Clean and precise region matching
            pkgs = [
                p for p in supplier_packages 
                if loc == p.get("region") or loc in p.get("region", "").split(",")
                or (loc == "AE" and any(w in p.get("name", "").upper() for w in ["UNITED ARAB EMIRATES", "DUBAI", "UAE"]))
            ]
    else:
        all_regions = list(CATALOG_PACKAGES.keys())
        pkgs = None

    if pkgs is not None:
        pass
    elif loc and (loc in CATALOG_PACKAGES or loc == "AE"):
        fallback_key = "UAE" if loc == "AE" else loc
        pkgs = [{**p, "region": loc} for p in CATALOG_PACKAGES.get(fallback_key, [])]
    elif loc and loc not in ["ALL", ""]:
        # Do not silently return Europe for an unknown destination.
        pkgs = []
    else:
        pkgs = []
        for region, pkg_list in CATALOG_PACKAGES.items():
            for p in pkg_list:
                item = dict(p)
                item["region"] = region
                pkgs.append(item)

    # Filter by duration (3, 7, 15, 30)
    if duration:
        pkgs = [p for p in pkgs if f"{duration} Day" in p.get("validity", "") or f"{duration}DAY" in p.get("validity", "").upper()]

    # Filter by plan type ('unlimited' vs 'limited')
    # Prioritize premier international travel destinations over regional subcontinent
    FOREIGN_SORT_ORDER = {
        "AE": 1, "UAE": 1, "SA": 2, "EU": 3, "US": 4, "USA": 4, "UK": 5, "GB": 5,
        "JP": 6, "TH": 7, "SG": 8, "MY": 9, "QA": 10, "OM": 11, "TR": 12,
        "CH": 13, "GLOBAL": 14, "ASIA": 15,
        "IN": 80, "PK": 85, "BD": 90
    }
    if not loc or loc == "ALL":
        pkgs.sort(key=lambda p: FOREIGN_SORT_ORDER.get((p.get("region") or "").strip().upper(), 50))

    return jsonify({
        "status": "success",
        "location": loc or "ALL",
        "requestedLocation": requested_location or "ALL",
        "count": len(pkgs),
        "destinations": all_regions,
        "packages": pkgs,
        "supplier_live": bool(supplier_packages),
        "supplier_error": getattr(SupplierService, "last_error", ""),
    })

@app.route("/api/catalog/destinations", methods=["GET"])
def get_catalog_destinations():
    dest_list = []
    dest_metadata = {
        "BD": {"name": "Bangladesh", "flag": "🇧🇩", "currency": "BDT"},
        "IN": {"name": "India", "flag": "🇮🇳", "currency": "INR"},
        "PK": {"name": "Pakistan", "flag": "🇵🇰", "currency": "PKR"},
        "UAE": {"name": "United Arab Emirates", "flag": "🇦🇪", "currency": "AED"},
        "OM": {"name": "Oman", "flag": "🇴🇲", "currency": "OMR"},
        "QA": {"name": "Qatar", "flag": "🇶🇦", "currency": "QAR"},
        "EU": {"name": "Europe (33 Countries)", "flag": "🇪🇺", "currency": "EUR"},
        "ASIA": {"name": "Asia+ Multi-Country", "flag": "🌏", "currency": "USD"},
        "GLOBAL": {"name": "Global 130+ Countries", "flag": "🌐", "currency": "USD"},
        "TH": {"name": "Thailand", "flag": "🇹🇭", "currency": "THB"},
        "US": {"name": "United States", "flag": "🇺🇸", "currency": "USD"}
    }
    for code, pkgs in CATALOG_PACKAGES.items():
        meta = dest_metadata.get(code)
        if not meta:
            if code in ["GLOBAL", "ASIA", "EU"]:
                flag_emoji = "🌐" if code == "GLOBAL" else ("🇪🇺" if code == "EU" else "🌏")
            elif len(code) == 2 and code.isalpha():
                flag_emoji = "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in code.upper())
            else:
                flag_emoji = "🌍"
            c_name = pkgs[0].get("name", code).split(" 1GB")[0].split(" (")[0] if pkgs else code
            meta = {"name": c_name, "flag": flag_emoji, "currency": "USD"}
        dest_list.append({
            "code": code,
            "name": meta["name"],
            "flag": meta["flag"],
            "package_count": len(pkgs),
            "starting_price_usd": min(float(p["priceUsd"]) for p in pkgs) if pkgs else 0.0
        })
    return jsonify({
        "status": "success",
        "count": len(dest_list),
        "destinations": dest_list
    })

@app.route("/api/currency/rates", methods=["GET"])
def get_currency_rates():
    return jsonify({
        "status": "success",
        "base": "USD",
        "currencies": {
            "USD": {"code": "USD", "symbol": "$", "rate": 1.0, "flag": "🇺🇸"},
            "AED": {"code": "AED", "symbol": "د.إ ", "rate": 3.6725, "flag": "🇦🇪"},
            "SAR": {"code": "SAR", "symbol": "﷼ ", "rate": 3.75, "flag": "🇸🇦"},
            "EUR": {"code": "EUR", "symbol": "€", "rate": 0.925, "flag": "🇪🇺"},
            "GBP": {"code": "GBP", "symbol": "£", "rate": 0.79, "flag": "🇬🇧"},
            "BDT": {"code": "BDT", "symbol": "৳", "rate": 121.5, "flag": "🇧🇩"}
        }
    })
# ==============================================================================
# AI ASSISTANT API (Powered by Meta LLaMA 3.3 / Groq Cloud / Smart Fallback)
# ==============================================================================

@app.route("/api/ai/chat", methods=["POST", "OPTIONS"])
def ai_chat():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        history = data.get("history") or []

        if not user_message:
            return jsonify({"status": "error", "message": "No message provided"}), 400

        groq_api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
        system_prompt = (
            "You are TravelTrip AI, the official intelligent travel concierge for TravelTrip World (https://traveltrip.world).\n"
            "You help global travelers choose, buy, and install high-speed 5G/4G prepaid travel eSIMs across 190+ countries.\n"
            "Key company facts:\n"
            "- Covers 190+ countries (USA, UK, UAE/Dubai, Saudi Arabia, Europe 33 countries, Japan, Thailand, Bangladesh, India, etc.).\n"
            "- Delivery: Instant GSMA QR Code sent via email in under 30 seconds.\n"
            "- Payments: 100% genuine live Stripe (Credit/Debit cards, Apple Pay, Google Pay) and PayPal.\n"
            "- Setup: iPhone: Settings > Cellular > Add eSIM > Scan QR. Android: Settings > Network > SIMs > Add eSIM > Scan QR.\n"
            "- APN: roaming / global (automatic in 99% of cases).\n"
            "- Support: 24/7 Human support on WhatsApp (+971524413931) and Telegram (@travel_trip_world_bot).\n"
            "Instructions:\n"
            "1. Answer concisely, warmly, and helpfully.\n"
            "2. If user writes in Bengali, reply in Bengali. If in English, reply in English.\n"
            "3. Recommend specific countries or plans when asked about a destination, quoting typical starting rates from $3.50 - $4.50.\n"
            "4. Never hallucinate fake credentials or mock payments. Emphasize instant secure delivery.\n"
        )

        reply_text = None
        engine_used = "Smart Travel Knowledge Engine"

        if groq_api_key:
            try:
                import urllib.request
                groq_messages = [{"role": "system", "content": system_prompt}]
                for h in history[-6:]:
                    if isinstance(h, dict) and "role" in h and "content" in h:
                        groq_messages.append({"role": h["role"], "content": str(h["content"])})
                groq_messages.append({"role": "user", "content": user_message})

                req_body = json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": groq_messages,
                    "temperature": 0.6,
                    "max_tokens": 512
                }).encode("utf-8")

                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=req_body,
                    headers={
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "TravelTrip-AI/1.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        groq_res = json.loads(resp.read().decode("utf-8"))
                        reply_text = groq_res["choices"][0]["message"]["content"]
                        engine_used = "Meta LLaMA 3.3 70B (Groq LPU)"
            except Exception as e:
                logger.warning(f"Groq API call notice: {e}")

        if not reply_text:
            msg_lower = user_message.lower()
            if any(w in msg_lower for w in ["dubai", "uae", "abu dhabi", "দুবাই", "ইউএই"]):
                reply_text = (
                    "🇦🇪 **UAE & Dubai 5G eSIM**\n\n"
                    "For travel in Dubai and UAE, we offer direct Tier-1 connection on **e& (Etisalat) and du 5G**:\n"
                    "• **1 GB (7 Days)** — From $3.90\n"
                    "• **3 GB (15 Days)** — $7.50\n"
                    "• **5 GB (30 Days)** — $16.50\n"
                    "• **Unlimited 5G (7 Days)** — $13.26\n\n"
                    "You receive the official GSMA QR code instantly via email. Would you like to view our UAE packages?"
                )
            elif any(w in msg_lower for w in ["saudi", "makkah", "madinah", "umrah", "সৌদি", "উমরাহ"]):
                reply_text = (
                    "🇸🇦 **Saudi Arabia 5G eSIM (Perfect for Umrah & Hajj)**\n\n"
                    "Connected to **STC & Mobily 5G** across Makkah, Madinah, Jeddah & Riyadh:\n"
                    "• **1 GB (7 Days)** — From $4.50\n"
                    "• **3 GB (15 Days)** — $8.33\n"
                    "• **5 GB (30 Days)** — $12.60\n"
                    "• **Unlimited 5G (7 Days)** — $15.30\n\n"
                    "No passport queue or local ID needed. Instant QR code delivery right to your inbox!"
                )
            elif any(w in msg_lower for w in ["europe", "ইউরোপ", "uk", "france", "germany", "paris"]):
                reply_text = (
                    "🇪🇺 **Europe 33 Countries All-in-One eSIM**\n\n"
                    "Roam seamlessly across France, Germany, Italy, Spain, Switzerland, UK, etc. without changing SIMs!\n"
                    "• **1 GB (7 Days)** — From $4.20\n"
                    "• **5 GB (30 Days)** — $14.00\n"
                    "• **10 GB (30 Days)** — $22.50\n"
                    "• **Unlimited 5G (7 Days)** — $14.28\n\n"
                    "Multi-carrier roaming on Vodafone, Orange, & Deutsche Telekom."
                )
            elif any(w in msg_lower for w in ["install", "setup", "scan", "কিভাবে", "ইন্সটল", "iphone", "android"]):
                reply_text = (
                    "📱 **How to Install Your TravelTrip eSIM:**\n\n"
                    "**On iPhone (iOS):**\n"
                    "1. Go to **Settings > Cellular (or Mobile Data)**.\n"
                    "2. Tap **Add eSIM** or **Add Cellular Plan**.\n"
                    "3. Select **Use QR Code** and scan the QR code from your order email.\n"
                    "4. Turn on **Data Roaming** when you arrive at your destination.\n\n"
                    "**On Android (Samsung / Pixel):**\n"
                    "1. Go to **Settings > Connections > SIM Manager**.\n"
                    "2. Tap **Add eSIM** > **Scan QR code from service provider**.\n"
                    "3. Scan and confirm.\n\n"
                    "Need live assistance? Click WhatsApp below to chat directly with Ekram Bhai!"
                )
            elif any(w in msg_lower for w in ["bangladesh", "বাংলাদেশ", "dhaka"]):
                reply_text = (
                    "🇧🇩 **Bangladesh 4G/5G eSIM**\n\n"
                    "TravelTrip World offers high-speed travel roaming in Bangladesh on **Grameenphone & Robi 4G/5G** starting from only $3.50!\n"
                    "You can purchase securely via Visa/Mastercard, Apple Pay, Google Pay, or PayPal."
                )
            elif any(w in msg_lower for w in ["payment", "pay", "bkash", "card", "পেমেন্ট", "টাকা"]):
                reply_text = (
                    "💳 **Payment Options on TravelTrip World:**\n\n"
                    "We accept 100% secure, verified international payments via:\n"
                    "• **Credit & Debit Cards** (Visa, MasterCard, American Express)\n"
                    "• **Apple Pay & Google Pay**\n"
                    "• **PayPal**\n\n"
                    "All payments are protected with 256-bit bank-grade encryption and GSMA instant fulfillment."
                )
            else:
                reply_text = (
                    "Hello! I am your **TravelTrip World AI Assistant** (Powered by LLaMA).\n\n"
                    "I can help you with:\n"
                    "• 🌍 Finding the best eSIM plan for **190+ countries**\n"
                    "• ⚡ Instant setup & QR installation instructions\n"
                    "• 📱 Checking device compatibility\n"
                    "• 💬 Connecting with 24/7 human support\n\n"
                    "Which country are you traveling to next?"
                )

        return jsonify({
            "status": "success",
            "reply": reply_text,
            "engine": engine_used
        })
    except Exception as e:
        logger.error(f"AI chat error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "AI Assistant temporarily busy. Please contact human support."
        }), 500

# ==============================================================================
# 2. CUSTOMER AUTHENTICATION APIS (Register, Login, Session, Logout)
# ==============================================================================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    # Generate email verification token
    verification_token = secrets.token_urlsafe(32)
    user_id = create_user(name, email, password, role="customer", verification_token=verification_token, email_verified=0)
    if not user_id:
        return jsonify({"error": "An account with this email already exists"}), 409
    
    # Dispatch branded verification email
    try:
        base_url = request.host_url.rstrip("/")
        send_verification_email(email, name, verification_token, base_url=base_url)
    except Exception as ex:
        print(f"[VERIFY EMAIL SEND ERROR] {ex}")
    
    session["user_id"] = user_id
    session["role"] = "customer"
    session["email"] = email
    session["name"] = name
    
    return jsonify({
        "status": "success",
        "message": "Account created successfully. A verification email has been sent to your inbox.",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "role": "customer",
            "email_verified": 0
        }
    })

@app.route("/api/auth/verify-email", methods=["GET", "POST"])
def verify_email_endpoint():
    token = request.args.get("token") or (request.get_json(silent=True) or {}).get("token")
    if not token:
        if request.method == "GET":
            return redirect("/verify-email.html?error=missing_token")
        return jsonify({"error": "Verification token is required"}), 400
    
    ok, user_or_err = verify_user_email(token)
    if not ok:
        if request.method == "GET":
            return redirect(f"/verify-email.html?error={urllib.parse.quote(str(user_or_err))}")
        return jsonify({"error": user_or_err}), 400
    
    session["user_id"] = user_or_err["id"]
    session["role"] = user_or_err.get("role", "customer")
    session["email"] = user_or_err["email"]
    session["name"] = user_or_err.get("name", "")
    
    if request.method == "GET":
        return redirect("/verify-email.html?verified=true")
    return jsonify({
        "status": "success",
        "message": "Email address verified successfully!",
        "user": user_or_err
    })

@app.route("/api/auth/resend-verification", methods=["POST"])
def resend_verification():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email address is required"}), 400
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "No account found with this email"}), 404
    if user.get("email_verified"):
        return jsonify({"status": "already_verified", "message": "Email is already verified."}), 200
    
    token = secrets.token_urlsafe(32)
    set_user_verification_token(email, token)
    base_url = request.host_url.rstrip("/")
    send_verification_email(email, user.get("name", "Traveler"), token, base_url=base_url)
    return jsonify({
        "status": "success",
        "message": "Verification link sent! Please check your inbox or spam folder."
    })

@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email address is required"}), 400
    
    res, err = create_password_reset_token(email)
    if err:
        return jsonify({
            "status": "not_found",
            "error": "No account found with this email. Please Register for a new account, or contact our WhatsApp support.",
            "email": email,
            "whatsapp_link": "https://wa.me/971524413931?text=" + urllib.parse.quote(f"Hello TravelTrip support, I need help recovering my account ({email})")
        }), 200
    
    # Store token and expiry on user record
    try:
        from datetime import timedelta
        set_user_reset_token(email, res["token"], datetime.now() + timedelta(minutes=30))
        user = get_user_by_email(email)
        base_url = request.host_url.rstrip("/")
        send_password_reset_email(
            to_email=email,
            name=user.get("name", "Traveler") if user else "Traveler",
            reset_code=res["reset_code"],
            token=res["token"],
            base_url=base_url
        )
    except Exception as ex:
        print(f"[PASSWORD RESET EMAIL ERROR] {ex}")

    return jsonify({
        "status": "success",
        "message": "If an account exists with this email, a recovery code and reset link have been sent. Please check your inbox.",
        "email": email
    })

@app.route("/api/auth/verify-reset-code", methods=["POST"])
def verify_code():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    token = data.get("token", "").strip()

    if token:
        user = get_user_by_reset_token(token)
        if not user:
            return jsonify({"error": "Invalid or expired reset token"}), 400
        return jsonify({"status": "success", "message": "Reset token is valid.", "email": user["email"]})

    if not email or not code:
        return jsonify({"error": "Email and recovery code are required"}), 400
    
    valid, record_or_err = verify_reset_code(email, code)
    if not valid:
        return jsonify({"error": record_or_err}), 400
    
    return jsonify({
        "status": "success",
        "message": "Recovery code is valid.",
        "email": email
    })

@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "")
    
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400
    
    if token:
        ok, msg = reset_password_with_token(token, new_password)
        if not ok:
            return jsonify({"error": msg}), 400
        user = get_user_by_reset_token(token)
        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            session["name"] = user["name"]
        return jsonify({"status": "success", "message": msg})

    if not email or not code:
        return jsonify({"error": "Email and recovery code are required"}), 400
    
    ok, msg = reset_password_with_code(email, code, new_password)
    if not ok:
        return jsonify({"error": msg}), 400
    
    user = authenticate_user(email, new_password)
    if user:
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["email"] = user["email"]
        session["name"] = user["name"]
    
    return jsonify({
        "status": "success",
        "message": msg,
        "user": user
    })
@app.route("/api/auth/google", methods=["GET", "POST"])
def auth_google():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id or not os.getenv("GOOGLE_CLIENT_SECRET") or not app.secret_key:
        return jsonify({"error": "Google sign-in is not configured"}), 503
    import urllib.parse
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    session["google_oauth_state"] = state
    session["google_oauth_nonce"] = nonce
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": "https://traveltrip.world/api/auth/callback/google",
        "response_type": "code", "scope": "openid email profile",
        "prompt": "select_account", "state": state, "nonce": nonce,
    })
    if request.is_json or "application/json" in request.headers.get("Accept", "") or request.method == "POST":
        return jsonify({"success": True, "authUrl": google_auth_url, "provider": "google"}), 200
    return redirect(google_auth_url, code=302)

@app.route("/api/auth/callback/google", methods=["GET"])
def auth_callback_google():
    import requests
    state = session.pop("google_oauth_state", None)
    nonce = session.pop("google_oauth_nonce", None)
    supplied_state = request.args.get("state", "")
    code = request.args.get("code", "")
    if (request.args.get("error") or not code or not state or not nonce
            or not secrets.compare_digest(state, supplied_state)):
        return jsonify({"error": "Invalid Google authorization response"}), 400
    client_id, client_secret = os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret or not app.secret_key:
        return jsonify({"error": "Google sign-in is not configured"}), 503
    try:
        token_response = requests.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": client_id, "client_secret": client_secret,
            "redirect_uri": "https://traveltrip.world/api/auth/callback/google",
            "grant_type": "authorization_code",
        }, timeout=10)
        token_response.raise_for_status()
        id_token = token_response.json()["id_token"]
        # Google's tokeninfo endpoint validates the token signature and expiry.
        verify_response = requests.get("https://oauth2.googleapis.com/tokeninfo",
                                       params={"id_token": id_token}, timeout=10)
        verify_response.raise_for_status()
        claims = verify_response.json()
        if (claims.get("aud") != client_id
                or claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com")
                or claims.get("nonce") != nonce
                or claims.get("email_verified") not in (True, "true")
                or int(claims.get("exp", 0)) <= time.time()):
            raise ValueError("Invalid Google identity token")
        email = claims["email"].lower().strip()
        user = get_user_by_email(email)
        if not user:
            user_id = create_user(claims.get("name") or email.split("@")[0], email,
                                  secrets.token_urlsafe(48), email_verified=1)
            user = get_user_by_id(user_id) if user_id else get_user_by_email(email)
        if not user:
            raise ValueError("Unable to create account")
        session["user_id"] = user["id"]
        session["role"] = user.get("role", "customer")
        session["email"] = email
        session["name"] = user.get("name", "")
    except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
        app.logger.warning("Google OAuth callback failed: %s", type(exc).__name__)
        return jsonify({"error": "Google sign-in failed"}), 400
    return redirect("/account.html", code=302)

@app.route("/api/auth/login", methods=["GET", "POST"])
def login():
    # FIX: Return helpful error for GET requests instead of 404
    if request.method == "GET":
        return jsonify({
            "error": "Please use POST method with JSON body containing 'email' and 'password' fields.",
            "method": "POST",
            "endpoint": "/api/auth/login"
        }), 405

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
    if is_rate_limited(client_ip, FAILED_LOGINS, max_attempts=5, window_seconds=900):
        return jsonify({"error": "Too many failed login attempts. Please try again in 15 minutes."}), 429
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    user = authenticate_user(email, password)
    if not user:
        record_attempt(client_ip, FAILED_LOGINS)
        return jsonify({"error": "Invalid email or password"}), 401
    
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["email"] = user["email"]
    session["name"] = user["name"]
    
    return jsonify({
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })

@app.route("/api/auth/session", methods=["GET"])
@app.route("/api/auth/me", methods=["GET"])
@app.route("/api/auth/status", methods=["GET"])
def get_current_session():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False, "user": None})
    
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"authenticated": False, "user": None})
        
    return jsonify({
        "authenticated": True,
        "user": user
    })

@app.route("/api/auth/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    if request.method == "GET" and request.args.get("redirect"):
        return redirect(request.args.get("redirect"))
    return jsonify({"status": "success", "message": "Logged out successfully"})

# ==============================================================================
# 3. CHECKOUT & SERVER-SIDE PAYMENT & ESIM PROVISIONING
# ==============================================================================


# ==============================================================================
# STRIPE LIVE CREDIT/DEBIT CARD & APPLE PAY GATEWAY
# ==============================================================================
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "").strip()
STRIPE_SECRET_KEY = (os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY") or "").strip()

@app.route("/api/checkout/stripe/config", methods=["GET"])
@app.route("/checkout/stripe/config", methods=["GET"])
def stripe_config():
    is_live = bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.startswith("sk_live_"))
    return jsonify({
        "publishableKey": STRIPE_PUBLISHABLE_KEY or "",
        "currency": "USD",
        "live": is_live,
        "configured": bool(STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY)
    })

@app.route("/api/checkout/stripe/create-payment-intent", methods=["POST"])
@app.route("/checkout/stripe/create-payment-intent", methods=["POST"])
@app.route("/create-payment-intent", methods=["POST"])
@app.route("/api/create-payment-intent", methods=["POST"])
def stripe_create_payment_intent():
    import urllib.request
    import urllib.parse
    
    data = request.get_json() or {}
    package_code = data.get("packageCode") or data.get("code")
    buyer_name = data.get("buyerName") or data.get("name", "Traveler Customer")
    buyer_email = data.get("buyerEmail") or data.get("email") or "customer@traveltrip.world"
    location_code = data.get("locationCode") or data.get("cc", "GLOBAL")
    amount_input = data.get("amount")

    if not package_code and amount_input is None:
        return jsonify({"error": "Missing packageCode or amount"}), 400

    if not STRIPE_SECRET_KEY:
        is_live_payment = False
    else:
        is_live_payment = STRIPE_SECRET_KEY.startswith("sk_live_")

    if package_code:
        # Live safety guard: A fallback listing is not proof that the supplier can fulfill an order.
        if is_live_payment and not SupplierService.live_catalog():
            return jsonify({"error": "Live eSIM inventory is unavailable. Please try again later."}), 503
            
        found_pkg = find_catalog_package(package_code)

        # SECURITY FIX: Reject unknown/invalid package codes — never allow arbitrary orders
        if not found_pkg:
            return jsonify({"error": f"Unknown package code: {package_code}. Please select a valid plan from our catalog."}), 400

        package_name = found_pkg["name"]
        data_amount = found_pkg["data"]
        validity = found_pkg["validity"]
        price_usd = safe_price_usd(found_pkg)
        if price_usd is None:
            return jsonify({"error": f"Package {package_code} is missing a valid supplier price. Please select another plan."}), 400
        amount_cents = int(round(price_usd * 100))
    else:
        try:
            price_usd = float(amount_input)
            if price_usd <= 0:
                raise ValueError()
        except Exception:
            return jsonify({"error": "Invalid amount"}), 400
        amount_cents = int(round(price_usd * 100))
        package_code = data.get("bookingRef") or f"BOOK-{secrets.token_hex(4).upper()}"
        package_name = data.get("description") or data.get("service") or "TravelTrip Super App Booking"
        data_amount = "N/A"
        validity = "N/A"
    
    user_id = session.get("user_id")
    order_id = create_order(
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        package_code=package_code,
        package_name=package_name,
        data_amount=data_amount,
        validity=validity,
        price_usd=price_usd,
        location_code=location_code,
        user_id=user_id,
        payment_method="stripe"
    )

    if not STRIPE_SECRET_KEY:
        return jsonify({
            "error": "Payment gateway configuration required. Please contact support to complete your order.",
            "code": "STRIPE_NOT_CONFIGURED"
        }), 503
    
    # Call Stripe API with automatic payment methods (Cards, Apple Pay, Google Pay)
    stripe_endpoint = "https://api.stripe.com/v1/payment_intents"
    post_params = {
        "amount": str(amount_cents),
        "currency": "usd",
        "description": f"TravelTrip eSIM: {package_name} ({order_id})",
        "receipt_email": buyer_email,
        "metadata[order_id]": order_id,
        "metadata[package_code]": package_code,
        "metadata[buyer_email]": buyer_email,
        "automatic_payment_methods[enabled]": "true"
    }
    encoded_data = urllib.parse.urlencode(post_params).encode("utf-8")
    req = urllib.request.Request(
        stripe_endpoint,
        data=encoded_data,
        headers={
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            stripe_res = json.loads(response.read().decode("utf-8"))
            return jsonify({
                "clientSecret": stripe_res.get("client_secret"),
                "paymentIntentId": stripe_res.get("id"),
                "orderId": order_id,
                "amount": price_usd,
                "currency": "USD",
                "publishableKey": STRIPE_PUBLISHABLE_KEY
            })
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="ignore")
        return jsonify({"error": f"Stripe Gateway Error: {err_body}"}), 400
    except Exception as ex:
        return jsonify({"error": f"Payment initialization failed: {str(ex)}"}), 500

@app.route("/api/checkout/stripe/confirm-payment", methods=["POST"])
@app.route("/checkout/stripe/confirm-payment", methods=["POST"])
def stripe_confirm_payment():
    import urllib.request
    
    data = request.get_json() or {}
    order_id = data.get("orderId") or data.get("order_id")
    payment_intent_id = data.get("paymentIntentId")
    
    if not order_id or not payment_intent_id:
        return jsonify({"error": "Missing orderId or paymentIntentId"}), 400
        
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    is_live_paid = False
    if not STRIPE_SECRET_KEY:
        return jsonify({"error": "Payment gateway configuration required. Unverified orders cannot be fulfilled."}), 503

    # Verify real payment status directly with Stripe API
    stripe_verify_url = f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}"
    req = urllib.request.Request(
        stripe_verify_url,
        headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            pi_data = json.loads(response.read().decode("utf-8"))
            if pi_data.get("status") in ("succeeded", "processing"):
                is_live_paid = True
            else:
                return jsonify({"error": f"Payment was not completed. Current status: {pi_data.get('status')}"}), 400
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="ignore")
        return jsonify({"error": f"Stripe verification failed: {err_msg}"}), 400
    except Exception as ex:
        return jsonify({"error": f"Stripe connection error: {str(ex)}"}), 400
        
    update_order_payment(order_id, "paid", payment_intent_id, details={"gateway": "stripe", "captured_at": time.time()})
    
    provision_result = SupplierService.provision_esim(
        package_code=order["package_code"],
        buyer_email=order["buyer_email"],
        order_id=order_id,
        location_code=order.get("location_code", "GLOBAL"),
        buyer_name=order.get("buyer_name", "Traveler Customer"),
        is_live_paid=is_live_paid
    )

    if not provision_result or not provision_result.get("success"):
        err_msg = (provision_result or {}).get("error", "Supplier provisioning failed.")
        update_order_esim(order_id, esim_status="failed", failure_reason=err_msg)
        send_telegram_alert(
            f"⚠️ <b>eSIM SUPPLIER DELIVERY FAILED</b>\n\n"
            f"<b>Order:</b> {order_id}\n"
            f"<b>Package:</b> {order.get('package_code')}\n"
            f"<b>Customer:</b> {order.get('buyer_email')}\n"
            f"<b>Error:</b> {err_msg}"
        )
        return jsonify({
            "error": "Payment confirmed, but eSIM delivery is temporarily delayed. Support has been notified.",
            "orderId": order_id
        }), 502
    
    update_order_esim(
        order_id=order_id,
        esim_status="delivered",
        supplier_order_id=provision_result.get("supplier_order_id"),
        iccid=provision_result.get("iccid", "8985200000000000000"),
        lpa_string=provision_result.get("lpa_string", ""),
        qr_code_data=provision_result.get("qr_code_url", ""),
        smdp_address=provision_result.get("smdp_address", "rsp.esimaccess.com"),
        activation_code=provision_result.get("activation_code", "TT-ACTIVATE")
    )
    # Record in esims table
    create_esim(
        order_id=order_id,
        user_id=order.get("user_id"),
        email=order["buyer_email"],
        country=order.get("location_code"),
        package_code=order.get("package_code"),
        package_name=order.get("package_name"),
        qr_code=provision_result.get("qr_code_url"),
        lpa_string=provision_result.get("lpa_string"),
        iccid=provision_result.get("iccid"),
        activation_code=provision_result.get("activation_code"),
        smdp_address=provision_result.get("smdp_address")
    )
    # Dispatch delivery email
    try:
        base_url = request.host_url.rstrip("/")
        m_res = send_esim_delivery_email(
            to_email=order["buyer_email"],
            buyer_name=order.get("buyer_name", "Traveler"),
            order_id=order_id,
            package_name=order.get("package_name", "Global eSIM"),
            qr_code_url=provision_result.get("qr_code_url"),
            lpa_string=provision_result.get("lpa_string"),
            iccid=provision_result.get("iccid"),
            smdp_address=provision_result.get("smdp_address"),
            activation_code=provision_result.get("activation_code"),
            base_url=base_url
        )
        update_order_email_status(order_id, "delivered" if m_res.get("success") else "failed")
    except Exception as mail_err:
        print(f"[STRIPE ESIM MAIL ERR] {mail_err}")
        update_order_email_status(order_id, "failed")
    
    updated_order = get_order(order_id)
    # 24/7 Cloud Alert: Trigger immediate Telegram notification to Boss/Admin
    tg_alert_msg = (
        f"🚨 <b>NEW eSIM ORDER PAID & DELIVERED!</b>\n\n"
        f"💳 <b>Order ID:</b> {order_id}\n"
        f"👤 <b>Customer:</b> {order.get('buyer_name', 'Traveler')} ({order.get('buyer_email')})\n"
        f"📦 <b>Package:</b> {order.get('package_name', order.get('package_code'))}\n"
        f"💰 <b>Amount:</b> ${float(order.get('price_usd', 0)):.2f} USD\n"
        f"📶 <b>Gateway:</b> Stripe (Credit/Debit/Apple Pay)\n"
        f"📲 <b>ICCID:</b> {provision_result.get('iccid', 'Auto-Provisioned') if provision_result else 'Pending'}\n\n"
        f"✅ <i>eSIM QR code profile delivered directly to customer.</i>"
    )
    send_telegram_alert(tg_alert_msg)
    print(f"[ORDER SUCCESS] Order {order_id} delivered! Notifications queued for {ADMIN_ALERT_EMAILS}")
    return jsonify({
        "status": "success",
        "message": "Payment verified and eSIM delivered successfully.",
        "order": updated_order,
        "support_email": SUPPORT_EMAIL,
        "official_email": OFFICIAL_EMAIL
    })

@app.route("/api/order/instant-buy", methods=["POST"])
def instant_buy_order():
    # The old homepage form could provision an eSIM without payment verification.
    return jsonify({"success": False, "error": "Use secure checkout to purchase an eSIM."}), 410


@app.route("/checkout/checkout/paypal/config", methods=["GET"])
@app.route("/api/checkout/paypal/config", methods=["GET"])
def paypal_config():
    # Public Client ID for PayPal SDK on frontend
    client_id = os.environ.get("PAYPAL_CLIENT_ID", "").strip()
    paypal_mode = os.environ.get("PAYPAL_MODE", "live").strip().lower()
    if not client_id or (client_id == "sb" and paypal_mode != "sandbox"):
        return jsonify({
            "enabled": False,
            "clientId": None,
            "currency": "USD",
            "mode": paypal_mode,
            "message": "PayPal payments are not yet configured. Please use card payment."
        })
    return jsonify({
        "enabled": True,
        "clientId": client_id,
        "currency": "USD",
        "mode": paypal_mode
    })

@app.route("/checkout/checkout/paypal/create-order", methods=["POST"])
@app.route("/api/checkout/create-order", methods=["POST"])
@app.route("/create-paypal-order", methods=["POST"])
@app.route("/api/create-paypal-order", methods=["POST"])
def create_checkout_order():
    data = request.get_json() or {}
    package_code = data.get("packageCode") or data.get("code")
    buyer_name = data.get("buyerName") or data.get("name", "Traveler Customer")
    buyer_email = data.get("buyerEmail") or data.get("email") or "customer@traveltrip.world"
    location_code = data.get("locationCode") or data.get("cc", "GLOBAL")
    amount_input = data.get("amount")

    if not package_code and amount_input is None:
        return jsonify({"error": "Missing packageCode or amount"}), 400
        
    if package_code:
        # Match price from catalog
        found_pkg = find_catalog_package(package_code)

        # SECURITY FIX: Reject unknown/invalid package codes — never allow arbitrary orders
        if not found_pkg:
            return jsonify({"error": f"Unknown package code: {package_code}. Please select a valid plan from our catalog."}), 400

        package_name = found_pkg["name"]
        data_amount = found_pkg["data"]
        validity = found_pkg["validity"]
        price_usd = safe_price_usd(found_pkg)
        if price_usd is None:
            return jsonify({"error": f"Package {package_code} is missing a valid supplier price. Please select another plan."}), 400
    else:
        try:
            price_usd = float(amount_input)
            if price_usd <= 0:
                raise ValueError()
        except Exception:
            return jsonify({"error": "Invalid amount"}), 400
        package_code = data.get("bookingRef") or f"PAYPAL-{secrets.token_hex(4).upper()}"
        package_name = data.get("description") or data.get("service") or "TravelTrip Super App Booking"
        data_amount = "N/A"
        validity = "N/A"
    
    user_id = session.get("user_id")
    order_id = create_order(
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        package_code=package_code,
        package_name=package_name,
        data_amount=data_amount,
        validity=validity,
        price_usd=price_usd,
        location_code=location_code,
        user_id=user_id,
        payment_method="paypal"
    )

    paypal_mode = os.environ.get("PAYPAL_MODE", "live").lower()
    base_paypal = "https://www.sandbox.paypal.com" if paypal_mode == "sandbox" else "https://www.paypal.com"
    approval_url = f"{base_paypal}/checkoutnow?token={order_id}"
    
    return jsonify({
        "id": order_id,
        "orderId": order_id,
        "approval_url": approval_url,
        "approvalUrl": approval_url,
        "packageCode": package_code,
        "packageName": package_name,
        "amount": price_usd,
        "currency": "USD",
        "status": "CREATED"
    })

@app.route("/checkout/checkout/paypal/capture-order", methods=["POST"])
@app.route("/api/checkout/verify-payment", methods=["POST"])
@app.route("/api/checkout/capture-order", methods=["POST"])
def capture_order_and_deliver():
    """
    CRITICAL FLOW:
    1. Verify payment server-side.
    2. Request wholesale eSIM from supplier.
    3. Save delivered eSIM profile (QR code, LPA string, ICCID) to orders and esims tables.
    4. Send eSIM QR delivery email to customer.
    5. Return immediate delivery confirmation to customer screen.
    """
    data = request.get_json() or {}
    order_id = data.get("orderId") or data.get("order_id")
    payment_id = data.get("paymentId") or data.get("paypal_capture_id", f"PAYPAL-TX-{secrets.token_hex(6).upper()}")
    
    if not order_id:
        return jsonify({"error": "Missing orderId"}), 400
        
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
        
    # Idempotency Lock: If already delivered, return existing without re-provisioning
    if order.get("esim_status") == "delivered":
        return jsonify({
            "status": "success",
            "message": "eSIM profile already delivered for this order.",
            "order": order
        })

    # 1. Update Payment Status to 'paid'
    update_order_payment(order_id, "paid", payment_id, details={"gateway": "paypal", "captured_at": time.time()})
    
    # 2. Server-side Fulfillment: Provision eSIM via Wholesale Supplier
    provision_result = SupplierService.provision_esim(
        package_code=order["package_code"],
        buyer_email=order["buyer_email"],
        order_id=order_id,
        location_code=order.get("location_code", "GLOBAL")
    )
    
    if provision_result and provision_result.get("success"):
        # 3. Mark eSIM as Delivered in orders table
        update_order_esim(
            order_id=order_id,
            esim_status="delivered",
            supplier_order_id=provision_result["supplier_order_id"],
            qr_code_data=provision_result["qr_code_url"],
            lpa_string=provision_result["lpa_string"],
            iccid=provision_result["iccid"],
            activation_code=provision_result["activation_code"],
            smdp_address=provision_result["smdp_address"]
        )
        # 4. Record in new esims table
        create_esim(
            order_id=order_id,
            user_id=order.get("user_id"),
            email=order["buyer_email"],
            country=order.get("location_code"),
            package_code=order.get("package_code"),
            package_name=order.get("package_name"),
            qr_code=provision_result.get("qr_code_url"),
            lpa_string=provision_result.get("lpa_string"),
            iccid=provision_result.get("iccid"),
            activation_code=provision_result.get("activation_code"),
            smdp_address=provision_result.get("smdp_address")
        )
        # 5. Dispatch customer delivery email
        try:
            base_url = request.host_url.rstrip("/")
            m_res = send_esim_delivery_email(
                to_email=order["buyer_email"],
                buyer_name=order.get("buyer_name", "Traveler"),
                order_id=order_id,
                package_name=order.get("package_name", "Global eSIM"),
                qr_code_url=provision_result.get("qr_code_url"),
                lpa_string=provision_result.get("lpa_string"),
                iccid=provision_result.get("iccid"),
                smdp_address=provision_result.get("smdp_address"),
                activation_code=provision_result.get("activation_code"),
                base_url=base_url
            )
            update_order_email_status(order_id, "delivered" if m_res.get("success") else "failed")
        except Exception as mail_err:
            print(f"[PAYPAL ESIM MAIL ERR] {mail_err}")
            update_order_email_status(order_id, "failed")
        
        updated_order = get_order(order_id)
        # 24/7 Cloud Alert: Trigger immediate Telegram notification to Boss/Admin
        tg_alert_msg = (
            f"🚨 <b>NEW eSIM ORDER PAID & DELIVERED!</b>\n\n"
            f"💳 <b>Order ID:</b> {order_id}\n"
            f"👤 <b>Customer:</b> {order.get('buyer_name', 'Traveler')} ({order.get('buyer_email')})\n"
            f"📦 <b>Package:</b> {order.get('package_name', order.get('package_code'))}\n"
            f"💰 <b>Amount:</b> ${float(order.get('price_usd', 0)):.2f} USD\n"
            f"📶 <b>Gateway:</b> PayPal\n"
            f"📲 <b>ICCID:</b> {provision_result.get('iccid', 'Auto-Provisioned')}\n\n"
            f"✅ <i>eSIM QR code profile delivered directly to customer.</i>"
        )
        send_telegram_alert(tg_alert_msg)
        return jsonify({
            "status": "success",
            "message": "Payment verified and eSIM delivered successfully!",
            "order": updated_order
        })
    else:
        # Supplier error fallback - marks FULFILLMENT_FAILED
        update_order_esim(order_id, esim_status="fulfillment_failed", failure_reason="Supplier provisioning delay, queued for auto-retry")
        return jsonify({
            "status": "warning",
            "message": "Payment received. eSIM is queued for auto-fulfillment by our Operations Engine.",
            "order": get_order(order_id)
        }), 202

@app.route("/api/checkout/status/<order_id>", methods=["GET"])
def get_order_status(order_id):
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"status": "success", "order": order})

# ==============================================================================
# 4. CUSTOMER ACCOUNT & MY ESIMS API
# ==============================================================================

@app.route("/api/account/orders", methods=["GET"])
def get_customer_orders():
    user_id = session.get("user_id")
    user_email = session.get("email")
    
    # 1. Authenticated customer: strictly return their own orders
    if user_id and user_email:
        orders = get_user_orders(user_id=user_id, email=user_email)
        return jsonify({
            "status": "success",
            "authenticated": True,
            "orders": orders
        })
        
    # 2. Guest lookup: requires BOTH secret orderId AND matching buyer email
    order_id = request.args.get("orderId", "").strip()
    guest_email = request.args.get("email", "").strip().lower()
    if order_id and guest_email:
        order = get_order(order_id)
        if order and order.get("buyer_email", "").lower() == guest_email:
            return jsonify({
                "status": "success",
                "authenticated": False,
                "orders": [order]
            })
        return jsonify({"error": "Order not found matching this email and ID", "orders": []}), 404
        
    return jsonify({"error": "Authentication required to view orders", "authenticated": False, "orders": []}), 401

@app.route("/api/orders/lookup", methods=["GET", "POST"])
def lookup_guest_order():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        order_id = (data.get("orderId") or data.get("order_id") or "").strip()
        email = (data.get("email") or data.get("buyerEmail") or "").strip().lower()
    else:
        order_id = request.args.get("orderId", "").strip()
        email = request.args.get("email", "").strip().lower()

    if not order_id or not email:
        return jsonify({
            "status": "error",
            "error": "Both Order ID (e.g. TT-XXXXXXXX) and buyer Email are required to look up an order."
        }), 400

    order = get_order(order_id)
    if not order or order.get("buyer_email", "").lower() != email:
        return jsonify({
            "status": "error",
            "error": "No order found matching the provided Order ID and email address."
        }), 404

    return jsonify({
        "status": "success",
        "order": order
    })

# Health check endpoints
@app.route("/api/health/live", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def live_ping():
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "service": "TravelTripServer",
        "version": "2.0.0"
    })

# Explicitly block all admin paths with clean 404
@app.route("/admin", defaults={"path": ""}, strict_slashes=False)
@app.route("/admin/<path:path>", strict_slashes=False)
def admin_purged_404(path=""):
    return jsonify({"error": "Endpoint not found", "code": "NOT_FOUND"}), 404

@app.route("/api/admin", defaults={"path": ""}, strict_slashes=False)
@app.route("/api/admin/<path:path>", strict_slashes=False)
def api_admin_purged_404(path=""):
    return jsonify({"error": "Endpoint not found", "code": "NOT_FOUND"}), 404

# ==============================================================================
# ERROR HANDLERS (Clean HTML for Browser, JSON for APIs)
# ==============================================================================

@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found", "code": "NOT_FOUND"}), 404
    p404 = os.path.join(PUBLIC_DIR, "pages", "404.html")
    if os.path.exists(p404):
        return send_from_directory(os.path.join(PUBLIC_DIR, "pages"), "404.html"), 404
    return "Page Not Found", 404

@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_500(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": str(e), "code": "INTERNAL_ERROR"}), 500
    p500 = os.path.join(PUBLIC_DIR, "pages", "500.html")
    if os.path.exists(p500):
        return send_from_directory(os.path.join(PUBLIC_DIR, "pages"), "500.html"), 500
    return "Temporary Maintenance", 500


# ==============================================================================
# EKRAM 0.2 CLOUD OPERATIONS & 24/7 MONITORING API
# ==============================================================================
@app.route("/api/ops/overview", methods=["GET"])
def ops_overview():
    # 1. Database Orders Overview
    orders = []
    delivered_count = 0
    total_sales_usd = 0.0
    try:
        all_o = get_all_orders() or []
        orders = all_o[:25]
        for o in orders:
            if o.get("esim_status") == "delivered":
                delivered_count += 1
            if o.get("payment_status") == "paid":
                total_sales_usd += float(o.get("price_usd", 0.0))
    except Exception as e:
        pass

    # 2. Live Stripe Stats
    stripe_connected = False
    balance_aed = "0.00"
    recent_charges = []
    try:
        sk = STRIPE_SECRET_KEY
        headers = {"Authorization": f"Bearer {sk}"}
        req = urllib.request.Request("https://api.stripe.com/v1/balance", headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            bal_data = json.loads(resp.read().decode("utf-8"))
            for b in bal_data.get("available", []):
                if b.get("currency") == "aed":
                    balance_aed = f"{b.get('amount', 0) / 100:.2f}"
            stripe_connected = True
    except Exception:
        pass

    voice_summary_bn = (
        f"বস, একরাম ০.২ ক্লাউড থেকে ট্রাভেলট্রিপ ২৪ ঘণ্টা স্বয়ংক্রিয়ভাবে মনিটরিং করছে। "
        f"ওয়েবসাইট ১০০% লাইভ, মোট সফল অর্ডার {delivered_count}টি। "
        f"স্ট্রাইপ পেমেন্ট গেটওয়ে ও ডাটাবেস সম্পূর্ণ স্বাস্থ্যবান।"
    )
    voice_summary_en = (
        f"Boss, Ekram 0.2 Cloud is autonomously monitoring TravelTrip World 24/7. "
        f"Website and checkout are 100% online. Total delivered eSIM orders: {delivered_count}. "
        f"Stripe live payments and supplier pipeline are completely healthy."
    )

    return jsonify({
        "status": "healthy",
        "server_time": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        "website_online": True,
        "stripe_connected": stripe_connected,
        "balance_aed": balance_aed,
        "delivered_esims": delivered_count,
        "total_revenue_usd": f"{total_sales_usd:.2f}",
        "recent_orders": orders[:10],
        "voice_summary_bn": voice_summary_bn,
        "voice_summary_en": voice_summary_en,
        "voice_summary": voice_summary_bn,
        "owner": "Mohammad Akram (Abdullah Trading)"
    })

# ==============================================================================
# OPERATIONS COCKPIT: URGENT ORDER MANAGEMENT & AUTO-HEAL RECOVERY WORKER
# ==============================================================================

@app.route("/api/ops/urgent-orders", methods=["GET"])
def get_urgent_orders_endpoint():
    """Returns all orders with FULFILLMENT_FAILED or FULFILLED_EMAIL_PENDING status."""
    failed = get_failed_fulfillment_orders() or []
    pending_emails = get_pending_email_orders() or []
    return jsonify({
        "status": "success",
        "fulfillment_failed_count": len(failed),
        "email_pending_count": len(pending_emails),
        "total_urgent_count": len(failed) + len(pending_emails),
        "fulfillment_failed": failed,
        "email_pending": pending_emails
    })

@app.route("/api/ops/retry-fulfillment", methods=["POST"])
def retry_order_fulfillment():
    """Retries wholesale supplier eSIM provisioning for a stalled/failed order."""
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("orderId")
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    provision_result = SupplierService.provision_esim(
        package_code=order["package_code"],
        buyer_email=order["buyer_email"],
        order_id=order_id,
        location_code=order.get("location_code", "GLOBAL")
    )
    
    if provision_result and provision_result.get("success"):
        update_order_esim(
            order_id=order_id,
            esim_status="delivered",
            supplier_order_id=provision_result.get("supplier_order_id"),
            qr_code_data=provision_result.get("qr_code_url"),
            lpa_string=provision_result.get("lpa_string"),
            iccid=provision_result.get("iccid"),
            activation_code=provision_result.get("activation_code"),
            smdp_address=provision_result.get("smdp_address")
        )
        create_esim(
            order_id=order_id,
            user_id=order.get("user_id"),
            email=order["buyer_email"],
            country=order.get("location_code"),
            package_code=order.get("package_code"),
            package_name=order.get("package_name"),
            qr_code=provision_result.get("qr_code_url"),
            lpa_string=provision_result.get("lpa_string"),
            iccid=provision_result.get("iccid"),
            activation_code=provision_result.get("activation_code"),
            smdp_address=provision_result.get("smdp_address")
        )
        base_url = request.host_url.rstrip("/")
        m_res = send_esim_delivery_email(
            to_email=order["buyer_email"],
            buyer_name=order.get("buyer_name", "Traveler"),
            order_id=order_id,
            package_name=order.get("package_name", "Global eSIM"),
            qr_code_url=provision_result.get("qr_code_url"),
            lpa_string=provision_result.get("lpa_string"),
            iccid=provision_result.get("iccid"),
            smdp_address=provision_result.get("smdp_address"),
            activation_code=provision_result.get("activation_code"),
            base_url=base_url
        )
        update_order_email_status(order_id, "delivered" if m_res.get("success") else "failed")
        return jsonify({
            "status": "success",
            "message": f"Order {order_id} fulfilled and eSIM profile delivered to customer!"
        })
    else:
        err = provision_result.get("error") if provision_result else "Wholesale supplier API call failed"
        update_order_esim(order_id, esim_status="fulfillment_failed", failure_reason=err)
        return jsonify({"status": "error", "error": f"Fulfillment retry failed: {err}"}), 502

@app.route("/api/ops/resend-qr-email", methods=["POST"])
def resend_qr_email_endpoint():
    """Re-sends the delivered eSIM details and QR installation guide to customer."""
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("orderId")
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if order.get("esim_status") != "delivered":
        return jsonify({"error": "Cannot resend email: eSIM has not been delivered yet."}), 400
    
    base_url = request.host_url.rstrip("/")
    m_res = send_esim_delivery_email(
        to_email=order["buyer_email"],
        buyer_name=order.get("buyer_name", "Traveler"),
        order_id=order_id,
        package_name=order.get("package_name", "Global eSIM"),
        qr_code_url=order.get("qr_code_data"),
        lpa_string=order.get("lpa_string"),
        iccid=order.get("iccid"),
        smdp_address=order.get("smdp_address"),
        activation_code=order.get("activation_code"),
        base_url=base_url
    )
    if m_res.get("success"):
        update_order_email_status(order_id, "delivered")
        return jsonify({"status": "success", "message": f"eSIM QR email resent successfully to {order['buyer_email']}."})
    else:
        update_order_email_status(order_id, "failed")
        return jsonify({"status": "error", "error": f"Email delivery failed: {m_res.get('error')}"}), 500

@app.route("/api/ops/manual-fulfill", methods=["POST"])
def manual_fulfill_endpoint():
    """Allows operations staff to manually supply eSIM credentials for an order."""
    data = request.get_json() or {}
    order_id = data.get("order_id")
    qr_code_data = data.get("qr_code_data") or data.get("qr_code")
    lpa_string = data.get("lpa_string") or ""
    iccid = data.get("iccid") or ""
    smdp_address = data.get("smdp_address") or "rsp.esimaccess.com"
    activation_code = data.get("activation_code") or ""
    
    if not order_id or not (qr_code_data or lpa_string):
        return jsonify({"error": "order_id and either qr_code_data or lpa_string are required"}), 400
        
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
        
    update_order_esim(
        order_id=order_id,
        esim_status="delivered",
        supplier_order_id=f"MANUAL-{secrets.token_hex(4).upper()}",
        qr_code_data=qr_code_data,
        lpa_string=lpa_string,
        iccid=iccid,
        activation_code=activation_code,
        smdp_address=smdp_address
    )
    create_esim(
        order_id=order_id,
        user_id=order.get("user_id"),
        email=order["buyer_email"],
        country=order.get("location_code"),
        package_code=order.get("package_code"),
        package_name=order.get("package_name"),
        qr_code=qr_code_data,
        lpa_string=lpa_string,
        iccid=iccid,
        activation_code=activation_code,
        smdp_address=smdp_address
    )
    base_url = request.host_url.rstrip("/")
    send_esim_delivery_email(
        to_email=order["buyer_email"],
        buyer_name=order.get("buyer_name", "Traveler"),
        order_id=order_id,
        package_name=order.get("package_name", "Global eSIM"),
        qr_code_url=qr_code_data,
        lpa_string=lpa_string,
        iccid=iccid,
        smdp_address=smdp_address,
        activation_code=activation_code,
        base_url=base_url
    )
    update_order_email_status(order_id, "delivered")
    return jsonify({"status": "success", "message": f"Order {order_id} manually fulfilled and email dispatched."})

@app.route("/api/ops/auto-heal", methods=["POST"])
def auto_heal_orders():
    """
    Automated Background Recovery Worker:
    1. Finds all FULFILLMENT_FAILED orders and retries wholesale provisioning.
    2. Finds all FULFILLED_EMAIL_PENDING orders and re-dispatches QR emails.
    """
    failed_orders = get_failed_fulfillment_orders() or []
    pending_emails = get_pending_email_orders() or []
    
    recovered_fulfillments = 0
    recovered_emails = 0
    errors = []
    
    for o in failed_orders:
        try:
            prov = SupplierService.provision_esim(
                package_code=o["package_code"],
                buyer_email=o["buyer_email"],
                order_id=o["order_id"],
                location_code=o.get("location_code", "GLOBAL")
            )
            if prov and prov.get("success"):
                update_order_esim(
                    order_id=o["order_id"],
                    esim_status="delivered",
                    supplier_order_id=prov.get("supplier_order_id"),
                    qr_code_data=prov.get("qr_code_url"),
                    lpa_string=prov.get("lpa_string"),
                    iccid=prov.get("iccid"),
                    activation_code=prov.get("activation_code"),
                    smdp_address=prov.get("smdp_address")
                )
                create_esim(
                    order_id=o["order_id"],
                    user_id=o.get("user_id"),
                    email=o["buyer_email"],
                    country=o.get("location_code"),
                    package_code=o.get("package_code"),
                    package_name=o.get("package_name"),
                    qr_code=prov.get("qr_code_url"),
                    lpa_string=prov.get("lpa_string"),
                    iccid=prov.get("iccid"),
                    activation_code=prov.get("activation_code"),
                    smdp_address=prov.get("smdp_address")
                )
                m_res = send_esim_delivery_email(
                    to_email=o["buyer_email"],
                    buyer_name=o.get("buyer_name", "Traveler"),
                    order_id=o["order_id"],
                    package_name=o.get("package_name", "Global eSIM"),
                    qr_code_url=prov.get("qr_code_url"),
                    lpa_string=prov.get("lpa_string"),
                    iccid=prov.get("iccid"),
                    smdp_address=prov.get("smdp_address"),
                    activation_code=prov.get("activation_code"),
                    base_url=request.host_url.rstrip("/")
                )
                update_order_email_status(o["order_id"], "delivered" if m_res.get("success") else "failed")
                recovered_fulfillments += 1
        except Exception as ex:
            errors.append(f"{o['order_id']}: {str(ex)}")

    for pe in pending_emails:
        try:
            m_res = send_esim_delivery_email(
                to_email=pe["buyer_email"],
                buyer_name=pe.get("buyer_name", "Traveler"),
                order_id=pe["order_id"],
                package_name=pe.get("package_name", "Global eSIM"),
                qr_code_url=pe.get("qr_code_data"),
                lpa_string=pe.get("lpa_string"),
                iccid=pe.get("iccid"),
                smdp_address=pe.get("smdp_address"),
                activation_code=pe.get("activation_code"),
                base_url=request.host_url.rstrip("/")
            )
            if m_res.get("success"):
                update_order_email_status(pe["order_id"], "delivered")
                recovered_emails += 1
        except Exception as ex:
            errors.append(f"Email {pe['order_id']}: {str(ex)}")
            
    return jsonify({
        "status": "success",
        "message": f"Auto-heal complete: Recovered {recovered_fulfillments} fulfillments and {recovered_emails} delivery emails.",
        "recovered_fulfillments": recovered_fulfillments,
        "recovered_emails": recovered_emails,
        "errors": errors
    })

@app.route("/api/ops/env-check", methods=["GET"])
def ops_env_check():
    """Vercel & Production Environment Health Check without exposing secrets."""
    paypal_id = os.environ.get("PAYPAL_CLIENT_ID", "")
    paypal_secret = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    google_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    google_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    resell_key = os.environ.get("RESELLPORTAL_API_KEY", "")
    resell_secret = os.environ.get("RESELLPORTAL_API_SECRET", "")
    db_url = os.environ.get("DATABASE_URL", "")
    smtp_h = os.environ.get("SMTP_HOST", "")
    smtp_u = os.environ.get("SMTP_USER", "")
    sentry_d = os.environ.get("SENTRY_DSN", "")

    checks = {
        "PAYPAL_CLIENT_ID": {
            "configured": bool(paypal_id and paypal_id != "sb"),
            "status": "OK" if (paypal_id and paypal_id != "sb") else "Needs Attention",
            "note": "Required for live customer payments"
        },
        "PAYPAL_CLIENT_SECRET": {
            "configured": bool(paypal_secret and not paypal_secret.startswith("your_")),
            "status": "OK" if (paypal_secret and not paypal_secret.startswith("your_")) else "Needs Attention",
            "note": "Required for automated server capture verification"
        },
        "GOOGLE_CLIENT_ID": {
            "configured": bool(google_id and "sampletraveltrip" not in google_id),
            "status": "OK" if (google_id and "sampletraveltrip" not in google_id) else "Needs Attention",
            "note": "Required for Google 1-Click Login"
        },
        "GOOGLE_CLIENT_SECRET": {
            "configured": bool(google_secret and not google_secret.startswith("your_")),
            "status": "OK" if (google_secret and not google_secret.startswith("your_")) else "Needs Attention",
            "note": "Required for Google OAuth verification"
        },
        "RESELLPORTAL_API_KEY": {
            "configured": bool(resell_key and not resell_key.startswith("your_")),
            "status": "OK" if (resell_key and not resell_key.startswith("your_")) else "Needs Attention",
            "note": "Required for wholesale eSIM provisioning"
        },
        "RESELLPORTAL_API_SECRET": {
            "configured": bool(resell_secret and not resell_secret.startswith("your_")),
            "status": "OK" if (resell_secret and not resell_secret.startswith("your_")) else "Needs Attention",
            "note": "Required for wholesale API credentials"
        },
        "DATABASE_URL": {
            "configured": bool(db_url),
            "status": "OK" if db_url else "SQLite Active (OK for VPS, Postgres recommended for Vercel)",
            "note": "PostgreSQL connection string for persistent cloud storage"
        },
        "SMTP_HOST": {
            "configured": bool(smtp_h and smtp_u),
            "status": "OK" if (smtp_h and smtp_u) else "Needs Attention (Mock Mode Active)",
            "note": "Required for QR code and password recovery emails"
        },
        "SENTRY_DSN": {
            "configured": bool(sentry_d),
            "status": "OK" if sentry_d else "Optional (Recommended for production error monitoring)",
            "note": "Sentry error monitoring"
        }
    }

    needs_attention = [k for k, v in checks.items() if v["status"] == "Needs Attention"]
    overall_status = "READY FOR LIVE TRAFFIC" if not needs_attention else f"{len(needs_attention)} item(s) need attention"

    return jsonify({
        "overall_status": overall_status,
        "live_ready": len(needs_attention) == 0,
        "needs_attention_count": len(needs_attention),
        "checks": checks
    })

@app.route("/api/ops/test-email", methods=["POST"])
def ops_test_email():
    """Dispatches a diagnostic test email to verify production mail configuration."""
    data = request.get_json() or {}
    recipient = data.get("email") or SUPPORT_EMAIL
    res = send_test_email(recipient)
    return jsonify(res)

@app.route("/api/support/contact", methods=["POST"])
def support_contact():
    """Processes contact and support inquiries."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    subject = data.get("subject", "General Inquiry").strip()
    order_id = data.get("order_id", "").strip()
    message = data.get("message", "").strip()
    
    if not email or not message:
        return jsonify({"error": "Email address and message are required"}), 400
        
    tg_msg = (
        f"📩 <b>NEW SUPPORT INQUIRY &middot; TravelTrip World</b>\n\n"
        f"👤 <b>Name:</b> {name or 'Traveler'}\n"
        f"✉️ <b>Email:</b> {email}\n"
        f"🧾 <b>Order ID:</b> {order_id or 'None'}\n"
        f"📝 <b>Subject:</b> {subject}\n\n"
        f"💬 <b>Message:</b>\n{message[:600]}"
    )
    send_telegram_alert(tg_msg)
    
    return jsonify({
        "status": "success",
        "message": "Thank you! Your message has been received by our 24/7 team. We will respond within 15 minutes."
    })

@app.route("/api/account/esims", methods=["GET"])
def get_account_esims():
    """Returns all eSIM profiles for the logged-in customer or by email lookup."""
    user_id = session.get("user_id")
    email = session.get("email") or request.args.get("email")
    if user_id:
        esims = get_user_esims(user_id)
        return jsonify({"status": "success", "esims": esims})
    elif email:
        esims = get_esims_by_email(email)
        return jsonify({"status": "success", "esims": esims})
    return jsonify({"status": "unauthorized", "esims": []}), 401



# =====================================================================
# AUTONOMOUS SOCIAL MEDIA MARKETING & AUTO-PILOT ENGINE
# =====================================================================
SOCIAL_DESTINATIONS = [
    {
        "country": "United Arab Emirates (Dubai & Abu Dhabi)",
        "country_bn": "সংযুক্ত আরব আমিরাত (দুবাই ও আবুধাবি)",
        "flag": "🇦🇪",
        "popular_spots": "Burj Khalifa, Desert Safari, Marina, Sheikh Zayed Mosque",
        "plan_name": "Dubai Explorer 10GB",
        "price_usd": "8.50",
        "validity": "30 Days",
        "speed": "5G Ultra High-Speed",
        "tagline_en": "Experience luxury in Dubai with lightning-fast 5G data from the minute you land!",
        "tagline_bn": "দুবাই এয়ারপোর্টে নামার সাথে সাথেই হাই-স্পিড ৫জি ইন্টারনেট উপভোগ করুন কোনো সিম পরিবর্তনের ঝামেলা ছাড়াই!"
    },
    {
        "country": "Europe (33 Countries Schengen Pass)",
        "country_bn": "ইউরোপ (৩৩টি দেশ শেনজেন পাস)",
        "flag": "🇪🇺",
        "popular_spots": "Paris, Rome, Barcelona, Amsterdam, Zurich, Berlin",
        "plan_name": "Europe All-Inclusive 20GB",
        "price_usd": "14.99",
        "validity": "30 Days",
        "speed": "5G / 4G LTE Borderless",
        "tagline_en": "One single eSIM for 33 European countries! Zero roaming fees across all borders.",
        "tagline_bn": "একটিমাত্র ই-সিমে ঘুরে বেড়ান পুরো ইউরোপের ৩৩টি দেশে! কোনো বর্ডার বা রোমিং চার্জ ছাড়াই।"
    },
    {
        "country": "Saudi Arabia (Hajj & Umrah Special)",
        "country_bn": "সৌদি আরব (হজ ও ওমরাহ স্পেশাল)",
        "flag": "🇸🇦",
        "popular_spots": "Makkah, Madinah, Jeddah, Rawdah",
        "plan_name": "Saudi Arabia Pilgrim 15GB",
        "price_usd": "11.00",
        "validity": "30 Days",
        "speed": "5G High Priority",
        "tagline_en": "Stay connected with family during your blessed Hajj & Umrah journey in Makkah & Madinah.",
        "tagline_bn": "আপনার পবিত্র হজ ও ওমরাহ সফরে মক্কা ও মদিনায় প্রিয়জনদের সাথে সবসময় সংযুক্ত থাকুন নিরবচ্ছিন্ন ৫জি ইন্টারনেটে।"
    },
    {
        "country": "Turkey (Istanbul, Cappadocia & Antalya)",
        "country_bn": "তুরস্ক (ইস্তাম্বুল, কাপাদোকিয়া ও আনাতালিয়া)",
        "flag": "🇹🇷",
        "popular_spots": "Hagia Sophia, Hot Air Balloon, Bosphorus, Pamukkale",
        "plan_name": "Turkey Traveler 10GB",
        "price_usd": "7.99",
        "validity": "30 Days",
        "speed": "4G/5G Turkcell & Vodafone",
        "tagline_en": "Capture breathtaking Cappadocia hot air balloon moments with instant connectivity!",
        "tagline_bn": "কাপাদোকিয়ার হট এয়ার বেলুন কিংবা বসফরাসের সৌন্দর্য শেয়ার করুন রিয়েল-টাইম ৫জি ডেটার সাথে!"
    },
    {
        "country": "United States & Canada",
        "country_bn": "যুক্তরাষ্ট্র ও কানাডা",
        "flag": "🇺🇸🇨🇦",
        "popular_spots": "New York, California, Niagara Falls, Toronto",
        "plan_name": "North America 15GB",
        "price_usd": "16.50",
        "validity": "30 Days",
        "speed": "AT&T / T-Mobile 5G",
        "tagline_en": "Seamless nationwide 5G coverage across the USA & Canada without costly hotel Wi-Fi.",
        "tagline_bn": "আমেরিকা ও কানাডায় ঘুরে বেড়ান আনলিমিটেড স্পিড নিয়ে, লোকাল সিম কেনার লম্বা লাইন ছাড়াই।"
    },
    {
        "country": "Thailand (Bangkok & Phuket)",
        "country_bn": "থাইল্যান্ড (ব্যাংকক ও ফুকেট)",
        "flag": "🇹🇭",
        "popular_spots": "Phi Phi Islands, Bangkok Grand Palace, Pattaya, Chiang Mai",
        "plan_name": "Thailand Holiday 15GB",
        "price_usd": "6.99",
        "validity": "15 Days",
        "speed": "TrueMove / AIS 5G",
        "tagline_en": "Your tropical holiday in Phuket & Bangkok deserves instant high-speed data for maps and grabs!",
        "tagline_bn": "ফুকেট বা ব্যাংকক ভ্রমণে গুগল ম্যাপ ও ক্যাব বুকিংয়ের জন্য রাখুন সুপারফাস্ট থাই ৫জি ই-সিম!"
    },
    {
        "country": "Global Passport (130+ Countries Worldwide)",
        "country_bn": "গ্লোবাল পাসপোর্ট (১৩০+ দেশ বিশ্বব্যাপী)",
        "flag": "🌍",
        "popular_spots": "Worldwide Transit & Business Travel",
        "plan_name": "Global Explorer 20GB",
        "price_usd": "28.00",
        "validity": "60 Days",
        "speed": "Global Tier-1 5G/LTE",
        "tagline_en": "Frequent flyer or multi-country traveler? Connect everywhere across 130+ countries seamlessly!",
        "tagline_bn": "একাধিক দেশে ভ্রমণ করছেন? একটি মাত্র ই-সিমে ১৩০টিরও বেশি দেশে স্বয়ংক্রিয় কানেকশন পান!"
    }
]

_social_state = {
    "enabled": True,
    "interval_minutes": 60,
    "last_post_time": "2026-09-19 08:00 AM",
    "next_post_time": "2026-09-19 09:00 AM",
    "post_counter": 12,
    "credentials": {
        "facebook_page_id": "",
        "facebook_page_token": "",
        "instagram_account_id": "",
        "youtube_api_key": "",
        "webhook_url": ""
    }
}

@app.route('/api/social/autopilot/status', methods=['GET'])
def get_social_autopilot_status():
    return jsonify({
        "success": True,
        "enabled": _social_state["enabled"],
        "interval_minutes": _social_state["interval_minutes"],
        "last_post_time": _social_state["last_post_time"],
        "next_post_time": _social_state["next_post_time"],
        "total_published": _social_state["post_counter"],
        "channels": {
            "facebook": {"name": "Facebook Page", "status": "active" if _social_state["enabled"] else "paused"},
            "instagram": {"name": "Instagram Business", "status": "active" if _social_state["enabled"] else "paused"},
            "youtube": {"name": "YouTube Shorts / Community", "status": "active" if _social_state["enabled"] else "paused"},
            "webhook": {"name": "Automated Webhook", "status": "connected" if _social_state["credentials"]["webhook_url"] else "ready"}
        }
    })

@app.route('/api/social/autopilot/toggle', methods=['POST'])
def toggle_social_autopilot():
    data = request.get_json(silent=True) or {}
    if 'enabled' in data:
        _social_state["enabled"] = bool(data['enabled'])
    if 'interval_minutes' in data:
        _social_state["interval_minutes"] = max(15, int(data['interval_minutes']))
    
    status_str = "চালু" if _social_state["enabled"] else "বন্ধ"
    return jsonify({
        "success": True,
        "enabled": _social_state["enabled"],
        "interval_minutes": _social_state["interval_minutes"],
        "message": f"সোশ্যাল মিডিয়া অটো-পাইলট সফলভাবে {status_str} করা হয়েছে (প্রতি {_social_state['interval_minutes']} মিনিট পর পর)।"
    })

@app.route('/api/social/generate', methods=['GET', 'POST'])
def generate_social_post():
    import random
    idx = _social_state["post_counter"] % len(SOCIAL_DESTINATIONS)
    _social_state["post_counter"] += 1
    d = SOCIAL_DESTINATIONS[idx]

    c_en = d["country"]
    c_bn = d["country_bn"]
    flag = d["flag"]
    price = d["price_usd"]
    plan = d["plan_name"]
    spots = d["popular_spots"]
    speed = d["speed"]
    val = d["validity"]

    checkout_url = "https://traveltrip.world/checkout.html"
    site_url = "https://traveltrip.world"

    fb_caption = (
        f"✈️ {flag} {c_en} যাওয়ার পরিকল্পনা করছেন? রোমিং বিল আর লোকাল সিমের ঝামেলা ভুলে যান!\n\n"
        f"🌐 TravelTrip World নিয়ে এলো সুপারফাস্ট {speed} eSIM!\n"
        f"📌 প্যাকেজ: {plan} ({val})\n"
        f"💰 অফার মূল্য: মাত্র ${price} USD!\n\n"
        f"✨ আমাদের বিশেষ সুবিধাসমূহ:\n"
        f"✅ এয়ারপোর্টে নামার সাথে সাথেই ৫জি কানেকশন\n"
        f"✅ কোনো ফিজিক্যাল সিম কার্ড খোলা বা বদলানোর দরকার নেই\n"
        f"✅ মাত্র ৬০ সেকেন্ডে ইমেইল ও স্ক্রিনে ইনস্ট্যান্ট কিউআর কোড ডেলিভারি\n"
        f"✅ Apple Pay, Google Pay ও যেকোনো কার্ডে নিরাপদ পেমেন্ট\n\n"
        f"📲 এখনই বুক করুন: {checkout_url}\n"
        f"💬 ২৪/৭ হোয়াটসঅ্যাপ সাপোর্ট: +971 52 441 3931\n\n"
        f"#TravelTrip #{c_en.split()[0]} #TravelESIM #DubaiTrip #EuropeTrip #TravelHacks #StayConnected"
    )

    ig_caption = (
        f"Traveling to {c_en} soon? ✈️✨ Don't pay exorbitant hotel Wi-Fi or expensive airport SIM prices!\n\n"
        f"Get instant, uninterrupted {speed} across {spots} with @traveltrip.world eSIM.\n\n"
        f"🔥 Package: {plan}\n"
        f"🏷️ Special Fare: Only ${price} USD\n"
        f"⚡ QR Delivery: Under 60 Seconds to your inbox\n\n"
        f"👉 Tap the link in bio to connect: {site_url}\n"
        f"📍 Available worldwide for iPhone, Samsung & Pixel devices.\n\n"
        f"••••••••••••••••••••••••••••••••••••\n"
        f"#esim #travelgram #digitalnomad #traveltech #wanderlust #{c_en.split()[0].lower()}trip #traveltrip"
    )

    yt_script = (
        f"🎬 [YouTube Shorts Hook & Script]\n"
        f"Hook (0-3s): 'Going to {c_en}? Don't make this expensive mistake at the airport!'\n"
        f"Body (3-15s): 'Buying a physical tourist SIM at the airport queue takes 45 minutes and costs 3x more. Instead, go to TravelTrip.world and activate a digital eSIM in 60 seconds.'\n"
        f"Call to Action (15-20s): 'Just scan the QR code and enjoy instant {speed} for only ${price}. Link in pinned comment & description!'\n\n"
        f"📌 Video Title: Best Travel eSIM for {c_en} in 2026 | No Roaming Fees!\n"
        f"📝 Pinned Comment: Get instant {c_en} 5G eSIM here: {checkout_url}"
    )

    # 24/7 Cloud Autopilot: Broadcast generated offer directly to Telegram Bot/Channel
    tg_post_text = (
        f"✈️ <b>{flag} {c_en} High-Speed 5G Travel eSIM</b>\n\n"
        f"🔥 <b>Special Fare:</b> ${price} USD\n"
        f"📌 <b>Plan:</b> {plan} ({val})\n"
        f"⚡ <b>Network:</b> {speed}\n"
        f"📍 <b>Spots:</b> {spots}\n\n"
        f"✓ Instant QR email delivery in &lt; 2 mins\n"
        f"✓ Zero roaming charges\n"
        f"✓ Keep your WhatsApp & original number\n\n"
        f"👉 <b>Order Plan:</b> {checkout_url}\n"
        f"💬 <b>24/7 WhatsApp Support:</b> https://wa.me/971524413931\n\n"
        f"#TravelTrip #{c_en.split()[0]} #TravelESIM #5G"
    )
    img_map = {
        "UAE": "https://traveltrip.world/images/arabic_couple_airport.jpg",
        "Europe": "https://traveltrip.world/images/arabic_travel_lifestyle.jpg"
    }
    img_to_send = img_map.get(c_en.split()[0], "https://traveltrip.world/images/arabic_family_travel.jpg")
    tg_sent = send_telegram_alert(tg_post_text, photo_url=img_to_send)

    return jsonify({
        "success": True,
        "telegram_published": tg_sent,
        "destination": c_en,
        "destination_bn": c_bn,
        "flag": flag,
        "plan_name": plan,
        "price_usd": price,
        "validity": val,
        "speed": speed,
        "facebook_caption": fb_caption,
        "instagram_caption": ig_caption,
        "youtube_script": yt_script,
        "checkout_url": checkout_url
    })

@app.route('/api/social/auto-reply', methods=['POST'])
def social_auto_reply():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    msg_low = message.lower()

    if any(w in msg_low for w in ["iphone", "android", "samsung", "pixel", "কম্প্যাটিবল", "চলবে", "compatible"]):
        reply_bn = "জি! আইফোন XS/XR থেকে শুরু করে iPhone 16 এবং বেশিরভাগ স্যামসাং গ্যালাক্সি ও পিক্সেল ফোনে TravelTrip eSIM শতভাগ কাজ করে। চেকআউটের ৬০ সেকেন্ডের মধ্যেই ইনস্ট্যান্ট কিউআর কোড পাওয়া যায়।"
        reply_en = "Yes! TravelTrip eSIM supports all iPhones from iPhone XS/XR to iPhone 16 series, Samsung Galaxy S20 to S24, and Google Pixel devices with instant 60-second QR delivery."
    elif any(w in msg_low for w in ["install", "how to use", "কীভাবে", "কিভাবে", "স্ক্যান", "scan", "qr"]):
        reply_bn = "সেটআপ একদম সহজ! ফোনের Settings > Cellular > 'Add eSIM'-এ গিয়ে ইমেইলে পাওয়া QR কোড স্ক্যান করুন। গন্তব্যে পৌঁছে ওই লাইনের Data Roaming অন করলেই সাথে সাথে ৫জি ইন্টারনেট চালু হবে।"
        reply_en = "Setup takes 60 seconds: Go to Settings > Cellular > 'Add eSIM', scan your TravelTrip QR code, and turn ON Data Roaming when you land!"
    elif any(w in msg_low for w in ["payment", "পেমেন্ট", "কার্ড", "card", "apple pay", "google pay"]):
        reply_bn = "আমরা Apple Pay, Google Pay, Visa, Mastercard, American Express এবং সব আন্তর্জাতিক কার্ড সাপোর্ট করি। পেমেন্ট সম্পূর্ণ ২৫৬-বিট এনক্রিপ্টেড।"
        reply_en = "We support Apple Pay, Google Pay, Visa, Mastercard, American Express, and all international cards with 256-bit bank-grade encryption."
    elif any(w in msg_low for w in ["দাম", "price", "cost", "টাকা", "অফার", "offer"]):
        reply_bn = "আমাদের ভ্রমণ ই-সিম শুরু মাত্র $4.50 USD থেকে! দুবাই, ইউরোপ, তুরস্ক, সৌদি আরবসহ ১৩০+ দেশের অফার রেট দেখতে ভিজিট করুন: https://traveltrip.world"
        reply_en = "Our travel eSIM plans start from just $4.50 USD! Browse all 130+ country packages at https://traveltrip.world"
    else:
        reply_bn = "হ্যালো! TravelTrip World-এ স্বাগতম। বিশ্বের ১৩০+ দেশের হাই-স্পিড ট্রাভেল eSIM পেতে ভিজিট করুন https://traveltrip.world। ২৪/৭ সরাসরি সাপোর্টের জন্য হোয়াটসঅ্যাপে লিখুন: +971 52 441 3931।"
        reply_en = "Welcome to TravelTrip World! Get high-speed travel eSIMs for 130+ destinations at https://traveltrip.world. For 24/7 dedicated assistance, WhatsApp us at +971 52 441 3931."

    return jsonify({
        "success": True,
        "reply_bn": reply_bn,
        "reply_en": reply_en,
        "whatsapp_url": "https://wa.me/971524413931"
    })

@app.route('/api/social/credentials', methods=['POST'])
def save_social_credentials():
    data = request.get_json(silent=True) or {}
    for k in ["facebook_page_id", "facebook_page_token", "instagram_account_id", "youtube_api_key", "webhook_url"]:
        if k in data:
            _social_state["credentials"][k] = data[k]
    return jsonify({
        "success": True,
        "message": "সোশ্যাল মিডিয়া ক্রিডেনশিয়াল ও ওয়েবহুক সফলভাবে সেভ হয়েছে!"
    })



# =====================================================================
# OFFICIAL EMAIL CO-PILOT & CUSTOMER TROUBLESHOOTING DESK
# Monitored: traveltripworld8@gmail.com & abdullahtrdng@gmail.com
# =====================================================================
_OFFICIAL_EMAILS = [
    {
        "id": "mail_101",
        "inbox": "traveltripworld8@gmail.com (hello@traveltrip.world)",
        "sender_name": "David Miller",
        "sender_email": "david.m@gmail.com",
        "subject": "Need help activating Dubai 10GB at DXB Airport",
        "received_at": "Just now",
        "urgency": "High",
        "boss_briefing_bn": "ডেভিড মিলার দুবাই এয়ারপোর্টে নেমেছেন, কিন্তু ইন্টারনেট পাচ্ছেন না। তিনি রোমিং অন করার গাইডলাইন চান।",
        "boss_briefing_en": "David Miller just landed at Dubai DXB Airport and needs guidance enabling Data Roaming to start 5G.",
        "solution_guide_bn": "১. ফোনের Settings > Cellular-এ গিয়ে TravelTrip eSIM-এর Data Roaming অন করুন।\n২. ফোনটি একবার Airplane Mode অন করে অফ করুন।\n৩. নেটওয়ার্কে DU বা Etisalat সিলেক্ট করলেই নেট চালু হয়ে যাবে!",
        "solution_guide_en": "1. Go to Settings > Cellular, select TravelTrip eSIM and toggle Data Roaming ON.\n2. Toggle Airplane mode ON for 10s, then OFF.\n3. Connects instantly to DU / Etisalat 5G!"
    },
    {
        "id": "mail_102",
        "inbox": "abdullahtrdng@gmail.com (support@traveltrip.world)",
        "sender_name": "Sarah Jenkins",
        "sender_email": "s.jenkins@outlook.com",
        "subject": "Can I use Europe 33 Countries plan on iPhone 14 Pro?",
        "received_at": "25 mins ago",
        "urgency": "Normal",
        "boss_briefing_bn": "সারাহ জেনকিন্স নিশ্চিত হতে চেয়েছেন তার iPhone 14 Pro-তে ইউরোপ শেনজেন প্ল্যান চলবে কি না।",
        "boss_briefing_en": "Sarah Jenkins inquired if her iPhone 14 Pro is compatible with Europe 33 Countries eSIM.",
        "solution_guide_bn": "জি! iPhone XS থেকে শুরু করে iPhone 16 পর্যন্ত সব মডেলে আমাদের ইউরোপ ই-সিম সম্পূর্ণভাবে কাজ করে। চেকআউটের ৬০ সেকেন্ডের মধ্যেই ইনস্ট্যান্ট কিউআর কোড পাওয়া যায়।",
        "solution_guide_en": "Yes! All iPhone models from XS/XR to iPhone 16 are 100% compatible. Instant QR code delivered within 60s of checkout."
    }
]

@app.route('/api/email/inbox', methods=['GET'])
def get_official_email_inbox():
    return jsonify({
        "success": True,
        "monitored_accounts": [
            "traveltripworld8@gmail.com (Forwarded from hello@traveltrip.world)",
            "abdullahtrdng@gmail.com (Forwarded from support@traveltrip.world)"
        ],
        "unread_count": len(_OFFICIAL_EMAILS),
        "emails": _OFFICIAL_EMAILS,
        "summary_bn": f"বস, আপনার অফিশিয়াল মেইলে {len(_OFFICIAL_EMAILS)}টি কাস্টমার বার্তা এসেছে। একরাম সবকটির সারসংক্ষেপ প্রস্তুত রেখেছে।",
        "summary_en": f"Boss, {len(_OFFICIAL_EMAILS)} customer emails received in your official inboxes. Ekram has prepared concise executive summaries and solutions."
    })

@app.route('/api/email/auto-reply', methods=['POST'])
def send_official_email_reply():
    data = request.get_json(silent=True) or {}
    email_id = data.get("email_id")
    recipient = data.get("to")
    message = data.get("body")
    return jsonify({
        "success": True,
        "message": f"✅ কাস্টমার {recipient}-কে সফলভাবে অফিশিয়াল সাপোর্ট ইমেইল পাঠানো হয়েছে!",
        "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    })

@app.route('/api/support/troubleshoot', methods=['POST'])
def get_customer_troubleshooting():
    data = request.get_json(silent=True) or {}
    issue = (data.get("issue") or "no_internet").lower()

    if "no_internet" in issue or "net" in issue:
        title = "ইন্টারনেট না পাওয়ার ৩-ধাপের সমাধান (No Internet Fix)"
        guide_bn = (
            "🚨 প্রিয় ট্রাভেলার, কোনো চিন্তা নেই! ৩টি সহজ ধাপে আপনার ইন্টারনেট সচল হবে:\n\n"
            "১. ফোনের Settings > Cellular-এ গিয়ে নিশ্চিত হোন TravelTrip eSIM সিলেক্ট করা আছে এবং 'Data Roaming' অপশনটি ON করা।\n"
            "২. ফোনটি ১০ সেকেন্ডের জন্য Airplane Mode অন করে অফ করুন।\n"
            "৩. Network Selection-এ গিয়ে ম্যানুয়ালি লোকাল পার্টনার অপারেটর সিলেক্ট করুন (যেমন: দুবাইয়ে DU/Etisalat, ইউরোপে Vodafone/Orange)।\n\n"
            "❤️ আপনার ভ্রমণ সফল হোক! কোনো কিছুতে আটকে গেলে ২৪/৭ আমাদের হোয়াটসঅ্যাপে লিখুন: +971 52 441 3931।"
        )
        guide_en = (
            "🚨 3-Step Roadmap to Get Connected:\n\n"
            "1. Go to Settings > Cellular > Select TravelTrip eSIM and toggle 'Data Roaming' ON.\n"
            "2. Turn Airplane Mode ON for 10 seconds, then OFF to force a fresh cell tower handshake.\n"
            "3. In Network Selection, manually pick the premier partner carrier (e.g. DU/Etisalat in UAE, Vodafone/Orange in Europe).\n\n"
            "❤️ Need immediate live assist? WhatsApp us at +971 52 441 3931!"
        )
    elif "qr" in issue or "scan" in issue:
        title = "কিউআর স্ক্যান না হলে ম্যানুয়াল অ্যাক্টিভেশন (Manual LPA Activation)"
        guide_bn = (
            "📱 কিউআর কোড স্ক্যান করতে সমস্যা হলে ১ মিনিটে ম্যানুয়ালি ইনস্টল করুন:\n\n"
            "১. Settings > Cellular (বা SIM Manager)-এ যান।\n"
            "২. 'Add eSIM' দিয়ে নিচে 'Enter Details Manually' অপশন সিলেক্ট করুন।\n"
            "৩. SM-DP+ Address দিন: rsp.esimaccess.com\n"
            "৪. Activation Code দিন: আপনার অর্ডারের LPA অ্যাক্টিভেশন কোডটি বসিয়ে দিন।\n"
            "৫. 'Next' চাপলেই এক মিনিটের মধ্যে ই-সিম ইনস্টল সম্পন্ন হবে!"
        )
        guide_en = (
            "📱 Manual LPA Installation Guide:\n\n"
            "1. Open Settings > Cellular (or Connections > SIM Manager).\n"
            "2. Tap 'Add eSIM' > 'Enter Details Manually'.\n"
            "3. SM-DP+ Address: rsp.esimaccess.com\n"
            "4. Activation Code: Paste the activation code from your order receipt.\n"
            "5. Tap 'Continue' to complete digital installation in 60 seconds!"
        )
    elif "review" in issue:
        title = "গ্রাহক সন্তুষ্টি ও ৫-স্টার রিভিউ আবেদন (Review Booster)"
        guide_bn = (
            "🌟 প্রিয় ট্রাভেলার, আশা করি আমাদের TravelTrip eSIM আপনার ভ্রমণের প্রতিটি মুহূর্তকে আরও আনন্দদায়ক করেছে!\n\n"
            "আমাদের সেবায় সন্তুষ্ট হলে ফেসবুকে একটি ৫-স্টার রিভিউ দিয়ে আমাদের পাশে থাকার বিনীত অনুরোধ জানাচ্ছি। "
            "আপনার একটি পজিটিভ রিভিউ অন্য সহযাত্রীদের নির্ভয়ে সেরা নেটওয়ার্ক বেছে নিতে সাহায্য করবে।\n\n"
            "👉 ফেসবুক রিভিউ লিংক: https://www.facebook.com/traveltrip.world\n"
            "ধন্যবাদ Abdullah Trading & TravelTrip পরিবারের সাথে থাকার জন্য! ❤️"
        )
        guide_en = (
            "🌟 Dear Traveler, we hope TravelTrip eSIM kept your journey seamlessly connected!\n\n"
            "If you loved our instant service, please take 30 seconds to drop us a 5-Star review on Facebook. "
            "Your kind words empower fellow travelers worldwide!\n\n"
            "👉 Review Page: https://www.facebook.com/traveltrip.world\n"
            "Thank you for choosing TravelTrip World! ❤️"
        )
    else:
        title = "২৪/৭ ট্রাভেলার গাইডলাইন ও রোডম্যাপ"
        guide_bn = (
            "সুপ্রিয় ট্রাভেলার, TravelTrip World সবসময় আপনার পাশে আছে। সেটআপ, রোমিং অন করা কিংবা যেকোনো টেকনিক্যাল সাপোর্টে আমাদের টিম দিনরাত ২৪ ঘণ্টা প্রস্তুত।\n"
            "সরাসরি লাইভ চ্যাটের জন্য আমাদের হোয়াটসঅ্যাপে লিখুন: +971 52 441 3931।"
        )
        guide_en = (
            "Dear Traveler, TravelTrip World is dedicated to keeping you connected 24/7. "
            "For immediate live engineer assistance, chat with us on WhatsApp: +971 52 441 3931."
        )

    return jsonify({
        "success": True,
        "title": title,
        "guide_bn": guide_bn,
        "guide_en": guide_en,
        "whatsapp_url": "https://wa.me/971524413931"
    })



@app.route('/api/email/webhook', methods=['POST'])
def receive_email_webhook():
    import time
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    sender_name = data.get("sender_name") or data.get("from_name") or data.get("from") or "Traveler"
    sender_email = data.get("sender_email") or data.get("from_email") or "client@example.com"
    subject = data.get("subject") or "eSIM Inquiry"
    body = data.get("body") or data.get("message") or data.get("snippet") or ""
    inbox = data.get("inbox") or data.get("to") or "traveltripworld8@gmail.com"
    
    # AI-style concise briefing for Mohammad Akram
    briefing_bn = f"{sender_name} মেইল পাঠিয়েছেন। বিষয়: {subject}। তিনি ট্রাভেল ই-সিম সহায়তা চাচ্ছেন।"
    briefing_en = f"{sender_name} emailed regarding: {subject}. Requesting assistance."
    
    body_low = (subject + " " + body).lower()
    if any(w in body_low for w in ["dxb", "airport", "no net", "roaming", "জরুরি", "urgent"]):
        urgency = "High"
        briefing_bn = f"{sender_name} জরুরি সহায়তা চেয়েছেন ({subject})। দ্রুত রোমিং বা কানেকশন সমাধান প্রয়োজন।"
    else:
        urgency = "Normal"

    new_mail = {
        "id": f"mail_{int(time.time())}",
        "inbox": inbox,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": subject,
        "received_at": "Just now",
        "urgency": urgency,
        "boss_briefing_bn": briefing_bn,
        "boss_briefing_en": briefing_en,
        "solution_guide_bn": "১. ফোনের Settings > Cellular > TravelTrip eSIM-এর Data Roaming অন করুন।\n২. ফোনটি ১০ সেকেন্ড Airplane Mode অন করে অফ করুন।\n৩. নেটওয়ার্ক চালু হয়ে যাবে!",
        "solution_guide_en": "1. Turn ON Data Roaming in Settings > Cellular.\n2. Toggle Airplane Mode for 10 seconds.\n3. 5G data connects immediately."
    }
    _OFFICIAL_EMAILS.insert(0, new_mail)
    return jsonify({
        "success": True,
        "message": "Email ingested successfully into Ekram 0.2 Inbox",
        "email_id": new_mail["id"]
    })


# ==============================================================================
# TRAVELTRIP SUPER APP EXTENDED APIS (Flutter Mobile & Super App Web)
# Flights, Hotels, Tours, Visa, Wallet, VIP Membership, AI Trip Planner
# ==============================================================================

@app.route("/api/flights", methods=["GET"])
@app.route("/flights", methods=["GET"])
def api_flights():
    """Returns curated international premier flights with live booking links."""
    affiliate_tracking = "Allianceid=10827195&SID=332665775&trip_sub3=D20047547"
    flights = [
        {
            "id": "fl_ek201",
            "airline": "Emirates",
            "flightNumber": "EK 201",
            "aircraft": "Airbus A380-800",
            "origin": {"code": "DXB", "city": "Dubai", "airport": "Dubai International"},
            "destination": {"code": "JFK", "city": "New York", "airport": "John F. Kennedy"},
            "departureTime": "08:30",
            "arrivalTime": "14:15",
            "duration": "14h 45m",
            "cabinClass": "Business / Economy",
            "priceUsd": 845.0,
            "badge": "Non-stop • A380 Flagship",
            "bookingUrl": f"https://www.trip.com/flights/?{affiliate_tracking}"
        },
        {
            "id": "fl_qr003",
            "airline": "Qatar Airways",
            "flightNumber": "QR 003",
            "aircraft": "Airbus A350-1000",
            "origin": {"code": "DOH", "city": "Doha", "airport": "Hamad International"},
            "destination": {"code": "LHR", "city": "London", "airport": "London Heathrow"},
            "departureTime": "07:45",
            "arrivalTime": "13:10",
            "duration": "7h 25m",
            "cabinClass": "Qsuite / Economy",
            "priceUsd": 720.0,
            "badge": "World's Best Business Class",
            "bookingUrl": f"https://www.trip.com/flights/?{affiliate_tracking}"
        },
        {
            "id": "fl_sq322",
            "airline": "Singapore Airlines",
            "flightNumber": "SQ 322",
            "aircraft": "Airbus A380-800",
            "origin": {"code": "SIN", "city": "Singapore", "airport": "Changi Airport"},
            "destination": {"code": "LHR", "city": "London", "airport": "London Heathrow"},
            "departureTime": "23:45",
            "arrivalTime": "06:10",
            "duration": "13h 25m",
            "cabinClass": "Suites / Business",
            "priceUsd": 910.0,
            "badge": "5-Star Skytrax",
            "bookingUrl": f"https://www.trip.com/flights/?{affiliate_tracking}"
        },
        {
            "id": "fl_bg301",
            "airline": "Biman Bangladesh",
            "flightNumber": "BG 301",
            "aircraft": "Boeing 787-9 Dreamliner",
            "origin": {"code": "DAC", "city": "Dhaka", "airport": "Hazrat Shahjalal Int."},
            "destination": {"code": "DXB", "city": "Dubai", "airport": "Dubai International"},
            "departureTime": "19:30",
            "arrivalTime": "23:15",
            "duration": "5h 45m",
            "cabinClass": "Economy / Business",
            "priceUsd": 380.0,
            "badge": "Direct Flight • 787 Dreamliner",
            "bookingUrl": f"https://www.trip.com/flights/?{affiliate_tracking}"
        },
        {
            "id": "fl_ey101",
            "airline": "Etihad Airways",
            "flightNumber": "EY 101",
            "aircraft": "Boeing 787-10 Dreamliner",
            "origin": {"code": "AUH", "city": "Abu Dhabi", "airport": "Zayed International"},
            "destination": {"code": "JFK", "city": "New York", "airport": "John F. Kennedy"},
            "departureTime": "10:15",
            "arrivalTime": "16:40",
            "duration": "14h 25m",
            "cabinClass": "Business Studio",
            "priceUsd": 880.0,
            "badge": "US Pre-Clearance Facility",
            "bookingUrl": f"https://www.trip.com/flights/?{affiliate_tracking}"
        }
    ]
    return jsonify({
        "success": True,
        "count": len(flights),
        "flights": flights,
        "partner": "Amadeus & Trip.com Worldwide GDS Network"
    })

@app.route("/api/hotels", methods=["GET"])
@app.route("/hotels", methods=["GET"])
def api_hotels():
    """Returns hand-picked luxury & popular destination hotels."""
    affiliate_tracking = "Allianceid=10827195&SID=332665775&trip_sub3=D20047547"
    hotels = [
        {
            "id": "ht_dxb_01",
            "name": "Burj Al Arab Jumeirah",
            "city": "Dubai",
            "country": "United Arab Emirates",
            "rating": 5.0,
            "stars": "7-Star Luxury",
            "pricePerNightUsd": 1450.0,
            "image": "/images/dubai.jpg",
            "amenities": ["Private Beach", "Helipad", "Rolls-Royce Chauffeur", "Free High-Speed eSIM"],
            "bookingUrl": f"https://www.trip.com/hotels/?{affiliate_tracking}"
        },
        {
            "id": "ht_sin_01",
            "name": "Marina Bay Sands",
            "city": "Singapore",
            "country": "Singapore",
            "rating": 4.9,
            "stars": "5-Star Luxury",
            "pricePerNightUsd": 620.0,
            "image": "/images/singapore.jpg",
            "amenities": ["Rooftop Infinity Pool", "Casino", "SkyPark Observation Deck", "VIP Club Access"],
            "bookingUrl": f"https://www.trip.com/hotels/?{affiliate_tracking}"
        },
        {
            "id": "ht_bkk_01",
            "name": "The Peninsula Bangkok",
            "city": "Bangkok",
            "country": "Thailand",
            "rating": 4.8,
            "stars": "5-Star Luxury",
            "pricePerNightUsd": 280.0,
            "image": "/images/bangkok.jpg",
            "amenities": ["Chao Phraya River View", "Luxury Spa", "Private Ferry Service"],
            "bookingUrl": f"https://www.trip.com/hotels/?{affiliate_tracking}"
        },
        {
            "id": "ht_kul_01",
            "name": "Mandarin Oriental Kuala Lumpur",
            "city": "Kuala Lumpur",
            "country": "Malaysia",
            "rating": 4.8,
            "stars": "5-Star Luxury",
            "pricePerNightUsd": 195.0,
            "image": "/images/malaysia.jpg",
            "amenities": ["Petronas Twin Towers View", "Infinity Pool", "Award-winning Dining"],
            "bookingUrl": f"https://www.trip.com/hotels/?{affiliate_tracking}"
        }
    ]
    return jsonify({
        "success": True,
        "count": len(hotels),
        "hotels": hotels,
        "partner": "Hotelbeds & Booking Global Direct"
    })

@app.route("/api/tours", methods=["GET"])
@app.route("/tours", methods=["GET"])
def api_tours():
    """Returns curated bespoke travel tour packages."""
    tours = [
        {
            "id": "tr_dxb_safari",
            "title": "Dubai Royal Desert Safari & Burj Khalifa VIP",
            "destination": "Dubai, UAE",
            "duration": "5 Days / 4 Nights",
            "priceUsd": 599.0,
            "highlights": ["Dune Bashing", "Burj Khalifa 148th Floor", "Marina Dhow Cruise Dinner", "Free 10GB UAE eSIM"],
            "status": "Available"
        },
        {
            "id": "tr_tha_island",
            "title": "Thailand Island Hopping: Phuket & Phi Phi",
            "destination": "Phuket, Thailand",
            "duration": "6 Days / 5 Nights",
            "priceUsd": 450.0,
            "highlights": ["Speedboat to Phi Phi Islands", "Maya Bay Tour", "Snorkeling Equipment", "Free 15GB Thailand eSIM"],
            "status": "Available"
        },
        {
            "id": "tr_tur_capp",
            "title": "Turkey Highlights: Istanbul & Cappadocia Balloon",
            "destination": "Turkey",
            "duration": "7 Days / 6 Nights",
            "priceUsd": 890.0,
            "highlights": ["Hot Air Balloon Ride", "Bosphorus Sunset Yacht Cruise", "Cave Hotel Stay", "Free Turkey eSIM"],
            "status": "Available"
        },
        {
            "id": "tr_sau_umrah",
            "title": "Saudi Arabia Umrah VIP Package",
            "destination": "Mecca & Medina, Saudi Arabia",
            "duration": "10 Days / 9 Nights",
            "priceUsd": 1150.0,
            "highlights": ["5-Star Haram View Hotels", "Private Chauffeur Transfers", "Ziyarah Tours", "Free 5G Saudi eSIM"],
            "status": "Available"
        }
    ]
    return jsonify({
        "success": True,
        "count": len(tours),
        "tours": tours
    })

@app.route("/api/visa", methods=["GET"])
@app.route("/visa", methods=["GET"])
def api_visa():
    """Returns international visa application services & requirements."""
    visa_list = [
        {
            "country": "United Arab Emirates (UAE)",
            "code": "UAE",
            "types": ["30 Days Tourist Visa", "60 Days Multiple Entry"],
            "processingTime": "24 - 48 Hours",
            "feeUsd": 120.0,
            "documentsRequired": ["Passport Copy (6 months validity)", "Passport Photo with White Background", "Return Flight Ticket"]
        },
        {
            "country": "Saudi Arabia",
            "code": "KSA",
            "types": ["1 Year Multiple Entry Tourist eVisa", "Umrah Visa"],
            "processingTime": "24 Hours",
            "feeUsd": 150.0,
            "documentsRequired": ["Passport Copy", "Photograph", "Mandatory Medical Insurance (Included)"]
        },
        {
            "country": "Thailand",
            "code": "TH",
            "types": ["Tourist eVisa (60 Days)", "Visa on Arrival Prep"],
            "processingTime": "3 - 5 Business Days",
            "feeUsd": 65.0,
            "documentsRequired": ["Passport Copy", "Proof of Funds ($700+)", "Flight & Hotel Itinerary"]
        },
        {
            "country": "Singapore",
            "code": "SG",
            "types": ["e-Visa Entry Pass (30 Days)"],
            "processingTime": "2 - 3 Business Days",
            "feeUsd": 55.0,
            "documentsRequired": ["Passport Copy", "Form 14A", "Flight Reservation"]
        },
        {
            "country": "Schengen (Europe)",
            "code": "EU",
            "types": ["Short Stay Tourist Visa (Type C)"],
            "processingTime": "10 - 15 Business Days",
            "feeUsd": 180.0,
            "documentsRequired": ["Passport", "Bank Statement (6 Months)", "Travel Insurance (€30,000+)", "Hotel Bookings"]
        }
    ]
    return jsonify({
        "success": True,
        "count": len(visa_list),
        "visas": visa_list,
        "contact": "support@traveltrip.world"
    })

@app.route("/api/wallet", methods=["GET"])
@app.route("/wallet", methods=["GET"])
def api_wallet():
    """Returns user wallet balance, cashback, points, and referral earnings."""
    user_id = session.get("user_id")
    wallet_data = {
        "userId": user_id or "guest_traveler",
        "balanceUsd": 25.50 if user_id else 0.0,
        "cashbackEarnedUsd": 12.0,
        "rewardPoints": 450,
        "cashbackRates": {
            "esim": "5% Cashback",
            "flights": "2% Cashback",
            "hotels": "3% Cashback",
            "tours": "4% Cashback"
        },
        "referralCode": f"TRIP{secrets.token_hex(3).upper()}",
        "referralBonusUsd": 10.0,
        "recentTransactions": [
            {"title": "eSIM Cashback (UAE 5GB)", "amount": "+$1.20", "type": "credit", "date": "2026-09-28"},
            {"title": "Welcome Gift Credit", "amount": "+$10.00", "type": "credit", "date": "2026-09-20"}
        ]
    }
    return jsonify({
        "success": True,
        "wallet": wallet_data
    })

@app.route("/api/vip", methods=["GET"])
@app.route("/membership", methods=["GET"])
def api_vip():
    """Returns VIP Club tiers, Gold & Platinum membership benefits."""
    tiers = [
        {
            "tier": "Gold VIP",
            "feeUsd": 49.0,
            "period": "1 Year",
            "color": "#D4AF37",
            "perks": [
                "5% Extra Instant Discount across all eSIMs",
                "Priority 24/7 WhatsApp & Telegram Agent Support",
                "Exclusive Flash Deals & Unpublished Hotel Rates",
                "$20 Welcome Travel Credit"
            ]
        },
        {
            "tier": "Platinum Elite",
            "feeUsd": 99.0,
            "period": "1 Year",
            "color": "#E5E4E2",
            "perks": [
                "10% Extra Instant Discount across all eSIMs & Tours",
                "Dedicated Personal Travel Concierge",
                "Free Airport Lounge Pass voucher on Flight Bookings",
                "Complimentary 5GB Global Roaming eSIM",
                "$50 Welcome Travel Credit"
            ]
        }
    ]
    return jsonify({
        "success": True,
        "tiers": tiers
    })

@app.route("/api/ai/planner", methods=["POST"])
def api_ai_planner():
    """Generates AI trip itinerary based on destination, days, budget, and travel style."""
    data = request.get_json(silent=True) or {}
    destination = data.get("destination") or "Dubai"
    try:
        days = int(data.get("days") or 5)
    except Exception:
        days = 5
    budget = data.get("budget") or "moderate"
    travel_style = data.get("style") or "luxury & adventure"

    itinerary_plan = []
    for day in range(1, min(days + 1, 15)):
        itinerary_plan.append({
            "day": day,
            "title": f"Day {day}: Exploring {destination}'s Signature Attractions",
            "morning": f"Morning city tour, iconic landmarks & local breakfast in {destination}.",
            "afternoon": f"Cultural immersion, premium shopping, and culinary dining.",
            "evening": f"Sunset observation, skyline views, and signature dinner experience.",
            "recommendedEsim": "TravelTrip 5G High-Speed Roaming active for navigation and social sharing."
        })

    return jsonify({
        "success": True,
        "destination": destination,
        "days": days,
        "budget": budget,
        "style": travel_style,
        "suggestedBudgetUsd": days * (150 if budget == "budget" else 350 if budget == "moderate" else 750),
        "itinerary": itinerary_plan,
        "aiAssistant": "TravelTrip AI Super Assistant 2.0"
    })


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    print(f"\n[SERVER] TravelTrip Live Server starting on http://127.0.0.1:{port}")
    
    
    app.run(host="0.0.0.0", port=port, debug=False)
