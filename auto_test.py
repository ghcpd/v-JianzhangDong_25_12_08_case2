import os
import platform
import subprocess
import datetime

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'test_run.log')
MODULES = ['input_backup.py', 'inputs.py']

os.makedirs(LOG_DIR, exist_ok=True)


def timestamp():
    return datetime.datetime.utcnow().isoformat() + 'Z'


def run_script_for_module(module):
    system = platform.system()
    if system == 'Windows':
        script = 'run_test.bat'
        cmd = [script, module]
    else:
        script = './run_test.sh'
        cmd = [script, module]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + '\n' + proc.stderr


def main():
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp()}] Starting automated tests\n")
        results = {}
        for mod in MODULES:
            f.write(f"[{timestamp()}] Running tests for {mod}\n")
            code, output = run_script_for_module(mod)
            f.write(output + '\n')
            f.write(f"[{timestamp()}] Exit code: {code}\n")
            results[mod] = code

        # Determine overall success: backup should FAIL (non-zero) and inputs.py should PASS (0)
        backup_ok = results.get('input_backup.py', 1) != 0
        fixed_ok = results.get('inputs.py', 1) == 0
        overall_ok = backup_ok and fixed_ok
        final_status = 'TEST PASSED' if overall_ok else 'TEST FAILED'
        f.write(f"[{timestamp()}] {final_status}\n")

    print(final_status)
    return 0 if overall_ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
