import os
import base64
import requests
from flask import Flask, jsonify, request
import logging
import sys

app = Flask(__name__)

# --- Configuration from .env ---
ADGUARD_URL = os.getenv("ADGUARD_URL")
USER_PASS = os.getenv("ADGUARD_USER_PASS")
LANGUAGE = os.getenv("LANGUAGE", "en").lower()
HOME_DASHBOARD_URL = os.getenv("HOME_DASHBOARD_URL") 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# --- Endpoint 1: Configuration for Frontend ---
@app.route('/config')
def get_config():
    """Returns language and dashboard configuration to the frontend."""
    return jsonify({
        "lang": LANGUAGE,
        "dashboard_url": HOME_DASHBOARD_URL
    })


# --- Endpoint 2: Fetch last block from AdGuard ---
@app.route('/last-block')
def get_last_block():
    """Queries the AdGuard API for the most recent filtered entry of the specific requester."""
    if not ADGUARD_URL or not USER_PASS:
        return jsonify({"error": "Configuration missing"}), 500

    # 1. Die IP des Gastes ermitteln (damit er nicht den Block von jemand anderem sieht)
    guest_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    guest_ip = guest_ip.split(',')[0].strip() # Falls mehrere IPs im Header sind
    
    # 2. Deine funktionierende Authentifizierung
    auth_header = {"Authorization": f"Basic {base64.b64encode(USER_PASS.encode()).decode()}"}
    
    # 3. Suche gezielt nach der IP des Gastes
    query_params = {
        "limit": 1, 
        "response_status": "filtered",
        "search": guest_ip  # Filtert das Log nach der IP des Besuchers
    }
    
    logging.info(f"Frage AdGuard nach letztem Block für IP: {guest_ip}")

    try:
        response = requests.get(ADGUARD_URL, headers=auth_header, params=query_params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('data') and len(data['data']) > 0:
            entry = data['data'][0]
            logging.info(f"✅ Block für {guest_ip} gefunden: {entry['question']['name']}")
            return jsonify({
                "domain": entry['question']['name'],
                "filter": entry.get('filter_id', 'System Default'),
                "reason": entry.get('reason', 'Blocked')
            })
    except Exception as e:
        # Falls response existiert, loggen wir Details, sonst nur den Fehler
        status = getattr(response, 'status_code', 'No Response')
        text = getattr(response, 'text', 'No Text')
        logging.error(f"❌ Fehler: Status Code {status}")
        logging.error(f"Antwort vom Server: {text}")
        logging.error(e)
        return jsonify({"error": "Failed to connect to AdGuard API"}), 500
        
    return jsonify({"domain": "No recent block found"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)