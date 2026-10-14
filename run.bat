@echo off
echo ====================================================================
echo  AI Healthcare Companion + Smart Vital Tracker & Emergency System
echo  B.Tech Final-Year Major Project Prototype
echo ====================================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

REM Copy .env.example if .env does not exist
if not exist .env (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env
)

REM Install dependencies if needed
echo [INFO] Checking Python dependencies...
python -m pip install -r requirements.txt

REM Run initial seed if database doesn't exist
if not exist backend\app.db (
    echo [INFO] Database not found. Seeding initial demo data...
    python -m seed.seed
)

echo.
echo ====================================================================
echo  Starting FastAPI Server on http://localhost:8000
echo  Simulator will auto-start in background.
echo  Press Ctrl+C to stop.
echo ====================================================================
echo.

python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
