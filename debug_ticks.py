#!/usr/bin/env python3
"""
Debug script to examine MT5 tick data structure
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def debug_tick_structure():
    """Debug the actual structure of MT5 ticks"""
    
    # Initialize MT5
    if not mt5.initialize():
        log.error("Failed to initialize MT5")
        return
    
    symbol = "ETHUSD"
    
    try:
        # Get current tick
        current_tick = mt5.symbol_info_tick(symbol)
        if current_tick:
            log.info(f"=== CURRENT TICK DEBUG ===")
            log.info(f"Type: {type(current_tick)}")
            log.info(f"Dir: {dir(current_tick)}")
            
            # Print all attributes
            for attr in dir(current_tick):
                if not attr.startswith('_'):
                    try:
                        val = getattr(current_tick, attr)
                        log.info(f"{attr}: {val} (type: {type(val)})")
                    except Exception as e:
                        log.info(f"{attr}: ERROR - {e}")
        
        # Get historical ticks
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=30)
        
        log.info(f"\n=== HISTORICAL TICKS DEBUG ===")
        ticks = mt5.copy_ticks_range(symbol, start_time, end_time, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 0:
            log.info(f"Fetched {len(ticks)} ticks")
            
            # Examine first few ticks
            for i, tick in enumerate(ticks[:3]):
                log.info(f"\n--- TICK {i+1} ---")
                log.info(f"Type: {type(tick)}")
                
                # Print all attributes
                for attr in dir(tick):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(tick, attr)
                            if isinstance(val, (int, float)) and val > 100:
                                log.info(f"  {attr}: {val} (type: {type(val)}) *** POTENTIAL PRICE ***")
                            else:
                                log.info(f"  {attr}: {val} (type: {type(val)})")
                        except Exception as e:
                            log.info(f"  {attr}: ERROR - {e}")
        else:
            log.error("No historical ticks found!")
            
    except Exception as e:
        log.error(f"Debug failed: {e}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    debug_tick_structure()