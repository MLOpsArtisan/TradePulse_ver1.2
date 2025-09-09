"""
ML Strategy - Trading strategy using machine learning predictions
"""
import logging
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml_model.model_service import ml_service

log = logging.getLogger(__name__)

class MLStrategy:
    def __init__(self, symbol: str, config: Dict):
        self.name = "ML Neural Network Strategy"
        self.symbol = symbol
        self.config = config
        
        # ML-specific configuration
        self.min_confidence = config.get('ml_min_confidence', 0.6)
        self.min_expected_return = config.get('ml_min_expected_return', 0.1)  # 0.1%
        self.use_regression_filter = config.get('ml_use_regression_filter', True)
        
    def analyze(self, rates) -> Optional[Dict]:
        """Analyze market using ML predictions"""
        try:
            # Check if ML model is available
            if not ml_service.is_loaded:
                log.warning("ML model not loaded, cannot generate ML signals")
                return None
            
            # Get ML prediction
            prediction = ml_service.predict(bars=len(rates) + 50)  # Use more bars for better context
            
            if not prediction:
                log.warning("Failed to get ML prediction")
                return None
            
            signal_type = prediction['signal']
            confidence = prediction['confidence']
            expected_return = prediction['expected_return']
            
            log.info(f"ML Prediction: {signal_type} (confidence: {confidence:.2%}, expected return: {expected_return:.2f}%)")
            
            # Apply confidence filter
            if confidence < self.min_confidence:
                log.info(f"ML signal confidence {confidence:.2%} below threshold {self.min_confidence:.2%}")
                return None
            
            # Apply expected return filter for BUY/SELL signals
            if signal_type in ['BUY', 'SELL']:
                if self.use_regression_filter:
                    if signal_type == 'BUY' and expected_return < self.min_expected_return:
                        log.info(f"BUY signal expected return {expected_return:.2f}% below threshold {self.min_expected_return:.2f}%")
                        return None
                    elif signal_type == 'SELL' and expected_return > -self.min_expected_return:
                        log.info(f"SELL signal expected return {expected_return:.2f}% above threshold {-self.min_expected_return:.2f}%")
                        return None
            
            # Skip HOLD signals unless explicitly enabled
            if signal_type == 'HOLD' and not self.config.get('ml_trade_hold_signals', False):
                log.info("HOLD signal ignored (ml_trade_hold_signals=False)")
                return None
            
            # Generate trading signal
            if signal_type in ['BUY', 'SELL']:
                current_price = prediction['current_price']
                
                # Calculate dynamic stop loss and take profit based on expected return
                if self.config.get('ml_dynamic_sl_tp', True):
                    # Use expected return to set more intelligent SL/TP
                    expected_move = abs(expected_return) / 100 * current_price
                    
                    if signal_type == 'BUY':
                        # For BUY: SL below current, TP above current
                        sl_distance = max(expected_move * 0.5, current_price * 0.001)  # At least 0.1%
                        tp_distance = max(expected_move * 1.5, current_price * 0.002)  # At least 0.2%
                    else:  # SELL
                        # For SELL: SL above current, TP below current
                        sl_distance = max(expected_move * 0.5, current_price * 0.001)
                        tp_distance = max(expected_move * 1.5, current_price * 0.002)
                    
                    # Convert to pips (assuming 4-digit broker for most pairs)
                    pip_size = 0.0001 if 'JPY' not in self.symbol else 0.01
                    sl_pips = int(sl_distance / pip_size)
                    tp_pips = int(tp_distance / pip_size)
                    
                    # Apply reasonable limits
                    sl_pips = max(10, min(sl_pips, 100))  # 10-100 pips
                    tp_pips = max(20, min(tp_pips, 200))  # 20-200 pips
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
                    'reason': f'ML Neural Network: {confidence:.1%} confidence, {expected_return:.2f}% expected return',
                    'ml_data': {
                        'signal_probabilities': prediction['signal_probabilities'],
                        'future_ohlc': prediction['future_ohlc'],
                        'model_version': prediction.get('model_version', '1.0')
                    }
                }
            
            return None
            
        except Exception as e:
            log.error(f"Error in ML strategy analysis: {e}")
            return None

def get_ml_strategy(symbol: str, config: Dict) -> MLStrategy:
    """Factory function to create ML strategy"""
    return MLStrategy(symbol, config)