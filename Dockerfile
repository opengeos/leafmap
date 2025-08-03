# ------------------------------
# Base image from Jupyter stack
# ------------------------------
FROM quay.io/jupyter/base-notebook:latest

# ------------------------------
# 1. Switch to root to install system packages
# ------------------------------
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ------------------------------
# 2. Install conda packages into base env
# ------------------------------
RUN mamba install -n base -c conda-forge -y \
    gdal \
    proj \
    geos \
    fiona \
    rasterio \
    pyproj \
    geopandas \
    maplibre \
    pmtiles \
    flask \
    flask-cors \
    localtileserver \
    jupyter-server-proxy \
    h5netcdf \
    h5py \
    opera-utils \
    rioxarray \
    rio-cogeo \
    polars \
    && mamba clean --all --yes \
    && fix-permissions $CONDA_DIR

# ------------------------------
# 2b. Create missing sqlite symlinks
# ------------------------------
RUN ln -s $CONDA_PREFIX/lib/libsqlite3.so.3.50.0 $CONDA_PREFIX/lib/libsqlite3.so \
    && ln -s $CONDA_PREFIX/lib/libsqlite3.so.3.50.0 $CONDA_PREFIX/lib/libsqlite3.so.0

# ------------------------------
# 3. Set geospatial environment variables
# ------------------------------
ENV PROJ_LIB=$CONDA_DIR/share/proj \
    GDAL_DATA=$CONDA_DIR/share/gdal \
    LOCALTILESERVER_CLIENT_PREFIX='proxy/{port}'

# ------------------------------
# 4. Add jupyter_server_config.py to increase websocket limit
# ------------------------------
RUN mkdir -p /home/jovyan/.jupyter && \
    echo "c = get_config()  # noqa" > /home/jovyan/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.tornado_settings = {\"websocket_max_message_size\": 100 * 1024 * 1024}" >> /home/jovyan/.jupyter/jupyter_server_config.py && \
    fix-permissions /home/jovyan/.jupyter


# ------------------------------
# 5. Copy source code and install leafmap
# ------------------------------
COPY . /home/jovyan/leafmap
WORKDIR /home/jovyan/leafmap

ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_LEAFMAP=0.0.0

RUN pip install . && \
    pip install quak && \
    rm -rf ./build ./dist *.egg-info && \
    mkdir -p /home/jovyan/work && \
    fix-permissions /home/jovyan

# ------------------------------
# 6. Switch back to default user
# ------------------------------
USER $NB_UID
WORKDIR /home/jovyan

# ------------------------------
# Usage:
# docker pull giswqs/leafmap:latest
# docker run -it -p 8888:8888 -v $(pwd):/home/jovyan/work giswqs/leafmap:latest
# ------------------------------
