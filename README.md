# Security Audit & Remediation — inputs.py

Overview
- inputs.py (original insecure source is saved in `input_backup.py`).
- `inputs.py` has been remediated to remove discovered vulnerabilities.
- This workspace contains tests and automation to verify the original file was vulnerable and the fixed file is secure.

Files generated
- `input_backup.py` — original, unchanged copy of the provided source.
- `inputs.py` — remediated version with security fixes.
- `report.json` — structured security report listing vulnerabilities, severities, lines and fixes.
- `requirements.txt` — Python deps for running tests.
- `Dockerfile` — Docker environment to run the project and automatic tests.
- `setup.sh` — sets up virtualenv, installs packages, and creates a sample test database and configs.
- `run_test.sh` (Linux/macOS) — run the static vulnerability scanner against a single file.
- `run_test.bat` (Windows) — Windows wrapper for running the scanner.
- `auto_test.py` — automatic test runner which checks `input_backup.py` and `inputs.py` in sequence and writes `logs/test_run.log`.
- `tests/scan_vulns.py` — a small static scanner that detects insecure patterns present in the original file.

Quick setup (Linux / macOS)
1. Make script executable: `chmod +x setup.sh run_test.sh`
2. Run setup: `./setup.sh` to create environment, database, and config sample.

Quick setup (Windows)
1. Ensure Python 3.8+ is installed and on PATH.
2. Create a virtual environment and install requirements: `python -m venv .venv` then `.
.venv\Scripts\activate` and `pip install -r requirements.txt`.

How to run tests
- Linux/macOS: `./run_test.sh <file>` — e.g. `./run_test.sh inputs.py`
- Windows: `run_test.bat <file>` — e.g. `run_test.bat inputs.py`

Automatic test runner
- Run `python auto_test.py` — this will:
  - Run the scanner for `input_backup.py` and `inputs.py` in sequence
  - Save timestamped outputs and a final status line to `logs/test_run.log`
  - Print either `TEST PASSED` or `TEST FAILED` depending on results

Log file
- `logs/test_run.log` will include per-file outputs, timestamps, and a final `TEST PASSED`/`TEST FAILED` line.

Notes
- This test suite uses static pattern checks to demonstrate the difference between the insecure original and the remediated version. In production you should add runtime and integration tests that exercise real endpoints and verify behaviour.
- Before deploying `inputs.py` make sure to set required environment variables: `PAYMENT_TOKEN`, `MAIL_SERVER_KEY`, `INTERNAL_AUTH` and optionally `NOTIFY_WHITELIST` and `DB_FILE`.
