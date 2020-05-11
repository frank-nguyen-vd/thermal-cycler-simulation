from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np


class DataHandler:
    def __init__(self):
        pass     

    def import_raw(self, volume, path):
        full_data = pd.read_csv(path)         
        list_of_features = ['Epoch Time', 'Z1 BlkTemp', 'Z1 HeatSink', 'Z1 Iset', 'Z1 Imea', 'Z1 Vset']
        raw_data = pd.DataFrame()
        raw_data = pd.concat([raw_data, full_data[list_of_features]], axis=1)    
        raw_data['Volume'] = volume
        return raw_data
    
    def rename_labels(self, raw_data):
        raw_data = raw_data.rename(columns={'Z1 BlkTemp': 'Block Temp',
                                            'Z1 HeatSink': 'Heat Sink Temp',
                                            'Z1 Iset': 'Iset',
                                            'Z1 Imea': 'Imeasure',
                                            'Z1 Vset': 'Vset'
                                           })        
        return raw_data
    
    def abs_time_to_period(self, raw_data):
        # Calculate and use delta_t instead of epoch time
        next_epoch = raw_data['Epoch Time'][1::]
        next_epoch.index -= 1
        
        raw_data['Epoch Time'] = next_epoch - raw_data['Epoch Time']
        raw_data = raw_data.rename(columns={'Epoch Time': 'Period'})
        raw_data = raw_data.dropna()
        
        return raw_data
    
    def add_present_block_rate(self, raw_data):
        prev_temp = raw_data['Block Temp'][:-1]
        prev_temp.index += 1
        raw_data['Block Rate'] = (raw_data['Block Temp'] - prev_temp) / raw_data['Period']
        raw_data = raw_data.dropna()
        
        return raw_data
    
    def add_new_block_rate(self, raw_data):
        raw_data['New Block Rate'] = (raw_data['New Block Temp'] - raw_data['Block Temp']) / raw_data['Period']
        raw_data = raw_data.dropna()
        
        return raw_data    
    
    def add_new_block_temp(self, raw_data):        
        new_block_temp = raw_data['Block Temp'][1::]
        new_block_temp.index -= 1
        raw_data['New Block Temp'] = new_block_temp
        
        raw_data = raw_data.dropna()
        
        return raw_data
    
    def select_columns(self, raw_data, columns):
        raw_data = raw_data[columns]
        return raw_data

    def process_data(self, raw_data):      
        raw_data = self.rename_labels(raw_data)
        raw_data = self.abs_time_to_period(raw_data)
        raw_data = self.add_present_block_rate(raw_data)
        raw_data = self.add_new_block_temp(raw_data)        
        
        return raw_data

    def generate(self, vols=[5, 10, 30, 50], raw_dir="train/raw/", data_path="train/pcr_training_set.csv"):        
        pcr_dataset = pd.DataFrame()
        for volume in vols:
            dir_path = raw_dir + f"{volume}ul/"
            try:
                file_list = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
            except:
                continue
            for path in file_list:
                new_data = self.import_raw(volume=volume, path=path)
                new_data = self.process_data(new_data)
                pcr_data = self.select_columns(new_data, columns = [
                                                                    'Volume',                                                                    
                                                                    'Block Temp',
                                                                    'Block Rate', 
                                                                    'Iset',
                                                                    'Vset',
                                                                    'New Block Temp'
                                                                ])
                pcr_dataset = pcr_dataset.append(pcr_data)
        pcr_dataset.to_csv(data_path, index=False)

if __name__ == "__main__":
    train_raw  = 'train/raw/'
    train_path = 'train/pcr_training_set.csv'
    test_raw   =  'test/raw/'
    test_path  = 'test/pcr_testing_set.csv'
    handler = DataHandler()
    handler.generate(raw_dir=train_raw, data_path=train_path)
    handler.generate(raw_dir=test_raw, data_path=test_path)