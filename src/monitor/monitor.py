import os
import json
import numpy as np
import pandas as pd
import time
import random
import math
from datetime import datetime

# Configuration for MAB tracking only
MONITORING_LOG = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'monitoring_log.jsonl')

def baseLine_stats(probabilities):
    """Calculate basic statistics for probability distribution (for MAB tracking only)"""
    return {
        'mean': np.mean(probabilities),
        'median': np.median(probabilities),
        'std': np.std(probabilities),
        'count': len(probabilities),
        'percentiles': {
            'p10': np.percentile(probabilities, 10),
            'p25': np.percentile(probabilities, 25),
            'p75': np.percentile(probabilities, 75),
            'p90': np.percentile(probabilities, 90)
        }
    }

def save_monitoring_stats(current_stats, batch_info):
    """Save monitoring stats for MAB tracking (no alerts)"""
    monitoring_entry = {
        'timestamp': datetime.now().isoformat(),
        'model_version': batch_info['model_version'],
        'batch_size': batch_info['batch_size'],
        'prediction_file': batch_info['prediction_file'],
        'stats': current_stats
    }
    
    # Ensure monitoring directory exists
    os.makedirs(os.path.dirname(MONITORING_LOG), exist_ok=True)
    
    # Append to monitoring log
    with open(MONITORING_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(monitoring_entry) + '\n')
    
    print(f" Monitoring stats saved for model: {batch_info['model_version']}")
    
    # No alerts - just return empty list
    return []

def get_recent_monitoring_stats(model_version, limit=10):
    """Get recent monitoring stats for a specific model version"""
    try:
        recent_stats = []
        
        with open(MONITORING_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry['model_version'] == model_version:
                    recent_stats.append(entry)
        
        # Return most recent entries
        return recent_stats[-limit:]
        
    except FileNotFoundError:
        print("No monitoring log found")
        return []
    except Exception as e:
        print(f"Error reading monitoring log: {e}")
        return []

def generate_monitoring_report(model_version):
    """Generate a basic monitoring report (MAB focused)"""
    try:
        recent_stats = get_recent_monitoring_stats(model_version)
        
        if not recent_stats:
            print(f"No monitoring data found for model: {model_version}")
            return
        
        print(f"\n MONITORING REPORT - Model: {model_version}")
        print("=" * 60)
        
        # Recent batches summary
        print(f"Recent Batches: {len(recent_stats)}")
        print(f"Total Predictions: {sum(s['batch_size'] for s in recent_stats)}")
        print(f"Date Range: {recent_stats[0]['timestamp'][:10]} to {recent_stats[-1]['timestamp'][:10]}")
        
        # Statistics trends
        means = [s['stats']['mean'] for s in recent_stats]
        stds = [s['stats']['std'] for s in recent_stats]
        
        print(f"\nProbability Trends:")
        print(f"Mean Range: {min(means):.3f} - {max(means):.3f}")
        print(f"Std Range: {min(stds):.3f} - {max(stds):.3f}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"Error generating monitoring report: {e}")

def monitor_predictions(probabilities, batch_info):
    """MAB-focused monitoring function (no drift alerts)"""
    try:
        # Calculate basic stats for tracking
        current_stats = baseLine_stats(probabilities)
        
        # Save stats for MAB tracking (no alerts)
        save_monitoring_stats(current_stats, batch_info)
        
        # Track model performance for MAB
        model_performance = track_model_performance(
            batch_info['model_version'], 
            batch_info['batch_size']
        )
        
        # Get current traffic allocation
        traffic_allocation = get_traffic_allocation()
        
        # Check memory usage and optimize if needed
        manage_model_memory()
        
        # Return MAB-focused results
        return {
            'stats': current_stats,
            'alerts': [],  # No alerts in MAB-only mode
            'status': 'STABLE',  # Always stable - no drift detection
            'model_performance': model_performance,
            'traffic_allocation': traffic_allocation,
            'bandit_status': {
                'active_models': len([k for k in traffic_allocation.keys() if k not in ['reason', 'winner', 'algorithm']]),
                'allocation_reason': traffic_allocation.get('reason', 'unknown'),
                'winner': traffic_allocation.get('winner', None),
                'algorithm': traffic_allocation.get('algorithm', 'thompson_sampling')
            }
        }
        
    except Exception as e:
        print(f"Error in MAB monitoring: {e}")
        return None

# OPTIMIZED MULTI-ARMED BANDIT IMPLEMENTATION

class OptimizedMABPredictor:
    """Optimized Multi-Armed Bandit with pre-loaded models and smart memory management"""
    
    def __init__(self):
        self.models = {}
        self.model_metadata = {}
        self.performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
        self.last_memory_check = time.time()
        
        # Initialize directories
        os.makedirs(os.path.dirname(self.performance_file), exist_ok=True)
        
        print(" Optimized MAB Predictor initialized")
    
    def load_model_if_needed(self, model_version):
        """Lazy loading of models with memory optimization"""
        if model_version not in self.models:
            try:
                import joblib
                
                # Construct model path
                model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', f'{model_version}.pkl')
                
                if os.path.exists(model_path):
                    print(f" Loading model: {model_version}")
                    start_time = time.time()
                    
                    self.models[model_version] = joblib.load(model_path)
                    load_time = time.time() - start_time
                    
                    self.model_metadata[model_version] = {
                        'load_time': load_time,
                        'last_used': time.time(),
                        'prediction_count': 0
                    }
                    
                    print(f" Loaded {model_version} in {load_time:.2f}s")
                    return True
                else:
                    print(f" Model file not found: {model_path}")
                    return False
            except Exception as e:
                print(f" Failed to load {model_version}: {e}")
                return False
        else:
            # Update last used time
            self.model_metadata[model_version]['last_used'] = time.time()
            return True
    
    def predict_batch_optimized(self, batch_data, model_version):
        """Optimized prediction for a specific model"""
        
        # Load model if needed
        if not self.load_model_if_needed(model_version):
            return None
        
        start_time = time.time()
        
        try:
            # Get model and predict
            model = self.models[model_version]
            predictions = model.predict_proba(batch_data)[:, 1]
            
            # Update metadata
            prediction_time = time.time() - start_time
            self.model_metadata[model_version]['prediction_count'] += len(predictions)
            
            print(f" {model_version}: {len(predictions)} predictions in {prediction_time*1000:.1f}ms")
            
            return predictions, prediction_time
            
        except Exception as e:
            print(f" Prediction failed for {model_version}: {e}")
            return None, 0
    
    def unload_unused_models(self, keep_recent=3):
        """Unload models that haven't been used recently"""
        if len(self.models) <= keep_recent:
            return
        
        # Sort by last used time
        models_by_usage = sorted(
            self.model_metadata.items(),
            key=lambda x: x[1]['last_used'],
            reverse=True
        )
        
        # Keep only recent models
        models_to_keep = [item[0] for item in models_by_usage[:keep_recent]]
        models_to_remove = [model for model in self.models.keys() if model not in models_to_keep]
        
        for model_version in models_to_remove:
            print(f" Unloading unused model: {model_version}")
            del self.models[model_version]
            del self.model_metadata[model_version]
    
    def get_memory_usage(self):
        """Get current memory usage (optional - works without psutil)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024**3)  # GB
        except ImportError:
            # psutil not available - return 0 (memory monitoring disabled)
            return 0
        except Exception:
            return 0

# Global optimized MAB predictor
mab_predictor = OptimizedMABPredictor()

def get_latest_model_from_config():
    """Get the latest model from models_version.json"""
    try:
        models_version_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'models_version.json')
        with open(models_version_file, 'r') as f:
            config = json.load(f)
        
        if 'timestamps' in config and config['timestamps']:
            latest_timestamp = config['timestamps'][-1]  # Get the most recent timestamp
            return f"model_V{latest_timestamp}"
        else:
            print(" No timestamps found in models_version.json")
            return None
    except FileNotFoundError:
        print(" models_version.json not found")
        return None
    except Exception as e:
        print(f" Error reading models_version.json: {e}")
        return None

def track_model_performance(model_version, num_predictions):
    """Enhanced model performance tracking with memory optimization"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    os.makedirs(os.path.dirname(performance_file), exist_ok=True)
    
    # Load existing performance data
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
    except FileNotFoundError:
        performance_data = {}
    
    # Initialize model if not exists
    if model_version not in performance_data:
        performance_data[model_version] = {
            'total_predictions': 0,
            'total_conversions': 0,
            'conversion_rate': 0.0,
            'first_seen': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'status': 'active',
            'confidence_interval': {'lower': 0, 'upper': 0}
        }
    
    # Update predictions count
    performance_data[model_version]['total_predictions'] += num_predictions
    performance_data[model_version]['last_updated'] = datetime.now().isoformat()
    
    # Calculate confidence interval
    performance_data[model_version]['confidence_interval'] = calculate_confidence_interval(performance_data[model_version])
    
    # Save back to file
    with open(performance_file, 'w') as f:
        json.dump(performance_data, f, indent=2)
    
    print(f" Tracked {num_predictions} predictions for {model_version}")
    return performance_data[model_version]

def calculate_confidence_interval(model_data, confidence_level=0.95):
    """Calculate confidence interval for conversion rate"""
    
    n = model_data['total_predictions']
    p = model_data['conversion_rate'] / 100  # Convert to proportion
    
    if n == 0:
        return {'lower': 0, 'upper': 0}
    
    # Calculate standard error
    se = math.sqrt((p * (1 - p)) / n)
    
    # Z-score for 95% confidence
    z = 1.96 if confidence_level == 0.95 else 1.645
    
    # Calculate interval
    margin_error = z * se
    lower = max(0, (p - margin_error) * 100)
    upper = min(100, (p + margin_error) * 100)
    
    return {'lower': lower, 'upper': upper}

def get_active_models():
    """Get list of active models with sufficient data"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
    except FileNotFoundError:
        return []
    
    # Filter active models - reduced minimum for real usage
    active_models = []
    min_predictions = 10  # Reduced minimum for actual usage
    
    for model_version, data in performance_data.items():
        if (data.get('status', 'active') == 'active' and 
            data['total_predictions'] >= min_predictions):
            active_models.append({
                'model_version': model_version,
                'conversion_rate': data['conversion_rate'],
                'total_predictions': data['total_predictions'],
                'total_conversions': data['total_conversions'],
                'confidence_interval': data.get('confidence_interval', {'lower': 0, 'upper': 0}),
                'last_updated': data['last_updated']
            })
    
    # If no models meet minimum, include all active models with any data
    if not active_models:
        for model_version, data in performance_data.items():
            if data.get('status', 'active') == 'active':
                active_models.append({
                    'model_version': model_version,
                    'conversion_rate': data['conversion_rate'],
                    'total_predictions': data['total_predictions'],
                    'total_conversions': data['total_conversions'],
                    'confidence_interval': data.get('confidence_interval', {'lower': 0, 'upper': 0}),
                    'last_updated': data['last_updated']
                })
                print(f"📊 Including model {model_version} with {data['total_predictions']} predictions")
    
    # Sort by conversion rate (descending)
    active_models.sort(key=lambda x: x['conversion_rate'], reverse=True)
    return active_models

def get_traffic_allocation():
    """Enhanced traffic allocation using Thompson Sampling for multiple models"""
    
    active_models = get_active_models()
    
    if not active_models:
        # Instead of returning default_model, return empty dict to trigger fallback
        return {'reason': 'no_active_models'}
    
    if len(active_models) == 1:
        return {
            active_models[0]['model_version']: 1.0, 
            'reason': 'single_active_model',
            'winner': active_models[0]['model_version'],
            'algorithm': 'single_model'
        }
    
    print(f" Evaluating {len(active_models)} active models:")
    for model in active_models:
        ci = model['confidence_interval']
        print(f"   {model['model_version']}: {model['conversion_rate']:.1f}% "
              f"({model['total_conversions']}/{model['total_predictions']}) "
              f"CI: [{ci['lower']:.1f}%, {ci['upper']:.1f}%]")
    
    # Use Thompson Sampling for optimal allocation
    allocation = thompson_sampling_allocation(active_models)
    
    print(f" Traffic Allocation (Thompson Sampling):")
    for model_version, weight in allocation.items():
        if model_version not in ['reason', 'winner', 'algorithm', 'total_models']:
            print(f"   {model_version}: {weight:.1%}")
    
    return allocation

def thompson_sampling_allocation(active_models):
    """Optimized Thompson Sampling for multiple models"""
    
    # Number of samples for Thompson Sampling
    num_samples = 5000  # Reduced for better performance
    model_wins = {model['model_version']: 0 for model in active_models}
    
    for _ in range(num_samples):
        sampled_rates = {}
        
        for model in active_models:
            # Beta distribution parameters
            successes = model['total_conversions']
            failures = model['total_predictions'] - model['total_conversions']
            
            # Add prior to avoid issues with zero data
            alpha = successes + 1
            beta = failures + 1
            
            # Sample from Beta distribution
            sampled_rate = random.betavariate(alpha, beta)
            sampled_rates[model['model_version']] = sampled_rate
        
        # Find winner for this sample
        winner = max(sampled_rates, key=sampled_rates.get)
        model_wins[winner] += 1
    
    # Convert wins to allocation percentages
    allocation = {}
    best_model = max(model_wins, key=model_wins.get)
    
    for model_version, wins in model_wins.items():
        allocation[model_version] = wins / num_samples
    
    # Add metadata
    allocation['reason'] = 'thompson_sampling'
    allocation['algorithm'] = 'optimized_thompson_sampling'
    allocation['winner'] = best_model
    allocation['total_models'] = len(active_models)
    
    return allocation

def choose_model_for_prediction():
    """Optimized model selection with smart fallback to real models"""
    
    allocation = get_traffic_allocation()
    model_weights = {k: v for k, v in allocation.items() 
                    if k not in ['reason', 'winner', 'algorithm', 'total_models']}
    
    # If no active models in MAB system, fallback to latest model from config
    if not model_weights:
        latest_model = get_latest_model_from_config()
        if latest_model:
            print(f" No active MAB models, using latest model from config: {latest_model}")
            return latest_model
        else:
            print(" No models available - neither in MAB system nor in config")
            return None
    
    if len(model_weights) == 1:
        selected_model = list(model_weights.keys())[0]
        
        # Check if it's the "default_model" placeholder
        if selected_model == "default_model":
            latest_model = get_latest_model_from_config()
            if latest_model:
                print(f" Replacing default_model with latest actual model: {latest_model}")
                return latest_model
            else:
                print(" default_model detected but no actual models found")
                return None
        else:
            print(f" Only one active model: {selected_model}")
            return selected_model
    
    # Optimized weighted random selection
    rand_val = random.random()
    cumulative = 0.0
    
    print(f" Random value: {rand_val:.3f}")
    print(f" Active models: {len(model_weights)}")
    
    for model, weight in model_weights.items():
        cumulative += weight
        if rand_val <= cumulative:
            print(f" Selected: {model} (weight: {weight:.1%})")
            return model
    
    # Fallback to winner
    winner = allocation.get('winner')
    if winner and winner in model_weights and winner != "default_model":
        print(f" Fallback to winner: {winner}")
        return winner
    
    # Final fallback to latest model from config
    latest_model = get_latest_model_from_config()
    if latest_model:
        print(f" Final fallback to latest model from config: {latest_model}")
        return latest_model
    
    print(" No valid models found")
    return None

def predict_with_mab_optimized(batch_data):
    """Main optimized MAB prediction function with improved error handling"""
    global mab_predictor
    
    start_time = time.time()
    
    # Choose optimal model
    selected_model = choose_model_for_prediction()
    
    if selected_model is None:
        print(" No valid model selected, cannot proceed with prediction")
        return None, None, None
    
    print(f" Selected model for prediction: {selected_model}")
    
    # Predict with selected model
    result = mab_predictor.predict_batch_optimized(batch_data, selected_model)
    
    if result is None:
        print(f" Prediction failed with {selected_model}")
        return None, None, None
    
    # Unpack the result safely
    if isinstance(result, tuple) and len(result) == 2:
        predictions, prediction_time = result
    else:
        print(f" Unexpected prediction result format: {result}")
        return None, None, None
    
    if predictions is None:
        print(f" Prediction returned None for {selected_model}")
        return None, None, None
    
    total_time = time.time() - start_time
    
    # Create enhanced batch info
    batch_info = {
        'model_version': selected_model,
        'batch_size': len(predictions),
        'prediction_file': f'mab_{selected_model}_predictions.csv',
        'timestamp': datetime.now().isoformat(),
        'prediction_time_ms': prediction_time * 1000,
        'total_time_ms': total_time * 1000,
        'mab_type': 'optimized_thompson_sampling'
    }
    
    # Monitor with enhanced tracking
    monitoring_result = monitor_predictions(predictions, batch_info)
    
    # Check memory usage periodically
    if time.time() - mab_predictor.last_memory_check > 300:  # Every 5 minutes
        manage_model_memory()
        mab_predictor.last_memory_check = time.time()
    
    return predictions, selected_model, monitoring_result

def update_conversions(lead_id, model_version):
    """Enhanced conversion tracking with automatic reallocation"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
    except FileNotFoundError:
        print(" No performance data found")
        return
    
    if model_version in performance_data:
        performance_data[model_version]['total_conversions'] += 1
        
        # Recalculate conversion rate
        total_pred = performance_data[model_version]['total_predictions']
        total_conv = performance_data[model_version]['total_conversions']
        performance_data[model_version]['conversion_rate'] = (total_conv / total_pred) * 100
        performance_data[model_version]['last_updated'] = datetime.now().isoformat()
        
        # Update confidence interval
        performance_data[model_version]['confidence_interval'] = calculate_confidence_interval(performance_data[model_version])
        
        # Save updated data
        with open(performance_file, 'w') as f:
            json.dump(performance_data, f, indent=2)
        
        print(f" Conversion tracked for {model_version}: {total_conv}/{total_pred} = {performance_data[model_version]['conversion_rate']:.1f}%")
        
        # Recalculate optimal allocation
        new_allocation = get_traffic_allocation()
        print(f" Updated allocation for {new_allocation.get('total_models', 0)} models")
        
        # Log conversion for tracking
        log_conversion_event(lead_id, model_version, performance_data[model_version])
        
    else:
        print(f" Model version {model_version} not found")

def log_conversion_event(lead_id, model_version, model_performance):
    """Log conversion events for tracking"""
    
    conversion_log = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'conversions.jsonl')
    os.makedirs(os.path.dirname(conversion_log), exist_ok=True)
    
    conversion_record = {
        'timestamp': datetime.now().isoformat(),
        'lead_id': lead_id,
        'model_version': model_version,
        'conversion_rate_after': model_performance['conversion_rate'],
        'total_predictions': model_performance['total_predictions'],
        'total_conversions': model_performance['total_conversions'],
        'confidence_interval': model_performance['confidence_interval']
    }
    
    with open(conversion_log, 'a') as f:
        f.write(json.dumps(conversion_record) + '\n')

def manage_model_memory():
    """Smart memory management for optimal performance"""
    global mab_predictor
    
    try:
        current_memory = mab_predictor.get_memory_usage()
        
        if current_memory > 0:  # If psutil is available
            print(f" Current memory usage: {current_memory:.1f}GB")
            
            if current_memory > 3.0:  # Over 3GB
                print(" High memory usage detected!")
                
                # Unload unused models
                mab_predictor.unload_unused_models(keep_recent=2)
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Check again
                new_memory = mab_predictor.get_memory_usage()
                print(f" Memory after cleanup: {new_memory:.1f}GB")
            
            elif current_memory > 2.0:  # Moderate usage
                # Keep only 3 most recent models
                mab_predictor.unload_unused_models(keep_recent=3)
        
        # Auto-retire old models to prevent accumulation
        retire_old_models(keep_recent=5)
        
    except Exception as e:
        print(f" Memory management error: {e}")

def retire_old_models(keep_recent=5):
    """Automatically retire old models to prevent memory bloat"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
    except FileNotFoundError:
        return
    
    # Sort models by last_updated
    models_by_date = sorted(
        performance_data.items(),
        key=lambda x: x[1]['last_updated'],
        reverse=True
    )
    
    updated = False
    
    # Keep only recent models active
    for i, (model_version, data) in enumerate(models_by_date):
        if i < keep_recent:
            if data['status'] != 'active':
                data['status'] = 'active'
                updated = True
        else:
            if data['status'] == 'active':
                data['status'] = 'retired'
                updated = True
                print(f" Auto-retired old model: {model_version}")
    
    # Save if updated
    if updated:
        with open(performance_file, 'w') as f:
            json.dump(performance_data, f, indent=2)

def add_new_model(model_version):
    """Add a new model to the optimized bandit system"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    os.makedirs(os.path.dirname(performance_file), exist_ok=True)
    
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
    except FileNotFoundError:
        performance_data = {}
    
    # Add new model
    performance_data[model_version] = {
        'total_predictions': 0,
        'total_conversions': 0,
        'conversion_rate': 0.0,
        'first_seen': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'status': 'active',
        'confidence_interval': {'lower': 0, 'upper': 0}
    }
    
    # Save updated data
    with open(performance_file, 'w') as f:
        json.dump(performance_data, f, indent=2)
    
    print(f" Added new model to optimized bandit: {model_version}")
    
    # Auto-manage old models
    retire_old_models(keep_recent=5)

def show_bandit_status():
    """Enhanced status display with performance metrics"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
        
        print("\n OPTIMIZED MULTI-ARMED BANDIT STATUS")
        print("=" * 70)
        
        # Memory status
        try:
            memory_usage = mab_predictor.get_memory_usage()
            if memory_usage > 0:
                print(f" Memory Usage: {memory_usage:.1f}GB")
        except:
            pass
        
        # Model status
        active_models = {k: v for k, v in performance_data.items() if v.get('status', 'active') == 'active'}
        retired_models = {k: v for k, v in performance_data.items() if v.get('status', 'active') != 'active'}
        
        print(f"\n ACTIVE MODELS ({len(active_models)}):")
        print("-" * 40)
        
        for model, data in active_models.items():
            ci = data.get('confidence_interval', {'lower': 0, 'upper': 0})
            print(f"🔹 {model}:")
            print(f"   Predictions: {data['total_predictions']:,}")
            print(f"   Conversions: {data['total_conversions']:,}")
            print(f"   Rate: {data['conversion_rate']:.1f}%")
            print(f"   Confidence: [{ci['lower']:.1f}%, {ci['upper']:.1f}%]")
            print(f"   Status: {data['status'].upper()}")
            print()
        
        if retired_models:
            print(f" RETIRED MODELS ({len(retired_models)}):")
            print("-" * 35)
            for model, data in retired_models.items():
                print(f"🔸 {model}: {data['conversion_rate']:.1f}% ({data['total_conversions']}/{data['total_predictions']})")
        
        # Current allocation
        allocation = get_traffic_allocation()
        print("\n🚦 CURRENT TRAFFIC ALLOCATION:")
        print("-" * 35)
        
        for model, weight in allocation.items():
            if model not in ['reason', 'winner', 'algorithm', 'total_models']:
                print(f"   {model}: {weight:.1%}")
        
        print(f"\n Algorithm: {allocation.get('algorithm', 'unknown')}")
        print(f" Current Winner: {allocation.get('winner', 'none')}")
        print(f" Total Active Models: {allocation.get('total_models', 0)}")
        
        # Performance summary
        if active_models:
            rates = [data['conversion_rate'] for data in active_models.values()]
            print(f"\n PERFORMANCE SUMMARY:")
            print(f"   Best Rate: {max(rates):.1f}%")
            print(f"   Worst Rate: {min(rates):.1f}%")
            print(f"   Avg Rate: {np.mean(rates):.1f}%")
            print(f"   Performance Spread: {max(rates) - min(rates):.1f}%")
        
        print("=" * 70)
        
    except FileNotFoundError:
        print(" No performance data found yet")

def benchmark_mab_performance():
    """Benchmark the optimized MAB system"""
    
    print("\n BENCHMARKING OPTIMIZED MAB PERFORMANCE")
    print("=" * 50)
    
    # Generate test data
    test_data = pd.DataFrame({
        'feature_1': np.random.randn(1000),
        'feature_2': np.random.randn(1000),
        'feature_3': np.random.randn(1000)
    })
    
    # Test model selection speed
    start_time = time.time()
    for i in range(100):
        selected_model = choose_model_for_prediction()
    selection_time = (time.time() - start_time) * 1000 / 100  # ms per selection
    
    print(f" Model Selection: {selection_time:.2f}ms per selection")
    
    # Test memory usage
    try:
        memory_usage = mab_predictor.get_memory_usage()
        print(f" Memory Usage: {memory_usage:.1f}GB")
    except:
        print(" Memory Usage: Unknown (psutil not available)")
    
    # Test allocation algorithm speed
    start_time = time.time()
    allocation = get_traffic_allocation()
    allocation_time = (time.time() - start_time) * 1000
    
    print(f" Allocation Calculation: {allocation_time:.1f}ms")
    print(f" Total Models Evaluated: {allocation.get('total_models', 0)}")
    print(f" Algorithm: {allocation.get('algorithm', 'unknown')}")
    
    print("=" * 50)
    
    return {
        'selection_time_ms': selection_time,
        'allocation_time_ms': allocation_time,
        'memory_gb': memory_usage if 'memory_usage' in locals() else 0,
        'active_models': allocation.get('total_models', 0)
    }

# DEMONSTRATION AND TESTING FUNCTIONS


def initialize_real_models():
    """Initialize MAB system with actual trained models only"""
    
    performance_file = os.path.join(os.path.dirname(__file__), '..', '..', 'metadata', 'model_performance.json')
    models_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
    
    # Get actual model files
    actual_models = []
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.startswith('model_V') and f.endswith('.pkl')]
        actual_models = [f.replace('.pkl', '') for f in model_files]
    
    print(f" Found {len(actual_models)} actual models: {actual_models}")
    
    # If no models found in directory, try to get from config
    if not actual_models:
        latest_model = get_latest_model_from_config()
        if latest_model:
            print(f" No model files found, but config suggests: {latest_model}")
            actual_models = [latest_model]
    
    # Clean performance data - keep only real models
    try:
        with open(performance_file, 'r') as f:
            performance_data = json.load(f)
    except FileNotFoundError:
        performance_data = {}
    
    # Remove demo models and keep only actual models
    cleaned_data = {}
    demo_models = ['model_v2_stable', 'model_v3_champion', 'model_v4_retrained', 'model_v2_experimental', 'default_model']
    
    for model_version, data in performance_data.items():
        if model_version not in demo_models and (model_version in actual_models or model_version.startswith('model_V')):
            cleaned_data[model_version] = data
            print(f" Keeping real model: {model_version}")
        else:
            print(f" Removing demo/placeholder model: {model_version}")
    
    # Add any missing actual models
    for model in actual_models:
        if model not in cleaned_data:
            cleaned_data[model] = {
                'total_predictions': 0,
                'total_conversions': 0,
                'conversion_rate': 0.0,
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'status': 'active',
                'confidence_interval': {'lower': 0, 'upper': 0}
            }
            print(f" Added actual model: {model}")
    
    # Save cleaned data
    with open(performance_file, 'w') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print(f" MAB system initialized with {len(cleaned_data)} real models")
    return cleaned_data

if __name__ == "__main__":
    # Initialize MAB system with real models
    print(" INITIALIZING LEAD SCORING MAB SYSTEM")
    print("=" * 50)
    
    # Clean up demo models and initialize with real models
    real_models = initialize_real_models()
    
    # Show current status
    print("\n CURRENT MAB STATUS:")
    show_bandit_status()
    
    # Test model selection if models are available
    if real_models:
        print(f"\n TESTING MODEL SELECTION:")
        print("-" * 30)
        for i in range(3):
            selected = choose_model_for_prediction()
            print(f"   Test {i+1}: {selected}")
    
    print(f"\n MAB SYSTEM READY FOR PRODUCTION!")
    print(f" Use predict_with_mab_optimized(data) for predictions")
    print(f" Call update_conversions(lead_id, model) when conversions happen")
    print(f" Use show_bandit_status() to monitor performance")