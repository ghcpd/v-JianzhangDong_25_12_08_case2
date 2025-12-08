# Security audit and remediation for `inputs.py`

Overview
- `inputs_backup.py`: original unmodified source (backup)
- `inputs.py`: secured and hardened version
- `report.json`: structured vulnerability report and fixes
- `requirements.txt`: Python dependencies
- `Dockerfile`: container image for quick environment
- `setup.sh`: sets up a virtualenv and installs deps (Linux/macOS)
- `run_test.sh`: runs smoke tests on Linux/macOS
- `run_test.bat`: runs smoke tests on Windows
- `auto_test.py`: detects environment and runs appropriate tests, logs to `logs/test_run.log`

Setup
1. Create a virtual environment and install dependencies (Linux/macOS):
```bash
./setup.sh
```
On Windows, run:
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

Running tests
- Linux/macOS: `bash run_test.sh`
- Windows: `run_test.bat`
- Docker: `docker build -t inputs-test . && docker run --rm inputs-test`

Auto test
- Run `python auto_test.py`. It will detect OS then run the matching test script and append logs to `logs/test_run.log`.

Logs
- `logs/test_run.log` contains timestamped entries and final status lines: `TEST PASSED` or `TEST FAILED`.
