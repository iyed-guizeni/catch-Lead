import numpy as np


def baseLine_stats(baseline_probabilities):
    baseline_stats = {
        'mean': np.mean(baseline_probabilities),
        'median': np.median(baseline_probabilities), 
        'std': np.std(baseline_probabilities),
        'percentiles': {
            'p10': np.percentile(baseline_probabilities, 10),  
            'p25': np.percentile(baseline_probabilities, 25),  
            'p75': np.percentile(baseline_probabilities, 75),  
            'p90': np.percentile(baseline_probabilities, 90)   
        }
    }
    return baseline_stats