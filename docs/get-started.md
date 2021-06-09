# Get Started

This Get Started guide is intended as a quick way to start programming with **leafmap**. You can try out leafmap by using Goolge Colab ([![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/leafmap-colab)) or Binder ([![image](https://binder.pangeo.io/badge_logo.svg)](https://gishub.org/leafmap-pangeo)) without having to install anything on your computer.

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

## Use HERE Map Widget for Jupyter plotting backend

### Prerequisites
- A HERE developer account, free and available under [HERE Developer Portal](https://developer.here.com)
- An [API key](https://developer.here.com/documentation/identity-access-management/dev_guide/topics/dev-apikey.html) from the [HERE Developer Portal](https://developer.here.com)
- Export API key into environment variable `HEREMAPS_API_KEY`
```bash
export HEREMAPS_API_KEY=YOUR-ACTUAL-API-KEY
```

```python
import leafmap.heremap as leafmap
```

### Create an interactive map

```python
import os
api_key = os.environ.get("HEREMAPS_API_KEY") # read api_key from environment variable.
m = leafmap.Map(api_key=api_key, center=(40, -100), zoom=4)
m
```

## Demo

![](data/leafmap_demo.gif)
