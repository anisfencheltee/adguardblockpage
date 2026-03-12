from flask import Flask, jsonify
import requests
import base64
import os

app = Flask(__name__)

# Holt die Daten sicher aus den Umgebungsvariablen des Containers
ADGUARD_URL = os.getenv("ADGUARD_URL")
USER_PASS = os.getenv("ADGUARD_USER_PASS")

@app.route('/last-block')
def get_block():
    if not ADGUARD_URL or not USER_PASS:
        return jsonify({"error": "Konfiguration fehlt (env vars)"}), 500

    headers = {
        "Authorization": f"Basic {base64.b64encode(USER_PASS.encode()).decode()}"
    }
    # Wir holen nur den allerletzten, tatsächlich gefilterten Eintrag
    params = {"limit": 1, "response_status": "filtered"}
    
    try:
        r = requests.get(ADGUARD_URL, headers=headers, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        if data.get('data') and len(data['data']) > 0:
            entry = data['data'][0]
            # Wir extrahieren nur die relevanten, harmlosen Infos
            return jsonify({
                "domain": entry['question']['name'],
                "filter": entry.get('filter_id', 'Manuelle Sperre'),
                "rule": entry.get('rule', 'Systemregel')
            })
    except Exception as e:
        # Sicherheitshalber geben wir keine Details über den Fehler nach außen
        return jsonify({"error": "AdGuard API nicht erreichbar"}), 500
    
    return jsonify({"domain": "Keine aktuelle Sperre gefunden"})

if __name__ == '__main__':
    # WICHTIG: Port 5000, damit es mit NPM harmoniert
    app.run(host='0.0.0.0', port=5000)