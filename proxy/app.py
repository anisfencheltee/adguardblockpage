import os
import requests
import smtplib
from email.mime.text import MIMEText
from flask import Flask, jsonify, request

app = Flask(__name__)

# --- NOTIFICATION DISPATCHER ---
def notify_admin(domain):
    subject = f"Veto-Anfrage: {domain}"
    message = f"Der Pixar-Butler meldet: Die Domain '{domain}' wurde als Fehlalarm gemeldet."
    sent_any = False

    # 1. E-MAIL
    if os.getenv("SMTP_SERVER") and os.getenv("SMTP_USER"):
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = os.getenv("SMTP_USER")
            msg['To'] = os.getenv("EMAIL_TO")
            with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", 587))) as server:
                server.starttls()
                server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
                server.send_message(msg)
            sent_any = True
        except Exception as e: print(f"Email Error: {e}")

    # 2. TELEGRAM
    if os.getenv("TELEGRAM_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        try:
            token = os.getenv("TELEGRAM_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": f"🚨 *{subject}*\n\n{message}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
            sent_any = True
        except Exception as e: print(f"Telegram Error: {e}")

    # 3. GOTIFY
    if os.getenv("GOTIFY_URL") and os.getenv("GOTIFY_TOKEN"):
        try:
            url = os.getenv("GOTIFY_URL") + "/message"
            token = os.getenv("GOTIFY_TOKEN")
            requests.post(url, headers={"X-Gotify-Key": token}, json={
                "title": subject,
                "message": message,
                "priority": 5
            }, timeout=5)
            sent_any = True
        except Exception as e: print(f"Gotify Error: {e}")

    return sent_any

@app.route('/whitelist', methods=['POST'])
def send_veto():
    data = request.json
    domain = data.get('domain', 'Unbekannt')
    
    if notify_admin(domain):
        return jsonify({"status": "Erfolgreich versendet"}), 200
    else:
        return jsonify({"error": "Keine Versandwege konfiguriert oder Fehler aufgetreten"}), 500