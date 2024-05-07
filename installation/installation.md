# Installation

## Install from PyPI

**leafmap** is available on [PyPI](https://pypi.org/project/leafmap/). To install **leafmap**, run this command in your terminal:

```bash
pip install leafmap
```

## Install from conda-forge

**leafmap** is also available on [conda-forge](https://anaconda.org/conda-forge/leafmap). If you have
[Anaconda](https://www.anaconda.com/distribution/#download-section) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer, you can install leafmap using the following command:

```bash
conda install leafmap -c conda-forge
```

The leafmap package has some optional dependencies (e.g., [geopandas](https://geopandas.org/) and [localtileserver](https://github.com/banesullivan/localtileserver)), which can be challenging to install on some computers, especially Windows. It is highly recommended that you create a fresh conda environment to install geopandas and leafmap. Follow the commands below to set up a conda env and install [geopandas](https://geopandas.org), [localtileserver](https://github.com/banesullivan/localtileserver), [keplergl](https://docs.kepler.gl/docs/keplergl-jupyter), [pydeck](https://deckgl.readthedocs.io/), and leafmap.

```bash
conda install -n base mamba -c conda-forge
mamba create -n geo leafmap geopandas localtileserver python -c conda-forge
```

Optionally, you can install some [Jupyter notebook extensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions), which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this [post](https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231) for more information.

```bash
conda install jupyter_contrib_nbextensions -c conda-forge
```

## Install from GitHub

To install the development version from GitHub using [Git](https://git-scm.com/), run the following command in your terminal:

```bash
pip install git+https://github.com/opengeos/leafmap
```

## Use docker

You can also use [docker](https://hub.docker.com/r/giswqs/leafmap/) to run leafmap:

```bash
docker run -it -p 8888:8888 giswqs/leafmap:latest
```

## Upgrade leafmap

If you have installed **leafmap** before and want to upgrade to the latest version, you can run the following command in your terminal:

```bash
pip install -U leafmap
```

If you use conda, you can update leafmap to the latest version by running the following command in your terminal:

```bash
conda update -c conda-forge leafmap
```

To install the development version from GitHub directly within Jupyter notebook without using Git, run the following code:

```python
import leafmap
leafmap.update_package()
```

## Troubleshooting

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
