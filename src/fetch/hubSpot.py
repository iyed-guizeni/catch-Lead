import os
import json
#import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from datetime import datetime
import sys

# Add the adapter directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'adapter'))

load_dotenv()
LAST_FETCH= os.path.join(os.path.dirname(__file__),'..','..','config','last_fetch_timestamp.json')



def get_access_token_from_file(TOKEN_FILE):
  
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
    return data["access_token"]

def check_for_last_fetch():
    try:
        with open(LAST_FETCH, 'r') as f:
            data = json.load(f)
        # Handle both old format (single timestamp) and new format (separate timestamps)
        if isinstance(data, dict):
            return data
        else:
            # Convert old format to new format
            return {
                "last_fetch_labeled": data,
                "last_fetch_unlabeled": data
            }
    except FileNotFoundError:
        print("Last fetch timestamp file not found. This might be the first run.")
        return {
            "last_fetch_labeled": None,
            "last_fetch_unlabeled": None
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing last fetch timestamp: {e}")
        return {
            "last_fetch_labeled": None,
            "last_fetch_unlabeled": None
        }  
    
def update_last_fetch_timestamp(data_type, timestamp):
    try:
        # Read existing data
        existing_data = check_for_last_fetch()
        
        #Clean up any old typos and normalize to correct spelling
        if "last_fetch_labled" in existing_data:
            # Migrate old typo to correct spelling
            if data_type == "labeled" and existing_data["last_fetch_labled"]:
                existing_data["last_fetch_labeled"] = existing_data["last_fetch_labled"]
            # Remove the typo key
            del existing_data["last_fetch_labled"]
        
        # Update specific timestamp with correct spelling
        key = f"last_fetch_{data_type}"
        existing_data[key] = timestamp
        
        # Write back to file
        with open(LAST_FETCH, 'w') as f:
            json.dump(existing_data, f, indent=2)
            
        
    except Exception as e:
        print(f" Error updating last fetch timestamp: {e}")

class HubSpotLeadFetcher:
    """Class to fetch leads from HubSpot CRM using OAuth."""

    def __init__(self, access_token=None):
       
        self.access_token = access_token or os.environ.get("HUBSPOT_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("HubSpot OAuth access token not provided and HUBSPOT_ACCESS_TOKEN environment variable not set.")

        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

 
    
    def fetch_leads(self,time,filter_groups,data_type):
        
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
        
        
        
        if time:
            readable_time = datetime.fromtimestamp(time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            print(f" Filtering for contacts modified after: {readable_time}")
            
            for filter_group in filter_groups:
                filter_group["filters"].append({
                    "propertyName": "lastmodifieddate",
                    "operator": "GT",
                    "value": str(time)
                })
        payload = {
            "filterGroups": filter_groups,
               
            
            "properties": [
                "lead_id","firstname", "lastname", "email", "lifecyclestage", "hs_lead_status", "company_size", "source","region","contact_attempts","days_since_first_contact","job_title","has_company_website"
            ],
            "limit": 100
        }

        
            
        try:
            response = requests.post(url, headers=self.headers ,json=payload)
            
            response.raise_for_status()
             
           
            try:
                
                data = response.json()
                current_timestamp = int(datetime.now().timestamp() * 1000)
                update_last_fetch_timestamp(data_type, current_timestamp)
            except ValueError as json_error:
                print(f"Invalid JSON response , error message: {json_error}, data : {data}")
                return []
        except requests.exceptions.HTTPError as httpError:
            print(f"PROBLEM while fetch Data: {httpError.response}")
            return httpError.response.status_code
             
           
        return data
            
 

    def refresh_token(self, TOKEN_FILE):
        """Refresh the OAuth token using refresh_token"""
        try:
            # Read current token data
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            refresh_token = token_data.get('refresh_token')
            if not refresh_token:
                print(" No refresh token available")
                return False
                
            # Refresh token request
            token_url = "https://api.hubapi.com/oauth/v1/token"
            data = {
                "grant_type": "refresh_token",
                "client_id": os.environ.get("HUBSPOT_CLIENT_ID"),
                "client_secret": os.environ.get("HUBSPOT_CLIENT_SECRET"),
                "refresh_token": refresh_token
            }
            
            response = requests.post(token_url, data=data)
            if response.status_code != 200:
                print(f" Token refresh failed: {response.text}")
                return False
                
            new_token_data = response.json()
            
            # Preserve refresh token if not returned
            if 'refresh_token' not in new_token_data:
                new_token_data['refresh_token'] = refresh_token
                
            # Update stored token
            with open(TOKEN_FILE, 'w') as f:
                json.dump(new_token_data, f, indent=4)
                
            # Update instance token
            self.access_token = new_token_data['access_token']
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            return True
            
        except Exception as e:
            print(f" Error during token refresh: {e}")
            return False
    


