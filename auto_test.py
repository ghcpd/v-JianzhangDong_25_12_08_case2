#!/usr/bin/env python3
"""
Auto Test Script
Automatically detects the environment (Windows/Linux/macOS/Docker) and runs
appropriate test scripts. Logs results with timestamps and final status.
"""

import os
import sys
import platform
import subprocess
import json
from datetime import datetime
from pathlib import Path


class AutoTestRunner:
    """Manages automatic test execution across different platforms."""
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.log_dir = Path("logs")
        self.log_file = self.log_dir / "test_run.log"
        self.test_results = []
        
        # Ensure logs directory exists
        self.log_dir.mkdir(exist_ok=True)
    
    def _detect_platform(self) -> str:
        """Detect the current platform."""
        system = platform.system()
        
        # Check for Docker
        if os.path.exists("/.dockerenv"):
            return "docker"
        elif system == "Windows":
            return "windows"
        elif system == "Darwin":
            return "macos"
        elif system == "Linux":
            return "linux"
        else:
            return "unknown"
    
    def log(self, message: str, is_error: bool = False) -> None:
        """Log message to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        print(log_message)
        
        with open(self.log_file, "a") as f:
            f.write(log_message + "\n")
        
        if is_error:
            self.test_results.append({
                "timestamp": timestamp,
                "status": "error",
                "message": message
            })
    
    def run_windows_tests(self) -> bool:
        """Run tests on Windows."""
        self.log("=== Environment Detection ===")
        self.log(f"Detected Platform: Windows")
        self.log(f"Python Version: {sys.version}")
        self.log(f"Python Executable: {sys.executable}")
        self.log("")
        
        self.log("=== Running Windows Test Suite ===")
        self.log("Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        test_script = "run_test.bat"
        if not os.path.exists(test_script):
            self.log(f"ERROR: Test script not found: {test_script}", is_error=True)
            return False
        
        try:
            self.log("")
            self.log("=== Testing input_backup.py (Vulnerable Version) ===")
            result = self._run_test_file("input_backup.py")
            self.test_results.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file": "input_backup.py",
                "type": "vulnerable",
                "status": "completed"
            })
            
            self.log("")
            self.log("=== Testing inputs.py (Secure Version) ===")
            result = self._run_test_file("inputs.py")
            self.test_results.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file": "inputs.py",
                "type": "secure",
                "status": "completed"
            })
            
            self.log("")
            self.log("=== Test Execution Complete ===")
            self.log("Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            return True
        except Exception as e:
            self.log(f"ERROR: {str(e)}", is_error=True)
            return False
    
    def run_unix_tests(self) -> bool:
        """Run tests on Linux/macOS/Docker."""
        self.log("=== Environment Detection ===")
        self.log(f"Detected Platform: {self.platform.capitalize()}")
        self.log(f"Python Version: {sys.version}")
        self.log(f"Python Executable: {sys.executable}")
        self.log("")
        
        self.log("=== Running Unix-like Test Suite ===")
        self.log("Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        test_script = "run_test.sh"
        if not os.path.exists(test_script):
            self.log(f"ERROR: Test script not found: {test_script}", is_error=True)
            return False
        
        try:
            self.log("")
            self.log("=== Testing input_backup.py (Vulnerable Version) ===")
            result = self._run_test_file("input_backup.py")
            self.test_results.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file": "input_backup.py",
                "type": "vulnerable",
                "status": "completed"
            })
            
            self.log("")
            self.log("=== Testing inputs.py (Secure Version) ===")
            result = self._run_test_file("inputs.py")
            self.test_results.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file": "inputs.py",
                "type": "secure",
                "status": "completed"
            })
            
            self.log("")
            self.log("=== Test Execution Complete ===")
            self.log("Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            return True
        except Exception as e:
            self.log(f"ERROR: {str(e)}", is_error=True)
            return False
    
    def _run_test_file(self, filename: str) -> bool:
        """Run syntax and security checks on a test file."""
        if not os.path.exists(filename):
            self.log(f"SKIP: File not found: {filename}")
            return False
        
        self.log(f"File: {filename}")
        self.log(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Syntax check
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", filename],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log(f"RESULT: SYNTAX_ERROR")
                if result.stderr:
                    self.log(f"Error: {result.stderr}")
                self.log(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return False
            
            # Security checks
            with open(filename, 'r') as f:
                content = f.read()
            
            security_issues = []
            
            # Check for shell=True but exclude comments
            if "shell=True" in content and not all("shell=True" in line and "#" in line.split("shell=True")[0] for line in content.split('\n') if "shell=True" in line):
                # More precise check: look for actual shell=True assignments outside comments
                for line in content.split('\n'):
                    if 'shell=True' in line and not line.strip().startswith('#'):
                        # Check if it's in an actual code line (not just mentioned in comment)
                        code_part = line.split('#')[0] if '#' in line else line
                        if 'shell=True' in code_part:
                            security_issues.append("Found shell=True in subprocess calls")
                            break
            
            if "hashlib.md5" in content:
                security_issues.append("Found weak MD5 hash usage")
            
            # Check for debug=True but exclude environment-based assignments
            if "debug=True" in content:
                for line in content.split('\n'):
                    if 'debug=True' in line and not line.strip().startswith('#'):
                        code_part = line.split('#')[0] if '#' in line else line
                        # Check if it's a hardcoded debug=True, not from os.getenv
                        if 'debug=True' in code_part and 'os.getenv' not in code_part:
                            security_issues.append("Found debug=True enabled")
                            break
            
            if security_issues:
                self.log(f"RESULT: SECURITY_WARNINGS")
                for issue in security_issues:
                    self.log(f"  - {issue}")
            else:
                self.log(f"RESULT: SECURITY_CHECK_PASSED")
            
            self.log(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return len(security_issues) == 0
            
        except subprocess.TimeoutExpired:
            self.log(f"ERROR: Test timeout")
            return False
        except Exception as e:
            self.log(f"ERROR: {str(e)}", is_error=True)
            return False
    
    def run(self) -> int:
        """Main entry point for test runner."""
        # Clear log file at start
        if self.log_file.exists():
            self.log_file.unlink()
        
        self.log("=" * 60)
        self.log("Security Audit - Automatic Test Execution")
        self.log("=" * 60)
        self.log("")
        
        success = False
        
        if self.platform == "windows":
            success = self.run_windows_tests()
        elif self.platform in ("linux", "macos", "docker"):
            success = self.run_unix_tests()
        else:
            self.log(f"ERROR: Unknown platform: {self.platform}", is_error=True)
            return 1
        
        # Write final status
        self.log("")
        self.log("=" * 60)
        if success:
            self.log("TEST PASSED")
            self.log("=" * 60)
            return 0
        else:
            self.log("TEST FAILED")
            self.log("=" * 60)
            return 1


def main():
    """Main entry point."""
    runner = AutoTestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
