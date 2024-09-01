# FAQ

## How do I report an issue or make a feature request

Please go to <https://github.com/opengeos/leafmap/issues>.

## What's the difference between folium and ipyleaflet

A key difference between [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium) is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input, while folium is meant for displaying static data only ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). Note that [Google Colab](https://colab.research.google.com/) currently does not support ipyleaflet ([source](https://github.com/googlecolab/colabtools/issues/498#issuecomment-695335421)). Therefore, if you are using leafmap
with Google Colab, `import leafmap` will automatically use the `folium` plotting backend. If you are using leafmap with Jupyter installed locally, `import leafmap` will automatically use the `ipyleaflet', which provides more functionalities for capturing user input (e.g., mouse-clicking and moving).

## How to use a specific plotting backend

`leafmap` has three plotting backends: [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), and [here-map-widget-for-jupyter](https://github.com/heremaps/here-map-widget-for-jupyter). If you are using `leafmap` with Jupyter installed locally, `import leafmap` will use the `ipyleaflet` plotting backend by default. If you are using `leafmap` with [Google Colab](https://colab.research.google.com/github/opengeos/leafmap/blob/master/docs/notebooks/01_leafmap_intro.ipynb), `import leafmap` will use the `folium` plotting backend by default. Note that Google Colab does not yet support `ipyleaflet` ([source](https://github.com/googlecolab/colabtools/issues/498#issuecomment-695335421)). Therefore, you won't be able to access the `leafmap` toolbar in Colab. Note that the backends do not offer equal functionality. Some interactive functionality in `ipyleaflet` might not be available in `folium` or `heremap`. To use a specific plotting backend, use one of the following:

-   `import leafmap.leafmap as leafmap`
-   `import leafmap.foliumap as leafmap`
-   `import leafmap.heremap as leafmap`

## Why the interactive map does not show up

If the interactive map does not show up on Jupyter Notebook and JupyterLab, it is probably because the [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) extension is not installed properly.
For example, you might receive an error message saying `Error displaying widget: model not found`. This a well-known issue related to ipyleaflet. See some relevant issues below.

-   [How to display map object using ipyleaflet in jupyter notebook or jupyter Lab](https://github.com/jupyter-widgets/ipyleaflet/issues/739)
-   [ipyleaflet does not work in jupyter lab - "Error displaying widget: model not found"](https://github.com/jupyter-widgets/ipyleaflet/issues/418)
-   [Error displaying widget: model not found](https://github.com/jupyter-widgets/ipyleaflet/issues/504)

Try some of the options below to resolve the issue. If the issue persists after trying these steps, you can open an issue on the [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet/issues) repository.

For Jupyter notebook, try running the following two commands within your leafmap conda environment:

```
jupyter nbextension install --py --symlink --sys-prefix ipyleaflet
jupyter nbextension enable --py --sys-prefix ipyleaflet
```

For JupyterLab, try running the following command within your leafmap conda environment:

```
jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-leaflet

```

Alternatively, you can run leafmap directly using binder:

-   <https://mybinder.org/v2/gh/opengeos/leafmap/HEAD>
-   <https://mybinder.org/v2/gh/opengeos/leafmap/HEAD>

## How to use leafmap in countries where Google Services are blocked

If you are trying to use leafmap in countries where Google Services are blocked (e.g., China), you will need a VPN. Use `leafmap.set_proxy(port=your-port-number)` to connect to Google servers. Otherwise, you might encounter a connection timeout issue.

```python
import leafmap
leafmap.set_proxy(port=your-port-number)
m = leafmap.Map()
m
```
