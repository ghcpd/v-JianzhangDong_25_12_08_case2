import subprocess
import time
import requests
import tempfile
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

LOG = 'logs/test_run.log'
os.makedirs('logs', exist_ok=True)

def log(s):
    ts = datetime.utcnow().isoformat() + 'Z'
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {s}\n")

class MockHandler(BaseHTTPRequestHandler):
    received = None
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode('utf-8')
        MockHandler.received = body
        self.send_response(200)
        self.end_headers()

def start_mock_server(port):
    server = HTTPServer(('127.0.0.1', port), MockHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server

def prepare_db(dbfile):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, name TEXT, balance REAL)')
    c.execute("INSERT OR REPLACE INTO profiles (id,name,balance) VALUES ('1','Alice',100.0)")
    c.execute("INSERT OR REPLACE INTO profiles (id,name,balance) VALUES ('2','Bob',200.0)")
    conn.commit()
    conn.close()

def run_server_and_tests(server_script, env_overrides):
    env = os.environ.copy()
    env.update(env_overrides)
    # Ensure mock handler state is cleared
    MockHandler.received = None
    p = subprocess.Popen(['python', server_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    time.sleep(1.5)
    try:
        # Run checks against this running server on port 5000
        results = {}

        # 1) Hashing type via /auth
        try:
            r = requests.post('http://127.0.0.1:5000/auth', json={'username':'user'}, timeout=5)
            tok = r.json().get('token') if r.status_code==200 else None
            results['token'] = tok
        except Exception as e:
            results['token'] = None

        # 2) SQLi via /profile
        inj = "1' OR '1'='1"
        try:
            r = requests.get('http://127.0.0.1:5000/profile', params={'id':inj}, timeout=5)
            results['sqli_resp'] = r.json() if r.status_code==200 else None
            results['sqli_status'] = r.status_code
        except Exception as e:
            results['sqli_resp'] = None
            results['sqli_status'] = None

        # 3) Start mock server and test /transfer
        mock_port = 8001
        mock = start_mock_server(mock_port)
        time.sleep(0.2)
        try:
            r = requests.post('http://127.0.0.1:5000/transfer', json={'target':'x','amount':10,'notify_url':f'http://127.0.0.1:{mock_port}/notify'}, timeout=5)
            time.sleep(0.5)
            results['mock_received'] = MockHandler.received
            results['transfer_status'] = r.status_code
        except Exception as e:
            results['mock_received'] = None
            results['transfer_status'] = None

        # 4) Path traversal via /config
        # create a config file outside CONFIG_DIR
        outside = os.path.abspath('outside_config.yml')
        with open(outside,'w',encoding='utf-8') as f:
            f.write('ok: true')
        try:
            r = requests.post('http://127.0.0.1:5000/config', json={'file': outside}, timeout=5)
            results['config_status'] = r.status_code
            results['config_resp'] = r.json() if r.status_code==200 else None
        except Exception as e:
            results['config_status'] = None

        # 5) Export name validation via /export
        try:
            r = requests.get('http://127.0.0.1:5000/export', params={'name':'../evil'}, timeout=5)
            results['export_status'] = r.status_code
            results['export_resp'] = r.json() if r.status_code==200 else None
        except Exception as e:
            results['export_status'] = None

        return results
    finally:
        p.terminate()
        p.wait(timeout=2)

def evaluate(vuln_results, patched_results):
    # Determine vulnerability presence in original and safety in patched
    summary = {}

    # Token lengths: md5=32, sha256=64
    tok_v = vuln_results.get('token')
    tok_p = patched_results.get('token')
    summary['vuln_hash_md5'] = tok_v is not None and len(tok_v)==32
    summary['patched_hash_sha256'] = tok_p is not None and len(tok_p)==64

    # SQLi: vuln likely returns list of rows (length>=2) when injection used; patched should reject (400) or return None
    sqli_v = vuln_results.get('sqli_resp')
    sqli_p_status = patched_results.get('sqli_status')
    summary['vulnerable_to_sqli'] = isinstance(sqli_v, list) and len(sqli_v) >= 2
    summary['patched_resists_sqli'] = (sqli_p_status is not None and sqli_p_status >=400)

    # SSRF: vuln should have mock_received not None; patched should not post to http (requires https)
    summary['vuln_ssrf_sent'] = vuln_results.get('mock_received') is not None
    summary['patched_ssrf_blocked'] = patched_results.get('mock_received') is None

    # Path traversal: vuln should return config content (status 200), patched should block (400)
    summary['vuln_path_traversal'] = vuln_results.get('config_status')==200
    summary['patched_blocks_path_traversal'] = patched_results.get('config_status') is not None and patched_results.get('config_status')>=400

    # Export unsafe name: vuln may accept (200), patched should block (400)
    summary['vuln_export_accepts_invalid'] = vuln_results.get('export_status')==200
    summary['patched_export_blocks'] = patched_results.get('export_status') is not None and patched_results.get('export_status')>=400

    return summary

def main():
    tmpdir = tempfile.mkdtemp()
    dbfile = os.path.join(tmpdir, 'test.db')
    prepare_db(dbfile)

    # Run vulnerable server
    log('Starting vulnerable server tests')
    vuln_env = {'DB_FILE': dbfile, 'CONFIG_DIR': tmpdir}
    vuln_results = run_server_and_tests('inputs_backup.py', vuln_env)
    log(f'vulnerable_results: {vuln_results}')

    # Run patched server
    log('Starting patched server tests')
    patched_env = {'DB_FILE': dbfile, 'CONFIG_DIR': tmpdir, 'PAYMENT_TOKEN':'test_pay', 'MAIL_SERVER_KEY':'m', 'INTERNAL_AUTH':'secret'}
    patched_results = run_server_and_tests('inputs.py', patched_env)
    log(f'patched_results: {patched_results}')

    summary = evaluate(vuln_results, patched_results)
    log(f'summary: {summary}')

    # Decide final pass: patched_resists_sqli and patched_ssrf_blocked and patched_blocks_path_traversal and patched_export_blocks and patched_hash_sha256
    ok = all([
        summary['patched_hash_sha256'],
        summary['patched_resists_sqli'],
        summary['patched_ssrf_blocked'],
        summary['patched_blocks_path_traversal'],
        summary['patched_export_blocks']
    ])

    log('FINAL_TEST_RESULT: ' + ('PASSED' if ok else 'FAILED'))
    return 0 if ok else 2

if __name__ == '__main__':
    rc = main()
    exit(rc)
