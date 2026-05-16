#!/bin/bash

# Kill all background processes if the script is stopped
trap "kill 0" EXIT

echo "------------------------------------------"
echo "🚀 Starting Ritu AI Ecosystem..."
echo "------------------------------------------"

# 1. Start Backend (FastAPI + Assistant)
echo "📡 [1/3] Starting Backend & Assistant..."
python main.py &
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
