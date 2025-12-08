@echo off
python -u tests\test_runner.py both
if %ERRORLEVEL%==0 (
  echo ALL TESTS PASSED
) else (
  echo SOME TESTS FAILED
)
exit /b %ERRORLEVEL%
