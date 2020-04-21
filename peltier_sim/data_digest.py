import pandas as pd
import numpy as np

class DataHandler:
    def __init__(self):
        pass     

    def import_raw(self, volume, path):
        full_data = pd.read_csv(path)    
        raw_data = pd.DataFrame()
        list_of_features = ['Epoch Time', 'Z1 BlkTemp', 'Z1 HeatSink', 'Z1 Iset', 'Z1 Imea']
        raw_data = pd.concat([raw_data, full_data[list_of_features]], axis=1)    
        raw_data['Volume'] = volume
        return raw_data
    
    def rename_labels(self, raw_data):
        raw_data = raw_data.rename(columns={'Z1 BlkTemp': 'Block Temp',
                                            'Z1 HeatSink': 'Heat Sink Temp',
                                            'Z1 Iset': 'Iset',
                                            'Z1 Imea': 'Imeasure'
                                           })        
        return raw_data
    
    def replace_with_period(self, raw_data):
        # Calculate and use delta_t instead of epoch time
        next_epoch = raw_data['Epoch Time'][1::]
        next_epoch.index -= 1
        
        raw_data['Epoch Time'] = next_epoch - raw_data['Epoch Time']
        raw_data = raw_data.rename(columns={'Epoch Time': 'Period'})
        raw_data = raw_data.dropna()
        
        return raw_data
    
    def add_block_rate(self, raw_data):
        prev_temp = raw_data['Block Temp'][:-1]
        prev_temp.index += 1
        raw_data['Block Rate'] = (raw_data['Block Temp'] - prev_temp) / raw_data['Period']
        raw_data = raw_data.dropna()
        
        return raw_data
    
    def add_new_block_temp(self, raw_data):        
        new_block_temp = raw_data['Block Temp'][1::]
        new_block_temp.index -= 1
        raw_data['New Block Temp'] = new_block_temp
        
        raw_data = raw_data.dropna()
        
        return raw_data
    
    def reorder_labels(self, raw_data):
        raw_data = raw_data[['Volume',
                             'Period',
                             'Heat Sink Temp',
                             'Block Temp',
                             'Block Rate', 'Iset',
                             'Imeasure',
                             'New Block Temp'
                            ]]
        return raw_data

    def process_data(self, raw_data):      
        raw_data = self.rename_labels(raw_data)
        raw_data = self.replace_with_period(raw_data)
        raw_data = self.add_block_rate(raw_data)
        raw_data = self.add_new_block_temp(raw_data)
        raw_data = self.reorder_labels(raw_data)
        return raw_data
