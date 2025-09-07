#!/usr/bin/env python3
"""
Test the tick processing fix
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import logging
from backend.trading_bot.tick_strategies import _ticks_to_arrays

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_tick_processing():
    """Test if the tick processing fix works"""
    
    # Initialize MT5
    if not mt5.initialize():
        log.error("Failed to initialize MT5")
        return False
    
    symbol = "ETHUSD"
    
    try:
        log.info("=== TESTING TICK PROCESSING FIX ===")
        
        # Get historical ticks (the problematic ones)
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=30)
        
        ticks = mt5.copy_ticks_range(symbol, start_time, end_time, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 0:
            log.info(f"✅ Fetched {len(ticks)} historical ticks")
            
            # Test the fixed processing function
            result = _ticks_to_arrays(ticks)
            
            bid_prices = result['bid']
            ask_prices = result['ask']
            last_prices = result['last']
            
            log.info(f"📊 PROCESSING RESULTS:")
            log.info(f"   - Bid prices: {len(bid_prices)} valid")
            log.info(f"   - Ask prices: {len(ask_prices)} valid")
            log.info(f"   - Last prices: {len(last_prices)} valid")
            
            if len(bid_prices) > 0:
                log.info(f"   - Bid range: {bid_prices.min():.2f} - {bid_prices.max():.2f}")
                log.info(f"   - Ask range: {ask_prices.min():.2f} - {ask_prices.max():.2f}")
                log.info(f"✅ SUCCESS: Tick processing is now working!")
                return True
            else:
                log.error(f"❌ FAILED: Still no valid prices extracted")
                return False
        else:
            log.error("❌ No historical ticks found")
            return False
            
    except Exception as e:
        log.error(f"❌ Test failed: {e}")
        return False
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    success = test_tick_processing()
    if success:
        print("\n🎉 TICK PROCESSING FIX SUCCESSFUL!")
        print("The HFT bots should now be able to generate signals.")
    else:
        print("\n❌ TICK PROCESSING FIX FAILED!")
        print("Further debugging needed.")