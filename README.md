# TradePulse 📈

> Advanced High-Frequency Trading (HFT) Platform with Real-Time Market Analysis

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![MetaTrader5](https://img.shields.io/badge/MetaTrader5-5.0+-orange.svg)](https://www.metatrader5.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Features

### Core Trading Engine
- **High-Frequency Trading (HFT)** - Sub-second analysis and execution
- **Multiple Trading Strategies** - MACD, RSI, Stochastic, Breakout, VWAP, Bollinger Bands
- **Real-Time Tick Processing** - Advanced tick data analysis with fallback mechanisms
- **Automated Risk Management** - Configurable SL/TP with manual and ratio-based modes
- **Multi-Bot Management** - Run multiple strategies simultaneously

### Advanced Analytics
- **Real-Time Candlestick Charts** - Interactive price visualization
- **Performance Metrics** - Comprehensive trading statistics
- **Live Market Data** - WebSocket-based real-time updates
- **Trade History** - Detailed execution logs and analysis

### Professional Interface
- **Modern Web Dashboard** - React-based responsive UI
- **Real-Time Notifications** - Instant trade alerts and system status
- **Configuration Management** - Easy strategy and risk parameter setup
- **Multi-Timeframe Analysis** - 1M, 5M, 15M, 1H, 4H, 1D charts

## 🛠️ Technology Stack

### Backend
- **Python 3.8+** - Core application logic
- **Flask** - Web framework and API
- **Flask-SocketIO** - Real-time WebSocket communication
- **MetaTrader5** - Trading platform integration
- **NumPy/Pandas** - Data processing and analysis

### Frontend
- **React.js** - Modern UI framework
- **Socket.IO** - Real-time client communication
- **Chart.js/Plotly** - Interactive charting
- **Bootstrap** - Responsive design

### Trading Integration
- **MetaTrader 5** - Primary trading platform
- **Real-Time Data Feeds** - Live market data processing
- **Order Management** - Automated trade execution

## 📦 Installation

### Prerequisites
1. **Python 3.8+** installed
2. **MetaTrader 5** platform installed and configured
3. **Trading account** with MT5 broker
4. **Git** for version control

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/TradePulse.git
cd TradePulse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python start_backend.py
```

### Detailed Setup
1. **MetaTrader 5 Setup**:
   - Install MT5 from official website
   - Create demo/live trading account
   - Enable algorithmic trading
   - Configure symbol permissions

2. **Python Environment**:
   ```bash
   # Install required packages
   pip install MetaTrader5 Flask Flask-SocketIO numpy pandas
   
   # Verify MT5 connection
   python -c "import MetaTrader5 as mt5; print('MT5 Available:', mt5.initialize())"
   ```

## 🎯 Usage

### Starting the Platform
```bash
# Start backend server
python start_backend.py

# Access web interface
# Open browser: http://localhost:3000
```

### Creating Trading Bots
1. **Navigate to Trading Dashboard**
2. **Click "Start New Bot"**
3. **Configure Parameters**:
   - Symbol (e.g., ETHUSD, EURUSD)
   - Strategy (MACD, RSI, Breakout, etc.)
   - Risk Management (SL/TP, lot size)
   - Analysis interval

4. **Enable Auto Trading**
5. **Monitor Performance**

### HFT Mode Configuration
```javascript
{
  "mode": "HFT",
  "analysis_interval": 5,        // seconds
  "tick_lookback": 30,          // seconds
  "min_signal_confidence": 0.6,
  "max_orders_per_minute": 5,
  "use_manual_sl_tp": true,     // ✅ RECOMMENDED
  "stop_loss_pips": 20,
  "take_profit_pips": 40
}
```

## 📊 Trading Strategies

### 1. MACD Strategy
- **Signal**: Moving Average Convergence Divergence crossovers
- **Timeframe**: 1M - 1H
- **Best for**: Trending markets

### 2. RSI Strategy  
- **Signal**: Relative Strength Index overbought/oversold
- **Timeframe**: 5M - 4H
- **Best for**: Range-bound markets

### 3. Breakout Strategy
- **Signal**: Price breakouts from support/resistance
- **Timeframe**: 1M - 1H  
- **Best for**: Volatile markets

### 4. Stochastic Strategy
- **Signal**: Stochastic oscillator crossovers
- **Timeframe**: 1M - 1H
- **Best for**: Sideways markets

### 5. VWAP Strategy
- **Signal**: Volume Weighted Average Price deviations
- **Timeframe**: 1M - 1H
- **Best for**: Intraday trading

## ⚙️ Configuration

### Risk Management
```python
RISK_CONFIG = {
    "max_risk_per_trade": 2.0,      # % of account
    "max_daily_loss": 5.0,          # % of account  
    "max_concurrent_trades": 3,
    "stop_loss_pips": 20,
    "take_profit_pips": 40,
    "trailing_stop": False
}
```

### HFT Settings
```python
HFT_CONFIG = {
    "analysis_interval": 5,          # seconds
    "tick_lookback": 30,            # seconds
    "min_signal_confidence": 0.6,
    "max_orders_per_minute": 5,
    "cooldown_after_trade": 5       # seconds
}
```

## 🚨 Important Notes

### Risk Disclaimer
- **Trading involves substantial risk** of loss
- **Past performance does not guarantee future results**
- **Only trade with money you can afford to lose**
- **Test thoroughly on demo accounts first**

### System Requirements
- **Stable internet connection** for real-time data
- **MetaTrader 5** platform running
- **Sufficient account balance** for margin requirements
- **VPS recommended** for 24/7 operation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/yourusername/TradePulse/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/TradePulse/issues)

## 🏆 Acknowledgments

- MetaTrader 5 for trading platform integration
- Flask community for web framework
- NumPy/Pandas for data processing
- Chart.js for visualization components

---

**⚠️ Disclaimer**: This software is for educational and research purposes. Trading financial instruments carries risk. Always test on demo accounts first and never risk more than you can afford to lose.