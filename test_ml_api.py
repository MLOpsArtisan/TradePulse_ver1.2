#!/usr/bin/env python3
"""
Quick ML API Test - Test ML endpoints without starting full server
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_ml_endpoints():
    """Test ML API endpoints directly"""
    print("🧪 Testing ML API Endpoints...")
    
    try:
        # Import Flask app components
        from flask import Flask
        from ml_api import ml_api
        
        # Create test app
        app = Flask(__name__)
        app.register_blueprint(ml_api)
        
        # Test with app context
        with app.test_client() as client:
            # Test status endpoint
            print("📊 Testing /api/ml/status...")
            response = client.get('/api/ml/status')
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print("✅ ML Status API working")
                print(f"   Model loaded: {data.get('data', {}).get('is_loaded', False)}")
                print(f"   TensorFlow available: {data.get('data', {}).get('tensorflow_available', False)}")
            else:
                print(f"❌ ML Status API failed: {response.status_code}")
                return False
            
            # Test prediction endpoint
            print("\n🔮 Testing /api/ml/predict...")
            response = client.get('/api/ml/predict')
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    prediction = data.get('data', {})
                    print("✅ ML Prediction API working")
                    print(f"   Signal: {prediction.get('signal', 'N/A')}")
                    print(f"   Confidence: {prediction.get('confidence', 0):.2%}")
                    print(f"   Expected Return: {prediction.get('expected_return', 0):.2f}%")
                else:
                    print(f"❌ ML Prediction API error: {data.get('error', 'Unknown')}")
                    return False
            else:
                print(f"❌ ML Prediction API failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ML API: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ML API Direct Test")
    print("=" * 50)
    
    success = test_ml_endpoints()
    
    print("\n📊 Test Results")
    print("=" * 50)
    
    if success:
        print("✅ ML API endpoints are working correctly!")
        print("\n🎉 Your ML integration is fully functional!")
        print("\n📋 To use the full system:")
        print("1. Start backend: cd backend && python candlestickData.py")
        print("2. Start frontend: cd frontend && npm start")
        print("3. Go to ML Predictions tab in the dashboard")
    else:
        print("❌ ML API has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)