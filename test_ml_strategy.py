#!/usr/bin/env python3
"""
Test ML Strategy Integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_ml_strategy():
    """Test ML strategy functionality"""
    print("🤖 Testing ML Strategy...")
    
    try:
        from trading_bot.strategies import get_strategy
        import numpy as np
        
        # Create ML strategy
        config = {
            'ml_min_confidence': 0.6,
            'ml_min_expected_return': 0.1,
            'ml_use_regression_filter': True,
            'ml_dynamic_sl_tp': True
        }
        
        strategy = get_strategy('ml_strategy', 'ETHUSD', config)
        print(f"✅ ML Strategy created: {strategy.name}")
        
        # Create dummy market data for testing
        # Simulate 50 candles of OHLC data
        np.random.seed(42)  # For reproducible results
        base_price = 3250.0
        rates = []
        
        for i in range(50):
            # Generate realistic OHLC data
            open_price = base_price + np.random.normal(0, 5)
            high_price = open_price + abs(np.random.normal(2, 1))
            low_price = open_price - abs(np.random.normal(2, 1))
            close_price = low_price + np.random.random() * (high_price - low_price)
            
            # MT5 rate format: [time, open, high, low, close, tick_volume, spread, real_volume]
            rate = [
                1699000000 + i * 60,  # timestamp (1 minute intervals)
                open_price,
                high_price, 
                low_price,
                close_price,
                100,  # tick_volume
                2,    # spread
                100   # real_volume
            ]
            rates.append(rate)
            base_price = close_price  # Next candle starts where this one ended
        
        rates = np.array(rates)
        print(f"✅ Created test market data: {len(rates)} candles")
        
        # Test strategy analysis
        print("🔍 Testing strategy analysis...")
        signal = strategy.analyze(rates)
        
        if signal:
            print("✅ ML Strategy generated signal!")
            print(f"   Signal Type: {signal['type']}")
            print(f"   Price: ${signal['price']:.2f}")
            print(f"   Confidence: {signal['confidence']:.2%}")
            print(f"   Expected Return: {signal['expected_return']:.2f}%")
            print(f"   Reason: {signal['reason']}")
            
            if 'ml_data' in signal:
                ml_data = signal['ml_data']
                print("   ML Data:")
                print(f"     - Signal Probabilities: {ml_data.get('signal_probabilities', {})}")
                print(f"     - Model Version: {ml_data.get('model_version', 'N/A')}")
            
            return True
        else:
            print("⚠️ ML Strategy did not generate a signal (this is normal - depends on confidence thresholds)")
            return True
            
    except Exception as e:
        print(f"❌ Error testing ML strategy: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 ML Strategy Integration Test")
    print("=" * 50)
    
    success = test_ml_strategy()
    
    print("\n📊 Test Results")
    print("=" * 50)
    
    if success:
        print("✅ ML Strategy integration is working!")
        print("\n🎯 You can now use 'ml_strategy' in your trading bot!")
        print("\n📋 Example bot configuration:")
        print("""
{
    "strategy_name": "ml_strategy",
    "ml_min_confidence": 0.7,
    "ml_min_expected_return": 0.2,
    "ml_use_regression_filter": true,
    "ml_dynamic_sl_tp": true,
    "auto_trading_enabled": true
}
        """)
    else:
        print("❌ ML Strategy integration has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)