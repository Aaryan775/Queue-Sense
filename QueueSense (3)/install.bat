@echo off
REM =============================================
REM QueueSense - Dependency Installation Script
REM =============================================

echo =============================================
echo    QueueSense - Installation Script
echo    Smart Queues. Human Care.
echo =============================================
echo.

REM Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b 1
)
echo Python found!
echo.

REM Navigate to backend directory
echo [2/4] Setting up backend environment...
cd /d "%~dp0backend"

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment and install dependencies
echo [3/4] Installing Python dependencies...
call venv\Scripts\activate.bat

REM Install required packages
pip install flask flask-cors flask-sqlalchemy pymysql pyjwt bcrypt python-dotenv >nul 2>&1
if errorlevel 1 (
    echo Installing packages with pip...
    pip install flask flask-cors flask-sqlalchemy pymysql pyjwt bcrypt python-dotenv
)
echo Python dependencies installed!
echo.

REM Return to root directory
cd /d "%~dp0"

REM Database setup reminder
echo [4/4] Database Setup Reminder
echo =============================================
echo Please import the database schema by running:
echo   mysql -u root -p ^< database\queuesense.sql
echo.
echo Or use MySQL Workbench to import:
echo   database\queuesense.sql
echo =============================================
echo.

echo =============================================
echo    Installation Complete!
echo    Run 'run.bat' to start the application.
echo =============================================
pause
