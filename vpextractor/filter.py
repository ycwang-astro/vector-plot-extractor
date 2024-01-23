# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 19:09:47 2024

@author: Yu-Chen Wang

helper functions for filtering out not useful elements
"""

import numpy as np
from itertools import repeat

def eq(ar0, ar1, eta=1e-2):
    ar0 = np.array(ar0)
    ar1 = np.array(ar1)
    if ar0.shape != ar1.shape:
        return False
    else:
        return np.all(np.abs(ar0 - ar1) < eta)

def select_paths(target_feature, path_features, modes='s'):
    if isinstance(modes, (tuple, list)) and len(modes) != len(path_features):
        raise ValueError(f'expected {len(path_features)} or 1 modes, got {len(path_features)}')
    if isinstance(modes, str):
        modes = repeat(modes)
    
    idx = []
    for i, (path_feature, mode) in enumerate(zip(path_features, modes)):
        if mode in 'sl' and not eq(target_feature['rel_pos'], path_feature['rel_pos']):
            continue # not matched
        elif mode in 'ol' and not (np.array_equal(target_feature['color'], path_feature['color']) and np.array_equal(target_feature['fill'], path_feature['fill'])):
            continue # not matched
        idx.append(i)
    return idx

def rect_filter_objects(objects, x0, x1, y0, y1, mode='touch'):
    # objects is of format the same as that in `drawing.py`
    # filter with rectangle
    
    selected = {}
    
    if mode == 'touch':
        for typ, typ_objs in objects.items():
            selected[typ] = np.full(len(typ_objs), False, dtype=bool)
    
            for i, obj in enumerate(typ_objs):
                x, y = obj['coords']
                x, y = np.array(x), np.array(y)
                if np.any((x0 <= x) & (x <= x1) & (y0 <= y) & (y <= y1)):
                    selected[typ][i] = True
        
    return selected
    
def get_filtered_objects(objects, selection):
    filtered_objects = {}
    
    for typ, typ_objs in objects.items():
        filtered_objects[typ] = []

        for idx in np.where(selection[typ])[0]:
            filtered_objects[typ].append(typ_objs[idx])
    
    return filtered_objects
