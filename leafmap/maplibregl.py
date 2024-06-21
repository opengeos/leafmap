"""The maplibregl module provides the Map class for creating interactive maps using the maplibre.ipywidget module.
"""

import requests
import xyzservices
import geopandas as gpd
from box import Box
from maplibre.basemaps import background
from maplibre.basemaps import construct_carto_basemap_url
from maplibre.ipywidget import MapWidget
from maplibre import Layer, LayerType, MapOptions
from maplibre.sources import GeoJSONSource, RasterTileSource
from maplibre.utils import get_bounds
from maplibre.controls import (
    ScaleControl,
    FullscreenControl,
    GeolocateControl,
    NavigationControl,
    Marker,
)

from .basemaps import xyz_to_leaflet
from .common import *
from typing import Tuple, Dict, Any, Optional

basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(MapWidget):
    """The Map class inherits from the MapWidget class of the maplibre.ipywidget module."""

    def __init__(
        self,
        center: Tuple[float, float] = (0, 20),
        zoom: float = 1,
        pitch: float = 0,
        bearing: float = 0,
        style: str = "dark-matter",
        height: str = "600px",
        controls: Dict[str, str] = {
            "navigation": "top-right",
            "fullscreen": "top-right",
            "scale": "bottom-left",
        },
        **kwargs: Any,
    ) -> None:
        """
        Create a Map object.

        Args:
            center (tuple, optional): The center of the map (lon, lat). Defaults
                to (0, 20).
            zoom (float, optional): The zoom level of the map. Defaults to 1.
            pitch (float, optional): The pitch of the map. Measured in degrees
                away from the plane of the screen (0-85) Defaults to 0.
            bearing (float, optional): The bearing of the map. Measured in degrees
                counter-clockwise from north. Defaults to 0.
            style (str, optional): The style of the map. It can be a string or a URL.
                If it is a string, it must be one of the following: "dark-matter",
                "positron", "voyager", "positron-nolabels", "dark-matter-nolabels",
                "voyager-nolabels", or "demotiles". If it is a URL, it must point to
                a MapLibre style JSON. Defaults to "dark-matter".
            height (str, optional): The height of the map. Defaults to "600px".
            controls (dict, optional): The controls and their positions on the
                map. Defaults to {"fullscreen": "top-right", "scale": "bottom-left"}.
            **kwargs: Additional keyword arguments that are passed to the MapOptions class.
                See https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/MapOptions/
                for more information.

        Returns:
            None
        """
        carto_basemaps = [
            "dark-matter",
            "positron",
            "voyager",
            "positron-nolabels",
            "dark-matter-nolabels",
            "voyager-nolabels",
        ]
        if isinstance(style, str):

            if style.startswith("https"):
                response = requests.get(style)
                if response.status_code != 200:
                    style = "dark-matter"

            if style.lower() in carto_basemaps:
                style = construct_carto_basemap_url(style.lower())
            elif style == "demotiles":
                style = "https://demotiles.maplibre.org/style.json"
            elif "background-" in style:
                color = style.split("-")[1]
                style = background(color)
            elif style == "3d-terrain":
                style = self._get_3d_terrain_style()

        if style is not None:
            kwargs["style"] = style
        map_options = MapOptions(
            center=center, zoom=zoom, pitch=pitch, bearing=bearing, **kwargs
        )

        super().__init__(map_options, height=height)
        super().use_message_queue()

        for control, position in controls.items():
            self.add_control(control, position)

        self.layer_dict = {}
        self.layer_dict["background"] = {
            "layer": Layer(id="background", type=LayerType.BACKGROUND),
            "opacity": 1.0,
            "visible": True,
            "type": "background",
            "color": None,
        }

    def add_layer(
        self,
        layer: "Layer",
        before_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Adds a layer to the map.

        This method adds a layer to the map. If a name is provided, it is used
            as the key to store the layer in the layer dictionary. Otherwise,
            the layer's ID is used as the key. If a before_id is provided, the
            layer is inserted before the layer with that ID.

        Args:
            layer (Layer): The layer object to add to the map.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            name (str, optional): The name to use as the key to store the layer
                in the layer dictionary. If None, the layer's ID is used as the key.

        Returns:
            None
        """
        if isinstance(layer, dict):
            layer = replace_top_level_hyphens(layer)
            layer = Layer(**layer)

        if name is None:
            name = layer.id

        if (
            "paint" in layer.to_dict()
            and f"{layer.type}-color" in layer.paint
            and isinstance(layer.paint[f"{layer.type}-color"], str)
        ):
            color = check_color(layer.paint[f"{layer.type}-color"])
        else:
            color = None

        self.layer_dict[name] = {
            "layer": layer,
            "opacity": 1.0,
            "visible": True,
            "type": layer.type,
            "color": color,
        }
        super().add_layer(layer, before_id=before_id)

    def remove_layer(self, name: str) -> None:
        """
        Removes a layer from the map.

        This method removes a layer from the map using the layer's name.

        Args:
            name (str): The name of the layer to remove.

        Returns:
            None
        """

        if name in self.layer_dict:
            super().add_call("removeLayer", name)
            self.layer_dict.pop(name)

    def add_control(
        self, control: Union[str, Any], position: str = "top-right", **kwargs: Any
    ) -> None:
        """
        Adds a control to the map.

        This method adds a control to the map. The control can be one of the
            following: 'scale', 'fullscreen', 'geolocate', 'navigation'. If the
            control is a string, it is converted to the corresponding control object.
            If the control is not a string, it is assumed to be a control object.

        Args:
            control (str or object): The control to add to the map. Can be one
                of the following: 'scale', 'fullscreen', 'geolocate', 'navigation'.
            position (str, optional): The position of the control. Defaults to "top-right".
            **kwargs: Additional keyword arguments that are passed to the control object.

        Returns:
            None

        Raises:
            ValueError: If the control is a string and is not one of the
                following: 'scale', 'fullscreen', 'geolocate', 'navigation'.
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

    def set_center(self, lon: float, lat: float, zoom: Optional[int] = None) -> None:
        """
        Sets the center of the map.

        This method sets the center of the map to the specified longitude and latitude.
        If a zoom level is provided, it also sets the zoom level of the map.

        Args:
            lon (float): The longitude of the center of the map.
            lat (float): The latitude of the center of the map.
            zoom (int, optional): The zoom level of the map. If None, the zoom
                level is not changed.

        Returns:
            None
        """
        center = [lon, lat]
        self.add_call("setCenter", center)

        if zoom is not None:
            self.add_call("setZoom", zoom)

    def set_zoom(self, zoom: Optional[int] = None) -> None:
        """
        Sets the zoom level of the map.

        This method sets the zoom level of the map to the specified value.

        Args:
            zoom (int): The zoom level of the map.

        Returns:
            None
        """
        self.add_call("setZoom", zoom)

    def fit_bounds(self, bounds: List[Tuple[float, float]]) -> None:
        """
        Adjusts the viewport of the map to fit the specified geographical bounds
            in the format of [[lon_min, lat_min], [lon_max, lat_max]] or
            [lon_min, lat_min, lon_max, lat_max].

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

        if isinstance(bounds, list):
            if len(bounds) == 4 and all(isinstance(i, (int, float)) for i in bounds):
                bounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]

        self.add_call("fitBounds", bounds)

    def add_basemap(
        self,
        basemap: Union[str, xyzservices.TileProvider] = None,
        opacity: float = 1.0,
        visible: bool = True,
        attribution: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a basemap to the map.

        This method adds a basemap to the map. The basemap can be a string from
        predefined basemaps, an instance of xyzservices.TileProvider, or a key
        from the basemaps dictionary.

        Args:
            basemap (str or TileProvider, optional): The basemap to add. Can be
                one of the predefined strings, an instance of xyzservices.TileProvider,
                or a key from the basemaps dictionary. Defaults to None, which adds
                the basemap widget.
            opacity (float, optional): The opacity of the basemap. Defaults to 1.0.
            visible (bool, optional): Whether the basemap is visible or not.
                Defaults to True.
            attribution (str, optional): The attribution text to display for the
                basemap. If None, the attribution text is taken from the basemap
                or the TileProvider. Defaults to None.
            **kwargs: Additional keyword arguments that are passed to the
                RasterTileSource class. See https://bit.ly/4erD2MQ for more information.

        Returns:
            None

        Raises:
            ValueError: If the basemap is not one of the predefined strings,
                not an instance of TileProvider, and not a key from the basemaps dictionary.
        """

        if basemap is None:
            return self._basemap_widget()

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
            tile_size=256,
            **kwargs,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
        self.add_layer(layer)
        self.set_opacity(name, opacity)
        self.set_visibility(name, visible)

    def add_geojson(
        self,
        data: Union[str, Dict],
        layer_type: Optional[str] = None,
        filter: Optional[Dict] = None,
        paint: Optional[Dict] = None,
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a GeoJSON layer to the map.

        This method adds a GeoJSON layer to the map. The GeoJSON data can be a
        URL to a GeoJSON file or a GeoJSON dictionary. If a name is provided, it
        is used as the key to store the layer in the layer dictionary. Otherwise,
        a random name is generated.

        Args:
            data (str | dict): The GeoJSON data. This can be a URL to a GeoJSON
                file or a GeoJSON dictionary.
            layer_type (str, optional): The type of the layer. It can be one of
                the following: 'circle', 'fill', 'fill-extrusion', 'line', 'symbol',
                'raster', 'background', 'heatmap', 'hillshade'. If None, the type
                is inferred from the GeoJSON data.
            filter (dict, optional): The filter to apply to the layer. If None,
                no filter is applied.
            paint (dict, optional): The paint properties to apply to the layer.
                If None, no paint properties are applied.
            name (str, optional): The name of the layer. If None, a random name
                is generated.
            fit_bounds (bool, optional): Whether to adjust the viewport of the
                map to fit the bounds of the GeoJSON data. Defaults to True.
            visible (bool, optional): Whether the layer is visible or not.
                Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the GeoJSONSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://maplibre.org/maplibre-style-spec/layers/ for more info.

        Returns:
            None

        Raises:
            ValueError: If the data is not a URL or a GeoJSON dictionary.
        """

        import os

        bounds = None
        geom_type = None

        if isinstance(data, str):
            if os.path.isfile(data) or data.startswith("http"):
                data = gpd.read_file(data).__geo_interface__
                bounds = get_bounds(data)
                source = GeoJSONSource(data=data, **source_args)
            else:
                raise ValueError("The data must be a URL or a GeoJSON dictionary.")
        elif isinstance(data, dict):
            source = GeoJSONSource(data=data, **source_args)

            bounds = get_bounds(data)
        else:
            raise ValueError("The data must be a URL or a GeoJSON dictionary.")

        if name is None:
            name = "geojson_" + random_string()

        if filter is not None:
            kwargs["filter"] = filter
        if paint is None:
            geom_type = data["features"][0]["geometry"]["type"]
            print(geom_type)
            if geom_type in ["Point", "MultiPoint"]:
                if layer_type is None:
                    layer_type = "circle"
                paint = {
                    "circle-radius": 5,
                    "circle-color": "#3388ff",
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1,
                }
            elif geom_type in ["LineString", "MultiLineString"]:
                if layer_type is None:
                    layer_type = "line"
                paint = {"line-color": "#3388ff", "line-width": 2}
            elif geom_type in ["Polygon", "MultiPolygon"]:
                if layer_type is None:
                    layer_type = "fill"
                paint = {
                    "fill-color": "#3388ff",
                    "fill-opacity": 0.8,
                    "fill-outline-color": "#ffffff",
                }

        if paint is not None:
            kwargs["paint"] = paint

        layer = Layer(
            id=name,
            type=layer_type,
            source=source,
            **kwargs,
        )
        self.add_layer(layer, before_id=before_id, name=name)
        if fit_bounds and bounds is not None:
            self.fit_bounds(bounds)
        self.set_visibility(name, visible)

        if isinstance(paint, dict) and f"{layer_type}-opacity" in paint:
            self.set_opacity(name, paint[f"{layer_type}-opacity"])
        else:
            self.set_opacity(name, 1.0)

    def add_vector(
        self,
        data: Union[str, Dict],
        layer_type: Optional[str] = None,
        filter: Optional[Dict] = None,
        paint: Optional[Dict] = None,
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a vector layer to the map.

        This method adds a vector layer to the map. The vector data can be a
        URL or local file path to a vector file. If a name is provided, it
        is used as the key to store the layer in the layer dictionary. Otherwise,
        a random name is generated.

        Args:
            data (str | dict): The vector data. This can be a URL or local file
                path to a vector file.
            layer_type (str, optional): The type of the layer. If None, the type
                is inferred from the GeoJSON data.
            filter (dict, optional): The filter to apply to the layer. If None,
                no filter is applied.
            paint (dict, optional): The paint properties to apply to the layer.
                If None, no paint properties are applied.
            name (str, optional): The name of the layer. If None, a random name
                is generated.
            fit_bounds (bool, optional): Whether to adjust the viewport of the
                map to fit the bounds of the GeoJSON data. Defaults to True.
            visible (bool, optional): Whether the layer is visible or not.
                Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the GeoJSONSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.

        Returns:
            None

        Raises:
            ValueError: If the data is not a URL or a GeoJSON dictionary.
        """

        if not isinstance(data, gpd.GeoDataFrame):
            data = gpd.read_file(data).__geo_interface__

        self.add_geojson(
            data,
            layer_type=layer_type,
            filter=filter,
            paint=paint,
            name=name,
            fit_bounds=fit_bounds,
            visible=visible,
            before_id=before_id,
            source_args=source_args,
            **kwargs,
        )

    def add_tile_layer(
        self,
        url: str,
        name: str = "Tile Layer",
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        tile_size: int = 256,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a TileLayer to the map.

        This method adds a TileLayer to the map. The TileLayer is created from
            the specified URL, and it is added to the map with the specified
            name, attribution, visibility, and tile size.

        Args:
            url (str): The URL of the tile layer.
            name (str, optional): The name to use for the layer. Defaults to '
                Tile Layer'.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            visible (bool, optional): Whether the layer should be visible by
                default. Defaults to True.
            tile_size (int, optional): The size of the tiles in the layer.
                Defaults to 256.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the RasterTileSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.

        Returns:
            None
        """

        raster_source = RasterTileSource(
            tiles=[url.strip()],
            attribution=attribution,
            tile_size=tile_size,
            **source_args,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER, **kwargs)
        self.add_layer(layer, before_id=before_id, name=name)
        self.set_visibility(name, visible)
        self.set_opacity(name, opacity)

    def add_wms_layer(
        self,
        url: str,
        name: str = "WMS Layer",
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        tile_size: int = 256,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a WMS layer to the map.

        This method adds a WMS layer to the map. The WMS  is created from
            the specified URL, and it is added to the map with the specified
            name, attribution, visibility, and tile size.

        Args:
            url (str): The URL of the tile layer.
            name (str, optional): The name to use for the layer. Defaults to
                'WMS Layer'.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            visible (bool, optional): Whether the layer should be visible by
                default. Defaults to True.
            tile_size (int, optional): The size of the tiles in the layer.
                Defaults to 256.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the RasterTileSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.

        Returns:
            None
        """
        self.add_tile_layer(
            url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            visible=visible,
            tile_size=tile_size,
            before_id=before_id,
            source_args=source_args,
            **kwargs,
        )

    def add_ee_layer(
        self,
        asset_id: str,
        name: str = None,
        opacity: float = 1.0,
        attribution: str = "Google Earth Engine",
        visible: bool = True,
        before_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Adds a Google Earth Engine tile layer to the map based on the tile layer URL from
            https://github.com/opengeos/ee-tile-layers/blob/main/datasets.tsv.

        Args:
            asset_id (str): The ID of the Earth Engine asset.
            name (str, optional): The name of the tile layer. If not provided,
                the asset ID will be used. Default is None.
            opacity (float, optional): The opacity of the tile layer (0 to 1).
                Default is 1.
            attribution (str, optional): The attribution text to be displayed.
                Default is "Google Earth Engine".
            visible (bool, optional): Whether the tile layer should be shown on
                the map. Default is True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            **kwargs: Additional keyword arguments to be passed to the underlying
                `add_tile_layer` method.

        Returns:
            None
        """
        import pandas as pd

        df = pd.read_csv(
            "https://raw.githubusercontent.com/opengeos/ee-tile-layers/main/datasets.tsv",
            sep="\t",
        )

        asset_id = asset_id.strip()
        if name is None:
            name = asset_id

        if asset_id in df["id"].values:
            url = df.loc[df["id"] == asset_id, "url"].values[0]
            self.add_tile_layer(
                url,
                name,
                attribution=attribution,
                opacity=opacity,
                visible=visible,
                before_id=before_id,
                **kwargs,
            )
        else:
            print(f"The provided EE tile layer {asset_id} does not exist.")

    def add_cog_layer(
        self,
        url: str,
        name: Optional[str] = None,
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        bands: Optional[List[int]] = None,
        titiler_endpoint: str = "https://titiler.xyz",
        fit_bounds: bool = True,
        before_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a Cloud Optimized Geotiff (COG) TileLayer to the map.

        This method adds a COG TileLayer to the map. The COG TileLayer is created
        from the specified URL, and it is added to the map with the specified name,
        attribution, opacity, visibility, and bands.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The name to use for the layer. If None, a
                random name is generated. Defaults to None.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            visible (bool, optional): Whether the layer should be visible by default.
                Defaults to True.
            bands (list, optional): A list of bands to use for the layer.
                Defaults to None.
            titiler_endpoint (str, optional): The endpoint of the titiler service.
                Defaults to "https://titiler.xyz".
            fit_bounds (bool, optional): Whether to adjust the viewport of
                the map to fit the bounds of the layer. Defaults to True.
            **kwargs: Arbitrary keyword arguments, including bidx, expression,
                nodata, unscale, resampling, rescale, color_formula, colormap,
                    colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/.
                    To select a certain bands, use bidx=[1, 2, 3]. apply a
                        rescaling to multiple bands, use something like
                        `rescale=["164,223","130,211","99,212"]`.
        Returns:
            None
        """

        if name is None:
            name = "COG_" + random_string()

        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(
            tile_url, name, attribution, opacity, visible, before_id=before_id
        )
        if fit_bounds:
            self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

    def add_stac_layer(
        self,
        url: Optional[str] = None,
        collection: Optional[str] = None,
        item: Optional[str] = None,
        assets: Optional[Union[str, List[str]]] = None,
        bands: Optional[List[str]] = None,
        titiler_endpoint: Optional[str] = None,
        name: str = "STAC Layer",
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        fit_bounds: bool = True,
        before_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a STAC TileLayer to the map.

        This method adds a STAC TileLayer to the map. The STAC TileLayer is
        created from the specified URL, collection, item, assets, and bands, and
        it is added to the map with the specified name, attribution, opacity,
        visibility, and fit bounds.

        Args:
            url (str, optional): HTTP URL to a STAC item, e.g., https://bit.ly/3VlttGm.
                Defaults to None.
            collection (str, optional): The Microsoft Planetary Computer STAC
                collection ID, e.g., landsat-8-c2-l2. Defaults to None.
            item (str, optional): The Microsoft Planetary Computer STAC item ID, e.g.,
                LC08_L2SP_047027_20201204_02_T1. Defaults to None.
            assets (str | list, optional): The Microsoft Planetary Computer STAC asset ID,
                e.g., ["SR_B7", "SR_B5", "SR_B4"]. Defaults to None.
            bands (list, optional): A list of band names, e.g.,
                ["SR_B7", "SR_B5", "SR_B4"]. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz",
                "https://planetarycomputer.microsoft.com/api/data/v1",
                "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            visible (bool, optional): A flag indicating whether the layer should
                be on by default. Defaults to True.
            fit_bounds (bool, optional): A flag indicating whether the map should
                be zoomed to the layer extent. Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            **kwargs: Arbitrary keyword arguments, including bidx, expression,
                nodata, unscale, resampling, rescale, color_formula, colormap,
                colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select
                a certain bands, use bidx=[1, 2, 3]. apply a rescaling to multiple
                bands, use something like `rescale=["164,223","130,211","99,212"]`.

        Returns:
            None
        """
        if "colormap_name" in kwargs and kwargs["colormap_name"] is None:
            kwargs.pop("colormap_name")

        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(
            tile_url, name, attribution, opacity, visible, before_id=before_id
        )
        if fit_bounds:
            self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

    def add_raster(
        self,
        source,
        indexes=None,
        colormap=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution="Localtileserver",
        name="Raster",
        before_id=None,
        fit_bounds=True,
        visible=True,
        opacity=1.0,
        array_args={},
        client_args={"cors_all": True},
        **kwargs,
    ):
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server
            (e.g., Binder, Microsoft Planetary Computer) and if the raster
            does not render properly, try installing jupyter-server-proxy using
            `pip install jupyter-server-proxy`, then running the following code
            before calling this function. For more info, see https://bit.ly/3JbmF93.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud
                Optimized GeoTIFF.
            indexes (int, optional): The band(s) to use. Band indexing starts
                at 1. Defaults to None.
            colormap (str, optional): The name of the colormap from `matplotlib`
                to use when plotting a single band.
                See https://matplotlib.org/stable/gallery/color/colormap_reference.html.
                Default is greyscale.
            vmin (float, optional): The minimum value to use when colormapping
                the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping
                the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret
                as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This
                defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Raster'.
            layer_index (int, optional): The index of the layer. Defaults to None.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the
                layer. Defaults to True.
            visible (bool, optional): Whether the layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            array_args (dict, optional): Additional arguments to pass to
                `array_to_memory_file` when reading the raster. Defaults to {}.
            client_args (dict, optional): Additional arguments to pass to
                localtileserver.TileClient. Defaults to { "cors_all": False }.
        """
        import numpy as np
        import xarray as xr

        if isinstance(source, np.ndarray) or isinstance(source, xr.DataArray):
            source = array_to_image(source, **array_args)

        tile_layer, tile_client = get_local_tile_layer(
            source,
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            opacity=opacity,
            attribution=attribution,
            layer_name=name,
            client_args=client_args,
            return_client=True,
            **kwargs,
        )

        self.add_tile_layer(
            tile_layer.url,
            name=name,
            opacity=opacity,
            visible=visible,
            attribution=attribution,
            before_id=before_id,
        )

        bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
        bounds = [[bounds[2], bounds[0]], [bounds[3], bounds[1]]]
        # [minx, miny, maxx, maxy]
        if fit_bounds:
            self.fit_bounds(bounds)

    def to_html(
        self,
        title: str = "Map",
        width: str = "100%",
        height: str = "880px",
        output: str = None,
        **kwargs,
    ):
        """Render the map to an HTML page.

        Args:
            title (str, optional): The title of the HTML page. Defaults to 'Map'.
            width (str, optional): The width of the map. Defaults to '100%'.
            height (str, optional): The height of the map. Defaults to '880px'.
            **kwargs: Additional keyword arguments that are passed to the
                `maplibre.ipywidget.MapWidget.to_html()` method.

        Returns:
            str: The HTML content of the map.
        """

        if "style" not in kwargs:
            kwargs["style"] = f"width: {width}; height: {height};"
        else:
            kwargs["style"] += f"width: {width}; height: {height};"
        html = super().to_html(title=title, **kwargs)
        if output:
            with open(output, "w") as f:
                f.write(html)
        else:
            return html

    def set_paint_property(self, name: str, prop: str, value: Any) -> None:
        """
        Set the opacity of a layer.

        This method sets the opacity of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            opacity (float): The opacity value to set.

        Returns:
            None
        """
        super().set_paint_property(name, prop, value)

        if "opacity" in prop:
            self.layer_dict[name]["opacity"] = value

    def set_color(self, name: str, color: str) -> None:
        """
        Set the color of a layer.

        This method sets the color of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            color (str): The color value to set.

        Returns:
            None
        """
        color = check_color(color)
        super().set_paint_property(
            name, f"{self.layer_dict[name]['layer'].type}-color", color
        )
        self.layer_dict[name]["color"] = color

    def set_opacity(self, name: str, opacity: float) -> None:
        """
        Set the opacity of a layer.

        This method sets the opacity of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            opacity (float): The opacity value to set.

        Returns:
            None
        """
        layer_type = self.layer_dict[name]["layer"].to_dict()["type"]
        prop_name = f"{layer_type}-opacity"

        super().set_paint_property(name, prop_name, opacity)
        self.layer_dict[name]["opacity"] = opacity

    def set_visibility(self, name: str, visible: bool) -> None:
        """
        Set the visibility of a layer.

        This method sets the visibility of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            visible (bool): The visibility value to set.

        Returns:
            None
        """
        super().set_visibility(name, visible)
        self.layer_dict[name]["visible"] = visible

    def layer_interact(self, name=None):
        """Create a layer widget for changing the visibility and opacity of a layer.

        Args:
            name (str): The name of the layer.

        Returns:
            ipywidgets.Widget: The layer widget.
        """

        import ipywidgets as widgets

        layer_names = list(self.layer_dict.keys())
        if name is None:
            name = layer_names[-1]
        elif name not in layer_names:
            raise ValueError(f"Layer {name} not found.")

        style = {"description_width": "initial"}
        dropdown = widgets.Dropdown(
            options=layer_names,
            value=name,
            description="Layer",
            style=style,
        )
        checkbox = widgets.Checkbox(
            description="Visible",
            value=self.layer_dict[name]["visible"],
            style=style,
            layout=widgets.Layout(width="120px"),
        )
        opacity_slider = widgets.FloatSlider(
            description="Opacity",
            min=0,
            max=1,
            step=0.01,
            value=self.layer_dict[name]["opacity"],
            style=style,
        )

        color_picker = widgets.ColorPicker(
            concise=True,
            value="white",
            style=style,
        )

        if self.layer_dict[name]["color"] is not None:
            color_picker.value = self.layer_dict[name]["color"]
            color_picker.disabled = False
        else:
            color_picker.value = "white"
            color_picker.disabled = True

        def color_picker_event(change):
            if self.layer_dict[dropdown.value]["color"] is not None:
                self.set_color(dropdown.value, change.new)

        color_picker.observe(color_picker_event, "value")

        hbox = widgets.HBox(
            [dropdown, checkbox, opacity_slider, color_picker],
            layout=widgets.Layout(width="750px"),
        )

        def dropdown_event(change):
            name = change.new
            checkbox.value = self.layer_dict[dropdown.value]["visible"]
            opacity_slider.value = self.layer_dict[dropdown.value]["opacity"]
            if self.layer_dict[dropdown.value]["color"] is not None:
                color_picker.value = self.layer_dict[dropdown.value]["color"]
                color_picker.disabled = False
            else:
                color_picker.value = "white"
                color_picker.disabled = True

        dropdown.observe(dropdown_event, "value")

        def update_layer(change):
            self.set_visibility(dropdown.value, checkbox.value)
            self.set_opacity(dropdown.value, opacity_slider.value)

        checkbox.observe(update_layer, "value")
        opacity_slider.observe(update_layer, "value")

        return hbox

    def _basemap_widget(self, name=None):
        """Create a layer widget for changing the visibility and opacity of a layer.

        Args:
            name (str): The name of the layer.

        Returns:
            ipywidgets.Widget: The layer widget.
        """

        import ipywidgets as widgets

        layer_names = [
            basemaps[basemap]["name"]
            for basemap in basemaps.keys()
            if "layers" not in basemaps[basemap]
        ][1:]
        if name is None:
            name = layer_names[0]
        elif name not in layer_names:
            raise ValueError(f"Layer {name} not found.")

        tile = basemaps[name]
        raster_source = RasterTileSource(
            tiles=[tile["url"]],
            attribution=tile["attribution"],
            tile_size=256,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
        self.add_layer(layer)
        self.set_opacity(name, 1.0)
        self.set_visibility(name, True)

        style = {"description_width": "initial"}
        dropdown = widgets.Dropdown(
            options=layer_names,
            value=name,
            description="Basemap",
            style=style,
        )
        checkbox = widgets.Checkbox(
            description="Visible",
            value=self.layer_dict[name]["visible"],
            style=style,
            layout=widgets.Layout(width="120px"),
        )
        opacity_slider = widgets.FloatSlider(
            description="Opacity",
            min=0,
            max=1,
            step=0.01,
            value=self.layer_dict[name]["opacity"],
            style=style,
        )
        hbox = widgets.HBox(
            [dropdown, checkbox, opacity_slider], layout=widgets.Layout(width="600px")
        )

        def dropdown_event(change):
            old = change["old"]
            name = change.new
            self.remove_layer(old)

            tile = basemaps[name]
            raster_source = RasterTileSource(
                tiles=[tile["url"]],
                attribution=tile["attribution"],
                tile_size=256,
            )
            layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
            self.add_layer(layer)
            self.set_opacity(name, 1.0)
            self.set_visibility(name, True)

            checkbox.value = self.layer_dict[dropdown.value]["visible"]
            opacity_slider.value = self.layer_dict[dropdown.value]["opacity"]

        dropdown.observe(dropdown_event, "value")

        def update_layer(change):
            self.set_visibility(dropdown.value, checkbox.value)
            self.set_opacity(dropdown.value, opacity_slider.value)

        checkbox.observe(update_layer, "value")
        opacity_slider.observe(update_layer, "value")

        return hbox

    def add_pmtiles(
        self,
        url: str,
        style: Optional[Dict] = None,
        visible: bool = True,
        opacity: float = 1.0,
        exclude_mask: bool = False,
        tooltip: bool = True,
        properties: Optional[Dict] = None,
        template: Optional[str] = None,
        attribution: str = "PMTiles",
        fit_bounds: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Adds a PMTiles layer to the map.

        Args:
            url (str): The URL of the PMTiles file.
            style (dict, optional): The CSS style to apply to the layer. Defaults to None.
                See https://docs.mapbox.com/style-spec/reference/layers/ for more info.
            visible (bool, optional): Whether the layer should be shown initially. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            exclude_mask (bool, optional): Whether to exclude the mask layer. Defaults to False.
            tooltip (bool, optional): Whether to show tooltips on the layer. Defaults to True.
            properties (dict, optional): The properties to use for the tooltips. Defaults to None.
            template (str, optional): The template to use for the tooltips. Defaults to None.
            attribution (str, optional): The attribution to use for the layer. Defaults to 'PMTiles'.
            fit_bounds (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the PMTilesLayer constructor.

        Returns:
            None
        """

        try:

            if "sources" in kwargs:
                del kwargs["sources"]

            if "version" in kwargs:
                del kwargs["version"]

            pmtiles_source = {
                "type": "vector",
                "url": f"pmtiles://{url}",
                "attribution": attribution,
            }

            if style is None:
                style = pmtiles_style(url)

            if "sources" in style:
                source_name = list(style["sources"].keys())[0]
            elif "layers" in style:
                source_name = style["layers"][0]["source"]
            else:
                source_name = "source"

            self.add_source(source_name, pmtiles_source)

            style = replace_hyphens_in_keys(style)

            for params in style["layers"]:

                if exclude_mask and params.get("source_layer") == "mask":
                    continue

                layer = Layer(**params)
                self.add_layer(layer)
                self.set_visibility(params["id"], visible)
                self.set_opacity(params["id"], opacity)

                if tooltip:
                    self.add_tooltip(params["id"], properties, template)

            if fit_bounds:
                metadata = pmtiles_metadata(url)
                bounds = metadata["bounds"]  # [minx, miny, maxx, maxy]
                self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

        except Exception as e:
            print(e)

    def add_marker(
        self,
        lng_lat: List[Union[float, float]],
        popup: Optional[Dict] = {},
        options: Optional[Dict] = {},
    ) -> None:
        """
        Adds a marker to the map.

        Args:
            lng_lat (List[Union[float, float]]): A list of two floats
                representing the longitude and latitude of the marker.
            popup (Optional[str], optional): The text to display in a popup when
                the marker is clicked. Defaults to None.
            options (Optional[Dict], optional): A dictionary of options to
                customize the marker. Defaults to None.

        Returns:
            None
        """

        marker = Marker(lng_lat=lng_lat, popup=popup, options=options)
        super().add_marker(marker)

    def fly_to(
        self,
        lon: float,
        lat: float,
        zoom: Optional[float] = None,
        speed: Optional[float] = None,
        essential: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Makes the map fly to a specified location.

        Args:
            lon (float): The longitude of the location to fly to.
            lat (float): The latitude of the location to fly to.
            zoom (Optional[float], optional): The zoom level to use when flying
                to the location. Defaults to None.
            speed (Optional[float], optional): The speed of the fly animation.
                Defaults to None.
            essential (bool, optional): Whether the flyTo animation is considered
                essential and not affected by prefers-reduced-motion. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the flyTo function.

        Returns:
            None
        """

        center = [lon, lat]
        kwargs["center"] = center
        if zoom is not None:
            kwargs["zoom"] = zoom
        if speed is not None:
            kwargs["speed"] = speed
        if essential:
            kwargs["essential"] = essential

        super().add_call("flyTo", kwargs)

    def _read_image(self, image: str) -> Dict[str, Union[int, List[int]]]:
        """
        Reads an image from a URL or a local file path and returns a dictionary
            with the image data.

        Args:
            image (str): The URL or local file path to the image.

        Returns:
            Dict[str, Union[int, List[int]]]: A dictionary with the image width,
                height, and flattened data.

        Raises:
            ValueError: If the image argument is not a string representing a URL
                or a local file path.
        """

        import os
        from PIL import Image
        import requests
        from io import BytesIO
        import numpy as np

        if isinstance(image, str):
            try:
                if os.path.isfile(image):
                    img = Image.open(image)
                else:
                    response = requests.get(image)
                    img = Image.open(BytesIO(response.content))

                width, height = img.size

                # Convert image to numpy array and then flatten it
                img_data = np.array(img, dtype="uint8")
                flat_img_data = img_data.flatten()

                # Create the image dictionary with the flattened data
                image_dict = {
                    "width": width,
                    "height": height,
                    "data": flat_img_data.tolist(),  # Convert to list if necessary
                }

                return image_dict
            except Exception as e:
                print(e)
                return None
        else:
            raise ValueError("The image must be a URL or a local file path.")

    def add_image(
        self, id: str, image: Union[str, Dict], width: int = None, height: int = None
    ) -> None:
        """Add an image to the map.

        Args:
            id (str): The layer ID of the image.
            image (Union[str, Dict, np.ndarray]): The URL or local file path to
                the image, or a dictionary containing image data, or a numpy
                array representing the image.
            width (int, optional): The width of the image. Defaults to None.
            height (int, optional): The height of the image. Defaults to None.

        Returns:
            None
        """
        import numpy as np

        if isinstance(image, str):
            image_dict = self._read_image(image)
        elif isinstance(image, dict):
            image_dict = image
        elif isinstance(image, np.ndarray):
            image_dict = {
                "width": width,
                "height": height,
                "data": image.tolist(),
            }
        else:
            raise ValueError(
                "The image must be a URL, a local file path, or a numpy array."
            )
        super().add_call("addImage", id, image_dict)

    def to_streamlit(
        self,
        width: Optional[int] = None,
        height: Optional[int] = 600,
        scrolling: Optional[bool] = False,
        **kwargs: Any,
    ) -> Any:
        """
        Convert the map to a Streamlit component.

        This function converts the map to a Streamlit component by encoding the
        HTML representation of the map as base64 and embedding it in an iframe.
        The width, height, and scrolling parameters control the appearance of
        the iframe.

        Args:
            width (Optional[int]): The width of the iframe. If None, the width
                will be determined by Streamlit.
            height (Optional[int]): The height of the iframe. Default is 600.
            scrolling (Optional[bool]): Whether the iframe should be scrollable.
                Default is False.
            **kwargs (Any): Additional arguments to pass to the Streamlit iframe
                function.

        Returns:
            Any: The Streamlit component.

        Raises:
            Exception: If there is an error in creating the Streamlit component.
        """

        try:
            import streamlit.components.v1 as components
            import base64

            raw_html = self.to_html().encode("utf-8")
            raw_html = base64.b64encode(raw_html).decode()
            return components.iframe(
                f"data:text/html;base64,{raw_html}",
                width=width,
                height=height,
                scrolling=scrolling,
                **kwargs,
            )

        except Exception as e:
            raise Exception(e)

    def rotate_to(
        self, bearing: float, options: Dict[str, Any] = {}, **kwargs: Any
    ) -> None:
        """
        Rotate the map to a specified bearing.

        This function rotates the map to a specified bearing. The bearing is specified in degrees
        counter-clockwise from true north. If the bearing is not specified, the map will rotate to
        true north. Additional options and keyword arguments can be provided to control the rotation.
        For more information, see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#rotateto

        Args:
            bearing (float): The bearing to rotate to, in degrees counter-clockwise from true north.
            options (Dict[str, Any], optional): Additional options to control the rotation. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the rotation.

        Returns:
            None
        """
        super().add_call("rotateTo", bearing, options, **kwargs)

    def open_geojson(self, **kwargs: Any) -> "widgets.FileUpload":
        """
        Creates a file uploader widget to upload a GeoJSON file. When a file is
        uploaded, it is written to a temporary file and added to the map.

        Args:
            **kwargs: Additional keyword arguments to pass to the add_geojson method.

        Returns:
            widgets.FileUpload: The file uploader widget.
        """

        import ipywidgets as widgets

        uploader = widgets.FileUpload(
            accept=".geojson",  # Accept GeoJSON files
            multiple=False,  # Only single file upload
            description="Open GeoJSON",
        )

        def on_upload(change):
            content = uploader.value[0]["content"]
            temp_file = temp_file_path(extension=".geojson")
            with open(temp_file, "wb") as f:
                f.write(content)
            self.add_geojson(temp_file, **kwargs)

        uploader.observe(on_upload, names="value")

        return uploader

    def pan_to(
        self,
        lnglat: List[float],
        options: Dict[str, Any] = {},
        **kwargs: Any,
    ) -> None:
        """
        Pans the map to a specified location.

        This function pans the map to the specified longitude and latitude coordinates.
        Additional options and keyword arguments can be provided to control the panning.
        For more information, see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#panto

        Args:
            lnglat (List[float, float]): The longitude and latitude coordinates to pan to.
            options (Dict[str, Any], optional): Additional options to control the panning. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the panning.

        Returns:
            None
        """
        super().add_call("panTo", lnglat, options, **kwargs)

    def set_pitch(self, pitch: float, **kwargs: Any) -> None:
        """
        Sets the pitch of the map.

        This function sets the pitch of the map to the specified value. The pitch is the
        angle of the camera measured in degrees where 0 is looking straight down, and 60 is
        looking towards the horizon. Additional keyword arguments can be provided to control
        the pitch. For more information, see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#setpitch

        Args:
            pitch (float): The pitch value to set.
            **kwargs (Any): Additional keyword arguments to control the pitch.

        Returns:
            None
        """
        super().add_call("setPitch", pitch, **kwargs)

    def jump_to(self, options: Dict[str, Any] = {}, **kwargs: Any) -> None:
        """
        Jumps the map to a specified location.

        This function jumps the map to the specified location with the specified options.
        Additional keyword arguments can be provided to control the jump. For more information,
        see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#jumpto

        Args:
            options (Dict[str, Any], optional): Additional options to control the jump. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the jump.

        Returns:
            None
        """
        super().add_call("jumpTo", options, **kwargs)

    def _get_3d_terrain_style(
        self,
        exaggeration: float = 1,
        token: str = "MAPTILER_KEY",
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the 3D terrain style for the map.

        This function generates a style dictionary for the map that includes 3D terrain features.
        The terrain exaggeration and API key can be specified. If the API key is not provided,
        it will be retrieved using the specified token.

        Args:
            exaggeration (float, optional): The terrain exaggeration. Defaults to 1.
            token (str, optional): The token to use to retrieve the API key. Defaults to "MAPTILER_KEY".
            api_key (Optional[str], optional): The API key. If not provided, it will be retrieved using the token.

        Returns:
            Dict[str, Any]: The style dictionary for the map.

        Raises:
            ValueError: If the API key is not provided and cannot be retrieved using the token.
        """

        if api_key is None:
            api_key = get_api_key(token)

        if api_key is None:
            raise ValueError("An API key is required to use the 3D terrain feature.")

        style = {
            "version": 8,
            "sources": {
                "satellite": {
                    "type": "raster",
                    "tiles": [
                        "https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key="
                        + api_key
                    ],
                    "tileSize": 256,
                    "attribution": "&copy; MapTiler",
                    "maxzoom": 19,
                },
                "terrainSource": {
                    "type": "raster-dem",
                    "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                    "tileSize": 256,
                },
                "hillshadeSource": {
                    "type": "raster-dem",
                    "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                    "tileSize": 256,
                },
            },
            "layers": [
                {"id": "satellite", "type": "raster", "source": "satellite"},
                {
                    "id": "hills",
                    "type": "hillshade",
                    "source": "hillshadeSource",
                    "layout": {"visibility": "visible"},
                    "paint": {"hillshade-shadow-color": "#473B24"},
                },
            ],
            "terrain": {"source": "terrainSource", "exaggeration": exaggeration},
        }

        return style
