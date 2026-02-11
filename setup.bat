@echo off
echo ==========================================
echo   DABO - First Time Setup
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

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Creating data directories...
if not exist "data\projects" mkdir "data\projects"
if not exist "data\templates" mkdir "data\templates"
if not exist "logs" mkdir "logs"

echo.
echo Running self-test...
python run.py --test

echo.
echo ==========================================
echo   Setup complete!
echo   Run: launch.bat
echo   Or:  python run.py --test
echo ==========================================
pause
