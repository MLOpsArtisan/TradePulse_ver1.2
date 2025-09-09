"""
Model Training Script - Train the ML model with your data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from model_service import MLModelService
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def main():
    """Train the ML model"""
    print("🤖 Starting ML Model Training...")
    
    # Initialize ML service
    ml_service = MLModelService()
    
    # Check if we have your CSV data
    csv_path = "../../XAUUSD_enhanced_all_timeframes.csv"  # Adjust path as needed
    
    if os.path.exists(csv_path):
        print(f"📊 Found training data: {csv_path}")
        success = ml_service.train_model(csv_path)
    else:
        print("⚠️ No CSV data found, training with live data (not recommended)")
        success = ml_service.train_model()
    
    if success:
        print("✅ Model training completed successfully!")
        print(f"📁 Model saved to: {ml_service.model_path}")
        print(f"📁 Scalers saved to: {ml_service.scaler_path}")
        
        # Test prediction
        print("\n🔮 Testing prediction...")
        prediction = ml_service.predict()
        if prediction:
            print(f"Signal: {prediction['signal']}")
            print(f"Confidence: {prediction['confidence']:.2%}")
            print(f"Expected Return: {prediction['expected_return']:.2f}%")
        else:
            print("❌ Prediction test failed")
    else:
        print("❌ Model training failed!")

if __name__ == "__main__":
    main()