from datetime import datetime
import os
import json
import joblib
import pandas as pd
#from baseLine_stats import baseLine_stats
from monitor.monitor import monitor_predictions, predict_with_mab_optimized, track_model_performance, choose_model_for_prediction
from fetch.fetch_unlabled_leads import main

TIMESTAMP_FETCH_FILE = os.path.join(os.path.dirname(__file__),'..','config','last_fetch_timestamp.json')
TIMESTAMP_TRAIN_FILE = os.path.join(os.path.dirname(__file__),'..','config','models_version.json')
BASELINE_STATS  = os.path.join(os.path.dirname(__file__),'..','metadata','baseLine_stats.json')
PREPROCESSOR_PATH = os.path.join(os.path.dirname(__file__),'..','models')


def get_last_timestamp_model():
    try:
        with open(TIMESTAMP_TRAIN_FILE,'r') as f:
            temp = json.load(f)
        if temp:
            timestamps = temp['timestamps'][-1]
            return timestamps
        else:
            print('No current version stored as timestamp')
            return None
    except ValueError as e:
        print(e)
        return None

def get_last_fetch_timestamp():
    try:
        with open(TIMESTAMP_FETCH_FILE,'r') as f:
            timestamp = json.load(f) 
        return timestamp
    except FileNotFoundError:
        print(" Last fetch timestamp file not found. This might be the first run.")
        return None
    except (json.JSONDecodeError, ValueError) as e:
        print(f" Error reading timestamp file: {e}")
        return None

def find_latest_unlabeled_file():
    """Find the most recent unlabeled leads file"""
    adapted_dir = os.path.join(os.path.dirname(__file__), "..", "data", "adapted")
    
    if not os.path.exists(adapted_dir):
        print(f" Adapted data directory not found: {adapted_dir}")
        return None, None
    
    unlabeled_files = [f for f in os.listdir(adapted_dir) if f.startswith('unlabeled_leads_') and f.endswith('.csv')]
    
    if not unlabeled_files:
        print(" No unlabeled data files found in adapted directory")
        print(" Run the fetch process first: python fetch/fetch_unlabled_leads.py")
        return None, None
    
    # Sort files and get the most recent one
    latest_file = sorted(unlabeled_files)[-1]
    
    # Extract timestamp from filename: unlabeled_leads_20250719_194228.csv
    unlabeled_temp = latest_file.replace('unlabeled_leads_', '').replace('.csv', '')
    
    print(f" Found latest unlabeled data file: {latest_file}")
    return latest_file, unlabeled_temp

def predict():
    # Fetch for recent leads 
    try:
        main()
        print(" LEAD FETCHED SUCCESSFULLY: Begin scoring attempt...")
    except Exception as e:
        print(f" Error fetching recent unlabeled leads: {e}")
        print(" Continuing with existing data if available...")
    
    # Handle first run scenario
    timestamp = get_last_fetch_timestamp()
    
    if timestamp is None:
        print(" First run detected or timestamp file missing...")
        print(" Looking for any available unlabeled data files...")
        
        filename, unlabeled_temp = find_latest_unlabeled_file()
        
        if filename is None:
            print(" No unlabeled data available for prediction")
            print(" Steps to resolve:")
            print("   1. Check your HubSpot token in config/hubspot_token.json")
            print("   2. Run: python fetch/fetch_unlabled_leads.py")
            print("   3. Then run: python predict.py")
            return []
        
        path = os.path.join(os.path.dirname(__file__), "..", "data", "adapted", filename)
        
    else:
        # Normal operation with existing timestamp
        unlabeled_temp = timestamp.get('last_fetch_unlabeled')
        
        if unlabeled_temp is None:
            print(" No unlabeled timestamp found in config file")
            filename, unlabeled_temp = find_latest_unlabeled_file()
            
            if filename is None:
                return []
            
            path = os.path.join(os.path.dirname(__file__), "..", "data", "adapted", filename)
        else:
            filename = f"unlabeled_leads_{unlabeled_temp}.csv"
            path = os.path.join(os.path.dirname(__file__), "..", "data", "adapted", filename)
    
    print(f" Using data file: {filename}")
    print(f" Full path: {path}")
    
    
    try:
        content = pd.read_csv(path)
        
        if content.empty:
            print(" The unlabeled leads file is empty - no new leads since last fetch")
            print(" This means no new leads were found in HubSpot since the last run")
            print(" This is normal behavior when there are no new leads to score")
            return []
        
        print(f" Loaded {len(content)} leads for prediction")
        
        # Extract lead information
        lead_ids = content['lead_id'].copy()
        lead_firstNames = content['firstname'].copy()
        lead_lastNames = content['lastname'].copy()
        lead_emails = content['email'].copy()
        
        # Prepare feature data
        data = content.drop(columns=['lead_id', 'firstname', 'lastname', 'email'])
        
    except FileNotFoundError:
        print(f" Unlabeled leads file not found: {path}")
        print(" Looking for alternative data files...")
        
        # Try to find any existing unlabeled file as fallback
        filename, unlabeled_temp = find_latest_unlabeled_file()
        
        if filename is None:
            print(" No unlabeled data files found. Steps to resolve:")
            print("   1. Check your HubSpot token in config/hubspot_token.json")
            print("   2. Run: python fetch/fetch_unlabled_leads.py")
            print("   3. Then run: python predict.py")
            return []
        
        # Try the fallback file
        fallback_path = os.path.join(os.path.dirname(__file__), "..", "data", "adapted", filename)
        try:
            content = pd.read_csv(fallback_path)
            if content.empty:
                print(" Fallback file is also empty - no leads to score")
                return []
            
            print(f" Using fallback file with {len(content)} leads")
            
            # Extract data from fallback file
            lead_ids = content['lead_id'].copy()
            lead_firstNames = content['firstname'].copy()
            lead_lastNames = content['lastname'].copy()
            lead_emails = content['email'].copy()
            data = content.drop(columns=['lead_id', 'firstname', 'lastname', 'email'])
            
        except Exception as fallback_error:
            print(f" Fallback file also failed: {fallback_error}")
            return []
            
    except KeyError as e:
        print(f" Missing expected columns in data file: {e}")
        print(f"Available columns: {list(content.columns) if 'content' in locals() else 'Could not read file'}")
        return []
    except Exception as e:
        print(f" Error loading data file: {e}")
        return []

    # OPTIMIZED MAB PREDICTION WITH MONITORING
    
    print(" STARTING MAB PREDICTION WITH MONITORING")
    print("=" * 50)
    
    # Get model selection from MAB system
    model_name = choose_model_for_prediction()
    print(f" MAB Selected Model: {model_name}")
    
    # Handle model selection result and extract timestamp
    if model_name == "default_model" or not model_name:
        # Fallback to the latest model
        temp = get_last_timestamp_model()
        print(f"**temp fallback: {temp}")
        model_version = f"model_V{temp}"
        print(f" Using fallback model: {model_version}")
    else:
        # Extract timestamp from real model version
        if model_name.startswith("model_V"):
            temp = model_name.replace("model_V", "")  # Gets "20250719_194228"
            model_version = model_name
            print(f" Using MAB selected model: {model_version}")
        else:
            # Another fallback if format is unexpected
            temp = get_last_timestamp_model()
            model_version = f"model_V{temp}"
            print(f" Unexpected model format, using fallback: {model_version}")
    
    # Load the appropriate preprocessor
    preprocessor_path = os.path.join(PREPROCESSOR_PATH, f'preprocessor_{temp}.pkl')
    try:
        preprocessor = joblib.load(preprocessor_path)
        print(f" Preprocessor loaded: preprocessor_{temp}.pkl")
    except Exception as e:
        print(f' ERROR while loading preprocessor: {e}')
        return []
    
    # Preprocess the data
    try:
        to_predict = preprocessor.transform(data)
        print(f" Data preprocessed: {to_predict.shape}")
    except Exception as e:
        print(f" Error preprocessing data: {e}")
        return []
    
    # Convert to DataFrame with feature names (for better monitoring)
    try:
        feature_names = preprocessor.get_feature_names_out()
        to_predict_df = pd.DataFrame(to_predict, columns=feature_names)
        print(f" Feature names extracted: {len(feature_names)} features")
    except Exception:
        # If get_feature_names_out fails, use numpy array
        to_predict_df = pd.DataFrame(to_predict)
        print(f" Using default feature names")
    
    # MAB PREDICTION WITH MONITORING
    
    try:
        # Use the optimized MAB prediction system
        predictions, selected_model, monitoring_result = predict_with_mab_optimized(to_predict_df)
        
        if predictions is None:
            print(" MAB prediction failed")
            return []
        
        print(f" MAB Prediction completed!")
        print(f"   Model Used: {selected_model}")
        print(f"   Predictions: {len(predictions)}")
        print(f"   Avg Score: {predictions.mean():.3f}")
        print(f"   Score Range: [{predictions.min():.3f}, {predictions.max():.3f}]")
        
        # Display monitoring results
        if monitoring_result:
            print(f"\n MONITORING RESULTS:")
            print(f"   Status: {monitoring_result['status']}")
            print(f"   Algorithm: {monitoring_result['bandit_status']['algorithm']}")
            print(f"   Winner: {monitoring_result['bandit_status']['winner']}")
            print(f"   Active Models: {monitoring_result['bandit_status']['active_models']}")
            
    except Exception as e:
        print(f" Error in MAB prediction: {e}")
        # Fallback to direct model prediction
        print(" Falling back to direct prediction...")
        
        try:
            # Load model directly
            model_path = os.path.join(os.path.dirname(__file__), '..', 'models', f'{model_version}.pkl')
            model = joblib.load(model_path)
            predictions = model.predict_proba(to_predict)[:, 1]
            selected_model = model_version
            
            # Manual tracking for fallback
            track_model_performance(selected_model, len(predictions))
            
            print(f" Fallback prediction completed with {selected_model}")
            
        except Exception as fallback_error:
            print(f" Fallback prediction also failed: {fallback_error}")
            return []
    
    # SAVE PREDICTIONS WITH MAB INFO
    
    try:
        # Create results DataFrame
        results_df = pd.DataFrame({
            'lead_id': lead_ids,
            'firstname': lead_firstNames,
            'lastname': lead_lastNames,
            'email': lead_emails,
            'lead_score': predictions,
            'model_used': selected_model,
            'prediction_timestamp': datetime.now().isoformat(),
            'mab_selection': True if model_name != "default_model" else False
        })
        
        # Save predictions
        predictions_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'predictions')
        os.makedirs(predictions_dir, exist_ok=True)
        
        prediction_filename = f'lead_scores_{unlabeled_temp}_{selected_model.replace("model_V", "")}.csv'
        prediction_path = os.path.join(predictions_dir, prediction_filename)
        
        results_df.to_csv(prediction_path, index=False)
        print(f" Predictions saved: {prediction_filename}")
        
        # Summary statistics
        high_score_leads = (predictions > 0.7).sum()
        medium_score_leads = ((predictions > 0.4) & (predictions <= 0.7)).sum()
        low_score_leads = (predictions <= 0.4).sum()
        
        print(f"\n PREDICTION SUMMARY:")
        print(f"   Total Leads: {len(predictions)}")
        print(f"   High Score (>70%): {high_score_leads}")
        print(f"   Medium Score (40-70%): {medium_score_leads}")
        print(f"   Low Score (≤40%): {low_score_leads}")
        print(f"   Model Used: {selected_model}")
        print(f"   MAB Selection: {'Yes' if model_name != 'default_model' else 'No (Fallback)'}")
        
        print("=" * 50)
        print(" PREDICTION WITH MAB MONITORING COMPLETED!")
        
        return results_df.to_dict('records')
        
    except Exception as e:
        print(f" Error saving predictions: {e}")
        return []

if __name__ == "__main__":
    predict()