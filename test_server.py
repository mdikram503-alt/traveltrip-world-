"""
Automated Test Suite for TravelTrip Server & eSIM Workflow
Tests:
1. Database initialization and user registration/login.
2. Order creation and server-side payment verification.
3. Automated Wholesale eSIM provisioning & QR code generation.
4. Customer account order fetching.
5. Admin stats & order listing.
6. 24/7 VPS Health Daemon single pass check.
"""

import os
import sys
import unittest

import os
import sys
import unittest

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from database import (
    init_db, create_user, authenticate_user, create_order,
    get_order, update_order_payment, update_order_esim,
    get_user_orders, get_dashboard_stats, get_recent_health_metrics
)
from supplier_service import SupplierService
from monitor.vps_health_daemon import check_target

class TestTravelTripWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_user_authentication(self):
        email = "testcustomer@example.com"
        # Register
        user_id = create_user("Test Customer", email, "Secret123!", role="customer")
        self.assertTrue(user_id is not None or authenticate_user(email, "Secret123!") is not None)
        
        # Authenticate
        auth = authenticate_user(email, "Secret123!")
        self.assertIsNotNone(auth)
        self.assertEqual(auth["email"], email)
        self.assertEqual(auth["role"], "customer")
        print("[PASS] [TEST] User Registration & Auth Verified")

    def test_02_order_and_automated_esim_provisioning(self):
        # 1. Create Pending Order
        order_id = create_order(
            buyer_name="Rahim Khan",
            buyer_email="rahim@example.com",
            package_code="EU-1GB-7D",
            package_name="Europe 1GB (7 Days)",
            data_amount="1 GB",
            validity="7 Days",
            price_usd=4.50,
            location_code="EU"
        )
        self.assertTrue(order_id.startswith("TT-"))
        order = get_order(order_id)
        self.assertEqual(order["payment_status"], "pending")
        self.assertEqual(order["esim_status"], "pending")

        # 2. Server-side payment verification
        update_order_payment(order_id, "paid", "TX-PAYPAL-998822")
        
        # 3. Wholesale Supplier automated provisioning
        provision = SupplierService.provision_esim(
            package_code=order["package_code"],
            buyer_email=order["buyer_email"],
            order_id=order_id,
            location_code=order["location_code"]
        )
        self.assertTrue(provision["success"])
        self.assertTrue(provision["iccid"].startswith("89"))
        self.assertTrue(provision["lpa_string"].startswith("LPA:1$"))
        self.assertTrue(provision["qr_code_url"].startswith("https://api.qrserver.com"))

        # 4. Mark eSIM delivered
        update_order_esim(
            order_id=order_id,
            esim_status="delivered",
            supplier_order_id=provision["supplier_order_id"],
            qr_code_data=provision["qr_code_url"],
            lpa_string=provision["lpa_string"],
            iccid=provision["iccid"],
            activation_code=provision["activation_code"],
            smdp_address=provision["smdp_address"]
        )

        updated = get_order(order_id)
        self.assertEqual(updated["payment_status"], "paid")
        self.assertEqual(updated["esim_status"], "delivered")
        self.assertIsNotNone(updated["qr_code_data"])
        print(f"[PASS] [TEST] Payment Verified & eSIM Delivered: {order_id}")
        print(f"   ICCID: {updated['iccid']} | LPA: {updated['lpa_string'][:35]}...")

    def test_03_customer_portal_orders(self):
        orders = get_user_orders(email="rahim@example.com")
        self.assertGreaterEqual(len(orders), 1)
        self.assertEqual(orders[0]["esim_status"], "delivered")
        print(f"[PASS] [TEST] Customer Portal Orders retrieved: {len(orders)} order(s)")

    def test_04_admin_dashboard_stats(self):
        stats = get_dashboard_stats()
        self.assertGreaterEqual(stats["total_orders"], 1)
        self.assertGreaterEqual(stats["paid_orders"], 1)
        self.assertGreaterEqual(stats["delivered_esims"], 1)
        self.assertGreater(stats["total_revenue_usd"], 0)
        print(f"[PASS] [TEST] Admin Stats Verified: Revenue=${stats['total_revenue_usd']}, Delivered={stats['delivered_esims']}")

    def test_05_vps_health_monitoring_daemon(self):
        # Test probe against wholesaler portal
        target = {
            "name": "Wholesale Reseller Portal",
            "url": "https://esimtraveler.appserviceportal.com/",
            "timeout": 12
        }
        res = check_target(target)
        metrics = get_recent_health_metrics(limit=5)
        self.assertGreaterEqual(len(metrics), 1)
        print(f"[PASS] [TEST] 24/7 Health Daemon Check: {metrics[0]['service_name']} -> {metrics[0]['status']} ({metrics[0]['latency_ms']}ms)")

if __name__ == "__main__":
    unittest.main()
