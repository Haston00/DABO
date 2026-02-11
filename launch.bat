@echo off
echo ==========================================
echo   DABO - AI Plan Review ^& Scheduling
echo ==========================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.11+ first.
    pause
    exit /b 1
)

:: Launch
python run.py %*

pause
