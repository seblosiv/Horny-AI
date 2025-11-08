#!/bin/bash

# Quick start script for B2B Chat API

set -e

echo "🚀 B2B Chat API - Quick Start"
echo "=============================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration!"
fi

# Check if Docker is running (for Postgres/Redis)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Docker detected. Starting Postgres and Redis..."
    docker-compose up -d postgres redis
    echo "⏳ Waiting for services to be ready..."
    sleep 5
else
    echo "⚠️  Docker not found. Please start Postgres and Redis manually."
    echo "   Or install Docker and run: docker-compose up -d"
fi

# Initialize database
echo "🔧 Initializing database..."
python scripts/init_db.py

# Create test user
echo "👤 Creating test user..."
python scripts/create_test_user.py

echo ""
echo "✨ Setup complete!"
echo ""
echo "🚀 To start the API server:"
echo "   python app/main.py"
echo ""
echo "🎨 To start the admin console:"
echo "   streamlit run console/streamlit_app.py"
echo ""
echo "📖 API docs will be at: http://localhost:8000/docs"
echo "🖥️  Console will be at: http://localhost:8501"
echo ""
echo "🔑 Test credentials:"
echo "   Email: test@example.com"
echo "   Password: testpassword123"
echo ""
