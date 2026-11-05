# Installation

**leafmap** supports Python 3.9 and later. The core package is lightweight; heavier
features (raster tiling, vector analysis, extra mapping backends) are available
through [optional dependencies](#optional-dependencies).

## Install from PyPI

**leafmap** is available on [PyPI](https://pypi.org/project/leafmap/). To install **leafmap**, run this command in your terminal:

```bash
pip install leafmap
```

## Install from conda-forge

**leafmap** is also available on [conda-forge](https://anaconda.org/conda-forge/leafmap). If you have
[Miniforge](https://github.com/conda-forge/miniforge) (recommended), [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download) installed on your computer, you can install leafmap using the following command:

```bash
conda install -c conda-forge leafmap
```

Some optional dependencies (e.g., [geopandas](https://geopandas.org/) and [localtileserver](https://github.com/banesullivan/localtileserver)) depend on compiled libraries such as GDAL, which can be challenging to install with pip on some computers, especially Windows. It is highly recommended that you create a fresh conda environment for them:

```bash
conda create -n geo -c conda-forge python=3.12 leafmap geopandas localtileserver jupyterlab
conda activate geo
```

[Miniforge](https://github.com/conda-forge/miniforge) ships with `mamba`, a faster drop-in replacement for `conda`. If you have it, you can replace `conda` with `mamba` in the commands above.

## Optional dependencies

Leafmap has various optional dependencies to enable additional features. You can install them as needed:

| Extra      | Command                            | Enables                                                                          |
| ---------- | ---------------------------------- | -------------------------------------------------------------------------------- |
| `raster`   | `pip install "leafmap[raster]"`    | Local raster/COG visualization (localtileserver, rioxarray, TiTiler, NetCDF)     |
| `vector`   | `pip install "leafmap[vector]"`    | Vector analysis, OpenStreetMap (osmnx), PMTiles, lonboard, classification        |
| `maplibre` | `pip install "leafmap[maplibre]"`  | The MapLibre GL backend (`leafmap.maplibregl`)                                   |
| `backends` | `pip install "leafmap[backends]"`  | The bokeh, kepler.gl, MapLibre, pydeck and plotly backends                       |
| `polars`   | `pip install "leafmap[polars]"`    | `add_polars()` for Polars DataFrames with geometry columns                       |
| `duckdb`   | `pip install "leafmap[duckdb]"`    | DuckDB and SQL integration                                                       |
| `sql`      | `pip install "leafmap[sql]"`       | Reading vector data from PostGIS                                                 |
| `pmtiles`  | `pip install "leafmap[pmtiles]"`   | Creating and serving PMTiles                                                     |
| `titiler`  | `pip install "leafmap[titiler]"`   | Running a local TiTiler server                                                   |
| `usgs`     | `pip install "leafmap[usgs]"`      | USGS hydrography and 3DEP elevation data                                         |
| `lidar`    | `pip install "leafmap[lidar]"`     | LiDAR point cloud visualization                                                  |
| `apps`     | `pip install "leafmap[apps]"`      | Building web apps with Streamlit, Voilà and Solara                               |
| `ai`       | `pip install "leafmap[ai]"`        | AI/ML features (torchgeo, raster-vision)                                         |

Multiple extras can be combined, for example `pip install "leafmap[raster,vector,maplibre]"`.

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

## Check your installation

To print the versions of leafmap and its key dependencies (useful when reporting an issue), run:

```python
import leafmap
leafmap.Report()
```

## Troubleshooting

If the interactive map does not show up in Jupyter Notebook or JupyterLab, or you see an error such as `Error displaying widget: model not found`, the Jupyter widget front-end is usually out of sync with the Python packages. Modern versions of JupyterLab (4.x) and Notebook (7.x) install widget extensions automatically together with the Python package, so no `jupyter nbextension` or `jupyter labextension install` commands are needed.

Try the following steps:

1. Make sure `ipywidgets`, `ipyleaflet` and Jupyter are installed **in the same environment** as the kernel you are using, and upgrade them together:

    ```bash
    pip install -U ipywidgets ipyleaflet jupyterlab notebook
    ```

2. Restart the Jupyter server (not just the kernel) and hard-refresh the browser page.
3. Run `jupyter labextension list` and check that `jupyter-leaflet` and `@jupyter-widgets/jupyterlab-manager` are listed as enabled.

If the issue persists, you can open an issue on the [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet/issues) repository, or try a different backend such as `import leafmap.foliumap as leafmap` or `import leafmap.maplibregl as leafmap`.

Alternatively, you can run leafmap directly in the cloud without installing anything:

-   [Google Colab](https://colab.research.google.com/github/opengeos/leafmap/blob/master)
-   [Binder](https://mybinder.org/v2/gh/opengeos/leafmap/HEAD)
