import os
import requests
from user_agents import parse

# ---------- ipinfo.io (free with token) ----------
def get_ip_info(ip):
    """
    Query ipinfo.io to get geolocation, ISP, and organisation.
    Requires IPINFO_TOKEN set as environment variable.
    Returns a dict with: ip, city, region, country, loc (lat,lon), org, etc.
    """
    token = os.getenv("IPINFO_TOKEN")
    if not token:
        return {}
    try:
        url = f"https://ipinfo.io/{ip}?token={token}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # extract lat/lon from 'loc' field
            loc = data.get('loc', '').split(',')
            lat = loc[0] if len(loc) > 0 else None
            lon = loc[1] if len(loc) > 1 else None
            return {
                "city": data.get("city", ""),
                "region": data.get("region", ""),
                "country": data.get("country", ""),
                "org": data.get("org", ""),          # often includes VPN provider name
                "lat": lat,
                "lon": lon,
            }
    except:
        pass
    return {}

# ---------- Reverse geocoding (street) via OpenStreetMap Nominatim ----------
def reverse_geocode(lat, lon):
    """Convert coordinates to a street address (free, no token)."""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 18,
        "addressdetails": 1
    }
    headers = {"User-Agent": "TicTacToeLogger/1.0"}   # required by Nominatim
    resp = requests.get(url, params=params, headers=headers, timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        address = data.get("address", {})
        # try common street fields
        street = address.get("road") or address.get("pedestrian") or address.get("street") or address.get("footway") or "Unknown"
        return street
    return "Unknown"

# ---------- User‑Agent parsing ----------
def parse_user_agent(ua_string):
    ua = parse(ua_string)
    return {
        "device": ua.device.family or "Unknown",
        "os": f"{ua.os.family} {ua.os.version_string}" if ua.os.family else "Unknown",
        "browser": f"{ua.browser.family} {ua.browser.version_string}" if ua.browser.family else "Unknown"
    }

# ---------- VPN detection ----------
def detect_vpn(org):
    """
    Try to identify if the organisation is a known VPN provider.
    If yes, return the provider name; otherwise return the org string (or "Unknown").
    """
    if not org:
        return "Unknown"
    # Normalise for case‑insensitive matching
    org_lower = org.lower()
    # List of common VPN names (you can expand this)
    vpn_keywords = {
        "nordvpn": "NordVPN",
        "nord security": "NordVPN",
        "protonvpn": "ProtonVPN",
        "proton vpn": "ProtonVPN",
        "mullvad": "Mullvad",
        "expressvpn": "ExpressVPN",
        "cyberghost": "CyberGhost",
        "surfshark": "Surfshark",
        "windscribe": "Windscribe",
        "vyprvpn": "VyprVPN",
        "ipvanish": "IPVanish",
        "purevpn": "PureVPN",
        "zenmate": "ZenMate",
        "hotspot shield": "Hotspot Shield",
        "private internet access": "Private Internet Access",
        "pia": "PIA",
        "torguard": "TorGuard",
        "hide.me": "hide.me",
        "ivpn": "IVPN",
        "airvpn": "AirVPN",
        "perfect privacy": "Perfect Privacy",
        "azirevpn": "AzireVPN",
        "oceanvpn": "OceanVPN",
        "fastestvpn": "FastestVPN",
        "buffered": "Buffered",
        "safervpn": "SaferVPN",
        "vpn unlimited": "VPN Unlimited",
        "keepsolid": "KeepSolid",
        "vpn.ac": "VPN.ac",
        "cactusvpn": "CactusVPN",
        "earthvpn": "EarthVPN",
        "bolehvpn": "BolehVPN",
        "cryptostorm": "Cryptostorm",
        "blackvpn": "BlackVPN",
        "vpn.ht": "VPN.ht",
        "mullvad": "Mullvad"  # already included
    }
    for key, name in vpn_keywords.items():
        if key in org_lower:
            return name
    # If not found in the list, return the original organisation name (might be ISP name)
    return org
