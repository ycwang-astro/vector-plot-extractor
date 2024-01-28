# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 21:43:40 2024

@author: Yu-Chen Wang

general UIs
"""

import matplotlib.pyplot as plt
from .drawing import plot_paths, group_paths, plot_objects
import os
from .fileio import pdf2drawings, load_pickle, save_pickle
from .mplui import ElementIdentifier, DataExtractor, RectObjectSelector
from .utils import pause_and_warn
# from copy import deepcopy
import logging
from argparse import ArgumentParser
plt.style.use('vpextractor.disable_key')

class EmptyPathError(Exception):
    '''The `paths` is empty.'''
    pass

def element_identifier(paths):
    fig, ax = plt.subplot_mosaic(
        [['main', 'marker'],
         ['main', 'group']],
        width_ratios=[5, 3], height_ratios=[5-3, 3])
    # ax['group'].set_title('')
    
    artists, artists_in_plot, path_features = plot_paths(paths, ax=ax['main'])
    
    with ElementIdentifier(fig=fig, ax=ax, artists=artists, artists_in_plot=artists_in_plot, path_features=path_features) as ei:
        plt.show()
        ei.wait()
    return ei

def data_filter(objects):
    fig, ax = plt.subplots()
    
    # plot_objects(deepcopy(objects))
    with RectObjectSelector(fig=fig, objects=objects, ax=ax) as ros:
        plt.show()
        ros.wait()
    return ros
    
def data_extractor(objects, pdf_path=None):
    # fig, ax = plt.subplots(1, 2)
    # fig.add_axes((0.1, 0.05, 0.4, 0.075))
    fig, ax = plt.subplot_mosaic(
        [['main', 'plot'],
         ['box', 'plot']],
        width_ratios=[5, 5], height_ratios=[8, 1], 
        figsize=(6.4*1.7, 4.8*1.2))
    fig.suptitle('\n')
    plt.tight_layout()
    
    with DataExtractor(fig=fig, objects=objects, ax0=ax['main'], ax1=ax['plot'], axbox=ax['box'], pdf_path=pdf_path) as de:
        plt.show()
        de.wait()
        
    return de
    
def runall(pdf_path):
    drw_path = pdf_path + '.drw'
    if not os.path.exists(drw_path):
        pdf2drawings(pdf_path)
    paths = load_pickle(drw_path)
    
    if len(paths) == 0:
        raise EmptyPathError(f"Found nothing to extract from '{pdf_path}': is it a vector image?")
    
    ei_files = ['.mkr', '.typ']
    if any(os.path.exists(pdf_path + ei_file) for ei_file in ei_files):
        redo = pause_and_warn('Seems that you have already identified plot elements. Re-identifing will overwrite the information saved (files "{}") earlier'.format('" and "'.join([pdf_path + ei_file for ei_file in ei_files])),
                              choose='do you want to redo this step? ',
                              no_message='', warn=False)
        if redo:        
            ei = element_identifier(paths)
            ei.save(pdf_path, yes=True)
    else: # element_identifier not run
        ei = element_identifier(paths)
        ei.save(pdf_path)
    
    filtered_obj_path = pdf_path + '.sel.obj'
    
    if os.path.exists(filtered_obj_path):
        do_selection = pause_and_warn('Seems that you have already selected part of the plot for extraction. Re-selecting will overwrite the information saved (files "{}") earlier'.format('" and "'.join([filtered_obj_path])),
                              choose='do you want to redo this step? ',
                              no_message='', warn=False)
    else:
        do_selection = True
    
    if do_selection:
        types, known_markers = ElementIdentifier.load(pdf_path)
        objects = group_paths(paths, types, mode='typestr', markers=known_markers, marker_getter='mean')
        
        ros = data_filter(objects)
        
        # selection = ros.selected
        filtered_objects = ros.get_filtered_objects()
        
        save_pickle(filtered_obj_path, filtered_objects)
    else:
        filtered_objects = load_pickle(filtered_obj_path)
    
    de = data_extractor(filtered_objects, pdf_path=pdf_path)
    
def main(argv=None):
    parser = ArgumentParser(
        prog='vpextract',
        description='extracting data points from vector plots (pdf, etc.): a general UI',
        epilog='This is part of the Python package vector-plot-extractor, (C) Yu-Chen Wang, distributed under GPL v3.')
    parser.add_argument('pdfpath', help='path to your pdf file')
    
    args = parser.parse_args(argv)
    
    runall(pdf_path=args.pdfpath)
    
if __name__ == '__main__':
    main()
