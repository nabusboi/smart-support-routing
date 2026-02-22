@echo off
REM Smart-Support Ticket Routing Engine - Run All
REM This script starts both the backend API and frontend development server

echo ================================================
echo Starting Smart-Support Ticket Routing Engine
echo ================================================
echo.

REM Start backend in a new window
echo Starting FastAPI Backend on port 8001...
start "Backend - FastAPI" cmd /k "python app.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo Starting Frontend on port 5173...
start "Frontend - React" cmd /k "cd frontend && npm run dev"

echo.
echo ================================================
echo Services started!
echo.
echo Backend API:    http://localhost:8001
echo Frontend:       http://localhost:5173
echo API Docs:       http://localhost:8001/docs
echo.
echo Press any key to exit (services will keep running)
echo ================================================
pause >nul
