#!/usr/bin/env python3
"""
Start Backend Server - Production startup script
"""

import os
import sys

def main():
    """Start the backend server"""
    print("🚀 Starting TradePulse Backend Server with ML Integration...")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir('backend')
    
    # Import and start the server
    try:
        from candlestickData import app, socketio
        
        print("✅ Flask app loaded successfully")
        print("✅ ML API integrated")
        print("✅ SocketIO configured")
        print("\n🌐 Server starting on http://localhost:5000")
        print("📊 ML API available at http://localhost:5000/api/ml/")
        print("\n📋 Available ML endpoints:")
        print("   • GET /api/ml/status - Model status")
        print("   • GET /api/ml/predict - Get predictions")
        print("   • POST /api/ml/train - Train model")
        print("\n🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the server
        socketio.run(
            app, 
            host='0.0.0.0',  # Allow external connections
            port=5000, 
            debug=False,  # Set to True for development
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()