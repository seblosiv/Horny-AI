#!/bin/bash

# Start all services (API + Console)

set -e

echo "🚀 Starting B2B Chat API & Console..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/quickstart.sh first"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Start API in background
echo "🔧 Starting API server..."
python app/main.py &
API_PID=$!

# Wait a bit for API to start
sleep 3

# Start Streamlit console
echo "🎨 Starting admin console..."
streamlit run console/streamlit_app.py &
CONSOLE_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "📖 API: http://localhost:8000/docs"
echo "🖥️  Console: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $API_PID $CONSOLE_PID
