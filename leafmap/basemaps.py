"""Module for basemaps.

Each basemap is defined as an item in the `basemaps` dictionary.

For example, to access Google basemaps, users first need to get a Google Maps API key from https://bit.ly/3sw0THG.
    Then, set the environment variable using geemap.set_api_key(<API-KEY>). Then Google basemaps can be accessed using:

    * `basemaps['ROADMAP']`
    * `basemaps['SATELLITE']`
    * `basemaps['TERRAIN']`
    * `basemaps['HYBRID']`

More WMS basemaps can be found at the following websites:

  1. USGS National Map: https://viewer.nationalmap.gov/services/
  2. MRLC NLCD Land Cover data: https://viewer.nationalmap.gov/services/
  3. FWS NWI Wetlands data: https://www.fws.gov/wetlands/Data/Web-Map-Services.html

"""

import collections
import os
import requests
import folium
import ipyleaflet
import xyzservices
from .common import check_package, planet_tiles

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "YOUR-API-KEY")

XYZ_TILES = {
    "OpenStreetMap": {
        "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": "OpenStreetMap",
        "name": "OpenStreetMap",
    },
}

# Add Google basemaps if API key is detected in the environment variables.
if GOOGLE_MAPS_API_KEY != "":
    XYZ_TILES.update(
        {
            "ROADMAP": {
                "url": f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}",
                "attribution": "Google",
                "name": "Google Maps",
            },
            "SATELLITE": {
                "url": f"https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}",
                "attribution": "Google",
                "name": "Google Satellite",
            },
            "TERRAIN": {
                "url": f"https://mt1.google.com/vt/lyrs=p&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}",
                "attribution": "Google",
                "name": "Google Terrain",
            },
            "HYBRID": {
                "url": f"https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}&key={GOOGLE_MAPS_API_KEY}",
                "attribution": "Google",
                "name": "Google Hybrid",
            },
        }
    )
else:  # If Google Maps API key is not detected, defaulting to Esri basemaps.
    XYZ_TILES.update(
        {
            "ROADMAP": {
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
                "attribution": "Esri",
                "name": "Esri.WorldStreetMap",
            },
            "SATELLITE": {
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "attribution": "Esri",
                "name": "Esri.WorldImagery",
            },
            "TERRAIN": {
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
                "attribution": "Esri",
                "name": "Esri.WorldTopoMap",
            },
            "HYBRID": {
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "attribution": "Esri",
                "name": "Esri.WorldImagery",
            },
        }
    )


# Custom WMS tile services.
WMS_TILES = {
    "FWS NWI Wetlands": {
        "url": "https://www.fws.gov/wetlands/arcgis/services/Wetlands/MapServer/WMSServer?",
        "layers": "1",
        "name": "FWS NWI Wetlands",
        "attribution": "FWS",
        "format": "image/png",
        "transparent": True,
    },
    "FWS NWI Wetlands Raster": {
        "url": "https://www.fws.gov/wetlands/arcgis/services/Wetlands_Raster/ImageServer/WMSServer?",
        "layers": "0",
        "name": "FWS NWI Wetlands Raster",
        "attribution": "FWS",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2021 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2021_Land_Cover_L48/wms?",
        "layers": "NLCD_2021_Land_Cover_L48",
        "name": "NLCD 2021 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2019 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2019_Land_Cover_L48/wms?",
        "layers": "NLCD_2019_Land_Cover_L48",
        "name": "NLCD 2019 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2016 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms?",
        "layers": "NLCD_2016_Land_Cover_L48",
        "name": "NLCD 2016 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2013 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2013_Land_Cover_L48/wms?",
        "layers": "NLCD_2013_Land_Cover_L48",
        "name": "NLCD 2013 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2011 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2011_Land_Cover_L48/wms?",
        "layers": "NLCD_2011_Land_Cover_L48",
        "name": "NLCD 2011 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2008 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2008_Land_Cover_L48/wms?",
        "layers": "NLCD_2008_Land_Cover_L48",
        "name": "NLCD 2008 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2006 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2006_Land_Cover_L48/wms?",
        "layers": "NLCD_2006_Land_Cover_L48",
        "name": "NLCD 2006 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2004 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2004_Land_Cover_L48/wms?",
        "layers": "NLCD_2004_Land_Cover_L48",
        "name": "NLCD 2004 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2001 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2001_Land_Cover_L48/wms?",
        "layers": "NLCD_2001_Land_Cover_L48",
        "name": "NLCD 2001 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "USGS NAIP Imagery": {
        "url": "https://imagery.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        "layers": "USGSNAIPImagery:NaturalColor",
        "name": "USGS NAIP Imagery",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS NAIP Imagery False Color": {
        "url": "https://imagery.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        "layers": "USGSNAIPImagery:FalseColorComposite",
        "name": "USGS NAIP Imagery False Color",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS NAIP Imagery NDVI": {
        "url": "https://imagery.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        "layers": "USGSNAIPImagery:NDVI_Color",
        "name": "USGS NAIP Imagery NDVI",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS Hydrography": {
        "url": "https://basemap.nationalmap.gov/arcgis/services/USGSHydroCached/MapServer/WMSServer?",
        "layers": "0",
        "name": "USGS Hydrography",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS 3DEP Elevation": {
        "url": "https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?",
        "layers": "33DEPElevation:Hillshade Elevation Tinted",
        "name": "USGS 3DEP Elevation",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2020": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2020_MAP",
        "name": "ESA Worldcover 2020",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2020 S2 FCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2020_S2_FCC",
        "name": "ESA Worldcover 2020 S2 FCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2020 S2 TCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2020_S2_TCC",
        "name": "ESA Worldcover 2020 S2 TCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2021": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2021_MAP",
        "name": "ESA Worldcover 2021",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2021 S2 FCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2021_S2_FCC",
        "name": "ESA Worldcover 2021 S2 FCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2021 S2 TCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2021_S2_TCC",
        "name": "ESA Worldcover 2021 S2 TCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
}

custom_tiles = {"xyz": XYZ_TILES, "wms": WMS_TILES}


def get_xyz_dict(free_only=True, france=False):
    """Returns a dictionary of xyz services.

    Args:
        free_only (bool, optional): Whether to return only free xyz tile
            services that do not require an access token. Defaults to True.
        france (bool, optional): Whether to include Geoportail France basemaps.
            Defaults to False.

    Returns:
        dict: A dictionary of xyz services.
    """
    xyz_bunch = xyzservices.providers

    if free_only:
        xyz_bunch = xyz_bunch.filter(requires_token=False)
    if not france:
        xyz_bunch = xyz_bunch.filter(
            function=lambda tile: "france" not in dict(tile)["name"].lower()
        )

    xyz_dict = xyz_bunch.flatten()

    for key, value in xyz_dict.items():
        tile = xyzservices.TileProvider(value)
        if "type" not in tile:
            tile["type"] = "xyz"
        xyz_dict[key] = tile

    xyz_dict = collections.OrderedDict(sorted(xyz_dict.items()))
    return xyz_dict


def xyz_to_leaflet():
    """Convert xyz tile services to ipyleaflet tile layers.

    Returns:
        dict: A dictionary of ipyleaflet tile layers.
    """
    leaflet_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    # Add custom tiles.
    for tile_type, tile_dict in custom_tiles.items():
        for tile_provider, tile_info in tile_dict.items():
            tile_info["type"] = tile_type
            leaflet_dict[tile_info["name"]] = tile_info

    # Add xyzservices.provider tiles.
    for tile_provider, tile_info in get_xyz_dict().items():
        if tile_info["name"] in ignore_list:
            continue
        tile_info["url"] = tile_info.build_url()
        leaflet_dict[tile_info["name"]] = tile_info

    return leaflet_dict


def xyz_to_folium():
    """Convert xyz tile services to folium tile layers.

    Returns:
        dict: A dictionary of folium tile layers.
    """
    folium_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    for key, tile in custom_tiles["xyz"].items():
        folium_dict[key] = folium.TileLayer(
            tiles=tile["url"],
            attr=tile["attribution"],
            name=tile["name"],
            overlay=True,
            control=True,
            max_zoom=22,
        )

    for key, tile in custom_tiles["wms"].items():
        folium_dict[key] = folium.WmsTileLayer(
            url=tile["url"],
            layers=tile["layers"],
            name=tile["name"],
            attr=tile["attribution"],
            fmt=tile["format"],
            transparent=tile["transparent"],
            overlay=True,
            control=True,
        )

    for item in get_xyz_dict().values():
        if item["name"] in ignore_list:
            continue
        folium_dict[item.name] = folium.TileLayer(
            tiles=item.build_url(),
            attr=item.attribution,
            name=item.name,
            max_zoom=item.get("max_zoom", 22),
            overlay=True,
            control=True,
        )

    if os.environ.get("PLANET_API_KEY") is not None:
        planet_dict = planet_tiles(tile_format="folium")
        folium_dict.update(planet_dict)

    return folium_dict


def xyz_to_pydeck():
    """Convert xyz tile services to pydeck custom tile layers.

    Returns:
        dict: A dictionary of pydeck tile layers.
    """

    check_package("pydeck", "https://deckgl.readthedocs.io/en/latest/installation.html")
    import pydeck as pdk

    pydeck_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    for key, tile in custom_tiles["xyz"].items():
        url = tile["url"]
        pydeck_dict[key] = url

    for key, item in get_xyz_dict().items():
        if item["name"] in ignore_list:
            continue
        url = item.build_url()
        pydeck_dict[key] = url

        if os.environ.get("PLANET_API_KEY") is not None:
            planet_dict = planet_tiles(tile_format="ipyleaflet")
            for id_, tile in planet_dict.items():
                pydeck_dict[id_] = tile.url

    pdk.settings.custom_libraries = [
        {
            "libraryName": "MyTileLayerLibrary",
            "resourceUri": "https://cdn.jsdelivr.net/gh/giswqs/pydeck_myTileLayer@master/dist/bundle.js",
        }
    ]

    for key in pydeck_dict:
        pydeck_dict[key] = pdk.Layer("MyTileLayer", pydeck_dict[key], key)

    return pydeck_dict


def xyz_to_plotly():
    """Convert xyz tile services to plotly tile layers.

    Returns:
        dict: A dictionary of plotly tile layers.
    """
    plotly_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    for key, tile in custom_tiles["xyz"].items():
        plotly_dict[key] = {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": tile["attribution"],
            "source": [tile["url"]],
            "name": key,
        }

    for item in get_xyz_dict().values():
        if item["name"] in ignore_list:
            continue
        plotly_dict[item.name] = {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": item.attribution,
            "source": [item.build_url()],
            "name": item.name,
        }

    return plotly_dict


def xyz_to_bokeh():
    """Convert xyz tile services to bokeh tile layers.

    Returns:
        dict: A dictionary of bokeh tile layers.
    """
    from bokeh.models import WMTSTileSource

    bokeh_dict = {}

    for key in XYZ_TILES:
        url = XYZ_TILES[key]["url"]
        attribution = XYZ_TILES[key]["attribution"]
        tile_options = {
            "url": url,
            "attribution": attribution,
        }
        bokeh_dict[key] = WMTSTileSource(**tile_options)

    xyz_dict = get_xyz_dict()
    for item in xyz_dict:
        url = xyz_dict[item].build_url()
        attribution = xyz_dict[item].attribution
        key = xyz_dict[item].name
        tile_options = {
            "url": url,
            "attribution": attribution,
        }
        bokeh_dict[key] = WMTSTileSource(**tile_options)

    return bokeh_dict


def search_qms(keywords, limit=10):
    """Search qms files for keywords. Reference: https://github.com/geopandas/xyzservices/issues/65

    Args:
        keywords (str): Keywords to search for.
        limit (int): Number of results to return.
    """
    QMS_API = "https://qms.nextgis.com/api/v1/geoservices"

    services = requests.get(
        f"{QMS_API}/?search={keywords}&type=tms&epsg=3857&limit={str(limit)}"
    )
    services = services.json()
    if services["count"] == 0:
        return None
    elif services["count"] <= limit:
        return services["results"]
    else:
        return services["results"][:limit]


def get_qms(service_id):
    QMS_API = "https://qms.nextgis.com/api/v1/geoservices"
    service_details = requests.get(f"{QMS_API}/{service_id}")
    return service_details.json()


def qms_to_geemap(service_id):
    """Convert a qms service to an ipyleaflet tile layer.

    Args:
        service_id (str): Service ID.

    Returns:
        ipyleaflet.TileLayer: An ipyleaflet tile layer.
    """
    service_details = get_qms(service_id)
    name = service_details["name"]
    url = service_details["url"]
    attribution = service_details["copyright_text"]

    layer = ipyleaflet.TileLayer(url=url, name=name, attribution=attribution)
    return layer
