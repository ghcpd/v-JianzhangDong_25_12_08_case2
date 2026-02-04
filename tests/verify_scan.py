#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

def run(file):
    proc = subprocess.run([sys.executable, '-m', 'tests.scan_vulns', str(ROOT / file)], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def main():
    files = [('input_backup.py', 1), ('inputs.py', 0)]
    ok = True
    for fname, expected in files:
        rc, out = run(fname)
        print('---', fname, 'expected exit', expected, 'got', rc)
        print(out)
        if rc != expected:
            ok = False
    return 0 if ok else 2

if __name__ == '__main__':
    sys.exit(main())
