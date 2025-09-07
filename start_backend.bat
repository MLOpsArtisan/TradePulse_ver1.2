@echo off
echo ========================================
echo  TradePulse Backend Startup Script
echo ========================================
echo.

cd backend

echo Checking virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo Starting TradePulse Backend Server...
echo Backend will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================

python candlestickData.py

pause


