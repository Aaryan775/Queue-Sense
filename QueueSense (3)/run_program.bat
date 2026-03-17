@echo off
REM =============================================
REM QueueSense - Run Application
REM =============================================

echo.
echo ============================================
echo      QueueSense - Starting Application
echo ============================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please run install_dependencies.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set environment variables
set FLASK_APP=app
set FLASK_ENV=development
set FLASK_DEBUG=1

echo Starting Flask Backend Server...
echo.
echo Backend running at: http://localhost:5000
echo Frontend files at:  %~dp0frontend
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run with UV
uv run flask run --host=0.0.0.0 --port=5000

pause
