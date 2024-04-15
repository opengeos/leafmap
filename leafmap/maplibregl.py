"""The maplibregl module provides the Map class for creating interactive maps using the maplibre.ipywidget module.
"""

import xyzservices
from box import Box
from maplibre.ipywidget import MapWidget
from maplibre import Layer, LayerType, MapOptions
from maplibre.sources import GeoJSONSource, RasterTileSource
from maplibre.controls import (
    ScaleControl,
    FullscreenControl,
    GeolocateControl,
    NavigationControl,
)

from .basemaps import xyz_to_leaflet
from .common import *

basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(MapWidget):
    """The Map class inherits from the MapWidget class of the maplibre.ipywidget module."""

    def __init__(self, center=(20, 0), zoom=1, height="600px", **kwargs):
        """Create a Map object.

        Args:
            center (tuple, optional): The center of the map (lat, lon). Defaults to (20, 0).
            zoom (int, optional): The zoom level of the map. Defaults to 1.
            height (str, optional): The height of the map. Defaults to "600px".
            **kwargs: Additional keyword arguments that are passed to the MapOptions class.
                See https://maplibre.org/maplibre-gl-js/docs/API/types/MapOptions/ for more information.
        """
        center = (center[1], center[0])
        map_options = MapOptions(center=center, zoom=zoom, **kwargs)

        super().__init__(map_options, height=height)

        self.layers = {}

    def add_layer(self, layer, name=None):
        """Adds a layer to the map.

        Args:
            layer (object): The layer object.
            name (str, optional): The name of the layer. Defaults to None.
        """

        if name is None:
            name = layer.id

        self.layers[name] = layer
        super().add_layer(layer)

    def add_control(self, control, position="top-right", **kwargs):
        """Adds a control to the map.

        Args:
            control (object | str): The control object. Can be one of the following: 'scale', 'fullscreen', 'geolocate', 'navigation'.
            position (str, optional): The position of the control. Defaults to "top-right".
            **kwargs: Additional keyword arguments that are passed to the control object.
        """

        if isinstance(control, str):
            control = control.lower()
            if control == "scale":
                control = ScaleControl(**kwargs)
            elif control == "fullscreen":
                control = FullscreenControl(**kwargs)
            elif control == "geolocate":
                control = GeolocateControl(**kwargs)
            elif control == "navigation":
                control = NavigationControl(**kwargs)
            else:
                print(
                    "Control can only be one of the following: 'scale', 'fullscreen', 'geolocate', 'navigation'"
                )
                return

        super().add_control(control, position)

    def set_center(self, lon, lat, zoom=None):
        """Sets the center of the map.

        This method sets the center of the map to the specified longitude and latitude.
        If a zoom level is provided, it also sets the zoom level of the map.

        Args:
            lon (float): The longitude of the center of the map.
            lat (float): The latitude of the center of the map.
            zoom (int, optional): The zoom level of the map. If None, the zoom level is not changed.

        Returns:
            None
        """
        center = [lon, lat]
        self.add_call("setCenter", center)

        if zoom is not None:
            self.add_call("setZoom", zoom)

    def set_zoom(self, zoom):
        """
        Sets the zoom level of the map.

        This method sets the zoom level of the map to the specified value.

        Args:
            zoom (int): The zoom level of the map.

        Returns:
            None
        """
        self.add_call("setZoom", zoom)

    def fit_bounds(self, bounds):
        """
        Adjusts the viewport of the map to fit the specified geographical bounds in the format of [[lon_min, lat_min], [lon_max, lat_max]].

        This method adjusts the viewport of the map so that the specified geographical bounds
        are visible in the viewport. The bounds are specified as a list of two points,
        where each point is a list of two numbers representing the longitude and latitude.

        Args:
            bounds (list): A list of two points representing the geographical bounds that
                        should be visible in the viewport. Each point is a list of two
                        numbers representing the longitude and latitude. For example,
                        [[32.958984, -5.353521],[43.50585, 5.615985]]

        Returns:
            None
        """

        self.add_call("fitBounds", bounds)

    def add_basemap(self, basemap="HYBRID", show=True, attribution=None, **kwargs):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'HYBRID'.
            show (bool, optional): Whether the basemap is visible or not. Defaults to True.
            **kwargs: Additional keyword arguments that are passed to the RasterTileSource class.
                See https://eodagmbh.github.io/py-maplibregl/api/sources/#maplibre.sources.RasterTileSource for more information.
        """

        map_dict = {
            "ROADMAP": "Google Maps",
            "SATELLITE": "Google Satellite",
            "TERRAIN": "Google Terrain",
            "HYBRID": "Google Hybrid",
        }

        name = basemap
        url = None
        max_zoom = 30
        min_zoom = 0

        if isinstance(basemap, str) and basemap.upper() in map_dict:
            layer = get_google_map(basemap.upper(), **kwargs)
            url = layer.url
            name = layer.name
            attribution = layer.attribution

        elif isinstance(basemap, xyzservices.TileProvider):
            name = basemap.name
            url = basemap.build_url()
            if attribution is None:
                attribution = basemap.attribution
            if "max_zoom" in basemap.keys():
                max_zoom = basemap["max_zoom"]
            if "min_zoom" in basemap.keys():
                min_zoom = basemap["min_zoom"]

        elif basemap in basemaps:
            url = basemaps[basemap]["url"]
            if attribution is None:
                attribution = basemaps[basemap]["attribution"]
            if "max_zoom" in basemaps[basemap]:
                max_zoom = basemaps[basemap]["max_zoom"]
            if "min_zoom" in basemaps[basemap]:
                min_zoom = basemaps[basemap]["min_zoom"]
        else:
            print(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )
            return

        raster_source = RasterTileSource(
            tiles=[url],
            attribution=attribution,
            max_zoom=max_zoom,
            min_zoom=min_zoom,
            **kwargs,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
        self.add_layer(layer)
        self.set_visibility(name, show)

    def add_geojson(self, data, layer_name=None, show=True, source_args={}, **kwargs):
        """Adds a GeoJSON layer to the map.

        Args:
            data (str | dict): The GeoJSON data. This can be a URL to a GeoJSON file or a GeoJSON dictionary.
            layer_name (str, optional): The name of the layer. Defaults to 'geojson'.
            show (bool, optional): Whether the layer is visible or not. Defaults to True.
            source_args (dict, optional): Additional keyword arguments that are passed to the GeoJSONSource class.
                See https://eodagmbh.github.io/py-maplibregl/api/sources/#maplibre.sources.GeoJSONSource for more information.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.
        """

        if isinstance(data, str) or isinstance(data, dict):
            source = GeoJSONSource(data=data, **source_args)
        else:
            print("The data must be a URL or a GeoJSON dictionary.")
            return

        layer = Layer(id=layer_name, source=source, type=LayerType.LINE, **kwargs)
        self.add_layer(layer)
        self.set_visibility(layer_name, show)

    def add_tile_layer(
        self,
        url,
        name="Tile Layer",
        attribution="",
        show=True,
        tile_size=256,
        source_args={},
        **kwargs,
    ):
        """Adds a TileLayer to the map.

        Args:
            url (str): The URL of the tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Tile Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            show (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            tile_size (int, optional): The size of the tiles. Defaults to 256.
            source_args (dict, optional): Additional keyword arguments that are passed to the RasterTileSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.
        """

        raster_source = RasterTileSource(
            tiles=[url], attribution=attribution, tile_size=tile_size, **source_args
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER, **kwargs)
        self.add_layer(layer)
        self.set_visibility(name, show)

    def add_cog_layer(
        self,
        url,
        name="COG Layer",
        attribution="",
        opacity=1.0,
        shown=True,
        bands=None,
        titiler_endpoint=None,
        zoom_to_layer=True,
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            bands (list, optional): A list of bands to use for the layer. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
            zoom_to_layer (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
        """
        available_bands = cog_bands(url, titiler_endpoint)

        if bands is None:
            if len(available_bands) >= 3:
                indexes = [1, 2, 3]
            else:
                indexes = [1]
        else:
            indexes = bands

        vis_bands = [available_bands[idx - 1] for idx in indexes]

        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        if zoom_to_layer:
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
