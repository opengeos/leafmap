# Welcome to leafmap

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)
[![image](https://binder.pangeo.io/badge_logo.svg)](https://binder.pangeo.io/v2/gh/giswqs/leafmap/master)
[![image](https://img.shields.io/pypi/v/leafmap.svg)](https://pypi.python.org/pypi/leafmap)
[![image](https://img.shields.io/conda/vn/conda-forge/leafmap.svg)](https://anaconda.org/conda-forge/leafmap)
[![image](https://pepy.tech/badge/leafmap)](https://pepy.tech/project/leafmap)
[![image](https://github.com/giswqs/leafmap/workflows/docs/badge.svg)](https://leafmap.gishub.org)
[![image](https://github.com/giswqs/leafmap/workflows/build/badge.svg)](https://github.com/giswqs/leafmap/actions?query=workflow%3Abuild)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![image](https://img.shields.io/badge/YouTube-Channel-red)](https://www.youtube.com/c/QiushengWu)
[![image](https://img.shields.io/twitter/follow/giswqs?style=social)](https://twitter.com/giswqs)

**A Python package for geospatial analysis and interactive mapping in a Jupyter environment.**

-   GitHub repo: <https://github.com/giswqs/leafmap>
-   Documentation: <https://leafmap.gishub.org>
-   PyPI: <https://pypi.org/project/leafmap>
-   Conda-forge: <https://anaconda.org/conda-forge/leafmap>
-   Leafmap tutorials on YouTube: <https://www.youtube.com/c/QiushengWu>
-   Free software: [MIT license](https://opensource.org/licenses/MIT)

## Introduction

**leafmap** is a Python package for geospatial analysis and interactive mapping in a Jupyter environment. It is a spin-off project of the [geemap](https://geemap.org) Python package, which was designed specifically to work with [Google Earth Engine](https://earthengine.google.com) (GEE). However, not everyone in the geospatial community has a GEE account. **leafmap** is designed to fill this gap for non-GEE users. It enables users to perform advanced geospatial analysis and interactive mapping with minimal coding in a Jupyter environment (e.g., Google Colab, JupyterLab, Jupyter notebook). It is built upon a number of open-source packages, such as [folium](https://github.com/python-visualization/folium) and [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) (for creating interactive maps), [WhiteboxTools](https://github.com/jblindsay/whitebox-tools) and [whiteboxgui](https://github.com/giswqs/whiteboxgui) (for analyzing geospatial data), and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets) (for designing interactive graphical user interface).

The [WhiteboxTools](https://github.com/jblindsay/whitebox-tools) library currently contains **447** tools, which are each grouped based on their main function into one of the following categories. For a list of available tools with comprehensive documentation and usage details, please see the [WhiteboxTools User Manual](https://jblindsay.github.io/wbt_book/available_tools/index.html).

-   [Data Tools](https://jblindsay.github.io/wbt_book/available_tools/data_tools.html)
-   [Geomorphometric Analysis](https://jblindsay.github.io/wbt_book/available_tools/geomorphometric_analysis.html)
-   [GIS Analysis](https://jblindsay.github.io/wbt_book/available_tools/gis_analysis.html)
-   [Hydrological Analysis](https://jblindsay.github.io/wbt_book/available_tools/hydrological_analysis.html)
-   [Image Analysis](https://jblindsay.github.io/wbt_book/available_tools/image_processing_tools.html)
-   [LiDAR Analysis](https://jblindsay.github.io/wbt_book/available_tools/lidar_tools.html)
-   [Mathematical and Statistical Analysis](https://jblindsay.github.io/wbt_book/available_tools/mathand_stats_tools.html)
-   [Stream Network Analysis](https://jblindsay.github.io/wbt_book/available_tools/stream_network_analysis.html)

Launch the interactive notebook tutorial for the **leafmap** Python package with Google Colab or Binder now:

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)
[![image](https://binder.pangeo.io/badge_logo.svg)](https://binder.pangeo.io/v2/gh/giswqs/leafmap/master)

## Key Features

Below is a partial list of features available for the leafmap package. Please check the [examples](https://github.com/giswqs/leafmap/tree/master/examples) page for notebook examples, GIF animations, and video tutorials.

-   Create an interactive map with only one-line of code.
-   Select from a variety of basemaps interactively without coding.
-   Add XYZ and WMS tile services to the map.
-   Convert CSV to points and display points as a marker cluster.
-   Add local vector data (e.g., shapefile, GeoJSON, KML) to the map without coding.
-   Add local raster data (e.g., GeoTIFF) to the map without coding.
-   Add Cloud Optimized GeoTIFF (COG) and SpatialTemporal Asset Catalog (STAC) to the map.
-   Add custom legends and colorbars to the map.
-   Perform geospatial analysis using WhiteboxTools and whiteboxgui.
-   Publish interactive maps with only one line of code.

## Demo

![](data/leafmap_demo.gif)

## YouTube Channel

I have created a [YouTube Channel](https://www.youtube.com/c/QiushengWu) for sharing geospatial tutorials. You can subscribe to my channel for regular updates. If there is any specific tutorial you would like to see, please submit a feature request [here](https://github.com/giswqs/leafmap/issues).

[![Earth Engine Tutorials on YouTube](https://wetlands.io/file/images/youtube.png)](https://www.youtube.com/c/QiushengWu)
