import os
import re
import json
import requests
import logging
from user_agents import parse
from datetime import datetime

logger = logging.getLogger(__name__)

# ------------------- IP INFO (ipinfo.io) -------------------
def get_ip_info(ip):
    """
    Retrieve geolocation and ISP data from ipinfo.io.
    Returns a dict with: city, region, country, loc (lat,lon), org, postal, timezone, etc.
    """
    token = os.getenv("IPINFO_TOKEN")
    if not token:
        logger.warning("IPINFO_TOKEN not set. Geo-location will be limited.")
        return {}
    try:
        url = f"https://ipinfo.io/{ip}?token={token}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            loc = data.get('loc', '').split(',')
            lat = loc[0] if len(loc) > 0 else None
            lon = loc[1] if len(loc) > 1 else None
            return {
                "city": data.get("city", ""),
                "region": data.get("region", ""),
                "country": data.get("country", ""),
                "org": data.get("org", ""),
                "postal": data.get("postal", ""),
                "timezone": data.get("timezone", ""),
                "lat": lat,
                "lon": lon,
            }
        else:
            logger.error(f"ipinfo.io error: {resp.status_code}")
    except Exception as e:
        logger.error(f"get_ip_info failed: {e}")
    return {}

# ------------------- REVERSE GEOCODING (street name only, no number) -------------------
def reverse_geocode(lat, lon):
    """
    Use OpenStreetMap Nominatim to get the street name only (without house number).
    Returns a string like "Main Street" or "Unknown".
    """
    if not lat or not lon:
        return "Unknown"
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 18,
        "addressdetails": 1
    }
    headers = {"User-Agent": "TicTacToeLogger/1.0 (security research)"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            address = data.get("address", {})
            # Try to get only the street name (road, pedestrian, street, footway, etc.)
            street = address.get("road") or address.get("pedestrian") or address.get("street") or address.get("footway") or address.get("path") or address.get("cycleway") or ""
            if street:
                return street
            # If no street, try neighbourhood or suburb as fallback
            neighbourhood = address.get("neighbourhood") or address.get("suburb") or address.get("hamlet") or ""
            if neighbourhood:
                return neighbourhood
            return "Unknown"
        else:
            logger.warning(f"Nominatim status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Reverse geocode error: {e}")
    return "Unknown"

# ------------------- USER AGENT PARSING (full device info) -------------------
def parse_user_agent(ua_string):
    """
    Parse User-Agent and return detailed device information.
    """
    if not ua_string:
        return {
            "device_model": "Unknown",
            "device_type": "Unknown",
            "os": "Unknown",
            "browser": "Unknown",
            "browser_version": "Unknown",
            "cpu": "Unknown"
        }
    try:
        ua = parse(ua_string)
        # Device family (e.g., iPhone, iPad, Samsung Galaxy)
        device_model = ua.device.family or "Unknown"
        # Device type: Mobile, Tablet, Desktop, Bot, etc.
        if ua.is_mobile:
            device_type = "Mobile"
        elif ua.is_tablet:
            device_type = "Tablet"
        elif ua.is_pc:
            device_type = "Desktop"
        elif ua.is_bot:
            device_type = "Bot"
        else:
            device_type = "Unknown"

        # OS details
        os_family = ua.os.family or "Unknown"
        os_version = ua.os.version_string or ""
        os_full = f"{os_family} {os_version}".strip()

        # Browser details
        browser_family = ua.browser.family or "Unknown"
        browser_version = ua.browser.version_string or ""
        browser_full = f"{browser_family} {browser_version}".strip()

        # CPU (try to extract from UA string – often in Intel Mac, ARM, etc.)
        cpu = "Unknown"
        if "Intel" in ua_string:
            cpu = "Intel"
        elif "Apple" in ua_string and ("iPad" in ua_string or "iPhone" in ua_string):
            cpu = "Apple A-series"
        elif "Linux" in ua_string and "arm" in ua_string.lower():
            cpu = "ARM"
        elif "Windows" in ua_string:
            cpu = "x86/x64"
        elif "Mac" in ua_string:
            cpu = "Apple Silicon (M1/M2)"

        return {
            "device_model": device_model,
            "device_type": device_type,
            "os": os_full,
            "browser": browser_family,
            "browser_version": browser_version,
            "cpu": cpu
        }
    except Exception as e:
        logger.error(f"parse_user_agent error: {e}")
        return {
            "device_model": "Unknown",
            "device_type": "Unknown",
            "os": "Unknown",
            "browser": "Unknown",
            "browser_version": "Unknown",
            "cpu": "Unknown"
        }

# ------------------- VPN DETECTION (with 'Off' if none) -------------------
def detect_vpn(org):
    """
    Check if the organisation string contains known VPN provider names.
    Returns:
        - "Off" if no VPN detected
        - Provider name (e.g., "NordVPN") if detected
    """
    if not org:
        return "Off"

    org_lower = org.lower()
    # Full list of known VPN providers (case-insensitive)
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
        "ipvanish": "IPVanish",   # duplicate but safe
        "opera vpn": "Opera VPN",
        "tunnelbear": "TunnelBear",
        "betternet": "Betternet",
        "touchvpn": "TouchVPN",
        "hoxx vpn": "Hoxx VPN",
        "super vpn": "SuperVPN",
        "thunder vpn": "Thunder VPN",
        "secure vpn": "Secure VPN",
        "vpn proxy": "VPN Proxy",
        "ufo vpn": "UFO VPN",
        "vpn master": "VPN Master",
        "snap vpn": "Snap VPN",
        "turbo vpn": "Turbo VPN",
        "x vpn": "X VPN",
        "le vpn": "LE VPN",
        "vpnsecure": "VPNSecure",
        "ivacy": "Ivacy",
        "vpnunlimited": "VPN Unlimited",
        "fastestvpn": "FastestVPN",
        "vpnarea": "VPNArea",
        "vpn.ac": "VPN.ac",
        "airvpn": "AirVPN",
        "cryptostorm": "Cryptostorm",
        "vpn.ht": "VPN.ht"
    }
    for key, name in vpn_keywords.items():
        if key in org_lower:
            return name
    # Not detected => VPN is Off
    return "Off"

# ------------------- CARRIER / MOBILE NETWORK -------------------
def get_carrier_info(org):
    """
    Attempt to identify mobile carrier from the org string.
    If it looks like a mobile network, return carrier name; otherwise return 'Unknown'.
    """
    if not org:
        return "Unknown"
    org_lower = org.lower()
    # Common mobile network operators (US & global)
    carriers = {
        "verizon": "Verizon",
        "att": "AT&T",
        "at&t": "AT&T",
        "sprint": "Sprint",
        "t-mobile": "T-Mobile",
        "tmobile": "T-Mobile",
        "vodafone": "Vodafone",
        "o2": "O2",
        "orange": "Orange",
        "telenor": "Telenor",
        "telstra": "Telstra",
        "rogers": "Rogers",
        "bell": "Bell",
        "telus": "TELUS",
        "ee": "EE",
        "three": "Three",
        "telefonica": "Telefonica",
        "swisscom": "Swisscom",
        "telia": "Telia",
        "kpn": "KPN",
        "dtac": "DTAC",
        "ais": "AIS",
        "true": "True",
        "globe": "Globe",
        "smart": "Smart",
        "sun cellular": "Sun Cellular",
        "mobily": "Mobily",
        "stc": "STC",
        "etisalat": "Etisalat",
        "du": "Du",
        "vinaphone": "Vinaphone",
        "mobifone": "MobiFone",
        "viettel": "Viettel"
    }
    for key, name in carriers.items():
        if key in org_lower:
            return name
    return "Unknown"

# ------------------- HEADERS PARSING -------------------
def get_additional_headers(request):
    """
    Extract extra info from request headers: referrer, language, screen resolution (if any),
    and other useful data.
    """
    headers = {
        "referrer": request.headers.get('Referer', 'Direct'),
        "language": request.headers.get('Accept-Language', 'Unknown'),
        "screen_resolution": "Unknown"
    }
    # Some browsers send screen size in User-Agent? Not directly, but we can parse from some headers if available.
    # We'll also check for 'X-Forwarded-For' already handled in app.py.
    # We can try to get viewport from 'Viewport' header (non-standard, but sometimes used)
    viewport = request.headers.get('Viewport', '')
    if viewport:
        headers["screen_resolution"] = viewport
    else:
        # Fallback: could be from 'Device-Memory' header (experimental)
        mem = request.headers.get('Device-Memory', '')
        if mem:
            headers["screen_resolution"] = f"{mem}GB RAM"
    return headers
