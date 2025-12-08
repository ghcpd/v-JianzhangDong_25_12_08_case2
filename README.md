# Security Audit Report: Flask Application Security Fixes

## Overview

This repository contains the results of a comprehensive security audit of a Flask application. The original `input_backup.py` contained **6 critical security vulnerabilities** that have been fixed in the secured version `inputs.py`.

### Executive Summary

- **Total Vulnerabilities Found**: 6
- **Critical**: 3
- **High**: 2
- **Medium**: 1
- **Status**: All vulnerabilities have been remediated

## Generated Files and Their Purpose

### Core Application Files
- **`inputs.py`** - Secured version of the Flask application with all vulnerabilities fixed
- **`input_backup.py`** - Original vulnerable version (for comparison and testing)
- **`report.json`** - Detailed vulnerability report in JSON format with remediation details

### Configuration Files
- **`requirements.txt`** - Python package dependencies
- **`.env.example`** - Template for environment variables (copy to `.env` and populate with actual values)
- **`Dockerfile`** - Docker container configuration for consistent environment setup

### Setup and Test Scripts
- **`setup.sh`** - Linux/macOS environment setup script
- **`run_test.sh`** - Linux/macOS test execution script
- **`run_test.bat`** - Windows test execution script
- **`auto_test.py`** - Cross-platform automatic test runner with environment detection

### Documentation
- **`README.md`** - This file, containing setup instructions and usage guidelines

## Vulnerabilities Fixed

### 1. SQL Injection (Critical)
**Location**: `inputs.py` line 21 (formerly `query_profile()`)

**Vulnerability**: User input was directly interpolated into SQL queries using string formatting.
```python
# VULNERABLE CODE
q = "SELECT id,name,balance FROM profiles WHERE id = '%s'" % uid
```

**Fix**: Implemented parameterized queries to separate SQL code from data.
```python
# SECURE CODE
c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
```

### 2. Hardcoded Secrets (Critical)
**Location**: `inputs.py` lines 12-14

**Vulnerability**: API keys and tokens were hardcoded in source code, exposing them in version control.
```python
# VULNERABLE CODE
PAYMENT_TOKEN = "tok_production_998877"
MAIL_SERVER_KEY = "mail_srv_key_ABCDEFG"
INTERNAL_AUTH = "admin_internal_5566"
```

**Fix**: Moved all secrets to environment variables.
```python
# SECURE CODE
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN", "")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY", "")
INTERNAL_AUTH_KEY = os.getenv("INTERNAL_AUTH_KEY", "")
```

### 3. Command Injection (Critical)
**Location**: `inputs.py` line 37 (formerly `export_data()`)

**Vulnerability**: User input used in shell commands with `shell=True`, allowing arbitrary command execution.
```python
# VULNERABLE CODE
cmd = f"zip {name}.zip {DB_FILE}"
subprocess.Popen(cmd, shell=True)
```

**Fix**: Used list-based arguments with `shell=False` to prevent shell interpretation.
```python
# SECURE CODE
cmd = ["zip", f"{safe_name}.zip", DB_FILE]
result = subprocess.run(cmd, shell=False, capture_output=True, timeout=30)
```

### 4. Weak Cryptographic Hash (High)
**Location**: `inputs.py` lines 18-19 (formerly `auth_user()`)

**Vulnerability**: MD5 is cryptographically broken and unsuitable for authentication.
```python
# VULNERABLE CODE
hashed = hashlib.md5(raw.encode()).hexdigest()
```

**Fix**: Implemented HMAC-SHA256 for cryptographically secure authentication.
```python
# SECURE CODE
hashed = hmac.new(
    INTERNAL_AUTH_KEY.encode(),
    raw.encode(),
    "sha256"
).hexdigest()
```

### 5. Path Traversal (High)
**Location**: `inputs.py` line 33 (formerly `update_records()`)

**Vulnerability**: Arbitrary file paths allowed, enabling access to sensitive files outside intended directories.
```python
# VULNERABLE CODE
with open(path) as f:
    cfg = yaml.safe_load(f)
```

**Fix**: Implemented strict path validation to restrict file access.
```python
# SECURE CODE
allowed_dir = os.path.abspath("./config")
abs_path = os.path.abspath(path)
if not abs_path.startswith(allowed_dir):
    raise ValueError("Access denied: file path not in allowed directory")
```

### 6. Debug Mode in Production (Medium)
**Location**: `inputs.py` line 45

**Vulnerability**: Flask debug mode enabled by default, exposing sensitive information and enabling remote code execution.
```python
# VULNERABLE CODE
app.run(debug=True)
```

**Fix**: Made debug mode environment-controlled with secure defaults.
```python
# SECURE CODE
debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
app.run(debug=debug_mode, host="127.0.0.1", port=5000)
```

## Environment Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment support (built-in with Python 3.3+)
- For Linux/macOS: bash shell
- For Windows: PowerShell or Command Prompt

### Setup Instructions

#### On Linux/macOS

1. **Make setup script executable**:
   ```bash
   chmod +x setup.sh run_test.sh
   ```

2. **Run setup script**:
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install all dependencies from requirements.txt
   - Create necessary directories (logs, config, data)
   - Set up example environment variables
   - Create test configuration files

3. **Activate virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual secrets
   nano .env
   ```

#### On Windows

1. **Run setup in PowerShell**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   mkdir logs, config, data
   copy .env.example .env
   ```

2. **Configure environment variables**:
   - Edit `.env` with your actual secrets

### Environment Variables

The application requires the following environment variables (see `.env.example`):

```
PAYMENT_TOKEN=your_payment_token_here
MAIL_SERVER_KEY=your_mail_server_key_here
INTERNAL_AUTH_KEY=your_internal_auth_key_here
FLASK_ENV=production
FLASK_DEBUG=False
```

**IMPORTANT**: Never commit `.env` to version control. Keep this file local and secure.

## Running Tests

### Using run_test.sh (Linux/macOS)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run tests
bash run_test.sh
```

This script will:
- Test both vulnerable (`input_backup.py`) and secure (`inputs.py`) versions
- Perform syntax validation
- Check for security issues (shell=True, MD5 usage, debug=True, etc.)
- Output results to both console and logs/test_run.log
- Return exit code 0 on success, 1 on failure

### Using run_test.bat (Windows)

```cmd
# Run tests
run_test.bat
```

This batch script will:
- Create and activate virtual environment if needed
- Test both vulnerable and secure versions
- Perform syntax and security checks
- Log results to logs/test_run.log
- Exit with code 0 on success, 1 on failure

### Expected Test Output

```
=== Security Audit Test Suite ===
Timestamp: 2024-01-15 14:30:45

--- Testing: Vulnerable Version
File: input_backup.py
Start Time: 2024-01-15 14:30:45
WARNING: Found shell=True in subprocess calls
RESULT: SECURITY_CHECK_FAILED
End Time: 2024-01-15 14:30:46

--- Testing: Secure Version
File: inputs.py
Start Time: 2024-01-15 14:30:47
RESULT: SECURITY_CHECK_PASSED
End Time: 2024-01-15 14:30:48

=== Test Summary ===
TEST PASSED
```

## Using auto_test.py for Automatic Testing

The `auto_test.py` script provides cross-platform automatic test execution with environment detection.

### Features
- **Automatic Platform Detection**: Detects Windows, Linux, macOS, or Docker
- **Timestamped Logging**: All outputs include timestamps
- **Comprehensive Reporting**: Tests both vulnerable and secure versions
- **Structured Output**: Results saved to `logs/test_run.log`
- **Exit Code Handling**: Returns proper exit codes for CI/CD integration

### Running auto_test.py

```bash
# Make sure Python is available
python auto_test.py
```

or

```bash
python3 auto_test.py
```

### auto_test.py Output

```
[2024-01-15 14:30:45] ============================================================
[2024-01-15 14:30:45] Security Audit - Automatic Test Execution
[2024-01-15 14:30:45] ============================================================
[2024-01-15 14:30:45] 
[2024-01-15 14:30:45] === Environment Detection ===
[2024-01-15 14:30:45] Detected Platform: Windows
[2024-01-15 14:30:45] Python Version: 3.11.0 (main, Oct 24 2022, 18:26:48) [MSC v.1933 64 bit (AMD64)]
[2024-01-15 14:30:45] Python Executable: C:\path\to\venv\Scripts\python.exe
[2024-01-15 14:30:45] 
[2024-01-15 14:30:45] === Testing input_backup.py (Vulnerable Version) ===
[2024-01-15 14:30:46] File: input_backup.py
[2024-01-15 14:30:46] RESULT: SECURITY_WARNINGS
[2024-01-15 14:30:46]   - Found shell=True in subprocess calls
[2024-01-15 14:30:46]   - Found weak MD5 hash usage
[2024-01-15 14:30:46]   - Found debug=True enabled
[2024-01-15 14:30:46] 
[2024-01-15 14:30:46] === Testing inputs.py (Secure Version) ===
[2024-01-15 14:30:47] File: inputs.py
[2024-01-15 14:30:47] RESULT: SECURITY_CHECK_PASSED
[2024-01-15 14:30:47] 
[2024-01-15 14:30:47] ============================================================
[2024-01-15 14:30:47] TEST PASSED
[2024-01-15 14:30:47] ============================================================
```

### Exit Codes
- **0**: All tests passed
- **1**: Tests failed or errors encountered

## Checking Test Logs

Test results are saved to `logs/test_run.log`:

```bash
# View test log
cat logs/test_run.log

# View last 20 lines
tail -20 logs/test_run.log

# Search for test status
grep "TEST PASSED\|TEST FAILED" logs/test_run.log
```

### Log Format

Each log entry includes:
- **Timestamp**: `[YYYY-MM-DD HH:MM:SS]`
- **Message**: Descriptive text of test step
- **Final Status**: Either `TEST PASSED` or `TEST FAILED`

Example log format:
```
[2024-01-15 14:30:45] === Environment Detection ===
[2024-01-15 14:30:45] Detected Platform: Windows
[2024-01-15 14:30:45] === Testing input_backup.py (Vulnerable Version) ===
[2024-01-15 14:30:46] Start Time: 2024-01-15 14:30:46
[2024-01-15 14:30:46] RESULT: SECURITY_WARNINGS
[2024-01-15 14:30:46] === Testing inputs.py (Secure Version) ===
[2024-01-15 14:30:47] Start Time: 2024-01-15 14:30:47
[2024-01-15 14:30:47] RESULT: SECURITY_CHECK_PASSED
[2024-01-15 14:30:47] End Time: 2024-01-15 14:30:47
[2024-01-15 14:30:47] TEST PASSED
```

## Using Docker

A `Dockerfile` is provided for containerized testing:

### Building Docker Image

```bash
docker build -t security-audit:latest .
```

### Running Tests in Docker

```bash
# Run tests
docker run --rm security-audit:latest python auto_test.py

# Run with volume mount to see logs
docker run --rm -v $(pwd)/logs:/app/logs security-audit:latest python auto_test.py
```

## Security Best Practices

### For Production Deployment

1. **Environment Variables**: Always use environment variables for secrets
   ```bash
   export PAYMENT_TOKEN="actual_token_value"
   export INTERNAL_AUTH_KEY="actual_key_value"
   ```

2. **Disable Debug Mode**: Ensure `FLASK_DEBUG=False` in production
   ```bash
   export FLASK_DEBUG=False
   ```

3. **Use HTTPS**: Always use HTTPS in production
   ```python
   # Use a production WSGI server like Gunicorn
   gunicorn --certfile=cert.pem --keyfile=key.pem inputs:app
   ```

4. **Restrict Network Access**: Bind to localhost by default
   - Use a reverse proxy (nginx, Apache) for external access
   - Never expose Flask development server to the internet

5. **Input Validation**: All user inputs are validated before use
   - SQL queries use parameterized queries
   - File paths are validated against a whitelist
   - Command arguments are passed as lists, not strings

6. **Logging**: Security events are logged appropriately
   - Sensitive information (tokens, passwords) are never logged
   - All errors are logged for monitoring

## Comparing Vulnerable vs. Secure Versions

Use the `report.json` file to understand each vulnerability:

```bash
# View the full report
cat report.json | python -m json.tool

# Or use jq (if available)
jq '.details[] | "\(.id): \(.vulnerability_type) - \(.severity)"' report.json
```

### Report Structure

Each vulnerability in `report.json` includes:
- **id**: Unique identifier
- **file**: Affected file
- **line_numbers**: Lines where vulnerability exists
- **vulnerability_type**: Type of vulnerability
- **severity**: Critical/High/Medium/Low
- **description**: Detailed explanation
- **fix_explanation**: How it was fixed
- **secure_code_snippet**: Example of secure code

## Continuous Integration / Continuous Deployment

The test scripts are designed for CI/CD integration:

### GitHub Actions Example

```yaml
name: Security Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: python auto_test.py
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### Missing Dependencies

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Permission Denied (Linux/macOS)

```bash
# Make scripts executable
chmod +x setup.sh run_test.sh auto_test.py
```

### Import Errors

```bash
# Verify all packages are installed
pip list | grep -E "Flask|requests|PyYAML|python-dotenv"

# Reinstall if needed
pip install -r requirements.txt --force-reinstall
```

## Additional Resources

- **Flask Security**: https://flask.palletsprojects.com/en/latest/security/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Python Security**: https://python.readthedocs.io/en/latest/library/security_warnings.html
- **CWE (Common Weakness Enumeration)**: https://cwe.mitre.org/

## Support and Reporting

For questions or issues with the security audit:
1. Review the detailed `report.json` file
2. Check test logs in `logs/test_run.log`
3. Verify environment setup with `python auto_test.py`
4. Consult the OWASP Top 10 for vulnerability details

## License

This security audit and all fixes are provided for educational and security purposes.

---

**Audit Date**: December 8, 2024  
**Status**: All vulnerabilities remediated and verified  
**Next Steps**: Deploy fixed version and maintain security updates
