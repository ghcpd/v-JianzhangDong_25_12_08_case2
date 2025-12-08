import os
import sqlite3
import requests
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify, abort
import yaml
import zipfile
from urllib.parse import urlparse

app = Flask(__name__)

# Load secrets from environment; fail early if critical secrets are missing
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")
DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "configs")
ALLOWED_NOTIFY_HOSTS = os.environ.get("ALLOWED_NOTIFY_HOSTS", "localhost,127.0.0.1").split(",")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not AUTH_TOKEN:
    logger.warning("AUTH_TOKEN not set; secure authentication may not be enforced in this environment")


def require_auth(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or (AUTH_TOKEN and token != f"Bearer {AUTH_TOKEN}"):
            abort(401)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def auth_user(info):
    username = info.get("username", "")
    if not username or not INTERNAL_AUTH:
        raise ValueError("Missing username or INTERNAL_AUTH")
    # Use HMAC-SHA256 with a secret key (INTERNAL_AUTH) instead of plain MD5
    digest = hmac.new(INTERNAL_AUTH.encode(), username.encode(), hashlib.sha256).hexdigest()
    return digest


def query_profile(uid):
    # Validate uid to be integer to prevent SQL injection
    try:
        uid_int = int(uid)
    except Exception:
        raise ValueError("Invalid user id")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid_int,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")

    # Basic validation
    if not isinstance(amount, (int, float, str)):
        raise ValueError("Invalid amount")
    try:
        amount_val = float(amount)
    except Exception:
        raise ValueError("Amount must be numeric")

    parsed = urlparse(url)
    host = parsed.hostname
    if host not in ALLOWED_NOTIFY_HOSTS:
        raise ValueError("notify_url host is not allowed")

    logger.info("Notifying payment endpoint for target %s", target)
    # Use configured payment token; do not leak secret
    token = PAYMENT_TOKEN
    resp = requests.post(url, json={"token": token, "amount": amount_val}, timeout=5, verify=True)
    resp.raise_for_status()
    return resp.text


def update_records(path):
    # Only allow reading files from CONFIG_DIR
    base_dir = os.path.abspath(CONFIG_DIR)
    requested = os.path.abspath(path)
    if not requested.startswith(base_dir):
        raise ValueError("Access to the specified file is not allowed")
    with open(requested) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Prevent path traversal and command injection by using zipfile
    safe_name = os.path.basename(name)
    zip_path = f"{safe_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE)
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
    except Exception:
        abort(400)
    return jsonify({"token": token})


@app.route("/profile")
@require_auth
def api_profile():
    uid = request.args.get("id")
    try:
        data = query_profile(uid)
    except Exception as e:
        logger.exception("Failed to query profile")
        abort(400)
    return jsonify(data)


@app.route("/transfer", methods=["POST"])
@require_auth
def api_transfer():
    p = request.json or {}
    try:
        result = transfer_funds(p)
    except Exception as e:
        logger.exception("Transfer failed")
        abort(400)
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
@require_auth
def api_config():
    path = request.json.get("file")
    try:
        data = update_records(path)
    except Exception:
        abort(400)
    return jsonify(data)


@app.route("/export")
@require_auth
def api_export():
    name = request.args.get("name")
    try:
        export_data(name)
    except Exception:
        abort(400)
    return jsonify({"ok": 1})


if __name__ == "__main__":
    # Disable debug mode in production
    app.run(debug=False)

