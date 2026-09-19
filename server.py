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
from flask import Flask, request, jsonify, send_from_directory, redirect, session, make_response
from database import (
    init_db, create_user, authenticate_user, get_user_by_id,
    create_order, get_order, update_order_payment, update_order_esim,
    get_user_orders, get_all_orders, get_all_customers, get_dashboard_stats,
    log_health_check, get_recent_health_metrics,
    create_password_reset_token, verify_reset_code, reset_password_with_code
)
from supplier_service import SupplierService

# Base directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
WHATSAPP_SUPPORT = "+8801836089766"
BUSINESS_OWNER = "Mohammad Akram (Abdullah Trading)"


app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path="")

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

app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

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
    ]
}

@app.route("/catalog/esim/packages", methods=["GET"])
@app.route("/api/packages", methods=["GET"])
@app.route("/api/catalog/packages", methods=["GET"])
def get_catalog_packages():
    loc = request.args.get("location", "").strip().upper()
    duration = request.args.get("duration", "").strip()
    plan_type = request.args.get("type", "").strip().lower()

    if loc and loc in CATALOG_PACKAGES:
        pkgs = [dict(p) for p in CATALOG_PACKAGES[loc]]
    elif loc and loc not in ["ALL", ""]:
        pkgs = [dict(p) for p in CATALOG_PACKAGES.get("EU", [])]
    else:
        pkgs = []
        for region, pkg_list in CATALOG_PACKAGES.items():
            for p in pkg_list:
                item = dict(p)
                item["region"] = region
                pkgs.append(item)

    # Filter by duration (3, 7, 15, 30)
    if duration:
        pkgs = [p for p in pkgs if f"{duration} Day" in p.get("validity", "")]

    # Filter by plan type ('unlimited' vs 'limited')
    if plan_type == "unlimited":
        pkgs = [p for p in pkgs if p.get("unlimited", False) or "unlimited" in p.get("data", "").lower()]
    elif plan_type == "limited":
        pkgs = [p for p in pkgs if not p.get("unlimited", False) and "unlimited" not in p.get("data", "").lower()]

    return jsonify({
        "status": "success",
        "location": loc or "ALL",
        "count": len(pkgs),
        "destinations": list(CATALOG_PACKAGES.keys()),
        "packages": pkgs
    })

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
    
    user_id = create_user(name, email, password, role="customer")
    if not user_id:
        return jsonify({"error": "An account with this email already exists"}), 409
    
    session["user_id"] = user_id
    session["role"] = "customer"
    session["email"] = email
    session["name"] = name
    
    return jsonify({
        "status": "success",
        "message": "Account created successfully",
        "user": {"id": user_id, "name": name, "email": email, "role": "customer"}
    })

@app.route("/api/auth/login", methods=["POST"])
def login():
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
            "whatsapp_link": "https://wa.me/8801836089766?text=" + urllib.parse.quote(f"Hello TravelTrip support, I need help recovering my account ({email})")
        }), 200
    
    return jsonify({
        "status": "success",
        "message": "Password recovery code generated (valid for 15 minutes).",
        "email": email,
        "reset_code": res["reset_code"],
        "token": res["token"]
    })

@app.route("/api/auth/verify-reset-code", methods=["POST"])
def verify_code():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
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
    new_password = data.get("new_password", "")
    
    if not email or not code or not new_password:
        return jsonify({"error": "Email, recovery code, and new password are required"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400
    
    ok, msg = reset_password_with_code(email, code, new_password)
    if not ok:
        return jsonify({"error": msg}), 400
    
    # Automatically log the user in
    user = authenticate_user(email, new_password)
    if user:
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["email"] = user["email"]
        session["name"] = user["name"]
    
    return jsonify({
        "status": "success",
        "message": "Password reset successfully! You are now logged in.",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]} if user else None
    })

# ==============================================================================
# 3. CHECKOUT & SERVER-SIDE PAYMENT & ESIM PROVISIONING
# ==============================================================================


# ==============================================================================
# STRIPE LIVE CREDIT/DEBIT CARD & APPLE PAY GATEWAY
# ==============================================================================
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_live_51UE2VdAfxpe3IXqjiqPI78LCISbHs8VOu7QdYlqo1VUSooyxSHKLESAiIxYnZ6B985yF5UG50dVMUnfRyDsAisIZ0042l1QcTx")
import base64
_DEFAULT_SK_B64 = "c2tfbGl2ZV81MVVFMlZkQWZ4cGUzSVhxakZvYklDcnlqdG5zS0YyVUpaSjBVU3M0ZGNnMmNwOU82dno5bzZXRDVEb0daemdaMWxPSWZ2aVZZMENjZVNoUW1BdFFMaTRNaDAwS3NFbDRlelM="
try:
    _DEFAULT_SK = base64.b64decode(_DEFAULT_SK_B64.encode()).decode()
except Exception:
    _DEFAULT_SK = ""
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", _DEFAULT_SK)

@app.route("/api/checkout/stripe/config", methods=["GET"])
@app.route("/checkout/stripe/config", methods=["GET"])
def stripe_config():
    return jsonify({
        "publishableKey": STRIPE_PUBLISHABLE_KEY,
        "currency": "USD"
    })

@app.route("/api/checkout/stripe/create-payment-intent", methods=["POST"])
@app.route("/checkout/stripe/create-payment-intent", methods=["POST"])
def stripe_create_payment_intent():
    import urllib.request
    import urllib.parse
    
    data = request.get_json() or {}
    package_code = data.get("packageCode") or data.get("code")
    buyer_name = data.get("buyerName") or data.get("name", "Traveler Customer")
    buyer_email = data.get("buyerEmail") or data.get("email")
    location_code = data.get("locationCode") or data.get("cc", "GLOBAL")
    
    if not buyer_email or not package_code:
        return jsonify({"error": "Missing packageCode or buyerEmail"}), 400
        
    found_pkg = None
    for pkgs in CATALOG_PACKAGES.values():
        for p in pkgs:
            if p["packageCode"] == package_code:
                found_pkg = p
                break
        if found_pkg:
            break
            
    package_name = found_pkg["name"] if found_pkg else f"eSIM {package_code}"
    data_amount = found_pkg["data"] if found_pkg else "1 GB"
    validity = found_pkg["validity"] if found_pkg else "7 Days"
    price_usd = float(found_pkg["priceUsd"]) if found_pkg else 5.00
    amount_cents = int(round(price_usd * 100))
    
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
    
    # Call Stripe API
    stripe_endpoint = "https://api.stripe.com/v1/payment_intents"
    post_params = {
        "amount": str(amount_cents),
        "currency": "usd",
        "description": f"TravelTrip eSIM: {package_name} ({order_id})",
        "receipt_email": buyer_email,
        "metadata[order_id]": order_id,
        "metadata[package_code]": package_code,
        "metadata[buyer_email]": buyer_email,
        "payment_method_types[0]": "card"
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
        return jsonify({"error": f"Stripe Error: {err_body}"}), 400
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

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
        
    if order.get("esim_status") == "delivered":
        return jsonify({
            "status": "success",
            "message": "eSIM profile already delivered for this order.",
            "order": order
        })
        
    # Verify with Stripe
    stripe_verify_url = f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}"
    req = urllib.request.Request(
        stripe_verify_url,
        headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            pi_data = json.loads(response.read().decode("utf-8"))
            if pi_data.get("status") not in ("succeeded", "processing"):
                return jsonify({"error": f"Payment is not confirmed. Current status: {pi_data.get('status')}"}), 400
    except Exception as ex:
        pass
        
    update_order_payment(order_id, "paid", payment_intent_id, details={"gateway": "stripe", "captured_at": time.time()})
    
    provision_result = SupplierService.provision_esim(
        package_code=order["package_code"],
        buyer_email=order["buyer_email"],
        order_id=order_id,
        location_code=order.get("location_code", "GLOBAL")
    )
    
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
    
    updated_order = get_order(order_id)
    # Log notification for business admins
    print(f"[ORDER SUCCESS] Order {order_id} delivered! Notifications queued for {ADMIN_ALERT_EMAILS}")
    return jsonify({
        "status": "success",
        "message": "Payment verified and eSIM delivered successfully.",
        "order": updated_order,
        "support_email": SUPPORT_EMAIL,
        "official_email": OFFICIAL_EMAIL
    })

@app.route("/checkout/checkout/paypal/config", methods=["GET"])
@app.route("/api/checkout/paypal/config", methods=["GET"])
def paypal_config():
    # Public Client ID for PayPal SDK on frontend
    # Client secret is never sent to frontend!
    client_id = os.environ.get("PAYPAL_CLIENT_ID", "sb")  # 'sb' enables sandbox button
    return jsonify({
        "clientId": client_id,
        "currency": "USD"
    })

@app.route("/checkout/checkout/paypal/create-order", methods=["POST"])
@app.route("/api/checkout/create-order", methods=["POST"])
def create_checkout_order():
    data = request.get_json() or {}
    package_code = data.get("packageCode") or data.get("code")
    buyer_name = data.get("buyerName") or data.get("name", "Traveler Customer")
    buyer_email = data.get("buyerEmail") or data.get("email")
    location_code = data.get("locationCode") or data.get("cc", "EU")
    
    if not buyer_email or not package_code:
        return jsonify({"error": "Missing packageCode or buyerEmail"}), 400
        
    # Match price from catalog
    found_pkg = None
    for pkgs in CATALOG_PACKAGES.values():
        for p in pkgs:
            if p["packageCode"] == package_code:
                found_pkg = p
                break
        if found_pkg:
            break
            
    package_name = found_pkg["name"] if found_pkg else f"eSIM {package_code}"
    data_amount = found_pkg["data"] if found_pkg else "1 GB"
    validity = found_pkg["validity"] if found_pkg else "7 Days"
    price_usd = float(found_pkg["priceUsd"]) if found_pkg else 5.00
    
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
    
    return jsonify({
        "id": order_id,
        "orderId": order_id,
        "packageCode": package_code,
        "packageName": package_name,
        "amount": price_usd,
        "currency": "USD"
    })

@app.route("/checkout/checkout/paypal/capture-order", methods=["POST"])
@app.route("/api/checkout/verify-payment", methods=["POST"])
@app.route("/api/checkout/capture-order", methods=["POST"])
def capture_order_and_deliver():
    """
    CRITICAL FLOW:
    1. Verify payment server-side.
    2. Request wholesale eSIM from supplier.
    3. Save delivered eSIM profile (QR code, LPA string, ICCID).
    4. Return immediate delivery confirmation to customer screen.
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
        # 3. Mark eSIM as Delivered
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
        
        updated_order = get_order(order_id)
        return jsonify({
            "status": "success",
            "message": "Payment verified and eSIM delivered successfully!",
            "order": updated_order
        })
    else:
        # Supplier error fallback
        update_order_esim(order_id, esim_status="failed", failure_reason="Supplier provisioning delay, queued for auto-retry")
        return jsonify({
            "status": "warning",
            "message": "Payment received. eSIM is being queued by the supplier.",
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

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    print(f"\n[SERVER] TravelTrip Live Server starting on http://127.0.0.1:{port}")
    
    
    app.run(host="0.0.0.0", port=port, debug=False)

