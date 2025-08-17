import os
import json
import time
from fetch.hubSpot import HubSpotLeadFetcher
from fetch.hubSpot import get_access_token_from_file
from adapter.adapt_fetched_data import HubSpotDataAdapter

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'hubspot_token.json')
TIMESTAMP_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'last_fetch_timestamp.json')

def check_for_last_fetch():
    """Check for last fetch timestamp, create default if not exists"""
    try:
        with open(TIMESTAMP_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(" First run detected - creating default timestamp file")
        
        # Create default timestamps (30 days ago for initial comprehensive fetch)
        thirty_days_ago = int((time.time() - (30 * 24 * 60 * 60)) * 1000)
        
        default_timestamps = {
            "last_fetch_labeled": thirty_days_ago,
            "last_fetch_unlabeled": thirty_days_ago
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(TIMESTAMP_FILE), exist_ok=True)
        
        # Save default timestamps
        with open(TIMESTAMP_FILE, 'w') as f:
            json.dump(default_timestamps, f, indent=2)
        
        print(f"Created timestamp file with 30-day lookback period")
        return default_timestamps
    except json.JSONDecodeError as e:
        print(f" Corrupted timestamp file, recreating: {e}")
        # If file is corrupted, recreate it
        thirty_days_ago = int((time.time() - (30 * 24 * 60 * 60)) * 1000)
        default_timestamps = {
            "last_fetch_labeled": thirty_days_ago,
            "last_fetch_unlabeled": thirty_days_ago
        }
        with open(TIMESTAMP_FILE, 'w') as f:
            json.dump(default_timestamps, f, indent=2)
        return default_timestamps

def main():
    try:
        # Get access token from hubspot_token.json
        try:
            access_token = get_access_token_from_file(TOKEN_FILE)
        except Exception as e:
            print(f"Error reading access token from file: {e}")
            return

        fetcher = HubSpotLeadFetcher(access_token)
        
        # This will now create the file if it doesn't exist
        last_fetch_data = check_for_last_fetch()
        last_fetch_unlabeled = last_fetch_data.get("last_fetch_unlabeled")
        
        print(f" Fetching unlabeled leads since: {last_fetch_unlabeled}")
      
        unlabeled_filter_groups = [
            {
                "filters": [
                    {
                        "propertyName": "lifecyclestage",
                        "operator": "NEQ",  
                        "value": "customer"
                    },
                    {
                        "propertyName": "hs_lead_status",
                        "operator": "NEQ",  
                        "value": "QUALIFIED"
                    }
                ]
            }
        ]
        
        unlabled_response = fetcher.fetch_leads(last_fetch_unlabeled, unlabeled_filter_groups, "unlabeled")
        print("*******unlabled", unlabled_response)
        
        if unlabled_response == 401:
            print(" Access token expired, refreshing...")
            if fetcher.refresh_token(TOKEN_FILE):
                unlabled_response = fetcher.fetch_leads(last_fetch_unlabeled, unlabeled_filter_groups, "unlabeled")
            else:
                print(" Failed to refresh token")
                return
        
        if unlabled_response and unlabled_response != 401:
            # Process and save data using the adapter
            print(" Processing and saving unlabeled data...")
            adapter = HubSpotDataAdapter()
            saved_files = adapter.process_all_data(unlabled_response, type="unlabeled")
            
            print(f" Processing for UNLABELED DATA complete! Saved {len(saved_files)} files:")
            for file in saved_files:
                print(f"    {file}")
        else:
            print(" No unlabeled data retrieved or API error occurred")

    except Exception as e:
        print(f" Error in HubSpot fetch process: {e}")

if __name__ == "__main__":
    main()