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
    fiona \
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
    && mamba clean --all --yes \
    && fix-permissions $CONDA_DIR

# RUN mamba install -c conda-forge gdal==3.11.0 -y

# ------------------------------
# 2b. Create missing sqlite symlinks (after files exist)
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
# 4. Copy source code after env setup
# ------------------------------
COPY . /home/jovyan/leafmap
WORKDIR /home/jovyan/leafmap

# ------------------------------
# 5. Install leafmap from source
# ------------------------------
# Prevent version resolution errors in CI
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_LEAFMAP=0.0.0

RUN pip install . && \
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
