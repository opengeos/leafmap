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

The leafmap package has an optional dependency - [geopandas](https://geopandas.org/), which can be challenging to install on some computers, especially Windows. It is highly recommended that you create a fresh conda environment to install geopandas and leafmap. Follow the commands below to set up a conda env and isntall geopandas, xarray_leaflet, and leafmap.

```bash
    conda create -n geo python=3.8
    conda activate geo
    conda install geopandas
    conda install mamba -c conda-forge
    mamba install leafmap xarray_leaflet -c conda-forge
```

Optionally, you can install some [Jupyter notebook extensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions), which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this [post](https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231) for more information.

```bash
    conda install jupyter_contrib_nbextensions -c conda-forge
```

## Install from GitHub

To install the development version from GitHub using [Git](https://git-scm.com/), run the following command in your terminal:

```bash
    pip install git+https://github.com/giswqs/leafmap
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
