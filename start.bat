@echo off
title Property Defect Inspection System

echo ============================================
echo   Property Defect Inspection System
echo   AI-Powered by Claude Opus 4.6
echo ============================================
echo.

REM Check for .env file
if not exist ".env" (
    echo [SETUP] No .env file found. Creating from template...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Open .env and set your ANTHROPIC_API_KEY
    echo    File location: %CD%\.env
    echo.
    pause
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
)

echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

echo [SETUP] Installing/updating dependencies...
pip install -r requirements.txt -q

echo.
echo [OK] Starting server at http://localhost:8000
echo [OK] Press Ctrl+C to stop
echo.

REM Open browser after short delay
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

REM Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
