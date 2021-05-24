# Installation

## Install from PyPI

**leafmap** is available on [PyPI](https://pypi.org/project/leafmap/). To install **leafmap**, run this command in your terminal:

    pip install leafmap

## Install from conda-forge

**leafmap** is also available on [conda-forge](https://anaconda.org/conda-forge/leafmap). If you have
[Anaconda](https://www.anaconda.com/distribution/#download-section) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer, you can create a conda Python environment to install leafmap:

    conda create -n geo python
    conda activate geo
    conda install mamba -c conda-forge
    mamba install leafmap -c conda-forge

Optionally, you can install some [Jupyter notebook extensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions), which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this [post](https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231) for more information.

    conda install jupyter_contrib_nbextensions -c conda-forge

## Install from GitHub

To install the development version from GitHub using [Git](https://git-scm.com/), run the following command in your terminal:

    pip install git+https://github.com/giswqs/leafmap

## Upgrade leafmap

If you have installed **leafmap** before and want to upgrade to the latest version, you can run the following command in your terminal:

    pip install -U leafmap

If you use conda, you can update leafmap to the latest version by running the following command in your terminal:

    mamba update -c conda-forge leafmap

To install the development version from GitHub directly within Jupyter notebook without using Git, run the following code:

    import leafmap
    leafmap.update_package()
