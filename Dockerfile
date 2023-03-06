FROM jupyter/scipy-notebook:latest
# RUN pip install --find-links=https://girder.github.io/large_image_wheels --no-cache GDAL
RUN mamba install -c conda-forge leafmap geopandas localtileserver -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

RUN mkdir ./examples
COPY --chown=jovyan:users /examples/notebooks ./examples/notebooks
COPY --chown=jovyan:users /examples/workshops ./examples/workshops
COPY --chown=jovyan:users /examples/data ./examples/data
COPY --chown=jovyan:users /examples/README.md ./examples/README.md