# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 15:24:50 2024

@author: Yu-Chen Wang
"""

from .utils import save_pickle, load_pickle
from .drawing import split_broken_paths

import fitz

#%%
def pdf2drawings(pdf_path, out_path=None, page=0, split_broken_path=False):
    if out_path is None:
        out_path = pdf_path + '.drw'
    with fitz.open(pdf_path) as doc:
        page = doc[page]
        paths = page.get_drawings()
    
    if split_broken_path:
        paths = split_broken_paths(paths) 
    
    save_pickle(out_path, paths)
    return paths


