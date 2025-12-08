@echo off
REM Test script for Windows
REM Runs security audit tests on both vulnerable and fixed versions

setlocal enabledelayedexpansion

echo === Security Audit Test Suite ^(Windows^) ===
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
echo Timestamp: !mydate! !mytime!
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating Python virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -q -r requirements.txt

REM Create logs directory
if not exist "logs" mkdir logs

REM Function to run test on a file
:test_file
setlocal
set "test_file=%1"
set "test_name=%2"

echo ---
echo Testing: !test_name!
echo File: !test_file!
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
echo Start Time: !mydate! !mytime!

if not exist "!test_file!" (
    echo ERROR: Test file not found: !test_file!
    exit /b 1
)

REM Run basic syntax check
python -m py_compile "!test_file!" 2>nul
if errorlevel 1 (
    echo RESULT: SYNTAX_ERROR - File has syntax errors
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
    echo End Time: !mydate! !mytime!
    exit /b 1
)

REM Check for security issues using findstr
findstr /M "shell=True" "!test_file!" >nul
if not errorlevel 1 (
    echo WARNING: Found shell=True in subprocess calls
    exit /b 1
)

findstr /M "hashlib.md5" "!test_file!" >nul
if not errorlevel 1 (
    echo WARNING: Found weak MD5 hash usage
    exit /b 1
)

findstr /M "debug=True" "!test_file!" >nul
if not errorlevel 1 (
    echo WARNING: Found debug=True enabled
    exit /b 1
)

echo RESULT: SECURITY_CHECK_PASSED
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
echo End Time: !mydate! !mytime!
exit /b 0
endlocal

REM Main execution
echo === Testing Original ^(Vulnerable^) Version ===
call :test_file "input_backup.py" "Vulnerable Version"
if errorlevel 1 (
    echo input_backup.py: Tests found issues ^(expected for vulnerable version^)
) else (
    echo input_backup.py: Tests completed
)

echo.
echo === Testing Fixed Version ===
call :test_file "inputs.py" "Secure Version"
if errorlevel 1 (
    echo inputs.py: Security checks failed
    goto test_failed
) else (
    echo inputs.py: All security checks passed!
)

echo.
echo === Test Summary ===
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
echo Timestamp: !mydate! !mytime!
echo TEST PASSED
exit /b 0

:test_failed
echo.
echo === Test Summary ===
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
echo Timestamp: !mydate! !mytime!
echo TEST FAILED
exit /b 1
