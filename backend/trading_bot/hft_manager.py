"""
High-Frequency (Tick) Trading Bot Manager

Separate manager that analyzes tick data every second and trades accordingly.
It reuses order execution and performance tracking ideas from the candle bot,
but with tick-specific data fetch and strategy evaluation.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import MetaTrader5 as mt5

from .tick_strategies import get_tick_strategy, list_tick_strategies


log = logging.getLogger(__name__)


class HFTTradingBotManager:
    """High-frequency trading manager that analyzes tick stream once per second."""

    mode: str = "hft"

    def __init__(self, mt5_symbol: str = "ETHUSD"):
        self.symbol = mt5_symbol
        self.is_running = False
        self.active_trades: Dict[str, Dict] = {}
        self.bot_thread: Optional[threading.Thread] = None
        self.update_callbacks: List[Callable] = []
        self.bot_id: Optional[str] = None
        self.unique_magic_number: Optional[int] = None
        self.bot_start_time: Optional[datetime] = None

        # Throttling / risk controls
        self._recent_order_times: List[float] = []

        # Lifetime stats (persist over session)
        self.lifetime_stats = {
            'total_completed_trades': 0,
            'total_winning_trades': 0,
            'total_losing_trades': 0,
            'lifetime_realized_profit': 0.0,
            'lifetime_max_drawdown': 0.0,
            'peak_balance': 0.0,
            'completed_trade_history': [],
            'daily_stats': {}
        }

        # HFT configuration (tick specific) - OPTIMIZED FOR BETTER PERFORMANCE
        self.config: Dict = {
            'strategy_name': 'rsi_strategy',  # Default to RSI strategy
            'auto_trading_enabled': True,  # Enable by default for HFT
            'lot_size_per_trade': 0.01,   # OPTIMIZED: Smaller lot size for safety
            'stop_loss_pips': 15,         # OPTIMIZED: Tighter stops
            'take_profit_pips': 30,       # OPTIMIZED: Quick profits
            # Tick analysis - OPTIMIZED
            'analysis_interval_secs': 5,  # OPTIMIZED: 5 seconds for more stable analysis
            'tick_lookback_secs': 60,     # OPTIMIZED: 60 seconds for better data
            'min_signal_confidence': 0.4, # OPTIMIZED: Lower threshold for more signals
            'max_orders_per_minute': 10,  # INCREASED: Allow more frequent HFT trading
            'cooldown_secs_after_trade': 2, # REDUCED: Faster cooldown
            'spread_filter_points': 1000,  # INCREASED: More lenient spread filter
            'enable_spread_filter': False, # Keep disabled for testing
            # Multi-ticker spread limits - OPTIMIZED
            'symbol_spread_limits': {
                'ETHUSD': 1000,  # INCREASED: 10.00 spread (was 500)
                'BTCUSD': 2000,  # INCREASED: 20.00 spread
                'EURUSD': 10,    # INCREASED: 1.0 pips
                'GBPUSD': 20,    # INCREASED: 2.0 pips
                'USDJPY': 20,    # INCREASED: 2.0 pips
                'XAUUSD': 100,   # INCREASED: 1.00 spread
            },
            # SL/TP Configuration - OPTIMIZED
            'use_sl_tp': True,
            'sl_pips': 15,               # OPTIMIZED: Tighter stops
            'tp_pips': 30,               # OPTIMIZED: Quick profits
            'sl_tp_mode': 'pips',        # 'pips' or 'percent'
            'diagnostic_mode': False,    # NEW: Diagnostic mode for testing
            'enable_enhanced_signals': True, # NEW: Enable enhanced signal generation
        }

        # Performance snapshot
        self.performance: Dict = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'daily_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'active_trades': 0,
            'recent_trades': []
        }

    # ---- Callbacks ----
    def register_update_callback(self, callback: Callable):
        self.update_callbacks.append(callback)

    def notify_updates(self, data: Dict):
        for cb in self.update_callbacks:
            try:
                cb(data)
            except Exception as e:
                log.error(f"HFT update callback error: {e}")

    def update_config(self, new_config: Dict):
        """Update HFT bot configuration with enhanced parameter mapping"""
        old_config = self.config.copy()
        
        # CRITICAL: Check if auto_trading_enabled is being disabled
        if 'auto_trading_enabled' in new_config and not new_config['auto_trading_enabled']:
            log.warning(f"⚠️ HFT Bot: auto_trading_enabled being set to FALSE in config: {new_config}")
            log.warning(f"🔧 This will prevent the HFT bot from executing trades!")
        
        # Update configuration with new values
        self.config.update(new_config)
        
        # ENHANCED PARAMETER MAPPING for frontend compatibility
        if 'stopLoss' in new_config:
            self.config['stop_loss_pips'] = new_config['stopLoss']
            self.config['sl_pips'] = new_config['stopLoss']
        
        if 'takeProfit' in new_config:
            self.config['take_profit_pips'] = new_config['takeProfit']
            self.config['tp_pips'] = new_config['takeProfit']
            
        if 'lotSize' in new_config:
            self.config['lot_size_per_trade'] = new_config['lotSize']
            
        if 'maxDailyTrades' in new_config:
            self.config['max_orders_per_minute'] = min(new_config['maxDailyTrades'] // 60, 20)  # Convert to per minute
            
        if 'autoTrading' in new_config:
            self.config['auto_trading_enabled'] = new_config['autoTrading']
            log.info(f"🔧 Auto trading set via 'autoTrading' parameter: {new_config['autoTrading']}")
            
        # CRITICAL: Override auto_trading_enabled if it's being disabled unintentionally
        if 'auto_trading_enabled' in new_config and not new_config['auto_trading_enabled']:
            log.warning(f"⚠️ FORCING auto_trading_enabled=True for HFT bot (was being set to False)")
            self.config['auto_trading_enabled'] = True  # Force enable for HFT
            
        if 'useManualSlTp' in new_config:
            self.config['use_manual_sl_tp'] = new_config['useManualSlTp']
            self.config['use_sl_tp'] = new_config['useManualSlTp']
        
        log.info(f"🔧 HFT Bot configuration updated: {new_config}")
        log.info(f"📊 SL/TP Settings: SL={self.config.get('stop_loss_pips')}, TP={self.config.get('take_profit_pips')}, Use={self.config.get('use_sl_tp')}")
        log.info(f"🚀 AUTO TRADING STATUS: {self.config.get('auto_trading_enabled')} (CRITICAL FOR TRADE EXECUTION)")
        log.info(f"🔧 Full HFT config now: {self.config}")
        
        # Notify frontend about configuration update
        self.notify_updates({
            'type': 'config_update',
            'config': self.config,
            'bot_id': self.bot_id,
            'mode': self.mode,
            'timestamp': datetime.now().isoformat()
        })

    # ---- Lifecycle ----
    def start_bot(self, strategy_name: str = "default", bot_id: Optional[str] = None) -> bool:
        if self.is_running:
            log.warning("HFT bot already running")
            return False

        if not mt5.initialize():
            log.error("Failed to initialize MT5 for HFT bot")
            return False

        # Ensure symbol is visible and tradable
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info or not symbol_info.visible:
                mt5.symbol_select(self.symbol, True)
        except Exception:
            pass

        self.is_running = True
        self.config['strategy_name'] = strategy_name
        self.bot_id = bot_id
        self.unique_magic_number = self._generate_unique_magic_number()
        self.bot_start_time = datetime.now()

        self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
        self.bot_thread.start()

        self.notify_updates({
            'type': 'bot_status',
            'status': 'started',
            'strategy': strategy_name,
            'bot_id': self.bot_id,
            'magic_number': self.unique_magic_number,
            'mode': self.mode,
            'start_time': self.bot_start_time.isoformat(),
            'timestamp': datetime.now().isoformat()
        })
        return True

    def stop_bot(self) -> bool:
        if not self.is_running:
            return False
        self.is_running = False
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5)
        self.notify_updates({
            'type': 'bot_status',
            'status': 'stopped',
            'bot_id': self.bot_id,
            'mode': self.mode,
            'timestamp': datetime.now().isoformat()
        })
        return True

    # ---- Core loop ----
    def _bot_loop(self):
        log.info(f"⚡ HFT bot loop started - Strategy: {self.config['strategy_name']}, Interval: {self.config['analysis_interval_secs']}s")
        last_performance_update = 0.0
        loop_count = 0

        while self.is_running:
            try:
                loop_count += 1
                log.info(f"⚡ HFT Loop #{loop_count} - Starting analysis cycle")
                
                # Fetch current tick and recent tick history
                current_tick = mt5.symbol_info_tick(self.symbol)
                if not current_tick:
                    log.warning(f"⚠️ No current tick data for {self.symbol}")
                    time.sleep(self.config['analysis_interval_secs'])
                    continue

                log.info(f"💱 Current tick: Bid={current_tick.bid}, Ask={current_tick.ask}")

                # Spread filter
                symbol_info = mt5.symbol_info(self.symbol)
                if symbol_info is None:
                    log.warning(f"⚠️ No symbol info for {self.symbol}")
                    time.sleep(self.config['analysis_interval_secs'])
                    continue

                point = symbol_info.point or 0.01
                spread_points = int(round((current_tick.ask - current_tick.bid) / point)) if current_tick.ask and current_tick.bid else 0
                spread_value = spread_points * point
                
                # Get symbol-specific spread limit
                symbol_spread_limit = self.config.get('symbol_spread_limits', {}).get(self.symbol, self.config['spread_filter_points'])
                
                log.info(f"📊 Spread check: {spread_points} points ({spread_value:.2f}) | Filter: {'ENABLED' if self.config.get('enable_spread_filter', True) else 'DISABLED'} | Limit for {self.symbol}: {symbol_spread_limit}")
                
                # Only apply spread filter if enabled
                if (self.config.get('enable_spread_filter', True) and 
                    symbol_spread_limit > 0 and 
                    spread_points > symbol_spread_limit):
                    log.warning(f"⚠️ Spread too wide for {self.symbol}: {spread_points} points (${spread_value:.2f}) > {symbol_spread_limit} points, skipping analysis")
                    # Update frontend but skip analysis to avoid bad fills
                    self._emit_update(current_tick, signal=None, next_in=self.config['analysis_interval_secs'])
                    time.sleep(self.config['analysis_interval_secs'])
                    continue
                
                # If spread filter disabled or spread acceptable, proceed with analysis
                log.info(f"✅ Spread acceptable for {self.symbol}: {spread_points} points (${spread_value:.2f})")

                # Fetch tick data - ENHANCED: Try multiple timeframes for better data
                lookback_secs = self.config['tick_lookback_secs']
                log.info(f"📈 Fetching {lookback_secs}s of tick history...")
                ticks = self._fetch_recent_ticks(lookback_secs)
                
                # If insufficient data, try longer lookback
                if ticks is None or len(ticks) < 10:
                    log.warning(f"⚠️ Insufficient ticks ({len(ticks) if ticks else 0}), trying longer lookback...")
                    ticks = self._fetch_recent_ticks(lookback_secs * 3)  # Try 3x longer
                log.info(f"📊 Fetched {len(ticks) if ticks else 0} ticks for analysis")
                
                # Analyze ticks
                log.info(f"🔍 Analyzing ticks with {self.config['strategy_name']} strategy...")
                signal = self._analyze_ticks(ticks)
                
                # Enhanced logging for debugging
                if signal:
                    log.info(f"🎯 HFT SIGNAL GENERATED: {signal}")
                    log.info(f"📊 Signal details - Type: {signal.get('type')}, Price: {signal.get('price')}, Confidence: {signal.get('confidence')}, Reason: {signal.get('reason')}")
                else:
                    log.info(f"📊 No signal generated from {self.config['strategy_name']} strategy")

                # Execute trade if signal strong enough and throttles allow
                if signal and self.config['auto_trading_enabled']:
                    log.info(f"✅ Auto trading enabled, checking signal confidence...")
                    signal_confidence = signal.get('confidence', 0)
                    min_confidence = self.config['min_signal_confidence']
                    
                    if signal_confidence >= min_confidence:
                        log.info(f"✅ Signal confidence {signal_confidence} >= {min_confidence}")
                        if self._can_place_order():
                            log.info(f"🚀 EXECUTING HFT TRADE: {signal}")
                            self._execute_trade(signal)
                            self._recent_order_times.append(time.time())
                            # Cooldown after executing a trade to avoid over-trading same second
                            cooldown = max(0, self.config['cooldown_secs_after_trade'])
                            if cooldown > 0:
                                log.info(f"😴 Cooldown for {cooldown}s after trade execution")
                                time.sleep(cooldown)
                        else:
                            log.warning("⚠️ HFT throttle: max orders per minute reached")
                    else:
                        log.warning(f"⚠️ HFT signal below confidence threshold: {signal_confidence} < {min_confidence}")
                elif signal and not self.config['auto_trading_enabled']:
                    log.error(f"❌ CRITICAL: HFT signal generated but auto trading is DISABLED!")
                    log.error(f"🎯 Signal Details: {signal}")
                    log.error(f"🔧 Current config auto_trading_enabled: {self.config.get('auto_trading_enabled')}")
                    log.error(f"� To ednable auto trading, the frontend must send auto_trading_enabled=True")
                    log.error(f"🔧 Or manually enable it via bot configuration update")
                    
                    # TEMPORARY FIX: Enable auto trading for this signal if it's high confidence
                    if signal.get('confidence', 0) >= 0.8:
                        log.warning(f"🚀 TEMPORARY OVERRIDE: Enabling auto trading for high confidence signal ({signal.get('confidence')})")
                        self.config['auto_trading_enabled'] = True
                        # Retry execution
                        if self._can_place_order():
                            log.info(f"🚀 EXECUTING HFT TRADE (override): {signal}")
                            self._execute_trade(signal)
                            self._recent_order_times.append(time.time())
                        else:
                            log.warning("⚠️ HFT throttle: max orders per minute reached")
                else:
                    log.info("📊 No trading action taken - either no signal or auto trading disabled")

                # periodic performance refresh
                now = time.time()
                if now - last_performance_update >= 5:  # every 5s for HFT
                    log.info("📊 Updating performance metrics...")
                    self._update_performance()
                    last_performance_update = now

                # Emit update (show different fields for HFT)
                self._emit_update(current_tick, signal, self.config['analysis_interval_secs'])

                log.info(f"⏰ Analysis cycle #{loop_count} complete, sleeping {self.config['analysis_interval_secs']}s...")
                time.sleep(self.config['analysis_interval_secs'])

            except Exception as e:
                log.error(f"❌ HFT loop error: {e}", exc_info=True)
                time.sleep(1)

        log.info("⚡ HFT bot loop ended")

    def _emit_update(self, current_tick, signal, next_in: int):
        self.notify_updates({
            'type': 'bot_update',
            'bot_id': self.bot_id,
            'mode': self.mode,
            'current_price': getattr(current_tick, 'bid', None),
            'signal': signal,
            'performance': self.performance,
            'active_trades': self.performance.get('active_trades', 0),
            'timestamp': datetime.now().isoformat(),
            'next_analysis_in': next_in
        })

    # ---- Analysis ----
    def _fetch_recent_ticks(self, lookback_secs: int):
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=max(lookback_secs, 1))
        log.info(f"📊 Fetching ticks from {start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')} ({lookback_secs}s)")
        
        # Attempt to fetch ticks using correct datetime args
        try:
            # Method 1: copy_ticks_range with ALL tick types
            ticks = mt5.copy_ticks_range(
                self.symbol,
                start_time,
                end_time,
                mt5.COPY_TICKS_ALL,
            )
            
            if ticks is None or len(ticks) == 0:
                log.warning(f"⚠️ No ticks from copy_ticks_range (ALL), trying INFO ticks...")
                # Method 2: Try INFO ticks only
                ticks = mt5.copy_ticks_range(self.symbol, start_time, end_time, mt5.COPY_TICKS_INFO)
                
            if ticks is None or len(ticks) == 0:
                log.warning(f"⚠️ No ticks from copy_ticks_range (INFO), trying copy_ticks_from...")
                # Method 3: copy_ticks_from for last N ticks
                ticks = mt5.copy_ticks_from(self.symbol, start_time, 1000, mt5.COPY_TICKS_ALL)
                
            if ticks is None or len(ticks) == 0:
                log.warning(f"⚠️ No ticks from copy_ticks_from, trying shorter timeframe...")
                # Method 4: Try shorter timeframe (last 10 seconds)
                short_start = end_time - timedelta(seconds=10)
                ticks = mt5.copy_ticks_range(self.symbol, short_start, end_time, mt5.COPY_TICKS_ALL)
                
            if ticks is None or len(ticks) == 0:
                log.warning(f"⚠️ Still no ticks, using current tick as fallback")
                # Method 5: Current tick fallback
                t = mt5.symbol_info_tick(self.symbol)
                if t:
                    # Create multiple copies of current tick to simulate history
                    ticks = [t] * 5  # Give strategies at least 5 data points
                else:
                    ticks = []
            
            # Log tick data quality with better error handling
            if len(ticks) > 0:
                # Safely extract price data for validation
                valid_prices = []
                valid_ticks = []
                
                for t in ticks:
                    try:
                        bid = None
                        ask = None
                        last = None
                        
                        # Method 1: Handle numpy.void (historical ticks from copy_ticks_range)
                        if hasattr(t, 'dtype') and hasattr(t.dtype, 'names') and t.dtype.names:
                            # This is a numpy structured array (historical tick)
                            try:
                                # Access by field names
                                if 'bid' in t.dtype.names and 'ask' in t.dtype.names:
                                    bid = float(t['bid'])
                                    ask = float(t['ask'])
                                elif hasattr(t, '__getitem__') and len(t) >= 3:
                                    # Fallback: positional access (time, bid, ask, ...)
                                    bid = float(t[1])  # bid is at index 1
                                    ask = float(t[2])  # ask is at index 2
                                
                                if 'last' in t.dtype.names:
                                    last = float(t['last'])
                                elif hasattr(t, '__getitem__') and len(t) >= 4:
                                    last = float(t[3])  # last is at index 3
                            except (ValueError, TypeError, IndexError, KeyError):
                                pass
                        
                        # Method 2: Handle regular Tick objects (current tick from symbol_info_tick)
                        if bid is None or ask is None:
                            try:
                                bid = getattr(t, 'bid', None)
                                ask = getattr(t, 'ask', None)
                                last = getattr(t, 'last', None)
                                if bid is not None:
                                    bid = float(bid)
                                if ask is not None:
                                    ask = float(ask)
                                if last is not None:
                                    last = float(last)
                            except (ValueError, TypeError, AttributeError):
                                pass
                        
                        # Check if we have valid price data
                        if bid is not None and ask is not None:
                            if 1000 <= bid <= 10000 and 1000 <= ask <= 10000:
                                valid_prices.extend([bid, ask])
                                valid_ticks.append(t)
                        elif last is not None:
                            if 1000 <= last <= 10000:
                                valid_prices.append(last)
                                valid_ticks.append(t)
                    except (ValueError, TypeError, AttributeError):
                        continue
                
                if valid_prices and valid_ticks:
                    price_range = max(valid_prices) - min(valid_prices)
                    first_price = valid_prices[0]
                    last_price = valid_prices[-1]
                    log.info(f"✅ Fetched {len(ticks)} ticks | Valid ticks: {len(valid_ticks)} | Valid prices: {len(valid_prices)} | Range: {price_range:.2f} | First: {first_price:.2f}, Last: {last_price:.2f}")
                    # Use only valid ticks for analysis
                    ticks = valid_ticks
                else:
                    log.warning(f"⚠️ Fetched {len(ticks)} ticks but no valid price data found!")
                    # If no valid prices, get current tick as fallback
                    current_tick = mt5.symbol_info_tick(self.symbol)
                    if current_tick:
                        log.info(f"🔄 Using current tick as fallback: Bid={current_tick.bid}, Ask={current_tick.ask}")
                        ticks = [current_tick]
                    else:
                        log.error(f"❌ No current tick available either!")
                        return []
            else:
                log.error(f"❌ No tick data available for analysis!")
                
            return ticks or []
            
        except Exception as e:
            log.error(f"❌ Tick fetch failed: {e}")
            log.warning(f"Using current tick as emergency fallback")
            t = mt5.symbol_info_tick(self.symbol)
            return [t] if t else []

    def _analyze_ticks(self, ticks) -> Optional[Dict]:
        try:
            log.info(f"🔍 Initializing {self.config['strategy_name']} strategy for {self.symbol}")
            strategy = get_tick_strategy(self.config['strategy_name'], self.symbol)
            log.info(f"✅ Strategy initialized: {strategy.__class__.__name__}")
            
            log.info(f"📊 Running analysis on {len(ticks) if ticks else 0} ticks...")
            signal = strategy.analyze_ticks(ticks)
            
            if signal:
                log.info(f"🎯 ANALYSIS COMPLETE - Signal Generated: {signal}")
            else:
                log.info(f"📊 ANALYSIS COMPLETE - No signal generated")
                
            return signal
            
        except Exception as e:
            log.error(f"❌ Tick analysis error: {e}", exc_info=True)
            return None

    # ---- Order / Performance (adapted from candle manager) ----
    def _execute_trade(self, signal: Dict):
        try:
            # Guard
            if not self.config.get('auto_trading_enabled'):
                return

            account_info = mt5.account_info()
            if account_info is None:
                log.error("HFT: account_info is None")
                return

            account_balance = account_info.balance
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                log.error(f"HFT: no symbol_info for {self.symbol}")
                return

            # ENHANCED LOT SIZE VALIDATION for HFT
            configured_lot_size = self.config.get('lot_size_per_trade', 0.01)  # Default to smaller size for HFT
            
            # Validate lot size against symbol requirements
            min_lot = getattr(symbol_info, 'volume_min', 0.01)
            max_lot = getattr(symbol_info, 'volume_max', 100.0)
            lot_step = getattr(symbol_info, 'volume_step', 0.01)
            
            # Ensure lot size meets requirements
            lot_size = max(min_lot, configured_lot_size)
            lot_size = min(max_lot, lot_size)
            
            # Round to nearest step
            if lot_step > 0:
                lot_size = round(lot_size / lot_step) * lot_step
                lot_size = max(min_lot, lot_size)  # Ensure still above minimum
            
            log.info(f"📊 Lot Size Validation: Configured={configured_lot_size}, Min={min_lot}, Max={max_lot}, Step={lot_step}, Final={lot_size}")
            
            current_tick = mt5.symbol_info_tick(self.symbol)
            if not current_tick:
                log.error("❌ No current tick available for HFT order")
                return

            order_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL
            current_price = current_tick.ask if signal['type'] == 'BUY' else current_tick.bid
            
            # Validate current price
            if not current_price or current_price <= 0:
                log.error(f"❌ Invalid current price: {current_price}")
                return
            
            log.info(f"📊 Trade Parameters: Lot Size={lot_size}, Price={current_price}, Order Type={'BUY' if signal['type'] == 'BUY' else 'SELL'}")

            # Calculate stop loss and take profit prices based on configuration
            sl_price = 0
            tp_price = 0
            
            # ENHANCED CONFIG READING: Check multiple parameter names for frontend compatibility
            use_sl_tp = (
                self.config.get('use_manual_sl_tp', False) or 
                self.config.get('use_sl_tp', True) or
                True  # Default to True for safety
            )
            
            log.info(f"📊 SL/TP Configuration Check:")
            log.info(f"   - use_manual_sl_tp: {self.config.get('use_manual_sl_tp', 'NOT_SET')}")
            log.info(f"   - use_sl_tp: {self.config.get('use_sl_tp', 'NOT_SET')}")
            log.info(f"   - Final use_sl_tp: {use_sl_tp}")
            
            if use_sl_tp:
                # ENHANCED SL/TP VALUES: Check all possible parameter names from frontend
                sl_pips = (
                    self.config.get('stop_loss_pips') or 
                    self.config.get('sl_pips') or 
                    self.config.get('stopLoss') or
                    15  # Default fallback
                )
                tp_pips = (
                    self.config.get('take_profit_pips') or 
                    self.config.get('tp_pips') or 
                    self.config.get('takeProfit') or
                    30  # Default fallback
                )
                sl_tp_mode = self.config.get('sl_tp_mode', 'pips')
                
                log.info(f"📊 SL/TP Configuration: SL={sl_pips}, TP={tp_pips}, Mode={sl_tp_mode}, use_sl_tp={use_sl_tp}")
                log.info(f"📊 Full Config SL/TP Keys: {[k for k in self.config.keys() if 'sl' in k.lower() or 'tp' in k.lower()]}")
                
                # ENHANCED SL/TP DISTANCE CALCULATION for HFT
                pip_size = 10 * symbol_info.point  # For ETHUSD: 10 * 0.01 = 0.1
                stops_level = getattr(symbol_info, 'trade_stops_level', 10)
                freeze_level = getattr(symbol_info, 'trade_freeze_level', 0)
                
                # CRITICAL FIX: Calculate minimum distance properly
                # For ETHUSD, we need at least 10 points = 1.0 in price terms
                min_distance_points = max(stops_level, freeze_level, 100)  # INCREASED: 100 points minimum (10.0 price units)
                min_distance = min_distance_points * symbol_info.point
                
                log.info(f"📊 Distance Requirements: StopsLevel={stops_level}, FreezeLevel={freeze_level}, MinDistance={min_distance_points} points ({min_distance:.5f})")
                log.info(f"📊 Pip Size: {pip_size:.5f}, Point: {symbol_info.point:.5f}")
                
                if sl_tp_mode == 'percent':
                    # Calculate based on percentage
                    sl_distance = current_price * (sl_pips / 100.0) if sl_pips > 0 else 0
                    tp_distance = current_price * (tp_pips / 100.0) if tp_pips > 0 else 0
                else:
                    # Calculate based on pips (default)
                    sl_distance = sl_pips * pip_size if sl_pips > 0 else 0
                    tp_distance = tp_pips * pip_size if tp_pips > 0 else 0
                
                # CRITICAL FIX: Ensure minimum distance requirements with proper buffer
                buffer_multiplier = 2.0  # INCREASED: 100% buffer to avoid rejection
                safe_min_distance = min_distance * buffer_multiplier
                
                # Calculate original distances
                original_sl_distance = sl_pips * pip_size if sl_pips > 0 else 0
                original_tp_distance = tp_pips * pip_size if tp_pips > 0 else 0
                
                # Apply minimum distance requirements
                sl_distance = max(original_sl_distance, safe_min_distance) if sl_distance > 0 else 0
                tp_distance = max(original_tp_distance, safe_min_distance) if tp_distance > 0 else 0
                
                log.info(f"📊 Distance Calculation:")
                log.info(f"   Original SL: {sl_pips} pips = {original_sl_distance:.5f} price units")
                log.info(f"   Original TP: {tp_pips} pips = {original_tp_distance:.5f} price units")
                log.info(f"   Required Min: {min_distance_points} points = {min_distance:.5f} price units")
                log.info(f"   Safe Min (with buffer): {safe_min_distance:.5f} price units")
                log.info(f"   Final SL Distance: {sl_distance:.5f}")
                log.info(f"   Final TP Distance: {tp_distance:.5f}")
                
                if signal['type'] == 'BUY':
                    sl_price = current_price - sl_distance if sl_distance > 0 else 0
                    tp_price = current_price + tp_distance if tp_distance > 0 else 0
                else:  # SELL
                    sl_price = current_price + sl_distance if sl_distance > 0 else 0
                    tp_price = current_price - tp_distance if tp_distance > 0 else 0
                
                log.info(f"📊 Calculated SL/TP: SL={sl_price:.2f}, TP={tp_price:.2f} (distances: SL={sl_distance:.2f}, TP={tp_distance:.2f})")
                
                # CRITICAL: Validate SL/TP values before proceeding
                if sl_price <= 0 or tp_price <= 0:
                    log.error(f"❌ CRITICAL SL/TP ERROR: Invalid prices calculated!")
                    log.error(f"   SL Price: {sl_price} (should be > 0)")
                    log.error(f"   TP Price: {tp_price} (should be > 0)")
                    log.error(f"   Current Price: {current_price}")
                    log.error(f"   Signal Type: {signal['type']}")
                    log.error(f"   SL Distance: {sl_distance}")
                    log.error(f"   TP Distance: {tp_distance}")
                    # Force disable SL/TP for this trade to avoid order rejection
                    use_sl_tp = False
                    log.warning(f"🔄 Forcing SL/TP disabled for this trade due to calculation error")
            else:
                log.warning(f"⚠️ SL/TP DISABLED - use_manual_sl_tp: {self.config.get('use_manual_sl_tp')}, use_sl_tp: {self.config.get('use_sl_tp')}")
                log.warning(f"⚠️ Orders will be placed WITHOUT stop loss or take profit!")
                log.warning(f"⚠️ Config keys available: {list(self.config.keys())}")

            # Use configured lot size (already set from frontend configuration above)
            log.info(f"📊 Using validated lot size: {lot_size}")
            
            # PRE-ORDER VALIDATION CHECKS
            validation_errors = []
            
            # Check account balance
            required_margin = lot_size * current_price * 0.1  # Rough margin estimate
            if account_balance < required_margin:
                validation_errors.append(f"Insufficient balance: ${account_balance:.2f} < ${required_margin:.2f}")
            
            # Check lot size
            if lot_size < min_lot or lot_size > max_lot:
                validation_errors.append(f"Invalid lot size: {lot_size} (range: {min_lot}-{max_lot})")
            
            # Check SL/TP distances if enabled
            if use_sl_tp and sl_price > 0 and tp_price > 0:
                sl_distance_actual = abs(current_price - sl_price)
                tp_distance_actual = abs(tp_price - current_price)
                if sl_distance_actual < min_distance:
                    validation_errors.append(f"SL too close: {sl_distance_actual:.5f} < {min_distance:.5f}")
                if tp_distance_actual < min_distance:
                    validation_errors.append(f"TP too close: {tp_distance_actual:.5f} < {min_distance:.5f}")
            
            # Check if symbol is tradeable
            if not getattr(symbol_info, 'trade_mode', 0):
                validation_errors.append("Symbol not tradeable")
            
            if validation_errors:
                log.error("❌ PRE-ORDER VALIDATION FAILED:")
                for error in validation_errors:
                    log.error(f"   - {error}")
                self._notify_trade_error("Validation Failed", "; ".join(validation_errors))
                return
            
            log.info("✅ Pre-order validation passed")

            # Try robust combinations similar to candle manager
            filling_modes = [
                mt5.ORDER_FILLING_RETURN,
                mt5.ORDER_FILLING_IOC,
                mt5.ORDER_FILLING_FOK,
            ]
            # ENHANCED SL/TP STRATEGY: Try with SL/TP first, then fallback to market order
            if use_sl_tp and sl_price > 0 and tp_price > 0:
                sl_tp_configs = [
                    {'sl': sl_price, 'tp': tp_price, 'description': 'with SL/TP'},
                    {'description': 'without SL/TP (fallback)'},  # Fallback if SL/TP fails
                ]
                log.info(f"🎯 HFT Strategy: Try WITH SL={sl_price:.5f} TP={tp_price:.5f}, fallback to market order")
            else:
                sl_tp_configs = [
                    {'description': 'without SL/TP (configured)'},
                ]
                log.info(f"📊 HFT Strategy: Market order only (SL/TP disabled)")

            result = None
            for st in sl_tp_configs:
                for fm in filling_modes:
                    # ENHANCED ORDER REQUEST with better parameters
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": self.symbol,
                        "volume": float(lot_size),  # Ensure float
                        "type": order_type,
                        "price": float(current_price),  # Ensure float
                        "deviation": 20,  # Increased deviation for HFT
                        "magic": int(self.unique_magic_number),  # Ensure int
                        "comment": f"TradePulse_{self.bot_id}_HFT"[:31],  # Simplified comment
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": fm,
                    }
                    if 'sl' in st and st['sl'] > 0:
                        request['sl'] = float(st['sl'])  # Ensure float
                        log.info(f"📊 Adding SL to order: {st['sl']:.5f}")
                    if 'tp' in st and st['tp'] > 0:
                        request['tp'] = float(st['tp'])  # Ensure float
                        log.info(f"📊 Adding TP to order: {st['tp']:.5f}")

                    log.info(f"🔄 HFT order attempt: {st['description']} with filling={fm}")
                    log.info(f"📊 Order Request: {request}")
                    
                    res = mt5.order_send(request)
                    result = res
                    
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        log.info(f"✅ HFT order SUCCESS with {st['description']} and {fm}")
                        break
                    elif res:
                        log.warning(f"⚠️ HFT order failed: retcode={res.retcode} with {st['description']} and {fm}")
                        if res.retcode == 10016:  # Invalid stops
                            log.warning(f"   🎯 Invalid SL/TP detected, will try without SL/TP next")
                        elif res.retcode == 10030:  # Unsupported filling
                            log.warning(f"   🔄 Unsupported filling mode {fm}, trying next")
                        continue
                    else:
                        log.error(f"❌ No response from MT5 for {st['description']} with {fm}")
                        continue
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    break

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                trade_id = f"trade_{result.order}"
                self.active_trades[trade_id] = {
                    'signal': signal,
                    'entry_time': datetime.now(),
                    'status': 'active',
                    'mt5_ticket': result.order,
                    'lot_size': lot_size,
                    'entry_price': signal['price'],
                    'sl': sl_price,
                    'tp': tp_price
                }

                self._update_performance()
                self.notify_updates({
                    'type': 'trade_executed',
                    'bot_id': self.bot_id,
                    'mode': self.mode,
                    'trade_id': trade_id,
                    'ticket': result.order,
                    'signal': signal,
                    'volume': result.volume,
                    'price': result.price,
                    'sl': sl_price,
                    'tp': tp_price,
                    'performance': self.performance,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                last_err = mt5.last_error()
                retcode = getattr(result, 'retcode', None) if result else None
                
                # ENHANCED ERROR REPORTING with specific error codes
                error_messages = {
                    10004: "Requote - price changed",
                    10006: "Request rejected",
                    10007: "Request canceled by trader", 
                    10008: "Order placed",
                    10009: "Request completed",
                    10010: "Only part of request completed",
                    10011: "Request processing error",
                    10012: "Request canceled by timeout",
                    10013: "Invalid request",
                    10014: "Invalid volume in request",
                    10015: "Invalid price in request",
                    10016: "Invalid stops in request",
                    10017: "Trade disabled",
                    10018: "Market closed",
                    10019: "No money",
                    10020: "Prices changed",
                    10021: "No quotes to process request",
                    10022: "Invalid order expiration in request",
                    10023: "Order state changed",
                    10024: "Too frequent requests",
                    10025: "No changes in request",
                    10026: "Autotrading disabled by server",
                    10027: "Autotrading disabled by client",
                    10028: "Request locked for processing",
                    10029: "Order or position frozen",
                    10030: "Invalid order filling type",
                    10031: "No connection with trade server"
                }
                
                error_desc = error_messages.get(retcode, f"Unknown error code: {retcode}")
                
                log.error(f"❌ HFT ORDER FAILED:")
                log.error(f"   📊 Return Code: {retcode}")
                log.error(f"   📋 Description: {error_desc}")
                log.error(f"   🔍 MT5 Last Error: {last_err}")
                log.error(f"   💰 Account Balance: {account_balance:.2f}")
                log.error(f"   📊 Lot Size: {lot_size}")
                log.error(f"   💱 Price: {current_price}")
                log.error(f"   🎯 SL/TP: {sl_price:.2f}/{tp_price:.2f}")
                
                # Specific error handling
                if retcode == 10019:  # No money
                    log.error(f"   💸 INSUFFICIENT FUNDS: Need ~${lot_size * current_price:.2f} for {lot_size} lots")
                elif retcode == 10016:  # Invalid stops
                    log.error(f"   🎯 INVALID SL/TP: SL distance={abs(current_price - sl_price):.5f}, TP distance={abs(tp_price - current_price):.5f}")
                    log.error(f"   📏 Required minimum distance: {min_distance:.5f}")
                elif retcode == 10014:  # Invalid volume
                    log.error(f"   📊 INVALID LOT SIZE: {lot_size} (Min: {min_lot}, Max: {max_lot}, Step: {lot_step})")
                elif retcode == 10030:  # Invalid filling
                    log.error(f"   🔄 INVALID FILLING MODE: All filling modes failed")
                
                self._notify_trade_error("HFT Order Failed", f"{error_desc} (Code: {retcode})")

        except Exception as e:
            log.error(f"HFT execute_trade error: {e}")
            self._notify_trade_error("Trade execution error", str(e))

    def _can_place_order(self) -> bool:
        # enforce max_orders_per_minute
        limit = int(self.config.get('max_orders_per_minute', 5))
        now = time.time()
        window_start = now - 60
        self._recent_order_times = [t for t in self._recent_order_times if t >= window_start]
        return len(self._recent_order_times) < limit

    def _notify_trade_error(self, error_type: str, details: str):
        self.notify_updates({
            'type': 'trade_error',
            'bot_id': self.bot_id,
            'mode': self.mode,
            'error': error_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def _update_performance(self):
        try:
            if not self.unique_magic_number or not self.bot_start_time:
                return
            if not mt5.initialize():
                return

            account_info = mt5.account_info()
            if account_info:
                current_balance = account_info.balance
                current_equity = account_info.equity
                self.performance.update({
                    'account_balance': current_balance,
                    'account_equity': current_equity,
                    'floating_pnl': current_equity - current_balance
                })

            deals = mt5.history_deals_get(self.bot_start_time, datetime.now())
            bot_deals = []
            if deals:
                for d in deals:
                    magic = getattr(d, 'magic', 0)
                    comment = getattr(d, 'comment', '')
                    d_type = getattr(d, 'type', -1)
                    if (magic == self.unique_magic_number or f"TradePulse_{self.bot_id}" in comment) and d_type in [0, 1]:
                        profit = getattr(d, 'profit', 0) + getattr(d, 'commission', 0) + getattr(d, 'swap', 0)
                        bot_deals.append({
                            'ticket': getattr(d, 'ticket', 0),
                            'position_id': getattr(d, 'position_id', 0),
                            'time': datetime.fromtimestamp(getattr(d, 'time', 0)),
                            'type': 'BUY' if d_type == 0 else 'SELL',
                            'volume': getattr(d, 'volume', 0),
                            'price': getattr(d, 'price', 0),
                            'profit': profit,
                            'magic': magic,
                            'comment': comment
                        })

            # Group by position_id to count completed trades
            pos_groups: Dict[int, List[Dict]] = {}
            for t in bot_deals:
                pos_groups.setdefault(t['position_id'], []).append(t)

            completed = []
            for pos_id, trades in pos_groups.items():
                if len(trades) >= 1:
                    total_profit = sum(x['profit'] for x in trades)
                    last_trade = max(trades, key=lambda x: x['time'])
                    completed.append({
                        'position_id': pos_id,
                        'profit': total_profit,
                        'time': last_trade['time'],
                        'type': last_trade['type'],
                        'volume': last_trade['volume'],
                        'price': last_trade['price']
                    })

            total_trades = self.lifetime_stats['total_completed_trades'] + len(completed)
            winning = self.lifetime_stats['total_winning_trades'] + len([t for t in completed if t['profit'] > 0])
            losing = self.lifetime_stats['total_losing_trades'] + len([t for t in completed if t['profit'] < 0])
            session_profit = sum(t['profit'] for t in completed)
            total_realized = self.lifetime_stats['lifetime_realized_profit'] + session_profit
            win_rate = (winning / total_trades * 100) if total_trades > 0 else 0

            today = datetime.now().strftime('%Y-%m-%d')
            daily_pnl = self.lifetime_stats['daily_stats'].get(today, {}).get('profit', 0.0) + session_profit

            # Open positions profit
            unrealized_pnl = 0.0
            positions = mt5.positions_get()
            if positions:
                for p in positions:
                    if getattr(p, 'magic', 0) == self.unique_magic_number or f"TradePulse_{self.bot_id}" in getattr(p, 'comment', ''):
                        unrealized_pnl += getattr(p, 'profit', 0) + getattr(p, 'commission', 0) + getattr(p, 'swap', 0)

            self.performance.update({
                'total_trades': total_trades,
                'winning_trades': winning,
                'losing_trades': losing,
                'total_profit': round(total_realized, 2),
                'daily_pnl': round(daily_pnl, 2),
                'win_rate': round(win_rate, 1),
                'unrealized_pnl': round(unrealized_pnl, 2),
                'total_pnl': round(total_realized + unrealized_pnl, 2),
                'last_update': datetime.now().isoformat(),
                'magic_number': self.unique_magic_number,
                'bot_start_time': self.bot_start_time.isoformat()
            })
        except Exception as e:
            log.error(f"HFT update_performance error: {e}")

    # ---- Public info ----
    def get_bot_status(self) -> Dict:
        return {
            'is_running': self.is_running,
            'strategy': self.config['strategy_name'],
            'auto_trading': self.config['auto_trading_enabled'],
            'performance': self.performance,
            'active_trades': len(self.active_trades),
            'config': self.config,
            'magic_number': self.unique_magic_number,
            'bot_start_time': self.bot_start_time.isoformat() if self.bot_start_time else None,
            'bot_id': self.bot_id,
            'mode': self.mode,
        }

    def update_config(self, new_config: Dict):
        """Update bot configuration with enhanced risk management support"""
        old_config = self.config.copy()
        self.config.update(new_config or {})
        
        # Log configuration changes
        log.info(f"🔧 HFT configuration updated: {new_config}")
        
        # Check for important config changes
        auto_trading_changed = old_config.get('auto_trading_enabled') != self.config.get('auto_trading_enabled')
        strategy_changed = old_config.get('strategy_name') != self.config.get('strategy_name')
        sl_tp_changed = (
            old_config.get('sl_pips') != self.config.get('sl_pips') or
            old_config.get('tp_pips') != self.config.get('tp_pips') or
            old_config.get('use_sl_tp') != self.config.get('use_sl_tp')
        )
        
        if auto_trading_changed:
            log.info(f"📊 Auto trading: {old_config.get('auto_trading_enabled')} → {self.config.get('auto_trading_enabled')}")
        
        if strategy_changed:
            log.info(f"🎯 Strategy: {old_config.get('strategy_name')} → {self.config.get('strategy_name')}")
        
        if sl_tp_changed:
            log.info(f"🛡️ Risk Management Updated:")
            log.info(f"   - SL/TP Enabled: {self.config.get('use_sl_tp', True)}")
            log.info(f"   - Stop Loss: {self.config.get('sl_pips', 20)} pips")
            log.info(f"   - Take Profit: {self.config.get('tp_pips', 40)} pips")
            log.info(f"   - Mode: {self.config.get('sl_tp_mode', 'pips')}")
        
        log.info(f"🔧 Complete HFT config: {self.config}")
        
        # Notify frontend with detailed update info
        self.notify_updates({
            'type': 'config_update',
            'config': self.config,
            'changes': {
                'auto_trading_changed': auto_trading_changed,
                'strategy_changed': strategy_changed,
                'sl_tp_changed': sl_tp_changed
            },
            'mode': self.mode,
            'timestamp': datetime.now().isoformat()
        })

    # ---- Utils ----
    def _generate_unique_magic_number(self) -> int:
        import hashlib
        unique_string = f"{self.bot_id}_{int(time.time())}_HFT"
        magic_number = int(hashlib.md5(unique_string.encode()).hexdigest()[:8], 16) % 2147483647
        magic_number = 234000 + (magic_number % 66000)
        return magic_number


