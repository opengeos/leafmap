"""Module for basemaps. Each basemap is defined as item in the ee_basemaps dictionary. For example, to access Google basemaps, use the following:

ee_basemaps['ROADMAP'], ee_basemaps['SATELLITE'], ee_basemaps['HYBRID'].

More WMS basemaps can be found at the following websites:

1. USGS National Map: https://viewer.nationalmap.gov/services/

2. MRLC NLCD Land Cover data: https://viewer.nationalmap.gov/services/

3. FWS NWI Wetlands data: https://www.fws.gov/wetlands/Data/Web-Map-Services.html

"""
import os
import folium
from box import Box
from ipyleaflet import TileLayer, WMSLayer, basemap_to_tiles
import ipyleaflet.basemaps as ipybasemaps
import here_map_widget
from here_map_widget import ImageTileProvider, DefaultLayers, DefaultLayerNames


leaf_basemaps = {
    "ROADMAP": TileLayer(
        url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Maps",
    ),
    "SATELLITE": TileLayer(
        url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Satellite",
    ),
    "TERRAIN": TileLayer(
        url="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Terrain",
    ),
    "HYBRID": TileLayer(
        url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Satellite",
    ),
    "ESRI": TileLayer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Satellite",
    ),
    "Esri Ocean": TileLayer(
        url="https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Ocean",
    ),
    "Esri Satellite": TileLayer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Satellite",
    ),
    "Esri Standard": TileLayer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Standard",
    ),
    "Esri Terrain": TileLayer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Terrain",
    ),
    "Esri Transportation": TileLayer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Transportation",
    ),
    "Esri Topo World": TileLayer(
        url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Topo World",
    ),
    "Esri National Geographic": TileLayer(
        url="http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri National Geographic",
    ),
    "Esri Shaded Relief": TileLayer(
        url="https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Shaded Relief",
    ),
    "Esri Physical Map": TileLayer(
        url="https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attribution="Esri",
        name="Esri Physical Map",
    ),
    "FWS NWI Wetlands": WMSLayer(
        url="https://www.fws.gov/wetlands/arcgis/services/Wetlands/MapServer/WMSServer?",
        layers="1",
        name="FWS NWI Wetlands",
        attribution="FWS",
        format="image/png",
        transparent=True,
    ),
    "FWS NWI Wetlands Raster": WMSLayer(
        url="https://www.fws.gov/wetlands/arcgis/services/Wetlands_Raster/ImageServer/WMSServer?",
        layers="0",
        name="FWS NWI Wetlands Raster",
        attribution="FWS",
        format="image/png",
        transparent=True,
    ),
    "Google Maps": TileLayer(
        url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Maps",
    ),
    "Google Satellite": TileLayer(
        url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Satellite",
    ),
    "Google Terrain": TileLayer(
        url="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Terrain",
    ),
    "Google Satellite Hybrid": TileLayer(
        url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attribution="Google",
        name="Google Satellite",
    ),
    "NLCD 2016 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms?",
        layers="NLCD_2016_Land_Cover_L48",
        name="NLCD 2016 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "NLCD 2013 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2013_Land_Cover_L48/wms?",
        layers="NLCD_2013_Land_Cover_L48",
        name="NLCD 2013 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "NLCD 2011 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2011_Land_Cover_L48/wms?",
        layers="NLCD_2011_Land_Cover_L48",
        name="NLCD 2011 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "NLCD 2008 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2008_Land_Cover_L48/wms?",
        layers="NLCD_2008_Land_Cover_L48",
        name="NLCD 2008 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "NLCD 2006 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2006_Land_Cover_L48/wms?",
        layers="NLCD_2006_Land_Cover_L48",
        name="NLCD 2006 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "NLCD 2004 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2004_Land_Cover_L48/wms?",
        layers="NLCD_2004_Land_Cover_L48",
        name="NLCD 2004 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "NLCD 2001 CONUS Land Cover": WMSLayer(
        url="https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2001_Land_Cover_L48/wms?",
        layers="NLCD_2001_Land_Cover_L48",
        name="NLCD 2001 CONUS Land Cover",
        attribution="MRLC",
        format="image/png",
        transparent=True,
    ),
    "USGS NAIP Imagery": WMSLayer(
        url="https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        layers="0",
        name="USGS NAIP Imagery",
        attribution="USGS",
        format="image/png",
        transparent=True,
    ),
    "USGS Hydrography": WMSLayer(
        url="https://basemap.nationalmap.gov/arcgis/services/USGSHydroCached/MapServer/WMSServer?",
        layers="0",
        name="USGS Hydrography",
        attribution="USGS",
        format="image/png",
        transparent=True,
    ),
    "USGS 3DEP Elevation": WMSLayer(
        url="https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?",
        layers="3DEPElevation:None",
        name="USGS 3DEP Elevation",
        attribution="USGS",
        format="image/png",
        transparent=True,
    ),
}


folium_basemaps = {
    "ROADMAP": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Maps",
        overlay=True,
        control=True,
    ),
    "SATELLITE": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
    ),
    "TERRAIN": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Terrain",
        overlay=True,
        control=True,
    ),
    "HYBRID": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
    ),
    "ESRI": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satellite",
        overlay=True,
        control=True,
    ),
    "Esri Ocean": folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Ocean",
        overlay=True,
        control=True,
    ),
    "Esri Satellite": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satellite",
        overlay=True,
        control=True,
    ),
    "Esri Standard": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Standard",
        overlay=True,
        control=True,
    ),
    "Esri Terrain": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Terrain",
        overlay=True,
        control=True,
    ),
    "Esri Transportation": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Transportation",
        overlay=True,
        control=True,
    ),
    "Esri Topo World": folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Topo World",
        overlay=True,
        control=True,
    ),
    "Esri National Geographic": folium.TileLayer(
        tiles="http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri National Geographic",
        overlay=True,
        control=True,
    ),
    "Esri Shaded Relief": folium.TileLayer(
        tiles="https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Shaded Relief",
        overlay=True,
        control=True,
    ),
    "Esri Physical Map": folium.TileLayer(
        tiles="https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Physical Map",
        overlay=True,
        control=True,
    ),
    "Bing VirtualEarth": folium.TileLayer(
        tiles="http://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1",
        attr="Microsoft",
        name="Bing VirtualEarth",
        overlay=True,
        control=True,
    ),
    "3DEP Elevation": folium.WmsTileLayer(
        url="https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?",
        layers="3DEPElevation:None",
        attr="USGS",
        name="3DEP Elevation",
        overlay=True,
        control=True,
    ),
    "NAIP Imagery": folium.WmsTileLayer(
        url="https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        layers="0",
        attr="USGS",
        name="NAIP Imagery",
        overlay=True,
        control=True,
    ),
}

here_basemaps = {
    "ROADMAP": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Maps",
        )
    ),
    "SATELLITE": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Satellite",
        )
    ),
    "TERRAIN": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Terrain",
        )
    ),
    "HYBRID": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Satellite",
        )
    ),
    "ESRI": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Satellite",
        )
    ),
    "ESRI Ocean": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Ocean",
        )
    ),
    "Esri Satellite": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            naem="Esri Satellite",
        )
    ),
    "Esri Standard": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Standard",
        )
    ),
    "Esri Terrain": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Terrain",
        )
    ),
    "Esri Transportation": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Transportation",
        )
    ),
    "Esri Topo World": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Topo World",
        )
    ),
    "Esri National Geographic": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri National Geographic",
        )
    ),
    "Esri Shaded Relief": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri Shaded Relief",
        )
    ),
    "Esri Physical Map": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
        )
    ),
    "Google Maps": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Maps",
        )
    ),
    "Google Satellite": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Satellite",
        )
    ),
    "Google Terrain": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Terrain",
        )
    ),
    "Google Satellite Hybrid": here_map_widget.TileLayer(
        provider=ImageTileProvider(
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Satellite",
        )
    ),
    "HERE_RASTER_NORMAL_MAP": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.map
    ),
    "HERE_RASTER_NORMAL_BASE": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.base
    ),
    "HERE_RASTER_NORMAL_BASE_NIGHT": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.basenight
    ),
    "HERE_RASTER_NORMAL_LABELS": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.labels
    ),
    "HERE_RASTER_NORMAL_TRANSIT": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.transit
    ),
    "HERE_RASTER_NORMAL_XBASE": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.xbase
    ),
    "HERE_RASTER_NORMAL_XBASE_NIGHT": DefaultLayers(
        layer_name=DefaultLayerNames.raster.normal.xbasenight
    ),
    "HERE_RASTER_SATELLITE_MAP": DefaultLayers(
        layer_name=DefaultLayerNames.raster.satellite.map
    ),
    "HERE_RASTER_SATELLITE_LABELS": DefaultLayers(
        layer_name=DefaultLayerNames.raster.satellite.labels
    ),
    "HERE_RASTER_SATELLITE_BASE": DefaultLayers(
        layer_name=DefaultLayerNames.raster.satellite.base
    ),
    "HERE_RASTER_SATELLITE_XBASE": DefaultLayers(
        layer_name=DefaultLayerNames.raster.satellite.xbase
    ),
    "HERE_RASTER_TERRAIN_MAP": DefaultLayers(
        layer_name=DefaultLayerNames.raster.terrain.map
    ),
    "HERE_RASTER_TERRAIN_LABELS": DefaultLayers(
        layer_name=DefaultLayerNames.raster.terrain.labels
    ),
    "HERE_RASTER_TERRAIN_BASE": DefaultLayers(
        layer_name=DefaultLayerNames.raster.terrain.base
    ),
    "HERE_RASTER_TERRAIN_XBASE": DefaultLayers(
        layer_name=DefaultLayerNames.raster.terrain.xbase
    ),
    "HERE_VECTOR_NORMAL_MAP": DefaultLayers(
        layer_name=DefaultLayerNames.vector.normal.map
    ),
    "HERE_VECTOR_NORMAL_TRUCK": DefaultLayers(
        layer_name=DefaultLayerNames.vector.normal.truck
    ),
}


# Adds ipyleaflet basemaps
for item in ipybasemaps.values():
    try:
        name = item["name"]
        basemap = "ipybasemaps.{}".format(name)
        leaf_basemaps[name] = basemap_to_tiles(eval(basemap))
    except Exception:
        for sub_item in item:
            name = item[sub_item]["name"]
            basemap = "ipybasemaps.{}".format(name)
            basemap = basemap.replace("Mids", "Modis")
            leaf_basemaps[name] = basemap_to_tiles(eval(basemap))

if os.environ.get("PLANET_API_KEY") is not None:
    from .common import planet_tiles_tropical

    planet_dict = planet_tiles_tropical()
    for key in planet_dict:
        leaf_basemaps[key] = planet_dict[key]

basemap_tiles = Box(leaf_basemaps, frozen_box=True)
basemaps = Box(
    dict(zip(list(leaf_basemaps.keys()), list(leaf_basemaps.keys()))), frozen_box=True
)
