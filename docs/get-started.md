# Get Started

This Get Started guide is intended as a quick way to start programming with **leafmap**. You can try out leafmap by using Goolge Colab ([![image](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/opengeos/leafmap/blob/master)) or Binder ([![image](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/opengeos/leafmap/HEAD)) without having to install anything on your computer.

## Important Note

**Leafmap** has six plotting backends, including [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), [plotly](https://plotly.com/), [pydeck](https://deckgl.readthedocs.io/en/latest/), [kepler.gl](https://docs.kepler.gl/docs/keplergl-jupyter), and [heremap](https://github.com/heremaps/here-map-widget-for-jupyter). An interactive map created using one of the plotting backends can be displayed in a Jupyter environment, such as Google Colab, Jupyter Notebook, and JupyterLab. By default, `import leafmap` will use the `ipyleaflet` plotting backend.

The six plotting backends do not offer equal functionality. The `ipyleaflet` plotting backend provides the richest interactive functionality, including the custom toolset for loading, analyzing, and visualizing geospatial data interactively without coding. For example, users can add vector data (e.g., GeoJSON, Shapefile, KML, GeoDataFrame) and raster data (e.g., GeoTIFF, Cloud Optimized GeoTIFF [COG]) to the map with a few clicks (see Figure 1). Users can also perform geospatial analysis using the WhiteboxTools GUI with 468 geoprocessing tools directly within the map interface (see Figure 2). Other interactive functionality (e.g., split-panel map, linked map, time slider, time-series inspector) can also be useful for visualizing geospatial data. The `ipyleaflet` package is built upon `ipywidgets` and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). In contrast, `folium` has relatively limited interactive functionality. It is meant for displaying static data only. Note that the aforementioned custom toolset and interactive functionality are not available for other plotting backends. Compared with `ipyleaflet` and `folium`, the `pydeck`, `kepler.gl`, and `heremap` plotting backend provides some unique 3D mapping functionality. An [API key](https://developer.here.com/documentation/identity-access-management/dev_guide/topics/dev-apikey.html) from the [Here Developer Portal](https://developer.here.com/) is required to use `heremap`.

To choose a specific plotting backend, use one of the following:

-   `import leafmap.leafmap as leafmap`
-   `import leafmap.foliumap as leafmap`
-   `import leafmap.deck as leafmap`
-   `import leafmap.kepler as leafmap`
-   `import leafmap.plotlymap as leafmap`
-   `import leafmap.heremap as leafmap`

![](https://i.imgur.com/pe7CoC7.png)
**Figure 1.** The leafmap user interface built upon ipyleaflet and ipywidgets.

![](https://i.imgur.com/5GzDG3W.png)
**Figure 2.** The WhiteboxTools graphical user interface integrated into leafmap.

## Leafmap Modules

The key functionality of the leafmap Python package is organized into nine modules as shown in the table below.

| Module    | Description                                                                   |
| --------- | ----------------------------------------------------------------------------- |
| basemaps  | A collection of XYZ and WMS tile layers to be used as basemaps                |
| colormaps | Commonly used colormaps and palettes for visualizing geospatial data          |
| common    | Functions being used by multiple plotting backends to process geospatial data |
| foliumap  | A plotting backend built upon the folium Python package                       |
| heremap   | A plotting backend built upon the here-map-widget-for-jupyter                 |
| kepler    | A plotting backend built upon keplergl Python package                         |
| leafmap   | The default plotting backend built upon the ipyleaflet Python package         |
| legends   | Built-in legends for commonly used geospatial datasets                        |
| osm       | Functions for extracting and downloading OpenStreetMap data                   |
| pc        | Functions for working with Microsoft Planetary Computer                       |
| plotlymap | A plotting backend built upon plotly Python package                           |
| pydeck    | A plotting backend built upon pydeck Python package                           |
| toolbar   | A custom toolset with interactive tools built upon ipywidgets and ipyleaflet  |

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

![](https://assets.gishub.org/images/leafmap_demo.gif)
