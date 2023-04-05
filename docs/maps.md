# Interactive maps

This page demonstrates some interactive maps created using the [kepler.gl](https://kepler.gl/) plotting backend.

## Create an interactive map

You can specify various parameters to initialize the map, such as `center`, `zoom`, `height`, and `widescreen`.

```python
import leafmap.kepler as leafmap
m = leafmap.Map(center=[40, -100], zoom=2, height=600, widescreen=False)
m
```

<iframe width=760 height=500 frameBorder=0 src="../html/kepler.html"></iframe>

## Add a CSV

```python
m = leafmap.Map(center=[37.7621, -122.4143], zoom=12)
in_csv = 'https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/hex_data.csv'
config = 'https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/hex_config.json'
m.add_csv(in_csv, layer_name="hex_data", config=config)
m
```

<iframe width=760 height=500 frameBorder=0 src="../html/kepler_hex.html"></iframe>

## Add a GeoJSON

```python
m = leafmap.Map(center=[20, 0], zoom=1)
lines = 'https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/cable_geo.geojson'
m.add_geojson(lines, layer_name="Cable lines")
m
```

<iframe width=760 height=500 frameBorder=0 src="../html/kepler_lines.html"></iframe>

Add a GeoJSON with US state boundaries to the map.

```python
m = leafmap.Map(center=[50, -110], zoom=2)
polygons = 'https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/us_states.json'
m.add_geojson(polygons, layer_name="Countries")
m
```

<iframe width=760 height=500 frameBorder=0 src="../html/kepler_states.html"></iframe>

## Add a shapefile

```python
m = leafmap.Map(center=[20, 0], zoom=1)
in_shp = "https://github.com/opengeos/leafmap/raw/master/examples/data/countries.zip"
m.add_shp(in_shp, "Countries")
m
```

<iframe width=760 height=500 frameBorder=0 src="../html/kepler_countries.html"></iframe>

## Add a GeoDataFrame

```python
import geopandas as gpd
gdf = gpd.read_file("https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/world_cities.geojson")
m = leafmap.Map(center=[20, 0], zoom=1)
m.add_gdf(gdf, "World cities")
m
```

<iframe width=760 height=500 frameBorder=0 src="../html/kepler_cities.html"></iframe>
