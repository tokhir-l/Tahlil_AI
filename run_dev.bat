@echo off
echo Starting Tahlil in development mode...
echo.
echo This will start:
echo   1. Flask backend on http://localhost:5000
echo   2. Vite dev server on http://localhost:3000
echo.
echo Press Ctrl+C to stop both servers
echo.

start "Flask Backend" cmd /k "python app.py"
timeout /t 3 /nobreak >nul
cd frontend
start "Vite Dev Server" cmd /k "npm run dev"
cd ..

echo.
echo Both servers are starting...
echo Access the app at: http://localhost:3000
echo.

pause

