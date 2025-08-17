import json
from flask import Blueprint, request, redirect, session, url_for
import os
from dotenv import load_dotenv
import requests

load_dotenv()

auth_bp = Blueprint('auth', __name__)

# HubSpot auth config
CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:5000/oauth-callback'
SCOPES = 'crm.objects.contacts.read'
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'hubspot_token.json')

@auth_bp.route('/connect-hubspot')
def connect_hubspot():
    """Redirect the user to HubSpot authorization page"""
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"scope={SCOPES}&"
        f"redirect_uri={REDIRECT_URI}"
    )
    return redirect(auth_url)

@auth_bp.route('/oauth-callback')
def oauth_callback():
    """Handle OAuth callback from HubSpot"""
    # Extract the authorization code from query parameters
    auth_code = request.args.get('code')
    if not auth_code:
        return "Error: No authorization code received", 400
    
    token_url = "https://api.hubapi.com/oauth/v1/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': auth_code
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return f"Error: {response.text}", 400
    
    tokens = response.json()
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)
        
    return " Authorization successful! You can now fetch predictions."

@auth_bp.route('/auth-status')
def auth_status():
    """Check if HubSpot authentication is valid"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        
        return {
            "authenticated": True,
            "token_exists": True,
            "expires_in": token_data.get("expires_in", "unknown")
        }
    except FileNotFoundError:
        return {
            "authenticated": False,
            "token_exists": False,
            "message": "No token file found. Please authenticate first."
        }