#!/usr/bin/env python3
"""
ML Model Setup Script for TradePulse
This script sets up the ML model integration by:
1. Installing required dependencies
2. Training the model with your data
3. Testing the integration
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def run_command(command, description):
    """Run a command and handle errors"""
    log.info(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        log.info(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"❌ {description} failed: {e}")
        log.error(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        log.error("❌ Python 3.8+ is required for TensorFlow")
        return False
    log.info(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install ML dependencies"""
    log.info("📦 Installing ML dependencies...")
    
    # Change to backend directory
    backend_dir = Path("backend")
    if not backend_dir.exists():
        log.error("❌ Backend directory not found")
        return False
    
    os.chdir(backend_dir)
    
    # Install requirements
    success = run_command(
        "pip install tensorflow==2.15.0 keras==2.15.0",
        "Installing TensorFlow and Keras"
    )
    
    if not success:
        log.warning("⚠️ TensorFlow installation failed, trying alternative...")
        success = run_command(
            "pip install tensorflow-cpu==2.15.0",
            "Installing TensorFlow CPU version"
        )
    
    # Install other requirements
    if success:
        success = run_command(
            "pip install -r requirements.txt",
            "Installing other requirements"
        )
    
    os.chdir("..")
    return success

def copy_training_data():
    """Copy your ML model training data to the right location"""
    log.info("📊 Setting up training data...")
    
    # Check if your CSV file exists
    csv_file = "ML Model.ipynb"  # Your original file
    if os.path.exists(csv_file):
        log.info(f"✅ Found your ML notebook: {csv_file}")
        
        # Extract the CSV path from your notebook if needed
        # For now, we'll assume you have the CSV file
        csv_data_file = "XAUUSD_enhanced_all_timeframes.csv"
        if os.path.exists(csv_data_file):
            log.info(f"✅ Found training data: {csv_data_file}")
            return True
        else:
            log.warning(f"⚠️ Training data file not found: {csv_data_file}")
            log.info("💡 The model will train with live data instead (not recommended for production)")
            return True
    else:
        log.warning("⚠️ ML notebook not found, will use live data for training")
        return True

def train_model():
    """Train the ML model"""
    log.info("🤖 Training ML model...")
    
    # Change to backend directory
    os.chdir("backend")
    
    # Run the training script
    success = run_command(
        "python ml_model/train_model.py",
        "Training ML model"
    )
    
    os.chdir("..")
    return success

def test_integration():
    """Test the ML integration"""
    log.info("🧪 Testing ML integration...")
    
    os.chdir("backend")
    
    # Test the ML service
    test_code = '''
import sys
sys.path.append(".")
from ml_model.model_service import ml_service

# Test model status
status = ml_service.get_model_status()
print("Model Status:", status)

if status["is_loaded"]:
    print("✅ Model loaded successfully!")
    
    # Test prediction
    prediction = ml_service.predict(bars=100)
    if prediction:
        print("✅ Prediction test successful!")
        print(f"Signal: {prediction['signal']}")
        print(f"Confidence: {prediction['confidence']:.2%}")
    else:
        print("❌ Prediction test failed")
else:
    print("❌ Model not loaded")
'''
    
    with open("test_ml.py", "w") as f:
        f.write(test_code)
    
    success = run_command("python test_ml.py", "Testing ML integration")
    
    # Cleanup
    if os.path.exists("test_ml.py"):
        os.remove("test_ml.py")
    
    os.chdir("..")
    return success

def main():
    """Main setup function"""
    log.info("🚀 Starting TradePulse ML Model Setup...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        log.error("❌ Failed to install dependencies")
        return False
    
    # Setup training data
    copy_training_data()
    
    # Train model
    if not train_model():
        log.error("❌ Failed to train model")
        return False
    
    # Test integration
    if not test_integration():
        log.error("❌ Integration test failed")
        return False
    
    log.info("🎉 ML Model setup completed successfully!")
    log.info("📋 Next steps:")
    log.info("   1. Start your backend server: cd backend && python candlestickData.py")
    log.info("   2. Start your frontend: cd frontend && npm start")
    log.info("   3. Go to the ML Predictions tab in the dashboard")
    log.info("   4. Click 'Get Prediction' to test the model")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)