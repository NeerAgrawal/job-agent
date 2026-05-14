#!/bin/bash

echo "🚀 Starting Job AI Agent Streamlit Dashboard..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Start Streamlit app
echo "🌐 Starting Streamlit dashboard..."
echo "   Dashboard:     http://localhost:8501"
echo
streamlit run app/web/app.py
