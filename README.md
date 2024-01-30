# vector-plot-extractor
tools for extracting data from vector plots

This Python package has been tested on various PDF files, including [example.pdf](examples/example.pdf), under normal usage conditions. However, it has not undergone comprehensive testing and optimization yet. I will improve it in the future. Your suggestions and contributions are welcome.

Documentation is currently in progress. Stay tuned for updates!

## Dependencies
This package mainly depends on the following packages:
- matplotlib
- numpy
- pymupdf

These will be automatically installed when running `pip install`.

## Installation
To install this package, you can simply use `pip`:
```
pip install vector-plot-extractor
```

If you would like to try the latest development version, you may directly install from the project repository by:
```
pip install git+https://github.com/ycwang-astro/vector-plot-extractor.git
```

## Usage
To execute the main UI, run this in your terminal
```
vpextract path/to/figure/file
```
To import this package in a Python script:
```Python
import vpextractor
```

## Notice
A bug in version 0.1.1 causes minor errors in the extracted scatter data. If you have used 0.1.1 version, follow the steps in the [changelog](CHANGELOG.md#012) ("Notes" under "0.1.2") to fix it.
