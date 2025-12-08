Overview

This project contains a repaired version of inputs.py and supporting artifacts produced by a security audit.

Files generated:
- input_backup.py: Original, unmodified source (backup)
- inputs.py: Secured/fixed source
- report.json: Structured vulnerability report and fixes
- requirements.txt: Python dependencies
- Dockerfile: Minimal container for the app
- setup.sh: Virtualenv setup script for Linux/macOS
- run_test.sh: Runs the security tests for a given module (Linux/macOS)
- run_test.bat: Runs the security tests for a given module (Windows)
- auto_test.py: Detects environment and runs tests for input_backup.py and inputs.py, logs to logs/test_run.log
- tests/test_runner.py: Test runner that checks for SQLi, path traversal, export safety, SSRF, and hash strength
- logs/: Directory where auto_test.py writes logs (logs/test_run.log)

Setup

1. Create a virtual environment and install requirements (Linux/macOS):
   ./setup.sh

2. On Windows:
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

3. Configure environment variables (required for running the fixed app and tests):
   - PAYMENT_TOKEN
   - INTERNAL_AUTH
   - ADMIN_TOKEN
   Optionally:
   - ALLOWED_NOTIFY_HOSTS (comma-separated hostnames allowed for notify_url)
   - CONFIG_DIR (defaults to ./configs)
   - DB_FILE (defaults to appdata.db)

Running tests

- Linux/macOS:
  ./run_test.sh input_backup.py   # expected to FAIL (demonstrates vulnerabilities)
  ./run_test.sh inputs.py        # expected to PASS (fixed)

- Windows:
  run_test.bat input_backup.py
  run_test.bat inputs.py

Using auto_test.py

Run automatic testing which runs tests for both input_backup.py and inputs.py and writes logs to logs/test_run.log:

  python auto_test.py

The log contains timestamps and a final status line: TEST PASSED or TEST FAILED

Interpreting logs

- Each run records the module tested, test output, exit codes, and a final overall status.
- The intended passing condition is: input_backup.py should fail the vulnerability checks (non-zero exit code) and inputs.py should pass (zero exit code). If so, auto_test.py will log TEST PASSED.

Notes

- The fixed code requires environment variables to be set at runtime.
- The tests are unit-style checks aimed at demonstrating the presence/absence of the specific vulnerabilities fixed in inputs.py.
