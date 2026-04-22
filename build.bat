@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ====================================
echo BIPT Info Organizer - Build Frontend
echo ====================================
echo.

cd /d "%~dp0"

REM Check Node.js
set "NODE_FOUND=0"
where node >nul 2>&1
if not errorlevel 1 set "NODE_FOUND=1"
if exist "C:\Program Files\nodejs\node.exe" set "NODE_FOUND=1"
if exist "C:\Program Files (x86)\nodejs\node.exe" set "NODE_FOUND=1"

if "%NODE_FOUND%"=="0" (
    echo [Info] Node.js not found.
    echo [Installing] Node.js LTS via winget...
    echo.

    winget install OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [Error] winget install failed.
        echo [Tip] Install Node.js manually from https://nodejs.org/
        pause
        exit /b 1
    )

    echo [Info] Node.js installed via winget.
    echo [Tip] If node is not found, restart your terminal and run build.bat again.
    echo.
)

REM Find npm
set "NPM_CMD=npm"
if exist "C:\Program Files\nodejs\npm.cmd" set "NPM_CMD=C:\Program Files\nodejs\npm.cmd"

echo [Info] Node.js found:
node --version
echo.

cd /d "%~dp0frontend"

REM Install dependencies
if not exist "node_modules" (
    echo [Step 1] Installing frontend dependencies...
    call "%NPM_CMD%" install
    if errorlevel 1 (
        echo [Error] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo.
)

REM Build
echo [Step 2] Building frontend SPA...
call "%NPM_CMD%" run build
if errorlevel 1 (
    echo [Error] Build failed.
    pause
    exit /b 1
)

REM Deploy
echo [Step 3] Deploying frontend...
if exist "%~dp0backend\assets\frontend" (
    rmdir /S /Q "%~dp0backend\assets\frontend" 2>nul
)
mkdir "%~dp0backend\assets\frontend" 2>nul
xcopy /E /I /Y "%~dp0frontend\dist\*" "%~dp0backend\assets\frontend\" >nul 2>&1
echo [Done] Frontend deployed to backend/assets/frontend/

echo.
echo ====================================
echo [Success] Build completed!
echo ====================================
echo.
echo Now run run.bat to start the system.
pause
