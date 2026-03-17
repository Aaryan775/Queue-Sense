@echo off
REM =============================================
REM QueueSense - Application Launcher
REM =============================================

echo =============================================
echo    QueueSense - Starting Application
echo    Smart Queues. Human Care.
echo =============================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the Flask application
echo Starting Flask backend server...
echo.
echo Backend URL: http://localhost:5000
echo Frontend URL: Open frontend/index.html in browser
echo.
echo Press Ctrl+C to stop the server.
echo =============================================
echo.

REM Run the Flask application
python run.py

REM Deactivate on exit
call venv\Scripts\deactivate.bat
