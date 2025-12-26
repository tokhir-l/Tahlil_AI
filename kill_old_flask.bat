@echo off
echo Killing old Flask processes on port 5000...
echo.

REM Find and kill processes using port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo Killing process %%a...
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill all Python processes (be careful!)
echo.
echo Killing all Python processes...
taskkill /IM python.exe /F >nul 2>&1

echo.
echo Done! Port 5000 should now be free.
echo.
pause

