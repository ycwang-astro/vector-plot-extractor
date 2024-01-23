# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 16:39:26 2024

@author: Yu-Chen Wang
"""

from setuptools import setup, find_packages
import vpextractor

setup(
    name='vector-plot-extractor',
    version=vpextractor.__version__,
    packages=find_packages(include=['vpextractor', 'vpextractor.*']),
    install_requires=[
        'matplotlib',
        'numpy',
        'pymupdf',
        ],
    entry_points={
        'console_scripts': [
            'vpextract = vpextractor:vpextract',
            ],
        },
)

