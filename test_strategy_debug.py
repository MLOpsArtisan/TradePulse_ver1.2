#!/usr/bin/env python3
"""
Debug the strategy error in detail
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import logging
import traceback
from backend.trading_bot.tick_strategies import TickBreakoutStrategy

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def debug_strategy_error():
    """Debug the exact error in strategy processing"""
    
    # Initialize MT5
    if not mt5.initialize():
        log.error("Failed to initialize MT5")
        return False
    
    symbol = "ETHUSD"
    
    try:
        log.info("=== DEBUGGING STRATEGY ERROR ===")
        
        # Get historical ticks
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=30)
        
        ticks = mt5.copy_ticks_range(symbol, start_time, end_time, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 0:
            log.info(f"✅ Fetched {len(ticks)} historical ticks")
            
            # Test breakout strategy with detailed error tracking
            strategy = TickBreakoutStrategy(symbol)
            
            try:
                log.info("🔍 Testing Breakout Strategy with detailed error tracking...")
                signal = strategy.analyze_ticks(ticks)
                log.info(f"✅ Strategy completed successfully: {signal}")
                return True
            except Exception as e:
                log.error(f"❌ Strategy error: {e}")
                log.error(f"Full traceback:")
                traceback.print_exc()
                return False
            
        else:
            log.error("❌ No historical ticks found")
            return False
            
    except Exception as e:
        log.error(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    debug_strategy_error()