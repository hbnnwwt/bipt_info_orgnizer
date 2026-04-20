@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ====================================
echo BIPTInfoOrganizer - Build Frontend
echo ====================================
echo.

cd /d "%~dp0"

set "NODE_FOUND=0"
where node >nul 2>&1
if not errorlevel 1 set "NODE_FOUND=1"

if "%NODE_FOUND%"=="0" (
    echo [Info] Node.js not found. Installing via winget...
    winget install OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements
)

where node >nul 2>&1
if errorlevel 1 (
    echo [Error] Node.js not found after installation.
    pause & exit /b 1
)

echo [Info] Node.js found:
node --version
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [Step 1] Installing frontend dependencies...
    npm install
    if errorlevel 1 (
        echo [Error] Failed to install dependencies
        pause & exit /b 1
    )
    echo.
)

echo [Step 2] Building SPA...
npm run build
if errorlevel 1 (
    echo [Error] Build failed
    pause & exit /b 1
)

echo [Step 3] Deploying SPA...
if exist "%~dp0backend\assets\frontend" (
    rmdir /S /Q "%~dp0backend\assets\frontend" 2>nul
)
mkdir "%~dp0backend\assets\frontend" 2>nul
xcopy /E /I /Y "%~dp0frontend\dist\*" "%~dp0backend\assets\frontend\" >nul 2>&1
echo [Done] SPA deployed to backend/assets/frontend/

echo.
echo ====================================
echo [Success] Build completed!
echo [SPA] backend/assets/frontend/
echo ====================================
echo.
pause