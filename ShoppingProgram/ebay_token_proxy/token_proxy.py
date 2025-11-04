from flask import Flask, jsonify
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_USE_SANDBOX = os.getenv("EBAY_USE_SANDBOX", "false").lower() in ("1", "true", "yes")
IDENTITY_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if EBAY_USE_SANDBOX else "https://api.ebay.com/identity/v1/oauth/api_scope"

@app.route("/get-ebay-token")
def get_ebay_token():
    creds = base64.b64encode(f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
    
    resp = requests.post(IDENTITY_URL, headers=headers, data=data)
    if resp.status_code != 200:
        return jsonify({"error": resp.text}), 500
    token = resp.json().get("access_token")
    return jsonify({"access_token": token})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
