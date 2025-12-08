@echo off
if "%1"=="" (
  echo Usage: run_test.bat ^<file-to-scan^>
  exit /b 2
)
python -m tests.scan_vulns %1
exit /b %errorlevel%
