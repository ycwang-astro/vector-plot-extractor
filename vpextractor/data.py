# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 2024

@author: Yu-Chen Wang
"""

import json
import numpy as np

class DataExplorer():
    def __init__(self, path):
        if path.endswith(('.pdf', '.svg', '.ps')):
            path += '.out'
        self.filepath = path
        
        with open(self.filepath) as f:
            self.data = json.load(f)
        
        for axis_data in self.data.values():
            for type_data in axis_data.values():
                for data in type_data:
                    data['x'] = np.array(data['x'])
                    data['y'] = np.array(data['y'])
    
    def __getitem__(self, key):
        if isinstance(key, int):
            key = str(key)
        return self.data[key]
