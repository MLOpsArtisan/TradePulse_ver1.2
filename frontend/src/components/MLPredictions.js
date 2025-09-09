import React, { useState, useEffect, useCallback } from 'react';
import './MLPredictions.css';

const MLPredictions = () => {
  const [mlStatus, setMlStatus] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  // Fetch ML model status
  const fetchMLStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/ml/status`);
      const data = await response.json();
      
      if (data.success) {
        setMlStatus(data.data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch ML status');
      console.error('ML Status Error:', err);
    }
  }, [API_BASE]);

  // Fetch ML prediction
  const fetchPrediction = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/ml/predict`);
      const data = await response.json();
      
      if (data.success) {
        setPrediction(data.data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch prediction');
      console.error('Prediction Error:', err);
    } finally {
      setLoading(false);
    }
  }, [API_BASE]);

  // Train model
  const trainModel = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/ml/train`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('Model training completed successfully!');
        fetchMLStatus(); // Refresh status
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to train model');
      console.error('Training Error:', err);
    } finally {
      setLoading(false);
    }
  };



  // Auto-refresh predictions
  useEffect(() => {
    let interval;
    if (autoRefresh && mlStatus?.is_loaded) {
      interval = setInterval(fetchPrediction, 30000); // Every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, mlStatus, fetchPrediction]);

  // Initial load
  useEffect(() => {
    fetchMLStatus();
  }, [fetchMLStatus]);

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'BUY': return '#00ff88';
      case 'SELL': return '#ff4444';
      case 'HOLD': return '#ffaa00';
      default: return '#888';
    }
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="ml-predictions">
      <div className="ml-header">
        <h3>🤖 ML Neural Network Predictions</h3>
        <div className="ml-controls">
          <button 
            onClick={fetchPrediction} 
            disabled={loading || !mlStatus?.is_loaded}
            className="btn-predict"
          >
            {loading ? '⏳' : '🔮'} Get Prediction
          </button>
          <button 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn-auto ${autoRefresh ? 'active' : ''}`}
            disabled={!mlStatus?.is_loaded}
          >
            🔄 Auto Refresh
          </button>
        </div>
      </div>

      {/* ML Status */}
      <div className="ml-status">
        <div className="status-item">
          <span className="label">Model Status:</span>
          <span className={`status ${mlStatus?.is_loaded ? 'loaded' : 'not-loaded'}`}>
            {mlStatus?.is_loaded ? '✅ Loaded' : '❌ Not Loaded'}
          </span>
        </div>
        <div className="status-item">
          <span className="label">TensorFlow:</span>
          <span className={`status ${mlStatus?.tensorflow_available ? 'available' : 'unavailable'}`}>
            {mlStatus?.tensorflow_available ? '✅ Available' : '❌ Unavailable'}
          </span>
        </div>
        {mlStatus?.features && (
          <div className="status-item">
            <span className="label">Features:</span>
            <span className="features">{mlStatus.features.length} indicators</span>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {/* Model Training */}
      {!mlStatus?.is_loaded && mlStatus?.tensorflow_available && (
        <div className="training-section">
          <p>No trained model found. Train a new model:</p>
          <button onClick={trainModel} disabled={loading} className="btn-train">
            {loading ? '⏳ Training...' : '🎯 Train Model'}
          </button>
        </div>
      )}

      {/* Prediction Results */}
      {prediction && (
        <div className="prediction-results">
          <div className="main-prediction">
            <div className="signal-display">
              <div 
                className="signal-badge"
                style={{ backgroundColor: getSignalColor(prediction.signal) }}
              >
                {prediction.signal}
              </div>
              <div className="confidence">
                Confidence: {formatPercentage(prediction.confidence)}
              </div>
            </div>
            
            <div className="expected-return">
              <span className="label">Expected Return:</span>
              <span 
                className={`value ${prediction.expected_return >= 0 ? 'positive' : 'negative'}`}
              >
                {prediction.expected_return >= 0 ? '+' : ''}{prediction.expected_return.toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Signal Probabilities */}
          <div className="probabilities">
            <h4>Signal Probabilities</h4>
            <div className="prob-bars">
              {Object.entries(prediction.signal_probabilities).map(([signal, prob]) => (
                <div key={signal} className="prob-bar">
                  <span className="prob-label">{signal.toUpperCase()}</span>
                  <div className="prob-container">
                    <div 
                      className="prob-fill"
                      style={{ 
                        width: `${prob * 100}%`,
                        backgroundColor: getSignalColor(signal.toUpperCase())
                      }}
                    />
                    <span className="prob-value">{formatPercentage(prob)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Future OHLC Prediction */}
          <div className="future-ohlc">
            <h4>Predicted Next Candle</h4>
            <div className="ohlc-grid">
              <div className="ohlc-item">
                <span className="ohlc-label">Open:</span>
                <span className="ohlc-value">${prediction.future_ohlc.open.toFixed(2)}</span>
              </div>
              <div className="ohlc-item">
                <span className="ohlc-label">High:</span>
                <span className="ohlc-value">${prediction.future_ohlc.high.toFixed(2)}</span>
              </div>
              <div className="ohlc-item">
                <span className="ohlc-label">Low:</span>
                <span className="ohlc-value">${prediction.future_ohlc.low.toFixed(2)}</span>
              </div>
              <div className="ohlc-item">
                <span className="ohlc-label">Close:</span>
                <span className="ohlc-value">${prediction.future_ohlc.close.toFixed(2)}</span>
              </div>
            </div>
            <div className="current-price">
              Current Price: ${prediction.current_price.toFixed(2)}
            </div>
          </div>

          <div className="prediction-meta">
            <small>
              Last updated: {new Date(prediction.timestamp).toLocaleTimeString()} | 
              Model v{prediction.model_version}
            </small>
          </div>
        </div>
      )}
    </div>
  );
};

export default MLPredictions;