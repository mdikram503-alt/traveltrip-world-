import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supplier_service import SupplierService

def match_package(country_name, data_str="", validity_str=""):
    pkgs = SupplierService.live_catalog()
    c_lower = country_name.lower().strip()
    
    # 1. Exact packageCode match
    for p in pkgs:
        if p['packageCode'].upper() == country_name.upper():
            return p
            
    # 2. Country/Region match
    candidates = []
    for p in pkgs:
        p_name = p['name'].lower()
        p_reg = p.get('region', '').lower()
        if c_lower in p_name or c_lower == p_reg:
            candidates.append(p)
            
    if not candidates:
        # Check alias
        aliases = {"uae": "united arab emirates", "uk": "united kingdom", "usa": "united states"}
        if c_lower in aliases:
            alt = aliases[c_lower]
            candidates = [p for p in pkgs if alt in p['name'].lower()]

    if not candidates:
        return None

    # Filter by data if provided (e.g. '1gb', '3gb', '5gb')
    if data_str:
        d_clean = data_str.lower().replace(" ", "")
        data_filtered = [p for p in candidates if d_clean in p['data'].lower().replace(" ", "")]
        if data_filtered:
            candidates = data_filtered

    # Sort by lowest price
    candidates.sort(key=lambda x: float(x.get('priceUsd', 999) or 999))
    return candidates[0]

# Test matching
for country in ["Bangladesh", "Spain", "Japan", "United States", "UAE"]:
    res = match_package(country, "1GB")
    print(f"Matched {country} 1GB -> {res['packageCode']} ({res['name']}) - ${res['priceUsd']}")
