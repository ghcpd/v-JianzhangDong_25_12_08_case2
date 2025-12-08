# Security Audit and Fixes

This repository contains the original vulnerable implementation (input_backup.py), the secured implementation (inputs.py), an automated test framework, and automation artifacts for reproduction and verification.

Files generated:

- input_backup.py: Backup copy of the original vulnerable source.
- inputs.py: Secured, refactored version of the application.
- report.json: Structured vulnerability report listing findings and fixes.
- tests/test_runner.py: Automated tests that demonstrate vulnerabilities in the backup and verify fixes in the secured code.
- run_test.sh / run_test.bat: Platform-specific test runners.
- auto_test.py: Automatic test executor that detects the platform, runs tests for backup and fixed code sequentially, and writes logs to logs/test_run.log.
- requirements.txt: Python package requirements.
- Dockerfile: Image recipe to run the app in a container.
- setup.sh: Convenience script to create a virtualenv and install dependencies.
- logs/: Directory where auto_test.py will save test output logs.

Setup and run:

1) Linux / macOS:

- Create virtual environment and install dependencies:
  ./setup.sh

- Run tests manually:
  ./run_test.sh

- Run automated detection and tests:
  python3 auto_test.py

2) Windows:

- Install dependencies:
  pip install -r requirements.txt

- Run tests manually:
  run_test.bat

- Run automated detection and tests:
  python auto_test.py

Explore logs:

- The auto_test.py script saves detailed logs to `logs/test_run.log` with timestamps. A final status line will contain either `TEST PASSED` or `TEST FAILED`.

Notes:

- The secure implementation reads secret values from environment variables. For local testing you can export the following variables:

  export AUTH_TOKEN=devtoken
  export PAYMENT_TOKEN=paytoken
  export INTERNAL_AUTH=internalsecret

- In production, run the Flask app behind a WSGI server such as gunicorn and ensure secret values are injected via secure mechanisms (vaults, secrets manager).

