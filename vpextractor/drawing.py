# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 15:51:36 2024

@author: Yu-Chen Wang

parse drawings, converting them to matplotlib objects
"""

import numpy as np
from matplotlib.patches import Polygon, Rectangle, PathPatch, Patch
from matplotlib.lines import Line2D
from matplotlib.collections import PatchCollection, PathCollection, LineCollection
from matplotlib.path import Path
from matplotlib.colors import to_rgba
import matplotlib.pyplot as plt
import warnings
from copy import copy
from .filter import select_paths
from .utils import dedup

def add(ax, artist):
    # add artist to ax given different types
    if isinstance(artist, Patch):
        ax.add_patch(artist)
    elif isinstance(artist, (Line2D)):
        ax.add_line(artist)
    elif isinstance(artist, (PatchCollection, LineCollection)):
        ax.add_collection(artist)
    # elif isinstance(artist, PathCollection):
    #     ax.add_artist(artist)
    else:
        raise TypeError(type(artist))

def get_color(artist):
    # get color from artist
    if isinstance(artist, (Line2D)):
        return {'color': (artist.get_color())}
    elif isinstance(artist, PatchCollection):
        return {'facecolor': dedup(artist.get_facecolor()),
                'edgecolor': dedup(artist.get_edgecolor())}
    elif isinstance(artist, LineCollection): # this is a collection of lines as markers of scatter
        return {'facecolor': dedup(artist.get_color()),
                'edgecolor': None}
    else:
        raise TypeError(type(artist))

def parse_path(path):
    '''
    

    Parameters
    ----------
    path : dict
        .

    Returns
    -------
    item_type : 
        .
    coords : 
        .
    artist : 
        .

    '''
    items = path['items']
    item_type = np.unique([item[0] for item in items])
    item_type = set(str(i) for i in item_type)
    coords = get_coords(items)
    patch_kwargs = dict(
        fill=False,
        closed=path['closePath'],
        )
    if 's' in path['type']: # stroke
        patch_kwargs.update(dict(
            ec=path['color'], # edgecolor
            alpha=path['stroke_opacity'],
            lw=path['width'], # linewidth
            # closed=path['closePath'], 
            ls=get_ls(path['dashes']), # linestyle
            ))
    if 'f' in path['type']: # fill
        patch_kwargs.update(dict(
            fill=True,
            fc=path['fill'], # facecolor
            alpha=path['fill_opacity'],
            ))
    if item_type in [{'c'}, {'c', 'l'}]:  # Bezier curve, or combination of Bezier curve & line
        itempath = get_curv_path(items)
        patch_kwargs.pop('closed') # TODO: manually handle this: add the starting point at the end (if not)
        artist = PathPatch(itempath, **patch_kwargs)
    elif item_type == {'l'}: # line
        if (path['closePath'] or 'f' in path['type']) and len(coords[0]) > 2:  # closed path or fill, and more than 2 pts (if only 2 pts, it is still a line)
            artist = Polygon(np.vstack(coords).T, **patch_kwargs)
        else: # not a closed path, and not fill: seems to be a line
            patch_kwargs.pop('closed') 
            patch_kwargs.pop('fill') 
            if 'fc' in patch_kwargs:
                patch_kwargs.pop('fc')
            patch_kwargs['color'] = patch_kwargs.pop('ec') 
            # patch_kwargs['lw'] = min((2, patch_kwargs['lw']))
            x, y = coords
            artist = Line2D(x, y, **patch_kwargs) #, picker=True, pickradius=5
    elif item_type == {'re'}:
        assert len(items) == 1
        item = items[0]
        rect = item[1]
        patch_kwargs.pop('closed') # TODO: manually handle this: add the starting point at the end (if not)
        # notes: the coordinates for fitz.fitz.Rect is UPSIDE DOWN, so `rect.tl` ("top-left") is the real "bottom-left" (smaller x, smaller y) in Matplotlib
        # see https://pymupdf.readthedocs.io/en/latest/rect.html
        artist = Rectangle(rect.tl, rect.width, rect.height, **patch_kwargs)
    elif item_type == {'qu'}:
        artist = Polygon(np.vstack(coords).T, **patch_kwargs)
    else:
        raise NotImplementedError(f'not implemented for item_type {item_type}')
    
    x, y = coords
    x, y = np.array(x), np.array(y)
    rel_pt = np.argmin(x)
    x_rel, y_rel = x[rel_pt], y[rel_pt]
    path_feature = { # features of the path used to identify similar paths
        'rel_pos': np.array([x - x_rel, y - y_rel]), # relative positions
        'type': '+'.join(item_type),
        'color': np.array(path['color']),
        'fill': np.array(path['fill']),
        }
    
    artist.set_picker(True)
    
    return item_type, coords, artist, path_feature

def plot_path(path, ax=None):
    if ax is None:
        ax = plt.gca()
        
    item_type, coords, artist, _ = parse_path(path)
    xs, ys = coords
    # if item_type == 'l':
    #     ax.plot(xs, ys)
    # elif item_type in ['c', 're', 'qu']:
    #     add(ax, artist)
    # else:
    #     raise ValueError(f"unrecognized type '{item_type}'")
    add(ax, artist)
        
    # ax.autoscale_view()
    ax.autoscale()
    ax.invert_yaxis()
    
def plot_paths(paths, ax=None):
    if ax is None:
        ax = plt.gca()
        
    artists = [] # the original artists
    artists_in_plot = [] # the artists made in plot (once an artist is added, it can never be added to somewhere else)
    path_features = []
    for path in paths:
        item_type, coords, artist, path_feature = parse_path(path)
        artists.append(artist)
        path_features.append(path_feature)
        artist_in_plot = copy(artist)
        add(ax, artist_in_plot)
        # print(artist_in_plot.pickable())
        artists_in_plot.append(artist_in_plot)
    
    ax.autoscale()
    ax.invert_yaxis()
    # ax.set_aspect('equal')
    
    return artists, artists_in_plot, path_features

def get_coords(items):
    # get points that the shape goes through
    xs = []
    ys = []
    x, y = None, None
    for item in items:
        if item[0] == 'c': # Bezier curve
            pts = item[1:]
            if len(pts) == 4: # cubic
                pts = [pts[0], pts[3]]
            else:
                raise NotImplementedError()
            for pt in pts:
                if (x, y) == (pt.x, pt.y):
                    continue
                x, y = pt.x, pt.y
                xs.append(x)
                ys.append(y)
        elif item[0] == 're': #rectangle
            rect = item[1]
            x0, x1, y0, y1 = rect.x0, rect.x1, rect.y0, rect.y1
            xs += [x0, x1, x1, x0, x0]
            ys += [y0, y0, y1, y1, y0]
        elif item[0] == 'qu': # quad
            quad = item[1]
            pts = [quad.ul, quad.ur, quad.lr, quad.ll]
            for pt in pts:
                if (x, y) == (pt.x, pt.y):
                    continue
                x, y = pt.x, pt.y
                xs.append(x)
                ys.append(y)
        elif item[0] == 'l':
            pts = item[1:]
            for pt in pts:
                if (x, y) == (pt.x, pt.y):
                    continue
                x, y = pt.x, pt.y
                xs.append(x)
                ys.append(y)
        else:
            raise NotImplementedError()
    
    return xs, ys

def get_curv_path(items):
    # get matplotlib.path.Path object
    # this should not be used if the item type for a path is only 'l': should treat is as normal Polygon or Line2D
    path_data = []
    endx, endy = None, None
    for item in items:
        pts = item[1:]
        # firstcode = Path.LINETO if len(path_data) > 0 else Path.MOVETO
        firstcode = Path.LINETO if (endx, endy) == (pts[0].x, pts[0].y) else Path.MOVETO
        if item[0] == 'c': # Bezier curve
            if len(pts) == 4: # cubic
                path_data += [
                    (firstcode, (pts[0].x, pts[0].y)),
                    (Path.CURVE4, (pts[1].x, pts[1].y)),
                    (Path.CURVE4, (pts[2].x, pts[2].y)),
                    (Path.CURVE4, (pts[3].x, pts[3].y)),
                    ]
                endx, endy = (pts[3].x, pts[3].y)
            else:
                raise NotImplementedError('only implemented cubic Bezier curve')
        elif item[0] == 'l': # line
            assert len(pts) == 2
            path_data += [
                (firstcode, (pts[0].x, pts[0].y)),
                (Path.LINETO, (pts[1].x, pts[1].y)),
                ]
            endx, endy = (pts[1].x, pts[1].y)
        else:
            raise ValueError(f"unexpected item type '{item[0]}'")
    
    codes, verts = zip(*path_data)
    path = Path(verts, codes)
    return path

def get_ls(s):
    if s in ["[] 0", None, ""]:
        return '-'
    else:
        return '--' # TODO: handle dash styles

def analyze_marker():
    raise NotImplementedError() # analyze the center of it 

def mean_getter(coords):
    xs, ys = coords
    # since the first and last coord generated by get_coords() *may* be the same, we need to remove this duplication
    if (xs[0], ys[0]) == (xs[-1], ys[-1]):
        xs, ys = xs[:-1], ys[:-1]
    _, counts = np.unique(np.array((xs, ys)), axis=-1, return_counts=True)
    assert np.max(counts) == 1 # there should not be any duplicate point now!
    return np.mean(xs), np.mean(ys)

def group_paths(paths, typestr=None, markers=None, marker_getter='mean', mode='typestr'):
    # marker_getter: method to get the position of the marker if arg `marker` do not contain center information
    if marker_getter == 'mean': #simply use mean of coords as position
        marker_getter = mean_getter
    else:
        return ValueError()
    
    if mode == 'typestr': # simply group using typestr
        if typestr is None:
            raise ValueError('expected argument "typestr" for "mode=typestr"')
        if markers is None:
            raise ValueError('expected argument "markers" for "mode=typestr"')
        marker_features = [marker['feature'] for marker in markers]
        match_modes = [marker['match_by'] for marker in markers]
        objects = {
            'u': [], # undefined
            's': [], # scatter
            'l': [], # line
            'o': [], # other objects
            }
        scatter = False
        scatter_artists = []
        idx0 = -1
        scatter_coords = []
        for path, typ in zip(paths, typestr):
            item_type, coords, artist, path_feature = parse_path(path)

            if typ == 's':
                idx = select_paths(path_feature, marker_features, match_modes)
                # if len(idx) != 1:
                #     pass
                assert len(idx) == 1, idx
                idx = idx[0]
    
            if scatter and (typ != 's' or idx != idx0): # ends a group of scatter
                artists_type = list({type(a) for a in scatter_artists})
                if len(artists_type) > 1:
                    raise TypeError(f'expected one single type for a collection of scatter, got {artists_type}')
                artists_type = artists_type[0]
                if artists_type == Line2D:
                    warnings.warn(f'a group of {len(scatter_artists)} line-like objects marked as scatters')
                    lc_kwargs = { # LineCollection kwargs
                        'linewidths': [l.get_linewidth() for l in scatter_artists],
                        'colors': [to_rgba(l.get_color(), l.get_alpha()) for l in scatter_artists],
                        'linestyles': [l.get_linestyle() for l in scatter_artists],
                        }
                    collection = LineCollection((a.get_xydata() for a in scatter_artists), **lc_kwargs)
                else:
                    collection = PatchCollection(scatter_artists, match_original=True)
                objects['s'].append({
                    'artist': collection, # todo: what if user mark line as scatter? should disallow it!
                    'coords': np.array(scatter_coords).T})
                scatter = False
                idx0 = -1
                scatter_artists.clear()
                scatter_coords.clear()
            
            if typ == 's':
                scatter = True
                idx0 = idx
                scatter_artists.append(artist)
                scatter_coords.append(marker_getter(coords))
    
            elif typ in ['u', 'l', 'o']:
                objects[typ].append({'artist': artist,
                                     'coords': coords})
            elif typ == 'd':
                continue
                
    else:
        raise ValueError
    
    return objects

def plot_objects(objects, ax=None):
    # plot grouped objects
    
    if ax is None:
        ax = plt.gca()
    
    for typ, typ_objs in objects.items():
        for obj in typ_objs:
            add(ax, obj['artist'])
            
    ax.autoscale()
    ax.invert_yaxis()

