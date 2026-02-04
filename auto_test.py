#!/usr/bin/env python3
import os
import platform
import subprocess
import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "test_run.log"

def timestamp():
    return datetime.datetime.utcnow().isoformat() + 'Z'

def run_test_script(target_file):
    system = platform.system()
    if system == 'Windows':
        cmd = [str(ROOT / 'run_test.bat'), target_file]
    else:
        cmd = ['bash', str(ROOT / 'run_test.sh'), target_file]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def main():
    files = ['input_backup.py', 'inputs.py']
    results = {}

    for f in files:
        t = timestamp()
        log(f"[{t}] Starting test for: {f}")
        rc, out = run_test_script(f)
        t2 = timestamp()
        log(f"[{t2}] OUTPUT for {f}:\n{out.strip()}")
        status = 'PASS' if rc == 0 else 'FAIL'
        log(f"[{t2}] RESULT for {f}: {status} (exit code {rc})")
        results[f] = rc

    # Interpret results: backup must be vulnerable (non-zero), patched must be zero
    backup_rc = results.get('input_backup.py', 1)
    fixed_rc = results.get('inputs.py', 1)

    final = 'TEST FAILED'
    if backup_rc != 0 and fixed_rc == 0:
        final = 'TEST PASSED'

    log(f"[{timestamp()}] FINAL STATUS: {final}")

    # Also print final status
    print(final)
    return 0 if final == 'TEST PASSED' else 2

if __name__ == '__main__':
    exit(main())
