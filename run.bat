@echo off
REM Wrapper script for content_ingestion.py

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is required but not installed. Please install Python and try again.
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    
    REM Activate virtual environment
    call venv\Scripts\activate
    
    REM Install required packages
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    REM Activate virtual environment
    call venv\Scripts\activate
)

REM Run the content ingestion tool
python content_ingestion.py %*

REM Deactivate virtual environment
call venv\Scripts\deactivate
