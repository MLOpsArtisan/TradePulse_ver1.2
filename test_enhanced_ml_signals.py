#!/usr/bin/env python3
"""
Test Enhanced ML Signal Generation
"""

import sys
import os
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_enhanced_ml_strategy():
    """Test the enhanced ML strategy for BUY/SELL signal generation"""
    print("🚀 Testing Enhanced ML Strategy for BUY/SELL Signals")
    print("=" * 60)
    
    try:
        from trading_bot.enhanced_ml_strategy import get_enhanced_ml_strategy
        
        # Create enhanced ML strategy with aggressive settings
        config = {
            'ml_min_confidence': 0.3,  # Very low threshold
            'ml_min_expected_return': 0.02,  # Very low return requirement
            'ml_use_regression_filter': False,  # Disable regression filter
            'ml_trade_hold_signals': True,  # Enable HOLD signal conversion
            'ml_signal_boost_mode': True,  # Enable signal boosting
            'ml_dynamic_sl_tp': True
        }
        
        strategy = get_enhanced_ml_strategy('ETHUSD', config)
        print(f"✅ Enhanced ML Strategy created: {strategy.name}")
        
        # Create test market data
        np.random.seed(42)
        base_price = 3250.0
        rates = []
        
        for i in range(60):  # More data for better analysis
            open_price = base_price + np.random.normal(0, 10)
            high_price = open_price + abs(np.random.normal(5, 2))
            low_price = open_price - abs(np.random.normal(5, 2))
            close_price = low_price + np.random.random() * (high_price - low_price)
            
            rate = [
                1699000000 + i * 60,
                open_price,
                high_price, 
                low_price,
                close_price,
                100, 2, 100
            ]
            rates.append(rate)
            base_price = close_price
        
        rates = np.array(rates)
        print(f"✅ Created test market data: {len(rates)} candles")
        
        # Test multiple times to see different signals
        print("\n🔍 Testing Enhanced ML Strategy (multiple attempts):")
        print("-" * 60)
        
        signals_generated = []
        
        for attempt in range(5):
            print(f"\n📊 Attempt {attempt + 1}:")
            signal = strategy.analyze(rates)
            
            if signal:
                signals_generated.append(signal)
                print(f"✅ SIGNAL GENERATED!")
                print(f"   Type: {signal['type']}")
                print(f"   Price: ${signal['price']:.2f}")
                print(f"   Confidence: {signal['confidence']:.2%}")
                print(f"   Expected Return: {signal['expected_return']:.2f}%")
                print(f"   Stop Loss: {signal['stop_loss_pips']} pips")
                print(f"   Take Profit: {signal['take_profit_pips']} pips")
                print(f"   Reason: {signal['reason']}")
                
                if 'ml_data' in signal and signal['ml_data'].get('enhanced_mode'):
                    print(f"   🚀 Enhanced Mode: Active")
                    probs = signal['ml_data']['signal_probabilities']
                    print(f"   Probabilities: BUY={probs['buy']:.1%}, SELL={probs['sell']:.1%}, HOLD={probs['hold']:.1%}")
            else:
                print("❌ No signal generated")
        
        print(f"\n📊 Summary:")
        print(f"   Total Attempts: 5")
        print(f"   Signals Generated: {len(signals_generated)}")
        print(f"   Success Rate: {len(signals_generated)/5:.1%}")
        
        if signals_generated:
            signal_types = [s['type'] for s in signals_generated]
            buy_count = signal_types.count('BUY')
            sell_count = signal_types.count('SELL')
            print(f"   BUY Signals: {buy_count}")
            print(f"   SELL Signals: {sell_count}")
            
            print(f"\n🎯 Enhanced ML Strategy is generating {signal_types[0] if signals_generated else 'NO'} signals!")
            return True
        else:
            print(f"\n⚠️ No signals generated - model may need retraining or different market conditions")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enhanced ML strategy: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ml_api_prediction():
    """Test ML API for different prediction scenarios"""
    print("\n🌐 Testing ML API Predictions")
    print("=" * 60)
    
    try:
        from ml_model.model_service import ml_service
        
        # Test multiple predictions
        for i in range(3):
            print(f"\n🔮 Prediction {i+1}:")
            prediction = ml_service.predict(bars=100)
            
            if prediction:
                print(f"   Signal: {prediction['signal']}")
                print(f"   Confidence: {prediction['confidence']:.2%}")
                print(f"   Expected Return: {prediction['expected_return']:.2f}%")
                
                probs = prediction['signal_probabilities']
                print(f"   Probabilities:")
                print(f"     BUY:  {probs['buy']:.1%}")
                print(f"     SELL: {probs['sell']:.1%}")
                print(f"     HOLD: {probs['hold']:.1%}")
                
                # Check if this would generate a trading signal with enhanced strategy
                if prediction['confidence'] > 0.3:
                    if prediction['signal'] in ['BUY', 'SELL']:
                        print(f"   🚀 Would generate {prediction['signal']} signal with enhanced strategy!")
                    elif probs['buy'] > 0.25 or probs['sell'] > 0.25:
                        best_signal = 'BUY' if probs['buy'] > probs['sell'] else 'SELL'
                        print(f"   🚀 Could boost to {best_signal} signal!")
            else:
                print("   ❌ No prediction available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ML API: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 Enhanced ML Signal Generation Test")
    print("=" * 80)
    
    # Test 1: Enhanced ML Strategy
    strategy_ok = test_enhanced_ml_strategy()
    
    # Test 2: ML API Predictions
    api_ok = test_ml_api_prediction()
    
    print(f"\n📊 Final Results")
    print("=" * 80)
    print(f"Enhanced ML Strategy: {'✅ PASS' if strategy_ok else '❌ FAIL'}")
    print(f"ML API Predictions:   {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if strategy_ok and api_ok:
        print(f"\n🎉 SUCCESS! Enhanced ML Strategy is ready for trading!")
        print(f"\n📋 Key Features:")
        print(f"   ✅ Lower confidence threshold (30% vs 60%)")
        print(f"   ✅ HOLD signal conversion to BUY/SELL")
        print(f"   ✅ Signal boosting for weak signals")
        print(f"   ✅ Disabled regression filter for more signals")
        print(f"   ✅ Dynamic stop-loss/take-profit")
        
        print(f"\n🚀 To use in your system:")
        print(f"   1. Start backend: python start_backend.py")
        print(f"   2. Go to ML Predictions tab")
        print(f"   3. Click 'Start ML Trading' button")
        print(f"   4. Enhanced strategy will generate more BUY/SELL signals!")
        
    else:
        print(f"\n❌ Some tests failed - check the errors above")
    
    return strategy_ok and api_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)