#!/bin/bash

echo "🚀 Setting up Job AI Agent..."
echo

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+' || echo "")
if [[ $(echo "$python_version >= 3.11" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data

# Initialize database
echo "🗄️ Initializing database..."
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

echo
echo "🎉 Setup complete!"
echo
echo "🚀 To start the applications:"
echo "   API Server:     ./scripts/start_api.sh"
echo "   Streamlit App:  ./scripts/start_streamlit.sh"
echo
echo "🌐 Access points:"
echo "   API:           http://localhost:8000"
echo "   API Docs:      http://localhost:8000/docs"
echo "   Dashboard:     http://localhost:8501"
