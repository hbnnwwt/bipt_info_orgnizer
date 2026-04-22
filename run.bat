@echo off
chcp 65001 >nul
echo ====================================
echo BIPT Info Organizer - Startup
echo ====================================
echo.

cd /d "%~dp0"

REM Check Python environment: portable > system
set "PYTHON_EXE="

if exist "%~dp0vendor\python\python.exe" (
    set "PYTHON_EXE=%~dp0vendor\python\python.exe"
    goto :check_bipthelper
)

where python >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('where python') do set "PYTHON_EXE=%%i"
    goto :check_bipthelper
)

echo [Error] Python not found.
echo [Info] Please run setup.bat first.
echo.
pause
exit /b 1

:check_bipthelper
REM Check if bipthelper is running on port 8000
echo [Checking] bipthelper on port 8000...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -TimeoutSec 3 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo [Warning] bipthelper is not running on port 8000!
    echo [Info] Please start bipthelper first, then restart this script.
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 0
)
echo [OK] bipthelper is running.
echo.

REM Set environment
if exist "%~dp0vendor\python\python.exe" (
    set "PYTHONPATH=%~dp0backend"
    set "PYTHONHOME=%~dp0vendor\python"
)

REM Free port 8001 if already in use
echo [Info] Checking port 8001...
powershell -ExecutionPolicy Bypass -File "%~dp0kill8001.ps1"

REM Start backend (port 8001)
echo [Starting] Organizer backend on port 8001...
cd backend
start "BIPT-Organizer" cmd /c "%PYTHON_EXE% main.py 2> ..\backend_err.txt"

timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:8001

echo.
echo ====================================
echo System started!
echo Organizer:  http://localhost:8001
echo Bipthelper:  http://localhost:8000
echo ====================================
echo.
echo Press any key to close this window...
pause >nul
