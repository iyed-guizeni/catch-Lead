from datetime import datetime
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
import joblib
import os

def train_model(temp, dataSource):
    #load the data
    try:
        data_train = pd.read_csv(dataSource)
    except Exception as e:
        print(f"Error loading data from {dataSource}: {e}")
        return
    X_train = data_train.drop('converted' ,axis=1)
    y_train = data_train['converted']

    model = LogisticRegression()
    parameters = {
        'C': [0.01, 0.1, 1, 10, 100]
    }

    cv = GridSearchCV(model,  param_grid=parameters, cv=5)
    cv.fit(X_train, y_train)

    try:
        #save the trained model
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', f'model_V{temp}.pkl')
        joblib.dump(cv, model_path) 
    except Exception as e:
        print("ERROR: problem while storing model as pkl")
        return
    
    
    
    
    
