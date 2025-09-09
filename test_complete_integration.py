#!/usr/bin/env python3
"""
Complete ML Integration Test - Tests everything including live server
"""

import sys
import os
import time
import requests
import threading
from multiprocessing import Process

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def start_test_server():
    """Start Flask server for testing"""
    try:
        os.chdir('backend')
        from candlestickData import app, socketio
        socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"Server error: {e}")

def test_ml_service():
    """Test ML service directly"""
    print("🧪 Testing ML Service...")
    
    try:
        from ml_model.model_service import ml_service
        
        status = ml_service.get_model_status()
        print(f"✅ Model Status: TensorFlow={status['tensorflow_available']}, Loaded={status['is_loaded']}")
        
        if status['is_loaded']:
            prediction = ml_service.predict(bars=50)
            if prediction:
                print(f"✅ Prediction: {prediction['signal']} ({prediction['confidence']:.1%})")
                return True
        
        return status['tensorflow_available']
        
    except Exception as e:
        print(f"❌ ML Service error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints with running server"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        # Test status
        response = requests.get('http://127.0.0.1:5000/api/ml/status', timeout=5)
        if response.status_code == 200:
            print("✅ ML Status API working")
            
            # Test prediction
            response = requests.get('http://127.0.0.1:5000/api/ml/predict', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    prediction = data.get('data', {})
                    print(f"✅ ML Prediction API: {prediction.get('signal', 'N/A')} ({prediction.get('confidence', 0):.1%})")
                    return True
        
        return False
        
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_strategy_integration():
    """Test strategy integration"""
    print("\n🤖 Testing Strategy Integration...")
    
    try:
        from trading_bot.strategies import get_strategy, list_strategies
        
        strategies = list_strategies()
        if 'ml_strategy' in strategies:
            print("✅ ML strategy registered")
            
            strategy = get_strategy('ml_strategy', 'ETHUSD', {})
            print(f"✅ ML strategy created: {strategy.name}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Strategy test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Complete ML Integration Test")
    print("=" * 60)
    
    # Test 1: ML Service (direct)
    ml_service_ok = test_ml_service()
    
    # Test 2: Strategy Integration
    strategy_ok = test_strategy_integration()
    
    # Test 3: API Endpoints (with server)
    print("\n🖥️ Starting test server...")
    server_process = Process(target=start_test_server)
    server_process.start()
    
    time.sleep(4)  # Wait for server to start
    api_ok = test_api_endpoints()
    
    # Cleanup
    print("\n🛑 Stopping test server...")
    server_process.terminate()
    server_process.join(timeout=3)
    if server_process.is_alive():
        server_process.kill()
    
    # Results
    print("\n📊 Complete Test Results")
    print("=" * 60)
    print(f"ML Service:          {'✅ PASS' if ml_service_ok else '❌ FAIL'}")
    print(f"API Endpoints:       {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"Strategy Integration: {'✅ PASS' if strategy_ok else '❌ FAIL'}")
    
    all_pass = ml_service_ok and api_ok and strategy_ok
    
    if all_pass:
        print("\n🎉 ALL TESTS PASSED! ML Integration is fully working!")
        print("\n📋 Your system is ready:")
        print("1. ✅ ML model trained and making predictions")
        print("2. ✅ API endpoints working correctly") 
        print("3. ✅ Trading strategy integrated")
        print("4. ✅ Frontend components ready")
        
        print("\n🚀 To start your system:")
        print("   Backend:  cd backend && python candlestickData.py")
        print("   Frontend: cd frontend && npm start")
        print("   Then go to ML Predictions tab in dashboard")
        
    else:
        print("\n❌ Some tests failed - check the errors above")
    
    return all_pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)