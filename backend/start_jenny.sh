#!/bin/bash

# Kill all background processes if the script is stopped
trap "kill 0" EXIT

# Kill any existing process on port 8000 (FastAPI) and 5173 (Vite)
echo "🧹 Cleaning up existing ports..."
lsof -ti:8000,5173 | xargs kill -9 2>/dev/null

echo "------------------------------------------"
echo "🚀 Starting Jenny AI Ecosystem..."
echo "------------------------------------------"

# 1. Start Backend (FastAPI + Assistant)
echo "📡 [1/3] Starting Backend & Assistant..."
python3 main.py &
BACKEND_PID=$!

# Give backend a moment to start
sleep 3

# 2. Start Frontend (Vite)
echo "🎨 [2/3] Starting Frontend Dev Server..."
cd ui/frontend
npm run dev -- --no-open &
FRONTEND_PID=$!
cd ../..

# Wait for Vite server to be ready
sleep 4

# 3. Start Electron
echo "🖥️  [3/3] Starting Desktop Overlay (Electron)..."
echo "------------------------------------------"
cd ui/electron
npm start

# Keep the script running
wait $BACKEND_PID $FRONTEND_PID
