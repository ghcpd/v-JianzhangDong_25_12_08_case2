import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify, abort
import subprocess
import yaml
import logging

app = Flask(__name__)

# Load secrets from environment to avoid hardcoding
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")

DB_FILE = os.environ.get("DB_FILE", "appdata.db")

logging.basicConfig(level=logging.INFO)


def auth_user(info):
    username = info.get("username", "")
    if not username:
        raise ValueError("username required")
    if not INTERNAL_AUTH:
        raise RuntimeError("Internal auth not configured")
    raw = username + INTERNAL_AUTH
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return hashed


def query_profile(uid):
    if not uid or not uid.isdigit():
        raise ValueError("invalid user id")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        q = "SELECT id,name,balance FROM profiles WHERE id = ?"
        c.execute(q, (uid,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    if not target or not isinstance(amount, (int, float)):
        raise ValueError("invalid transfer payload")
    logging.info("transfer:%s:%s", target, amount)
    url = payload.get("notify_url")
    if not url or not url.startswith("https://"):
        raise ValueError("invalid notify_url")
    if not PAYMENT_TOKEN:
        raise RuntimeError("Payment token not configured")
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.exception("Failed to notify payment gateway")
        return str(e)
    return resp.text


def update_records(path):
    # Restrict to a safe config directory
    base_dir = os.path.abspath(os.environ.get("CONFIG_DIR", "."))
    full_path = os.path.abspath(path)
    if not full_path.startswith(base_dir):
        raise ValueError("invalid config path")
    with open(full_path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Avoid shell=True and validate name
    if not name or any(c in name for c in ['/', '\\', '..']):
        raise ValueError("invalid export name")
    archive = f"{name}.zip"
    try:
        subprocess.Popen(["zip", archive, DB_FILE], shell=False)
    except Exception:
        logging.exception("Failed to export data")
        return False
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
    except Exception as e:
        logging.exception("auth failed")
        abort(400, str(e))
    return jsonify({"token": token})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    try:
        data = query_profile(uid)
    except Exception as e:
        logging.exception("profile query failed")
        abort(400, str(e))
    return jsonify(data)


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.json or {}
    try:
        result = transfer_funds(p)
    except Exception as e:
        logging.exception("transfer failed")
        abort(400, str(e))
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
def api_config():
    path = (request.json or {}).get("file")
    try:
        cfg = update_records(path)
    except Exception as e:
        logging.exception("config update failed")
        abort(400, str(e))
    return jsonify(cfg)


@app.route("/export")
def api_export():
    name = request.args.get("name")
    try:
        ok = export_data(name)
    except Exception as e:
        logging.exception("export failed")
        abort(400, str(e))
    return jsonify({"ok": 1 if ok else 0})


if __name__ == "__main__":
    # Do not run with debug=True in production
    app.run(debug=False)
