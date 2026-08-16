@echo off

set "SSSF_ROOT=%~dp0.."
for %%I in ("%SSSF_ROOT%") do set "SSSF_ROOT=%%~fI"

cd /d "%SSSF_ROOT%"
if errorlevel 1 (
    echo FAIL: could not enter SSSF repository root
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo FAIL: Python is required before the SSSF Windows bootstrap can run.
    echo       Install Python 3.11 or newer and reopen Command Prompt.
    exit /b 1
)

set "SSSF_BOOTSTRAP_PATH="

for /f "usebackq delims=" %%P in (`python tools\windows_host.py emit-path`) do set "SSSF_BOOTSTRAP_PATH=%%P"

if not defined SSSF_BOOTSTRAP_PATH (
    echo FAIL: Windows bootstrap could not construct the SSSF session PATH.
    exit /b 1
)

set "PATH=%SSSF_BOOTSTRAP_PATH%"
set "SSSF_BOOTSTRAP_PATH="
set "SSSF_ROOT=%CD%"

python tools\windows_host.py doctor %*
if errorlevel 1 exit /b %errorlevel%

echo.
echo SSSF Windows session ready.
echo repo: %SSSF_ROOT%
echo line endings: python docs/validation/check_line_endings.py --require-worktree-lf
echo next: just
