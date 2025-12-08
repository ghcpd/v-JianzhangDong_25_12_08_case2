import os
import sqlite3
import requests
import hmac
from flask import Flask, request, jsonify
import subprocess
import yaml
import shlex
import logging
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)

# Secrets should be loaded from environment variables, not hardcoded
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN", "")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY", "")
INTERNAL_AUTH_KEY = os.getenv("INTERNAL_AUTH_KEY", "")

# Enable secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "appdata.db"


def auth_user(info):
    # Use HMAC-SHA256 instead of MD5 for secure authentication
    if not INTERNAL_AUTH_KEY:
        raise ValueError("INTERNAL_AUTH_KEY environment variable not set")
    username = info.get("username", "")
    password = info.get("password", "")
    raw = username + password
    hashed = hmac.new(
        INTERNAL_AUTH_KEY.encode(),
        raw.encode(),
        "sha256"
    ).hexdigest()
    return hashed


def query_profile(uid):
    # Prevent SQL Injection using parameterized queries
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Use parameterized query instead of string formatting
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
        data = c.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        return []


def transfer_funds(payload):
    # Validate input to prevent injection attacks
    target = payload.get("target")
    amount = payload.get("amount")
    
    # Validate target and amount
    if not target or not isinstance(amount, (int, float)):
        logger.error("Invalid transfer parameters")
        raise ValueError("Invalid transfer parameters")
    
    # Log securely without exposing sensitive information
    logger.info(f"Transfer initiated to target: {target}")
    
    url = payload.get("notify_url")
    if not url or not url.startswith(("http://", "https://")):
        logger.error("Invalid notification URL")
        raise ValueError("Invalid notification URL")
    
    try:
        # Use environment variable for sensitive token
        token = os.getenv("PAYMENT_TOKEN", "")
        if not token:
            raise ValueError("Payment token not configured")
        resp = requests.post(
            url,
            json={"token": token, "amount": amount},
            timeout=10
        )
        return resp.text
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise


def update_records(path):
    # Prevent arbitrary file access
    if not path:
        raise ValueError("File path cannot be empty")
    
    # Validate path to prevent directory traversal attacks
    allowed_dir = os.path.abspath("./config")
    abs_path = os.path.abspath(path)
    
    if not abs_path.startswith(allowed_dir):
        logger.error(f"Unauthorized access attempt to: {path}")
        raise ValueError("Access denied: file path not in allowed directory")
    
    if not os.path.exists(abs_path):
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    try:
        with open(abs_path) as f:
            # Use safe_load to prevent YAML deserialization attacks
            cfg = yaml.safe_load(f)
        return cfg
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {str(e)}")
        raise ValueError(f"Invalid YAML configuration: {str(e)}")


def export_data(name):
    # Prevent command injection using proper argument handling
    if not name or not isinstance(name, str):
        logger.error("Invalid export name")
        raise ValueError("Invalid export name")
    
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(name)
    if not safe_name:
        raise ValueError("Invalid filename")
    
    try:
        # Use list form instead of shell=True to prevent command injection
        cmd = ["zip", f"{safe_name}.zip", DB_FILE]
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            timeout=30
        )
        if result.returncode != 0:
            logger.error(f"Zip command failed: {result.stderr.decode()}")
            raise RuntimeError("Export failed")
        logger.info(f"Data exported successfully: {safe_name}.zip")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Export process timed out")
        raise
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise


@app.route("/auth", methods=["POST"])
def api_auth():
    try:
        info = request.get_json()
        if not info:
            return jsonify({"error": "Invalid request"}), 400
        token = auth_user(info)
        return jsonify({"token": token})
    except (ValueError, KeyError) as e:
        logger.error(f"Auth error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 401


@app.route("/profile")
def api_profile():
    try:
        uid = request.args.get("id")
        if not uid:
            return jsonify({"error": "ID parameter required"}), 400
        data = query_profile(uid)
        return jsonify({"profile": data})
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"error": "Profile lookup failed"}), 500


@app.route("/transfer", methods=["POST"])
def api_transfer():
    try:
        p = request.get_json()
        if not p:
            return jsonify({"error": "Invalid request"}), 400
        result = transfer_funds(p)
        return jsonify({"result": result})
    except ValueError as e:
        logger.error(f"Transfer validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Transfer error: {str(e)}")
        return jsonify({"error": "Transfer failed"}), 500


@app.route("/config", methods=["POST"])
def api_config():
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"error": "Invalid request"}), 400
        path = req_data.get("file")
        config = update_records(path)
        return jsonify({"config": config})
    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Config error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Config error: {str(e)}")
        return jsonify({"error": "Config update failed"}), 500


@app.route("/export")
def api_export():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Name parameter required"}), 400
        export_data(name)
        return jsonify({"ok": 1})
    except ValueError as e:
        logger.error(f"Export validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({"error": "Export failed"}), 500


if __name__ == "__main__":
    # Disable debug mode and set secure defaults for production
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
