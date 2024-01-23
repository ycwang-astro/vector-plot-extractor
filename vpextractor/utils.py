# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 23:26:16 2024

@author: Yu-Chen Wang
"""

try:
    from astrotable.utils import save_pickle, load_pickle, pause_and_warn
    from astrotable.plot import _annotate
except ModuleNotFoundError:
    from ._utils import save_pickle, load_pickle, pause_and_warn, _annotate

from functools import wraps
import numpy as np

@wraps(_annotate)
def annotate(*args, **kwargs):
    artists = _annotate(*args, **kwargs)
    for artist in artists.values():
        artist.set_picker(True)
    return artists

def dedup(arr, axis=0):
    if axis != 0:
        raise NotImplementedError()
    
    if isinstance(arr, np.ndarray) and arr.ndim >= 1: # and arr.ndim == 2:
        arr_unique = np.unique(arr, axis=axis)
        if len(arr_unique) == 1:
            return arr_unique[0]
        else:
            return arr
    if isinstance(arr, list) and len(set(arr)) == 1:
        return arr[0]
    else:
        return arr
    

