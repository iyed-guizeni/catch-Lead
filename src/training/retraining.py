import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fetch.fetch_labled_leads import main as fetch_labeled_leads
from training.smart_data_merger import SmartDataMerger
from preprocess.preprocess import preprocess_and_save
from train_model import train_model
def retrain_model():
    # fetch new lead
    try:
        lead = fetch_labeled_leads()
        if not lead:
            print('No fresh labeled lead for training.')
            return
    except Exception as e:
        print('ERROR WHILE FETCHING NEW LABELED LEADS:', e)
        return
    smart_merge = SmartDataMerger()
    master_path, metadata = smart_merge.create_master_dataset()
    print(master_path)
    print(metadata)
    
    #preprocess the merged data
    temp = preprocess_and_save(master_path)
    #print(temp)
    #retrain the mode
    dataSource = os.path.join(os.path.dirname(__file__),'..','..','data','processed', f'train_data_{temp}.csv')

    try:
        train_model(temp, dataSource)
    except Exception as e:
        print('ERROR DURING MODEL TRAINING:', e) 

if __name__ == "__main__":
    retrain_model()
