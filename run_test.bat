@echo off
if "%1"=="" (
  echo Usage: %~nx0 module_file
  exit /b 2
)
python -u tests\test_runner.py --module "%1"
exit /b %errorlevel%
