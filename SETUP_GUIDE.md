# 🚀 TradePulse Setup Guide - Complete Installation

## 📋 **Prerequisites**

### **System Requirements:**
- **Windows 10/11** (for MetaTrader 5 integration)
- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **Node.js 16+** and **npm 8+**
- **MetaTrader 5** platform installed
- **Git** for cloning the repository

---

## 🔧 **Quick Setup (5 Minutes)**

### **1. Clone the Repository**
```bash
git clone <your-repository-url>
cd TradePulse
```

### **2. Backend Setup**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python candlestickData.py
```

The backend will start on `http://localhost:5000`

### **3. Frontend Setup**
```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will start on `http://localhost:3000`

---

## 🔧 **Detailed Setup Instructions**

### **Backend Configuration**

#### **Python Environment Setup:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Create isolated environment
python -m venv tradepulse-env

# Activate environment
tradepulse-env\Scripts\activate  # Windows
source tradepulse-env/bin/activate  # macOS/Linux

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

#### **MetaTrader 5 Setup:**
1. **Install MetaTrader 5** from official website
2. **Enable Algorithmic Trading** in MT5:
   - Tools → Options → Expert Advisors
   - Check "Allow automated trading"
   - Check "Allow DLL imports"
3. **Login to Demo/Live Account** in MT5

#### **Backend Dependencies:**
```bash
# Core dependencies installed via requirements.txt:
Flask==3.1.0                 # Web framework
Flask-SocketIO==5.5.1        # Real-time communication
MetaTrader5==5.0.4993        # MT5 integration
numpy==2.2.5                 # Mathematical operations
pandas==2.2.0                # Data manipulation
eventlet==0.39.1             # Async web server
```

### **Frontend Configuration**

#### **Node.js Setup:**
```bash
# Check Node.js version
node --version  # Should be 16+
npm --version   # Should be 8+

# If outdated, install latest LTS from nodejs.org
```

#### **React Dependencies:**
```bash
# Install all dependencies
npm install

# Key dependencies:
react ^18.2.0                # React framework
socket.io-client ^4.8.1      # Real-time WebSocket client
lightweight-charts ^5.0.6    # Trading charts
axios ^1.4.0                 # HTTP requests
react-router-dom ^7.6.0      # Navigation
```

---

## 🚀 **Running the Application**

### **Method 1: Manual Start (Development)**

#### **Terminal 1 - Backend:**
```bash
cd backend
python candlestickData.py
```
**Expected Output:**
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://[your-ip]:5000
MetaTrader5 initialized successfully
WebSocket server ready for connections
```

#### **Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```
**Expected Output:**
```
Compiled successfully!
Local:            http://localhost:3000
On Your Network:  http://[your-ip]:3000
```

### **Method 2: Quick Start Scripts**

#### **Windows Batch Files:**

**Create `start_backend.bat`:**
```batch
@echo off
echo Starting TradePulse Backend...
cd backend
venv\Scripts\activate
python candlestickData.py
pause
```

**Create `start_frontend.bat`:**
```batch
@echo off
echo Starting TradePulse Frontend...
cd frontend
npm start
pause
```

**Create `start_all.bat`:**
```batch
@echo off
echo Starting TradePulse Complete System...
start "" "start_backend.bat"
timeout /t 5
start "" "start_frontend.bat"
echo Both servers starting...
pause
```

#### **Linux/macOS Shell Scripts:**

**Create `start_backend.sh`:**
```bash
#!/bin/bash
echo "Starting TradePulse Backend..."
cd backend
source venv/bin/activate
python candlestickData.py
```

**Create `start_frontend.sh`:**
```bash
#!/bin/bash
echo "Starting TradePulse Frontend..."
cd frontend
npm start
```

---

## 🎯 **Verification Steps**

### **1. Backend Verification:**
Open `http://localhost:5000` in browser:
- Should see Flask welcome/status page
- Check console for MetaTrader5 connection status

### **2. Frontend Verification:**
Open `http://localhost:3000` in browser:
- Should see TradePulse login page
- No console errors in browser DevTools

### **3. System Integration Test:**
1. **Login** to the platform
2. **Start HFT Bot** with Moving Average strategy
3. **Check Trade History** for proper bot name display
4. **Verify SL/TP** application in trades
5. **Test Manual Close** button functionality

---

## 🔧 **Troubleshooting**

### **Common Backend Issues:**

#### **MetaTrader5 Connection Failed:**
```bash
# Error: MetaTrader5 package not found
pip install MetaTrader5==5.0.4993

# Error: MT5 not initialized
# Solution: Ensure MT5 is running and logged in
```

#### **Port Already in Use:**
```bash
# Error: Port 5000 already in use
# Solution: Kill existing process or change port
netstat -ano | findstr :5000
taskkill /PID <process-id> /F
```

#### **Module Import Errors:**
```bash
# Error: No module named 'flask'
# Solution: Activate virtual environment
venv\Scripts\activate
pip install -r requirements.txt
```

### **Common Frontend Issues:**

#### **Node Modules Missing:**
```bash
# Error: Module not found
# Solution: Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### **Port Conflicts:**
```bash
# Error: Port 3000 already in use
# Solution: Use different port
PORT=3001 npm start
```

#### **Build Errors:**
```bash
# Error: Build failed
# Solution: Clear cache and rebuild
npm run build
```

---

## 🎯 **Production Deployment**

### **Backend Production:**
```bash
# Install production WSGI server
pip install gunicorn

# Start production server
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 candlestickData:app
```

### **Frontend Production:**
```bash
# Build production bundle
npm run build

# Serve static files
npm install -g serve
serve -s build -l 3000
```

---

## 📦 **Full Dependency List**

### **Backend (Python):**
```txt
Flask==3.1.0                 # Web framework
flask-cors==5.0.1            # CORS handling
Flask-SocketIO==5.5.1        # WebSocket support
MetaTrader5==5.0.4993        # MT5 integration
numpy==2.2.5                 # Mathematical operations
pandas==2.2.0                # Data manipulation
eventlet==0.39.1             # Async server
python-socketio==5.13.0      # Socket communication
python-dateutil==2.9.0.post0 # Date handling
requests==2.31.0             # HTTP requests
pytz==2023.3                 # Timezone handling
```

### **Frontend (Node.js):**
```json
{
  "react": "^18.2.0",           // React framework
  "socket.io-client": "^4.8.1", // WebSocket client
  "lightweight-charts": "^5.0.6", // Trading charts
  "axios": "^1.4.0",            // HTTP client
  "react-router-dom": "^7.6.0", // Navigation
  "react-scripts": "5.0.1"      // Build tools
}
```

---

## ✅ **Success Indicators**

### **System is working correctly when:**
1. **✅ Backend**: Starts without errors, shows MT5 connection
2. **✅ Frontend**: Loads without console errors
3. **✅ Login**: Authentication works properly
4. **✅ HFT Bots**: Generate signals with SL/TP
5. **✅ Trade History**: Shows correct bot names
6. **✅ Manual Close**: Trade closure works
7. **✅ Real-time Updates**: Live price and trade updates

---

## 🎯 **Next Steps After Setup**

1. **Configure MetaTrader 5** with your broker account
2. **Test with Demo Account** before live trading
3. **Customize HFT Strategies** parameters
4. **Monitor Performance** in Trade History
5. **Scale to Multiple Symbols** as needed

**Your TradePulse HFT system is now ready for production trading!** 🚀


