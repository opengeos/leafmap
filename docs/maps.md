# Interactive maps

This page demonstrates some interactive maps created using the kepler.gl plotting backend.

Create an interactive map. You can specify various parameters to initialize the map, such as `center`, `zoom`, `height`, and `widescreen`.

```python
import leafmap.kepler as leafmap
m = leafmap.Map(center=[40, -100], zoom=2, height=600, widescreen=False)
m
```

<iframe width=1000, height=600 frameBorder=0 src="notebooks/cache/kepler.html"></iframe>

Add a GeoJSON to the map.

```python
m = leafmap.Map(center=[20, 0], zoom=1)
lines = 'https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/cable-geo.geojson'
m.add_geojson(lines, layer_name="Cable lines")
m
```

<iframe width=1000, height=600 frameBorder=0 src="notebooks/cache/kepler_lines.html"></iframe>

Add a GeoJSON with US state boundaries to the map.

```python
m = leafmap.Map(center=[50, -110], zoom=2)
polygons = 'https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us-states.json'
m.add_geojson(polygons, layer_name="Countries")
m
```

<iframe width=1000, height=600 frameBorder=0 src="notebooks/cache/kepler_states.html"></iframe>

Add a shapefile to the map.

```python
m = leafmap.Map(center=[20, 0], zoom=1)
in_shp = "https://github.com/giswqs/leafmap/raw/master/examples/data/countries.zip"
m.add_shp(in_shp, "Countries")
m
```

<iframe width=1000, height=600 frameBorder=0 src="notebooks/cache/kepler_states.html"></iframe>

Add a GeoPandas GeoDataFrame to the map.

```python
import geopandas as gpd
gdf = gpd.read_file("https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/world_cities.geojson")
m = leafmap.Map(center=[20, 0], zoom=1)
m.add_gdf(gdf, "World cities")
m
```

<iframe width=1000, height=600 frameBorder=0 src="notebooks/cache/kepler_cities.html"></iframe>
