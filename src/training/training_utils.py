import os
import json
import pandas as pd
from datetime import datetime


def get_latest_model_version(models_dir):
    """Get the latest model version from the models directory"""
    try:
        model_files = [f for f in os.listdir(models_dir) if f.startswith('model_V') and f.endswith('.pkl')]
        if not model_files:
            return None
        
        # Extract timestamps and find the latest
        latest_file = max(model_files, key=lambda x: os.path.getmtime(os.path.join(models_dir, x)))
        version = latest_file.replace('model_V', '').replace('.pkl', '')
        return version
    except Exception as e:
        print(f"Error getting latest model version: {e}")
        return None


def validate_dataset(dataset_path):
    """Validate that a dataset has the required columns and structure"""
    # Core training features (excluding lead_id as it's not used for training)
    required_columns = ['company_size', 'source', 'region', 'contact_attempts', 
                       'days_since_first_contact', 'job_title', 'has_company_website', 'converted']
    
    try:
        data = pd.read_csv(dataset_path)
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
        
        # Check for empty dataset
        if len(data) == 0:
            return False, "Dataset is empty"
        
        # Check target column values
        if 'converted' in data.columns:
            unique_targets = data['converted'].unique()
            if len(unique_targets) < 2:
                return False, f"Target column has insufficient unique values: {unique_targets}"
        
        # Check if lead_id exists (optional but recommended)
        has_lead_id = 'lead_id' in data.columns
        
        return True, f"Dataset valid: {len(data)} records, lead_id present: {has_lead_id}"
        
    except Exception as e:
        return False, f"Error validating dataset: {e}"


def log_training_event(event_type, details, metadata_dir):
    """Log training events to a centralized log"""
    try:
        log_file = os.path.join(metadata_dir, "training_log.jsonl")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    except Exception as e:
        print(f"Warning: Failed to log training event: {e}")


def compare_model_performance(old_version, new_version, models_dir, metadata_dir):
    """Compare performance between old and new model versions"""
  
    try:
        # Load metadata for both models if available
        old_metadata_path = os.path.join(metadata_dir, f"retrain_metadata_{old_version}.json")
        new_metadata_path = os.path.join(metadata_dir, f"retrain_metadata_{new_version}.json")
        
        comparison = {
            "old_version": old_version,
            "new_version": new_version,
            "comparison_date": datetime.now().isoformat(),
            "old_model_exists": os.path.exists(os.path.join(models_dir, f"model_V{old_version}.pkl")),
            "new_model_exists": os.path.exists(os.path.join(models_dir, f"model_V{new_version}.pkl")),
            "performance_metrics": {
                "accuracy_improvement": "TBD",
                "precision_improvement": "TBD", 
                "recall_improvement": "TBD"
            }
        }
        
        return comparison
        
    except Exception as e:
        print(f"Warning: Model comparison failed: {e}")
        return None


def get_training_summary(metadata_dir):
    """Get a summary of all training activities"""
    try:
        # Get all retrain metadata files
        retrain_files = [f for f in os.listdir(metadata_dir) if f.startswith('retrain_metadata_')]
        
        summary = {
            "total_retrains": len(retrain_files),
            "retrain_history": [],
            "summary_generated": datetime.now().isoformat()
        }
        
        for file in sorted(retrain_files):
            try:
                with open(os.path.join(metadata_dir, file), 'r') as f:
                    metadata = json.load(f)
                    
                    summary["retrain_history"].append({
                        "version": metadata.get("new_model_version"),
                        "date": metadata.get("retrain_date"),
                        "training_records": metadata.get("merge_metadata", {}).get("merge_statistics", {}).get("final_records", 0),
                        "fresh_records": metadata.get("merge_metadata", {}).get("merge_statistics", {}).get("fresh_records", 0)
                    })
            except Exception as e:
                print(f"Warning: Could not read {file}: {e}")
        
        return summary
        
    except Exception as e:
        print(f"Error generating training summary: {e}")
        return None
