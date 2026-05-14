@echo off
echo Starting Job AI Agent Streamlit Dashboard...
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

REM Start Streamlit app
echo Starting Streamlit dashboard on http://%STREAMLIT_HOST%:%STREAMLIT_PORT%
streamlit run app/web/app.py

pause
