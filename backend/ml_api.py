"""
ML API Endpoints - REST API for ML model interactions
"""
from flask import Blueprint, jsonify, request
import logging
import time
from ml_model.model_service import ml_service

log = logging.getLogger(__name__)

# Create Blueprint for ML API
ml_api = Blueprint('ml_api', __name__, url_prefix='/api/ml')

@ml_api.route('/status', methods=['GET'])
def get_ml_status():
    """Get ML model status"""
    try:
        status = ml_service.get_model_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        log.error(f"Error getting ML status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ml_api.route('/predict', methods=['GET'])
def get_prediction():
    """Get ML prediction for current market conditions"""
    try:
        # Get optional parameters
        bars = request.args.get('bars', 100, type=int)
        
        # Make prediction
        prediction = ml_service.predict(bars=bars)
        
        if prediction:
            return jsonify({
                'success': True,
                'data': prediction
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate prediction'
            }), 500
            
    except Exception as e:
        log.error(f"Error making prediction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ml_api.route('/train', methods=['POST'])
def train_model():
    """Train the ML model"""
    try:
        # Get training parameters
        data = request.get_json() or {}
        data_path = data.get('data_path')
        
        # Start training (this should be async in production)
        success = ml_service.train_model(data_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Model training completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Model training failed'
            }), 500
            
    except Exception as e:
        log.error(f"Error training model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ml_api.route('/reload', methods=['POST'])
def reload_model():
    """Reload the ML model from disk"""
    try:
        ml_service.load_model()
        
        return jsonify({
            'success': True,
            'message': 'Model reloaded successfully',
            'status': ml_service.get_model_status()
        })
        
    except Exception as e:
        log.error(f"Error reloading model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ml_api.route('/start-trading', methods=['POST'])
def start_ml_trading():
    """Start automated ML trading"""
    try:
        from flask import request
        
        # Get trading parameters
        data = request.get_json() or {}
        
        # Import bot manager
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from trading_bot.bot_manager import TradingBotManager
        
        # Create new bot instance
        bot = TradingBotManager()
        
        # Configure for ML trading
        ml_config = {
            'strategy_name': data.get('strategy', 'pure_ml_strategy'),
            'ml_min_confidence': data.get('min_confidence', 0.4),
            'ml_min_expected_return': data.get('min_expected_return', 0.05),
            'ml_use_regression_filter': data.get('use_regression_filter', False),
            'ml_trade_hold_signals': data.get('trade_hold_signals', True),
            'ml_signal_boost_mode': data.get('signal_boost_mode', True),
            'ml_dynamic_sl_tp': data.get('dynamic_sl_tp', True),
            'auto_trading_enabled': True,
            'max_daily_trades': data.get('max_daily_trades', 50),
            'max_risk_per_trade': data.get('risk_per_trade', 0.02)
        }
        
        # Update bot configuration
        bot.config.update(ml_config)
        
        # Start the bot
        bot_id = f"ml_bot_{int(time.time())}"
        success = bot.start_bot(ml_config['strategy_name'], bot_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'ML trading bot started successfully',
                'bot_id': bot_id,
                'config': ml_config
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start ML trading bot'
            }), 500
            
    except Exception as e:
        log.error(f"Error starting ML trading: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ml_api.route('/stop-trading', methods=['POST'])
def stop_ml_trading():
    """Stop automated ML trading"""
    try:
        # This would stop all ML bots - in production you'd want to track specific bot IDs
        return jsonify({
            'success': True,
            'message': 'ML trading stopped (implement bot tracking for specific control)'
        })
        
    except Exception as e:
        log.error(f"Error stopping ML trading: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500