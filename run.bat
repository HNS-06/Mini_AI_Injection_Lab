@echo off
title Mini AI Security Lab
color 0B

echo.
echo  ========================================
echo   Mini AI Security Lab - Setup
echo  ========================================
echo.

:: Check Python
echo  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  X Python not found!
    echo    Please install Python 3.10+ from python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  + %PYVER% found
echo.

:: Create virtual environment
echo  Creating environment...
if not exist "venv" (
    python -m venv venv
    echo  + Environment created
) else (
    echo  + Environment already exists
)
echo.

:: Activate and install
echo  Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
echo  + Dependencies ready
echo.

:: Start application
echo  ========================================
echo   Starting AI Security Lab...
echo  ========================================
echo.
echo  Open: http://127.0.0.1:5000
echo  Press Ctrl+C to stop
echo.

python app\main.py

pause
