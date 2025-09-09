"""
Trading Strategies for the Bot
This file contains different trading strategies that can be used by the bot.
"""
import MetaTrader5 as mt5
import numpy as np
import logging
import time
from typing import Dict, Optional, List
from datetime import datetime

log = logging.getLogger(__name__)

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, symbol: str = "ETHUSD"):
        self.symbol = symbol
        self.name = "base_strategy"
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """
        Analyze market data and return trading signal
        Returns: Dict with signal info or None
        """
        raise NotImplementedError("Subclasses must implement analyze method")
        
    def get_name(self) -> str:
        return self.name

class MovingAverageCrossover(BaseStrategy):
    """Enhanced Moving Average Crossover Strategy with configurable periods"""
    
    def __init__(self, symbol: str = "ETHUSD", ma_fast: int = 3, ma_slow: int = 8, 
                 use_ema: bool = True, diagnostic_mode: bool = False):
        super().__init__(symbol)
        self.name = "ma_crossover"
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.use_ema = use_ema
        self.diagnostic_mode = diagnostic_mode
        
        # Diagnostic mode: ultra-responsive periods
        if self.diagnostic_mode:
            self.ma_fast = 2   # Ultra-fast for immediate testing
            self.ma_slow = 4   # Very short for rapid signals
            self.use_ema = True  # Force EMA for maximum responsiveness
            log.info(f"🧪 MA Diagnostic Mode: Fast={self.ma_fast}, Slow={self.ma_slow}, EMA={self.use_ema}")
        
        # OPTIMIZED: More responsive default settings for better signal generation
        self.ma_fast = max(2, self.ma_fast)    # Minimum 2 for responsiveness
        self.ma_slow = max(4, self.ma_slow)    # Minimum 4 for trend detection
        
    def calculate_ma(self, prices: np.ndarray, period: int) -> float:
        """Calculate moving average (SMA or EMA)"""
        if len(prices) < period:
            return np.mean(prices)  # Use all available data
            
        if self.use_ema:
            # Exponential Moving Average
            multiplier = 2 / (period + 1)
            ema = prices[-period]  # Start with oldest price in period
            for price in prices[-period+1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            return ema
        else:
            # Simple Moving Average
            return np.mean(prices[-period:])
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """
        Generate signal based on moving average crossover with enhanced detection
        """
        try:
            # More lenient minimum data requirement
            min_data_needed = max(self.ma_slow + 2, 10)
            if len(rates) < min_data_needed:
                log.debug(f"MA: Insufficient data {len(rates)} < {min_data_needed}")
                return None
                
            # Extract close prices
            close_prices = np.array([rate[4] for rate in rates])
            
            # Calculate current MAs
            short_ma = self.calculate_ma(close_prices, self.ma_fast)
            long_ma = self.calculate_ma(close_prices, self.ma_slow)
            
            # Calculate previous MAs for crossover detection
            if len(close_prices) >= self.ma_slow + 1:
                prev_short_ma = self.calculate_ma(close_prices[:-1], self.ma_fast)
                prev_long_ma = self.calculate_ma(close_prices[:-1], self.ma_slow)
            else:
                # Use available data for previous calculation
                if len(close_prices) >= 2:
                    prev_short_ma = self.calculate_ma(close_prices[:-1], min(self.ma_fast, len(close_prices)-1))
                    prev_long_ma = self.calculate_ma(close_prices[:-1], min(self.ma_slow, len(close_prices)-1))
                else:
                    return None
            
            current_price = close_prices[-1]
            
            # Calculate MA difference and change
            ma_diff = short_ma - long_ma
            prev_ma_diff = prev_short_ma - prev_long_ma
            diff_change = ma_diff - prev_ma_diff
            
            # Enhanced logging with trend info
            ma_type = "EMA" if self.use_ema else "SMA"
            trend = "BULLISH" if ma_diff > 0 else "BEARISH"
            convergence = "CONVERGING" if abs(ma_diff) < abs(prev_ma_diff) else "DIVERGING"
            
            log.info(f"📊 {ma_type} Status: Fast={short_ma:.4f}, Slow={long_ma:.4f}, Diff={ma_diff:.4f} [{trend}] [{convergence}]")
            
            signal = None
            
            # ENHANCED CROSSOVER DETECTION with MORE SENSITIVE CONDITIONS
            # Check for actual sign change in MA difference OR strong momentum
            crossover_threshold = 0.01  # Small threshold to catch near-crossovers
            momentum_threshold = abs(ma_diff) * 0.1  # 10% of current difference
            
            # BULLISH CONDITIONS (more sensitive)
            if (prev_ma_diff <= crossover_threshold and ma_diff > crossover_threshold) or \
               (ma_diff > 0 and diff_change > momentum_threshold and short_ma > long_ma):
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.75 if ma_diff > crossover_threshold else 0.65,
                    'strategy': self.name,
                    'short_ma': short_ma,
                    'long_ma': long_ma,
                    'ma_diff': ma_diff,
                    'diff_change': diff_change,
                    'reason': f'{ma_type} Bullish Signal (Fast={short_ma:.4f}, Slow={long_ma:.4f})'
                }
                log.info(f"🚀 {ma_type} BULLISH SIGNAL: Fast {short_ma:.4f} vs Slow {long_ma:.4f} (diff: {prev_ma_diff:.4f}→{ma_diff:.4f}, change: {diff_change:.4f})")
            
            # BEARISH CONDITIONS (more sensitive)
            elif (prev_ma_diff >= -crossover_threshold and ma_diff < -crossover_threshold) or \
                 (ma_diff < 0 and diff_change < -momentum_threshold and short_ma < long_ma):
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.75 if ma_diff < -crossover_threshold else 0.65,
                    'strategy': self.name,
                    'short_ma': short_ma,
                    'long_ma': long_ma,
                    'ma_diff': ma_diff,
                    'diff_change': diff_change,
                    'reason': f'{ma_type} Bearish Signal (Fast={short_ma:.4f}, Slow={long_ma:.4f})'
                }
                log.info(f"🔻 {ma_type} BEARISH SIGNAL: Fast {short_ma:.4f} vs Slow {long_ma:.4f} (diff: {prev_ma_diff:.4f}→{ma_diff:.4f}, change: {diff_change:.4f})")
            
            else:
                # No crossover, provide diagnostic info
                if ma_diff > 0:
                    if diff_change > 0:
                        log.info(f"📊 {ma_type}: Bullish trend strengthening (diff: {ma_diff:.4f}, change: +{diff_change:.4f})")
                    else:
                        log.info(f"📊 {ma_type}: Bullish trend weakening (diff: {ma_diff:.4f}, change: {diff_change:.4f})")
                else:
                    if diff_change < 0:
                        log.info(f"📊 {ma_type}: Bearish trend strengthening (diff: {ma_diff:.4f}, change: {diff_change:.4f})")
                    else:
                        log.info(f"📊 {ma_type}: Bearish trend weakening (diff: {ma_diff:.4f}, change: +{diff_change:.4f})")
            
            return signal
            
        except Exception as e:
            log.error(f"Error in MA crossover analysis: {e}")
            return None

class RSIStrategy(BaseStrategy):
    """Enhanced RSI strategy with crossing logic and configurable thresholds"""
    
    def __init__(self, symbol: str = "ETHUSD", period: int = 8, rsi_buy_threshold: float = 40, 
                 rsi_sell_threshold: float = 60, use_crossing: bool = True, diagnostic_mode: bool = False):
        super().__init__(symbol)
        self.name = "rsi_strategy"
        self.period = period
        self.rsi_buy_threshold = rsi_buy_threshold  # OPTIMIZED: Default 40 vs 35
        self.rsi_sell_threshold = rsi_sell_threshold  # OPTIMIZED: Default 60 vs 65
        self.use_crossing = use_crossing
        self.diagnostic_mode = diagnostic_mode
        self.last_rsi = None  # Track previous RSI for crossing detection
        
        # Diagnostic mode: ultra-responsive settings
        if self.diagnostic_mode:
            self.period = 6  # Faster RSI calculation
            self.rsi_buy_threshold = 45  # Even more sensitive for quick signals
            self.rsi_sell_threshold = 55  # Even more sensitive for quick signals
            log.info(f"🧪 RSI Diagnostic Mode: Period={self.period}, BUY<{self.rsi_buy_threshold}, SELL>{self.rsi_sell_threshold}")
        
        # OPTIMIZED: More responsive default settings for better signal generation
        log.info(f"📊 RSI Strategy initialized: Period={self.period}, BUY<{self.rsi_buy_threshold}, SELL>{self.rsi_sell_threshold}, Crossing={self.use_crossing}")
        
    def calculate_rsi(self, prices: np.ndarray) -> float:
        """Calculate RSI value"""
        if len(prices) < 2:
            return 50.0
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Use available data up to period
        use_period = min(self.period, len(gains))
        if use_period == 0:
            return 50.0
            
        avg_gain = np.mean(gains[-use_period:])
        avg_loss = np.mean(losses[-use_period:])
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate signal based on RSI levels and crossing logic"""
        try:
            if len(rates) < max(2, self.period // 2):  # More lenient minimum
                log.debug(f"RSI: Insufficient data {len(rates)} < {max(2, self.period // 2)}")
                return None
                
            close_prices = np.array([rate[4] for rate in rates])
            current_price = close_prices[-1]
            
            # Calculate current and previous RSI
            current_rsi = self.calculate_rsi(close_prices)
            
            # Calculate previous RSI if we have enough data
            prev_rsi = None
            if len(close_prices) >= 3:
                prev_rsi = self.calculate_rsi(close_prices[:-1])
            
            # Always log current RSI status with enhanced details
            if current_rsi < self.rsi_buy_threshold:
                status = f"OVERSOLD ({current_rsi:.1f} < {self.rsi_buy_threshold})"
            elif current_rsi > self.rsi_sell_threshold:
                status = f"OVERBOUGHT ({current_rsi:.1f} > {self.rsi_sell_threshold})"
            else:
                status = f"NEUTRAL ({current_rsi:.1f})"
            
            crossing_info = ""
            if prev_rsi is not None:
                rsi_change = current_rsi - prev_rsi
                crossing_info = f" [Δ{rsi_change:+.1f}]"
            
            log.info(f"📊 RSI Status: {status}{crossing_info}")
            
            signal = None
            
            if self.use_crossing and prev_rsi is not None:
                # ENHANCED CROSSING LOGIC: More sophisticated and sensitive signal generation
                rsi_change = current_rsi - prev_rsi
                
                # BULLISH CONDITIONS (enhanced sensitivity)
                # 1. Traditional cross up from oversold
                # 2. Strong upward momentum when RSI is low
                # 3. Bounce from extreme oversold levels
                if ((prev_rsi <= self.rsi_buy_threshold and current_rsi > self.rsi_buy_threshold) or
                    (current_rsi < self.rsi_buy_threshold + 5 and rsi_change > 3) or
                    (current_rsi < 25 and rsi_change > 2)):  # Extreme oversold bounce
                    
                    confidence = 0.85 if prev_rsi <= self.rsi_buy_threshold and current_rsi > self.rsi_buy_threshold else 0.75
                    signal = {
                        'type': 'BUY',
                        'price': current_price,
                        'confidence': confidence,
                        'strategy': self.name,
                        'rsi': current_rsi,
                        'prev_rsi': prev_rsi,
                        'rsi_change': rsi_change,
                        'reason': f'RSI Bullish Signal ({prev_rsi:.1f}→{current_rsi:.1f}, Δ{rsi_change:+.1f})'
                    }
                    log.info(f"🚀 RSI BULLISH SIGNAL: {prev_rsi:.1f}→{current_rsi:.1f} (change: {rsi_change:+.1f}, threshold: {self.rsi_buy_threshold})")
                
                # BEARISH CONDITIONS (enhanced sensitivity)
                # 1. Traditional cross down from overbought
                # 2. Strong downward momentum when RSI is high
                # 3. Drop from extreme overbought levels
                elif ((prev_rsi >= self.rsi_sell_threshold and current_rsi < self.rsi_sell_threshold) or
                      (current_rsi > self.rsi_sell_threshold - 5 and rsi_change < -3) or
                      (current_rsi > 75 and rsi_change < -2)):  # Extreme overbought drop
                    
                    confidence = 0.85 if prev_rsi >= self.rsi_sell_threshold and current_rsi < self.rsi_sell_threshold else 0.75
                    signal = {
                        'type': 'SELL',
                        'price': current_price,
                        'confidence': confidence,
                        'strategy': self.name,
                        'rsi': current_rsi,
                        'prev_rsi': prev_rsi,
                        'rsi_change': rsi_change,
                        'reason': f'RSI Bearish Signal ({prev_rsi:.1f}→{current_rsi:.1f}, Δ{rsi_change:+.1f})'
                    }
                    log.info(f"🔻 RSI BEARISH SIGNAL: {prev_rsi:.1f}→{current_rsi:.1f} (change: {rsi_change:+.1f}, threshold: {self.rsi_sell_threshold})")
                
                else:
                    # Enhanced diagnostic info
                    if current_rsi < self.rsi_buy_threshold:
                        log.info(f"📊 RSI: Still oversold {current_rsi:.1f}, waiting for cross above {self.rsi_buy_threshold}")
                    elif current_rsi > self.rsi_sell_threshold:
                        log.info(f"📊 RSI: Still overbought {current_rsi:.1f}, waiting for cross below {self.rsi_sell_threshold}")
                    else:
                        distance_to_buy = current_rsi - self.rsi_buy_threshold
                        distance_to_sell = self.rsi_sell_threshold - current_rsi
                        if distance_to_buy < distance_to_sell:
                            log.info(f"📊 RSI: {current_rsi:.1f} is {distance_to_buy:.1f} points above buy level ({self.rsi_buy_threshold})")
                        else:
                            log.info(f"📊 RSI: {current_rsi:.1f} is {distance_to_sell:.1f} points below sell level ({self.rsi_sell_threshold})")
            
            else:
                # LEVEL-BASED LOGIC: Fallback to original behavior
                if current_rsi < self.rsi_buy_threshold:
                    signal = {
                        'type': 'BUY',
                        'price': current_price,
                        'confidence': 0.7,
                        'strategy': self.name,
                        'rsi': current_rsi,
                        'reason': f'RSI Oversold ({current_rsi:.2f})'
                    }
                    log.info(f"🚀 RSI BUY: RSI {current_rsi:.1f} is oversold (< {self.rsi_buy_threshold})")
                
                elif current_rsi > self.rsi_sell_threshold:
                    signal = {
                        'type': 'SELL',
                        'price': current_price,
                        'confidence': 0.7,
                        'strategy': self.name,
                        'rsi': current_rsi,
                        'reason': f'RSI Overbought ({current_rsi:.2f})'
                    }
                    log.info(f"🔻 RSI SELL: RSI {current_rsi:.1f} is overbought (> {self.rsi_sell_threshold})")
            
            # Store for next iteration
            self.last_rsi = current_rsi
            
            return signal
            
        except Exception as e:
            log.error(f"Error in RSI analysis: {e}")
            return None

class BreakoutStrategy(BaseStrategy):
    """Price breakout strategy based on support/resistance levels"""
    
    def __init__(self, symbol: str = "ETHUSD", lookback_period: int = 6, breakout_threshold: float = 0.0005):
        super().__init__(symbol)
        self.name = "breakout_strategy"
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold  # OPTIMIZED: Increased from 0.0002 to 0.0005 for more signals
        
        # Log initialization for debugging
        log.info(f"📊 Breakout Strategy initialized: Lookback={self.lookback_period}, Threshold={self.breakout_threshold*100:.3f}%")
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate signal based on price breakouts"""
        try:
            if len(rates) < self.lookback_period + 1:
                return None
                
            # Get recent data
            recent_rates = rates[-self.lookback_period:]
            high_prices = np.array([rate[2] for rate in recent_rates])
            low_prices = np.array([rate[3] for rate in recent_rates])
            close_prices = np.array([rate[4] for rate in recent_rates])
            
            current_price = close_prices[-1]
            
            # Calculate support and resistance levels
            resistance = np.max(high_prices[:-1])  # Exclude current candle
            support = np.min(low_prices[:-1])      # Exclude current candle
            
            signal = None
            
            # Calculate distances for enhanced detection
            distance_to_resistance = (resistance - current_price) / current_price
            distance_to_support = (current_price - support) / current_price
            
            # ENHANCED BREAKOUT DETECTION with multiple conditions
            # 1. Traditional breakout above resistance
            if current_price > resistance * (1 + self.breakout_threshold):
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'resistance': resistance,
                    'support': support,
                    'reason': f'Breakout above resistance ({current_price:.4f} > {resistance:.4f})'
                }
                log.info(f"🚀 BREAKOUT BUY: Price {current_price:.4f} broke above resistance {resistance:.4f}")
            
            # 2. Near-resistance with momentum (approaching breakout)
            elif distance_to_resistance < 0.002 and current_price > close_prices[-2]:  # Within 0.2% and rising
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.65,
                    'strategy': self.name,
                    'resistance': resistance,
                    'support': support,
                    'reason': f'Approaching resistance breakout ({current_price:.4f} near {resistance:.4f})'
                }
                log.info(f"📈 APPROACHING BREAKOUT BUY: Price {current_price:.4f} approaching resistance {resistance:.4f}")
            
            # 3. Traditional breakdown below support
            elif current_price < support * (1 - self.breakout_threshold):
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'resistance': resistance,
                    'support': support,
                    'reason': f'Breakdown below support ({current_price:.4f} < {support:.4f})'
                }
                log.info(f"🔻 BREAKDOWN SELL: Price {current_price:.4f} broke below support {support:.4f}")
            
            # 4. Near-support with downward momentum (approaching breakdown)
            elif distance_to_support < 0.002 and current_price < close_prices[-2]:  # Within 0.2% and falling
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.65,
                    'strategy': self.name,
                    'resistance': resistance,
                    'support': support,
                    'reason': f'Approaching support breakdown ({current_price:.4f} near {support:.4f})'
                }
                log.info(f"📉 APPROACHING BREAKDOWN SELL: Price {current_price:.4f} approaching support {support:.4f}")
            
            else:
                # Enhanced diagnostic logging
                log.info(f"📊 Breakout Analysis: Price={current_price:.4f}, Support={support:.4f}, Resistance={resistance:.4f}")
                log.info(f"📊 Distances: To resistance={distance_to_resistance*100:.3f}%, To support={distance_to_support*100:.3f}%")
            
            return signal
            
        except Exception as e:
            log.error(f"Error in breakout analysis: {e}")
            return None

class AlwaysSignalStrategy(BaseStrategy):
    """Strategy that ALWAYS generates signals for immediate testing"""
    
    def __init__(self, symbol: str = "ETHUSD"):
        super().__init__(symbol)
        self.name = "always_signal"
        self.signal_count = 0
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Always generate a signal for testing"""
        try:
            if len(rates) < 1:
                return None
                
            current_price = float(rates[-1][4])
            self.signal_count += 1
            
            # Alternate between BUY and SELL
            signal_type = 'BUY' if self.signal_count % 2 == 1 else 'SELL'
            
            signal = {
                'type': signal_type,
                'price': current_price,
                'confidence': 0.9,
                'strategy': self.name,
                'reason': f'Always {signal_type} Signal #{self.signal_count}'
            }
            
            log.info(f"⚡ AlwaysSignal GENERATED: {signal}")
            return signal
            
        except Exception as e:
            log.error(f"❌ Error in always signal strategy: {e}")
            return None

class TestStrategy(BaseStrategy):
    """Test strategy that generates frequent signals for testing"""
    
    def __init__(self, symbol: str = "ETHUSD"):
        super().__init__(symbol)
        self.name = "test_strategy"
        self.last_signal_time = 0
        self.signal_interval = 15  # ULTRA-OPTIMIZED: Generate signal every 15 seconds for rapid testing
        self.signal_count = 0  # Track total signals generated
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate alternating buy/sell signals for testing"""
        try:
            if len(rates) < 5:
                log.warning(f"🧪 TestStrategy: Insufficient rates: {len(rates)}")
                return None
                
            current_time = time.time()
            time_since_last = current_time - self.last_signal_time
            
            log.info(f"🧪 TestStrategy: Time since last signal: {time_since_last:.1f}s (interval: {self.signal_interval}s)")
            
            if time_since_last < self.signal_interval:
                log.debug(f"🧪 TestStrategy: Waiting... {self.signal_interval - time_since_last:.1f}s remaining")
                return None
                
            current_price = float(rates[-1][4])
            self.signal_count += 1
            
            # ENHANCED: Multiple signal patterns for better testing
            pattern = self.signal_count % 4
            if pattern == 0:
                signal_type = 'BUY'
                reason = f'Test BUY Signal #{self.signal_count} - Pattern A'
                confidence = 0.85
            elif pattern == 1:
                signal_type = 'SELL'
                reason = f'Test SELL Signal #{self.signal_count} - Pattern B'
                confidence = 0.80
            elif pattern == 2:
                signal_type = 'BUY'
                reason = f'Test BUY Signal #{self.signal_count} - Pattern C'
                confidence = 0.90
            else:
                signal_type = 'SELL'
                reason = f'Test SELL Signal #{self.signal_count} - Pattern D'
                confidence = 0.75
            
            self.last_signal_time = current_time
            
            signal = {
                'type': signal_type,
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': reason,
                'signal_count': self.signal_count,
                'test_mode': True
            }
            
            log.info(f"🚀 TestStrategy GENERATED: {signal}")
            log.info(f"🧪 Test Signal Details: Type={signal_type}, Count={self.signal_count}, Confidence={confidence}")
            return signal
            
        except Exception as e:
            log.error(f"❌ Error in test strategy analysis: {e}")
            return None

class CombinedStrategy(BaseStrategy):
    """Combined strategy using multiple indicators"""
    
    def __init__(self, symbol: str = "ETHUSD"):
        super().__init__(symbol)
        self.name = "combined_strategy"
        self.ma_strategy = MovingAverageCrossover(symbol)
        self.rsi_strategy = RSIStrategy(symbol)
        self.breakout_strategy = BreakoutStrategy(symbol)
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Combine signals from multiple strategies"""
        try:
            # Get signals from individual strategies
            ma_signal = self.ma_strategy.analyze(rates)
            rsi_signal = self.rsi_strategy.analyze(rates)
            breakout_signal = self.breakout_strategy.analyze(rates)
            
            signals = [s for s in [ma_signal, rsi_signal, breakout_signal] if s is not None]
            
            if not signals:
                return None
            
            # Count buy and sell signals
            buy_signals = [s for s in signals if s['type'] == 'BUY']
            sell_signals = [s for s in signals if s['type'] == 'SELL']
            
            current_price = rates[-1][4]
            
            # Require at least 2 agreeing signals
            if len(buy_signals) >= 2:
                avg_confidence = np.mean([s['confidence'] for s in buy_signals])
                reasons = [s['reason'] for s in buy_signals]
                
                return {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': min(avg_confidence * 1.2, 0.95),  # Boost confidence for agreement
                    'strategy': self.name,
                    'reasons': reasons,
                    'supporting_signals': len(buy_signals)
                }
            
            elif len(sell_signals) >= 2:
                avg_confidence = np.mean([s['confidence'] for s in sell_signals])
                reasons = [s['reason'] for s in sell_signals]
                
                return {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': min(avg_confidence * 1.2, 0.95),
                    'strategy': self.name,
                    'reasons': reasons,
                    'supporting_signals': len(sell_signals)
                }
            
            return None
            
        except Exception as e:
            log.error(f"Error in combined strategy analysis: {e}")
            return None

# ============================================================================
# 🚀 ADVANCED STRATEGY EXAMPLES - ADD YOUR NEW STRATEGIES HERE
# ============================================================================

# Import ML Strategy
try:
    from .ml_strategy import get_ml_strategy
    from .enhanced_ml_strategy import get_enhanced_ml_strategy
    from .pure_ml_strategy import get_pure_ml_strategy
    ML_STRATEGY_AVAILABLE = True
except ImportError:
    ML_STRATEGY_AVAILABLE = False
    log.warning("ML Strategy not available - TensorFlow dependencies missing")

class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands Strategy - Price reversal at bands"""
    
    def __init__(self, symbol: str = "ETHUSD", period: int = 20, std_dev: float = 2.0):
        super().__init__(symbol)
        self.name = "bollinger_bands"
        self.period = period
        self.std_dev = std_dev
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate signals based on Bollinger Bands"""
        try:
            if len(rates) < self.period:
                return None
                
            close_prices = np.array([rate[4] for rate in rates])
            current_price = close_prices[-1]
            
            # Calculate Bollinger Bands
            sma = np.mean(close_prices[-self.period:])
            std = np.std(close_prices[-self.period:])
            
            upper_band = sma + (self.std_dev * std)
            lower_band = sma - (self.std_dev * std)
            
            # Always log current Bollinger status for debugging
            position_pct = ((current_price - lower_band) / (upper_band - lower_band)) * 100
            log.info(f"📊 BB Status: Price={current_price:.2f}, Upper={upper_band:.2f}, Lower={lower_band:.2f}, Position={position_pct:.1f}%")
            
            signal = None
            
            # Price touching lower band = BUY signal (oversold)
            if current_price <= lower_band:
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'upper_band': upper_band,
                    'lower_band': lower_band,
                    'sma': sma,
                    'reason': f'Price at lower band ({lower_band:.2f})'
                }
                log.info(f"📉 BOLLINGER BUY: Price {current_price:.2f} at lower band {lower_band:.2f}")
            
            # Price touching upper band = SELL signal (overbought)
            elif current_price >= upper_band:
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'upper_band': upper_band,
                    'lower_band': lower_band,
                    'sma': sma,
                    'reason': f'Price at upper band ({upper_band:.2f})'
                }
                log.info(f"📈 BOLLINGER SELL: Price {current_price:.2f} at upper band {upper_band:.2f}")
            else:
                # Show why no signal was generated
                if position_pct < 25:
                    log.info(f"📊 BB: Price near lower band ({position_pct:.1f}%) but not touching - waiting...")
                elif position_pct > 75:
                    log.info(f"📊 BB: Price near upper band ({position_pct:.1f}%) but not touching - waiting...")
                else:
                    log.info(f"📊 BB: Price in middle range ({position_pct:.1f}%) - no signal")
            
            return signal
            
        except Exception as e:
            log.error(f"Error in Bollinger Bands analysis: {e}")
            return None

class MACDStrategy(BaseStrategy):
    """MACD Strategy - Moving Average Convergence Divergence"""
    
    def __init__(self, symbol: str = "ETHUSD", fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(symbol)
        self.name = "macd_strategy"
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    def calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = prices[0]  # Start with first price
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate signals based on MACD crossover"""
        try:
            if len(rates) < self.slow_period + self.signal_period:
                return None
                
            close_prices = np.array([rate[4] for rate in rates])
            current_price = close_prices[-1]
            
            # Calculate MACD components
            ema_fast = self.calculate_ema(close_prices[-self.fast_period:], self.fast_period)
            ema_slow = self.calculate_ema(close_prices[-self.slow_period:], self.slow_period)
            
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line (EMA of MACD)
            if len(close_prices) >= self.slow_period + self.signal_period:
                macd_values = []
                for i in range(self.signal_period):
                    idx = -(self.signal_period - i)
                    fast = self.calculate_ema(close_prices[:idx] if idx < 0 else close_prices, self.fast_period)
                    slow = self.calculate_ema(close_prices[:idx] if idx < 0 else close_prices, self.slow_period)
                    macd_values.append(fast - slow)
                
                signal_line = self.calculate_ema(np.array(macd_values), self.signal_period)
                
                # Previous values for crossover detection
                if len(macd_values) >= 2:
                    prev_macd = macd_values[-2]
                    prev_signal = self.calculate_ema(np.array(macd_values[:-1]), self.signal_period)
                    
                    signal = None
                    
                    # MACD crosses above signal line = BUY
                    if prev_macd <= prev_signal and macd_line > signal_line:
                        signal = {
                            'type': 'BUY',
                            'price': current_price,
                            'confidence': 0.85,
                            'strategy': self.name,
                            'macd': macd_line,
                            'signal_line': signal_line,
                            'reason': 'MACD Bullish Crossover'
                        }
                        log.info(f"🚀 MACD BUY: MACD {macd_line:.4f} crossed above signal {signal_line:.4f}")
                    
                    # MACD crosses below signal line = SELL
                    elif prev_macd >= prev_signal and macd_line < signal_line:
                        signal = {
                            'type': 'SELL',
                            'price': current_price,
                            'confidence': 0.85,
                            'strategy': self.name,
                            'macd': macd_line,
                            'signal_line': signal_line,
                            'reason': 'MACD Bearish Crossover'
                        }
                        log.info(f"🔻 MACD SELL: MACD {macd_line:.4f} crossed below signal {signal_line:.4f}")
                    
                    return signal
            
            return None
            
        except Exception as e:
            log.error(f"Error in MACD analysis: {e}")
            return None

class StochasticStrategy(BaseStrategy):
    """Stochastic Oscillator Strategy - Momentum indicator"""
    
    def __init__(self, symbol: str = "ETHUSD", k_period: int = 14, d_period: int = 3, oversold: float = 20, overbought: float = 80):
        super().__init__(symbol)
        self.name = "stochastic_strategy"
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate signals based on Stochastic levels"""
        try:
            if len(rates) < self.k_period + self.d_period:
                return None
                
            # Get price data
            high_prices = np.array([rate[2] for rate in rates[-self.k_period:]])
            low_prices = np.array([rate[3] for rate in rates[-self.k_period:]])
            close_prices = np.array([rate[4] for rate in rates])
            current_price = close_prices[-1]
            
            # Calculate %K
            highest_high = np.max(high_prices)
            lowest_low = np.min(low_prices)
            
            if highest_high == lowest_low:
                return None
                
            k_percent = 100 * (current_price - lowest_low) / (highest_high - lowest_low)
            
            # Calculate %D (SMA of %K)
            if len(close_prices) >= self.k_period + self.d_period:
                k_values = []
                for i in range(self.d_period):
                    idx = -(self.d_period - i)
                    period_high = np.max([rate[2] for rate in rates[idx-self.k_period:idx if idx < 0 else len(rates)]])
                    period_low = np.min([rate[3] for rate in rates[idx-self.k_period:idx if idx < 0 else len(rates)]])
                    period_close = rates[idx][4] if idx < 0 else rates[-1][4]
                    
                    if period_high != period_low:
                        k_val = 100 * (period_close - period_low) / (period_high - period_low)
                        k_values.append(k_val)
                
                if len(k_values) >= self.d_period:
                    d_percent = np.mean(k_values[-self.d_period:])
                    
                    signal = None
                    
                    # Oversold condition + %K crosses above %D = BUY
                    if k_percent < self.oversold and k_percent > d_percent:
                        signal = {
                            'type': 'BUY',
                            'price': current_price,
                            'confidence': 0.75,
                            'strategy': self.name,
                            'k_percent': k_percent,
                            'd_percent': d_percent,
                            'reason': f'Stochastic oversold ({k_percent:.1f}%)'
                        }
                        log.info(f"📉 STOCHASTIC BUY: %K {k_percent:.1f}% oversold, above %D {d_percent:.1f}%")
                    
                    # Overbought condition + %K crosses below %D = SELL
                    elif k_percent > self.overbought and k_percent < d_percent:
                        signal = {
                            'type': 'SELL',
                            'price': current_price,
                            'confidence': 0.75,
                            'strategy': self.name,
                            'k_percent': k_percent,
                            'd_percent': d_percent,
                            'reason': f'Stochastic overbought ({k_percent:.1f}%)'
                        }
                        log.info(f"📈 STOCHASTIC SELL: %K {k_percent:.1f}% overbought, below %D {d_percent:.1f}%")
                    
                    return signal
            
            return None
            
        except Exception as e:
            log.error(f"Error in Stochastic analysis: {e}")
            return None

class VolumeWeightedStrategy(BaseStrategy):
    """Volume Weighted Average Price (VWAP) Strategy"""
    
    def __init__(self, symbol: str = "ETHUSD", period: int = 20, threshold: float = 0.002):
        super().__init__(symbol)
        self.name = "vwap_strategy"
        self.period = period
        self.threshold = threshold  # 0.2% threshold
        
    def analyze(self, rates: np.ndarray) -> Optional[Dict]:
        """Generate signals based on price vs VWAP"""
        try:
            if len(rates) < self.period:
                return None
                
            recent_rates = rates[-self.period:]
            
            # Calculate VWAP
            total_volume_price = 0
            total_volume = 0
            
            for rate in recent_rates:
                typical_price = (rate[2] + rate[3] + rate[4]) / 3  # (H+L+C)/3
                volume = rate[5] if len(rate) > 5 else 1000  # Use tick volume or default
                total_volume_price += typical_price * volume
                total_volume += volume
            
            if total_volume == 0:
                return None
                
            vwap = total_volume_price / total_volume
            current_price = rates[-1][4]
            
            # Calculate price deviation from VWAP
            deviation = (current_price - vwap) / vwap
            
            signal = None
            
            # Price significantly below VWAP = BUY signal
            if deviation < -self.threshold:
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'vwap': vwap,
                    'deviation': deviation * 100,
                    'reason': f'Price {deviation*100:.2f}% below VWAP'
                }
                log.info(f"📉 VWAP BUY: Price {current_price:.2f} is {deviation*100:.2f}% below VWAP {vwap:.2f}")
            
            # Price significantly above VWAP = SELL signal
            elif deviation > self.threshold:
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'vwap': vwap,
                    'deviation': deviation * 100,
                    'reason': f'Price {deviation*100:.2f}% above VWAP'
                }
                log.info(f"📈 VWAP SELL: Price {current_price:.2f} is {deviation*100:.2f}% above VWAP {vwap:.2f}")
            
            return signal
            
        except Exception as e:
            log.error(f"Error in VWAP analysis: {e}")
            return None

# ============================================================================

# Strategy factory
AVAILABLE_STRATEGIES = {
    'ma_crossover': MovingAverageCrossover,
    'moving_average': MovingAverageCrossover,  # Add frontend mapping
    'rsi_strategy': RSIStrategy,
    'breakout_strategy': BreakoutStrategy,
    'combined_strategy': CombinedStrategy,
    'bollinger_bands': BollingerBandsStrategy,  # Map to breakout for now
    'macd_strategy': MACDStrategy,  # New MACD strategy
    'stochastic_strategy': StochasticStrategy,  # New Stochastic strategy  
    'vwap_strategy': VolumeWeightedStrategy,  # New VWAP strategy
    'test_strategy': TestStrategy,  # Test strategy for debugging
    'always_signal': AlwaysSignalStrategy,  # Always generates signals
    'ml_strategy': 'ml_strategy',  # ML Neural Network strategy (special handling)
    'enhanced_ml_strategy': 'enhanced_ml_strategy',  # Enhanced ML strategy (more aggressive)
    'pure_ml_strategy': 'pure_ml_strategy',  # Pure ML strategy (respects original training)
    'default': AlwaysSignalStrategy  # Default to always signal for testing
}

def get_strategy(strategy_name: str, symbol: str = "ETHUSD", config: Dict = None) -> BaseStrategy:
    """Get strategy instance by name with optional configuration"""
    strategy_class = AVAILABLE_STRATEGIES.get(strategy_name, MovingAverageCrossover)
    
    # Extract strategy-specific configuration
    diagnostic_mode = False
    if config:
        diagnostic_mode = config.get('diagnostic_mode', False) or config.get('diagnostic_demo_mode', False)
    
    # Extract nested indicator settings if available (for frontend compatibility)
    indicator_settings = config.get('indicator_settings', {}) if config else {}
    
    # Create strategy with configuration (supports both direct and nested params) - OPTIMIZED DEFAULTS
    if strategy_name in ['ma_crossover', 'moving_average']:
        ma_fast = config.get('ma_fast') or indicator_settings.get('ma_fast_period', 2) if config else 2  # ULTRA-OPTIMIZED: 2 vs 3
        ma_slow = config.get('ma_slow') or indicator_settings.get('ma_slow_period', 5) if config else 5   # ULTRA-OPTIMIZED: 5 vs 8
        use_ema = config.get('use_ema', True) if config else True  # OPTIMIZED: Default to EMA
        return strategy_class(symbol, ma_fast=ma_fast, ma_slow=ma_slow, use_ema=use_ema, diagnostic_mode=diagnostic_mode)
    
    elif strategy_name == 'rsi_strategy':
        period = config.get('rsi_window') or indicator_settings.get('rsi_period', 6) if config else 6      # ULTRA-OPTIMIZED: 6 vs 8
        buy_threshold = config.get('rsi_buy_threshold') or indicator_settings.get('rsi_oversold', 40) if config else 40   # OPTIMIZED: 40 vs 35
        sell_threshold = config.get('rsi_sell_threshold') or indicator_settings.get('rsi_overbought', 60) if config else 60  # OPTIMIZED: 60 vs 65
        use_crossing = config.get('rsi_use_crossing', True) if config else True
        return strategy_class(symbol, period=period, rsi_buy_threshold=buy_threshold, 
                            rsi_sell_threshold=sell_threshold, use_crossing=use_crossing, 
                            diagnostic_mode=diagnostic_mode)
    
    elif strategy_name == 'breakout_strategy':
        lookback_period = config.get('breakout_lookback_period') or indicator_settings.get('breakout_lookback', 4) if config else 4      # ULTRA-OPTIMIZED: 4 vs 6
        breakout_threshold = config.get('breakout_threshold') or indicator_settings.get('breakout_threshold', 0.0005) if config else 0.0005  # OPTIMIZED: 0.0005 vs 0.0002
        return strategy_class(symbol, lookback_period=lookback_period, breakout_threshold=breakout_threshold)
    
    elif strategy_name == 'bollinger_bands':
        period = config.get('bb_period') or indicator_settings.get('bb_period', 20) if config else 20
        std_dev = config.get('bb_std_dev') or indicator_settings.get('bb_deviation', 2.0) if config else 2.0
        return strategy_class(symbol, period=period, std_dev=std_dev)
    
    elif strategy_name == 'macd_strategy':
        fast_period = config.get('macd_fast_period') or indicator_settings.get('macd_fast', 12) if config else 12
        slow_period = config.get('macd_slow_period') or indicator_settings.get('macd_slow', 26) if config else 26
        signal_period = config.get('macd_signal_period') or indicator_settings.get('macd_signal', 9) if config else 9
        return strategy_class(symbol, fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
    
    elif strategy_name == 'stochastic_strategy':
        k_period = config.get('stoch_k_period') or indicator_settings.get('stoch_k_period', 14) if config else 14
        d_period = config.get('stoch_d_period') or indicator_settings.get('stoch_d_period', 3) if config else 3
        oversold = config.get('stoch_oversold') or indicator_settings.get('stoch_oversold', 20) if config else 20
        overbought = config.get('stoch_overbought') or indicator_settings.get('stoch_overbought', 80) if config else 80
        return strategy_class(symbol, k_period=k_period, d_period=d_period, oversold=oversold, overbought=overbought)
    
    elif strategy_name == 'vwap_strategy':
        period = config.get('vwap_period') or indicator_settings.get('vwap_period', 20) if config else 20
        threshold = config.get('vwap_threshold') or indicator_settings.get('vwap_deviation_threshold', 0.002) if config else 0.002
        return strategy_class(symbol, period=period, threshold=threshold)
    
    elif strategy_name == 'test_strategy':
        # Test strategy gets diagnostic mode for more frequent signals
        return strategy_class(symbol)
    
    elif strategy_name in ['always_signal', 'default']:
        # Always signal strategies for testing
        return strategy_class(symbol)
    
    elif strategy_name == 'combined_strategy':
        # Combined strategy uses other strategies internally
        return strategy_class(symbol)
    
    elif strategy_name == 'ml_strategy':
        # ML Neural Network strategy - special handling
        if ML_STRATEGY_AVAILABLE:
            return get_ml_strategy(symbol, config or {})
        else:
            log.error("ML Strategy requested but TensorFlow not available. Falling back to RSI strategy.")
            return RSIStrategy(symbol, diagnostic_mode=diagnostic_mode)
    
    elif strategy_name == 'enhanced_ml_strategy':
        # Enhanced ML Neural Network strategy - more aggressive
        if ML_STRATEGY_AVAILABLE:
            return get_enhanced_ml_strategy(symbol, config or {})
        else:
            log.error("Enhanced ML Strategy requested but TensorFlow not available. Falling back to RSI strategy.")
            return RSIStrategy(symbol, diagnostic_mode=diagnostic_mode)
    
    elif strategy_name == 'pure_ml_strategy':
        # Pure ML Neural Network strategy - respects original training
        if ML_STRATEGY_AVAILABLE:
            return get_pure_ml_strategy(symbol, config or {})
        else:
            log.error("Pure ML Strategy requested but TensorFlow not available. Falling back to RSI strategy.")
            return RSIStrategy(symbol, diagnostic_mode=diagnostic_mode)
    
    else:
        # Default instantiation for unknown strategies
        log.warning(f"Unknown strategy '{strategy_name}', defaulting to MovingAverageCrossover")
        return MovingAverageCrossover(symbol, diagnostic_mode=diagnostic_mode)

def list_strategies() -> List[str]:
    """Get list of available strategy names"""
    return list(AVAILABLE_STRATEGIES.keys())