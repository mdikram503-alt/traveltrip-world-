"""
TravelTrip World Database Module
SQLite Database abstraction for User Accounts, eSIM Orders, and Health Metrics.
"""

import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "traveltrip.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
    except Exception:
        pass
    return conn

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash:
        return False
    sep = '$' if '$' in stored_hash else (':' if ':' in stored_hash else None)
    if not sep:
        return False
    salt, hashed = stored_hash.split(sep, 1)
    if hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == hashed:
        return True
    if hashlib.sha256((password + salt).encode("utf-8")).hexdigest() == hashed:
        return True
    return False

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            buyer_name TEXT NOT NULL,
            buyer_email TEXT NOT NULL,
            package_code TEXT NOT NULL,
            package_name TEXT NOT NULL,
            data_amount TEXT,
            validity TEXT,
            price_usd REAL NOT NULL,
            location_code TEXT,
            payment_method TEXT DEFAULT 'paypal',
            payment_status TEXT DEFAULT 'pending',
            payment_id TEXT,
            payment_details TEXT,
            esim_status TEXT DEFAULT 'pending',
            supplier_order_id TEXT,
            qr_code_data TEXT,
            lpa_string TEXT,
            iccid TEXT,
            activation_code TEXT,
            smdp_address TEXT,
            failure_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            reset_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            service_name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            latency_ms REAL NOT NULL,
            is_healthy INTEGER DEFAULT 1,
            error_details TEXT
        )
        """)
        conn.commit()
    seed_default_users()

def seed_default_users():
    admin_email = "admin@traveltrip.world"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("TravelTrip Admin", admin_email, hash_password(os.environ.get("ADMIN_PASSWORD", secrets.token_urlsafe(16))), "admin")
            )
            conn.commit()

def create_user(name, email, password, role="customer"):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            pw_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email.lower().strip(), pw_hash, role)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def authenticate_user(email, password):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        user = cursor.fetchone()
        if user and verify_password(user["password_hash"], password):
            return dict(user)
        return None

def get_user_by_id(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None

def get_user_by_email(email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE email = ?", (email.lower().strip(),))
        user = cursor.fetchone()
        return dict(user) if user else None

def create_order(buyer_name, buyer_email, package_code, package_name, data_amount, validity, price_usd, location_code=None, user_id=None, payment_method="paypal"):
    order_id = f"TT-{secrets.token_hex(4).upper()}"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (
                order_id, user_id, buyer_name, buyer_email, package_code,
                package_name, data_amount, validity, price_usd, location_code,
                payment_method, payment_status, esim_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'pending')
        """, (
            order_id, user_id, buyer_name, buyer_email.lower().strip(),
            package_code, package_name, data_amount, validity, float(price_usd),
            location_code, payment_method
        ))
        conn.commit()
    return order_id

def get_order(order_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()
        return dict(order) if order else None

def update_order_payment(order_id, payment_status, payment_id=None, details=None):
    details_str = json.dumps(details) if isinstance(details, (dict, list)) else details
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE orders
            SET payment_status = ?, payment_id = coalesce(?, payment_id),
                payment_details = coalesce(?, payment_details),
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        """, (payment_status, payment_id, details_str, order_id))
        conn.commit()

def update_order_esim(order_id, esim_status, supplier_order_id=None, qr_code_data=None,
                      lpa_string=None, iccid=None, activation_code=None, smdp_address=None, failure_reason=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE orders
            SET esim_status = ?,
                supplier_order_id = coalesce(?, supplier_order_id),
                qr_code_data = coalesce(?, qr_code_data),
                lpa_string = coalesce(?, lpa_string),
                iccid = coalesce(?, iccid),
                activation_code = coalesce(?, activation_code),
                smdp_address = coalesce(?, smdp_address),
                failure_reason = coalesce(?, failure_reason),
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        """, (
            esim_status, supplier_order_id, qr_code_data, lpa_string,
            iccid, activation_code, smdp_address, failure_reason, order_id
        ))
        conn.commit()

def get_user_orders(user_id=None, email=None):
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        elif email:
            cursor.execute("SELECT * FROM orders WHERE buyer_email = ? ORDER BY created_at DESC", (email.lower().strip(),))
        else:
            return []
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_all_orders(status_filter=None):
    with get_db() as conn:
        cursor = conn.cursor()
        if status_filter and status_filter != "all":
            cursor.execute("SELECT * FROM orders WHERE payment_status = ? OR esim_status = ? ORDER BY created_at DESC", (status_filter, status_filter))
        else:
            cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_all_customers():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.role, u.created_at,
                   COUNT(o.id) as order_count,
                   COALESCE(SUM(CASE WHEN o.payment_status = 'paid' THEN o.price_usd ELSE 0 END), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_dashboard_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM orders")
        total_orders = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as paid FROM orders WHERE payment_status = 'paid'")
        paid_orders = cursor.fetchone()["paid"]
        cursor.execute("SELECT COUNT(*) as delivered FROM orders WHERE esim_status = 'delivered'")
        delivered_esims = cursor.fetchone()["delivered"]
        cursor.execute("SELECT COALESCE(SUM(price_usd), 0) as rev FROM orders WHERE payment_status = 'paid'")
        total_revenue = cursor.fetchone()["rev"]
        cursor.execute("SELECT COUNT(*) as users_count FROM users")
        total_users = cursor.fetchone()["users_count"]
        return {
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "delivered_esims": delivered_esims,
            "total_revenue_usd": round(float(total_revenue), 2),
            "total_customers": total_users
        }

def log_health_check(service_name, url, status, latency_ms, is_healthy=1, error_details=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO health_metrics (service_name, url, status, latency_ms, is_healthy, error_details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (service_name, url, status, float(latency_ms), 1 if is_healthy else 0, error_details))
        conn.commit()

def get_recent_health_metrics(limit=15):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM health_metrics ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


from datetime import timedelta

def create_password_reset_token(email: str):
    email_clean = email.lower().strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (email_clean,))
        user = cursor.fetchone()
        if not user:
            return None, "No account found with this email address"
        
        token = secrets.token_urlsafe(24)
        reset_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now() + timedelta(minutes=15)
        
        cursor.execute("""
            INSERT INTO password_resets (email, token, reset_code, expires_at, used)
            VALUES (?, ?, ?, ?, 0)
        """, (email_clean, token, reset_code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return {
            "token": token,
            "reset_code": reset_code,
            "email": email_clean,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S")
        }, None

def verify_reset_code(email: str, code_or_token: str):
    email_clean = email.lower().strip()
    code_clean = code_or_token.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM password_resets
            WHERE email = ? AND (reset_code = ? OR token = ?) AND used = 0
            ORDER BY id DESC LIMIT 1
        """, (email_clean, code_clean, code_clean))
        record = cursor.fetchone()
        if not record:
            return False, "Invalid or expired recovery code"
        
        expires_at = datetime.strptime(record["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires_at:
            return False, "Recovery code has expired. Please request a new one."
        return True, dict(record)

def reset_password_with_code(email: str, code_or_token: str, new_password: str):
    is_valid, record_or_err = verify_reset_code(email, code_or_token)
    if not is_valid:
        return False, record_or_err
    
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters long"
    
    email_clean = email.lower().strip()
    with get_db() as conn:
        cursor = conn.cursor()
        new_hash = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, email_clean))
        cursor.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (record_or_err["id"],))
        conn.commit()
    return True, "Password reset successfully. You can now log in with your new password."
