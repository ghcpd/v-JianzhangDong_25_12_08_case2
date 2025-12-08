import os
import platform
import subprocess
import datetime

LOG_DIR = os.path.join(os.getcwd(), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'test_run.log')
os.makedirs(LOG_DIR, exist_ok=True)


def ts():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def run_command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    out, _ = proc.communicate()
    return proc.returncode, out.decode(errors='replace')


def log_and_print(message):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + '\n')
    print(message)


def main():
    # Detect environment
    system = platform.system()
    log_and_print(f"{ts()} - Starting automated tests on {system}")

    # 1) Run tests against input_backup.py
    if system == 'Windows':
        cmd = 'python -u tests/test_runner.py backup'
    else:
        cmd = 'python3 -u tests/test_runner.py backup'
    log_and_print(f"{ts()} - Running backup tests: {cmd}")
    code, output = run_command(cmd)
    log_and_print(f"{ts()} - BACKUP OUTPUT:\n{output}")
    status = 'PASSED' if code == 0 else 'FAILED'
    log_and_print(f"{ts()} - BACKUP TEST {status} (exit={code})")

    # 2) Run tests against fixed inputs.py
    if system == 'Windows':
        cmd = 'python -u tests/test_runner.py fixed'
    else:
        cmd = 'python3 -u tests/test_runner.py fixed'
    log_and_print(f"{ts()} - Running fixed tests: {cmd}")
    code2, output2 = run_command(cmd)
    log_and_print(f"{ts()} - FIXED OUTPUT:\n{output2}")
    status2 = 'PASSED' if code2 == 0 else 'FAILED'
    log_and_print(f"{ts()} - FIXED TEST {status2} (exit={code2})")

    final_status = 'TEST PASSED' if (code == 0 and code2 == 0) else 'TEST FAILED'
    log_and_print(f"{ts()} - {final_status}")
    return 0 if final_status == 'TEST PASSED' else 2


if __name__ == '__main__':
    exit(main())
