
import os
import json
import glob
import re
from datetime import datetime

import pandas as pd

def load_predictions():
    try:
        predictions_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', 
            'data', 'predictions'
        )
        
        if not os.path.exists(predictions_dir):
            print(f"Predictions directory not found: {predictions_dir}")
            return None
        
        # Find all prediction files (pattern: lead_scores_*.csv)
        prediction_pattern = os.path.join(predictions_dir, 'lead_scores_*.csv')
        prediction_files = glob.glob(prediction_pattern)
        
        if not prediction_files:
            print(f"No prediction files found in: {predictions_dir}")
            return None
        
        # Get the latest file based on model timestamp in filename
        latest_file = get_latest_prediction_file(prediction_files)
        
        print(f"Loading latest predictions from: {os.path.basename(latest_file)}")
        
        # Read CSV with pandas
        df = pd.read_csv(latest_file)
        
        # Convert to JSON format (list of dictionaries)
        data = df.to_dict('records')
        
        # Add metadata about the file
        file_stats = os.stat(latest_file)
        model_info = extract_model_info_from_filename(latest_file)
        
        file_info = {
            'file_name': os.path.basename(latest_file),
            'file_size': file_stats.st_size,
            'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'total_predictions': len(data),
            'model_timestamp': model_info['model_timestamp'],
            'model_version': model_info['model_version'],
            'unix_timestamp': model_info['unix_timestamp']
        }
        
        return {
            'predictions': data,
            'metadata': file_info
        }
        
    except Exception as e:
        print(f"Error loading predictions: {e}")
        return None

def get_latest_prediction_file(prediction_files):
    """Get the latest prediction file based on model version timestamp in filename"""
    def extract_model_timestamp(filename):
        """Extract model timestamp from filename for comparison"""
        try:
            # Extract the model timestamp part: 20250720_211607
            pattern = r'lead_scores_\d+_(\d{8}_\d{6})\.csv'
            match = re.search(pattern, filename)
            
            if match:
                timestamp_str = match.group(1)  # "20250720_211607"
                return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            else:
                # Fallback to file modification time
                return datetime.fromtimestamp(os.path.getmtime(filename))
                
        except Exception as e:
            print(f"⚠️  Error parsing timestamp from {filename}: {e}")
            return datetime.fromtimestamp(os.path.getmtime(filename))
    
    return max(prediction_files, key=extract_model_timestamp)

def extract_model_info_from_filename(filename):
    """Extract detailed model information from filename"""
    try:
        # Pattern: lead_scores_1753049562162_20250720_211607.csv
        pattern = r'lead_scores_(\d+)_(\d{8}_\d{6})\.csv'
        match = re.search(pattern, os.path.basename(filename))
        
        if match:
            unix_timestamp = match.group(1)
            model_timestamp_str = match.group(2)
            
            model_datetime = datetime.strptime(model_timestamp_str, '%Y%m%d_%H%M%S')
            
            return {
                'unix_timestamp': int(unix_timestamp),
                'model_timestamp': model_datetime.isoformat(),
                'model_version': f"MODEL_V{model_timestamp_str}"
            }
        else:
            return {
                'unix_timestamp': None,
                'model_timestamp': None,
                'model_version': 'Unknown'
            }
            
    except Exception as e:
        print(f"Error extracting model info: {e}")
        return {
            'unix_timestamp': None,
            'model_timestamp': None,
            'model_version': 'Unknown'
        }

def calculate_prediction_stats(predictions):
    """Calculate summary statistics for predictions"""
    if not predictions:
        return {
            'total_predictions': 0,
            'positive_predictions': 0,
            'negative_predictions': 0,
            'high_probability_count': 0,
            'average_probability': 0,
            'conversion_rate': 0,
            'high_probability_percentage': 0
        }
    
    total = len(predictions)
    positive = sum(1 for p in predictions if p.get('prediction', 0) == 1)
    negative = total - positive
    high_prob = sum(1 for p in predictions if p.get('probability', 0) > 0.7)
    avg_prob = sum(p.get('probability', 0) for p in predictions) / total if total > 0 else 0
    
    return {
        'total_predictions': total,
        'positive_predictions': positive,
        'negative_predictions': negative,
        'high_probability_count': high_prob,
        'average_probability': round(avg_prob, 3),
        'conversion_rate': round((positive / total) * 100, 1) if total > 0 else 0,
        'high_probability_percentage': round((high_prob / total) * 100, 1) if total > 0 else 0
    }
