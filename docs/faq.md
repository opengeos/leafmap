# FAQ

## How do I report an issue or make a feature request

Please go to <https://github.com/giswqs/leafmap/issues>.

## Why does leafmap use two plotting backends: folium and ipyleaflet

A key difference between [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium) is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input, while folium is meant for displaying static data only ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). Note that [Google Colab](https://colab.research.google.com/) currently does not support ipyleaflet ([source](https://github.com/googlecolab/colabtools/issues/60#issuecomment-596225619)). Therefore, if you are using leafmap
with Google Colab, you should use `import leafmap.foliumap as leafmap`. If you are using leafmap with a local Jupyter notebook server, you can
use `import leafmap`, which provides more functionalities for capturing user input (e.g., mouse-clicking and moving).

## Why the interactive map does not show up

If the interactive map does not show up on Jupyter notebook and JupyterLab, it is probably because the ipyleaflet extentsion is not installed properly.
For Jupyter notebook, try running the following two commands within your leafmap conda environment:

```
jupyter nbextension install --py --symlink --sys-prefix ipyleaflet
jupyter nbextension enable --py --sys-prefix ipyleaflet
```

For JupyterLab, try running the following command within your leafmap conda environment:

```
jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-leaflet

```

## How to use leafmap in countries where Google Services are blocked

If you are trying to use leafmap in coutries where Gooogle Services are blocked (e.g., China), you will need a VPN. Use `leafmap.set_proxy(port=your-port-number)` to connect to Google servers. Otherwise, you might encounter a connection timeout issue.

```python
import leafmap
leafmap.set_proxy(port=your-port-number)
m = leafmap.Map()
m
```
