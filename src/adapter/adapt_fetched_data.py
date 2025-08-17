import os
import json
import pandas as pd
import time  # ← ADDED MISSING IMPORT
from datetime import datetime
from typing import Dict, List, Optional


class HubSpotDataAdapter:
    """Adapter class to transform HubSpot fetched data into CSV format."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'adapted')
        self.last_fetch_tmp = os.path.join(os.path.dirname(__file__), '..', '..', 'config','last_fetch_timestamp.json')
        # Create directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
    
    def extract_lead_properties(self, properties: Dict) -> Dict:
        """Extract and transform HubSpot properties to standardized format"""
        
        # HubSpot property mappings (actual HubSpot field names)
        hubspot_mappings = {
            'lead_id': ['id', 'hs_object_id'],  # HubSpot record ID
            'firstname': ['firstname', 'first_name'],
            'lastname': ['lastname', 'last_name'],
            'email': ['email'],
            'company_size': ['num_employees', 'company_size', 'numberofemployees'],
            'source': ['hs_analytics_source', 'source', 'lead_source'],
            'region': ['country', 'state', 'region'],
            'contact_attempts': ['num_contacted_notes', 'contact_attempts', 'num_times_contacted'],
            'days_since_first_contact': ['createdate', 'first_contact_date', 'days_since_first_contact'],
            'job_title': ['jobtitle', 'job_title'],
            'has_company_website': ['website', 'company_website', 'has_company_website']
        }
        
        extracted = {}
        
        for standard_field, hubspot_fields in hubspot_mappings.items():
            value = None
            
            # Try each possible HubSpot field name
            for field in hubspot_fields:
                if field in properties and properties[field]:
                    value = properties[field]
                    break
            
            # Apply data type conversions
            if standard_field == 'lead_id':
                extracted[standard_field] = str(value) if value else ''
            elif standard_field in ['contact_attempts']:
                extracted[standard_field] = self.safe_int_conversion(value)
            elif standard_field in ['days_since_first_contact']:
                extracted[standard_field] = self.calculate_days_since_contact(value)
            elif standard_field in ['has_company_website']:
                extracted[standard_field] = self.safe_bool_conversion(value)
            else:
                extracted[standard_field] = str(value) if value else ''
        
        return extracted
    
    def safe_int_conversion(self, value) -> int:
        """Safely convert value to integer"""
        if value is None or value == '':
            return 0
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return 0
    
    def safe_bool_conversion(self, value) -> int:
        """Convert value to boolean (1/0 for CSV compatibility)"""
        if value is None or value == '':
            return 0
        
        # Handle different boolean representations
        if isinstance(value, bool):
            return 1 if value else 0
        
        str_value = str(value).lower()
        if str_value in ['true', '1', 'yes', 'on']:
            return 1
        elif str_value in ['false', '0', 'no', 'off']:
            return 0
        else:
            # If it's a URL or any non-empty string, consider it as having a website
            return 1 if str_value.strip() else 0
    
    def calculate_days_since_contact(self, value) -> int:
        """Calculate days since first contact"""
        if value is None or value == '':
            return 0
        
        try:
            # If it's already a number of days
            if isinstance(value, (int, float)):
                return int(value)
            
            # If it's a timestamp (milliseconds)
            if str(value).isdigit() and len(str(value)) == 13:
                contact_date = datetime.fromtimestamp(int(value) / 1000)
                days_diff = (datetime.now() - contact_date).days
                return max(0, days_diff)
            
            # If it's a date string
            if isinstance(value, str):
                try:
                    contact_date = datetime.strptime(value, '%Y-%m-%d')
                    days_diff = (datetime.now() - contact_date).days
                    return max(0, days_diff)
                except ValueError:
                    pass
            
            return 0
        except (ValueError, TypeError):
            return 0
    
    def transform_labeled_data(self, labeled_data: Dict) -> pd.DataFrame:
        """Transform labeled data from HubSpot API response to DataFrame."""
        
        if not labeled_data or 'results' not in labeled_data:
            print(" No labeled data to transform")
            return pd.DataFrame(columns=[
                'lead_id','firstname','lastname','email','company_size','source','region',
                'contact_attempts','days_since_first_contact','job_title','has_company_website','converted'
            ])
        
        contacts_list = []
        
        for contact in labeled_data['results']:
            properties = contact.get('properties', {})
            
            # Extract standardized properties
            contact_data = self.extract_lead_properties(properties)
            
            # Determine converted value based on lifecyclestage and hs_lead_status
            lifecyclestage = properties.get('lifecyclestage', '')
            hs_lead_status = properties.get('hs_lead_status', '')
            
            # Enhanced conversion logic
            converted = 0  # Default value
            
            if lifecyclestage in ["customer", "opportunity", "qualified-to-buy"]:
                converted = 1
            elif hs_lead_status in ["CONNECTED", "QUALIFIED", "CONVERTED"]:
                converted = 1
            elif hs_lead_status in ["UNQUALIFIED", "DISQUALIFIED", "INVALID"]:
                converted = 0
            
            contact_data['converted'] = converted
            contacts_list.append(contact_data)
        
        df = pd.DataFrame(contacts_list)
        print(f" Transformed {len(df)} labeled contacts")
        return df
    
    def transform_unlabeled_data(self, unlabeled_data: Dict) -> pd.DataFrame:
        """Transform unlabeled data from HubSpot API response to DataFrame."""
        
        if not unlabeled_data or 'results' not in unlabeled_data:
            print(" No unlabeled data to transform")
            return pd.DataFrame(columns=[
                'lead_id', 'firstname', 'lastname', 'email', 'company_size',
                'source', 'region', 'contact_attempts', 'days_since_first_contact',
                'job_title', 'has_company_website'
            ])
        
        contacts_list = []
        
        for contact in unlabeled_data['results']:
            properties = contact.get('properties', {})
            
            # Extract standardized properties
            contact_data = self.extract_lead_properties(properties)
            contacts_list.append(contact_data)
        
        df = pd.DataFrame(contacts_list)
        print(f" Transformed {len(df)} unlabeled contacts")
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> Optional[str]:
        """Save DataFrame to CSV with proper timestamp handling"""
        
        # Get timestamp from the last fetch file
        try:
            with open(self.last_fetch_tmp, 'r') as f:
                timestamp_data = json.load(f)
                
            if filename == 'labeled_leads':
                timestamp = timestamp_data.get('last_fetch_labeled')
            elif filename == 'unlabeled_leads':
                timestamp = timestamp_data.get('last_fetch_unlabeled')
            else:
                timestamp = None
            
            # Use existing timestamp format (milliseconds) for consistency
            if timestamp is None:
                timestamp = int(time.time() * 1000)  # ← FIXED: Use milliseconds
                
        except (ValueError, FileNotFoundError) as e:
            print(f"Error loading last fetch timestamp: {e}")
            # Fallback to current timestamp in milliseconds
            timestamp = int(time.time() * 1000)  # ← FIXED: Consistent format
            
        filename_with_timestamp = f"{filename}_{timestamp}.csv"
        filepath = os.path.join(self.data_dir, filename_with_timestamp)
        
        try:
            # ALWAYS create the file, even if DataFrame is empty
            if df.empty:
                print(f" No new {filename} found, creating empty file for consistency")
                # Create empty DataFrame with expected columns
                if filename == 'labeled_leads':
                    empty_columns = [
                        'lead_id','firstname','lastname','email','company_size','source','region',
                        'contact_attempts','days_since_first_contact','job_title','has_company_website','converted'
                    ]
                else:  # unlabeled_leads
                    empty_columns = [
                        'lead_id', 'firstname', 'lastname', 'email', 'company_size',
                        'source', 'region', 'contact_attempts', 'days_since_first_contact',
                        'job_title', 'has_company_website'
                    ]
                
                df = pd.DataFrame(columns=empty_columns)
            
            df.to_csv(filepath, index=False)
            print(f" Saved {len(df)} records to: {filepath}")
            return filepath

        except Exception as e:
            print(f" Error saving CSV: {e}")
            return None

    def process_all_data(self, data, type) -> List[str]:
        """Process and save data based on type"""
        
        saved_files = []
        
        # Transform data
        if type == "labeled":
            labeled_df = self.transform_labeled_data(data)
            # Always save, even if empty
            filepath = self.save_to_csv(labeled_df, "labeled_leads")
            if filepath:
                saved_files.append(filepath)
        elif type == "unlabeled":
            unlabeled_df = self.transform_unlabeled_data(data)
            # Always save, even if empty
            filepath = self.save_to_csv(unlabeled_df, "unlabeled_leads")
            if filepath:
                saved_files.append(filepath)
        
        return saved_files