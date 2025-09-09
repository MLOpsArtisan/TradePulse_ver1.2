# 🤖 ML Model Integration for TradePulse

This document explains how to use the integrated machine learning model in your TradePulse trading platform.

## 📋 Overview

The ML integration includes:
- **Neural Network Model**: Multi-output CNN-LSTM architecture for signal classification and price prediction
- **Technical Indicators**: 12+ indicators including RSI, MACD, EMA, SMA, ATR
- **Real-time Predictions**: Live market analysis with confidence scores
- **Trading Integration**: ML strategy for automated trading
- **Web Interface**: React component for viewing predictions

## 🚀 Quick Start

### 1. Setup ML Environment

```bash
# Run the automated setup script
python setup_ml_model.py
```

This will:
- Install TensorFlow and required dependencies
- Train the model with your data
- Test the integration

### 2. Manual Setup (Alternative)

```bash
# Install ML dependencies
cd backend
pip install tensorflow==2.15.0 keras==2.15.0
pip install -r requirements.txt

# Train the model
python ml_model/train_model.py
```

### 3. Start the Application

```bash
# Terminal 1: Start backend
cd backend
python candlestickData.py

# Terminal 2: Start frontend
cd frontend
npm start
```

### 4. Access ML Predictions

1. Open http://localhost:3000
2. Login to the dashboard
3. Click the "ML Predictions" tab
4. Click "Get Prediction" to see live predictions

## 🧠 Model Architecture

### Neural Network Design
```
Input Layer (35 timesteps × 12 features)
    ↓
Conv1D Layer (64 filters, kernel=3) + BatchNorm + Dropout
    ↓
Conv1D Layer (64 filters, kernel=3) + BatchNorm + Dropout
    ↓
LSTM Layer (128 units) + Dropout
    ↓
Dense Layer (128 units) + Dropout
    ↓
┌─────────────────────┬─────────────────────┐
│  Classification     │    Regression       │
│  Head (3 classes)   │    Head (4 OHLC)    │
│  ↓                  │    ↓                │
│  Softmax Output     │    Linear Output    │
└─────────────────────┴─────────────────────┘
```

### Features Used
1. **OHLC Data**: Open, High, Low, Close prices
2. **Moving Averages**: EMA(14), SMA(20)
3. **MACD**: MACD line, Signal line, Histogram
4. **RSI**: 14-period Relative Strength Index
5. **ATR**: 14-period Average True Range

### Outputs
- **Classification**: BUY/SELL/HOLD signals with confidence
- **Regression**: Predicted next candle OHLC values
- **Expected Return**: Calculated profit/loss percentage

## 🔧 Configuration

### ML Strategy Parameters

Add these to your bot configuration:

```json
{
  "strategy_name": "ml_strategy",
  "ml_min_confidence": 0.6,
  "ml_min_expected_return": 0.1,
  "ml_use_regression_filter": true,
  "ml_dynamic_sl_tp": true,
  "ml_trade_hold_signals": false
}
```

### Parameter Descriptions

- `ml_min_confidence`: Minimum prediction confidence (0.0-1.0)
- `ml_min_expected_return`: Minimum expected return percentage
- `ml_use_regression_filter`: Use price prediction to filter signals
- `ml_dynamic_sl_tp`: Calculate SL/TP based on expected price movement
- `ml_trade_hold_signals`: Whether to trade on HOLD signals

## 📊 API Endpoints

### Get Model Status
```http
GET /api/ml/status
```

Response:
```json
{
  "success": true,
  "data": {
    "is_loaded": true,
    "model_available": true,
    "tensorflow_available": true,
    "symbol": "ETHUSD",
    "features": ["open", "high", "low", "close", "ema_14", ...],
    "sequence_length": 35
  }
}
```

### Get Prediction
```http
GET /api/ml/predict?bars=100
```

Response:
```json
{
  "success": true,
  "data": {
    "signal": "BUY",
    "confidence": 0.85,
    "signal_probabilities": {
      "hold": 0.1,
      "buy": 0.85,
      "sell": 0.05
    },
    "future_ohlc": {
      "open": 3250.0,
      "high": 3275.0,
      "low": 3240.0,
      "close": 3270.0
    },
    "current_price": 3245.50,
    "expected_return": 0.75,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Train Model
```http
POST /api/ml/train
Content-Type: application/json

{
  "data_path": "/path/to/training/data.csv"
}
```

## 🎯 Using ML Strategy in Trading Bot

### 1. Via Web Interface

1. Go to Trading Bot tab
2. Select "ML Neural Network Strategy" 
3. Configure ML parameters
4. Start the bot

### 2. Via API

```python
# Start bot with ML strategy
import requests

response = requests.post('http://localhost:5000/bot/start', json={
    'strategy': 'ml_strategy',
    'config': {
        'ml_min_confidence': 0.7,
        'ml_min_expected_return': 0.2,
        'auto_trading_enabled': True
    }
})
```

### 3. Programmatically

```python
from backend.trading_bot.bot_manager import TradingBotManager

bot = TradingBotManager()
bot.config.update({
    'strategy_name': 'ml_strategy',
    'ml_min_confidence': 0.6,
    'auto_trading_enabled': True
})
bot.start_bot('ml_strategy')
```

## 📈 Model Performance

### Training Metrics
- **Classification Accuracy**: Measures signal prediction accuracy
- **Regression MAE**: Mean Absolute Error for price predictions
- **F1 Score**: Balanced measure of precision and recall

### Live Performance
- **Signal Confidence**: Real-time confidence scores
- **Expected vs Actual Returns**: Track prediction accuracy
- **Win Rate**: Percentage of profitable signals

## 🔍 Monitoring & Debugging

### Check Model Status
```python
from backend.ml_model.model_service import ml_service

status = ml_service.get_model_status()
print(f"Model loaded: {status['is_loaded']}")
print(f"Features: {status['features']}")
```

### Test Predictions
```python
prediction = ml_service.predict(bars=100)
if prediction:
    print(f"Signal: {prediction['signal']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
else:
    print("Prediction failed")
```

### View Logs
```bash
# Backend logs show ML activity
tail -f backend/logs/trading.log | grep ML
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. TensorFlow Not Available
```
Error: TensorFlow not available for training
```
**Solution**: Install TensorFlow
```bash
pip install tensorflow==2.15.0
```

#### 2. Model Not Loaded
```
Warning: ML model not loaded, cannot generate ML signals
```
**Solution**: Train the model first
```bash
cd backend
python ml_model/train_model.py
```

#### 3. Insufficient Data
```
Error: Insufficient market data for prediction
```
**Solution**: Ensure MT5 is connected and has historical data

#### 4. Memory Issues
```
Error: ResourceExhaustedError
```
**Solution**: Reduce batch size or use CPU version
```bash
pip install tensorflow-cpu==2.15.0
```

### Performance Optimization

#### 1. Faster Predictions
- Reduce sequence length (default: 35)
- Use fewer features
- Enable GPU acceleration

#### 2. Better Accuracy
- Increase training data
- Add more technical indicators
- Tune hyperparameters

#### 3. Resource Management
- Use model caching
- Implement prediction batching
- Monitor memory usage

## 📚 Advanced Usage

### Custom Features
```python
# Add custom indicators to model_service.py
def create_custom_indicators(self, df):
    # Add your custom technical indicators
    df['custom_indicator'] = your_calculation(df)
    return df
```

### Model Retraining
```python
# Retrain with new data
ml_service.train_model('/path/to/new/data.csv')
```

### Multiple Timeframes
```python
# Train separate models for different timeframes
ml_service_1h = MLModelService(symbol="ETHUSD_1H")
ml_service_4h = MLModelService(symbol="ETHUSD_4H")
```

## 🔐 Security Considerations

1. **Model Files**: Store trained models securely
2. **API Access**: Implement authentication for ML endpoints
3. **Data Privacy**: Ensure training data is protected
4. **Resource Limits**: Set prediction rate limits

## 📞 Support

If you encounter issues:

1. Check the logs in `backend/logs/`
2. Verify MT5 connection
3. Ensure all dependencies are installed
4. Test with the provided examples

## 🎉 Success!

Your ML model is now integrated! The system will:
- ✅ Generate real-time predictions
- ✅ Provide confidence scores
- ✅ Enable automated ML trading
- ✅ Display results in the web interface

Happy trading with AI! 🚀📈