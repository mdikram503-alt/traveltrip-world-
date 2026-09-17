"""
TravelTrip World — Database Layer (SQLite)
Production-ready, ACID compliant, persistent storage.
"""

import psycopg2
import psycopg2.extras
from urllib.parse import urlparse
import os
import hashlib
import secrets
import json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "traveltrip.db")

def get_db():
    db_url = os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('DATABASE_URL')
    if not db_url:
        print("[WARNING] DATABASE_URL is not set. Using local sqlite for testing if needed.")
        import sqlite3
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    conn = psycopg2.connect(db_url)
    return conn

def hash_password(password: str, salt: str = None) -> str:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, hashed = stored_hash.split("$", 1)
    test_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(hashed, test_hash)

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 1. Users table (Customer accounts & Admins)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY SERIAL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Orders & eSIM fulfillment table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY SERIAL,
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
        
        # 3. 24/7 Health Monitoring Metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY SERIAL,
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

    # Seed initial default admin
    seed_default_users()

def seed_default_users():
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        if not cursor.fetchone():
            admin_pass = hash_password("AdminSecure2026!")
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ("TravelTrip Admin", "admin@traveltrip.world", admin_pass, "admin")
            )
            conn.commit()
            print("[DB] Initialized default Admin: admin@traveltrip.world")

def create_user(name: str, email: str, password: str, role: str = "customer"):
    email = email.strip().lower()
    pass_hash = hash_password(password)
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            if hasattr(conn, 'row_factory'):
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (name.strip(), email, pass_hash, role)
                )
                conn.commit()
                return cursor.lastrowid
            else:
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
                    (name.strip(), email, pass_hash, role)
                )
                user_id = cursor.fetchone()[0]
                conn.commit()
                return user_id
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            return None

def authenticate_user(email: str, password: str):
    email = email.strip().lower()
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and verify_password(password, user["password_hash"]):
            return dict(user)
    return None

def get_user_by_id(user_id: int):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_email(email: str):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE email = %s", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_order(buyer_name: str, buyer_email: str, package_code: str,
                 package_name: str, data_amount: str, validity: str,
                 price_usd: float, location_code: str, user_id: int = None,
                 payment_method: str = "paypal"):
    order_id = f"TT-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            INSERT INTO orders (
                order_id, user_id, buyer_name, buyer_email,
                package_code, package_name, data_amount, validity,
                price_usd, location_code, payment_method, payment_status,
                esim_status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            order_id, user_id, buyer_name.strip(), buyer_email.strip().lower(),
            package_code, package_name, data_amount, validity,
            price_usd, location_code, payment_method
        ))
        conn.commit()
    return order_id

def get_order(order_id: str):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_order_payment(order_id: str, payment_status: str, payment_id: str, payment_details: dict = None):
    details_json = json.dumps(payment_details or {})
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            UPDATE orders SET
                payment_status = %s,
                payment_id = %s,
                payment_details = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = %s
        """, (payment_status, payment_id, details_json, order_id))
        conn.commit()

def update_order_esim(order_id: str, esim_status: str, supplier_order_id: str = None,
                      qr_code_data: str = None, lpa_string: str = None,
                      iccid: str = None, activation_code: str = None,
                      smdp_address: str = None, failure_reason: str = None):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            UPDATE orders SET
                esim_status = %s,
                supplier_order_id = COALESCE(%s, supplier_order_id),
                qr_code_data = COALESCE(%s, qr_code_data),
                lpa_string = COALESCE(%s, lpa_string),
                iccid = COALESCE(%s, iccid),
                activation_code = COALESCE(%s, activation_code),
                smdp_address = COALESCE(%s, smdp_address),
                failure_reason = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = %s
        """, (
            esim_status, supplier_order_id, qr_code_data, lpa_string,
            iccid, activation_code, smdp_address, failure_reason, order_id
        ))
        conn.commit()

def get_user_orders(user_id: int = None, email: str = None):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if user_id and email:
            cursor.execute("""
                SELECT * FROM orders 
                WHERE user_id = %s OR LOWER(buyer_email) = LOWER(%s)
                ORDER BY created_at DESC
            """, (user_id, email))
        elif user_id:
            cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        elif email:
            cursor.execute("SELECT * FROM orders WHERE LOWER(buyer_email) = LOWER(%s) ORDER BY created_at DESC", (email,))
        else:
            return []
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_all_orders(status_filter: str = None, limit: int = 100):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if status_filter:
            cursor.execute("""
                SELECT * FROM orders 
                WHERE payment_status = %s OR esim_status = %s
                ORDER BY created_at DESC LIMIT %s
            """, (status_filter, status_filter, limit))
        else:
            cursor.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT %s", (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_all_customers():
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.role, u.created_at,
                   COUNT(o.id) as total_orders,
                   COALESCE(SUM(CASE WHEN o.payment_status = 'paid' THEN o.price_usd ELSE 0 END), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id OR LOWER(u.email) = LOWER(o.buyer_email)
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_dashboard_stats():
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cursor.execute("SELECT COUNT(*) as total FROM orders")
        total_orders = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as paid FROM orders WHERE payment_status = 'paid'")
        paid_orders = cursor.fetchone()["paid"]
        
        cursor.execute("SELECT COUNT(*) as failed FROM orders WHERE payment_status = 'failed'")
        failed_orders = cursor.fetchone()["failed"]
        
        cursor.execute("SELECT COUNT(*) as delivered FROM orders WHERE esim_status = 'delivered'")
        delivered_esims = cursor.fetchone()["delivered"]
        
        cursor.execute("SELECT COALESCE(SUM(price_usd), 0) as revenue FROM orders WHERE payment_status = 'paid'")
        revenue = cursor.fetchone()["revenue"]
        
        cursor.execute("SELECT COUNT(*) as users_count FROM users WHERE role = 'customer'")
        total_customers = cursor.fetchone()["users_count"]
        
        return {
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "failed_orders": failed_orders,
            "delivered_esims": delivered_esims,
            "total_revenue_usd": round(revenue, 2),
            "total_customers": total_customers
        }

def log_health_check(service_name: str, url: str, status: str, latency_ms: float, is_healthy: bool, error_details: str = None):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            INSERT INTO health_metrics (service_name, url, status, latency_ms, is_healthy, error_details)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (service_name, url, status, latency_ms, 1 if is_healthy else 0, error_details))
        conn.commit()

def get_recent_health_metrics(limit: int = 15):
    with get_db() as conn:
        if hasattr(conn, 'row_factory'): # sqlite fallback
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            SELECT * FROM health_metrics 
            ORDER BY id DESC LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

# Auto-initialize on import
init_db()
