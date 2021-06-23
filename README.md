# Welcome to leafmap

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)
[![image](https://binder.pangeo.io/badge_logo.svg)](https://gishub.org/leafmap-pangeo)
[![image](https://mybinder.org/badge_logo.svg)](https://gishub.org/leafmap-binder)
[![image](https://img.shields.io/pypi/v/leafmap.svg)](https://pypi.python.org/pypi/leafmap)
[![image](https://img.shields.io/conda/vn/conda-forge/leafmap.svg)](https://anaconda.org/conda-forge/leafmap)
[![image](https://pepy.tech/badge/leafmap)](https://pepy.tech/project/leafmap)
[![image](https://github.com/giswqs/leafmap/workflows/docs/badge.svg)](https://leafmap.org)
[![image](https://github.com/giswqs/leafmap/workflows/build/badge.svg)](https://github.com/giswqs/leafmap/actions?query=workflow%3Abuild)
[![image](https://img.shields.io/lgtm/grade/python/g/giswqs/leafmap.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/giswqs/leafmap/context:python)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![image](https://img.shields.io/badge/YouTube-Channel-red)](https://www.youtube.com/c/QiushengWu)
[![image](https://img.shields.io/twitter/follow/giswqs?style=social)](https://twitter.com/giswqs)

**A Python package for geospatial analysis and interactive mapping in a Jupyter environment.**

-   GitHub repo: <https://github.com/giswqs/leafmap>
-   Documentation: <https://leafmap.org>
-   PyPI: <https://pypi.org/project/leafmap>
-   Conda-forge: <https://anaconda.org/conda-forge/leafmap>
-   Leafmap tutorials on YouTube: <https://www.youtube.com/c/QiushengWu>
-   Free software: [MIT license](https://opensource.org/licenses/MIT)

## Introduction

**Leafmap** is a Python package for interactive mapping and geospatial analysis with minimal coding in a Jupyter environment. It is a spin-off project of the [geemap](https://geemap.org) Python package, which was designed specifically to work with [Google Earth Engine](https://earthengine.google.com) (GEE). However, not everyone in the geospatial community has access to the GEE cloud computing platform. Leafmap is designed to fill this gap for non-GEE users. It is a free and open-source Python package that enables users to analyze and visualize geospatial data with minimal coding in a Jupyter environment, such as Google Colab, Jupyter notebook, and JupyterLab. Leafmap is built upon a number of open-source packages, such as [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), and [here-map-widget-for-jupyter](https://github.com/heremaps/here-map-widget-for-jupyter) (for creating interactive maps), [WhiteboxTools](https://github.com/jblindsay/whitebox-tools) and [whiteboxgui](https://github.com/giswqs/whiteboxgui) (for analyzing geospatial data), and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets) (for designing interactive graphical user interface [GUI]). The WhiteboxTools library currently contains **470+** tools for advanced geospatial analysis, which are each grouped based on their main function into one of the following categories. Users can access these tools via whiteboxgui directly within the leafmap user interface without writing a single line of code.

-   [Data Tools](https://jblindsay.github.io/wbt_book/available_tools/data_tools.html)
-   [Geomorphometric Analysis](https://jblindsay.github.io/wbt_book/available_tools/geomorphometric_analysis.html)
-   [GIS Analysis](https://jblindsay.github.io/wbt_book/available_tools/gis_analysis.html)
-   [Hydrological Analysis](https://jblindsay.github.io/wbt_book/available_tools/hydrological_analysis.html)
-   [Image Processing Tools](https://jblindsay.github.io/wbt_book/available_tools/image_processing_tools.html)
-   [LiDAR Tools](https://jblindsay.github.io/wbt_book/available_tools/lidar_tools.html)
-   [Mathematical and Statistical Analysis](https://jblindsay.github.io/wbt_book/available_tools/mathand_stats_tools.html)
-   [Precision Agriculture](https://jblindsay.github.io/wbt_book/available_tools/precision_agriculture.html)
-   [Stream Network Analysis](https://jblindsay.github.io/wbt_book/available_tools/stream_network_analysis.html)

## Statement of Need

There are a plethora of Python packages for geospatial analysis, such as [geopandas](https://github.com/geopandas/geopandas) for vector data analysis and [xarray](https://github.com/pydata/xarray) for raster data analysis. However, few Python packages provide interactive GUIs for loading and visualizing geospatial data in a Jupyter environment. It might take many lines to code to load and display geospatial data with various file formats on an interactive map, which can be a challenging task for novice users with limited coding skills. Leafmap provides many convenient functions for loading and visualizing geospatial datasets with only one line of code. Users can also use the interactive GUI to load geospatial datasets without coding. Anyone with a web browser and Internet connection can use leafmap to perform geospatial analysis and data visualization in the cloud with minimal coding.

Launch the interactive notebook tutorial for the **leafmap** Python package with Google Colab or Binder now:

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)
[![image](https://binder.pangeo.io/badge_logo.svg)](https://binder.pangeo.io/v2/gh/giswqs/leafmap/master)

Check out this excellent article on Medium - [Leafmap a new Python Package for Geospatial data science](https://link.medium.com/HRRKDcynYgb)

To learn more about leafmap, check out the leafmap documentation website - <https://leafmap.org>

![](https://i.imgur.com/abd8pTH.gif)

## Key Features

Below is a partial list of features available for the leafmap package. Please check the [examples](https://github.com/giswqs/leafmap/tree/master/examples) page for notebook examples, GIF animations, and video tutorials.

-   Create an interactive map with only one-line of code.
-   Select from a variety of basemaps interactively without coding.
-   Add XYZ, WMS, and vector tile services to the map.
-   Convert CSV to points and display points as a marker cluster.
-   Add local vector data (e.g., shapefile, GeoJSON, KML) to the map without coding.
-   Add local raster data (e.g., GeoTIFF) to the map without coding.
-   Add Cloud Optimized GeoTIFF (COG) and SpatialTemporal Asset Catalog (STAC) to the map.
-   Add OpenStreetMap data to the map with a single line of code.
-   Add a GeoPandas GeoDataFrame to the map with a single line of code.
-   Add a point layer with popup attributes to the map.
-   Add data from a PostGIS database to the map.
-   Add custom legends and colorbars to the map.
-   Perform geospatial analysis using WhiteboxTools and whiteboxgui.
-   Create split-panel map and linked maps.
-   Publish interactive maps with a single line of code.
-   Download and display OpenStreetMap data with a single line of code.

## Demo

![](https://wetlands.io/file/images/leafmap_demo.gif)

## YouTube Channel

I have created a [YouTube Channel](https://www.youtube.com/c/QiushengWu) for sharing geospatial tutorials. You can subscribe to my channel for regular updates. If there is any specific tutorial you would like to see, please submit a feature request [here](https://github.com/giswqs/leafmap/issues).

[![Earth Engine Tutorials on YouTube](https://wetlands.io/file/images/youtube.png)](https://www.youtube.com/c/QiushengWu)
