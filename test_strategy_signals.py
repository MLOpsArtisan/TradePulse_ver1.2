#!/usr/bin/env python3
"""
Test if strategies can now generate signals with the fixed tick processing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import logging
from backend.trading_bot.tick_strategies import TickBreakoutStrategy, TickStochasticStrategy, TickMACDStrategy

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_strategy_signals():
    """Test if strategies can generate signals with fixed tick processing"""
    
    # Initialize MT5
    if not mt5.initialize():
        log.error("Failed to initialize MT5")
        return False
    
    symbol = "ETHUSD"
    
    try:
        log.info("=== TESTING STRATEGY SIGNAL GENERATION ===")
        
        # Get historical ticks
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=60)  # Get more data
        
        ticks = mt5.copy_ticks_range(symbol, start_time, end_time, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 0:
            log.info(f"✅ Fetched {len(ticks)} historical ticks")
            
            # Test each strategy
            strategies = [
                ("Breakout", TickBreakoutStrategy(symbol)),
                ("Stochastic", TickStochasticStrategy(symbol)),
                ("MACD", TickMACDStrategy(symbol))
            ]
            
            results = {}
            
            for name, strategy in strategies:
                log.info(f"\n🔍 Testing {name} Strategy...")
                try:
                    signal = strategy.analyze_ticks(ticks)
                    if signal:
                        log.info(f"✅ {name}: SIGNAL GENERATED!")
                        log.info(f"   Type: {signal.get('type', 'N/A')}")
                        log.info(f"   Price: {signal.get('price', 'N/A')}")
                        log.info(f"   Confidence: {signal.get('confidence', 'N/A')}")
                        log.info(f"   Reason: {signal.get('reason', 'N/A')}")
                        results[name] = "SUCCESS"
                    else:
                        log.info(f"📊 {name}: No signal (normal behavior)")
                        results[name] = "NO_SIGNAL"
                except Exception as e:
                    log.error(f"❌ {name}: ERROR - {e}")
                    results[name] = "ERROR"
            
            log.info(f"\n📊 STRATEGY TEST RESULTS:")
            for name, result in results.items():
                log.info(f"   {name}: {result}")
            
            # Check if at least one strategy worked without errors
            success = all(result != "ERROR" for result in results.values())
            return success
            
        else:
            log.error("❌ No historical ticks found")
            return False
            
    except Exception as e:
        log.error(f"❌ Test failed: {e}")
        return False
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    success = test_strategy_signals()
    if success:
        print("\n🎉 STRATEGY SIGNAL GENERATION TEST SUCCESSFUL!")
        print("All strategies can now process ticks without errors.")
        print("The HFT bots should now work properly and generate signals when conditions are met.")
    else:
        print("\n❌ STRATEGY SIGNAL GENERATION TEST FAILED!")
        print("Some strategies still have errors.")