# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 2024

@author: Yu-Chen Wang
"""

import json
import numpy as np
import matplotlib.pyplot as plt

class DataExplorer():
    def __init__(self, path):
        if path.endswith(('.pdf', '.svg', '.ps')):
            path += '.out'
        self.filepath = path
        
        with open(self.filepath) as f:
            self.data = json.load(f)
        
        for key, axis_data in self.data.items():
            if key == 'meta':
                continue
            for type_data in axis_data.values():
                for data in type_data:
                    data['x'] = np.array(data['x'])
                    data['y'] = np.array(data['y'])
    
    def plot(self, axisnumber=None, ax=None):
        '''
        plot data

        Parameters
        ----------
        axisnumber : int or str, optional
            Number of axis. If not given, the axis number 0 will be plotted.
            The default is None.
        ax : Axes, optional
            The Matplotlib Axes object. If not given, the currect axis (``plt.gca()``) will be used.
            The default is None.

        Returns
        -------
        None.
        '''
        if axisnumber is None:
            axisnumber = 0
        if ax is None:
            ax = plt.gca()
        for data in self[axisnumber]['scatters']:
            ax.scatter(data['x'], data['y'], fc=data['facecolor'], ec=data['edgecolor'])
        for data in self[axisnumber]['lines']:
            ax.plot(data['x'], data['y'], color=data['color'], linestyle=data['linestyle'], linewidth=data['linewidth'])
    
    def __getitem__(self, key):
        if isinstance(key, int):
            key = str(key)
        return self.data[key]
