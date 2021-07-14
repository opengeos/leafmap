# Get Started

This Get Started guide is intended as a quick way to start programming with **leafmap**. You can try out leafmap by using Goolge Colab ([![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)) or Binder ([![image](https://binder.pangeo.io/badge_logo.svg)](https://gishub.org/leafmap-pangeo)) without having to install anything on your computer.

## Important Note

`leafmap` has three plotting backends: [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), and [here-map-widget-for-jupyter](https://github.com/heremaps/here-map-widget-for-jupyter). If you are using `leafmap` with Jupyter installed locally, `import leafmap` will automatically use the `ipyleaflet` plotting backend. If you are using `leafmap` with [Google Colab](https://githubtocolab.com/giswqs/leafmap/blob/master/examples/notebooks/01_leafmap_intro.ipynb), `import leafmap` will automatically use the `folium` plotting backend. Note that Google Colab does not yet support `ipyleaflet` ([source](https://github.com/googlecolab/colabtools/issues/498#issuecomment-695335421)). Therefore, you won't be able to access the `leafmap` toolbar in Colab. Note that the backends do not offer equal functionality. Some interactive functionality in `ipyleaflet` might not be available in `folium` or `heremap`. To use a specific plotting backend, use one of the following:

-   `import leafmap.leafmap as leafmap`
-   `import leafmap.foliumap as leafmap`
-   `import leafmap.heremap as leafmap`

## Launch Jupyter notebook

```bash
conda activate geo
jupyter notebook
```

## Use the ipyleaflet plotting backend

```python
import leafmap
```

## Use the folium plotting backend

```python
import leafmap.foliumap as leafmap
```

## Create an interactive map

```python
m = leafmap.Map(center=(40, -100), zoom=4)
m
```

## Use the heremap plotting backend

### Prerequisites

-   A HERE developer account, free and available under [HERE Developer Portal](https://developer.here.com)
-   An [API key](https://developer.here.com/documentation/identity-access-management/dev_guide/topics/dev-apikey.html) from the [HERE Developer Portal](https://developer.here.com)
-   Export API key into environment variable `HEREMAPS_API_KEY`

```bash
export HEREMAPS_API_KEY=YOUR-ACTUAL-API-KEY
```

```python
import leafmap.heremap as leafmap
```

### Create an interactive map

```python
import os
api_key = os.environ.get("HEREMAPS_API_KEY") # read api_key from environment variable.
m = leafmap.Map(api_key=api_key, center=(40, -100), zoom=4)
m
```

## Demo

![](data/leafmap_demo.gif)
