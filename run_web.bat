@echo off
REM Tahlil Web Application Startup Script for Windows

echo.
echo ============================================
echo   Tahlil Web Application
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required packages...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing required packages...
    pip install flask flask-cors
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

REM Check if data and runs directories exist
if not exist "data" mkdir data
if not exist "runs" mkdir runs
if not exist "frontend" (
    echo ERROR: frontend directory not found
    echo Make sure you're in the Tahlil root directory
    pause
    exit /b 1
)

echo.
echo All requirements met!
echo.
echo Starting Tahlil Web Application...
echo.
echo Website will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
