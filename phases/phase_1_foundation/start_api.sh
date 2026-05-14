#!/bin/bash

echo "🚀 Starting Job AI Agent API Server..."
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

# Start the API server
echo "🌐 Starting FastAPI server..."
echo "   API:           http://localhost:8000"
echo "   API Docs:      http://localhost:8000/docs"
echo
python -m app.main
