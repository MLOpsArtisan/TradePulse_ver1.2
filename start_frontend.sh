#!/bin/bash

echo "========================================"
echo " TradePulse Frontend Startup Script"
echo "========================================"
echo

cd frontend

echo "Checking Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo "Dependencies found, checking for updates..."
    npm install
fi

echo
echo "Starting TradePulse Frontend Server..."
echo "Frontend will be available at: http://localhost:3000"
echo
echo "Press Ctrl+C to stop the server"
echo "========================================"

npm start


