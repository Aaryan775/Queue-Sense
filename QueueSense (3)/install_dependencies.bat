@echo off
REM =============================================
REM QueueSense - Install Dependencies
REM =============================================

echo.
echo ============================================
echo   QueueSense - Installing Dependencies
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

REM Check if UV is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo UV not found. Installing UV...
    pip install uv
    echo.
)

echo UV package manager found!
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Create virtual environment if not exists
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv
    echo.
)

REM Activate virtual environment and install dependencies
echo Installing Python dependencies...
echo.

REM Using UV to install dependencies from requirements.txt
uv pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Dependencies Installed Successfully!
echo ============================================
echo.
echo Next steps:
echo 1. Make sure MySQL is running
echo 2. Run database/schema.sql in MySQL
echo 3. Run run_program.bat to start the app
echo.

pause
