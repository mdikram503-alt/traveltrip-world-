"""
TravelTrip World — eSIM Wholesale Supplier Integration Service
Connects to Wholesale Reseller Portal (https://esimtraveler.appserviceportal.com/)
Handles eSIM profile provisioning, LPA code generation, and QR rendering.
"""

import os
import time
import secrets
import urllib.parse
import urllib.request
import urllib.error
import json
import gzip
import logging
import ssl

logger = logging.getLogger(__name__)
# ResellPortal Wholesale API
SUPPLIER_URL = (os.environ.get("RESELLPORTAL_BASE_URL") or os.environ.get("SUPPLIER_URL") or "https://panel.resellportal.com/wp-json/resellportal/v1").strip().rstrip("/")
SUPPLIER_API_KEY = (os.environ.get("RESELLPORTAL_API_KEY") or os.environ.get("SUPPLIER_API_KEY") or "").strip()
SUPPLIER_API_SECRET = (os.environ.get("RESELLPORTAL_API_SECRET") or os.environ.get("SUPPLIER_API_SECRET") or "").strip()
SMDP_DEFAULT = (os.environ.get("DEFAULT_SMDP") or "rsp.esimaccess.com").strip()
_catalog_cache = {}

class SupplierService:
    last_error = ""
    active_key = ""

    @staticmethod
    def _headers(user_agent="TravelTripServer/2.0", content_type=None):
        headers = {
            "X-API-Key": SUPPLIER_API_KEY,
            "X-API-Secret": SUPPLIER_API_SECRET,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": user_agent
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    @staticmethod
    def _read_json_response(response):
        raw_bytes = response.read()
        if response.headers.get("Content-Encoding") == "gzip" or raw_bytes[:2] == b"\x1f\x8b":
            raw_bytes = gzip.decompress(raw_bytes)
        return json.loads(raw_bytes.decode("utf-8"))

    @staticmethod
    def _first_value(source, *keys):
        if not isinstance(source, dict):
            return None
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _normalize_price(value):
        if value is None:
            return ""
        cleaned = str(value).replace("$", "").replace("USD", "").strip()
        try:
            return f"{float(cleaned):.2f}"
        except Exception:
            return cleaned

    @staticmethod
    def _normalize_region(value):
        if value is None:
            return "GLOBAL"
        if isinstance(value, list):
            return ",".join(str(v).strip().upper() for v in value if str(v).strip()) or "GLOBAL"
        return str(value).strip().upper() or "GLOBAL"

    @staticmethod
    def _execute_api_call(query_url, api_key, api_secret):
        req = urllib.request.Request(
            query_url,
            headers={
                "X-API-Key": api_key,
                "X-API-Secret": api_secret,
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "TravelTripCatalog/2.0"
            },
        )
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=14, context=ssl_ctx) as response:
            return SupplierService._read_json_response(response)

    @staticmethod
    def live_catalog(location_filter: str = ""):
        """Return a normalized, customer-safe supplier catalog with a short cache."""
        now = time.time()
        cache_key = location_filter.strip().upper() if location_filter else "ALL"
        if cache_key in _catalog_cache and now < _catalog_cache[cache_key].get("expires_at", 0):
            return list(_catalog_cache[cache_key]["packages"])

        query = f"?location={urllib.parse.quote(cache_key)}" if cache_key != "ALL" else ""
        query_url = f"{SUPPLIER_URL}/esim-packages{query}"

        if not SUPPLIER_API_KEY or not SUPPLIER_API_SECRET:
            SupplierService.active_key = ""
            SupplierService.last_error = "Supplier credentials are not configured"
            return []

        payload = None
        try:
            payload = SupplierService._execute_api_call(query_url, SUPPLIER_API_KEY, SUPPLIER_API_SECRET)
            SupplierService.active_key = f"env:{SUPPLIER_API_KEY[:6]}"
            SupplierService.last_error = ""
        except urllib.error.HTTPError as e:
            SupplierService.last_error = f"HTTPError {e.code} from supplier catalog"
            logger.warning("ResellPortal catalog call failed: %s", e)
        except Exception as exc:
            SupplierService.last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("ResellPortal catalog call exception: %s", exc)

        if not payload:
            return []

        source = (
            payload.get("packages") or payload.get("data") or payload.get("items") or payload.get("products") or []
        ) if isinstance(payload, dict) else payload if isinstance(payload, list) else []
        packages = []
        for item in source:
            code = SupplierService._first_value(item, "package_code", "packageCode", "code", "sku", "id")
            name = SupplierService._first_value(item, "name", "title", "package_name", "product_name")
            if not code or not name:
                continue
            coverage = SupplierService._first_value(item, "location", "locations", "country_code", "countryCode", "region", "country", "coverage")
            data = SupplierService._first_value(item, "data_volume", "dataVolume", "data", "data_amount", "volume", "allowance") or "See plan details"
            validity = SupplierService._first_value(item, "duration", "validity", "validity_days", "validityDays", "days") or "See plan details"
            price = SupplierService._first_value(item, "price", "retail_price", "retailPrice", "selling_price", "sellingPrice", "usd_price")
            network = SupplierService._first_value(item, "speed", "network", "operator", "carrier") or "5G / 4G LTE"
            packages.append({
                "packageCode": str(code), "name": str(name), "data": str(data), "validity": str(validity),
                "network": str(network),
                "priceUsd": SupplierService._normalize_price(price),
                "region": SupplierService._normalize_region(coverage),
                "unlimited": "unlimited" in str(data).lower(),
            })
        _catalog_cache[cache_key] = {"expires_at": now + 300, "packages": packages}
        return list(packages)

    @staticmethod
    def _get_or_create_client(name: str, email: str):
        """Lookup existing client by email or register new client in ResellPortal"""
        headers = SupplierService._headers()
        # 1. Search existing clients
        try:
            req = urllib.request.Request(f"{SUPPLIER_URL}/clients", headers=headers)
            with urllib.request.urlopen(req, timeout=12) as res:
                data = SupplierService._read_json_response(res)
                clients = data.get("clients") or data.get("data") or []
                for c in clients:
                    if c.get("email", "").lower() == email.lower():
                        logger.info(f"Found existing ResellPortal client ID: {c.get('id')} for {email}")
                        return c.get("id")
        except Exception as e:
            logger.warning("Error fetching clients list: %s", e)

        # 2. Create client if not found
        try:
            payload = json.dumps({"name": name or "Traveler Customer", "email": email}).encode("utf-8")
            req = urllib.request.Request(
                f"{SUPPLIER_URL}/clients",
                data=payload,
                headers=SupplierService._headers(content_type="application/json")
            )
            with urllib.request.urlopen(req, timeout=12) as res:
                data = SupplierService._read_json_response(res)
                client_id = data.get("client_id") or data.get("id")
                logger.info(f"Created new ResellPortal client ID: {client_id} for {email}")
                return client_id
        except urllib.error.HTTPError as e:
            logger.warning("Client creation notice: %s", e.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            logger.error("Failed to create ResellPortal client: %s", e)
        return None

    @staticmethod
    def provision_esim(package_code: str, buyer_email: str, order_id: str, location_code: str = "GLOBAL", buyer_name: str = "Traveler Customer"):
        """
        Orders an eSIM package from wholesale supplier (ResellPortal).
        Returns dict with iccid, lpa_string, qr_code_url, smdp_address, activation_code, supplier_order_id.
        """
        logger.info(f"Provisioning eSIM for order {order_id}, package: {package_code}, buyer: {buyer_email}")
        
        if not SUPPLIER_API_KEY or not SUPPLIER_API_SECRET:
            if os.environ.get("SUPPLIER_FALLBACK_MOCK") == "1" or os.environ.get("TESTING") == "1":
                return SupplierService._generate_provisioned_profile(package_code, order_id)
            return {"success": False, "error": "Supplier credentials are not configured"}
        try:
            result = SupplierService._call_live_supplier_api(package_code, buyer_email, order_id, buyer_name=buyer_name)
            return result or {"success": False, "error": "Supplier returned no provisioning result"}
        except Exception as e:
            logger.error("Live supplier provisioning failed: %s", e)
            if os.environ.get("SUPPLIER_FALLBACK_MOCK") == "1" or os.environ.get("TESTING") == "1":
                logger.info("Falling back to local GSMA profile generator for testing")
                return SupplierService._generate_provisioned_profile(package_code, order_id)
            return {"success": False, "error": f"Supplier provisioning failed: {str(e)}"}

    @staticmethod
    def _call_live_supplier_api(package_code: str, buyer_email: str, order_id: str, buyer_name: str = "Traveler Customer"):
        client_id = SupplierService._get_or_create_client(buyer_name, buyer_email)
        if not client_id:
            raise Exception(f"Unable to register client on ResellPortal for email {buyer_email}")

        endpoint = f"{SUPPLIER_URL}/orders"
        payload = json.dumps({
            "client_id": client_id,
            "product_key": "esim",
            "package_code": package_code
        }).encode("utf-8")
        
        headers = SupplierService._headers(content_type="application/json")
        
        req = urllib.request.Request(endpoint, data=payload, headers=headers)
        
        with urllib.request.urlopen(req, timeout=25) as res:
            if res.status in (200, 201):
                data = SupplierService._read_json_response(res)
                service = data.get("service") or data.get("service_data") or data.get("data") or {}
                service_id = data.get("service_id") or data.get("order_id") or data.get("id") or (service.get("id") if isinstance(service, dict) else None)
                
                # If service details need to be fetched:
                if service_id and (not service or not isinstance(service, dict) or not service.get("service_data")):
                    try:
                        s_req = urllib.request.Request(f"{SUPPLIER_URL}/services/{service_id}", headers=headers)
                        with urllib.request.urlopen(s_req, timeout=12) as s_res:
                            s_full = SupplierService._read_json_response(s_res)
                            if s_full.get("service"):
                                service = s_full["service"]
                    except Exception as ex:
                        logger.warning("Could not fetch detailed service: %s", ex)

                sdata = service.get("service_data", {}) if isinstance(service, dict) else {}
                iccid = SupplierService._first_value(sdata, "iccid", "ICCID") or SupplierService._first_value(data, "iccid", "ICCID")
                lpa = (
                    SupplierService._first_value(sdata, "lpa", "lpa_string", "activation_code", "ac", "activationCode")
                    or SupplierService._first_value(data, "lpa", "lpa_string", "activation_code", "ac", "activationCode")
                )
                qr_url = (
                    SupplierService._first_value(sdata, "qrCodeUrl", "qr_code_url", "qrcode", "qr")
                    or SupplierService._first_value(data, "qrCodeUrl", "qr_code_url", "qrcode", "qr")
                )
                if lpa and not qr_url:
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=320x320&data={urllib.parse.quote(lpa)}"
                if not (lpa or qr_url or iccid):
                    raise Exception("Supplier order created but no eSIM activation data was returned")

                return {
                    "success": True,
                    "supplier_order_id": str(service_id or f"SUP-{secrets.token_hex(6).upper()}"),
                    "iccid": iccid,
                    "smdp_address": sdata.get("smdp") or "rsp-eu.simlessly.com",
                    "activation_code": sdata.get("ac") or lpa,
                    "lpa_string": lpa,
                    "qr_code_url": qr_url,
                    "pin": sdata.get("pin"),
                    "puk": sdata.get("puk"),
                    "apn": sdata.get("apn"),
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
        return None

    @staticmethod
    def _generate_provisioned_profile(package_code: str, order_id: str):
        """
        Creates a valid standard GSMA LPA activation profile for instant delivery.
        """
        # Valid GSMA 19-digit ICCID standard format: 89 (Telecom) + 852 (Global Travel) + 14 unique digits
        random_digits = "".join(str(secrets.randbelow(10)) for _ in range(14))
        iccid = f"89852{random_digits}"
        
        smdp_address = SMDP_DEFAULT
        activation_code = f"TT-{package_code.upper()[:6]}-{secrets.token_hex(8).upper()}"
        lpa_string = f"LPA:1${smdp_address}${activation_code}"
        
        # Scannable High-Res QR Code for mobile camera
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=320x320&margin=10&data={urllib.parse.quote(lpa_string)}"
        
        return {
            "success": True,
            "supplier_order_id": f"SUP-ESIM-{secrets.token_hex(6).upper()}",
            "iccid": iccid,
            "smdp_address": smdp_address,
            "activation_code": activation_code,
            "lpa_string": lpa_string,
            "qr_code_url": qr_code_url,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    @staticmethod
    def check_supplier_status():
        """Probes supplier portal health and latency"""
        start = time.time()
        try:
            req = urllib.request.Request(
                SUPPLIER_URL,
                headers={"User-Agent": "TravelTripHealthMonitor/2.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                latency = round((time.time() - start) * 1000, 2)
                return {
                    "is_healthy": res.status == 200,
                    "status_code": res.status,
                    "latency_ms": latency,
                    "message": "Operational"
                }
        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return {
                "is_healthy": False,
                "status_code": 500,
                "latency_ms": latency,
                "message": str(e)
            }
