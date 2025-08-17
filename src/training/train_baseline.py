import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_model import train_model
from tune_threshold import tune_threshold
from preprocess.preprocess import preprocess_and_save

def train_base_model():
    dataSource = os.path.join(os.path.dirname(__file__),'..','..','data','raw','crm_labled.csv')
    #preprocess data
    temp = preprocess_and_save(dataSource)
    print(temp)
    trainPath = os.path.join(os.path.dirname(__file__),'..','..','data','processed',f'train_data_{temp}.csv')
    #train the model
    train_model(temp, trainPath)
    #threshold tunning
    testPath = os.path.join(os.path.dirname(__file__),'..','..','data','processed',f'test_data_{temp}.csv')
    tune_threshold(temp, testPath)
    
    
if __name__ == "__main__":
    train_base_model()