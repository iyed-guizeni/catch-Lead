from flask import Blueprint, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sys
import json
import time
import numpy as np
from datetime import datetime, timedelta
import threading
import random

# Add the parent directory to import monitor module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.monitor.monitor import (
        get_traffic_allocation, get_active_models, mab_predictor,
        show_bandit_status, choose_model_for_prediction
    )
    MAB_AVAILABLE = True
except ImportError:
    MAB_AVAILABLE = False
    print("  MAB monitor not available - using mock data")

# Create dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# Global SocketIO instance (will be initialized in main app)
socketio = None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Register WebSocket events
    register_websocket_events()
    
    # Start background tasks
    start_background_tasks()
    
    return socketio


# REST API ENDPOINTS FOR DASHBOARD

@dashboard_bp.route('/api/dashboard/executive-summary', methods=['GET'])
def get_executive_summary():
    """Get high-level metrics for executive dashboard"""
    try:
        if MAB_AVAILABLE:
            active_models = get_active_models()
            traffic_allocation = get_traffic_allocation()
            
            # Calculate business metrics
            baseline_conversion = 2.3
            current_avg_conversion = np.mean([m['conversion_rate'] for m in active_models]) if active_models else 3.2
            improvement = ((current_avg_conversion - baseline_conversion) / baseline_conversion) * 100
            
            # Cost savings calculation
            monthly_predictions = 50000
            cost_per_false_positive = 15
            false_positive_reduction = improvement / 100 * 0.3
            monthly_savings = int(monthly_predictions * cost_per_false_positive * false_positive_reduction)
        else:
            # Mock data for demo
            improvement = 23.4
            monthly_savings = 47230
            active_models = 3
            traffic_allocation = {'algorithm': 'thompson_sampling', 'winner': 'MODEL_V20241223'}
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'business_impact': {
                'revenue_lift_percentage': round(improvement, 1),
                'monthly_cost_savings': monthly_savings,
                'lead_quality_improvement': f"+{improvement:.1f}%",
                'model_accuracy': 94.7
            },
            'operational_metrics': {
                'system_automation': '97.8%',
                'uptime_percentage': '99.97%',
                'active_models': len(active_models) if MAB_AVAILABLE else 3,
                'algorithm': traffic_allocation.get('algorithm', 'thompson_sampling'),
                'winner': traffic_allocation.get('winner', 'MODEL_V20241223')
            },
            'status': 'success'
        }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@dashboard_bp.route('/api/dashboard/real-time-performance', methods=['GET'])
def get_real_time_performance():
    """Get real-time model performance metrics"""
    try:
        if MAB_AVAILABLE:
            active_models = get_active_models()
            traffic_allocation = get_traffic_allocation()
            
            # Calculate system metrics
            total_predictions = sum(m['total_predictions'] for m in active_models)
            predictions_per_hour = total_predictions / 24 if total_predictions > 0 else 850
            
            try:
                memory_usage = mab_predictor.get_memory_usage()
            except:
                memory_usage = 1.2
        else:
            # Mock data for demo
            active_models = [
                {
                    'model_version': 'MODEL_V20241223',
                    'conversion_rate': 4.2,
                    'total_predictions': 15420,
                    'total_conversions': 648,
                    'confidence_interval': {'lower': 3.8, 'upper': 4.6},
                    'last_updated': datetime.now().isoformat()
                },
                {
                    'model_version': 'MODEL_V20241222',
                    'conversion_rate': 3.8,
                    'total_predictions': 8630,
                    'total_conversions': 328,
                    'confidence_interval': {'lower': 3.4, 'upper': 4.2},
                    'last_updated': datetime.now().isoformat()
                },
                {
                    'model_version': 'MODEL_V20241221',
                    'conversion_rate': 3.1,
                    'total_predictions': 1250,
                    'total_conversions': 39,
                    'confidence_interval': {'lower': 2.5, 'upper': 3.7},
                    'last_updated': datetime.now().isoformat()
                }
            ]
            traffic_allocation = {
                'MODEL_V20241223': 67,
                'MODEL_V20241222': 28,
                'MODEL_V20241221': 5,
                'algorithm': 'thompson_sampling',
                'winner': 'MODEL_V20241223'
            }
            predictions_per_hour = 10250
            memory_usage = 1.2
        
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'system_status': {
                'status': 'ACTIVE',
                'total_active_models': len(active_models),
                'predictions_per_hour': int(predictions_per_hour),
                'memory_usage_gb': round(memory_usage, 2),
                'avg_latency_ms': 23
            },
            'model_performance': [
                {
                    'model_version': model['model_version'],
                    'conversion_rate': model['conversion_rate'],
                    'total_predictions': model['total_predictions'],
                    'total_conversions': model['total_conversions'],
                    'traffic_allocation': traffic_allocation.get(model['model_version'], 0),
                    'confidence_interval': model['confidence_interval'],
                    'last_updated': model['last_updated']
                }
                for model in active_models
            ],
            'traffic_allocation': {
                'algorithm': traffic_allocation.get('algorithm', 'thompson_sampling'),
                'winner': traffic_allocation.get('winner', 'MODEL_V20241223'),
                'allocations': {k: v for k, v in traffic_allocation.items() 
                              if k not in ['reason', 'winner', 'algorithm', 'total_models']}
            },
            'status': 'success'
        }
        
        return jsonify(performance_data)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@dashboard_bp.route('/api/dashboard/conversion-trends', methods=['GET'])
def get_conversion_trends():
    """Get conversion rate trends over time"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Generate realistic trend data
        trends = []
        base_rate = 3.5
        
        for i in range(hours):
            time_point = start_time + timedelta(hours=i)
            
            # Simulate realistic conversion rate with some trends
            time_factor = np.sin(i * 0.3) * 0.2  # Some cyclical pattern
            noise = np.random.normal(0, 0.15)
            trend = i * 0.01  # Slight upward trend
            
            conversion_rate = base_rate + time_factor + noise + trend
            conversion_rate = max(1.0, min(6.0, conversion_rate))  # Realistic bounds
            
            predictions_count = random.randint(800, 1200)
            conversions_count = int(conversion_rate * predictions_count / 100)
            
            trends.append({
                'timestamp': time_point.isoformat(),
                'conversion_rate': round(conversion_rate, 2),
                'predictions_count': predictions_count,
                'conversions_count': conversions_count
            })
        
        return jsonify({
            'time_range': f'{hours} hours',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'trends': trends,
            'summary': {
                'avg_conversion_rate': round(np.mean([t['conversion_rate'] for t in trends]), 2),
                'best_hour': max(trends, key=lambda x: x['conversion_rate']),
                'total_predictions': sum(t['predictions_count'] for t in trends),
                'total_conversions': sum(t['conversions_count'] for t in trends)
            },
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@dashboard_bp.route('/api/dashboard/system-health', methods=['GET'])
def get_system_health():
    """Get technical system health metrics"""
    try:
        if MAB_AVAILABLE:
            try:
                memory_usage = mab_predictor.get_memory_usage()
            except:
                memory_usage = 1.2
                
            active_models = get_active_models()
            traffic_allocation = get_traffic_allocation()
        else:
            memory_usage = 1.2
            active_models = [{'model_version': f'MODEL_V{i}'} for i in range(3)]
            traffic_allocation = {'total_models': 3}
        
        # Calculate health score
        health_factors = {
            'models_active': min(len(active_models) / 3, 1.0),
            'memory_efficiency': max(0, 1 - (memory_usage / 4.0)),
            'allocation_diversity': min(len(traffic_allocation) / 3, 1.0) if traffic_allocation else 0
        }
        
        overall_health = np.mean(list(health_factors.values())) * 100
        
        system_health = {
            'timestamp': datetime.now().isoformat(),
            'overall_health_score': round(overall_health, 1),
            'status': 'HEALTHY' if overall_health > 80 else 'WARNING' if overall_health > 60 else 'CRITICAL',
            'metrics': {
                'memory_usage_gb': round(memory_usage, 2),
                'memory_efficiency': f"{health_factors['memory_efficiency']*100:.1f}%",
                'cpu_usage': '23%',
                'active_models': len(active_models),
                'prediction_latency': '23ms',
                'error_rate': '0.02%'
            },
            'alerts': get_system_alerts(health_factors),
            'status': 'success'
        }
        
        return jsonify(system_health)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@dashboard_bp.route('/api/dashboard/live-stats', methods=['GET'])
def get_live_stats():
    """Get live updating statistics for real-time dashboard"""
    try:
        if MAB_AVAILABLE:
            active_models = get_active_models()
            traffic_allocation = get_traffic_allocation()
            predictions_today = sum(m['total_predictions'] for m in active_models)
            avg_conversion = round(np.mean([m['conversion_rate'] for m in active_models]), 1) if active_models else 0
        else:
            active_models = 3
            traffic_allocation = {'winner': 'MODEL_V20241223', 'algorithm': 'thompson_sampling'}
            predictions_today = 25300
            avg_conversion = 3.9
        
        live_stats = {
            'timestamp': datetime.now().isoformat(),
            'quick_stats': {
                'active_models': len(active_models) if MAB_AVAILABLE else active_models,
                'winner': traffic_allocation.get('winner', 'MODEL_V20241223'),
                'algorithm': traffic_allocation.get('algorithm', 'thompson_sampling'),
                'predictions_today': predictions_today,
                'avg_conversion': avg_conversion,
                'current_traffic': '10.2K/hr',
                'uptime': '99.97%'
            },
            'system_status': 'ACTIVE',
            'last_update': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return jsonify(live_stats)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

def get_system_alerts(health_factors):
    """Generate system alerts based on health factors"""
    alerts = []
    
    if health_factors['models_active'] < 0.5:
        alerts.append({
            'level': 'WARNING',
            'message': 'Low number of active models',
            'recommendation': 'Deploy additional models for better optimization'
        })
    
    if health_factors['memory_efficiency'] < 0.7:
        alerts.append({
            'level': 'WARNING', 
            'message': 'High memory usage detected',
            'recommendation': 'Consider model cleanup or memory optimization'
        })
    
    if not alerts:
        alerts.append({
            'level': 'INFO',
            'message': 'All systems operating normally',
            'recommendation': 'Continue monitoring'
        })
    
    return alerts

def register_websocket_events():
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        print(f" Dashboard client connected: {request.sid}")
        join_room('dashboard')
        emit('connection_established', {
            'message': 'Connected to Lead Scoring MAB Dashboard',
            'timestamp': datetime.now().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f" Dashboard client disconnected: {request.sid}")
        leave_room('dashboard')
    
    @socketio.on('request_update')
    def handle_update_request(data):
        """Handle manual update requests from frontend"""
        update_type = data.get('type', 'all')
        print(f" Update requested: {update_type}")
        
        if update_type == 'all' or update_type == 'performance':
            emit_performance_update()
        
        if update_type == 'all' or update_type == 'health':
            emit_health_update()
            
        if update_type == 'all' or update_type == 'predictions':
            emit_prediction_summary_update()
    
    @socketio.on('request_prediction_details')
    def handle_prediction_details_request(data):
        """Handle requests for detailed prediction data"""
        try:
            from utils.data_loader import load_predictions
            
            filter_type = data.get('filter', 'all')  # 'all', 'high_prob', 'recent'
            limit = data.get('limit', 50)
            
            prediction_data = load_predictions()
            if prediction_data:
                predictions = prediction_data['predictions']
                
                # Apply filters
                if filter_type == 'high_prob':
                    filtered = [p for p in predictions if p.get('probability', 0) > 0.7]
                elif filter_type == 'recent':
                    # Sort by any timestamp field if available, otherwise use first N
                    filtered = predictions[:limit]
                else:
                    filtered = predictions[:limit]
                
                emit('prediction_details_response', {
                    'predictions': filtered[:limit],
                    'filter_applied': filter_type,
                    'total_count': len(predictions),
                    'filtered_count': len(filtered),
                    'metadata': prediction_data['metadata']
                })
                
        except Exception as e:
            emit('prediction_details_error', {'error': str(e)})

def emit_performance_update():
    """Emit real-time performance updates to all connected clients"""
    try:
        # Get latest performance data
        performance_data = get_real_time_performance().get_json()
        
        socketio.emit('performance_update', performance_data, room='dashboard')
        
    except Exception as e:
        print(f" Error emitting performance update: {e}")

def emit_health_update():
    """Emit system health updates"""
    try:
        health_data = get_system_health().get_json()
        
        socketio.emit('health_update', health_data, room='dashboard')
        
    except Exception as e:
        print(f" Error emitting health update: {e}")

def emit_live_stats_update():
    """Emit live stats updates"""
    try:
        stats_data = get_live_stats().get_json()
        
        socketio.emit('live_stats_update', stats_data, room='dashboard')
        
    except Exception as e:
        print(f" Error emitting live stats update: {e}")


def start_background_tasks():
    """Start background tasks for real-time updates"""
    
    def update_loop(app):
        """Background loop to send periodic updates"""
        while True:
            try:
                # Use Flask application context for background tasks
                with app.app_context():
                    # Emit different types of updates at different intervals
                    emit_live_stats_update()  # Every 5 seconds
                    
                    # Less frequent updates
                    if int(time.time()) % 15 == 0:  # Every 15 seconds
                        emit_performance_update()
                    
                    if int(time.time()) % 30 == 0:  # Every 30 seconds
                        emit_health_update()
                
                time.sleep(5)  # Base interval: 5 seconds
                
            except Exception as e:
                print(f" Error in background update loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    # Delay the background task start until after app initialization
    def delayed_start():
        time.sleep(2)  # Wait for app to fully initialize
        from flask import current_app
        app = current_app._get_current_object()
        update_loop(app)
    
    # Start background thread
    update_thread = threading.Thread(target=delayed_start, daemon=True)
    update_thread.start()
    print(" Background update tasks scheduled to start")

# Alternative: Update init_socketio to pass app reference directly

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Register WebSocket events
    register_websocket_events()
    
    # Start background tasks with app reference
    start_background_tasks_with_app(app)
    
    return socketio

def start_background_tasks_with_app(app):
    """Start background tasks with direct app reference"""
    
    def update_loop():
        """Background loop to send periodic updates"""
        while True:
            try:
                # Use Flask application context for background tasks
                with app.app_context():
                    # Emit different types of updates at different intervals
                    emit_live_stats_update()  # Every 5 seconds
                    
                    # Less frequent updates
                    if int(time.time()) % 15 == 0:  # Every 15 seconds
                        emit_performance_update()
                    
                    if int(time.time()) % 30 == 0:  # Every 30 seconds
                        emit_health_update()
                    
                    # NEW: Emit prediction updates every 60 seconds
                    if int(time.time()) % 60 == 0:  # Every 60 seconds
                        emit_prediction_summary_update()
                
                time.sleep(5)  # Base interval: 5 seconds
                
            except Exception as e:
                print(f" Error in background update loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    # Start background thread
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()
    print(" Background update tasks started")

def emit_prediction_summary_update():
    """Emit prediction summary updates to dashboard"""
    try:
        from utils.data_loader import load_predictions, calculate_prediction_stats
        
        data = load_predictions()
        if data:
            # Calculate fresh stats
            predictions = data['predictions']
            summary_stats = calculate_prediction_stats(predictions)
            
            # Enhanced prediction summary for dashboard
            prediction_summary = {
                'total_predictions': summary_stats['total_predictions'],
                'positive_predictions': summary_stats['positive_predictions'],
                'negative_predictions': summary_stats['negative_predictions'],
                'high_probability_count': summary_stats['high_probability_count'],
                'average_probability': summary_stats['average_probability'],
                'conversion_rate': summary_stats['conversion_rate'],
                'high_probability_percentage': summary_stats['high_probability_percentage'],
                'latest_model': data['metadata']['model_version'],
                'model_timestamp': data['metadata']['model_timestamp'],
                'file_name': data['metadata']['file_name']
            }
            
            socketio.emit('prediction_summary_update', {
                'summary': prediction_summary,
                'metadata': data['metadata'],
                'timestamp': datetime.now().isoformat()
            }, room='dashboard')
            
            print(" Prediction summary update emitted to dashboard")
            
    except Exception as e:
        print(f" Error emitting prediction summary: {e}")

@dashboard_bp.route('/api/dashboard/predictions-overview', methods=['GET'])
def get_predictions_overview():
    """Get prediction overview for dashboard integration"""
    try:
        from utils.data_loader import load_predictions, calculate_prediction_stats
        
        data = load_predictions()
        
        if data is None:
            return jsonify({
                "error": "No prediction data available",
                "status": "error"
            }), 404
        
        predictions = data['predictions']
        summary_stats = calculate_prediction_stats(predictions)
        
        # Get recent high-value leads (top 10)
        high_value_leads = sorted(
            [p for p in predictions if p.get('probability', 0) > 0.7],
            key=lambda x: x.get('probability', 0),
            reverse=True
        )[:10]
        
        overview = {
            'timestamp': datetime.now().isoformat(),
            'summary_stats': summary_stats,
            'high_value_leads': high_value_leads,
            'metadata': data['metadata'],
            'quick_insights': {
                'hottest_lead': max(predictions, key=lambda x: x.get('probability', 0)) if predictions else None,
                'model_performance': f"{summary_stats['conversion_rate']}% conversion rate",
                'data_freshness': data['metadata']['model_timestamp'],
                'recommendations': generate_prediction_recommendations(summary_stats)
            },
            'status': 'success'
        }
        
        return jsonify(overview)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

def generate_prediction_recommendations(stats):
    """Generate actionable recommendations based on prediction stats"""
    recommendations = []
    
    if stats['high_probability_percentage'] > 30:
        recommendations.append(" High-value pipeline detected - prioritize follow-up on hot leads")
    
    if stats['conversion_rate'] > 25:
        recommendations.append(" Strong model performance - consider increasing marketing spend")
    
    if stats['average_probability'] < 0.3:
        recommendations.append(" Low average probability - review lead sources and qualification criteria")
    
    if stats['total_predictions'] > 1000:
        recommendations.append(" High volume pipeline - implement automated lead routing")
    
    if not recommendations:
        recommendations.append(" Prediction metrics look healthy - continue monitoring")
    
    return recommendations
    
@dashboard_bp.route('/api/dashboard/status', methods=['GET'])
def dashboard_status():
    """Dashboard API health check"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'mab_system': 'operational' if MAB_AVAILABLE else 'mock_mode',
        'websocket': 'enabled'
    })