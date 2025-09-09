#!/usr/bin/env python3
"""
Test ML Integration Script
Quick test to verify ML model integration is working
"""

import sys
import os
import requests
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_ml_service():
    """Test ML service directly"""
    print("🧪 Testing ML Service...")
    
    try:
        from ml_model.model_service import ml_service
        
        # Test model status
        status = ml_service.get_model_status()
        print(f"✅ Model Status: {status}")
        
        if status['tensorflow_available']:
            print("✅ TensorFlow is available")
        else:
            print("❌ TensorFlow not available")
            return False
        
        if status['is_loaded']:
            print("✅ Model is loaded")
            
            # Test prediction
            print("🔮 Testing prediction...")
            prediction = ml_service.predict(bars=50)
            
            if prediction:
                print("✅ Prediction successful!")
                print(f"   Signal: {prediction['signal']}")
                print(f"   Confidence: {prediction['confidence']:.2%}")
                print(f"   Expected Return: {prediction['expected_return']:.2f}%")
                return True
            else:
                print("❌ Prediction failed")
                return False
        else:
            print("⚠️ Model not loaded - need to train first")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_endpoints():
    """Test ML API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/api/ml/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ ML Status API working")
            print(f"   Model loaded: {data.get('data', {}).get('is_loaded', False)}")
        else:
            print(f"❌ ML Status API failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure the backend server is running: python backend/candlestickData.py")
        return False
    
    # Test prediction endpoint
    try:
        response = requests.get(f"{base_url}/api/ml/predict", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                prediction = data.get('data', {})
                print("✅ ML Prediction API working")
                print(f"   Signal: {prediction.get('signal', 'N/A')}")
                print(f"   Confidence: {prediction.get('confidence', 0):.2%}")
            else:
                print(f"❌ ML Prediction API error: {data.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ ML Prediction API failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Prediction API error: {e}")
        return False
    
    return True

def test_strategy_integration():
    """Test ML strategy integration"""
    print("\n🤖 Testing Strategy Integration...")
    
    try:
        from trading_bot.strategies import get_strategy, list_strategies
        
        # Check if ML strategy is available
        strategies = list_strategies()
        print(f"✅ Available strategies: {strategies}")
        
        if 'ml_strategy' in strategies:
            print("✅ ML strategy is registered")
            
            # Try to create ML strategy
            try:
                strategy = get_strategy('ml_strategy', 'ETHUSD', {})
                print("✅ ML strategy can be created")
                print(f"   Strategy name: {strategy.name}")
                return True
            except Exception as e:
                print(f"❌ Cannot create ML strategy: {e}")
                return False
        else:
            print("❌ ML strategy not found in available strategies")
            return False
            
    except ImportError as e:
        print(f"❌ Strategy import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Strategy test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TradePulse ML Integration Test")
    print("=" * 50)
    
    # Test 1: ML Service
    service_ok = test_ml_service()
    
    # Test 2: API Endpoints (optional - server might not be running)
    api_ok = test_api_endpoints()
    
    # Test 3: Strategy Integration
    strategy_ok = test_strategy_integration()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"ML Service:          {'✅ PASS' if service_ok else '❌ FAIL'}")
    print(f"API Endpoints:       {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"Strategy Integration: {'✅ PASS' if strategy_ok else '❌ FAIL'}")
    
    if service_ok and strategy_ok:
        print("\n🎉 ML Integration is working!")
        print("\n📋 Next steps:")
        print("1. Start backend: cd backend && python candlestickData.py")
        print("2. Start frontend: cd frontend && npm start")
        print("3. Test ML predictions in the web interface")
        
        if not api_ok:
            print("\n💡 Note: API test failed - make sure backend server is running for full functionality")
        
        return True
    else:
        print("\n❌ ML Integration has issues - check the errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)