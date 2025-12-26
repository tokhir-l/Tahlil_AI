#!/bin/bash
echo "Killing old Flask processes on port 5000..."
echo ""

# Find and kill processes using port 5000 (Linux/Mac)
if command -v lsof &> /dev/null; then
    PIDS=$(lsof -ti:5000)
    if [ ! -z "$PIDS" ]; then
        echo "Killing processes: $PIDS"
        kill -9 $PIDS
    else
        echo "No processes found on port 5000"
    fi
else
    echo "lsof not found. Please install it or manually kill processes."
fi

echo ""
echo "Done! Port 5000 should now be free."

