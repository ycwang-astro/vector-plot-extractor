# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 19:28:30 2024

@author: Yu-Chen Wang
"""

import numpy as np
from .filter import select_paths, rect_filter_objects, get_filtered_objects
from copy import copy, deepcopy
from .drawing import add, plot_objects, get_color, Line2D
import matplotlib.pyplot as plt
from .utils import pause_and_warn, save_pickle, annotate, dedup
import os
import json
from matplotlib.widgets import TextBox
from itertools import chain
from . import __version__

class ConsistencyError(Exception):
    pass

class BaseEventHandler():
    def __init__(self, fig=None, **kwargs):
        self.pressed_down = False
        self.key_pressed_down = False
        self.cids = []
        self.finished = False
        
        if fig is not None:
            self.connect(fig)
       
        self.init(**kwargs)
    
    def init(self, **kwargs):
        pass
        
    def connect(self, fig):
        self.fig = fig
        self.cids += [
            fig.canvas.mpl_connect('button_press_event', self._onpress),
            fig.canvas.mpl_connect('button_release_event', self._onrelease),
            fig.canvas.mpl_connect('key_press_event', self._onkeypress),
            fig.canvas.mpl_connect('key_release_event', self._onkeyrelease),
            fig.canvas.mpl_connect('motion_notify_event', self._onmove),
            fig.canvas.mpl_connect('pick_event', self.onpick),
            fig.canvas.mpl_connect('close_event', self.onclose),
            ]
        
    def disconnect(self):
        for cid in self.cids:
            self.fig.canvas.mpl_disconnect(cid)
        self.cids.clear()
    
    def _onpress(self, event):
        self.pressed_down = True
        self.onpress(event)
    
    def onpress(self, event):
        pass
    
    def _onrelease(self, event):
        self.pressed_down = False
        self.onrelease(event)
    
    def onrelease(self, event):
        pass
    
    def _onkeypress(self, event):
        self.key_pressed_down = True
        self.onkeypress(event)
    
    def onkeypress(self, event):
        pass
    
    def _onkeyrelease(self, event):
        self.key_pressed_down = False
        self.onkeyrelease(event)
    
    def onkeyrelease(self, event):
        pass
    
    def _onmove(self, event):
        if self.pressed_down:
            self.onmove_down(event)
        else:
            self.onmove_up(event)
    
    def onmove(self, event):
        pass
    
    def onmove_up(self, event):
        self.onmove(event)
        
    def onmove_down(self, event):
        self.onmove(event)
        
    def onpick(self, event):
        pass
    
    def onclose(self, event):
        if not self.finished:
            self.finished = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, *exc):
        self.disconnect()
        self.finalize()
        
    def finalize(self):
        pass
        
    def wait(self, interval=.1):
        # wait until self.finish
        while True:
            if self.finished:
                return
            plt.pause(interval)
            

class RectSelector(BaseEventHandler):
    def init(self, finish=True):
        # finish: if set to True, will be considered finished whenever a region is selected
        self.rects = {}
        for ax in self.fig.axes:
            rect, = ax.plot([], [], linestyle='--', color='r')
            self.rects[ax] = rect
        self.finish = finish
    
    def onpress(self, event):
        self.finished = False
        self.ax = event.inaxes
        self.x0, self.y0 = event.xdata, event.ydata
    
    def onmove_down(self, event):
        if event.inaxes == self.ax:
            self.x1, self.y1 = event.xdata, event.ydata
            
            x, y  = self.get_xydata()
            self.rects[self.ax].set_data(x, y)
            self.rects[self.ax].set_marker('')
            self.fig.canvas.draw()
            
    def onrelease(self, event):
        self.x0, self.x1 = np.sort((self.x0, self.x1))
        self.y0, self.y1 = np.sort((self.y0, self.y1))
        self.rects[self.ax].set_marker('s')
        self.fig.canvas.draw()
        
        if self.finish: 
            self.finished = True
        
    def get_xydata(self, closed=True):
        x0, x1 = np.sort((self.x0, self.x1))
        y0, y1 = np.sort((self.y0, self.y1))
        if closed:
            return [x0, x0, x1, x1, x0], [y0, y1, y1, y0, y0]
        else:
            return [x0, x0, x1, x1], [y0, y1, y1, y0]
        
class ElementIdentifier(BaseEventHandler):
    def init(self, ax, artists, artists_in_plot, path_features):
        self.ax = ax
        self.artists = artists
        self.artists_in_plot = artists_in_plot
        self.path_features = path_features
        self.indexes = np.arange(len(self.path_features), dtype=int)
        self.known_markers = []
        self.matches = []
        self.types = np.full((len(artists),), fill_value='u', dtype='S1') # [S]catter, [L]ine, [D]iscard. u means "not marked"
        self.state = 0
        self.fig.suptitle('click element to identify')
    
    def onpick(self, event):
        artist = event.artist
        # print(artist)
        if self.state == 0 and artist in self.artists_in_plot: #event.inaxes == self.ax['main']:
            self.picked = True
            idx = self.artists_in_plot.index(artist)
            self.path_feature = self.path_features[idx]
            # print(idx, self.path_feature)
            self.fig.suptitle('object type: [S]catter, [L]ine, [D]iscard, [O]thers, or [C]ancel')
            self.ax['marker'].clear()
            add(self.ax['marker'], copy(self.artists[idx]))
            self.ax['marker'].autoscale(True)
            self.ax['marker'].invert_yaxis()
            self.state = 1
            
            self.fig.canvas.draw()
        
    # match_mode_dict = { # keyboard shortcut: mode code in code
    #     's': 's',
    #     'o': 'c',
    #     'l': 'sc',
    #     }
    
    type_names = { # type names to display
        's': 'scatter',
        'l': 'line',
        'd': 'discard',
        'o': 'others',
        }
        
    def onkeyrelease(self, event):
        if self.state == 0: #
            if event.key == 'f': # finish?
                self.state = 99
                self.fig.suptitle('[F]inish? (press "f" again to confirm)')
        elif self.state == 99:
            if event.key == 'f':
                plt.close(self.fig)
                self.finished = True
            else:
                self.state = 0
                self.fig.suptitle('click element to identify, or [F]inish')
        elif self.state >= 1 and self.state <= 9: # currently handling an object
            if event.key == 'c': # cancelled
                self.state = 0
                self.fig.suptitle('click element to identify, or [F]inish')
                
            elif self.state == 1 and event.key in 'sldo': # have just chosen object type
                self.type = event.key
                # next step, choose how to match similar objects
                self.fig.suptitle('chosen "{}". match [S]hape, c[O]lor, co[L]or+shape, or [C]ancel'.format(self.__class__.type_names[self.type]))
                self.state = 2
                
            elif self.state == 2 and event.key in 'sol':
                self.match_mode = event.key
                self.matched_idxs = select_paths(self.path_feature, self.path_features, modes=self.match_mode)
                self.ax['group'].clear()
                warntxt = ''
                for i, artist in enumerate(self.artists):
                    if i in self.matched_idxs:
                        add(self.ax['group'], copy(artist))
                        # print(artist, isinstance(artist, Line2D))
                        if self.type == 's' and not warntxt and isinstance(artist, Line2D):
                            # print('here')
                            warntxt = '\n(WARNING: elements labelled as "scatter", but at least one is line-like)'
                self.ax['group'].set_title(f'found {len(self.matched_idxs)}')
                self.ax['group'].autoscale(True)
                self.ax['group'].invert_yaxis()
                # self.ax['group'].set_xlim(self.ax['main'].get_xlim())
                # self.ax['group'].set_ylim(self.ax['main'].get_ylim())
                self.fig.suptitle(f'press any key to continue or [C]ancel{warntxt}')
                self.state = 3
                    
            elif self.state == 3:
                self.types[self.indexes[self.matched_idxs]] = self.type
                    
                if self.type == 's':
                    self.known_markers.append({
                        'match_by': self.match_mode,
                        'feature': self.path_feature})
                elif self.type == 'd':  
                    pass
                elif self.type =='l':
                    pass
                elif self.type == 'o':
                    pass
                else:
                    raise ValueError
                
                # remove matched artists
                new_artists = []
                new_path_features = []
                new_artists_in_plot = []
                new_indexes = []
                for i, artist in enumerate(self.artists):
                    if i in self.matched_idxs:
                        self.artists_in_plot[i].remove()
                    else:
                        new_artists.append(artist)
                        new_artists_in_plot.append(self.artists_in_plot[i])
                        new_path_features.append(self.path_features[i])
                        new_indexes.append(self.indexes[i])
                self.artists = new_artists
                self.artists_in_plot = new_artists_in_plot
                self.path_features = new_path_features
                self.indexes = np.array(new_indexes)
                
                self.state = 0
                self.fig.suptitle('click element to identify, or [F]inish')
        else:
            return
            
        self.fig.canvas.draw()
            
    def save(self, basepath, yes=False):
        # save information to file
        type_path = basepath + '.typ'
        if not yes and os.path.exists(type_path):
            pause_and_warn('File "{}" already exists!'.format(type_path), choose='overwrite existing files?',
                           default='n', yes_message='overwritten', no_message='raise')
        with open(type_path, 'wb') as f:
            f.write(self.types.tobytes())
        
        marker_path = basepath + '.mkr'
        if not yes and os.path.exists(marker_path):
            pause_and_warn('File "{}" already exists!'.format(type_path), choose='overwrite existing files?',
                           default='n', yes_message='overwritten', no_message='raise')
        
        with open(marker_path, 'w') as f:
            json.dump(self.known_markers, f, #ensure_ascii=True, indent=2,
                      default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x,
                      )
    
    @staticmethod
    def load(basepath):
        type_path = basepath + '.typ'
        # with open(type_path, 'rb') as f:
        #     types = np.frombuffer(f.read(), dtype='S1')
        with open(type_path) as f:
            types = f.read()
        
        marker_path = basepath + '.mkr'
        with open(marker_path) as f:
            known_markers = json.load(f)
            
        return types, known_markers
    
class RectObjectSelector(RectSelector):
    def init(self, objects, ax=None, mode='touch'):
        # modes: 
        #     'touch': if any part of the group of object in this region (in other words, if the rectangle "touches" the object), select
        
        super().init()
        self.objects = objects
        if ax is None:
            ax = self.fig.ax
        self.ax = ax
        self.objects = deepcopy(objects)
        self.orig_objects = objects
        self.selected = {}
        for typ, typ_objs in objects.items():
            self.selected[typ] = np.full(len(typ_objs), True, dtype=bool)
        
        self.mode = mode
        
        plot_objects((self.objects))
        
        self.ax.set_title('change [M]ode, [R]estart, or select rectangle')
        
    def onrelease(self, event):
        super().onrelease(event)
        
        selected = rect_filter_objects(self.objects, self.x0, self.x1, self.y0, self.y1, mode=self.mode)
        self.last_selected = selected
        # print(selected)
        
        for typ, typ_objs in self.objects.items():
            for idx in np.where(self.selected[typ] & ~selected[typ])[0]: # make them fade
                # print(np.where(self.selected[typ] & ~selected[typ]))
                # print(idx)
                # assert typ_objs is self.objects[typ]
                # print(typ_objs[idx]['artist'])
                typ_objs[idx]['artist'].set_visible(False)
                self.selected[typ][idx] = False
        
        self.fig.canvas.draw()
        
    def onkeyrelease(self, event):
        if event.key == 'm':
            self.ax.set_title('sorry, not supported yet')
            plt.pause(1)
            self.ax.set_title('change [M]ode, [R]estart, or select rectangle')
        elif event.key == 'r':
            for typ, typ_objs in self.objects.items():
                self.selected[typ] = np.full(len(typ_objs), True, dtype=bool)
                for typ_obj in typ_objs:
                    typ_obj['artist'].set_visible(True)
        self.fig.canvas.draw()
            
    def get_filtered_objects(self):
        # print(self.selected)
        return get_filtered_objects(self.orig_objects, self.selected)
    
    
class DataExtractor(BaseEventHandler):
    def init(self, objects, ax0, ax1, axbox, pdf_path=None):
        self.exportpath = pdf_path + '.out'
        if os.path.exists(self.exportpath):
            pause_and_warn('File "{}" already exists: this file contains data you have exported.'.format(self.exportpath), choose='overwrite existing file?',
                           default='n', yes_message='', no_message='raise', warn=False)
        
        self.objects = objects
        self.ax0 = ax0
        self.ax1 = ax1
        self.axbox = axbox
        
        self.textbox = TextBox(self.axbox, '', textalignment="center")
        self.textbox.on_submit(self.onsubmit)
        
        # calibration line artists
        self.xcals = []
        self.ycals = []
        self.select_rect = None
        
        self.xscale = None
        self.yscale = None
        
        self.export_data = {
            'meta': {
                'vpextractor_version': __version__,
                },
            }
        
        self.axes = {} # data axes information, not real axes for plot
        self._ca = None # currect data axis number 
        self._next_axis = None # the next axis to be changed to
        
        self.select_mode = 'touch'
        
        if pdf_path is not None:
            self.savepath = pdf_path + '.axes'
            # if os.path.exists(self.savepath):
            #     pause_and_warn(f"'{self.savepath}' already exists!", choose='overwrite?')
            self.axes.update(self.load())
        else:
            raise NotImplementedError('please input pdf_path')
        
        plot_objects(self.objects, ax=self.ax0)
        
        self.set_status(-1)
        
    @property
    def ca(self): # currect data axis dict
        return self.axes[self._ca]
    
    status_title = {
        -1: '[A]dd an axis, input number of any saved axis, [E]xport all axes, or [S]ave',
        # 100: 'axis #%ca: click on an axis tick/data plot, or manally set [X]-axis/[Y]-axis calibration, \n'\
        #     'set [A]xis region, [S]ave, [E]xport, d[U]plicate, or e[X]it axis',
        100: 'axis #%ca: click on an axis tick/data plot, or: \n'\
            'set [A]xis region, [S]ave, [E]xport, d[U]plicate, or e[X]it axis',
        110: 'input x value in textbox, or [C]ancel',
        111: 'input y value in textbox, or [C]ancel',
        120: 'change x value, [D]elete, or [C]ancel',
        121: 'change y value, [D]elete, or [C]ancel',
        130: 'axis #%ca copied to axis #%na. press Enter to change to #%na',
        140: 'drag to select',
        }
    
    def set_status(self, code, **kwargs):
        self.status = code
        title = self.__class__.status_title[code]
        title = title.replace('%ca', str(self._ca))
        title = title.replace('%na', str(self._next_axis))
        for old, new in kwargs:
            title = title.replace(old, new)
        self.fig.suptitle(title)
    
    def onpick(self, event):
        if self.status == 100: # default state with axes activated
            for i, cal_artists in enumerate(self.xcals):
                # print(cal_artists.values())
                # print(self.xcals)
                if event.artist in cal_artists.values():
                    self.textbox.set_active(True)
                    # print(i, self.ca['x_cal'])
                    self.textbox.set_val(self.ca['x_cal']['data'][i])
                    self.set_status(120)
                    self.fig.canvas.draw()
                    self.changecal_idx = i # index of the activage cal
                    return
                
            for i, cal_artists in enumerate(self.ycals):
                if event.artist in cal_artists.values():
                    self.textbox.set_active(True)
                    self.textbox.set_val(self.ca['y_cal']['data'][i])
                    self.set_status(121)
                    self.fig.canvas.draw()
                    self.changecal_idx = i # index of the activage cal
                    return
        
            for obj in self.objects['u']:
                if event.artist is obj['artist']: # is it an axis label?
                    x, y = obj['coords']
                    x, y = np.unique(x), np.unique(y)
                    if x.size == 1: # x-axis
                        self.x = x[0]
                        self.textbox.label.set_text('x value:')
                        self.textbox.set_active(True)
                        # self.textbox._rendercursor()
                        # self.textbox.begin_typing()
                        self.set_status(110)
                    elif y.size == 1: # y-axis
                        self.y = y[0]
                        self.textbox.label.set_text('x value:')
                        self.textbox.set_active(True)
                        # self.textbox._rendercursor()
                        # self.textbox.begin_typing()
                        self.set_status(111)
                    self.fig.canvas.draw()
                    return
                
    def onkeypress(self, event):
        if self.status == -1: # initial state
            if event.key in '0123456789': # axis number
                self.fig.suptitle('available axes numbers include: ' + ' '.join(self.axes.keys()))
        
            self.fig.canvas.draw()
    
    def _change_current_axis(self, n):
        self._ca = n
                    
        for pos, data in zip(self.ca['x_cal']['pos'], self.ca['x_cal']['data']):
            self.xcals.append(annotate(x=pos, xtxt=f'{data:.2g}', ax=self.ax0))
        for pos, data in zip(self.ca['y_cal']['pos'], self.ca['y_cal']['data']):
            self.ycals.append(annotate(y=pos, ytxt=f'{data:.2g}', ax=self.ax0))
        
        self.set_status(100)
        
        self.calibrate()
        self.plot_data()
        
    def _exit_current_axis(self):
        for cal in chain(self.xcals, self.ycals):
            for artist in cal.values():
                artist.remove()
        self.xcals.clear()
        self.ycals.clear()
        if self.select_rect is not None:
            self.select_rect.remove()
        self.select_rect = None
        self.set_status(-1)
        self.xscale = None
        self.yscale = None
    
    def onkeyrelease(self, event):
        if self.status == -1: # initial state
            if event.key in '0123456789': # axis number
                if event.key not in self.axes: 
                    self.set_status(-1)
                else: # load one saved axis
                    self._change_current_axis(event.key)
                    
            elif event.key == 'a':
                for n in '0123456789':
                    if n not in self.axes:
                        self.axes[n] = {
                            'x_cal': {
                                'pos': [], # x position on the plot
                                'data': [], # real data
                                },
                            'y_cal': {
                                'pos': [], # y position on the plot
                                'data': [], # real data
                                },
                            'xlim': [-np.inf, np.inf],
                            'ylim': [-np.inf, np.inf],
                            }
                        self._ca = n
                        self.set_status(100)
                        break
                else:
                    raise NotImplementedError('maximum number of axes exceeded')
            elif event.key == 's':
                self.save()
                self.fig.suptitle(f"axis information saved to '{self.savepath}'")
                plt.pause(2)
                self.set_status(self.status)
            elif event.key == 'e': # export all
                self.export()
                self.fig.suptitle(f"data exported to '{self.exportpath}'")
                plt.pause(2)
                self.set_status(self.status)
            self.fig.canvas.draw()
        elif self.status // 100 == 1: # in axis mode
            if self.status in [110, 111] and event.key == 'c':
                self.set_status(100)

            elif self.status in [120, 121]: # editing calibration
                if event.key == 'c': # cancel
                    pass
                elif event.key == 'd': # delete
                    i = self.changecal_idx
                    if self.status == 120:
                        self.ca['x_cal']['data'].pop(i)
                        self.ca['x_cal']['pos'].pop(i)
                        for artist in self.xcals.pop(i).values():
                            artist.remove()
                    elif self.status == 121:
                        self.ca['y_cal']['data'].pop(i)
                        self.ca['y_cal']['pos'].pop(i)
                        for artist in self.ycals.pop(i).values():
                            artist.remove()
                    self.calibrate()
                    self.plot_data()
                
                if event.key in 'cd':
                    self.textbox.set_active(False)
                    self.set_status(100)
                    self.textbox.set_val('')
            elif self.status == 100:
                if event.key == 'a': # set axis region
                    self.set_status(140)
                    with RectSelector(fig=self.fig) as rs:
                        rs.wait()
                    self.set_status(100)
                    
                    if self.select_rect is not None:
                        self.select_rect.remove()
                    self.select_rect = rs.rects[rs.ax] # the selection rectangle artist
                    self.ca['xlim'] = [rs.x0, rs.x1]
                    self.ca['ylim'] = [rs.y0, rs.y1]
                    
                    self.plot_data()
                elif event.key == 'u': # duplicate axis
                    for n in '0123456789':
                        if n not in self.axes:
                            self.axes[n] = deepcopy(self.ca)
                            self._next_axis = n
                            self.set_status(130)
                            break
                    else:
                        raise NotImplementedError('maximum number of axes exceeded')
                elif event.key == 'e': # export all
                    self.export()
                    self.fig.suptitle(f"data exported to '{self.exportpath}'")
                    plt.pause(2)
                    self.set_status(self.status)
            elif self.status == 130:
                if event.key == 'enter':
                    self._exit_current_axis()
                    self._change_current_axis(self._next_axis)
                
            if event.key == 'x': # exit axis
                self._exit_current_axis()
                
            elif event.key == 's':
                self.save()
                self.fig.suptitle(f"axis information saved to '{self.savepath}'")
                plt.pause(2)
                self.set_status(self.status)
            self.fig.canvas.draw()
            
    def onsubmit(self, expression):
        if self.status in [110, 111, 120, 121]:
            if self.status == 110: # setting x value
                xdata = eval(expression)
                if xdata != '':
                    self.ca['x_cal']['pos'].append(self.x)
                    self.ca['x_cal']['data'].append(xdata)
                    self.xcals.append(annotate(x=self.x, xtxt=f'{xdata:.2g}', ax=self.ax0))
            elif self.status == 111: # setting y value
                ydata = eval(expression)
                if ydata != '':
                    self.ca['y_cal']['pos'].append(self.y)
                    self.ca['y_cal']['data'].append(ydata)
                    self.ycals.append(annotate(y=self.y, ytxt=f'{ydata:.2g}', ax=self.ax0))
            elif self.status == 120: # editing x value
                xdata = eval(expression)
                if xdata != '':
                    self.ca['x_cal']['data'][self.changecal_idx] = xdata
                    self.xcals[self.changecal_idx]['vtext'].set_text(xdata)
            elif self.status == 121: # editing y value
                ydata = eval(expression)
                if ydata != '':
                    self.ca['y_cal']['data'][self.changecal_idx] = ydata
                    # print(self.ycals[self.changecal_idx]['htext'])
                    self.ycals[self.changecal_idx]['htext'].set_text(ydata)
            self.set_status(100)
            self.textbox.set_active(False)
            self.textbox.set_val('')
            
            self.calibrate()
            self.plot_data()

            self.fig.canvas.draw()
    
    def calibrate(self):
        self.xscale = None
        self.yscale = None
        # calibrate axes
        try:
            xs, xds = self.ca['x_cal']['pos'], self.ca['x_cal']['data']
            self.xk, self.xb, self.xscale = self.__class__.get_coeffs_auto(xs, xds)
            print(f'calibration: got {self.xk} x + {self.xb}, {self.xscale} scale')
        except ConsistencyError:
            errmsg = f'inconsistent calibration for x axis: {xs}, {xds}'
            self.fig.suptitle(f'ERROR: {errmsg}\nclick on calibration line to edit')
            print(errmsg)
            self.fig.canvas.draw()
        try:
            ys, yds = self.ca['y_cal']['pos'], self.ca['y_cal']['data']
            self.yk, self.yb, self.yscale = self.__class__.get_coeffs_auto(ys, yds)
            print(f'calibration: got {self.yk} y + {self.yb}, {self.yscale} scale')
            # print(self.yk, self.yb, self.yscale)
        except ConsistencyError:
            # print(ys, yds)
            errmsg = f'inconsistent calibration for y axis: {ys}, {yds}'
            self.fig.suptitle(f'ERROR: {errmsg}\nclick on calibration line to edit')
            print(errmsg)
            self.fig.canvas.draw()
           
    scale_func = {
        'linear': lambda x: x,
        'log': np.log10,
        } 
    scale_inv_func = {
        'linear': lambda x: x,
        'log': lambda x: 10**np.array(x),
        } 

    @classmethod
    def get_coeffs_auto(cls, xs, xds, err=1e-5):
        if len(xs) != len(xds):
            raise ValueError('expected xs, xds with the same shape')
        if len(xs) < 2:
            return None, None, None
        
        # automatically choose linear or log scale, and check consistency 
        for scale, xfunc in cls.scale_func.items():
            ks = np.diff(xfunc(xds)) / np.diff(xs)
            
            # 1: unique
            # k = np.unique(ks)
            # if k.size == 1:
            #     k = k[0]
            #     b = xds[0] - k * xs[0]
            #     return k, b, scale
                
            # 2: allow error
            k = np.mean(ks)
            if (np.max(ks) - np.min(ks)) / np.abs(k) < err:
                b = np.mean(xfunc(xds)[:-1] - ks * xs[:-1])
                return k, b, scale
                
        else:
            raise ConsistencyError(f"inconsistent data: {xs} and {xds}")
        
    @staticmethod
    def get_coeffs(x1, x2, xd1, xd2, scale='linear'):
        if scale == 'linear':
            pass
        elif scale == 'log':
            x1, x2 = np.log10(x1), np.log(x2)
        else:
            raise ValueError(f"unknown scale '{scale}'")
        
        k = (xd2 - xd1) / (x2 - x1)
        b = xd1 - k * x1
    
        return k, b
    
    def get_data(self):
        # get calibrated data
        x0, x1 = self.ca['xlim']
        y0, y1 = self.ca['ylim']
        selected = rect_filter_objects(self.objects, x0, x1, y0, y1, mode=self.select_mode)
        
        out_data = {'l': [], 's': []}
        out_info = {'l': [], 's': []}
        
        self.export_data[self._ca] = {'lines': [], 'scatters': []}
        typecode_translate = {'l': 'lines', 's': 'scatters'}
        
        for typ in ['l', 's']: # line, scatter
            for obj, sel in zip(self.objects[typ], selected[typ]):
                if sel:
                    data_coords = self.transform(*obj['coords'])
                    out_data[typ].append(data_coords)
                    info = {'linestyle': dedup(obj['artist'].get_linestyle()),
                            'linewidth': dedup(obj['artist'].get_linewidth())}
                    info.update(get_color(obj['artist']))
                    # if typ == 's':
                    #     info.update({'s': obj['artist'].get_sizes()})
                    out_info[typ].append(info)
                    
                    export_dict = {
                        'x': data_coords[0],
                        'y': data_coords[1],
                        }
                    export_dict.update(info)
                    self.export_data[self._ca][typecode_translate[typ]].append(export_dict)
                    
        # self.export_data[self._ca] = {
        #     'axis_number': self._ca,
        #     'lines_data': out_data['l'],
        #     'lines_info': out_info['l'],
        #     'scatters_data': out_data['s'],
        #     'scatters_info': out_info['s'],
        #     }
        return out_data, out_info
    
    def plot_data(self):
        # plot calibrated data
        if self.xscale is not None and self.yscale is not None:
            self.ax1.clear()
            out_data, out_info = self.get_data()
            # print(out_data, out_info)
            for (x, y), info in zip(out_data['s'], out_info['s']):
                self.ax1.scatter(x, y, fc=info['facecolor'], ec=info['edgecolor']) # , s=info['s']
            for (x, y), info in zip(out_data['l'], out_info['l']):
                self.ax1.plot(x, y, color=info['color'], linestyle=info['linestyle'], linewidth=info['linewidth'])
            self.ax1.set_xscale(self.xscale)
            self.ax1.set_yscale(self.yscale)
            self.ax1.grid()
        
    def transform(self, x, y):
        x, y = np.array(x), np.array(y)
        func = self.__class__.scale_inv_func
        return [func[self.xscale](self.xk * x + self.xb),
                func[self.yscale](self.yk * y + self.yb)]
    
    def save(self):
        # print(self.axes)
        with open(self.savepath, 'w') as f:
            json.dump(self.axes, f,
                      indent=2,
                      # default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x,
                      )
        print(f"axis information saved to '{self.savepath}'")
            
    def load(self):
        if not os.path.exists(self.savepath):
            return {}
        with open(self.savepath) as f:
            return json.load(f)
        
    def export(self):
        for ca in self.axes:
            self._ca = ca
            self.calibrate()
            if self.xscale and self.yscale:
                self.get_data()
        with open(self.exportpath, 'w') as f:
            json.dump(self.export_data, f,
                      default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x,
                      )
        print(f"data exported to '{self.exportpath}'")
        
            