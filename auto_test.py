import os
import platform
import subprocess
import datetime

LOG_DIR = os.path.join('logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'test_run.log')

def log(msg):
    ts = datetime.datetime.utcnow().isoformat() + 'Z'
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {msg}\n")

def run_command(cmd, shell=False):
    start = datetime.datetime.utcnow()
    log(f"START {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        p = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        out = p.stdout.decode('utf-8', errors='replace')
        log(out)
        status = 'TEST PASSED' if p.returncode == 0 else 'TEST FAILED'
        log(f"{status} (exit {p.returncode})")
        return p.returncode == 0
    except Exception as e:
        log(str(e))
        log('TEST FAILED (exception)')
        return False

def main():
    env = platform.system()
    log(f"Auto test started on {env}")
    tests = []
    if env == 'Windows':
        tests = [(['cmd', '/c', 'run_test.bat'], True)]
    else:
        tests = [(['bash','run_test.sh'], True)]

    # Run tests for backup then secured version
    overall = True
    for cmd, shell_flag in tests:
        ok = run_command(cmd, shell=shell_flag)
        overall = overall and ok

    final = 'TEST PASSED' if overall else 'TEST FAILED'
    log(f"Auto test finished: {final}")

if __name__ == '__main__':
    main()
