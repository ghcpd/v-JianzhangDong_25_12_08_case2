import os
import re
import sqlite3
import requests
import hashlib
import hmac
import logging
import zipfile
import yaml
import pathlib
import ipaddress
import urllib.parse
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration via environment variables (required in production)
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.getenv("INTERNAL_AUTH")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
DB_FILE = os.getenv("DB_FILE", "appdata.db")
CONFIG_DIR = os.getenv("CONFIG_DIR", os.path.join(os.getcwd(), "configs"))
ALLOWED_NOTIFY_HOSTS = set([h.strip() for h in os.getenv("ALLOWED_NOTIFY_HOSTS", "").split(",") if h.strip()])

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _require_env(name):
    val = globals().get(name)
    if not val:
        raise RuntimeError(f"Environment variable {name} is required")
    return val


def auth_user(info):
    # Use HMAC-SHA256 instead of MD5 and require INTERNAL_AUTH be set
    username = info.get("username", "")
    if not username:
        raise ValueError("username required")
    secret = _require_env("INTERNAL_AUTH")
    token = hmac.new(secret.encode(), username.encode(), hashlib.sha256).hexdigest()
    return token


def query_profile(uid):
    # Validate uid as integer and use parameterized queries
    try:
        uid_int = int(uid)
    except Exception:
        raise ValueError("invalid id")
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid_int,))
        rows = c.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _is_private_host(host):
    # If host is an IP address and is private/reserved, return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_unspecified
    except ValueError:
        # not an IP literal
        return False


def _validate_notify_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("invalid URL scheme")
    host = parsed.hostname
    if not host:
        raise ValueError("invalid URL")
    if _is_private_host(host):
        raise ValueError("disallowed host")
    if ALLOWED_NOTIFY_HOSTS and host not in ALLOWED_NOTIFY_HOSTS:
        raise ValueError("host not allowed")
    return True


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    if target is None or amount is None:
        raise ValueError("target and amount are required")
    url = payload.get("notify_url")
    if not url:
        raise ValueError("notify_url required")
    _validate_notify_url(url)
    token = _require_env("PAYMENT_TOKEN")
    try:
        resp = requests.post(url, json={"token": token, "amount": amount}, timeout=5)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logging.exception("notify failed")
        raise


def update_records(filename):
    # Only allow files inside CONFIG_DIR and only by name
    if os.path.isabs(filename) or ".." in filename:
        raise ValueError("invalid filename")
    cfg_dir = CONFIG_DIR
    pathlib.Path(cfg_dir).mkdir(parents=True, exist_ok=True)
    path = os.path.realpath(os.path.join(cfg_dir, filename))
    if not path.startswith(os.path.realpath(cfg_dir)):
        raise ValueError("access denied")
    if not os.path.exists(path):
        raise FileNotFoundError("file not found")
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Validate name and create zip using Python's zipfile module
    if not NAME_RE.match(name):
        raise ValueError("invalid name")
    zip_name = f"{name}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE)
    return zip_name


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "missing authorization"}), 401
        if token.startswith("Bearer "):
            token = token.split(" ", 1)[1]
        if token != ADMIN_TOKEN:
            return jsonify({"error": "forbidden"}), 403
        return f(*args, **kwargs)

    return wrapper


@app.route("/auth", methods=["POST"])
def api_auth():
    try:
        info = request.json or {}
        return jsonify({"token": auth_user(info)})
    except Exception as e:
        logging.exception("auth failed")
        return jsonify({"error": str(e)}), 400


@app.route("/profile")
@require_auth
def api_profile():
    uid = request.args.get("id")
    try:
        return jsonify(query_profile(uid))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/transfer", methods=["POST"])
@require_auth
def api_transfer():
    p = request.json or {}
    try:
        return jsonify({"result": transfer_funds(p)})
    except Exception as e:
        logging.exception("transfer failed")
        return jsonify({"error": str(e)}), 400


@app.route("/config", methods=["POST"])
@require_auth
def api_config():
    filename = request.json.get("file") if request.json else None
    try:
        return jsonify(update_records(filename))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logging.exception("config failed")
        return jsonify({"error": str(e)}), 400


@app.route("/export")
@require_auth
def api_export():
    name = request.args.get("name")
    try:
        zip_name = export_data(name)
        return jsonify({"ok": 1, "file": zip_name})
    except Exception as e:
        logging.exception("export failed")
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # Do not run in debug mode by default
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
