from datetime import datetime
import pandas as pd
import numpy as np
import os
import json
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def preprocess_and_save(dataSource):
    # Load the data
    data = pd.read_csv(dataSource)
    
    # Remove columns if they exist
    columns_to_remove = ['firstname', 'lastname', 'email']
    data = data.drop(columns=[col for col in columns_to_remove if col in data.columns])
    #seperate features and target
    X = data.drop(['converted', 'lead_id'], axis=1)
    y = data['converted']
    num = [
    ('imputer', SimpleImputer(strategy='median') ),
    ('scaler', StandardScaler())
    ]
    numeric_pipeline = Pipeline(num)
    
    cat = [
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
    ]
    categorical_pipeline = Pipeline(cat)
    
    #compose the pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_pipeline, ['company_size', 'contact_attempts', 'days_since_first_contact']),
            ('cat', categorical_pipeline, ['source', 'region',  'job_title']),
            ('bool', 'passthrough', ['has_company_website'])
        ]
    )
    #split the dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
     
    # fit and transform features
    X_train = preprocessor.fit_transform(X_train)
    X_test = preprocessor.transform(X_test)
     
    # Create processed data directory if it doesn't exist
    processed_dir = os.path.join(os.path.dirname(__file__),'..','..','data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Get feature names from the preprocessor
    try:
        feature_names = preprocessor.get_feature_names_out()
    except:
        # Fallback if get_feature_names_out() is not available
        feature_names = [f'feature_{i}' for i in range(X_train.shape[1])]

    # Convert to DataFrames with proper column names
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_train_df['converted'] = y_train.reset_index(drop=True)

    # Convert test data with the same column names  
    X_test_df = pd.DataFrame(X_test, columns=feature_names)
    X_test_df['converted'] = y_test.reset_index(drop=True)

    # Save with timestamp
    train_filepath = os.path.join(processed_dir, f'train_data_{timestamp}.csv')
    test_filepath = os.path.join(processed_dir, f'test_data_{timestamp}.csv')

    X_train_df.to_csv(train_filepath, index=False)
    X_test_df.to_csv(test_filepath, index=False)

    # Save the preprocessor for future use
    preprocessor_filepath = os.path.join(os.path.dirname(__file__),'..','..','models', f'preprocessor_{timestamp}.pkl')
    joblib.dump(preprocessor, preprocessor_filepath)
    modelsVersion = os.path.join(os.path.dirname(__file__),'..','..','config','models_version.json')
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(modelsVersion), exist_ok=True)
    
    # Load existing versions or create new dict
    if os.path.exists(modelsVersion):
        with open(modelsVersion, 'r') as f:
            versions = json.load(f)
    else:
        versions = {}
    
    # Append new timestamp to the list
    if 'timestamps' not in versions:
        versions['timestamps'] = []
    versions['timestamps'].append(timestamp)
    
    # Save updated versions back to file
    with open(modelsVersion, 'w') as f:
        json.dump(versions, f, indent=2)
    
    return timestamp
 