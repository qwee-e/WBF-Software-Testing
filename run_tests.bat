@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "WBF_TEST_PYTHON=.venv-test\Scripts\python.exe"
if exist "%WBF_TEST_PYTHON%" goto install
where py >nul 2>nul
if errorlevel 1 goto fallback
py -3.10 -m venv .venv-test
if errorlevel 1 goto fallback
goto install
:fallback
python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3,10) else 1)"
if errorlevel 1 goto setup_error
python -m venv .venv-test
if errorlevel 1 goto setup_error
:install
"%WBF_TEST_PYTHON%" -m pip install -r requirements-test.txt
if errorlevel 1 goto setup_error
"%WBF_TEST_PYTHON%" -X utf8 run_tests.py
set "WBF_TEST_EXIT=%ERRORLEVEL%"
echo.
echo Finished. Exit code: %WBF_TEST_EXIT%
echo See test_results for logs and reports. Exit 1 means assertions failed.
pause
exit /b %WBF_TEST_EXIT%
:setup_error
echo Setup failed. Install Python 3.10 and check the error above.
pause
exit /b 2
