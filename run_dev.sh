#!/bin/bash
echo "Starting Tahlil in development mode..."
echo ""
echo "This will start:"
echo "  1. Flask backend on http://localhost:5000"
echo "  2. Vite dev server on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start Flask in background
python app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Start Vite
cd frontend
npm run dev &
VITE_PID=$!
cd ..

echo ""
echo "Both servers are running!"
echo "Access the app at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for user interrupt
trap "kill $FLASK_PID $VITE_PID; exit" INT TERM
wait

