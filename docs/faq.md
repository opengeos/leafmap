# FAQ

## How do I report an issue or make a feature request

Please go to <https://github.com/opengeos/leafmap/issues>. When reporting a bug, include a minimal code example and the output of the following code so that the versions of leafmap and its dependencies are known:

```python
import leafmap
leafmap.Report()
```

## What's the difference between folium and ipyleaflet

A key difference between [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium) is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the front-end and the Python kernel, so the map can capture user input (e.g., mouse clicks and drawn shapes). Folium produces static HTML maps and is meant for displaying data only ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). As a result, the leafmap toolbar and interactive tools are only available with the ipyleaflet backend, while folium maps are easy to save as standalone HTML files and embed in web apps.

## How to use a specific plotting backend

`import leafmap` uses the `ipyleaflet` plotting backend by default, in Jupyter Notebook, JupyterLab, Google Colab and VS Code. In [marimo](https://github.com/marimo-team/marimo) notebooks, it uses the `folium` backend. To use a specific plotting backend, import its module explicitly:

-   `import leafmap.leafmap as leafmap` (ipyleaflet)
-   `import leafmap.foliumap as leafmap` (folium)
-   `import leafmap.maplibregl as leafmap` (MapLibre GL JS)
-   `import leafmap.deckgl as leafmap` (lonboard)
-   `import leafmap.deck as leafmap` (pydeck)
-   `import leafmap.kepler as leafmap` (kepler.gl)
-   `import leafmap.plotlymap as leafmap` (plotly)
-   `import leafmap.bokehmap as leafmap` (bokeh)

Note that the backends do not offer equal functionality. See [Get Started](get-started.md#plotting-backends) for a comparison.

## Why the interactive map does not show up

If the interactive map does not show up in Jupyter Notebook or JupyterLab, or you see an error such as `Error displaying widget: model not found`, the Jupyter widget front-end is usually out of sync with the Python packages. Modern versions of JupyterLab (4.x) and Notebook (7.x) install widget extensions automatically, so the old `jupyter nbextension` and `jupyter labextension install` commands are no longer needed.

Try the following steps:

1. Make sure `ipywidgets`, `ipyleaflet` and Jupyter are installed in the same environment as the kernel you are using, and upgrade them together:

    ```bash
    pip install -U ipywidgets ipyleaflet jupyterlab notebook
    ```

2. Restart the Jupyter server (not just the kernel) and hard-refresh the browser page.
3. Run `jupyter labextension list` and check that `jupyter-leaflet` and `@jupyter-widgets/jupyterlab-manager` are enabled.

If the issue persists, you can open an issue on the [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet/issues) repository, or try another backend such as `import leafmap.foliumap as leafmap`.

Alternatively, you can run leafmap directly in the cloud using [Google Colab](https://colab.research.google.com/github/opengeos/leafmap/blob/master) or [Binder](https://mybinder.org/v2/gh/opengeos/leafmap/HEAD).

## Why is the map center different between backends

The ipyleaflet, folium, plotly, kepler.gl and lonboard (`deckgl`) backends use `(latitude, longitude)` order for `center`, following the Leaflet convention. The MapLibre (`maplibregl`) backend uses `(longitude, latitude)`, following the MapLibre GL JS and GeoJSON convention. For example, the same view of the contiguous United States is `leafmap.Map(center=(40, -100))` with ipyleaflet and `leafmap.Map(center=(-100, 40))` with MapLibre.

## How do I save a map as an HTML file

Most backends provide a `to_html()` method:

```python
m = leafmap.Map()
m.to_html("map.html")
```

## How do I set API keys

Some basemaps and data sources require API keys, such as `MAPTILER_KEY` for MapTiler styles in the MapLibre backend or `GOOGLE_MAPS_API_KEY` for Google basemaps. Set them as environment variables before importing leafmap, since some keys (e.g., `GOOGLE_MAPS_API_KEY`) are read when the package is imported:

```python
import os
os.environ["MAPTILER_KEY"] = "your-api-key"

import leafmap.maplibregl as leafmap
```

In Google Colab, you can also store keys in the Colab Secrets panel. For keys looked up when a function is called (such as `MAPTILER_KEY`), leafmap checks Colab Secrets first and falls back to the environment variable. Google basemaps are the exception: `GOOGLE_MAPS_API_KEY` is only read from the environment when leafmap is imported, so copy it from Secrets into the environment first:

```python
import os
from google.colab import userdata

os.environ["GOOGLE_MAPS_API_KEY"] = userdata.get("GOOGLE_MAPS_API_KEY")

import leafmap
```

## How to use leafmap in countries where Google Services are blocked

If you are trying to use leafmap in countries where Google Services are blocked (e.g., China), you will need a VPN. Use `leafmap.set_proxy(port=your-port-number)` to connect to Google servers. Otherwise, you might encounter a connection timeout issue.

```python
import leafmap
leafmap.set_proxy(port=your-port-number)
m = leafmap.Map()
m
```
