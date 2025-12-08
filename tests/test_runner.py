import os
import sys
import sqlite3
import importlib.util
import tempfile
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(__file__))

DB_PATH = os.path.join(ROOT, 'appdata.db')
CONFIG_DIR = os.path.join(ROOT, 'configs')

os.makedirs(CONFIG_DIR, exist_ok=True)

# Create test DB with two profiles
def prepare_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
    c.execute('INSERT INTO profiles (id, name, balance) VALUES (1, "Alice", 100.0)')
    c.execute('INSERT INTO profiles (id, name, balance) VALUES (2, "Bob", 200.0)')
    conn.commit()
    conn.close()

# Create a secret file outside configs
SECRETS_FILE = os.path.join(ROOT, 'secret.txt')
with open(SECRETS_FILE, 'w') as f:
    f.write('TOP_SECRET=1')

# Create a config file inside configs
CONFIG_FILE = os.path.join(CONFIG_DIR, 'app.yaml')
with open(CONFIG_FILE, 'w') as f:
    f.write('setting: ok')

prepare_db()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sql_injection(mod, expect_vulnerable=False):
    # For backup module expect that passing a predicate that always true returns both rows
    if expect_vulnerable:
        results = mod.query_profile("1' OR '1'='1")
        return len(results) > 1
    else:
        try:
            _ = mod.query_profile("1' OR '1'='1")
            return False
        except Exception:
            return True


def test_arbitrary_file_read(mod, expect_vulnerable=False):
    try:
        data = mod.update_records(SECRETS_FILE)
        if expect_vulnerable:
            return 'TOP_SECRET' in ''.join(str(data))
        else:
            return False
    except Exception:
        return not expect_vulnerable


def test_export_command_injection(mod, expect_vulnerable=False):
    # Monkeypatch subprocess.Popen if exists in module
    injected_flag = os.path.join(ROOT, 'injected.marker')
    if os.path.exists(injected_flag):
        os.remove(injected_flag)

    original_popen = getattr(mod, 'subprocess', None)
    recorded = {'cmd': None}

    class FakePopen:
        def __init__(self, cmd, shell=False):
            recorded['cmd'] = cmd
            # Simulate side effect if command contains suspicious chars
            if ';' in cmd or '&' in cmd:
                with open(injected_flag, 'w') as f:
                    f.write('injected')
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    # If module uses subprocess we can monkeypatch subprocess.Popen to our fake
    if hasattr(mod, 'subprocess'):
        mod.subprocess.Popen = FakePopen
    try:
        mod.export_data("testname; echo injected")
    except Exception:
        pass
    finally:
        # restore if needed
        if hasattr(mod, 'subprocess') and original_popen:
            mod.subprocess = original_popen

    exists = os.path.exists(injected_flag)
    if expect_vulnerable:
        return exists
    else:
        return not exists


def run_tests_for_module(path, name, expect_vulnerable):
    mod = load_module(path, name)
    results = []
    results.append(('sql_injection', test_sql_injection(mod, expect_vulnerable)))
    results.append(('file_read', test_arbitrary_file_read(mod, expect_vulnerable)))
    results.append(('export_injection', test_export_command_injection(mod, expect_vulnerable)))
    return results


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'both'
    overall_ok = True
    outputs = []

    if target in ('both', 'backup'):
        mod_path = os.path.join(ROOT, 'input_backup.py')
        outputs.append(('input_backup.py', run_tests_for_module(mod_path, 'input_backup', True)))

    if target in ('both', 'fixed'):
        mod_path = os.path.join(ROOT, 'inputs.py')
        outputs.append(('inputs.py', run_tests_for_module(mod_path, 'inputs', False)))

    # Print results
    for name, tests in outputs:
        print(f"Results for {name}:")
        for tname, ok in tests:
            print(f"  {tname}: {'PASSED' if ok else 'FAILED'}")
            if not ok:
                overall_ok = False
    if overall_ok:
        print('ALL TESTS PASSED')
        sys.exit(0)
    else:
        print('SOME TESTS FAILED')
        sys.exit(2)

if __name__ == '__main__':
    main()
