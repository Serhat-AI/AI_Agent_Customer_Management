@echo off
REM Windows Batch Script for RSD Analysis Agent Local Deployment
REM Run as Administrator

setlocal enabledelayedexpansion

echo ========================================
echo RSD Analysis Agent - Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ from https://www.python.org
    pause
    exit /b 1
)

REM Get project directory
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo Step 1: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 3: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 4: Checking .env configuration...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo Created .env from template. Please edit with your settings.
        echo Opening .env in notepad...
        notepad .env
    ) else (
        echo ERROR: .env.example not found
        pause
        exit /b 1
    )
)

echo.
echo Step 5: Running setup check...
python setup_check.py
if errorlevel 1 (
    echo Some checks failed. Please fix issues before running the agent.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Download credentials.json from Google Cloud Console
echo   2. Place credentials.json in: %PROJECT_DIR%
echo   3. Run: python main.py --init
echo   4. Then: python main.py
echo.
pause
