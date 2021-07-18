# Get Started

This Get Started guide is intended as a quick way to start programming with **leafmap**. You can try out leafmap by using Goolge Colab ([![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)) or Binder ([![image](https://binder.pangeo.io/badge_logo.svg)](https://gishub.org/leafmap-pangeo)) without having to install anything on your computer.

## Important Note

The `leafmap` package has three plotting backends, including [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), and [heremap](https://github.com/heremaps/here-map-widget-for-jupyter). An interactive map created using one of the plotting backends can be displayed in a Jupyter environment, such as Google Colab, Jupyter Notebook, and JupyterLab. By default, `import leafmap` in [Jupyter Notebook](https://gishub.org/leafmap-pangeo) and [JupyterLab](https://gishub.org/leafmap-binder) will use the `ipyleaflet` plotting backend, whereas `import leafmap` in [Google Colab](https://gishub.org/leafmap-colab) will use the `folium` plotting backend. Note that Google Colab does not yet support custom widgets, such as `ipyleaflet` and `heremap` ([source](https://github.com/googlecolab/colabtools/issues/498#issuecomment-695335421)). Therefore, interactive maps created using the `ipyleaflet` and `heremap` backends won't show up in Google Colab, even though the code might run successfully without any errors.

The three plotting backends do not offer equal functionality. The `ipyleaflet` plotting backend provides the richest interactive functionality, including the custom toolbox for loading, analyzing, and visualizing geospatial data interactively without coding. For example, users can add vector data (e.g., GeoJSON, Shapefile, KML, GeoDataFrame) and raster data (e.g., GeoTIFF, Cloud Optimized GeoTIFF) to the map with a few clicks. Users can also perform geospatial analysis using the WhiteboxTools GUI with 470+ geoprocessing tools directly within the map interface. Other interactive functionality (e.g., split-panel map, linked map, time slider, time-series inspector) can also be useful for visualizing geospatial data. The `ipyleaflet` package is built upon `ipywidgets` and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). In contrast, `folium` has relatively limited interactive functionality. It is meant for displaying static data only. The `folium` plotting backend is included in this package to support using `leafmap` in Google Colab. Note that the aforementioned custom toolbox and interactive functionality are not available for the `folium` plotting backend. Compared with `ipyleaflet` and `folium`, the `heremap` plotting backend provides some unique [3D functionality](https://github.com/heremaps/here-map-widget-for-jupyter#use-ipywidgets-controls-to-build-an-interactive-gui) for visualizing geospatial data. An [API key](https://developer.here.com/documentation/identity-access-management/dev_guide/topics/dev-apikey.html) from the [Here Developer Portal](https://developer.here.com/) is required to use `heremap`.

To use a specific plotting backend, use one of the following:

-   `import leafmap.leafmap as leafmap`
-   `import leafmap.foliumap as leafmap`
-   `import leafmap.heremap as leafmap`

## Launch Jupyter notebook

```bash
conda activate env_name
jupyter notebook
```

## Use ipyleaflet plotting backend

```python
import leafmap
m = leafmap.Map(center=(40, -100), zoom=4)
m
```

![](https://i.imgur.com/CUtzD19.png)

## Use folium plotting backend

```python
import leafmap.foliumap as leafmap
m = leafmap.Map(center=(40, -100), zoom=4)
m
```

![](https://i.imgur.com/cwdskMb.png)

## Use heremap plotting backend

### Prerequisites

-   A HERE developer account, free and available under [HERE Developer Portal](https://developer.here.com)
-   An [API key](https://developer.here.com/documentation/identity-access-management/dev_guide/topics/dev-apikey.html) from the [HERE Developer Portal](https://developer.here.com)
-   Export API key into environment variable `HEREMAPS_API_KEY`

```bash
export HEREMAPS_API_KEY=YOUR-ACTUAL-API-KEY
```

### Create an interactive map

```python
import os
import leafmap.heremap as leafmap
os.environ["HEREMAPS_API_KEY"] = "YOUR_HEREMAPS_API_KEY"
api_key = os.environ.get("HEREMAPS_API_KEY") # read api_key from environment variable.
m = leafmap.Map(api_key=api_key, center=(40, -100), zoom=4)
m
```

![](https://i.imgur.com/TWfgHsV.png)

## Leafmap demo with ipyleaflet backend

![](data/leafmap_demo.gif)
