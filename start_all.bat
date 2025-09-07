@echo off
echo ========================================
echo  TradePulse Complete System Startup
echo ========================================
echo.

echo Starting Backend Server...
start "TradePulse Backend" cmd /k "start_backend.bat"

echo Waiting for backend to initialize...
timeout /t 8 /nobreak

echo Starting Frontend Server...
start "TradePulse Frontend" cmd /k "start_frontend.bat"

echo.
echo ========================================
echo  TradePulse System Starting...
echo.
echo  Backend:  http://localhost:5000
echo  Frontend: http://localhost:3000
echo.
echo  Wait for both servers to fully start
echo  then open http://localhost:3000 in browser
echo ========================================
echo.

pause


