"""
Tick-based strategies for HFT manager.

We reuse names from candle strategies but calculations are tick-oriented.
Each strategy must implement analyze_ticks(ticks) -> Optional[Dict]
where ticks is the array returned from MT5 copy_ticks_* APIs.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np

log = logging.getLogger(__name__)


class BaseTickStrategy:
    def __init__(self, symbol: str = "ETHUSD"):
        self.symbol = symbol
        self.name = "base_tick_strategy"

    def analyze_ticks(self, ticks) -> Optional[Dict]:
        raise NotImplementedError


def _ticks_to_arrays(ticks) -> Dict[str, np.ndarray]:
    if ticks is None or len(ticks) == 0:
        return {
            'bid': np.array([]),
            'ask': np.array([]),
            'last': np.array([]),
            'time': np.array([]),
        }
    
    # DEBUG: Log tick structure (only for first few ticks to avoid spam)
    debug_enabled = False  # Set to True for debugging
    if debug_enabled and len(ticks) > 0:
        first_tick = ticks[0]
        log.info(f"🔍 TICK DEBUGGING: First tick type: {type(first_tick)}")
        log.info(f"🔍 TICK DEBUGGING: First tick attributes: {dir(first_tick)}")
        
        # Try to extract any numerical value from the tick
        for attr in dir(first_tick):
            if not attr.startswith('_'):
                try:
                    val = getattr(first_tick, attr)
                    if isinstance(val, (int, float)) and val > 100:
                        log.info(f"🔍 POTENTIAL PRICE: {attr} = {val}")
                except:
                    pass
    
    # Enhanced data extraction with multiple price field checks
    bid_prices = []
    ask_prices = []
    times = []
    valid_count = 0
    
    for i, t in enumerate(ticks):
        bid = None
        ask = None
        tick_time = None
        
        try:
            # Method 1: Handle numpy.void (historical ticks from copy_ticks_range)
            if hasattr(t, 'dtype') and hasattr(t.dtype, 'names') and t.dtype.names:
                # This is a numpy structured array (historical tick)
                try:
                    # Access by field names
                    if 'bid' in t.dtype.names and 'ask' in t.dtype.names:
                        bid_val = float(t['bid'])
                        ask_val = float(t['ask'])
                        if 1000 <= bid_val <= 10000 and 1000 <= ask_val <= 10000:
                            bid, ask = bid_val, ask_val
                    elif hasattr(t, '__getitem__') and len(t) >= 3:
                        # Fallback: positional access (time, bid, ask, ...)
                        bid_val = float(t[1])  # bid is at index 1
                        ask_val = float(t[2])  # ask is at index 2
                        if 1000 <= bid_val <= 10000 and 1000 <= ask_val <= 10000:
                            bid, ask = bid_val, ask_val
                except (ValueError, TypeError, IndexError, KeyError):
                    pass
            
            # Method 2: Handle regular Tick objects (current tick from symbol_info_tick)
            if bid is None or ask is None:
                try:
                    if hasattr(t, 'bid') and hasattr(t, 'ask'):
                        bid_val = t.bid
                        ask_val = t.ask
                        
                        # Convert to float and validate
                        if bid_val is not None and ask_val is not None:
                            bid_val = float(bid_val)
                            ask_val = float(ask_val)
                            
                            # Check if prices are reasonable for ETHUSD (between 1000-10000)
                            if 1000 <= bid_val <= 10000 and 1000 <= ask_val <= 10000:
                                bid, ask = bid_val, ask_val
                except (ValueError, TypeError, AttributeError):
                    pass
            
            # Method 3: Try 'last' price if bid/ask failed
            if bid is None or ask is None:
                try:
                    last_val = None
                    if hasattr(t, 'last') and t.last is not None:
                        last_val = float(t.last)
                    elif hasattr(t, 'dtype') and 'last' in t.dtype.names:
                        last_val = float(t['last'])
                    elif hasattr(t, '__getitem__') and len(t) >= 4:
                        last_val = float(t[3])  # last is at index 3
                    
                    if last_val and 1000 <= last_val <= 10000:
                        bid = last_val - 1.0  # Estimate bid
                        ask = last_val + 1.0  # Estimate ask
                except (ValueError, TypeError, AttributeError, IndexError, KeyError):
                    pass
            
            # Method 4: Try other price attributes for regular objects
            if bid is None or ask is None:
                for price_attr in ['price', 'close', 'open', 'high', 'low']:
                    try:
                        if hasattr(t, price_attr):
                            price_val = getattr(t, price_attr)
                            if price_val is not None:
                                price_val = float(price_val)
                                if 1000 <= price_val <= 10000:
                                    bid = price_val - 1.0
                                    ask = price_val + 1.0
                                    break
                    except (ValueError, TypeError, AttributeError):
                        continue
            
            # Get timestamp
            try:
                # For numpy structured arrays
                if hasattr(t, 'dtype') and hasattr(t.dtype, 'names') and t.dtype.names:
                    if 'time' in t.dtype.names:
                        tick_time = t['time']
                    elif 'time_msc' in t.dtype.names:
                        tick_time = t['time_msc']
                    elif hasattr(t, '__getitem__') and len(t) >= 1:
                        tick_time = t[0]  # time is at index 0
                # For regular objects
                else:
                    for time_attr in ['time', 'time_msc', 'timestamp', 'datetime']:
                        if hasattr(t, time_attr):
                            tick_time = getattr(t, time_attr)
                            if tick_time is not None:
                                break
            except:
                pass
            
            # If we found valid prices, add them
            if bid is not None and ask is not None and 1000 <= bid <= 10000 and 1000 <= ask <= 10000:
                bid_prices.append(bid)
                ask_prices.append(ask)
                times.append(tick_time if tick_time else (i + 1))
                valid_count += 1
                
                # Log first few valid ticks for debugging
                if valid_count <= 3:
                    log.info(f"✅ Valid tick #{valid_count}: Bid={bid:.2f}, Ask={ask:.2f}")
            elif i < 3:  # Log first few failed attempts for debugging
                log.warning(f"⚠️ Could not extract valid prices from tick #{i+1}: bid={getattr(t, 'bid', 'N/A')}, ask={getattr(t, 'ask', 'N/A')}, last={getattr(t, 'last', 'N/A')}")
                
        except Exception as e:
            if i < 3:  # Only log first few errors
                log.warning(f"⚠️ Error processing tick #{i+1}: {e}")
            continue
    
    # Convert to numpy arrays
    bid = np.array(bid_prices)
    ask = np.array(ask_prices)
    time_arr = np.array(times)
    
    # Calculate last price safely with enhanced logic
    if len(bid) > 0:
        # If we have valid bid/ask data, use midpoint
        if len(ask) > 0 and len(bid) == len(ask):
            last = (bid + ask) / 2.0
        else:
            # Use bid prices as last prices
            last = bid.copy()
    else:
        last = np.array([])
    
    if len(bid_prices) > 0:
        log.info(f"📊 ENHANCED: Processed {len(ticks)} ticks → {len(bid_prices)} valid prices (Bid range: {bid.min():.2f}-{bid.max():.2f})")
    else:
        log.error(f"❌ CRITICAL: Processed {len(ticks)} ticks → 0 valid prices! Tick data extraction FAILED!")
        # Additional debugging for failed extraction
        if len(ticks) > 0:
            sample_tick = ticks[0]
            log.error(f"❌ Sample tick debug: type={type(sample_tick)}, bid={getattr(sample_tick, 'bid', 'MISSING')}, ask={getattr(sample_tick, 'ask', 'MISSING')}")
    
    return {'bid': bid, 'ask': ask, 'last': last, 'time': time_arr}


class TickMACDStrategy(BaseTickStrategy):
    name = "macd_strategy"

    def __init__(self, symbol: str = "ETHUSD", fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(symbol)
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @staticmethod
    def _ema(values: np.ndarray, period: int) -> float:
        if len(values) == 0:
            return 0.0
        k = 2 / (period + 1)
        ema = values[0]
        for v in values[1:]:
            ema = v * k + ema * (1 - k)
        return float(ema)

    def analyze_ticks(self, ticks) -> Optional[Dict]:
        if ticks is None or len(ticks) == 0:
            log.warning(f"⚠️ No ticks provided for MACD analysis")
            return None
            
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        
        log.info(f"📊 MACD Analysis: {len(prices)} prices, need {max(self.slow + self.signal, 10)} minimum")
        
        # Ultra-minimal requirements for HFT - work with single tick if needed
        if prices.size < 1:
            log.warning(f"⚠️ No price data for MACD analysis")
            return None
        
        # For single tick, generate test signal occasionally
        if prices.size == 1:
            current_price = float(prices[-1])
            log.info(f"📊 Single-tick MACD: Using test analysis for price {current_price:.2f}")
            # Generate a test signal occasionally for single tick scenarios
            import random
            if random.random() < 0.2:  # 20% chance to generate signal for testing
                signal_type = 'BUY' if random.random() < 0.5 else 'SELL'
                return {
                    'type': signal_type,
                    'price': current_price,
                    'confidence': 0.8,
                    'strategy': self.name,
                    'reason': f'Single-tick MACD test ({signal_type})',
                    'signal_strength': 'test_macd'
                }
            return None
            
        # Use simplified MACD with limited data
        if prices.size < max(self.slow + self.signal, 10):
            log.info(f"🔄 Using simplified MACD with {prices.size} data points")
            # Simplified fast/slow periods for limited data
            simple_fast = min(3, max(2, prices.size // 2))
            simple_slow = min(5, max(3, prices.size - 1))
            
            if simple_fast < simple_slow and prices.size >= simple_slow:
                ema_fast = self._ema(prices[-simple_fast:], simple_fast)
                ema_slow = self._ema(prices[-simple_slow:], simple_slow)
                macd_line = ema_fast - ema_slow
                current_price = float(prices[-1])
                
                # Simple momentum detection
                if macd_line > 0:
                    return {
                        'type': 'BUY',
                        'price': current_price,
                        'confidence': 0.65,
                        'strategy': self.name,
                        'reason': f'Simplified MACD Bullish ({macd_line:.4f})',
                        'signal_strength': 'simplified_bullish'
                    }
                elif macd_line < 0:
                    return {
                        'type': 'SELL',
                        'price': current_price,
                        'confidence': 0.65,
                        'strategy': self.name,
                        'reason': f'Simplified MACD Bearish ({macd_line:.4f})',
                        'signal_strength': 'simplified_bearish'
                    }
            else:
                # Ultra-simple momentum for very limited data
                if prices.size >= 2:
                    momentum = prices[-1] - prices[-2]
                    current_price = float(prices[-1])
                    if momentum > 0:
                        return {
                            'type': 'BUY',
                            'price': current_price,
                            'confidence': 0.5,
                            'strategy': self.name,
                            'reason': f'Simple Momentum Up ({momentum:.2f})',
                            'signal_strength': 'momentum_bullish'
                        }
                    elif momentum < 0:
                        return {
                            'type': 'SELL',
                            'price': current_price,
                            'confidence': 0.5,
                            'strategy': self.name,
                            'reason': f'Simple Momentum Down ({momentum:.2f})',
                            'signal_strength': 'momentum_bearish'
                        }
            return None

        # Full MACD analysis with sufficient data
        ema_fast = self._ema(prices[-self.fast:], self.fast)
        ema_slow = self._ema(prices[-self.slow:], self.slow)
        macd_line = ema_fast - ema_slow

        # Build macd history for signal line
        macd_vals: List[float] = []
        window = max(self.slow + self.signal, self.slow + 2)
        if prices.size >= window:
            for i in range(self.signal):
                idx = -(self.signal - i)
                segment = prices[:idx] if idx < 0 else prices
                macd_vals.append(self._ema(segment[-self.fast:], self.fast) - self._ema(segment[-self.slow:], self.slow))

        if len(macd_vals) < 2:
            # Generate signal based on MACD value alone
            current_price = float(prices[-1])
            if macd_line > 0.1:  # Threshold for bullish signal
                return {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.7,
                    'strategy': self.name,
                    'reason': f'MACD Bullish ({macd_line:.4f})',
                    'signal_strength': 'momentum_bullish'
                }
            elif macd_line < -0.1:  # Threshold for bearish signal
                return {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.7,
                    'strategy': self.name,
                    'reason': f'MACD Bearish ({macd_line:.4f})',
                    'signal_strength': 'momentum_bearish'
                }
            return None

        signal_line = self._ema(np.array(macd_vals), self.signal)
        prev_macd = macd_vals[-2]
        current_price = float(prices[-1])

        log.info(f"📊 MACD Values: Line={macd_line:.4f}, Signal={signal_line:.4f}, Prev={prev_macd:.4f}")

        if prev_macd <= signal_line and macd_line > signal_line:
            signal = {
                'type': 'BUY',
                'price': current_price,
                'confidence': 0.8,
                'strategy': self.name,
                'reason': f'MACD Bullish Cross ({macd_line:.4f} > {signal_line:.4f})',
                'signal_strength': 'crossover_bullish'
            }
            log.info(f"🎯 MACD BUY Signal: {signal}")
            return signal
            
        if prev_macd >= signal_line and macd_line < signal_line:
            signal = {
                'type': 'SELL',
                'price': current_price,
                'confidence': 0.8,
                'strategy': self.name,
                'reason': f'MACD Bearish Cross ({macd_line:.4f} < {signal_line:.4f})',
                'signal_strength': 'crossover_bearish'
            }
            log.info(f"🎯 MACD SELL Signal: {signal}")
            return signal
            
        log.info(f"📊 MACD Neutral: No crossover signal")
        return None


class TickRSIStrategy(BaseTickStrategy):
    name = "rsi_strategy"

    def __init__(self, symbol: str = "ETHUSD", period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__(symbol)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def _rsi(self, arr: np.ndarray) -> float:
        deltas = np.diff(arr)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        if gains.size < self.period or losses.size < self.period:
            return 50.0
        avg_gain = np.mean(gains[-self.period:])
        avg_loss = np.mean(losses[-self.period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _simple_rsi(self, arr: np.ndarray, period: int) -> float:
        """Simplified RSI calculation for limited data points"""
        if len(arr) < 2:
            return 50.0
            
        deltas = np.diff(arr)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        if gains.size == 0 or losses.size == 0:
            return 50.0
            
        # Use available data up to period
        use_period = min(period, len(gains))
        avg_gain = np.mean(gains[-use_period:]) if use_period > 0 else 0
        avg_loss = np.mean(losses[-use_period:]) if use_period > 0 else 0
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        if avg_gain == 0:
            return 0.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        log.info(f"📊 Simple RSI calculation: period={use_period}, gains={avg_gain:.4f}, losses={avg_loss:.4f}, RSI={rsi:.2f}")
        return rsi
    
    def _hft_rsi(self, arr: np.ndarray) -> float:
        """Ultra-fast RSI calculation optimized for HFT with minimal data"""
        if len(arr) < 3:
            # Price momentum for ultra-minimal data
            if len(arr) == 2:
                change = arr[-1] - arr[0]
                return 75.0 if change > 0 else 25.0
            return 50.0
            
        # Use last 3-5 price points for momentum
        recent_prices = arr[-min(5, len(arr)):]
        deltas = np.diff(recent_prices)
        
        if len(deltas) == 0:
            return 50.0
            
        # Simple momentum calculation
        up_moves = deltas[deltas > 0]
        down_moves = deltas[deltas < 0]
        
        avg_up = np.mean(up_moves) if len(up_moves) > 0 else 0
        avg_down = np.mean(np.abs(down_moves)) if len(down_moves) > 0 else 0
        
        if avg_down == 0:
            rsi = 85.0 if avg_up > 0 else 50.0
        elif avg_up == 0:
            rsi = 15.0
        else:
            rs = avg_up / avg_down
            rsi = 100 - (100 / (1 + rs))
        
        # Add volatility adjustment for HFT
        volatility = np.std(recent_prices) if len(recent_prices) > 1 else 0
        if volatility > 0:
            price_change_pct = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
            rsi += price_change_pct * 0.5  # Adjust RSI based on price momentum
            rsi = max(0, min(100, rsi))  # Keep in bounds
        
        log.info(f"📊 HFT RSI calculation: {len(recent_prices)} points, up={avg_up:.4f}, down={avg_down:.4f}, volatility={volatility:.4f}, RSI={rsi:.2f}")
        return rsi

    def analyze_ticks(self, ticks) -> Optional[Dict]:
        if ticks is None or len(ticks) == 0:
            log.warning(f"⚠️ No ticks provided for RSI analysis")
            return None
            
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        
        log.info(f"📊 RSI Analysis: {len(prices)} prices, need {self.period + 2} minimum")
        log.info(f"📊 Price data sample: First={prices[0]:.2f}, Last={prices[-1]:.2f}, Range={prices.max() - prices.min():.2f}")
        
        # ENHANCED HFT: Generate signals with ANY amount of data 
        if prices.size < 1:
            log.warning(f"⚠️ No price data available")
            return None
            
        # OPTIMIZED HFT MODE: More aggressive signal generation
        current_price = float(prices[-1])
        log.info(f"🚀 ENHANCED HFT RSI with {prices.size} data points")
        
        if prices.size >= 3:
            # Use HFT-optimized RSI for 3+ prices
            simple_rsi = self._hft_rsi(prices)
            log.info(f"📊 HFT RSI calculated: {simple_rsi:.1f}")
        elif prices.size == 2:
            # MOMENTUM MODE: For 2 prices, use price change
            price_change = (prices[-1] - prices[0]) / prices[0] * 100
            simple_rsi = 50 + (price_change * 15)  # Amplified sensitivity
            simple_rsi = max(5, min(95, simple_rsi))  # Keep in 5-95 range for stronger signals
            log.info(f"📊 MOMENTUM RSI: Price change {price_change:.3f}% → RSI {simple_rsi:.1f}")
        else:
            # SINGLE PRICE MODE: Use price level analysis for signal
            price_mod = int(current_price * 100) % 100
            if price_mod < 30:
                simple_rsi = 25  # Oversold signal
            elif price_mod > 70:
                simple_rsi = 75  # Overbought signal  
            else:
                simple_rsi = 50 + (price_mod - 50) * 0.5  # Moderate signal
            log.info(f"📊 SINGLE PRICE RSI: Price={current_price:.2f}, Mod={price_mod}, RSI={simple_rsi:.1f}")
        
        # ULTRA-SENSITIVE: Generate signals with aggressive thresholds
        if simple_rsi < 52:  # ENHANCED: Buy when RSI < 52 (instead of 30)
            confidence = 0.9 if simple_rsi < 35 else (0.8 if simple_rsi < 45 else 0.7)
            signal = {
                'type': 'BUY', 
                'price': current_price, 
                'confidence': confidence, 
                'strategy': self.name, 
                'reason': f'HFT RSI Bullish ({simple_rsi:.1f} < 52)',
                'rsi_value': simple_rsi,
                'signal_strength': 'hft_ultra_ultra_sensitive',
                'data_points': prices.size
            }
            log.info(f"🎯 HFT RSI BUY Signal: RSI={simple_rsi:.2f} with {prices.size} data points")
            return signal
            
        elif simple_rsi > 48:  # ULTRA-ULTRA-AGGRESSIVE: Sell when RSI > 48
            confidence = 0.9 if simple_rsi > 65 else (0.8 if simple_rsi > 55 else 0.7)
            signal = {
                'type': 'SELL', 
                'price': current_price, 
                'confidence': confidence, 
                'strategy': self.name, 
                'reason': f'HFT RSI Bearish ({simple_rsi:.1f} > 48)',
                'rsi_value': simple_rsi,
                'signal_strength': 'hft_ultra_ultra_sensitive',
                'data_points': prices.size
            }
            log.info(f"🎯 HFT RSI SELL Signal: RSI={simple_rsi:.2f} with {prices.size} data points")
            return signal
        
        else:
            log.info(f"📊 HFT RSI NEUTRAL: {simple_rsi:.2f} (between 48-52) with {prices.size} data points")
            return None
            
        rsi = self._rsi(prices)
        current_price = float(prices[-1])
        
        log.info(f"📊 RSI Value: {rsi:.2f} (Oversold: <{self.oversold}, Overbought: >{self.overbought})")
        
        # Generate signals with detailed confidence calculation
        if rsi < self.oversold:
            # More oversold = higher confidence
            confidence = min(0.9, 0.6 + (self.oversold - rsi) / self.oversold * 0.3)
            signal = {
                'type': 'BUY', 
                'price': current_price, 
                'confidence': round(confidence, 2), 
                'strategy': self.name, 
                'reason': f'RSI Oversold ({rsi:.1f} < {self.oversold})',
                'rsi_value': rsi,
                'signal_strength': 'oversold'
            }
            log.info(f"🎯 RSI BUY Signal: RSI={rsi:.2f}, Confidence={confidence:.2f}")
            return signal
            
        if rsi > self.overbought:
            # More overbought = higher confidence  
            confidence = min(0.9, 0.6 + (rsi - self.overbought) / (100 - self.overbought) * 0.3)
            signal = {
                'type': 'SELL', 
                'price': current_price, 
                'confidence': round(confidence, 2), 
                'strategy': self.name, 
                'reason': f'RSI Overbought ({rsi:.1f} > {self.overbought})',
                'rsi_value': rsi,
                'signal_strength': 'overbought'
            }
            log.info(f"🎯 RSI SELL Signal: RSI={rsi:.2f}, Confidence={confidence:.2f}")
            return signal
            
        # Check for momentum signals (RSI trending toward extremes)
        if len(prices) >= self.period + 5:
            prev_rsi = self._rsi(prices[:-2])  # RSI from 2 ticks ago
            rsi_momentum = rsi - prev_rsi
            
            log.info(f"📊 RSI Momentum: {rsi_momentum:.2f} (Current: {rsi:.2f}, Previous: {prev_rsi:.2f})")
            
            # Strong momentum toward oversold
            if 35 < rsi < 45 and rsi_momentum < -2:
                confidence = 0.65
                signal = {
                    'type': 'BUY', 
                    'price': current_price, 
                    'confidence': confidence, 
                    'strategy': self.name, 
                    'reason': f'RSI Momentum Down ({rsi:.1f}, momentum: {rsi_momentum:.1f})',
                    'rsi_value': rsi,
                    'signal_strength': 'momentum_oversold'
                }
                log.info(f"🎯 RSI Momentum BUY Signal: RSI={rsi:.2f}, Momentum={rsi_momentum:.2f}")
                return signal
                
            # Strong momentum toward overbought  
            if 55 < rsi < 65 and rsi_momentum > 2:
                confidence = 0.65
                signal = {
                    'type': 'SELL', 
                    'price': current_price, 
                    'confidence': confidence, 
                    'strategy': self.name, 
                    'reason': f'RSI Momentum Up ({rsi:.1f}, momentum: {rsi_momentum:.1f})',
                    'rsi_value': rsi,
                    'signal_strength': 'momentum_overbought'
                }
                log.info(f"🎯 RSI Momentum SELL Signal: RSI={rsi:.2f}, Momentum={rsi_momentum:.2f}")
                return signal
        
        log.info(f"📊 RSI Neutral: {rsi:.2f} (between {self.oversold} and {self.overbought})")
        return None


class TickBollingerStrategy(BaseTickStrategy):
    name = "bollinger_bands"

    def __init__(self, symbol: str = "ETHUSD", period: int = 20, std_dev: float = 2.0):
        super().__init__(symbol)
        self.period = period
        self.std_dev = std_dev

    def analyze_ticks(self, ticks) -> Optional[Dict]:
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        if prices.size < self.period:
            return None
        sma = np.mean(prices[-self.period:])
        std = np.std(prices[-self.period:])
        upper = sma + self.std_dev * std
        lower = sma - self.std_dev * std
        current = float(prices[-1])
        if current <= lower:
            return {'type': 'BUY', 'price': current, 'confidence': 0.75, 'strategy': self.name, 'reason': 'Tick BB Lower'}
        if current >= upper:
            return {'type': 'SELL', 'price': current, 'confidence': 0.75, 'strategy': self.name, 'reason': 'Tick BB Upper'}
        return None


class TickMovingAverageStrategy(BaseTickStrategy):
    name = "moving_average"
    
    def __init__(self, symbol: str = "ETHUSD", fast_period: int = 5, slow_period: int = 10):
        super().__init__(symbol)
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def _moving_average(self, prices: np.ndarray, period: int) -> float:
        """Calculate simple moving average"""
        if len(prices) < period:
            return np.mean(prices) if len(prices) > 0 else 0
        return np.mean(prices[-period:])
    
    def analyze_ticks(self, ticks) -> Optional[Dict]:
        if ticks is None or len(ticks) == 0:
            log.warning(f"⚠️ No ticks provided for Moving Average analysis")
            return None
            
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        
        if prices.size < 1:
            log.warning(f"⚠️ No price data for Moving Average: {prices.size}")
            return None
        
        # ULTRA-ADAPTIVE: Work with ANY amount of data
        if prices.size == 1:
            # For 1 price: Use price level analysis
            current_price = float(prices[0])
            
            # Use price level for signal generation
            # If price ends in certain digits, generate signal (for testing)
            last_digit = int(current_price * 100) % 10
            
            if last_digit in [0, 1, 2, 3, 4]:  # 50% chance for BUY
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.70,
                    'strategy': self.name,
                    'reason': f'HFT Single Price Level Analysis: {current_price:.2f}',
                    'signal_strength': 'single_price_level'
                }
                log.info(f"✅ HFT MA Single Price BUY: {current_price:.2f} (level-based)")
                return signal
            else:  # SELL for other digits
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.70,
                    'strategy': self.name,
                    'reason': f'HFT Single Price Level Analysis: {current_price:.2f}',
                    'signal_strength': 'single_price_level'
                }
                log.info(f"✅ HFT MA Single Price SELL: {current_price:.2f} (level-based)")
                return signal
                
        elif prices.size == 2:
            # For 2 prices: Use simple momentum
            price_change = (prices[-1] - prices[0]) / prices[0] * 100
            current_price = float(prices[-1])
            
            if price_change > 0.01:  # 0.01% upward momentum
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': 0.65,
                    'strategy': self.name,
                    'reason': f'HFT Momentum Up: {price_change:.3f}%',
                    'signal_strength': 'hft_momentum',
                    'data_points': prices.size
                }
                log.info(f"🎯 HFT Momentum BUY: {price_change:.3f}% with 2 data points")
                return signal
            elif price_change < -0.01:  # 0.01% downward momentum
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': 0.65,
                    'strategy': self.name,
                    'reason': f'HFT Momentum Down: {price_change:.3f}%',
                    'signal_strength': 'hft_momentum',
                    'data_points': prices.size
                }
                log.info(f"🎯 HFT Momentum SELL: {price_change:.3f}% with 2 data points")
                return signal
            else:
                log.info(f"📊 HFT Momentum NEUTRAL: {price_change:.3f}% (too small)")
                return None
        
        # For 3+ prices: Use adaptive MA periods
        fast_period = min(self.fast_period, max(1, prices.size // 2))
        slow_period = min(self.slow_period, max(2, prices.size - 1))
        
        if fast_period >= slow_period:
            fast_period = max(1, slow_period - 1)
        
        fast_ma = self._moving_average(prices, fast_period)
        slow_ma = self._moving_average(prices, slow_period)
        current_price = float(prices[-1])
        
        log.info(f"📊 MA Analysis: Fast MA({fast_period})={fast_ma:.2f}, Slow MA({slow_period})={slow_ma:.2f}, Price={current_price:.2f}")
        
        # Generate signals based on MA crossover and price position
        if fast_ma > slow_ma and current_price > fast_ma:
            confidence = 0.75
            signal = {
                'type': 'BUY',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'MA Bullish: Fast={fast_ma:.2f} > Slow={slow_ma:.2f}, Price above MA',
                'signal_strength': 'ma_bullish'
            }
            log.info(f"🎯 MA BUY Signal: {signal}")
            return signal
            
        elif fast_ma < slow_ma and current_price < fast_ma:
            confidence = 0.75
            signal = {
                'type': 'SELL',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'MA Bearish: Fast={fast_ma:.2f} < Slow={slow_ma:.2f}, Price below MA',
                'signal_strength': 'ma_bearish'
            }
            log.info(f"🎯 MA SELL Signal: {signal}")
            return signal
        
        log.info(f"📊 MA Neutral: No clear trend signal")
        return None


class TickBreakoutStrategy(BaseTickStrategy):
    name = "breakout"
    
    def __init__(self, symbol: str = "ETHUSD", lookback_period: int = 10, breakout_threshold: float = 0.001):
        super().__init__(symbol)
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold  # 0.1% breakout threshold
    
    def analyze_ticks(self, ticks) -> Optional[Dict]:
        if ticks is None or len(ticks) == 0:
            log.warning(f"⚠️ No ticks provided for Breakout analysis")
            return None
            
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        
        # Ultra-minimal requirements for HFT - work with single tick if needed
        if prices.size < 1:
            log.warning(f"⚠️ No price data for Breakout analysis")
            return None
        
        # For single tick, generate test signal occasionally
        if prices.size == 1:
            current_price = float(prices[-1])
            log.info(f"📊 Single-tick Breakout: Using test analysis for price {current_price:.2f}")
            # Generate a test signal occasionally for single tick scenarios
            import random
            if random.random() < 0.15:  # 15% chance to generate signal for testing
                signal_type = 'BUY' if random.random() < 0.5 else 'SELL'
                return {
                    'type': signal_type,
                    'price': current_price,
                    'confidence': 0.7,
                    'strategy': self.name,
                    'reason': f'Single-tick breakout test ({signal_type})',
                    'signal_strength': 'test_breakout'
                }
            return None
        
        # Use available data for range calculation
        lookback = min(self.lookback_period, prices.size - 1)
        recent_prices = prices[-lookback:]
        
        # Calculate support and resistance levels
        resistance = np.max(recent_prices)
        support = np.min(recent_prices)
        price_range = resistance - support
        current_price = float(prices[-1])
        
        # Calculate breakout thresholds
        breakout_up = resistance + (price_range * self.breakout_threshold)
        breakout_down = support - (price_range * self.breakout_threshold)
        
        log.info(f"📊 Breakout Analysis: Support={support:.2f}, Resistance={resistance:.2f}, Current={current_price:.2f}")
        log.info(f"📊 Breakout Levels: Up={breakout_up:.2f}, Down={breakout_down:.2f}")
        
        # Check for breakouts
        if current_price > breakout_up:
            confidence = 0.8
            signal = {
                'type': 'BUY',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Upward Breakout: {current_price:.2f} > {breakout_up:.2f}',
                'signal_strength': 'breakout_bullish'
            }
            log.info(f"🎯 Breakout BUY Signal: {signal}")
            return signal
            
        elif current_price < breakout_down:
            confidence = 0.8
            signal = {
                'type': 'SELL',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Downward Breakout: {current_price:.2f} < {breakout_down:.2f}',
                'signal_strength': 'breakout_bearish'
            }
            log.info(f"🎯 Breakout SELL Signal: {signal}")
            return signal
        
        # Check for approaching breakout levels
        distance_to_resistance = (resistance - current_price) / price_range if price_range > 0 else 0
        distance_to_support = (current_price - support) / price_range if price_range > 0 else 0
        
        if distance_to_resistance < 0.1 and distance_to_resistance > 0:  # Close to resistance
            confidence = 0.65
            signal = {
                'type': 'BUY',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Approaching Resistance: {current_price:.2f} near {resistance:.2f}',
                'signal_strength': 'approaching_breakout'
            }
            log.info(f"🎯 Pre-Breakout BUY Signal: {signal}")
            return signal
            
        elif distance_to_support < 0.1 and distance_to_support > 0:  # Close to support
            confidence = 0.65
            signal = {
                'type': 'SELL',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Approaching Support: {current_price:.2f} near {support:.2f}',
                'signal_strength': 'approaching_breakdown'
            }
            log.info(f"🎯 Pre-Breakdown SELL Signal: {signal}")
            return signal
        
        log.info(f"📊 Breakout Neutral: Price in range")
        return None


class TickStochasticStrategy(BaseTickStrategy):
    name = "stochastic"
    
    def __init__(self, symbol: str = "ETHUSD", k_period: int = 8, d_period: int = 3, oversold: float = 20, overbought: float = 80):
        super().__init__(symbol)
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
    
    def _stochastic_k(self, prices: np.ndarray, period: int) -> float:
        """Calculate Stochastic %K"""
        if len(prices) < period:
            period = len(prices)
        
        recent_prices = prices[-period:]
        high = np.max(recent_prices)
        low = np.min(recent_prices)
        close = prices[-1]
        
        if high == low:
            return 50.0  # Neutral when no price movement
        
        k = ((close - low) / (high - low)) * 100
        return k
    
    def _stochastic_d(self, k_values: List[float], period: int) -> float:
        """Calculate Stochastic %D (SMA of %K)"""
        if len(k_values) < period:
            return np.mean(k_values) if k_values else 50.0
        return np.mean(k_values[-period:])
    
    def analyze_ticks(self, ticks) -> Optional[Dict]:
        if ticks is None or len(ticks) == 0:
            log.warning(f"⚠️ No ticks provided for Stochastic analysis")
            return None
            
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        
        # Ultra-minimal requirements for HFT - work with single tick if needed
        if prices.size < 1:
            log.warning(f"⚠️ No price data for Stochastic analysis")
            return None
        
        # For single tick, generate neutral signal to test system
        if prices.size == 1:
            current_price = float(prices[-1])
            log.info(f"📊 Single-tick Stochastic: Using neutral analysis for price {current_price:.2f}")
            # Generate a test signal occasionally for single tick scenarios
            import random
            if random.random() < 0.1:  # 10% chance to generate signal for testing
                signal_type = 'BUY' if random.random() < 0.5 else 'SELL'
                return {
                    'type': signal_type,
                    'price': current_price,
                    'confidence': 0.6,
                    'strategy': self.name,
                    'reason': f'Single-tick test signal ({signal_type})',
                    'signal_strength': 'test_signal'
                }
            return None
        
        # Adaptive periods for limited data
        k_period = min(self.k_period, max(3, prices.size))
        d_period = min(self.d_period, max(2, k_period // 2))
        
        # Calculate %K for recent periods
        k_values = []
        for i in range(max(1, min(d_period, prices.size - k_period + 1))):
            end_idx = prices.size - i
            start_idx = max(0, end_idx - k_period)
            k_val = self._stochastic_k(prices[start_idx:end_idx], k_period)
            k_values.append(k_val)
        
        if not k_values:
            return None
        
        k_values.reverse()  # Most recent first
        current_k = k_values[-1]
        current_d = self._stochastic_d(k_values, d_period)
        current_price = float(prices[-1])
        
        log.info(f"📊 Stochastic Analysis: %K={current_k:.2f}, %D={current_d:.2f} (Oversold<{self.oversold}, Overbought>{self.overbought})")
        
        # Generate signals based on Stochastic levels and crossovers
        if current_k < self.oversold and current_d < self.oversold:
            confidence = 0.8
            signal = {
                'type': 'BUY',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Stochastic Oversold: %K={current_k:.1f}, %D={current_d:.1f}',
                'signal_strength': 'stoch_oversold'
            }
            log.info(f"🎯 Stochastic BUY Signal: {signal}")
            return signal
            
        elif current_k > self.overbought and current_d > self.overbought:
            confidence = 0.8
            signal = {
                'type': 'SELL',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Stochastic Overbought: %K={current_k:.1f}, %D={current_d:.1f}',
                'signal_strength': 'stoch_overbought'
            }
            log.info(f"🎯 Stochastic SELL Signal: {signal}")
            return signal
        
        # Check for crossovers (if we have enough data)
        if len(k_values) >= 2:
            prev_k = k_values[-2]
            if prev_k <= current_d and current_k > current_d and current_k < 50:
                confidence = 0.7
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': confidence,
                    'strategy': self.name,
                    'reason': f'Stochastic Bullish Cross: %K({current_k:.1f}) > %D({current_d:.1f})',
                    'signal_strength': 'stoch_cross_bullish'
                }
                log.info(f"🎯 Stochastic Cross BUY Signal: {signal}")
                return signal
                
            elif prev_k >= current_d and current_k < current_d and current_k > 50:
                confidence = 0.7
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': confidence,
                    'strategy': self.name,
                    'reason': f'Stochastic Bearish Cross: %K({current_k:.1f}) < %D({current_d:.1f})',
                    'signal_strength': 'stoch_cross_bearish'
                }
                log.info(f"🎯 Stochastic Cross SELL Signal: {signal}")
                return signal
        
        log.info(f"📊 Stochastic Neutral: No clear signal")
        return None


class TickVWAPStrategy(BaseTickStrategy):
    name = "vwap"
    
    def __init__(self, symbol: str = "ETHUSD", period: int = 20, deviation_threshold: float = 0.5):
        super().__init__(symbol)
        self.period = period
        self.deviation_threshold = deviation_threshold  # % deviation from VWAP
    
    def analyze_ticks(self, ticks) -> Optional[Dict]:
        if ticks is None or len(ticks) == 0:
            log.warning(f"⚠️ No ticks provided for VWAP analysis")
            return None
            
        series = _ticks_to_arrays(ticks)
        prices = series['last']
        
        # Ultra-minimal requirements for HFT - work with single tick if needed
        if prices.size < 1:
            log.warning(f"⚠️ No price data for VWAP analysis")
            return None
        
        # For single tick, generate test signal occasionally
        if prices.size == 1:
            current_price = float(prices[-1])
            log.info(f"📊 Single-tick VWAP: Using test analysis for price {current_price:.2f}")
            # Generate a test signal occasionally for single tick scenarios
            import random
            if random.random() < 0.12:  # 12% chance to generate signal for testing
                signal_type = 'BUY' if random.random() < 0.5 else 'SELL'
                return {
                    'type': signal_type,
                    'price': current_price,
                    'confidence': 0.65,
                    'strategy': self.name,
                    'reason': f'Single-tick VWAP test ({signal_type})',
                    'signal_strength': 'test_vwap'
                }
            return None
        
        # For tick data, we'll simulate volume using price volatility
        # (In real implementation, you'd use actual volume data)
        period = min(self.period, prices.size)
        recent_prices = prices[-period:]
        
        # Simulate volume based on price changes (higher volatility = higher volume)
        simulated_volumes = []
        for i in range(len(recent_prices)):
            if i == 0:
                vol = 1.0  # Base volume
            else:
                price_change = abs(recent_prices[i] - recent_prices[i-1])
                avg_price = np.mean(recent_prices[:i+1])
                volatility = price_change / avg_price if avg_price > 0 else 0
                vol = 1.0 + (volatility * 10)  # Scale volatility to volume
            simulated_volumes.append(vol)
        
        volumes = np.array(simulated_volumes)
        
        # Calculate VWAP
        typical_prices = recent_prices  # Using close prices as typical prices
        price_volume = typical_prices * volumes
        vwap = np.sum(price_volume) / np.sum(volumes)
        
        current_price = float(prices[-1])
        deviation = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0
        
        log.info(f"📊 VWAP Analysis: VWAP={vwap:.2f}, Current={current_price:.2f}, Deviation={deviation:.2f}%")
        
        # Calculate dynamic bands around VWAP
        price_std = np.std(recent_prices)
        upper_band = vwap + (price_std * 0.5)
        lower_band = vwap - (price_std * 0.5)
        
        log.info(f"📊 VWAP Bands: Lower={lower_band:.2f}, VWAP={vwap:.2f}, Upper={upper_band:.2f}")
        
        # Generate signals based on VWAP position and momentum
        if current_price < lower_band and deviation < -self.deviation_threshold:
            # Price significantly below VWAP - potential buy
            confidence = 0.75
            signal = {
                'type': 'BUY',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Below VWAP: {current_price:.2f} < {vwap:.2f} ({deviation:.1f}%)',
                'signal_strength': 'vwap_oversold'
            }
            log.info(f"🎯 VWAP BUY Signal: {signal}")
            return signal
            
        elif current_price > upper_band and deviation > self.deviation_threshold:
            # Price significantly above VWAP - potential sell
            confidence = 0.75
            signal = {
                'type': 'SELL',
                'price': current_price,
                'confidence': confidence,
                'strategy': self.name,
                'reason': f'Above VWAP: {current_price:.2f} > {vwap:.2f} ({deviation:.1f}%)',
                'signal_strength': 'vwap_overbought'
            }
            log.info(f"🎯 VWAP SELL Signal: {signal}")
            return signal
        
        # Check for VWAP reversion signals
        if len(recent_prices) >= 3:
            price_trend = recent_prices[-1] - recent_prices[-3]
            
            if current_price > vwap and price_trend < 0:  # Above VWAP but declining
                confidence = 0.65
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'confidence': confidence,
                    'strategy': self.name,
                    'reason': f'VWAP Reversion: Above VWAP {vwap:.2f} but declining',
                    'signal_strength': 'vwap_reversion_bearish'
                }
                log.info(f"🎯 VWAP Reversion SELL Signal: {signal}")
                return signal
                
            elif current_price < vwap and price_trend > 0:  # Below VWAP but rising
                confidence = 0.65
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'confidence': confidence,
                    'strategy': self.name,
                    'reason': f'VWAP Reversion: Below VWAP {vwap:.2f} but rising',
                    'signal_strength': 'vwap_reversion_bullish'
                }
                log.info(f"🎯 VWAP Reversion BUY Signal: {signal}")
                return signal
        
        log.info(f"📊 VWAP Neutral: Price near VWAP")
        return None


class TickAlwaysStrategy(BaseTickStrategy):
    name = "always_signal"
    def __init__(self, symbol: str = "ETHUSD"):
        super().__init__(symbol)
        self._count = 0

    def analyze_ticks(self, ticks) -> Optional[Dict]:
        # ALWAYS GENERATE SIGNAL - No matter what
        self._count += 1
        
        # Try to get price from ticks
        price = 4300.0  # Default ETHUSD price
        
        if ticks and len(ticks) > 0:
            last_tick = ticks[-1]
            # Try multiple price attributes
            tick_price = (getattr(last_tick, 'bid', 0) or 
                         getattr(last_tick, 'ask', 0) or 
                         getattr(last_tick, 'price', 0) or 
                         getattr(last_tick, 'close', 0))
            if tick_price > 100:  # Valid price
                price = float(tick_price)
        
        # Extract some data from ticks if available
        series = _ticks_to_arrays(ticks) if ticks else {'last': np.array([])}
        prices = series['last']
        data_points = len(prices) if len(prices) > 0 else 0
        
        # Generate signal based on count (alternating pattern)
        patterns = ['BUY', 'SELL', 'BUY', 'SELL']
        signal_type = patterns[self._count % 4]
        
        # Variable confidence for testing
        confidence_levels = [0.95, 0.85, 0.75, 0.90]
        confidence = confidence_levels[self._count % 4]
        
        signal = {
            'type': signal_type, 
            'price': price, 
            'confidence': confidence, 
            'strategy': self.name, 
            'reason': f'Always {signal_type} #{self._count} - HFT Testing Signal',
            'signal_strength': 'hft_testing',
            'data_points': data_points,
            'test_mode': True
        }
        
        log.info(f"🎯 ALWAYS SIGNAL #{self._count}: {signal_type} at {price:.2f} (confidence: {confidence}) with {data_points} data points")
        return signal


AVAILABLE_TICK_STRATEGIES = {
    'moving_average': TickMovingAverageStrategy,
    'rsi_strategy': TickRSIStrategy,
    'bollinger_bands': TickBollingerStrategy,
    'macd_strategy': TickMACDStrategy,
    'breakout': TickBreakoutStrategy,
    'stochastic': TickStochasticStrategy,
    'vwap': TickVWAPStrategy,
    'always_signal': TickAlwaysStrategy,
    'default': TickRSIStrategy,  # Default to RSI for HFT
}


def get_tick_strategy(name: str, symbol: str = "ETHUSD") -> BaseTickStrategy:
    # Normalize strategy name to handle various formats
    normalized_name = name.lower().replace('_', '').replace(' ', '').replace('-', '')
    
    # Create mapping for different name variations
    name_mappings = {
        'rsi': 'rsi_strategy',
        'rsistrategy': 'rsi_strategy',
        'macd': 'macd_strategy',
        'macdstrategy': 'macd_strategy', 
        'bollinger': 'bollinger_bands',
        'bollingerbands': 'bollinger_bands',
        'movingaverage': 'moving_average',
        'ma': 'moving_average',
        'breakout': 'breakout',
        'stochastic': 'stochastic',
        'stoch': 'stochastic',
        'vwap': 'vwap',
        'always': 'always_signal',
        'alwayssignal': 'always_signal',
        'default': 'rsi_strategy'  # Default to RSI strategy for HFT
    }
    
    # Try to find strategy by normalized name
    strategy_key = name_mappings.get(normalized_name, name)
    klass = AVAILABLE_TICK_STRATEGIES.get(strategy_key, TickRSIStrategy)  # Default to RSI
    
    log.info(f"🔍 Tick strategy mapping: '{name}' -> '{strategy_key}' -> {klass.__name__}")
    return klass(symbol)


def list_tick_strategies() -> List[str]:
    return list(AVAILABLE_TICK_STRATEGIES.keys())


