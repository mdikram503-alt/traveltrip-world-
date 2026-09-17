# TravelTrip World — VPS Deployment & 24/7 Health Monitoring Guide

This guide details how to deploy the **TravelTrip eSIM Production Server** and the **24/7 VPS Health Monitoring Daemon** onto your cloud VPS (Ubuntu, Debian, or Windows Server).

---

## 🔒 1. Architecture & Security Model

```
                    [ Android APK / iOS App / Web Clients ]
                                      │
                                      │ HTTPS (NO SECRETS IN APP)
                                      ▼
             ┌───────────────────────────────────────────────────┐
             │                 Your Cloud VPS                    │
             │                                                   │
             │  ┌────────────────────┐   ┌────────────────────┐  │
             │  │ TravelTrip Server  │   │  24/7 VPS Daemon   │  │
             │  │  - Auth & Accounts │   │  - Site pings      │  │
             │  │  - Checkout & Pay  │   │  - API latency     │  │
             │  │  - eSIM Auto-order │   │  - Supplier health │  │
             │  │  - Admin Dashboard │   │  - SQLite logging  │  │
             │  └─────────┬──────────┘   └─────────┬──────────┘  │
             │            │                        │             │
             │            ▼                        ▼             │
             │      [ SQLite DB: users, orders, health_metrics ]  │
             └──────────────────────┬────────────────────────────┘
                                    │
                         HTTPS Server-to-Server
                                    ▼
             [ Wholesale Supplier: esimtraveler.appserviceportal.com ]
```

- **App Security**: No API keys, passwords, or supplier tokens are packaged into the APK or iOS app.
- **Server Verification**: The customer cannot fake payments. eSIM provisioning is executed only after the payment transaction is verified server-to-server.
- **24/7 Health Daemon**: Runs on the server as an independent system daemon so monitoring continues 24/7 regardless of app or user traffic.

---

## 🚀 2. Linux VPS Deployment (Ubuntu / Debian)

### Step 1: Upload Files
Upload the `TravelTrip_Server/` directory to your VPS:
```bash
scp -r TravelTrip_Server root@YOUR_VPS_IP:/var/www/traveltrip
```

### Step 2: Install Python Dependencies
```bash
ssh root@YOUR_VPS_IP
cd /var/www/traveltrip
apt-get update && apt-get install -y python3 python3-pip
pip3 install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy and edit `.env`:
```bash
cp .env.example .env
nano .env
```
Set your real wholesale credentials and PayPal/payment keys:
```ini
PORT=8000
FLASK_SECRET_KEY=generate_random_key_here
SUPPLIER_URL=https://esimtraveler.appserviceportal.com
SUPPLIER_API_KEY=your_wholesale_api_key
DEFAULT_SMDP=rsp.esimaccess.com
PAYPAL_CLIENT_ID=your_paypal_client_id
SITE_URL=https://traveltrip.world
```

---

## 🩺 3. Setup 24/7 Services via systemd (Auto-start on boot)

### Service 1: Web Server (`traveltrip.service`)
Create `/etc/systemd/system/traveltrip.service`:
```ini
[Unit]
Description=TravelTrip eSIM Production Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/traveltrip
ExecStart=/usr/bin/python3 /var/www/traveltrip/server.py
Restart=always
RestartSec=5
EnvironmentFile=/var/www/traveltrip/.env

[Install]
WantedBy=multi-user.target
```

### Service 2: 24/7 Health Monitoring Daemon (`traveltrip-monitor.service`)
Create `/etc/systemd/system/traveltrip-monitor.service`:
```ini
[Unit]
Description=TravelTrip 24/7 Background Health Monitor Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/traveltrip/monitor
ExecStart=/usr/bin/python3 /var/www/traveltrip/monitor/vps_health_daemon.py
Restart=always
RestartSec=10
EnvironmentFile=/var/www/traveltrip/.env

[Install]
WantedBy=multi-user.target
```

### Step 4: Enable and Start Services
```bash
systemctl daemon-reload
systemctl enable --now traveltrip.service
systemctl enable --now traveltrip-monitor.service
```

Verify that both services are running:
```bash
systemctl status traveltrip.service
systemctl status traveltrip-monitor.service
```

---

## 🌐 4. Nginx Reverse Proxy with SSL (traveltrip.world)

Install Nginx and Certbot for free auto-renewing HTTPS:
```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

Configure `/etc/nginx/sites-available/traveltrip`:
```nginx
server {
    server_name traveltrip.world www.traveltrip.world;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and activate SSL:
```bash
ln -s /etc/nginx/sites-available/traveltrip /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
certbot --nginx -d traveltrip.world -d www.traveltrip.world
```

---

## 🔑 5. Accessing Admin & Customer Portals

- **Customer Dashboard**: `https://traveltrip.world/pages/account.html`
- **Checkout & Instant Delivery**: `https://traveltrip.world/pages/checkout.html`
- **Admin Control Center**: `https://traveltrip.world/pages/admin.html`
  - Default Login: `admin@traveltrip.world`
  - Default Password: `AdminSecure2026!` *(Change in DB or via admin profile)*
- **Live Server Health Ping**: `https://traveltrip.world/api/health/live`
