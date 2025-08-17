import os
import sys

# Add current directory to path for local imports
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

from hubSpot import HubSpotLeadFetcher
from hubSpot import get_access_token_from_file, check_for_last_fetch

# Add adapter directory to path
adapter_dir = os.path.join(current_dir, '..', 'adapter')
sys.path.append(adapter_dir)
from adapt_fetched_data import HubSpotDataAdapter


TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'hubspot_token.json')

def main():
    try:
        # Get access token from hubspot_token.json
        try:
            access_token = get_access_token_from_file(TOKEN_FILE)
        except Exception as e:
            print(f"Error reading access token from file: {e}")
            return

        fetcher = HubSpotLeadFetcher(access_token)
        time = check_for_last_fetch()
        
        time_labled = time['last_fetch_labeled']
        
        
      
        labeled_filter_groups = [
            {
                "filters": [
                    {
                        "propertyName": "lifecyclestage",
                        "operator": "EQ",
                        "value": "customer"
                    }
                ]
            },
            {
                "filters": [
                    {
                        "propertyName": "hs_lead_status",
                        "operator": "EQ",
                        "value": "UNQUALIFIED"
                    }
                ]
            }
        ]
        
        
        
        labled_response = fetcher.fetch_leads(time_labled ,labeled_filter_groups,"labeled")
        print("*******labeled",labled_response)
        if labled_response == 401:
            if fetcher.refresh_token(TOKEN_FILE):
                labled_response = fetcher.fetch_leads(time_labled ,labeled_filter_groups,"labeled")
            else:
                print(" Authentication failed - could not refresh token")
                return 0
        
        # Check if we got valid response data
        if labled_response == 401 or not labled_response:
            print(" No data fetched or authentication failed")
            return 0
        
        # Process and save data using the adapter
        print(" Processing and saving labeled data...")
        adapter = HubSpotDataAdapter()
        saved_files = adapter.process_all_data(labled_response, type="labeled")
        
        # Count total leads processed
        total_leads = 0
        if isinstance(labled_response, list):
            total_leads = len(labled_response)
        elif isinstance(labled_response, dict) and 'results' in labled_response:
            total_leads = len(labled_response['results'])
            
        print(f" Processing for LABELED DATA complete! Saved {len(saved_files)} files")
        print(f" Total labeled leads fetched: {total_leads}")
        
        return total_leads
            
    except Exception as e:
        print(f"Error in HubSpot fetch process: {e}")
        return 0


if __name__ == "__main__":
    result = main()
    print(f"Fetched {result} labeled leads")