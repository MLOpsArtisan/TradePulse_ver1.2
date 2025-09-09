"""
ML Model Service - Integrates the trained neural network for trading predictions
"""
import numpy as np
import pandas as pd
import logging
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import MetaTrader5 as mt5

# TensorFlow imports
try:
    import tensorflow as tf
    import keras
    from keras.models import load_model
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not available. ML predictions will be disabled.")

log = logging.getLogger(__name__)

class MLModelService:
    def __init__(self, symbol="ETHUSD"):
        self.symbol = symbol
        self.model = None
        self.feature_scaler = None
        self.target_scaler = None
        self.is_loaded = False
        self.seq_len = 35  # From your model
        self.features = []
        
        # Model paths
        self.model_dir = os.path.join(os.path.dirname(__file__), 'saved_models')
        self.model_path = os.path.join(self.model_dir, f'{symbol}_model.h5')
        self.scaler_path = os.path.join(self.model_dir, f'{symbol}_scalers.pkl')
        
        # Create directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize if model exists
        if TF_AVAILABLE:
            self.load_model()
    
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators from OHLC data"""
        try:
            # EMA
            df['ema_14'] = df['close'].ewm(span=14, adjust=False).mean()
            
            # SMA
            df['sma_20'] = df['close'].rolling(window=20).mean()
            
            # MACD
            fast_ema = df['close'].ewm(span=12, adjust=False).mean()
            slow_ema = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = fast_ema - slow_ema
            df['macd_sig'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_sig']
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift()).abs()
            low_close = (df['low'] - df['close'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr_14'] = tr.rolling(14).mean()
            
            # RSI
            delta = df['close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            ma_up = up.ewm(alpha=1/14, adjust=False).mean()
            ma_down = down.ewm(alpha=1/14, adjust=False).mean()
            rs = ma_up / (ma_down + 1e-9)
            df['rsi_14'] = 100 - (100 / (1 + rs))
            
            # Fill NaN values
            df = df.bfill().ffill()
            
            return df
            
        except Exception as e:
            log.error(f"Error creating technical indicators: {e}")
            return df
    
    def prepare_features(self, df: pd.DataFrame) -> List[str]:
        """Prepare feature columns for the model"""
        # Base OHLC features
        base_features = ['open', 'high', 'low', 'close']
        
        # Technical indicators
        indicator_features = ['ema_14', 'sma_20', 'macd', 'macd_sig', 'macd_hist', 'atr_14', 'rsi_14']
        
        # Combine all features that exist in the dataframe
        features = []
        for feature in base_features + indicator_features:
            if feature in df.columns:
                features.append(feature)
        
        return features
    
    def get_market_data(self, bars: int = 100) -> Optional[pd.DataFrame]:
        """Get market data from MT5"""
        try:
            if not mt5.initialize():
                log.error("Failed to initialize MT5")
                return None
            
            # Get rates
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, bars)
            if rates is None or len(rates) == 0:
                log.error(f"No data received for {self.symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.set_index('time')
            
            # Rename columns to match expected format
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            return df[['open', 'high', 'low', 'close']]
            
        except Exception as e:
            log.error(f"Error getting market data: {e}")
            return None
    
    def train_model(self, data_path: Optional[str] = None) -> bool:
        """Train the ML model with the provided architecture"""
        if not TF_AVAILABLE:
            log.error("TensorFlow not available for training")
            return False
        
        try:
            # Get training data
            if data_path and os.path.exists(data_path):
                df = pd.read_csv(data_path)
                df['start_time'] = pd.to_datetime(df['start_time'])
                df = df.sort_values('start_time').reset_index(drop=True)
            else:
                # Use live data for training (not recommended for production)
                df = self.get_market_data(5000)
                if df is None:
                    return False
                df = df.reset_index()
                df.rename(columns={'time': 'start_time'}, inplace=True)
                
                # Create dummy signals for training (replace with your actual signals)
                df['type'] = np.random.choice(['hold', 'buy', 'sell'], len(df), p=[0.7, 0.15, 0.15])
            
            # Create technical indicators
            df = self.create_technical_indicators(df)
            
            # Prepare features
            self.features = self.prepare_features(df)
            log.info(f"Using features: {self.features}")
            
            # Create labels
            label_map = {'hold': 0, 'buy': 1, 'sell': 2}
            if 'type' in df.columns:
                df['signal_label'] = df['type'].map(label_map)
            else:
                # Create dummy labels based on price movement
                df['price_change'] = df['close'].pct_change()
                df['signal_label'] = 0  # Default to hold
                df.loc[df['price_change'] > 0.001, 'signal_label'] = 1  # Buy
                df.loc[df['price_change'] < -0.001, 'signal_label'] = 2  # Sell
            
            # Create future targets for regression
            df[['t_open', 't_high', 't_low', 't_close']] = df[['open', 'high', 'low', 'close']].shift(-1)
            df.dropna(inplace=True)
            
            # Prepare scalers
            self.feature_scaler = StandardScaler()
            self.target_scaler = MinMaxScaler()
            
            # Scale features and targets
            X_all = self.feature_scaler.fit_transform(df[self.features].values)
            y_reg_all = self.target_scaler.fit_transform(df[['t_open', 't_high', 't_low', 't_close']].values)
            y_cls_all = df['signal_label'].values.astype(int)
            
            # Create sequences
            X_seq, y_reg_seq, y_cls_seq = [], [], []
            for i in range(len(X_all) - self.seq_len):
                X_seq.append(X_all[i:i+self.seq_len])
                y_reg_seq.append(y_reg_all[i+self.seq_len])
                y_cls_seq.append(y_cls_all[i+self.seq_len])
            
            X_seq = np.array(X_seq)
            y_reg_seq = np.array(y_reg_seq)
            y_cls_seq = np.array(y_cls_seq)
            
            log.info(f"Training data shape: {X_seq.shape}")
            
            # Build model architecture (from your code)
            self.model = self._build_model(X_seq.shape[1:])
            
            # Train the model
            history = self.model.fit(
                X_seq,
                [y_cls_seq, y_reg_seq],
                epochs=10,
                batch_size=32,
                validation_split=0.2,
                verbose=1
            )
            
            # Save model and scalers
            self.save_model()
            
            log.info("Model training completed successfully")
            return True
            
        except Exception as e:
            log.error(f"Error training model: {e}")
            return False
    
    def _build_model(self, input_shape):
        """Build the neural network model architecture"""
        import keras
        from keras.layers import Input, Conv1D, LSTM, Dense, Dropout, BatchNormalization
        from keras.models import Model
        from keras import regularizers
        
        l2 = 1e-4
        inp = Input(shape=input_shape, name='input')
        
        # Convolutional layers
        x = Conv1D(filters=64, kernel_size=3, activation='relu',
                   kernel_regularizer=regularizers.l2(l2))(inp)
        x = BatchNormalization()(x)
        x = Dropout(0.2)(x)
        x = Conv1D(filters=64, kernel_size=3, activation='relu',
                   kernel_regularizer=regularizers.l2(l2))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.2)(x)
        
        # LSTM layer
        x = LSTM(128, kernel_regularizer=regularizers.l2(l2),
                 recurrent_regularizer=regularizers.l2(l2))(x)
        x = Dropout(0.25)(x)
        x = Dense(128, activation='relu', kernel_regularizer=regularizers.l2(l2))(x)
        x = Dropout(0.2)(x)
        
        # Classification head
        cls = Dense(64, activation='relu', kernel_regularizer=regularizers.l2(l2))(x)
        cls_out = Dense(3, activation='softmax', name='classification')(cls)
        
        # Regression head
        reg = Dense(64, activation='relu', kernel_regularizer=regularizers.l2(l2))(x)
        reg_out = Dense(4, activation='linear', name='regression')(reg)
        
        model = Model(inputs=inp, outputs=[cls_out, reg_out])
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-3),
            loss={'classification': 'sparse_categorical_crossentropy', 'regression': 'huber'},
            loss_weights={'classification': 1.0, 'regression': 1.0},
            metrics={'classification': 'accuracy', 'regression': 'mae'}
        )
        
        return model
    
    def save_model(self):
        """Save the trained model and scalers"""
        try:
            if self.model is not None:
                self.model.save(self.model_path)
                log.info(f"Model saved to {self.model_path}")
            
            if self.feature_scaler is not None and self.target_scaler is not None:
                scalers = {
                    'feature_scaler': self.feature_scaler,
                    'target_scaler': self.target_scaler,
                    'features': self.features
                }
                with open(self.scaler_path, 'wb') as f:
                    pickle.dump(scalers, f)
                log.info(f"Scalers saved to {self.scaler_path}")
            
            self.is_loaded = True
            
        except Exception as e:
            log.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load the trained model and scalers"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                # Load model
                self.model = load_model(self.model_path)
                log.info(f"Model loaded from {self.model_path}")
                
                # Load scalers
                with open(self.scaler_path, 'rb') as f:
                    scalers = pickle.load(f)
                    self.feature_scaler = scalers['feature_scaler']
                    self.target_scaler = scalers['target_scaler']
                    self.features = scalers['features']
                
                log.info(f"Scalers loaded from {self.scaler_path}")
                self.is_loaded = True
                
            else:
                log.info("No saved model found. Train a model first.")
                
        except Exception as e:
            log.error(f"Error loading model: {e}")
            self.is_loaded = False
    
    def predict(self, bars: int = 100) -> Optional[Dict]:
        """Make predictions using the loaded model"""
        if not self.is_loaded or self.model is None:
            log.warning("Model not loaded. Cannot make predictions.")
            return None
        
        try:
            # Get market data
            df = self.get_market_data(bars)
            if df is None or len(df) < self.seq_len:
                log.error("Insufficient market data for prediction")
                return None
            
            # Create technical indicators
            df = self.create_technical_indicators(df)
            
            # Prepare features
            if not all(feature in df.columns for feature in self.features):
                log.error("Missing required features in market data")
                return None
            
            # Scale features
            X = self.feature_scaler.transform(df[self.features].values)
            
            # Create sequence (use the last seq_len bars)
            X_seq = X[-self.seq_len:].reshape(1, self.seq_len, -1)
            
            # Make prediction
            cls_pred, reg_pred = self.model.predict(X_seq, verbose=0)
            
            # Process classification prediction
            cls_probs = cls_pred[0]
            cls_label = np.argmax(cls_probs)
            cls_confidence = float(cls_probs[cls_label])
            
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal = signal_map[cls_label]
            
            # Process regression prediction (future OHLC)
            reg_pred_inv = self.target_scaler.inverse_transform(reg_pred)
            future_ohlc = {
                'open': float(reg_pred_inv[0][0]),
                'high': float(reg_pred_inv[0][1]),
                'low': float(reg_pred_inv[0][2]),
                'close': float(reg_pred_inv[0][3])
            }
            
            # Get current price for comparison
            current_price = float(df['close'].iloc[-1])
            
            # Calculate expected return
            expected_return = (future_ohlc['close'] - current_price) / current_price * 100
            
            return {
                'signal': signal,
                'confidence': cls_confidence,
                'signal_probabilities': {
                    'hold': float(cls_probs[0]),
                    'buy': float(cls_probs[1]),
                    'sell': float(cls_probs[2])
                },
                'future_ohlc': future_ohlc,
                'current_price': current_price,
                'expected_return': expected_return,
                'timestamp': datetime.now().isoformat(),
                'model_version': '1.0'
            }
            
        except Exception as e:
            log.error(f"Error making prediction: {e}")
            return None
    
    def get_model_status(self) -> Dict:
        """Get the current status of the ML model"""
        return {
            'is_loaded': self.is_loaded,
            'model_available': self.model is not None,
            'tensorflow_available': TF_AVAILABLE,
            'symbol': self.symbol,
            'features': self.features if self.features else [],
            'sequence_length': self.seq_len,
            'model_path_exists': os.path.exists(self.model_path),
            'scaler_path_exists': os.path.exists(self.scaler_path)
        }

# Global ML service instance
ml_service = MLModelService()