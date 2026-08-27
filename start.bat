@echo off
REM Local AI Assistant Startup Script for Windows

echo 🚀 Local AI Assistant
echo ====================
echo.

REM Run initialization
echo Setting up directories...
python init.py

echo.
echo Starting Docker services...
echo Pulling latest images...
docker compose up --pull always

echo.
echo ✓ Services running:
echo   - Ollama:    http://localhost:11434
echo   - Backend:   http://localhost:8000
echo   - Frontend:  http://localhost:5173
echo.
echo Open http://localhost:5173 in your browser
