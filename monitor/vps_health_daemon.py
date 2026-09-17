"""
TravelTrip World — 24/7 VPS Server Health Monitoring Daemon
Runs continuously in the background on the Server / VPS (NOT inside the APK).
Continuously probes web endpoints, APIs, wholesale supplier portal, and database.
Saves telemetry into database for Admin Panel live monitoring and alerts.
"""

import os
import sys
import time
import urllib.request
import sqlite3
import datetime
import logging

# Ensure parent directory is in sys.path to import database
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

from database import log_health_check

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [VPS-DAEMON] %(message)s"
)
logger = logging.getLogger("HealthDaemon")

CHECK_INTERVAL_SECONDS = int(os.environ.get("MONITOR_INTERVAL", 60))
SERVER_PORT = os.environ.get("PORT", "8000")

# Targets to monitor 24/7
TARGETS = [
    {
        "name": "TravelTrip Web Frontend",
        "url": os.environ.get("SITE_URL", f"http://127.0.0.1:{SERVER_PORT}/"),
        "timeout": 10
    },
    {
        "name": "Catalog eSIM Packages API",
        "url": os.environ.get("CATALOG_URL", f"http://127.0.0.1:{SERVER_PORT}/catalog/esim/packages?location=EU"),
        "timeout": 10
    },
    {
        "name": "Wholesale Reseller Portal",
        "url": os.environ.get("SUPPLIER_URL", "https://panel.resellportal.com/"),
        "timeout": 12
    }
]

def check_target(target):
    name = target["name"]
    url = target["url"]
    timeout = target["timeout"]
    
    start = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TravelTrip-24-7-Daemon/2.0 (VPS Health Monitor)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            latency_ms = round((time.time() - start) * 1000, 2)
            code = res.status
            is_healthy = 200 <= code < 400
            status_text = f"HTTP {code} OK" if is_healthy else f"HTTP {code}"
            
            log_health_check(
                service_name=name,
                url=url,
                status=status_text,
                latency_ms=latency_ms,
                is_healthy=is_healthy,
                error_details=None
            )
            logger.info(f"HEALTHY: {name} ({status_text}) - Latency: {latency_ms}ms")
            return is_healthy
    except Exception as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        err_msg = str(e)
        log_health_check(
            service_name=name,
            url=url,
            status="DOWN / ERROR",
            latency_ms=latency_ms,
            is_healthy=False,
            error_details=err_msg
        )
        logger.error(f"ALERT DOWN: {name} ({err_msg}) - Latency: {latency_ms}ms")
        return False

def run_daemon_loop():
    logger.info("=======================================================")
    logger.info(" TravelTrip 24/7 VPS Health Monitoring Daemon Starting ")
    logger.info(f" Interval: every {CHECK_INTERVAL_SECONDS} seconds")
    logger.info(f" Monitoring {len(TARGETS)} vital endpoints")
    logger.info("=======================================================")
    
    while True:
        try:
            for target in TARGETS:
                check_target(target)
        except Exception as ex:
            logger.error(f"Unexpected monitor loop error: {ex}")
            
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    # If run once with --once flag, do single pass (useful for tests)
    if "--once" in sys.argv:
        for t in TARGETS:
            check_target(t)
    else:
        run_daemon_loop()
