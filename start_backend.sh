#!/bin/bash

echo "========================================"
echo " TradePulse Backend Startup Script"
echo "========================================"
echo

cd backend

echo "Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt

echo
echo "Starting TradePulse Backend Server..."
echo "Backend will be available at: http://localhost:5000"
echo
echo "Press Ctrl+C to stop the server"
echo "========================================"

python candlestickData.py


