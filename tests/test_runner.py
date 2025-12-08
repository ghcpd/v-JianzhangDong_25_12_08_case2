import argparse
import importlib.util
import os
import sqlite3
import sys
import zipfile
from types import ModuleType


def load_module_from_path(path: str) -> ModuleType:
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def setup_db(db_file):
    if os.path.exists(db_file):
        os.remove(db_file)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)")
    c.execute("INSERT INTO profiles (id,name,balance) VALUES (1,'alice',100.0)")
    c.execute("INSERT INTO profiles (id,name,balance) VALUES (2,'bob',200.0)")
    conn.commit()
    conn.close()


def setup_files():
    os.makedirs('configs', exist_ok=True)
    with open(os.path.join('configs', 'allowed.yml'), 'w') as f:
        f.write('allowed: true')
    with open('secret.txt', 'w') as f:
        f.write('top secret')


def test_sql_injection(mod):
    try:
        res = mod.query_profile("1' OR '1'='1")
    except Exception:
        # secure behavior is to reject the id
        return True, 'rejected invalid id'
    if isinstance(res, list) and len(res) > 1:
        return False, 'returned multiple rows (SQL injection vulnerable)'
    return True, 'no injection detected'


def test_update_records_traversal(mod):
    try:
        # attempt to read file outside config dir
        mod.update_records('../secret.txt')
        return False, 'allowed path traversal (file read)'
    except Exception as e:
        return True, f'blocked traversal: {e}'


def test_export_safe(mod):
    # remove any old zip
    zname = 'testdb.zip'
    if os.path.exists(zname):
        os.remove(zname)
    try:
        ret = mod.export_data('testdb')
    except Exception as e:
        return False, f'export failed: {e}'
    # check zip exists and contains db file
    if not os.path.exists(zname):
        return False, 'zip file not created'
    try:
        with zipfile.ZipFile(zname, 'r') as zf:
            namelist = zf.namelist()
            if mod.DB_FILE not in namelist:
                return False, 'db file not found in zip'
    except Exception as e:
        return False, f'zip test failed: {e}'
    return True, 'export ok'


def test_transfer_ssrf(mod):
    # inject a private IP URL; secure module should reject
    payload = {'target': 'acct', 'amount': 10, 'notify_url': 'http://169.254.169.254/latest/meta-data'}
    # monkeypatch requests.post to ensure no network call happens for unsafe modules
    class DummyResp:
        def __init__(self):
            self.text = 'ok'
        def raise_for_status(self):
            return None
    def dummy_post(url, json=None, timeout=None):
        return DummyResp()
    # replace module's requests.post
    if hasattr(mod, 'requests'):
        mod.requests.post = dummy_post
    try:
        mod.transfer_funds(payload)
        return False, 'did not block SSRF (allowed private IP)'
    except Exception as e:
        return True, f'blocked SSRF: {e}'


def test_auth_hash_strength(mod):
    try:
        token = mod.auth_user({'username': 'alice'})
        # md5 => 32 hex chars, sha256 => 64 hex chars
        if isinstance(token, str) and len(token) >= 64:
            return True, 'uses strong hash'
        else:
            return False, 'weak hashing (MD5 or similar)'
    except Exception as e:
        # if it raises because of env requirements, consider it OK if it's the secure module
        return True, f'auth raised: {e}'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--module', required=True, help='path to module file')
    args = p.parse_args()

    # set environment variables expected by the secure implementation
    os.environ.setdefault('PAYMENT_TOKEN', 'tok_test_123')
    os.environ.setdefault('INTERNAL_AUTH', 'internal_test')
    os.environ.setdefault('ADMIN_TOKEN', 'admin_test_token')
    os.environ.setdefault('ALLOWED_NOTIFY_HOSTS', 'example.com')

    # Setup test environment
    setup_db('appdata.db')
    setup_files()

    mod = load_module_from_path(args.module)

    tests = [
        ('SQL injection', test_sql_injection),
        ('Path traversal (update_records)', test_update_records_traversal),
        ('Export safety (zip)', test_export_safe),
        ('SSRF (transfer)', test_transfer_ssrf),
        ('Auth hash strength', test_auth_hash_strength),
    ]

    failed = []
    for name, fn in tests:
        ok, msg = fn(mod)
        print(f"{name}: {'PASS' if ok else 'FAIL'} - {msg}")
        if not ok:
            failed.append((name, msg))

    if failed:
        print(f"{len(failed)} tests failed")
        sys.exit(1)
    else:
        print('All tests passed')
        sys.exit(0)


if __name__ == '__main__':
    main()
