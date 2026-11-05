# Command-line interface

Leafmap installs command-line tools for viewing geospatial files in the browser
without writing any code or starting Jupyter. They are handy for a quick look at a
file on disk or at a URL.

| Command       | Equivalent             | Purpose                                     | Requires                          |
| ------------- | ---------------------- | ------------------------------------------- | --------------------------------- |
| `view-raster` | `leafmap view-raster`  | View a raster (GeoTIFF, COG, ...) file      | `pip install "leafmap[raster]"`   |
| `view-vector` | `leafmap view-vector`  | View a vector (GeoJSON, Shapefile, ...) file | `pip install "leafmap[maplibre]"` |

Run any command with `--help` to see all of its options.

## View a raster

`view-raster` starts a local tile server with [localtileserver](https://github.com/banesullivan/localtileserver)
and opens an interactive map in your default browser. The server keeps running
until you press `Ctrl+C`.

```bash
# Single-band raster with a colormap
view-raster dem.tif --colormap terrain

# False-color composite from bands 4, 3 and 2
view-raster landsat.tif --indexes 4,3,2

# Cloud Optimized GeoTIFF from a URL with a fixed value range
view-raster https://github.com/opengeos/datasets/releases/download/raster/srtm90.tif \
    --colormap terrain --vmin 0 --vmax 4000
```

Options:

| Option                          | Description                                                               |
| ------------------------------- | ------------------------------------------------------------------------- |
| `--band`, `--indexes INDEXES`   | Band index to display (1-based), or a comma-separated list for RGB        |
| `--colormap COLORMAP`           | Colormap name to apply to a single band (e.g., `viridis`, `terrain`)      |
| `--vmin VMIN`, `--vmax VMAX`    | Value range used for color mapping                                        |
| `--nodata NODATA`               | Nodata value to render as transparent                                     |
| `--port PORT`                   | Port for the tile server (default: chosen automatically)                  |
| `--no-browser`                  | Do not open the browser; print the path of the generated HTML file instead |

## View a vector

`view-vector` reads the file with geopandas, renders it with the MapLibre backend
and opens the resulting map in your browser.

```bash
view-vector countries.geojson
view-vector https://github.com/opengeos/datasets/releases/download/vector/countries.geojson --style positron
```

Options:

| Option          | Description                                                                 |
| --------------- | --------------------------------------------------------------------------- |
| `--style STYLE` | Basemap style, such as `dark-matter` (default), `positron`, `voyager` or `liberty` |
| `--no-browser`  | Do not open the browser; print the path of the generated HTML file instead  |

## Python API

The same viewers are available from Python:

```python
from leafmap.cli import view_raster, view_vector

view_raster("dem.tif", colormap="terrain")
view_vector("countries.geojson", style="positron")
```

::: leafmap.cli
