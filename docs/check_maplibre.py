import os
import leafmap.maplibregl as leafmap

in_dir = "docs/maplibre/"
out_dir = os.path.expanduser("~/Downloads/maplibre")
files = leafmap.find_files(in_dir, "*.ipynb")
leafmap.execute_maplibre_notebook_dir(in_dir, out_dir, replace_api_key=True)
