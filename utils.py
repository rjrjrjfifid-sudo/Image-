import requests
from user_agents import parse

def get_ip_info(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return data if data.get('status') == 'success' else {}
    except:
        return {}

def parse_user_agent(ua_string):
    ua = parse(ua_string)
    return {
        "device": ua.device.family or "Unknown",
        "os": f"{ua.os.family} {ua.os.version_string}" if ua.os.family else "Unknown",
        "browser": f"{ua.browser.family} {ua.browser.version_string}" if ua.browser.family else "Unknown"
    }
