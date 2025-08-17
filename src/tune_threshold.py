import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import json
from baseLine_stats import baseLine_stats

CONFIG_LOCATION = os.path.join(os.path.dirname(__file__),'..','config')
MODEL_LOCATION =os.path.join(os.path.dirname(__file__),'..','models')
BASELINE_LOCATION = os.path.join(os.path.dirname(__file__),'..','metadata','baseLine_stats.json')

def tune_threshold(temp, test_path):
    # Load data
    try:
        df = pd.read_csv(test_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load test data from {test_path}: {e}")
    X_test = df.drop('converted', axis=1)
    y_test = df['converted']
   
    # Load model
    model_name = f"model_v{temp}.pkl"
    model_path = os.path.join(MODEL_LOCATION, model_name)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    model = joblib.load(model_path)
    print(f"Loaded model from {model_path}")

    # Predict probabilities
    y_probs = model.predict_proba(X_test)[:, 1]

    # Range of thresholds to test
    thresholds = np.arange(0.1, 0.91, 0.05)

    # Store best result
    best_threshold = 0.5
    best_f1 = 0
    best_results = {}
    threshold_details = {}

    print(f"{'Threshold':<10} {'Precision':<10} {'Recall':<10} {'F1-score':<10} ")
    print("-" * 50)

    for threshold in thresholds:
        y_pred = (y_probs >= threshold).astype(int)

        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0) #add zero_division to avoid warnings when precision is undefiened
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        threshold_details[float(threshold)]={
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                    'Confusion_matrix':{
                        'false_negatives': int(fn),
                        'false_positives': int(fp),
                        'true_positives': int(tp),
                        'true_negatives': int(tn)
                    },
        }
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
            best_results = {
                'threshold': threshold,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1)
            
            }
    #save threshold  to use it for prediction
    threshold_location = os.path.join(CONFIG_LOCATION, "threshold.json")
    # Load existing thresholds or create new list
    try:
        with open(threshold_location, "r") as f:
            threshold_data = json.load(f)
            if not isinstance(threshold_data, list):
                threshold_data = []
    except (FileNotFoundError, json.JSONDecodeError):
        threshold_data = []
    
    # Append new threshold data
    threshold_data.append({
        "model_version": temp,
        "best_threshold": float(best_threshold)
    })
    
    # Save updated threshold data
    with open(threshold_location, "w") as f:
        json.dump(threshold_data, f, indent=4)

    #save the timestamp for production :predict
    production_threshold = os.path.join(CONFIG_LOCATION, 'production_threshold.json')
    with open(production_threshold,'w') as f:
        json.dump(temp ,f)

    # Update the model_tracking dictionary creation:

    model_tracking = {
        'model_path': f'model_v{temp}',
        'preprecessor_path': f'preprocessor_v{temp}',  # Fixed typo in 'preprocessor'
        'threshold_tune': {
            'details': threshold_details,
            'best_threshold_based_on_F1':{
                'threshold': float(best_results['threshold']),
                'precision': float(best_results['precision']),
                'recall': float(best_results['recall']),
                'f1': float(best_results['f1'])
            }
            
        }
    }

    #save log for the model
    os.makedirs("metadata", exist_ok=True)

    # Check if file exists and read existing data
    try:
        with open("metadata/model_track.json", "r") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]  # Convert to list if it's not already
            except json.JSONDecodeError:
                # File exists but not valid JSON or empty
                existing_data = []
    except FileNotFoundError:
        # File doesn't exist yet
        existing_data = []

    # Append new tracking data
    existing_data.append(model_tracking)

    # Write back the complete data
    with open("metadata/model_track.json", "w") as f:
        json.dump(existing_data, f, indent=4)
        
    print("\n✅ Best Threshold Based on F1:")
    for key, value in best_results.items():
        print(f"{key}: {value:.2f}")
        
    #return y_probs


def save_baseline_stats(baseline_stats):
    with open(BASELINE_LOCATION,"a") as f:
        json.dump(baseline_stats,f)

