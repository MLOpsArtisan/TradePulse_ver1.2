"""
Enhanced ML Strategy - More aggressive signal generation with MT5 integration
"""
import logging
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ml_model.model_service import ml_service

log = logging.getLogger(__name__)

class EnhancedMLStrategy:
    def __init__(self, symbol: str, config: Dict):
        self.name = "Enhanced ML Neural Network Strategy"
        self.symbol = symbol
        self.config = config
        
        # Enhanced ML-specific configuration - MORE AGGRESSIVE
        self.min_confidence = config.get('ml_min_confidence', 0.4)  # Lowered from 0.6 to 0.4
        self.min_expected_return = config.get('ml_min_expected_return', 0.05)  # Lowered from 0.1 to 0.05
        self.use_regression_filter = config.get('ml_use_regression_filter', False)  # Disabled by default
        self.enable_hold_trading = config.get('ml_trade_hold_signals', True)  # Enable HOLD trading
        self.signal_boost_mode = config.get('ml_signal_boost_mode', True)  # New: boost weak signals
        
        log.info(f"Enhanced ML Strategy initialized with aggressive settings:")
        log.info(f"  - Min Confidence: {self.min_confidence:.1%}")
        log.info(f"  - Min Expected Return: {self.min_expected_return:.2f}%")
        log.info(f"  - Regression Filter: {self.use_regression_filter}")
        log.info(f"  - HOLD Trading: {self.enable_hold_trading}")
        log.info(f"  - Signal Boost: {self.signal_boost_mode}")
        
    def analyze(self, rates) -> Optional[Dict]:
        """Enhanced analysis with more aggressive signal generation"""
        try:
            # Check if ML model is available
            if not ml_service.is_loaded:
                log.warning("ML model not loaded, cannot generate ML signals")
                return None
            
            # Get ML prediction
            prediction = ml_service.predict(bars=len(rates) + 50)
            
            if not prediction:
                log.warning("Failed to get ML prediction")
                return None
            
            signal_type = prediction['signal']
            confidence = prediction['confidence']
            expected_return = prediction['expected_return']
            signal_probs = prediction['signal_probabilities']
            
            log.info(f"🤖 Enhanced ML Analysis:")
            log.info(f"   Primary Signal: {signal_type} (confidence: {confidence:.2%})")
            log.info(f"   Expected Return: {expected_return:.2f}%")
            log.info(f"   Probabilities: BUY={signal_probs['buy']:.1%}, SELL={signal_probs['sell']:.1%}, HOLD={signal_probs['hold']:.1%}")
            
            # ENHANCED SIGNAL GENERATION LOGIC
            final_signal = None
            final_confidence = confidence
            
            # 1. Check primary signal with relaxed confidence
            if confidence >= self.min_confidence:
                if signal_type in ['BUY', 'SELL']:
                    # Apply relaxed expected return filter
                    if not self.use_regression_filter or self._check_expected_return(signal_type, expected_return):
                        final_signal = signal_type
                        log.info(f"✅ Primary {signal_type} signal accepted (confidence: {confidence:.2%})")
                elif signal_type == 'HOLD' and self.enable_hold_trading:
                    # Convert strong HOLD to opposite of market trend
                    final_signal = self._convert_hold_signal(signal_probs, expected_return)
                    if final_signal:
                        log.info(f"✅ HOLD converted to {final_signal} signal")
            
            # 2. SIGNAL BOOST MODE - Look for secondary signals
            if not final_signal and self.signal_boost_mode:
                final_signal, final_confidence = self._boost_weak_signals(signal_probs, expected_return)
                if final_signal:
                    log.info(f"🚀 Boosted {final_signal} signal (confidence: {final_confidence:.2%})")
            
            # 3. Generate trading signal if we have one
            if final_signal and final_signal in ['BUY', 'SELL']:
                return self._create_trading_signal(final_signal, prediction, final_confidence)
            
            # Log why no signal was generated
            if not final_signal:
                log.info(f"❌ No signal generated - confidence {confidence:.2%} < {self.min_confidence:.2%} or filters failed")
            
            return None
            
        except Exception as e:
            log.error(f"Error in Enhanced ML strategy analysis: {e}")
            return None
    
    def _check_expected_return(self, signal_type: str, expected_return: float) -> bool:
        """Check if expected return meets minimum threshold"""
        if signal_type == 'BUY' and expected_return < self.min_expected_return:
            log.info(f"BUY signal expected return {expected_return:.2f}% below threshold {self.min_expected_return:.2f}%")
            return False
        elif signal_type == 'SELL' and expected_return > -self.min_expected_return:
            log.info(f"SELL signal expected return {expected_return:.2f}% above threshold {-self.min_expected_return:.2f}%")
            return False
        return True
    
    def _convert_hold_signal(self, signal_probs: Dict, expected_return: float) -> Optional[str]:
        """Convert HOLD signal to BUY/SELL based on probabilities and expected return"""
        buy_prob = signal_probs['buy']
        sell_prob = signal_probs['sell']
        
        # If BUY and SELL probabilities are close, use expected return to decide
        prob_diff = abs(buy_prob - sell_prob)
        
        if prob_diff < 0.1:  # Very close probabilities
            if expected_return > 0.02:  # Positive expected return
                return 'BUY'
            elif expected_return < -0.02:  # Negative expected return
                return 'SELL'
        else:
            # Use the higher probability if it's significant
            if buy_prob > sell_prob and buy_prob > 0.25:
                return 'BUY'
            elif sell_prob > buy_prob and sell_prob > 0.25:
                return 'SELL'
        
        return None
    
    def _boost_weak_signals(self, signal_probs: Dict, expected_return: float) -> tuple:
        """Boost weak signals that might still be profitable"""
        buy_prob = signal_probs['buy']
        sell_prob = signal_probs['sell']
        hold_prob = signal_probs['hold']
        
        # Look for signals with at least 30% probability
        min_boost_prob = 0.30
        
        # Check for BUY signals
        if buy_prob >= min_boost_prob and buy_prob > sell_prob:
            # Boost confidence based on expected return
            boosted_confidence = buy_prob
            if expected_return > 0:
                boosted_confidence = min(0.8, buy_prob + (expected_return / 100) * 2)
            
            if boosted_confidence >= self.min_confidence:
                return 'BUY', boosted_confidence
        
        # Check for SELL signals
        if sell_prob >= min_boost_prob and sell_prob > buy_prob:
            # Boost confidence based on expected return
            boosted_confidence = sell_prob
            if expected_return < 0:
                boosted_confidence = min(0.8, sell_prob + abs(expected_return / 100) * 2)
            
            if boosted_confidence >= self.min_confidence:
                return 'SELL', boosted_confidence
        
        # Check for contrarian signals (when HOLD is very high but expected return suggests otherwise)
        if hold_prob > 0.6:
            if expected_return > 0.1:  # Strong positive expected return despite HOLD
                return 'BUY', 0.5
            elif expected_return < -0.1:  # Strong negative expected return despite HOLD
                return 'SELL', 0.5
        
        return None, 0
    
    def _create_trading_signal(self, signal_type: str, prediction: Dict, confidence: float) -> Dict:
        """Create the final trading signal with enhanced parameters"""
        current_price = prediction['current_price']
        expected_return = prediction['expected_return']
        
        # Calculate dynamic stop loss and take profit
        if self.config.get('ml_dynamic_sl_tp', True):
            # More aggressive SL/TP based on expected return and volatility
            expected_move = abs(expected_return) / 100 * current_price
            
            # Base SL/TP on expected move but with minimum values
            if signal_type == 'BUY':
                sl_distance = max(expected_move * 0.3, current_price * 0.0008)  # Tighter SL
                tp_distance = max(expected_move * 2.0, current_price * 0.0015)  # Bigger TP
            else:  # SELL
                sl_distance = max(expected_move * 0.3, current_price * 0.0008)
                tp_distance = max(expected_move * 2.0, current_price * 0.0015)
            
            # Convert to pips (assuming 4-digit broker for most pairs)
            pip_size = 0.0001 if 'JPY' not in self.symbol else 0.01
            sl_pips = max(8, min(int(sl_distance / pip_size), 50))  # 8-50 pips
            tp_pips = max(15, min(int(tp_distance / pip_size), 100))  # 15-100 pips
        else:
            # Use configured SL/TP
            sl_pips = self.config.get('stop_loss_pips', 15)
            tp_pips = self.config.get('take_profit_pips', 30)
        
        return {
            'type': signal_type,
            'price': current_price,
            'confidence': confidence,
            'expected_return': expected_return,
            'stop_loss_pips': sl_pips,
            'take_profit_pips': tp_pips,
            'reason': f'Enhanced ML: {confidence:.1%} confidence, {expected_return:.2f}% expected return',
            'ml_data': {
                'signal_probabilities': prediction['signal_probabilities'],
                'future_ohlc': prediction['future_ohlc'],
                'model_version': prediction.get('model_version', '1.0'),
                'enhanced_mode': True
            }
        }

def get_enhanced_ml_strategy(symbol: str, config: Dict) -> EnhancedMLStrategy:
    """Factory function to create Enhanced ML strategy"""
    return EnhancedMLStrategy(symbol, config)