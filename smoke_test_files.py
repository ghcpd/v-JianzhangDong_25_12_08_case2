import subprocess
import time
from datetime import datetime
import os

targets = ["inputs_backup.py", "inputs.py"]
log = 'logs/test_run.log'
os.makedirs('logs', exist_ok=True)

def log_line(s):
    ts = datetime.utcnow().isoformat() + 'Z'
    with open(log, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {s}\n")

def run_one(path):
    try:
        p = subprocess.Popen(["python", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        time.sleep(2)
        # Check if process is still running
        ret = p.poll()
        if ret is None:
            p.terminate()
            log_line(f"{path} START_OK")
            return True
        else:
            out = p.stdout.read().decode('utf-8', errors='replace') if p.stdout else ''
            log_line(f"{path} EXITED_IMMEDIATELY exit:{ret} output:{out[:200]}")
            return False
    except Exception as e:
        log_line(f"{path} ERROR {e}")
        return False

def main():
    overall = True
    for t in targets:
        ok = run_one(t)
        overall = overall and ok
    final = 'TEST PASSED' if overall else 'TEST FAILED'
    log_line(final)

if __name__ == '__main__':
    main()
