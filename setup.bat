@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo BIPT Info Organizer - Environment Setup
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
set "PYTHON_DIR=%PROJECT_DIR%vendor\python"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

REM =============================================
REM Step 1: Python Setup (Portable)
REM =============================================
echo [Step 1] Python Setup
echo.

if exist "%PYTHON_EXE%" (
    echo [Info] Portable Python found: %PYTHON_DIR%
    goto :check_python_configured
)

echo [Info] Portable Python not found.
echo [Downloading] Python 3.12.4 embeddable ...
echo.

set "PYTHON_VERSION=3.12.4"
set "PYTHON_ZIP=python-3.12.4-embed-amd64.zip"
set "DOWNLOAD_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP%"

powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%PROJECT_DIR%%PYTHON_ZIP%' -UseBasicParsing }"
if %errorlevel% neq 0 (
    echo [Error] Failed to download Python.
    pause
    exit /b 1
)

echo [Extracting] Python...
if exist "%PYTHON_DIR%" rmdir /s /q "%PYTHON_DIR%"
mkdir "%PYTHON_DIR%"
powershell -Command "Expand-Archive -Path '%PROJECT_DIR%%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"
del "%PROJECT_DIR%%PYTHON_ZIP%"

if not exist "%PYTHON_EXE%" (
    echo [Error] Failed to extract Python.
    pause
    exit /b 1
)

echo [OK] Python extracted.

:check_python_configured
set "PTH_FILE=%PYTHON_DIR%\python312._pth"

REM Create Lib\site-packages directory
if not exist "%PYTHON_DIR%\Lib" mkdir "%PYTHON_DIR%\Lib"
if not exist "%PYTHON_DIR%\Lib\site-packages" mkdir "%PYTHON_DIR%\Lib\site-packages"

REM Write proper _pth file with site-packages path
echo [Configuring] Python path...
(
    echo python312.zip
    echo .
    echo Lib
    echo Lib\site-packages
    echo import site
) > "%PTH_FILE%"
echo [OK] Python configured.

if not exist "%PYTHON_DIR%\Scripts\pip.exe" (
    echo [Downloading] pip...
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PYTHON_DIR%\get-pip.py' -UseBasicParsing }"
    if exist "%PYTHON_DIR%\get-pip.py" (
        echo [Installing] pip...
        "%PYTHON_EXE%" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
        del "%PYTHON_DIR%\get-pip.py"
    )
)

echo [Upgrading] pip...
"%PYTHON_EXE%" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn >nul 2>&1

echo.

REM =============================================
REM Step 2: Install Python Dependencies
REM =============================================
echo [Step 2] Python Dependencies
echo.

set "PYTHONPATH=%PROJECT_DIR%backend"
set "PYTHONHOME=%PYTHON_DIR%"

if exist "%PROJECT_DIR%backend\requirements.txt" (
    echo [Installing] packages from requirements.txt...
    "%PYTHON_EXE%" -m pip install -r "%PROJECT_DIR%backend\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
    if errorlevel 1 (
        echo [Error] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed.
) else (
    echo [Error] requirements.txt not found.
    pause
    exit /b 1
)

echo.

REM =============================================
REM Step 3: Create Directories
REM =============================================
echo [Step 3] Create Directories
echo.

if not exist "%PROJECT_DIR%data" mkdir "%PROJECT_DIR%data"
if not exist "%PROJECT_DIR%backend\assets" mkdir "%PROJECT_DIR%backend\assets"
echo [OK] Directories created.
echo.

REM =============================================
REM Complete
REM =============================================
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo   build.bat  - Build frontend
echo   run.bat    - Start the system
echo.
echo Note: bipthelper must be running on port 8000
echo.

pause
