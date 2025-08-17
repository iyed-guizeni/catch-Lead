from flask import Flask, jsonify
from routes.hubspot_auth import auth_bp
from routes.prediction import prediction_bp
from routes.dashboard import dashboard_bp, init_socketio  # Add these imports
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(prediction_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp)  # Add dashboard blueprint

# Initialize SocketIO for real-time dashboard
socketio = init_socketio(app)

@app.route('/')
def index():
    """Main landing page with available endpoints"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lead Scoring MLOps API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
            .method { color: #007bff; font-weight: bold; }
            .auth { color: #28a745; }
            .predictions { color: #6f42c1; }
            .dashboard { color: #fd7e14; }  /* Add dashboard styling */
            h1 { color: #333; }
            h2 { color: #666; margin-top: 30px; }
        </style>
    </head>
    <body>
        <h1>🚀 Lead Scoring MLOps API</h1>
        <p>Welcome to the Lead Scoring API with Real-Time Dashboard support.</p>
        
        <h2 class="dashboard">📊 Dashboard Endpoints (NEW!)</h2>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/status">/api/dashboard/status</a> - Dashboard API status
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/executive-summary">/api/dashboard/executive-summary</a> - Executive metrics
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/real-time-performance">/api/dashboard/real-time-performance</a> - Real-time performance
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/conversion-trends">/api/dashboard/conversion-trends</a> - Conversion trends
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/system-health">/api/dashboard/system-health</a> - System health
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/live-stats">/api/dashboard/live-stats</a> - Live statistics
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/dashboard/predictions-overview">/api/dashboard/predictions-overview</a> - Predictions overview
        </div>
        <div class="endpoint">
            <span class="method">WebSocket</span> ws://localhost:5000/socket.io/ - Real-time dashboard updates
        </div>
        
        <h2 class="auth">🔐 Authentication Endpoints</h2>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/connect-hubspot">/connect-hubspot</a> - Connect to HubSpot OAuth
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/oauth-callback">/oauth-callback</a> - OAuth callback handler
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/auth-status">/auth-status</a> - Check authentication status
        </div>
        
        <h2 class="predictions">📊 Predictions API Endpoints</h2>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/predictions">/api/predictions</a> - Get all lead predictions (with filtering & pagination)
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/predictions/summary">/api/predictions/summary</a> - Get prediction summary statistics
        </div>
        <div class="endpoint">
            <span class="method">GET</span> /api/predictions/&lt;lead_id&gt; - Get specific lead prediction
        </div>
        <div class="endpoint">
            <span class="method">GET</span> <a href="/api/predictions/high-probability">/api/predictions/high-probability</a> - Get high-probability leads (>70%)
        </div>
        
        <h2>📋 Query Parameters (for /api/predictions)</h2>
        <ul>
            <li><strong>prediction</strong>: Filter by prediction (0 or 1)</li>
            <li><strong>min_probability</strong>: Minimum probability threshold (0.0-1.0)</li>
            <li><strong>max_probability</strong>: Maximum probability threshold (0.0-1.0)</li>
            <li><strong>page</strong>: Page number for pagination (default: 1)</li>
            <li><strong>per_page</strong>: Items per page (default: 25)</li>
        </ul>
        
        <h2>🔄 WebSocket Events</h2>
        <ul>
            <li><strong>live_stats_update</strong>: Real-time system statistics (every 5s)</li>
            <li><strong>performance_update</strong>: Model performance data (every 15s)</li>
            <li><strong>health_update</strong>: System health metrics (every 30s)</li>
            <li><strong>prediction_summary_update</strong>: Prediction statistics (every 60s)</li>
            <li><strong>request_update</strong>: Manual update request (client → server)</li>
            <li><strong>request_prediction_details</strong>: Request detailed predictions (client → server)</li>
        </ul>
        
        <h2>🔧 Examples</h2>
        <ul>
            <li><a href="/api/predictions?prediction=1">/api/predictions?prediction=1</a> - Get positive predictions</li>
            <li><a href="/api/predictions?min_probability=0.5">/api/predictions?min_probability=0.5</a> - Get leads with >50% probability</li>
        </ul>
        
        <h2>🚀 WebSocket Usage</h2>
        <p>Connect to real-time dashboard updates:</p>
        <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
const socket = io('http://localhost:5000');
socket.on('performance_update', (data) => {
    // Update your dashboard in real-time
});
        </pre>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": "2024-12-23T10:00:00Z",
        "version": "1.0.0",
        "components": {
            "api": "operational",
            "dashboard": "operational",
            "websocket": "operational"
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": [
            "/",
            "/health",
            "/connect-hubspot",
            "/auth-status",
            "/api/predictions",
            "/api/predictions/summary",
            "/api/predictions/high-probability",
            "/api/dashboard/status",
            "/api/dashboard/executive-summary",
            "/api/dashboard/real-time-performance",
            "/api/dashboard/predictions-overview",
            "/api/dashboard/live-stats",
            "/api/dashboard/system-health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on our end"
    }), 500

# Enable CORS for API endpoints (optional)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ['HUBSPOT_CLIENT_ID', 'HUBSPOT_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        # Don't exit if only missing HubSpot vars - dashboard still works
        print("⚠️  Dashboard will work in demo mode without HubSpot integration")
    
    print("🚀 Starting Lead Scoring MLOps API with Real-Time Dashboard...")
    print("📋 Available endpoints:")
    print("   - Main page: http://localhost:5000/")
    print("   - Health check: http://localhost:5000/health")
    print("   - HubSpot auth: http://localhost:5000/connect-hubspot")
    print("   - Predictions: http://localhost:5000/api/predictions")
    print("   - Dashboard API: http://localhost:5000/api/dashboard/status")
    print("   - WebSocket: ws://localhost:5000/socket.io/")
    
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)