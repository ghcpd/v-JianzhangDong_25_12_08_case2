#!/usr/bin/env bash
set -e
echo "Running tests: starting Flask app for smoke test"
PYTHONPATH=. python - <<'PY'
import subprocess, time
proc = subprocess.Popen(["python3","inputs_backup.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1)
proc.terminate()
print('inputs_backup started and stopped')
proc = subprocess.Popen(["python3","inputs.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1)
proc.terminate()
print('inputs (secured) started and stopped')
PY
