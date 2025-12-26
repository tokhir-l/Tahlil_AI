#!/bin/bash
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..
echo ""
echo "Build complete! Flask will now serve the React app from frontend/dist/"
echo "You can now run: python app.py"

