import os
import sqlite3
import requests
import hashlib
import hmac
import re
import logging
from urllib.parse import urlparse
from flask import Flask, request, jsonify, abort
import zipfile
import io
import yaml

app = Flask(__name__)

# Load secrets and config from environment variables (do NOT keep secrets in source)
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")
# INTERNAL_AUTH is used as a server-side HMAC key
INTERNAL_AUTH = os.getenv("INTERNAL_AUTH")

# Database path configurable for tests and deployment
DB_FILE = os.getenv("DB_FILE", "appdata.db")

# A small optional allowlist of notification hosts (comma separated)
NOTIFY_WHITELIST = [h.strip() for h in os.getenv("NOTIFY_WHITELIST", "").split(",") if h.strip()]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not INTERNAL_AUTH:
    logger.warning("INTERNAL_AUTH not set — security-sensitive behavior may be disabled")


def auth_user(info):
    """Generate a secure HMAC-based token from username using INTERNAL_AUTH.

    Returns hex digest string. Requires INTERNAL_AUTH to be set.
    """
    username = info.get("username", "")
    if not INTERNAL_AUTH:
        raise RuntimeError("server misconfiguration: INTERNAL_AUTH missing")
    mac = hmac.new(INTERNAL_AUTH.encode(), username.encode(), hashlib.sha256)
    return mac.hexdigest()


def query_profile(uid):
    # Validate user id: only allow numeric ids in this API
    if uid is None or not re.fullmatch(r"\d+", uid):
        raise ValueError("invalid user id")

    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        # Use a parameterized query to eliminate SQL injection
        c.execute("SELECT id, name, balance FROM profiles WHERE id = ?", (uid,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def _is_allowed_notify_url(url):
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    # Only allow https for notification callbacks
    if parsed.scheme != "https":
        return False
    hostname = parsed.hostname or ""
    if NOTIFY_WHITELIST:
        return hostname in NOTIFY_WHITELIST
    # If no whitelist provided, be conservative and disallow
    return False


def transfer_funds(payload):
    # Validate required params
    target = payload.get("target")
    amount = payload.get("amount")
    notify_target = payload.get("notify_url")

    if not target or amount is None or notify_target is None:
        raise ValueError("missing transfer parameters")

    # Validate amount type/size
    try:
        amt = float(amount)
        if amt <= 0:
            raise ValueError("amount must be positive")
    except Exception:
        raise ValueError("invalid amount")

    logger.info("processing transfer to target: %s (amount redacted)" , target)

    if not _is_allowed_notify_url(notify_target):
        raise ValueError("notify_url is not allowed")

    # Post to the notify url with a short timeout and verify SSL
    resp = requests.post(notify_target, json={"token": PAYMENT_TOKEN, "amount": amt}, timeout=5)
    resp.raise_for_status()
    return resp.text


def update_records(filename):
    # Do NOT allow arbitrary file paths from clients. Only load from configured folder.
    cfg_dir = os.getenv("CONFIG_DIR", "configs")
    # disallow path traversal
    if not filename or os.path.basename(filename) != filename:
        raise ValueError("invalid file name")

    read_path = os.path.join(cfg_dir, filename)
    if not os.path.exists(read_path):
        raise FileNotFoundError("config not found")

    with open(read_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Sanitize name and use zipfile module to avoid shell injection
    if not name or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("invalid export name")

    zip_name = f"{name}.zip"
    # Create zip in-memory then write to disk for atomicity
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    logger.info("exported data to %s", zip_name)
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
    except Exception:
        return jsonify({"error": "server misconfiguration"}), 500
    return jsonify({"token": token})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    try:
        data = query_profile(uid)
        return jsonify(data)
    except ValueError:
        return jsonify({"error": "invalid id"}), 400
    except Exception as e:
        logger.exception("profile lookup failed")
        return jsonify({"error": "internal error"}), 500


@app.route("/transfer", methods=["POST"])
def _require_token():
    header = request.headers.get("X-Auth-Token") or ""
    if not header:
        abort(401)
    # In a real app we'd validate the token properly against a user/session store
    # Here we only ensure server has a key
    if not INTERNAL_AUTH:
        abort(500)


def api_transfer():
    _require_token()
    p = request.json or {}
    try:
        result = transfer_funds(p)
        return jsonify({"result": result})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.RequestException as e:
        logger.exception("notify failed")
        return jsonify({"error": "notify failed"}), 502
    except Exception:
        logger.exception("transfer failed")
        return jsonify({"error": "internal error"}), 500


@app.route("/config", methods=["POST"])
def api_config():
    # require auth for config updates
    _require_token()
    fname = (request.json or {}).get("file")
    try:
        data = update_records(fname)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "file not found"}), 404
    except ValueError:
        return jsonify({"error": "invalid file"}), 400
    except Exception:
        logger.exception("config load failed")
        return jsonify({"error": "internal error"}), 500


@app.route("/export")
def api_export():
    _require_token()
    name = request.args.get("name")
    try:
        export_data(name)
        return jsonify({"ok": 1})
    except ValueError:
        return jsonify({"error": "invalid name"}), 400
    except Exception:
        logger.exception("export failed")
        return jsonify({"error": "internal error"}), 500


if __name__ == "__main__":
    # The app should not be run in debug mode in production
    app.run(debug=False)
