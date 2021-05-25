# Usage

This Get Started guide is intended as a quick way to start programming with **leafmap**. You can try out leafmap by using Goolge Colab ([![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)) without having to install anything on your computer.

## Launch Jupyter notebook

```bash
conda activate geo
jupyter notebook
```

## Use ipyleaflet plotting backend

```python
import leafmap
```

## Use folium plotting backend

```python
import leafmap.foliumap as leafmap
```

## Create an interactive map

```python
m = leafmap.Map(center=(40, -100), zoom=4)
m
```

## Customize map height

```python
m = leafmap.Map(height="450px")
m
```

## Set control visibility

```python
m = leafmap.Map(draw_control=False, measure_control=False, fullscreen_control=False, attribution_control=True)
m
```

## Change basemaps

```python
m = leafmap.Map(google_map="TERRAIN")
m.add_basemap("HYBRID")
m
```

## Add XYZ tile layer

```python
m = leafmap.Map()
m.add_tile_layer(url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", name="Google Satellite")
m
```

## Add WMS tile layer

```python
m = leafmap.Map()
naip_url = 'https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?'
m.add_wms_layer(url=naip_url, layers='0', name='NAIP Imagery', format='image/png', shown=True)
m
```
