@echo off
echo Starting Job AI Agent API Server...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please create it first:
    echo python -m venv venv
    echo venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found. Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

REM Start the API server
echo Starting FastAPI server on http://%API_HOST%:%API_PORT%
python -m app.main

pause
