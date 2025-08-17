from flask import Blueprint, jsonify, request
from utils.data_loader import load_predictions, calculate_prediction_stats

prediction_bp = Blueprint('predictions', __name__)


@prediction_bp.route('/predictions')
def get_predictions():
    """Get predictions with optional filtering and pagination"""
    try:
        # Get query parameters for filtering
        prediction_filter = request.args.get('prediction')  # 0 or 1
        min_probability = request.args.get('min_probability', type=float)
        max_probability = request.args.get('max_probability', type=float)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        
        # Load predictions data
        data = load_predictions()
        
        if data is None:
            return jsonify({
                "error": "No prediction data available",
                "message": "No prediction files found in the data/predictions directory"
            }), 404
        
        predictions = data['predictions']
        
        # Apply filters
        filtered_predictions = apply_filters(
            predictions, 
            prediction_filter, 
            min_probability, 
            max_probability
        )
        
        # Apply pagination
        paginated_data = paginate_predictions(filtered_predictions, page, per_page)
        
        # Calculate summary stats
        summary_stats = calculate_prediction_stats(predictions)
        
        response = {
            'predictions': paginated_data['predictions'],
            'pagination': paginated_data['pagination'],
            'summary_stats': summary_stats,
            'metadata': data['metadata']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_bp.route('/predictions/summary')
def get_predictions_summary():
    """Get high-level prediction statistics"""
    try:
        data = load_predictions()
        
        if data is None:
            return jsonify({"error": "No prediction data available"}), 404
        
        predictions = data['predictions']
        summary = calculate_prediction_stats(predictions)
        
        return jsonify({
            'summary': summary,
            'metadata': data['metadata'],
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_bp.route('/predictions/high-probability')
def get_high_probability_leads():
    """Get leads with high conversion probability (>70%)"""
    try:
        data = load_predictions()
        
        if data is None:
            return jsonify({"error": "No prediction data available"}), 404
        
        predictions = data['predictions']
        
        # Filter for high probability leads
        high_prob_leads = [
            pred for pred in predictions 
            if pred.get('probability', 0) > 0.7
        ]
        
        return jsonify({
            'high_probability_leads': high_prob_leads,
            'count': len(high_prob_leads),
            'threshold': 0.7,
            'metadata': data['metadata'],
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prediction_bp.route('/predictions/<lead_id>')
def get_prediction_by_id(lead_id):
    """Get specific lead prediction by ID"""
    try:
        data = load_predictions()
        
        if data is None:
            return jsonify({"error": "No prediction data available"}), 404
        
        predictions = data['predictions']
        
        # Find prediction by lead_id
        prediction = next(
            (pred for pred in predictions if str(pred.get('lead_id', '')) == str(lead_id)), 
            None
        )
        
        if prediction is None:
            return jsonify({
                "error": "Lead not found",
                "message": f"No prediction found for lead_id: {lead_id}"
            }), 404
        
        return jsonify({
            'prediction': prediction,
            'metadata': data['metadata'],
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Utility functions
def apply_filters(predictions, prediction_filter, min_prob, max_prob):
    """Apply filters to prediction data"""
    filtered = predictions
    
    if prediction_filter is not None:
        prediction_value = int(prediction_filter)
        filtered = [p for p in filtered if p.get('prediction') == prediction_value]
    
    if min_prob is not None:
        filtered = [p for p in filtered if p.get('probability', 0) >= min_prob]
    
    if max_prob is not None:
        filtered = [p for p in filtered if p.get('probability', 0) <= max_prob]
    
    return filtered

def paginate_predictions(predictions, page, per_page):
    """Paginate predictions data"""
    total = len(predictions)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_predictions = predictions[start:end]
    
    return {
        'predictions': paginated_predictions,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_next': end < total,
            'has_prev': page > 1
        }
    }

# Function to emit prediction updates via WebSocket (will be imported by dashboard)
def emit_prediction_update():
    """Emit prediction updates to connected clients"""
    try:
        # Import socketio here to avoid circular imports
        from routes.dashboard import socketio
        
        if socketio:
            # Get latest prediction summary
            data = load_predictions()
            if data:
                summary = calculate_prediction_stats(data['predictions'])
                
                # Emit to dashboard clients
                socketio.emit('prediction_update', {
                    'summary': summary,
                    'metadata': data['metadata'],
                    'timestamp': data['metadata']['model_timestamp']
                }, room='dashboard')
                
                print("📊 Prediction update emitted to dashboard")
                
    except Exception as e:
        print(f" Error emitting prediction update: {e}")
        
        
    




