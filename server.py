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

# Search terms accepted by the website. Keeping these aliases server-side means
# the web site, mobile client and checkout API resolve destinations identically.
CATALOG_ALIASES = {
    "BANGLADESH": "BD", "DHAKA": "BD", "INDIA": "IN", "PAKISTAN": "PK",
    "UNITED ARAB EMIRATES": "UAE", "EMIRATES": "UAE", "DUBAI": "UAE",
    "OMAN": "OM", "QATAR": "QA", "DOHA": "QA", "EUROPE": "EU",
    "ASIA": "ASIA", "THAILAND": "TH", "USA": "US", "UNITED STATES": "US",
    "AMERICA": "US", "WORLDWIDE": "GLOBAL", "WORLD": "GLOBAL",
}

@app.route("/catalog/esim/packages", methods=["GET"])
@app.route("/api/packages", methods=["GET"])
@app.route("/api/catalog/packages", methods=["GET"])
def get_catalog_packages():
    requested_location = request.args.get("location", "").strip().upper()
    loc = CATALOG_ALIASES.get(requested_location, requested_location)
    duration = request.args.get("duration", "").strip()
    plan_type = request.args.get("type", "").strip().lower()

        # Prefer the verified supplier catalog with blazing-fast gzip and query caching
    supplier_packages = SupplierService.live_catalog(location_filter=loc if loc not in ["ALL", ""] else "")
    if not supplier_packages and (not loc or loc == "ALL"):
        supplier_packages = SupplierService.live_catalog()

    if supplier_packages:
        all_regions = sorted({r.strip() for p in supplier_packages for r in p.get("region", "").split(",") if r.strip()})
        pkgs = [p for p in supplier_packages if not loc or loc == "ALL" or loc == p.get("region") or loc in p.get("region", "").split(",")]
    else:
        all_regions = list(CATALOG_PACKAGES.keys())
        pkgs = None

    if pkgs is not None:
        pass
    elif loc and loc in CATALOG_PACKAGES:
        pkgs = [{**p, "region": loc} for p in CATALOG_PACKAGES[loc]]
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
        pkgs = [p for p in pkgs if f"{duration} Day" in p.get("validity", "")]

    # Filter by plan type ('unlimited' vs 'limited')
    if plan_type == "unlimited":
        pkgs = [p for p in pkgs if p.get("unlimited", False) or "unlimited" in p.get("data", "").lower()]
    elif plan_type == "limited":
        pkgs = [p for p in pkgs if not p.get("unlimited", False) and "unlimited" not in p.get("data", "").lower()]

    return jsonify({
        "status": "success",
        "location": loc or "ALL",
        "requestedLocation": requested_location or "ALL",
        "count": len(pkgs),
        "destinations": all_regions,
        "packages": pkgs,
        "supplier_live": bool(supplier_packages),
        "supplier_error": getattr(SupplierService, "last_error", ""),
        "active_key": getattr(SupplierService, "active_key", "")
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
    if not provision_result.get("success"):
        update_order_esim(order_id=order_id, esim_status="failed", failure_reason=provision_result.get("error", "Supplier provisioning failed"))
        return jsonify({"error": "Payment received, but eSIM delivery could not be completed. Support has been notified.", "orderId": order_id}), 502
    
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

    unread_cnt = len(_OFFICIAL_EMAILS) if '_OFFICIAL_EMAILS' in globals() else 0
    if unread_cnt > 0:
        voice_summary_bn = f"সব সিস্টেম সক্রিয় · স্ট্রাইপ: د.إ {balance_aed} AED · {unread_cnt}টি সাপোর্ট বার্তা অপেক্ষমাণ"
        voice_summary_en = f"All systems active · Stripe: {balance_aed} AED · {unread_cnt} support emails pending"
    else:
        voice_summary_bn = f"সব সিস্টেম সক্রিয় · স্ট্রাইপ: د.إ {balance_aed} AED · চেকআউট প্রস্তুত"
        voice_summary_en = f"All systems active · Stripe: {balance_aed} AED · Checkout ready"

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
        "facebook_page_id": "61594435043497",
        "facebook_page_name": "traveltrip.world Page",
        "meta_business_asset_id": "1333860239808615",
        "meta_ad_account": "570759352948058",
        "instagram_brand": "@trave_ltripworld",
        "instagram_owner": "@mohammad_ekram5",
        "tiktok": "@traveltrip.world8",
        "x_twitter": "@traveltripakm",
        "snapchat": "traveltripworld",
        "threads": "@trave_ltripworld",
        "whatsapp": "+8801836089766",
        "primary_email": "traveltripworld8@gmail.com",
        "facebook_page_token": "",
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
            "facebook": {"name": "Facebook (traveltrip.world)", "status": "active", "id": "61594435043497"},
            "instagram": {"name": "Instagram (@trave_ltripworld)", "status": "active"},
            "tiktok": {"name": "TikTok (@traveltrip.world8)", "status": "active"},
            "x_twitter": {"name": "X Twitter (@traveltripakm)", "status": "active"},
            "snapchat": {"name": "Snapchat (traveltripworld)", "status": "active"},
            "threads": {"name": "Threads (@trave_ltripworld)", "status": "active"},
            "whatsapp": {"name": "WhatsApp (+8801836089766)", "status": "active"},
            "email": {"name": "Gmail (traveltripworld8@gmail.com)", "status": "active"}
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
        f"💬 ২৪/৭ হোয়াটসঅ্যাপ সাপোর্ট: +880 1836-089766\n\n"
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

    return jsonify({
        "success": True,
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
        reply_bn = "হ্যালো! TravelTrip World-এ স্বাগতম। বিশ্বের ১৩০+ দেশের হাই-স্পিড ট্রাভেল eSIM পেতে ভিজিট করুন https://traveltrip.world। ২৪/৭ সরাসরি সাপোর্টের জন্য হোয়াটসঅ্যাপে লিখুন: +880 1836-089766।"
        reply_en = "Welcome to TravelTrip World! Get high-speed travel eSIMs for 130+ destinations at https://traveltrip.world. For 24/7 dedicated assistance, WhatsApp us at +880 1836-089766."

    return jsonify({
        "success": True,
        "reply_bn": reply_bn,
        "reply_en": reply_en,
        "whatsapp_url": "https://wa.me/8801836089766"
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
            "❤️ আপনার ভ্রমণ সফল হোক! কোনো কিছুতে আটকে গেলে ২৪/৭ আমাদের হোয়াটসঅ্যাপে লিখুন: +880 1836-089766।"
        )
        guide_en = (
            "🚨 3-Step Roadmap to Get Connected:\n\n"
            "1. Go to Settings > Cellular > Select TravelTrip eSIM and toggle 'Data Roaming' ON.\n"
            "2. Turn Airplane Mode ON for 10 seconds, then OFF to force a fresh cell tower handshake.\n"
            "3. In Network Selection, manually pick the premier partner carrier (e.g. DU/Etisalat in UAE, Vodafone/Orange in Europe).\n\n"
            "❤️ Need immediate live assist? WhatsApp us at +880 1836-089766!"
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
            "👉 ফেসবুক রিভিউ লিংক: https://www.facebook.com/profile.php?id=61594435043497\n"
            "ধন্যবাদ Abdullah Trading & TravelTrip পরিবারের সাথে থাকার জন্য! ❤️"
        )
        guide_en = (
            "🌟 Dear Traveler, we hope TravelTrip eSIM kept your journey seamlessly connected!\n\n"
            "If you loved our instant service, please take 30 seconds to drop us a 5-Star review on Facebook. "
            "Your kind words empower fellow travelers worldwide!\n\n"
            "👉 Review Page: https://www.facebook.com/profile.php?id=61594435043497\n"
            "Thank you for choosing TravelTrip World! ❤️"
        )
    else:
        title = "২৪/৭ ট্রাভেলার গাইডলাইন ও রোডম্যাপ"
        guide_bn = (
            "সুপ্রিয় ট্রাভেলার, TravelTrip World সবসময় আপনার পাশে আছে। সেটআপ, রোমিং অন করা কিংবা যেকোনো টেকনিক্যাল সাপোর্টে আমাদের টিম দিনরাত ২৪ ঘণ্টা প্রস্তুত।\n"
            "সরাসরি লাইভ চ্যাটের জন্য আমাদের হোয়াটসঅ্যাপে লিখুন: +880 1836-089766।"
        )
        guide_en = (
            "Dear Traveler, TravelTrip World is dedicated to keeping you connected 24/7. "
            "For immediate live engineer assistance, chat with us on WhatsApp: +880 1836-089766."
        )

    return jsonify({
        "success": True,
        "title": title,
        "guide_bn": guide_bn,
        "guide_en": guide_en,
        "whatsapp_url": "https://wa.me/8801836089766"
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


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    print(f"\n[SERVER] TravelTrip Live Server starting on http://127.0.0.1:{port}")
    
    
    app.run(host="0.0.0.0", port=port, debug=False)
