#!/usr/bin/env python3
"""
Live Bot Test - Start actual bots and monitor their behavior
Tests real market analysis and signal generation
"""

import socketio
import time
import json
from datetime import datetime

# Configuration
SERVER_URL = "http://localhost:5000"

class LiveBotTester:
    def __init__(self):
        self.sio = socketio.Client()
        self.setup_event_handlers()
        self.test_results = {
            'hft_signals': [],
            'candle_signals': [],
            'trade_executions': [],
            'errors': []
        }
        
    def setup_event_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.event
        def connect():
            print("✅ Connected to server")
            
        @self.sio.event
        def disconnect():
            print("❌ Disconnected from server")
            
        @self.sio.on('bot_start_response')
        def on_bot_start(data):
            print(f"🚀 Bot start response: {data}")
            
        @self.sio.on('bot_update')
        def on_bot_update(data):
            bot_id = data.get('bot_id', 'unknown')
            signal = data.get('signal')
            performance = data.get('performance', {})
            mode = data.get('mode', 'unknown')
            
            if signal:
                print(f"🎯 [{mode.upper()}] {bot_id} SIGNAL: {signal['type']} at {signal['price']:.2f} (confidence: {signal.get('confidence', 0):.2f})")
                print(f"   📊 Reason: {signal.get('reason', 'No reason provided')}")
                
                # Store signal for analysis
                if mode == 'hft':
                    self.test_results['hft_signals'].append({
                        'timestamp': datetime.now().isoformat(),
                        'bot_id': bot_id,
                        'signal': signal
                    })
                else:
                    self.test_results['candle_signals'].append({
                        'timestamp': datetime.now().isoformat(),
                        'bot_id': bot_id,
                        'signal': signal
                    })
            
            # Show performance updates
            total_trades = performance.get('total_trades', 0)
            if total_trades > 0:
                win_rate = performance.get('win_rate', 0)
                total_pnl = performance.get('total_pnl', 0)
                print(f"   📈 Performance: {total_trades} trades, {win_rate:.1f}% win rate, ${total_pnl:.2f} P&L")
                
        @self.sio.on('trade_executed')
        def on_trade_executed(data):
            print(f"💰 TRADE EXECUTED: {data}")
            self.test_results['trade_executions'].append({
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
            
        @self.sio.on('bot_error')
        def on_bot_error(data):
            print(f"❌ Bot error: {data}")
            self.test_results['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': data
            })
    
    def connect_to_server(self):
        """Connect to the WebSocket server"""
        try:
            self.sio.connect(SERVER_URL)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def start_hft_bot(self):
        """Start HFT bot for testing"""
        print("\n⚡ Starting HFT Bot Test...")
        
        hft_config = {
            'bot_id': 'live_test_hft',
            'mode': 'hft',
            'strategy': 'rsi_strategy',
            'config': {
                'auto_trading_enabled': False,  # Disable actual trading for safety
                'lot_size_per_trade': 0.01,
                'analysis_interval_secs': 5,  # 5-second analysis
                'min_signal_confidence': 0.4,
                'use_sl_tp': True,
                'sl_pips': 15,
                'tp_pips': 30,
                'enable_spread_filter': False,  # Disable for testing
                'max_orders_per_minute': 3,
                'diagnostic_mode': True  # Enable diagnostic mode for more signals
            }
        }
        
        self.sio.emit('bot_start', hft_config)
        print(f"   📊 HFT bot configuration sent: {hft_config}")
        
    def start_candle_bot(self):
        """Start Candle bot for testing"""
        print("\n📈 Starting Candle Bot Test...")
        
        candle_config = {
            'bot_id': 'live_test_candle',
            'mode': 'candle',
            'strategy': 'moving_average',
            'config': {
                'auto_trading_enabled': False,  # Disable actual trading for safety
                'lot_size_per_trade': 0.1,
                'analysis_bars': 60,
                'min_signal_confidence': 0.5,  # Lower for more signals
                'use_sl_tp': True,
                'sl_pips': 25,
                'tp_pips': 50,
                'ma_fast': 3,
                'ma_slow': 8,
                'use_ema': True,
                'max_daily_trades': 20,
                'diagnostic_mode': True  # Enable diagnostic mode
            }
        }
        
        self.sio.emit('bot_start', candle_config)
        print(f"   📊 Candle bot configuration sent: {candle_config}")
    
    def monitor_bots(self, duration_seconds=60):
        """Monitor bot behavior for specified duration"""
        print(f"\n👀 Monitoring bots for {duration_seconds} seconds...")
        print("   📊 Watching for signals, analysis, and potential issues...")
        
        start_time = time.time()
        last_summary = start_time
        
        while time.time() - start_time < duration_seconds:
            # Print periodic summary
            if time.time() - last_summary >= 15:  # Every 15 seconds
                self.print_summary()
                last_summary = time.time()
            
            time.sleep(1)
        
        print(f"\n⏰ Monitoring complete after {duration_seconds} seconds")
    
    def print_summary(self):
        """Print current test summary"""
        hft_count = len(self.test_results['hft_signals'])
        candle_count = len(self.test_results['candle_signals'])
        trade_count = len(self.test_results['trade_executions'])
        error_count = len(self.test_results['errors'])
        
        print(f"\n📊 LIVE TEST SUMMARY:")
        print(f"   ⚡ HFT signals: {hft_count}")
        print(f"   📈 Candle signals: {candle_count}")
        print(f"   💰 Trade executions: {trade_count}")
        print(f"   ❌ Errors: {error_count}")
        
        # Show recent signals
        if hft_count > 0:
            recent_hft = self.test_results['hft_signals'][-1]
            signal = recent_hft['signal']
            print(f"   🎯 Latest HFT: {signal['type']} at {signal['price']:.2f} ({signal.get('confidence', 0):.2f})")
        
        if candle_count > 0:
            recent_candle = self.test_results['candle_signals'][-1]
            signal = recent_candle['signal']
            print(f"   🎯 Latest Candle: {signal['type']} at {signal['price']:.2f} ({signal.get('confidence', 0):.2f})")
    
    def stop_bots(self):
        """Stop all test bots"""
        print("\n🛑 Stopping test bots...")
        
        for bot_id in ['live_test_hft', 'live_test_candle']:
            self.sio.emit('bot_stop', {'bot_id': bot_id})
            print(f"   🛑 Stop signal sent to {bot_id}")
    
    def analyze_results(self):
        """Analyze test results and provide assessment"""
        print("\n" + "="*60)
        print("📊 LIVE TEST ANALYSIS")
        print("="*60)
        
        hft_signals = self.test_results['hft_signals']
        candle_signals = self.test_results['candle_signals']
        errors = self.test_results['errors']
        
        # HFT Analysis
        print(f"\n⚡ HFT MODE ANALYSIS:")
        print(f"   📊 Total signals: {len(hft_signals)}")
        
        if hft_signals:
            buy_signals = [s for s in hft_signals if s['signal']['type'] == 'BUY']
            sell_signals = [s for s in hft_signals if s['signal']['type'] == 'SELL']
            avg_confidence = sum(s['signal'].get('confidence', 0) for s in hft_signals) / len(hft_signals)
            
            print(f"   📈 BUY signals: {len(buy_signals)}")
            print(f"   📉 SELL signals: {len(sell_signals)}")
            print(f"   🎯 Average confidence: {avg_confidence:.2f}")
            
            # Show signal reasons
            reasons = [s['signal'].get('reason', 'Unknown') for s in hft_signals[-3:]]
            print(f"   📋 Recent reasons: {reasons}")
        else:
            print("   ⚠️ No HFT signals generated - Check RSI strategy logic")
        
        # Candle Analysis
        print(f"\n📈 CANDLE MODE ANALYSIS:")
        print(f"   📊 Total signals: {len(candle_signals)}")
        
        if candle_signals:
            buy_signals = [s for s in candle_signals if s['signal']['type'] == 'BUY']
            sell_signals = [s for s in candle_signals if s['signal']['type'] == 'SELL']
            avg_confidence = sum(s['signal'].get('confidence', 0) for s in candle_signals) / len(candle_signals)
            
            print(f"   📈 BUY signals: {len(buy_signals)}")
            print(f"   📉 SELL signals: {len(sell_signals)}")
            print(f"   🎯 Average confidence: {avg_confidence:.2f}")
            
            # Show signal reasons
            reasons = [s['signal'].get('reason', 'Unknown') for s in candle_signals[-3:]]
            print(f"   📋 Recent reasons: {reasons}")
        else:
            print("   ⚠️ No Candle signals generated - Check MA strategy logic")
        
        # Error Analysis
        print(f"\n❌ ERROR ANALYSIS:")
        print(f"   📊 Total errors: {len(errors)}")
        
        if errors:
            for error in errors[-3:]:  # Show last 3 errors
                print(f"   🔍 {error['timestamp']}: {error['error']}")
        else:
            print("   ✅ No errors detected")
        
        # Overall Assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        
        issues = []
        if len(hft_signals) == 0:
            issues.append("HFT mode not generating signals")
        if len(candle_signals) == 0:
            issues.append("Candle mode not generating signals")
        if len(errors) > 0:
            issues.append(f"{len(errors)} errors detected")
        
        if not issues:
            print("   ✅ Both modes working correctly!")
            print("   ✅ Signal generation functioning")
            print("   ✅ No critical errors detected")
            return True
        else:
            print("   ⚠️ Issues detected:")
            for issue in issues:
                print(f"      - {issue}")
            return False
    
    def run_live_test(self):
        """Run complete live test"""
        print("🚀 Starting Live Bot Analysis Test")
        print("="*60)
        
        # Connect to server
        if not self.connect_to_server():
            print("❌ Cannot connect to server")
            return False
        
        try:
            # Start both bots
            self.start_hft_bot()
            time.sleep(2)  # Wait a bit between starts
            self.start_candle_bot()
            time.sleep(3)  # Wait for bots to initialize
            
            # Monitor for 60 seconds
            self.monitor_bots(60)
            
            # Stop bots
            self.stop_bots()
            time.sleep(2)
            
            # Analyze results
            success = self.analyze_results()
            
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            self.stop_bots()
            return False
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.stop_bots()
            return False
        finally:
            self.sio.disconnect()

if __name__ == "__main__":
    tester = LiveBotTester()
    success = tester.run_live_test()
    
    if success:
        print("\n🎉 LIVE TEST PASSED - Market analysis working correctly!")
    else:
        print("\n⚠️ LIVE TEST ISSUES - Review analysis above")