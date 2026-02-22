#!/bin/bash

# Smart-Support Ticket Routing Engine - Run All
# This script starts both the backend API and frontend development server

echo "🚀 Starting Smart-Support Ticket Routing Engine"
echo "================================================"

# Start backend (in background)
echo "📦 Starting FastAPI Backend on port 8000..."
cd "$(dirname "$0")"
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting Frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo "   Backend API: http://localhost:8000"
echo "   Frontend:    http://localhost:5173"
echo "   API Docs:    http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
