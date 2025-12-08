@echo off
echo Running tests: starting Flask app for smoke test
start /B python inputs_backup.py
timeout /t 1 >nul
taskkill /IM python.exe /F >nul 2>&1 || echo no python process
start /B python inputs.py
timeout /t 1 >nul
taskkill /IM python.exe /F >nul 2>&1 || echo no python process
echo Tests finished
