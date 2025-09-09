#!/usr/bin/env python3
"""
Test Server Startup - Quick test to verify server can start
"""

import sys
import os
import time
import threading
import requests
from multiprocessing import Process

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def start_server():
    """Start the Flask server in a separate process"""
    try:
        os.chdir('backend')
        from candlestickData import app, socketio
        
        print("🚀 Starting Flask server...")
        # Start server without debug mode for testing
        socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"❌ Server startup error: {e}")

def test_endpoints():
    """Test ML API endpoints"""
    print("⏳ Waiting for server to start...")
    time.sleep(3)  # Give server time to start
    
    try:
        # Test ML status endpoint
        print("📊 Testing ML Status endpoint...")
        response = requests.get('http://127.0.0.1:5000/api/ml/status', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ML Status API working!")
            print(f"   Model loaded: {data.get('data', {}).get('is_loaded', False)}")
            
            # Test prediction endpoint
            print("🔮 Testing ML Prediction endpoint...")
            response = requests.get('http://127.0.0.1:5000/api/ml/predict', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    prediction = data.get('data', {})
                    print("✅ ML Prediction API working!")
                    print(f"   Signal: {prediction.get('signal', 'N/A')}")
                    print(f"   Confidence: {prediction.get('confidence', 0):.2%}")
                    return True
                else:
                    print(f"❌ Prediction error: {data.get('error', 'Unknown')}")
            else:
                print(f"❌ Prediction API failed: {response.status_code}")
        else:
            print(f"❌ Status API failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    return False

def main():
    """Main test function"""
    print("🧪 Testing Server Startup and ML API")
    print("=" * 50)
    
    # Start server in background process
    server_process = Process(target=start_server)
    server_process.start()
    
    try:
        # Test endpoints
        success = test_endpoints()
        
        print("\n📊 Test Results")
        print("=" * 50)
        
        if success:
            print("✅ Server and ML API are working correctly!")
            print("🎉 Your backend is ready for production!")
        else:
            print("❌ Server or ML API has issues")
            
    finally:
        # Clean up
        print("\n🛑 Stopping test server...")
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)