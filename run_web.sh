#!/bin/bash

# Tahlil Web Application Startup Script for Linux/Mac

echo ""
echo "============================================"
echo "   Tahlil Web Application"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from python.org"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python: $python_version"

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Installing required packages..."
    pip3 install flask flask-cors
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install packages"
        exit 1
    fi
fi

# Create directories if they don't exist
mkdir -p data
mkdir -p runs

# Check if frontend exists
if [ ! -d "frontend" ]; then
    echo "ERROR: frontend directory not found"
    echo "Make sure you're in the Tahlil root directory"
    exit 1
fi

echo ""
echo "All requirements met!"
echo ""
echo "Starting Tahlil Web Application..."
echo ""
echo "Website will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
