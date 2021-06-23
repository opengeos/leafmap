---
title: "Leafmap: A Python package for interactive mapping and geospatial analysis with minimal coding in a Jupyter environment"
tags:
    - Python
    - geospatial
    - ipyleaflet
    - mapping
    - Jupyter
authors:
    - name: Qiusheng Wu
      orcid: 0000-0001-5437-4073
      affiliation: "1"
affiliations:
    - name: Department of Geography, University of Tennessee, Knoxville, TN 37996, United States
      index: 1
date: 22 June 2021
bibliography: paper.bib
---

# Summary

**Leafmap** is a Python package for interactive mapping and geospatial analysis with minimal coding in a Jupyter environment. It is a spin-off project of the [geemap](https://geemap.org) Python package [@Wu2020], which was designed specifically to work with [Google Earth Engine](https://earthengine.google.com) (GEE) [@Gorelick2017]. However, not everyone in the geospatial community has access to the GEE cloud computing platform. Leafmap is designed to fill this gap for non-GEE users. It is a free and open-source Python package that enables users to analyze and visualize geospatial data with minimal coding in a Jupyter environment, such as Google Colab, Jupyter notebook, and JupyterLab. Leafmap is built upon a number of open-source packages, such as [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), and [here-map-widget-for-jupyter](https://github.com/heremaps/here-map-widget-for-jupyter) (for creating interactive maps), [WhiteboxTools](https://github.com/jblindsay/whitebox-tools) [@Lindsay2018] and [whiteboxgui](https://github.com/giswqs/whiteboxgui) (for analyzing geospatial data), and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets) (for designing interactive graphical user interface [GUI]). The WhiteboxTools library currently contains **470+** tools for advanced geospatial analysis, which are each grouped based on their main function into one of the following categories. Users can access these tools via whiteboxgui directly within the leafmap user interface without writing a single line of code.

-   [Data Tools](https://jblindsay.github.io/wbt_book/available_tools/data_tools.html)
-   [Geomorphometric Analysis](https://jblindsay.github.io/wbt_book/available_tools/geomorphometric_analysis.html)
-   [GIS Analysis](https://jblindsay.github.io/wbt_book/available_tools/gis_analysis.html)
-   [Hydrological Analysis](https://jblindsay.github.io/wbt_book/available_tools/hydrological_analysis.html)
-   [Image Processing Tools](https://jblindsay.github.io/wbt_book/available_tools/image_processing_tools.html)
-   [LiDAR Tools](https://jblindsay.github.io/wbt_book/available_tools/lidar_tools.html)
-   [Mathematical and Statistical Analysis](https://jblindsay.github.io/wbt_book/available_tools/mathand_stats_tools.html)
-   [Precision Agriculture](https://jblindsay.github.io/wbt_book/available_tools/precision_agriculture.html)
-   [Stream Network Analysis](https://jblindsay.github.io/wbt_book/available_tools/stream_network_analysis.html)

# Statement of Need

There are a plethora of Python packages for geospatial analysis, such as geopandas for vector data analysis [@Jordahl2014] and xarray for raster data analysis [@Hoyer2017]. However, few Python packages provide interactive GUIs for loading and visualizing geospatial data in a Jupyter environment. It might take many lines to code to load and display geospatial data with various file formats on an interactive map, which can be a challenging task for novice users with limited coding skills. Leafmap provides many convenient functions for loading and visualizing geospatial datasets with only one line of code. Users can also use the interactive GUI to load geospatial datasets without coding. Anyone with a web browser and Internet connection can use leafmap to perform geospatial analysis and data visualization in the cloud with minimal coding.

# Leafmap Tutorials

Various tutorials and documentation are available for using leafmap, including:

-   [Complete API documentation on leafmap modules and methods](https://leafmap.org)
-   [20+ notebook examples for using leafmap with Google Colab and Jupyter](https://leafmap.org/tutorials)
-   [Video tutorials for using leafmap](https://gishub.org/youtube-leafmap)

# Acknowledgements

The author would like to thank the developers of ipyleaflet and ipywidgets, which empower the interactive mapping functionality of leafmap, including [Martin Renou](https://github.com/martinRenou), [David Brochart](https://github.com/davidbrochart), and [Sylvain Corlay](https://github.com/SylvainCorlay). The authors would also like to express thanks to [John Lindsay](https://github.com/jblindsay) for developing the WhiteboxTools library, which serves as the geospatial analysis backend of leafmap. Special thanks go to all leafmap contributors, especially [Sachin Kharude](https://github.com/sackh) for contributing the heremap plotting backend to leafmap.

# References
