@echo off
REM Flexible Agents MCP Server - Windows Batch Script
REM Simple launcher for Windows users

setlocal enabledelayedexpansion

echo Flexible Agents MCP Server v2.0.0
echo =====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or later from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

REM Check if config exists
if not exist "config.json" (
    if not exist ".env" (
        echo.
        echo WARNING: No configuration found!
        echo.
        echo Please either:
        echo 1. Create a config.json file (copy from config.json.example)
        echo 2. Create a .env file (copy from .env.example)
        echo 3. Set environment variables directly
        echo.
        echo Creating sample configuration files...
        python server.py --create-config
        echo.
        echo Please update config.json or .env with your actual values
        pause
        exit /b 1
    )
)

REM Start the server
echo.
echo Starting MCP Server...
echo Press Ctrl+C to stop the server
echo.

python server.py %*

echo.
echo Server stopped
pause
