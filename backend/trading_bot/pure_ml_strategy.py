"""
Pure ML Strategy - Uses only the trained model's predictions without modifications
This strategy respects the original model training and doesn't add artificial logic
"""
import logging
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml_model.model_service import ml_service

log = logging.getLogger(__name__)

class PureMLStrategy:
    def __init__(self, symbol: str, config: Dict):
        self.name = "Pure ML Neural Network Strategy"
        self.symbol = symbol
        self.config = config
        
        # Pure ML configuration - respects model's original training
        self.min_confidence = config.get('ml_min_confidence', 0.6)  # Original threshold
        self.min_expected_return = config.get('ml_min_expected_return', 0.1)  # Original threshold
        self.use_regression_filter = config.get('ml_use_regression_filter', True)  # Use regression as trained
        self.trade_only_model_signals = config.get('ml_trade_only_model_signals', True)  # Pure model signals only
        
        log.info(f"Pure ML Strategy initialized - respecting original model training:")
        log.info(f"  - Min Confidence: {self.min_confidence:.1%}")
        log.info(f"  - Min Expected Return: {self.min_expected_return:.2f}%")
        log.info(f"  - Use Regression Filter: {self.use_regression_filter}")
        log.info(f"  - Trade Only Model Signals: {self.trade_only_model_signals}")
        
    def analyze(self, rates) -> Optional[Dict]:
        """Pure analysis using only the trained model's predictions"""
        try:
            # Check if ML model is available
            if not ml_service.is_loaded:
                log.warning("ML model not loaded, cannot generate ML signals")
                return None
            
            # Get ML prediction - pure model output
            prediction = ml_service.predict(bars=len(rates) + 50)
            
            if not prediction:
                log.warning("Failed to get ML prediction")
                return None
            
            signal_type = prediction['signal']
            confidence = prediction['confidence']
            expected_return = prediction['expected_return']
            signal_probs = prediction['signal_probabilities']
            
            log.info(f"🤖 Pure ML Model Output:")
            log.info(f"   Model Signal: {signal_type}")
            log.info(f"   Model Confidence: {confidence:.2%}")
            log.info(f"   Expected Return: {expected_return:.2f}%")
            log.info(f"   Raw Probabilities: BUY={signal_probs['buy']:.1%}, SELL={signal_probs['sell']:.1%}, HOLD={signal_probs['hold']:.1%}")
            
            # PURE MODEL APPROACH: Only trade when model explicitly says BUY or SELL
            if signal_type == 'HOLD':
                log.info(f"✅ Model predicts HOLD - respecting model's decision (no artificial conversion)")
                return None
            
            # Only proceed if model explicitly predicts BUY or SELL
            if signal_type not in ['BUY', 'SELL']:
                log.info(f"❌ Model output '{signal_type}' is not a trading signal")
                return None
            
            # Apply confidence filter (as per original model training)
            if confidence < self.min_confidence:
                log.info(f"❌ Model confidence {confidence:.2%} below threshold {self.min_confidence:.2%}")
                return None
            
            # Apply regression filter if enabled (as per original model training)
            if self.use_regression_filter:
                if signal_type == 'BUY' and expected_return < self.min_expected_return:
                    log.info(f"❌ BUY signal expected return {expected_return:.2f}% below threshold {self.min_expected_return:.2f}%")
                    return None
                elif signal_type == 'SELL' and expected_return > -self.min_expected_return:
                    log.info(f"❌ SELL signal expected return {expected_return:.2f}% above threshold {-self.min_expected_return:.2f}%")
                    return None
            
            # If we reach here, the model has made a clear BUY/SELL prediction that meets all criteria
            log.info(f"✅ Pure ML Signal Accepted: {signal_type} with {confidence:.2%} confidence")
            
            return self._create_pure_trading_signal(signal_type, prediction)
            
        except Exception as e:
            log.error(f"Error in Pure ML strategy analysis: {e}")
            return None
    
    def _create_pure_trading_signal(self, signal_type: str, prediction: Dict) -> Dict:
        """Create trading signal based purely on model output"""
        current_price = prediction['current_price']
        confidence = prediction['confidence']
        expected_return = prediction['expected_return']
        
        # Use model's regression output for risk management
        future_ohlc = prediction['future_ohlc']
        
        # Calculate SL/TP based on model's price predictions (not artificial logic)
        if self.config.get('ml_use_model_prices_for_sltp', True):
            # Use the model's predicted future prices for SL/TP calculation
            predicted_high = future_ohlc['high']
            predicted_low = future_ohlc['low']
            predicted_close = future_ohlc['close']
            
            if signal_type == 'BUY':
                # For BUY: SL below current, TP at predicted high
                sl_price = max(predicted_low * 0.999, current_price * 0.995)  # Conservative SL
                tp_price = min(predicted_high * 1.001, current_price * 1.01)   # Conservative TP
            else:  # SELL
                # For SELL: SL above current, TP at predicted low
                sl_price = min(predicted_high * 1.001, current_price * 1.005)  # Conservative SL
                tp_price = max(predicted_low * 0.999, current_price * 0.99)    # Conservative TP
            
            # Convert to pips
            pip_size = 0.0001 if 'JPY' not in self.symbol else 0.01
            sl_pips = max(10, min(int(abs(current_price - sl_price) / pip_size), 100))
            tp_pips = max(15, min(int(abs(tp_price - current_price) / pip_size), 200))
        else:
            # Use configured SL/TP
            sl_pips = self.config.get('stop_loss_pips', 20)
            tp_pips = self.config.get('take_profit_pips', 40)
        
        return {
            'type': signal_type,
            'price': current_price,
            'confidence': confidence,
            'expected_return': expected_return,
            'stop_loss_pips': sl_pips,
            'take_profit_pips': tp_pips,
            'reason': f'Pure ML Model: {signal_type} signal with {confidence:.1%} confidence (no artificial modifications)',
            'ml_data': {
                'signal_probabilities': prediction['signal_probabilities'],
                'future_ohlc': prediction['future_ohlc'],
                'model_version': prediction.get('model_version', '1.0'),
                'pure_model_output': True,
                'artificial_conversion': False
            }
        }

def get_pure_ml_strategy(symbol: str, config: Dict) -> PureMLStrategy:
    """Factory function to create Pure ML strategy"""
    return PureMLStrategy(symbol, config)