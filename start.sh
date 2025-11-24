#!/bin/bash

# SiteSense Application Startup Script

echo "🚀 Starting SiteSense Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create it first with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the FastAPI server
echo ""
echo "✅ Starting FastAPI server..."
echo "📍 API: http://localhost:8000"
echo "📍 Frontend: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
