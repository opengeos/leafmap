"""The maplibregl module provides the Map class for creating interactive maps using the maplibre.ipywidget module."""

import os
import requests
from typing import Tuple, Dict, Any, Optional, Union, List
from IPython.display import display

import xyzservices
import geopandas as gpd
import ipyvuetify as v
import pandas as pd
import ipywidgets as widgets
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
    AttributionControl,
    Marker,
)

from .basemaps import xyz_to_leaflet
from . import common
from .common import (
    download_file,
    find_files,
    execute_maplibre_notebook_dir,
    generate_index_html,
    geojson_to_pmtiles,
    get_api_key,
    get_bounds,
    get_overture_data,
    geojson_bounds,
    geojson_to_gdf,
    pandas_to_geojson,
    pmtiles_metadata,
    pmtiles_style,
    random_string,
    read_geojson,
    stac_assets,
    start_server,
)

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
                If it is a string, it must be one of the following: "dark-matter", "positron",
                "carto-positron", "voyager", "positron-nolabels", "dark-matter-nolabels",
                "voyager-nolabels", "demotiles", "liberty", "bright", or "positron2".
                If a MapTiler API key is set, you can also use any of the MapTiler styles,
                such as aquarelle, backdrop, basic, bright, dataviz, landscape, ocean,
                openstreetmap, outdoor, satellite, streets, toner, topo, winter, etc.
                If it is a URL, it must point to a MapLibre style JSON. Defaults to "dark-matter".
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
        openfreemap_basemaps = [
            "liberty",
            "bright",
            "positron2",
        ]
        if isinstance(style, str):

            if style.startswith("https"):
                response = requests.get(style)
                if response.status_code != 200:
                    print(
                        "The provided style URL is invalid. Falling back to 'dark-matter'."
                    )
                    style = "dark-matter"
            elif style.startswith("3d-"):
                style = maptiler_3d_style(
                    style=style.replace("3d-", "").lower(),
                    exaggeration=kwargs.pop("exaggeration", 1),
                    tile_size=kwargs.pop("tile_size", 512),
                    hillshade=kwargs.pop("hillshade", True),
                )

            elif style.lower() in carto_basemaps:
                style = construct_carto_basemap_url(style.lower())
            elif style.lower() in openfreemap_basemaps:
                if style == "positron2":
                    style = "positron"
                style = f"https://tiles.openfreemap.org/styles/{style.lower()}"
            elif style == "demotiles":
                style = "https://demotiles.maplibre.org/style.json"
            elif "background-" in style:
                color = style.split("-")[1]
                style = background(color)
            else:
                style = construct_maptiler_style(style)

            if style in carto_basemaps:
                style = construct_carto_basemap_url(style)

        if style is not None:
            kwargs["style"] = style

        if len(controls) == 0:
            kwargs["attribution_control"] = False

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
        self._style = style
        self.style_dict = {}
        for layer in self.get_style_layers():
            self.style_dict[layer["id"]] = layer
        self.source_dict = {}

    def show(self) -> None:
        """Displays the map."""
        return Container(self)

    def _repr_html_(self, **kwargs):
        """Displays the map."""

        filename = os.environ.get("MAPLIBRE_OUTPUT", None)
        replace_key = os.environ.get("MAPTILER_REPLACE_KEY", False)
        if filename is not None:
            self.to_html(filename, replace_key=replace_key)

    def add_layer(
        self,
        layer: "Layer",
        before_id: Optional[str] = None,
        name: Optional[str] = None,
        opacity: float = 1.0,
        visible: bool = True,
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
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            visible (bool, optional): Whether the layer is visible by default.

        Returns:
            None
        """
        if isinstance(layer, dict):
            if "minzoom" in layer:
                layer["min-zoom"] = layer.pop("minzoom")
            if "maxzoom" in layer:
                layer["max-zoom"] = layer.pop("maxzoom")
            layer = common.replace_top_level_hyphens(layer)
            layer = Layer(**layer)

        if name is None:
            name = layer.id

        if (
            "paint" in layer.to_dict()
            and f"{layer.type}-color" in layer.paint
            and isinstance(layer.paint[f"{layer.type}-color"], str)
        ):
            color = common.check_color(layer.paint[f"{layer.type}-color"])
        else:
            color = None

        self.layer_dict[name] = {
            "layer": layer,
            "opacity": opacity,
            "visible": visible,
            "type": layer.type,
            "color": color,
        }
        super().add_layer(layer, before_id=before_id)
        self.set_visibility(name, visible)
        self.set_opacity(name, opacity)

    def remove_layer(self, name: str) -> None:
        """
        Removes a layer from the map.

        This method removes a layer from the map using the layer's name.

        Args:
            name (str): The name of the layer to remove.

        Returns:
            None
        """

        super().add_call("removeLayer", name)
        if name in self.layer_dict:
            self.layer_dict.pop(name)

    def add_deck_layers(
        self, layers: list[dict], tooltip: Union[str, dict] = None
    ) -> None:
        """Add Deck.GL layers to the layer stack

        Args:
            layers (list[dict]): A list of dictionaries containing the Deck.GL layers to be added.
            tooltip (str | dict): Either a single mustache template string applied to all layers
                or a dictionary where keys are layer ids and values are mustache template strings.
        """
        super().add_deck_layers(layers, tooltip)

        for layer in layers:

            self.layer_dict[layer["id"]] = {
                "layer": layer,
                "opacity": layer.get("opacity", 1.0),
                "visible": layer.get("visible", True),
                "type": layer.get("@@type", "deck"),
                "color": layer.get("getFillColor", "#ffffff"),
            }

    def add_arc_layer(
        self,
        data: Union[str, pd.DataFrame],
        src_lon: str,
        src_lat: str,
        dst_lon: str,
        dst_lat: str,
        src_color: List[int] = [255, 0, 0],
        dst_color: List[int] = [255, 255, 0],
        line_width: int = 2,
        layer_id: str = "arc_layer",
        pickable: bool = True,
        tooltip: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a DeckGL ArcLayer to the map.

        Args:
            data (Union[str, pd.DataFrame]): The file path or DataFrame containing the data.
            src_lon (str): The source longitude column name.
            src_lat (str): The source latitude column name.
            dst_lon (str): The destination longitude column name.
            dst_lat (str): The destination latitude column name.
            src_color (List[int]): The source color as an RGB list.
            dst_color (List[int]): The destination color as an RGB list.
            line_width (int): The width of the lines.
            layer_id (str): The ID of the layer.
            pickable (bool): Whether the layer is pickable.
            tooltip (Optional[Union[str, List[str]]], optional): The tooltip content or list of columns. Defaults to None.
            **kwargs (Any): Additional arguments for the layer.

        Returns:
            None
        """

        df = common.read_file(data)
        if "geometry" in df.columns:
            df = df.drop(columns=["geometry"])

        arc_data = [
            {
                "source_position": [row[src_lon], row[src_lat]],
                "target_position": [row[dst_lon], row[dst_lat]],
                **row.to_dict(),  # Include other columns
            }
            for _, row in df.iterrows()
        ]

        # Generate tooltip template dynamically based on the columns
        if tooltip is None:
            columns = df.columns
        elif isinstance(tooltip, list):
            columns = tooltip
        tooltip_content = "<br>".join([f"{col}: {{{{ {col} }}}}" for col in columns])

        deck_arc_layer = {
            "@@type": "ArcLayer",
            "id": layer_id,
            "data": arc_data,
            "getSourcePosition": "@@=source_position",
            "getTargetPosition": "@@=target_position",
            "getSourceColor": src_color,
            "getTargetColor": dst_color,
            "getWidth": line_width,
            "pickable": pickable,
        }

        deck_arc_layer.update(kwargs)

        self.add_deck_layers(
            [deck_arc_layer],
            tooltip={
                layer_id: tooltip_content,
            },
        )

    def add_control(
        self, control: Union[str, Any], position: str = "top-right", **kwargs: Any
    ) -> None:
        """
        Adds a control to the map.

        This method adds a control to the map. The control can be one of the
            following: 'scale', 'fullscreen', 'geolocate', 'navigation', "attribution",
            and "draw". If the control is a string, it is converted to the
            corresponding control object. If the control is not a string, it is
            assumed to be a control object.

        Args:
            control (str or object): The control to add to the map. Can be one
                of the following: 'scale', 'fullscreen', 'geolocate', 'navigation',
                 "attribution", and "draw".
            position (str, optional): The position of the control. Defaults to "top-right".
            **kwargs: Additional keyword arguments that are passed to the control object.

        Returns:
            None

        Raises:
            ValueError: If the control is a string and is not one of the
                following: 'scale', 'fullscreen', 'geolocate', 'navigation', "attribution".
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
            elif control == "attribution":
                control = AttributionControl(**kwargs)
            elif control == "draw":
                self.add_draw_control(position=position, **kwargs)
            elif control == "layers":
                self.add_layer_control(position=position, **kwargs)
                return
            else:
                print(
                    "Control can only be one of the following: 'scale', 'fullscreen', 'geolocate', 'navigation', and 'draw'."
                )
                return

        super().add_control(control, position)

    def add_draw_control(
        self,
        options: Optional[Dict[str, Any]] = None,
        controls: Optional[Dict[str, Any]] = None,
        position: str = "top-left",
        geojson: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a drawing control to the map.

        This method enables users to add interactive drawing controls to the map,
        allowing for the creation, editing, and deletion of geometric shapes on
        the map. The options, position, and initial GeoJSON can be customized.

        Args:
            options (Optional[Dict[str, Any]]): Configuration options for the
                drawing control. Defaults to None.
            controls (Optional[Dict[str, Any]]): The drawing controls to enable.
                Can be one or more of the following: 'polygon', 'line_string',
                'point', 'trash', 'combine_features', 'uncombine_features'.
                Defaults to None.
            position (str): The position of the control on the map. Defaults
                to "top-left".
            geojson (Optional[Dict[str, Any]]): Initial GeoJSON data to load
                into the drawing control. Defaults to None.
            **kwargs (Any): Additional keyword arguments to be passed to the
                drawing control.

        Returns:
            None
        """

        from maplibre.plugins import MapboxDrawControls, MapboxDrawOptions

        if isinstance(controls, list):
            args = {}
            for control in controls:
                if control == "polygon":
                    args["polygon"] = True
                elif control == "line_string":
                    args["line_string"] = True
                elif control == "point":
                    args["point"] = True
                elif control == "trash":
                    args["trash"] = True
                elif control == "combine_features":
                    args["combine_features"] = True
                elif control == "uncombine_features":
                    args["uncombine_features"] = True

            options = MapboxDrawOptions(
                display_controls_default=False,
                controls=MapboxDrawControls(**args),
            )
        super().add_mapbox_draw(
            options=options, position=position, geojson=geojson, **kwargs
        )

    def save_draw_features(self, filepath: str, indent=4, **kwargs) -> None:
        """
        Saves the drawn features to a file.

        This method saves all features created with the drawing control to a
        specified file in GeoJSON format. If there are no features to save, the
        file will not be created.

        Args:
            filepath (str): The path to the file where the GeoJSON data will be saved.
            **kwargs (Any): Additional keyword arguments to be passed to json.dump for custom serialization.

        Returns:
            None

        Raises:
            ValueError: If the feature collection is empty.
        """
        import json

        if len(self.draw_feature_collection_all) > 0:
            with open(filepath, "w") as f:
                json.dump(self.draw_feature_collection_all, f, indent=indent, **kwargs)
        else:
            print("There are no features to save.")

    def add_source(self, id: str, source: Union[str, Dict]) -> None:
        """
        Adds a source to the map.

        Args:
            id (str): The ID of the source.
            source (str or dict): The source data. .

        Returns:
            None
        """
        super().add_source(id, source)
        self.source_dict[id] = source

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

    def fit_bounds(
        self, bounds: List[Tuple[float, float]], options: Dict = None
    ) -> None:
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
            options (dict, optional): Additional options for fitting the bounds.
                See https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/FitBoundsOptions/.

        Returns:
            None
        """

        if options is None:
            options = {}

        if isinstance(bounds, list):
            if len(bounds) == 4 and all(isinstance(i, (int, float)) for i in bounds):
                bounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]

        options["animate"] = options.get("animate", True)
        self.add_call("fitBounds", bounds, options)

    def add_basemap(
        self,
        basemap: Union[str, xyzservices.TileProvider] = None,
        layer_name: Optional[str] = None,
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
            layer = common.get_google_map(basemap.upper(), **kwargs)
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

        if layer_name is None:
            if name == "OpenStreetMap.Mapnik":
                layer_name = "OpenStreetMap"
            else:
                layer_name = name
        layer = Layer(id=layer_name, source=raster_source, type=LayerType.RASTER)
        self.add_layer(layer)
        self.set_opacity(layer_name, opacity)
        self.set_visibility(layer_name, visible)

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
        fit_bounds_options: Dict = None,
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
            fit_bounds_options (dict, optional): Additional options for fitting the bounds.
                See https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/FitBoundsOptions
                for more information.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://maplibre.org/maplibre-style-spec/layers/ for more info.

        Returns:
            None

        Raises:
            ValueError: If the data is not a URL or a GeoJSON dictionary.
        """

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
            layer_names = list(self.layer_dict.keys())
            if "geojson" not in layer_names:
                name = "geojson"
            else:
                name = f"geojson_{common.random_string()}"

        if filter is not None:
            kwargs["filter"] = filter
        if paint is None:
            if "features" in data:
                geom_type = data["features"][0]["geometry"]["type"]
            elif "geometry" in data:
                geom_type = data["geometry"]["type"]
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
        self.add_layer(layer, before_id=before_id, name=name, visible=visible)
        self.add_popup(name)
        if fit_bounds and bounds is not None:
            self.fit_bounds(bounds, fit_bounds_options)

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
        else:
            data = data.__geo_interface__

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

    def add_gdf(
        self,
        gdf: gpd.GeoDataFrame,
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

        This method adds a GeoDataFrame to the map as a vector layer.

        Args:
            gdf (gpd.GeoDataFrame): The GeoDataFrame to add to the map.
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
        if not isinstance(gdf, gpd.GeoDataFrame):
            raise ValueError("The data must be a GeoDataFrame.")
        geojson = gdf.__geo_interface__
        self.add_geojson(
            geojson,
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
        layers: str,
        format: str = "image/png",
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
            layers (str): The layers to include in the WMS request.
            format (str, optional): The format of the tiles in the layer.
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

        url = f"{url.strip()}?service=WMS&request=GetMap&layers={layers}&styles=&format={format.replace('/', '%2F')}&transparent=true&version=1.1.1&height=256&width=256&srs=EPSG%3A3857&bbox={{bbox-epsg-3857}}"

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
        ee_object=None,
        vis_params={},
        asset_id: str = None,
        name: str = None,
        opacity: float = 1.0,
        attribution: str = "Google Earth Engine",
        visible: bool = True,
        before_id: Optional[str] = None,
        ee_initialize: bool = False,
        **kwargs,
    ) -> None:
        """
        Adds a Google Earth Engine tile layer to the map based on the tile layer URL from
            https://github.com/opengeos/ee-tile-layers/blob/main/datasets.tsv.

        Args:
            ee_object (object): The Earth Engine object to display.
            vis_params (dict): Visualization parameters. For example, {'min': 0, 'max': 100}.
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
            ee_initialize (bool, optional): Whether to initialize the Earth Engine
            **kwargs: Additional keyword arguments to be passed to the underlying
                `add_tile_layer` method.

        Returns:
            None
        """
        import pandas as pd

        if isinstance(asset_id, str):
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
        elif ee_object is not None:
            try:
                import geemap
                from geemap.ee_tile_layers import _get_tile_url_format

                if ee_initialize:
                    geemap.ee_initialize()
                url = _get_tile_url_format(ee_object, vis_params)
                if name is None:
                    name = "EE Layer"
                self.add_tile_layer(
                    url,
                    name,
                    attribution=attribution,
                    opacity=opacity,
                    visible=visible,
                    before_id=before_id,
                    **kwargs,
                )
            except Exception as e:
                print(e)
                print(
                    "Please install the `geemap` package to use the `add_ee_layer` function."
                )
                return

    def add_cog_layer(
        self,
        url: str,
        name: Optional[str] = None,
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        bands: Optional[List[int]] = None,
        nodata: Optional[Union[int, float]] = 0,
        titiler_endpoint: str = None,
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
            nodata (float, optional): The nodata value to use for the layer.
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
            name = "COG_" + common.random_string()

        tile_url = common.cog_tile(
            url, bands, titiler_endpoint, nodata=nodata, **kwargs
        )
        bounds = common.cog_bounds(url, titiler_endpoint)
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
        nodata: Optional[Union[int, float]] = 0,
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
            no_data (int | float, optional): The nodata value to use for the layer.
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

        tile_url = common.stac_tile(
            url,
            collection,
            item,
            assets,
            bands,
            titiler_endpoint,
            nodata=nodata,
            **kwargs,
        )
        bounds = common.stac_bounds(url, collection, item, titiler_endpoint)
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
            source = common.array_to_image(source, **array_args)

        tile_layer, tile_client = common.get_local_tile_layer(
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
        output: str = None,
        title: str = "My Awesome Map",
        width: str = "100%",
        height: str = "100%",
        replace_key: bool = False,
        remove_port: bool = True,
        preview: bool = False,
        overwrite: bool = False,
        **kwargs,
    ):
        """Render the map to an HTML page.

        Args:
            output (str, optional): The output HTML file. If None, the HTML content
                is returned as a string. Defaults
            title (str, optional): The title of the HTML page. Defaults to 'My Awesome Map'.
            width (str, optional): The width of the map. Defaults to '100%'.
            height (str, optional): The height of the map. Defaults to '100%'.
            replace_key (bool, optional): Whether to replace the API key in the HTML.
                If True, the API key is replaced with the public API key.
                The API key is read from the environment variable `MAPTILER_KEY`.
                The public API key is read from the environment variable `MAPTILER_KEY_PUBLIC`.
                Defaults to False.
            remove_port (bool, optional): Whether to remove the port number from the HTML.
            preview (bool, optional): Whether to preview the HTML file in a web browser.
                Defaults to False.
            overwrite (bool, optional): Whether to overwrite the output file if it already exists.
            **kwargs: Additional keyword arguments that are passed to the
                `maplibre.ipywidget.MapWidget.to_html()` method.

        Returns:
            str: The HTML content of the map.
        """
        if isinstance(height, int):
            height = f"{height}px"
        if isinstance(width, int):
            width = f"{width}px"

        if "style" not in kwargs:
            kwargs["style"] = f"width: {width}; height: {height};"
        else:
            kwargs["style"] += f"width: {width}; height: {height};"
        html = super().to_html(title=title, **kwargs)

        if isinstance(height, str) and ("%" in height):
            style_before = """</style>\n"""
            style_after = (
                """html, body {height: 100%; margin: 0; padding: 0;} #pymaplibregl {width: 100%; height: """
                + height
                + """;}\n</style>\n"""
            )
            html = html.replace(style_before, style_after)

            div_before = f"""<div id="pymaplibregl" style="width: 100%; height: {height};"></div>"""
            div_after = f"""<div id="pymaplibregl"></div>"""
            html = html.replace(div_before, div_after)

            div_before = f"""<div id="pymaplibregl" style="height: {height};"></div>"""
            html = html.replace(div_before, div_after)

        if replace_key or (os.getenv("MAPTILER_REPLACE_KEY") is not None):
            key_before = common.get_api_key("MAPTILER_KEY")
            key_after = common.get_api_key("MAPTILER_KEY_PUBLIC")
            if key_after is not None:
                html = html.replace(key_before, key_after)

        if remove_port:
            html = common.remove_port_from_string(html)

        if output is None:
            output = os.getenv("MAPLIBRE_OUTPUT", None)

        if output:

            if not overwrite and os.path.exists(output):
                import glob

                num = len(glob.glob(output.replace(".html", "*.html")))
                output = output.replace(".html", f"_{num}.html")

            with open(output, "w") as f:
                f.write(html)
            if preview:
                import webbrowser

                webbrowser.open(output)
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

        if "opacity" in prop and name in self.layer_dict:
            self.layer_dict[name]["opacity"] = value
        elif name in self.style_dict:
            layer = self.style_dict[name]
            if "paint" in layer:
                layer["paint"][prop] = value

    def set_layout_property(self, name: str, prop: str, value: Any) -> None:
        """
        Set the layout property of a layer.

        This method sets the layout property of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            prop (str): The layout property to set.
            value (Any): The value to set.

        Returns:
            None
        """
        super().set_layout_property(name, prop, value)

        if name in self.style_dict:
            layer = self.style_dict[name]
            if "layout" in layer:
                layer["layout"][prop] = value

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
        color = common.check_color(color)
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

        if name in self.layer_dict:
            layer_type = self.layer_dict[name]["layer"].to_dict()["type"]
            prop_name = f"{layer_type}-opacity"
            self.layer_dict[name]["opacity"] = opacity
        elif name in self.style_dict:
            layer = self.style_dict[name]
            layer_type = layer.get("type")
            prop_name = f"{layer_type}-opacity"
            if "paint" in layer:
                layer["paint"][prop_name] = opacity
        super().set_paint_property(name, prop_name, opacity)

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

    def style_layer_interact(self, id=None):
        """Create a layer widget for changing the visibility and opacity of a style layer.

        Args:
            id (str): The is of the layer.

        Returns:
            ipywidgets.Widget: The layer widget.
        """

        layer_ids = list(self.style_dict.keys())
        layer_ids.sort()
        if id is None:
            id = layer_ids[0]
        elif id not in layer_ids:
            raise ValueError(f"Layer {id} not found.")

        layer = self.style_dict[id]
        layer_type = layer.get("type")
        style = {"description_width": "initial"}
        dropdown = widgets.Dropdown(
            options=layer_ids,
            value=id,
            description="Layer",
            style=style,
        )

        visibility = layer.get("layout", {}).get("visibility", "visible")
        if visibility == "visible":
            visibility = True
        else:
            visibility = False

        checkbox = widgets.Checkbox(
            description="Visible",
            value=visibility,
            style=style,
            layout=widgets.Layout(width="120px"),
        )

        opacity = layer.get("paint", {}).get(f"{layer_type}-opacity", 1.0)
        opacity_slider = widgets.FloatSlider(
            description="Opacity",
            min=0,
            max=1,
            step=0.01,
            value=opacity,
            style=style,
        )

        def extract_rgb(rgba_string):
            import re

            # Extracting the RGB values using regex
            rgb_tuple = tuple(map(int, re.findall(r"\d+", rgba_string)[:3]))
            return rgb_tuple

        color = layer.get("paint", {}).get(f"{layer_type}-color", "white")
        if color.startswith("rgba"):
            color = extract_rgb(color)
        color = common.check_color(color)
        color_picker = widgets.ColorPicker(
            concise=True,
            value=color,
            style=style,
        )

        def color_picker_event(change):
            self.set_paint_property(dropdown.value, f"{layer_type}-color", change.new)

        color_picker.observe(color_picker_event, "value")

        hbox = widgets.HBox(
            [dropdown, checkbox, opacity_slider, color_picker],
            layout=widgets.Layout(width="750px"),
        )

        def dropdown_event(change):
            name = change.new
            layer = self.style_dict[name]
            layer_type = layer.get("type")

            visibility = layer.get("layout", {}).get("visibility", "visible")
            if visibility == "visible":
                visibility = True
            else:
                visibility = False

            checkbox.value = visibility
            opacity = layer.get("paint", {}).get(f"{layer_type}-opacity", 1.0)
            opacity_slider.value = opacity

            color = layer.get("paint", {}).get(f"{layer_type}-color", "white")
            if color.startswith("rgba"):
                color = extract_rgb(color)
            color = common.check_color(color)

            if color:
                color_picker.value = color
                color_picker.disabled = False
            else:
                color_picker.value = "white"
                color_picker.disabled = True

        dropdown.observe(dropdown_event, "value")

        def update_layer(change):
            self.set_layout_property(
                dropdown.value, "visibility", "visible" if checkbox.value else "none"
            )
            self.set_paint_property(
                dropdown.value, f"{layer_type}-opacity", opacity_slider.value
            )

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
                style = common.pmtiles_style(url)

            if "sources" in style:
                source_name = list(style["sources"].keys())[0]
            elif "layers" in style:
                source_name = style["layers"][0]["source"]
            else:
                source_name = "source"

            self.add_source(source_name, pmtiles_source)

            style = common.replace_hyphens_in_keys(style)

            for params in style["layers"]:

                if exclude_mask and params.get("source_layer") == "mask":
                    continue

                layer = Layer(**params)
                self.add_layer(layer)
                self.set_visibility(params["id"], visible)
                if "paint" in params:
                    for key in params["paint"]:
                        if "opacity" in key:
                            self.set_opacity(params["id"], params["paint"][key])
                            break
                    else:
                        self.set_opacity(params["id"], opacity)

                if tooltip:
                    self.add_tooltip(params["id"], properties, template)

            if fit_bounds:
                metadata = common.pmtiles_metadata(url)
                bounds = metadata["bounds"]  # [minx, miny, maxx, maxy]
                self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

        except Exception as e:
            print(e)

    def add_marker(
        self,
        marker: Marker = None,
        lng_lat: List[Union[float, float]] = [],
        popup: Optional[Dict] = {},
        options: Optional[Dict] = {},
    ) -> None:
        """
        Adds a marker to the map.

        Args:
            marker (Marker, optional): A Marker object. Defaults to None.
            lng_lat (List[Union[float, float]]): A list of two floats
                representing the longitude and latitude of the marker.
            popup (Optional[str], optional): The text to display in a popup when
                the marker is clicked. Defaults to None.
            options (Optional[Dict], optional): A dictionary of options to
                customize the marker. Defaults to None.

        Returns:
            None
        """

        if marker is None:
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
        import numpy as np

        if isinstance(image, str):
            try:
                if image.startswith("http"):
                    image = common.download_file(
                        image, common.temp_file_path(image.split(".")[-1]), quiet=True
                    )
                if os.path.exists(image):
                    img = Image.open(image)
                else:
                    raise ValueError("The image file does not exist.")

                width, height = img.size
                # Convert image to numpy array and then flatten it
                img_data = np.array(img, dtype="uint8")
                if len(img_data.shape) == 3 and img_data.shape[2] == 2:
                    # Split the grayscale and alpha channels
                    gray_channel = img_data[:, :, 0]
                    alpha_channel = img_data[:, :, 1]

                    # Create the R, G, and B channels by duplicating the grayscale channel
                    R_channel = gray_channel
                    G_channel = gray_channel
                    B_channel = gray_channel

                    # Combine the channels into an RGBA image
                    RGBA_image_data = np.stack(
                        (R_channel, G_channel, B_channel, alpha_channel), axis=-1
                    )

                    # Update img_data to the new RGBA image data
                    img_data = RGBA_image_data

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
        self,
        id: str = None,
        image: Union[str, Dict] = None,
        width: int = None,
        height: int = None,
        coordinates: List[float] = None,
        position: str = None,
        icon_size: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Add an image to the map.

        Args:
            id (str): The layer ID of the image.
            image (Union[str, Dict, np.ndarray]): The URL or local file path to
                the image, or a dictionary containing image data, or a numpy
                array representing the image.
            width (int, optional): The width of the image. Defaults to None.
            height (int, optional): The height of the image. Defaults to None.
            coordinates (List[float], optional): The longitude and latitude
                coordinates to place the image.
            position (str, optional): The position of the image. Defaults to None.
                Can be one of 'top-right', 'top-left', 'bottom-right', 'bottom-left'.
            icon_size (float, optional): The size of the icon. Defaults to 1.0.

        Returns:
            None
        """
        import numpy as np

        if id is None:
            id = "image"

        style = ""
        if isinstance(width, int):
            style += f"width: {width}px; "
        elif isinstance(width, str) and width.endswith("px"):
            style += f"width: {width}; "
        if isinstance(height, int):
            style += f"height: {height}px; "
        elif isinstance(height, str) and height.endswith("px"):
            style += f"height: {height}; "

        if position is not None:
            if style == "":
                html = f'<img src="{image}">'
            else:
                html = f'<img src="{image}" style="{style}">'
            self.add_html(html, position=position, **kwargs)
        else:
            if isinstance(image, str):
                image_dict = self._read_image(image)
            elif isinstance(image, dict):
                image_dict = image
            elif isinstance(image, np.ndarray):
                image_dict = {
                    "width": width,
                    "height": height,
                    "data": image.flatten().tolist(),
                }
            else:
                raise ValueError(
                    "The image must be a URL, a local file path, or a numpy array."
                )
            super().add_call("addImage", id, image_dict)

            if coordinates is not None:

                source = {
                    "type": "geojson",
                    "data": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": coordinates,
                                },
                            }
                        ],
                    },
                }

                self.add_source("image_point", source)

                kwargs["id"] = "image_points"
                kwargs["type"] = "symbol"
                kwargs["source"] = "image_point"
                if "layout" not in kwargs:
                    kwargs["layout"] = {}
                kwargs["layout"]["icon-image"] = id
                kwargs["layout"]["icon-size"] = icon_size
                self.add_layer(kwargs)

    def add_symbol(
        self,
        source: str,
        image: str,
        icon_size: int = 1,
        symbol_placement: str = "line",
        minzoom: Optional[float] = None,
        maxzoom: Optional[float] = None,
        filter: Optional[Any] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a symbol to the map.

        Args:
            source (str): The source of the symbol.
            image (str): The URL or local file path to the image. Default to the arrow image.
                at https://assets.gishub.org/images/arrow.png.
            icon_size (int, optional): The size of the symbol. Defaults to 1.
            symbol_placement (str, optional): The placement of the symbol. Defaults to "line".
            minzoom (Optional[float], optional): The minimum zoom level for the symbol. Defaults to None.
            maxzoom (Optional[float], optional): The maximum zoom level for the symbol. Defaults to None.
            filter (Optional[Any], optional): A filter to apply to the symbol. Defaults to None.
            name (Optional[str], optional): The name of the symbol layer. Defaults to None.
            **kwargs (Any): Additional keyword arguments to pass to the layer layout.
                For more info, see https://maplibre.org/maplibre-style-spec/layers/#symbol

        Returns:
            None
        """

        id = f"image_{common.random_string(3)}"
        self.add_image(id, image)

        if name is None:
            name = f"symbol_{common.random_string(3)}"

        layer = {
            "id": name,
            "type": "symbol",
            "source": source,
            "layout": {
                "icon-image": id,
                "icon-size": icon_size,
                "symbol-placement": symbol_placement,
            },
        }

        if minzoom is not None:
            layer["minzoom"] = minzoom
        if maxzoom is not None:
            layer["maxzoom"] = maxzoom
        if filter is not None:
            layer["filter"] = filter

        kwargs = common.replace_underscores_in_keys(kwargs)
        layer["layout"].update(kwargs)

        self.add_layer(layer)

    def add_arrow(
        self,
        source: str,
        image: Optional[str] = None,
        icon_size: int = 0.1,
        minzoom: Optional[float] = 19,
        **kwargs: Any,
    ) -> None:
        """
        Adds an arrow symbol to the map.

        Args:
            source (str): The source layer to which the arrow symbol will be added.
            image (Optional[str], optional): The URL of the arrow image.
                Defaults to "https://assets.gishub.org/images/arrow.png".
            icon_size (int, optional): The size of the icon. Defaults to 0.1.
            minzoom (Optional[float], optional): The minimum zoom level at which
                the arrow symbol will be visible. Defaults to 19.
            **kwargs: Additional keyword arguments to pass to the add_symbol method.

        Returns:
            None
        """
        if image is None:
            image = "https://assets.gishub.org/images/arrow.png"

        self.add_symbol(source, image, icon_size, minzoom=minzoom, **kwargs)

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
            import streamlit.components.v1 as components  # pylint: disable=E0401
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

    def open_geojson(self, **kwargs: Any) -> widgets.FileUpload:
        """
        Creates a file uploader widget to upload a GeoJSON file. When a file is
        uploaded, it is written to a temporary file and added to the map.

        Args:
            **kwargs: Additional keyword arguments to pass to the add_geojson method.

        Returns:
            widgets.FileUpload: The file uploader widget.
        """

        uploader = widgets.FileUpload(
            accept=".geojson",  # Accept GeoJSON files
            multiple=False,  # Only single file upload
            description="Open GeoJSON",
        )

        def on_upload(change):
            content = uploader.value[0]["content"]
            temp_file = common.temp_file_path(extension=".geojson")
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
        satellite=True,
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
            api_key = common.get_api_key(token)

        if api_key is None:
            print("An API key is required to use the 3D terrain feature.")
            return "dark-matter"

        layers = []

        if satellite:
            layers.append({"id": "satellite", "type": "raster", "source": "satellite"})

        layers.append(
            {
                "id": "hills",
                "type": "hillshade",
                "source": "hillshadeSource",
                "layout": {"visibility": "visible"},
                "paint": {"hillshade-shadow-color": "#473B24"},
            }
        )

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
            "layers": layers,
            "terrain": {"source": "terrainSource", "exaggeration": exaggeration},
        }

        return style

    def get_style(self):
        """
        Get the style of the map.

        Returns:
            Dict: The style of the map.
        """
        if self._style is not None:
            if isinstance(self._style, str):
                response = requests.get(self._style)
                style = response.json()
            elif isinstance(self._style, dict):
                style = self._style
            else:
                style = {}
            return style
        else:
            return {}

    def get_style_layers(self, return_ids=False, sorted=True) -> List[str]:
        """
        Get the names of the basemap layers.

        Returns:
            List[str]: The names of the basemap layers.
        """
        style = self.get_style()
        if "layers" in style:
            layers = style["layers"]
            if return_ids:
                ids = [layer["id"] for layer in layers]
                if sorted:
                    ids.sort()

                return ids
            else:
                return layers
        else:
            return []

    def find_style_layer(self, id: str) -> Optional[Dict]:
        """
        Searches for a style layer in the map's current style by its ID and returns it if found.

        Args:
            id (str): The ID of the style layer to find.

        Returns:
            Optional[Dict]: The style layer as a dictionary if found, otherwise None.
        """
        layers = self.get_style_layers()
        for layer in layers:
            if layer["id"] == id:
                return layer
        return None

    def zoom_to(self, zoom: float, options: Dict[str, Any] = {}, **kwargs: Any) -> None:
        """
        Zooms the map to a specified zoom level.

        This function zooms the map to the specified zoom level. Additional options and keyword
        arguments can be provided to control the zoom. For more information, see
        https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#zoomto

        Args:
            zoom (float): The zoom level to zoom to.
            options (Dict[str, Any], optional): Additional options to control the zoom. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the zoom.

        Returns:
            None
        """
        super().add_call("zoomTo", zoom, options, **kwargs)

    def find_first_symbol_layer(self) -> Optional[Dict]:
        """
        Find the first symbol layer in the map's current style.

        Returns:
            Optional[Dict]: The first symbol layer as a dictionary if found, otherwise None.
        """
        layers = self.get_style_layers()
        for layer in layers:
            if layer["type"] == "symbol":
                return layer
        return None

    def add_text(
        self,
        text: str,
        fontsize: int = 20,
        fontcolor: str = "black",
        bold: bool = False,
        padding: str = "5px",
        bg_color: str = "white",
        border_radius: str = "5px",
        position: str = "bottom-right",
        **kwargs: Any,
    ) -> None:
        """
        Adds text to the map with customizable styling.

        This method allows adding a text widget to the map with various styling options such as font size, color,
        background color, and more. The text's appearance can be further customized using additional CSS properties
        passed through kwargs.

        Args:
            text (str): The text to add to the map.
            fontsize (int, optional): The font size of the text. Defaults to 20.
            fontcolor (str, optional): The color of the text. Defaults to "black".
            bold (bool, optional): If True, the text will be bold. Defaults to False.
            padding (str, optional): The padding around the text. Defaults to "5px".
            bg_color (str, optional): The background color of the text widget. Defaults to "white".
                To make the background transparent, set this to "transparent".
                To make the background half transparent, set this to "rgba(255, 255, 255, 0.5)".
            border_radius (str, optional): The border radius of the text widget. Defaults to "5px".
            position (str, optional): The position of the text widget on the map. Defaults to "bottom-right".
            **kwargs (Any): Additional CSS properties to apply to the text widget.

        Returns:
            None
        """
        from maplibre.controls import InfoBoxControl

        if bg_color == "transparent" and "box-shadow" not in kwargs:
            kwargs["box-shadow"] = "none"

        css_text = f"""font-size: {fontsize}px; color: {fontcolor};
        font-weight: {'bold' if bold else 'normal'}; padding: {padding};
        background-color: {bg_color}; border-radius: {border_radius};"""

        for key, value in kwargs.items():
            css_text += f" {key.replace('_', '-')}: {value};"

        control = InfoBoxControl(content=text, css_text=css_text)
        self.add_control(control, position=position)

    def add_html(
        self,
        html: str,
        bg_color: str = "white",
        position: str = "bottom-right",
        **kwargs: Union[str, int, float],
    ) -> None:
        """
        Add HTML content to the map.

        This method allows for the addition of arbitrary HTML content to the map, which can be used to display
        custom information or controls. The background color and position of the HTML content can be customized.

        Args:
            html (str): The HTML content to add.
            bg_color (str, optional): The background color of the HTML content. Defaults to "white".
                To make the background transparent, set this to "transparent".
                To make the background half transparent, set this to "rgba(255, 255, 255, 0.5)".
            position (str, optional): The position of the HTML content on the map. Can be one of "top-left",
                "top-right", "bottom-left", "bottom-right". Defaults to "bottom-right".
            **kwargs: Additional keyword arguments for future use.

        Returns:
            None
        """
        # Check if an HTML string contains local images and convert them to base64.
        html = common.check_html_string(html)
        self.add_text(html, position=position, bg_color=bg_color, **kwargs)

    def add_legend(
        self,
        title: str = "Legend",
        legend_dict: Optional[Dict[str, str]] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        fontsize: int = 15,
        bg_color: str = "white",
        position: str = "bottom-right",
        builtin_legend: Optional[str] = None,
        shape_type: str = "rectangle",
        **kwargs: Union[str, int, float],
    ) -> None:
        """
        Adds a legend to the map.

        This method allows for the addition of a legend to the map. The legend can be customized with a title,
        labels, colors, and more. A built-in legend can also be specified.

        Args:
            title (str, optional): The title of the legend. Defaults to "Legend".
            legend_dict (Optional[Dict[str, str]], optional): A dictionary with legend items as keys and colors as values.
                If provided, `labels` and `colors` will be ignored. Defaults to None.
            labels (Optional[List[str]], optional): A list of legend labels. Defaults to None.
            colors (Optional[List[str]], optional): A list of colors corresponding to the labels. Defaults to None.
            fontsize (int, optional): The font size of the legend text. Defaults to 15.
            bg_color (str, optional): The background color of the legend. Defaults to "white".
                To make the background transparent, set this to "transparent".
                To make the background half transparent, set this to "rgba(255, 255, 255, 0.5)".
            position (str, optional): The position of the legend on the map. Can be one of "top-left",
                "top-right", "bottom-left", "bottom-right". Defaults to "bottom-right".
            builtin_legend (Optional[str], optional): The name of a built-in legend to use. Defaults to None.
            shape_type (str, optional): The shape type of the legend items. Can be one of "rectangle", "circle", or "line".
            **kwargs: Additional keyword arguments for future use.

        Returns:
            None
        """
        import importlib.resources
        from .legends import builtin_legends

        pkg_dir = os.path.dirname(importlib.resources.files("leafmap") / "leafmap.py")
        legend_template = os.path.join(pkg_dir, "data/template/legend.html")

        if not os.path.exists(legend_template):
            print("The legend template does not exist.")
            return

        if labels is not None:
            if not isinstance(labels, list):
                print("The legend keys must be a list.")
                return
        else:
            labels = ["One", "Two", "Three", "Four", "etc"]

        if colors is not None:
            if not isinstance(colors, list):
                print("The legend colors must be a list.")
                return
            elif all(isinstance(item, tuple) for item in colors):
                try:
                    colors = [common.rgb_to_hex(x) for x in colors]
                except Exception as e:
                    print(e)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                print("The legend colors must be a list of tuples.")
                return
        else:
            colors = [
                "#8DD3C7",
                "#FFFFB3",
                "#BEBADA",
                "#FB8072",
                "#80B1D3",
            ]

        if len(labels) != len(colors):
            print("The legend keys and values must be the same length.")
            return

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            if builtin_legend not in allowed_builtin_legends:
                print(
                    "The builtin legend must be one of the following: {}".format(
                        ", ".join(allowed_builtin_legends)
                    )
                )
                return
            else:
                legend_dict = builtin_legends[builtin_legend]
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                print("The legend dict must be a dictionary.")
                return
            else:
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if isinstance(colors[0], tuple) and len(colors[0]) == 2:
                    labels = [color[0] for color in colors]
                    colors = [color[1] for color in colors]
                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [common.rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        print(e)
        allowed_positions = [
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
        ]
        if position not in allowed_positions:
            print(
                "The position must be one of the following: {}".format(
                    ", ".join(allowed_positions)
                )
            )
            return

        header = []
        content = []
        footer = []

        with open(legend_template) as f:
            lines = f.readlines()
            lines[3] = lines[3].replace("Legend", title)
            header = lines[:6]
            footer = lines[11:]

        for index, key in enumerate(labels):
            color = colors[index]
            if isinstance(color, str) and (not color.startswith("#")):
                color = "#" + color
            item = "      <li><span style='background:{};'></span>{}</li>\n".format(
                color, key
            )
            content.append(item)

        legend_html = header + content + footer
        legend_text = "".join(legend_html)

        if shape_type == "circle":
            legend_text = legend_text.replace("width: 30px", "width: 16px")
            legend_text = legend_text.replace(
                "border: 1px solid #999;",
                "border-radius: 50%;\n      border: 1px solid #999;",
            )
        elif shape_type == "line":
            legend_text = legend_text.replace("height: 16px", "height: 3px")

        self.add_html(
            legend_text,
            fontsize=fontsize,
            bg_color=bg_color,
            position=position,
            **kwargs,
        )

    def add_colorbar(
        self,
        width: Optional[float] = 3.0,
        height: Optional[float] = 0.2,
        vmin: Optional[float] = 0,
        vmax: Optional[float] = 1.0,
        palette: Optional[List[str]] = None,
        vis_params: Optional[Dict[str, Union[str, float, int]]] = None,
        cmap: Optional[str] = "gray",
        discrete: Optional[bool] = False,
        label: Optional[str] = None,
        label_size: Optional[int] = 10,
        label_weight: Optional[str] = "normal",
        tick_size: Optional[int] = 8,
        bg_color: Optional[str] = "white",
        orientation: Optional[str] = "horizontal",
        dpi: Optional[Union[str, float]] = "figure",
        transparent: Optional[bool] = False,
        position: str = "bottom-right",
        **kwargs,
    ) -> str:
        """
        Add a colorbar to the map.

        This function uses matplotlib to generate a colorbar, saves it as a PNG file, and adds it to the map using
        the Map.add_html() method. The colorbar can be customized in various ways including its size, color palette,
        label, and orientation.

        Args:
            width (Optional[float]): Width of the colorbar in inches. Defaults to 3.0.
            height (Optional[float]): Height of the colorbar in inches. Defaults to 0.2.
            vmin (Optional[float]): Minimum value of the colorbar. Defaults to 0.
            vmax (Optional[float]): Maximum value of the colorbar. Defaults to 1.0.
            palette (Optional[List[str]]): List of colors or a colormap name for the colorbar. Defaults to None.
            vis_params (Optional[Dict[str, Union[str, float, int]]]): Visualization parameters as a dictionary.
            cmap (Optional[str]): Matplotlib colormap name. Defaults to "gray".
            discrete (Optional[bool]): Whether to create a discrete colorbar. Defaults to False.
            label (Optional[str]): Label for the colorbar. Defaults to None.
            label_size (Optional[int]): Font size for the colorbar label. Defaults to 10.
            label_weight (Optional[str]): Font weight for the colorbar label. Defaults to "normal".
            tick_size (Optional[int]): Font size for the colorbar tick labels. Defaults to 8.
            bg_color (Optional[str]): Background color for the colorbar. Defaults to "white".
            orientation (Optional[str]): Orientation of the colorbar ("vertical" or "horizontal"). Defaults to "horizontal".
            dpi (Optional[Union[str, float]]): Resolution in dots per inch. If 'figure', uses the figure's dpi value. Defaults to "figure".
            transparent (Optional[bool]): Whether the background is transparent. Defaults to False.
            position (str): Position of the colorbar on the map. Defaults to "bottom-right".
            **kwargs: Additional keyword arguments passed to matplotlib.pyplot.savefig().

        Returns:
            str: Path to the generated colorbar image.
        """

        if transparent:
            bg_color = "transparent"

        colorbar = common.save_colorbar(
            None,
            width,
            height,
            vmin,
            vmax,
            palette,
            vis_params,
            cmap,
            discrete,
            label,
            label_size,
            label_weight,
            tick_size,
            bg_color,
            orientation,
            dpi,
            transparent,
            show_colorbar=False,
        )

        html = f'<img src="{colorbar}">'

        self.add_html(html, bg_color=bg_color, position=position, **kwargs)

    def add_layer_control(
        self,
        layer_ids: Optional[List[str]] = None,
        theme: str = "default",
        css_text: Optional[str] = None,
        position: str = "top-left",
        bg_layers: Optional[Union[bool, List[str]]] = False,
    ) -> None:
        """
        Adds a layer control to the map.

        This function creates and adds a layer switcher control to the map, allowing users to toggle the visibility
        of specified layers. The appearance and functionality of the layer control can be customized with parameters
        such as theme, CSS styling, and position on the map.

        Args:
            layer_ids (Optional[List[str]]): A list of layer IDs to include in the control. If None, all layers
                in the map will be included. Defaults to None.
            theme (str): The theme for the layer switcher control. Can be "default" or other custom themes. Defaults to "default".
            css_text (Optional[str]): Custom CSS text for styling the layer control. If None, a default style will be applied.
                Defaults to None.
            position (str): The position of the layer control on the map. Can be "top-left", "top-right", "bottom-left",
                or "bottom-right". Defaults to "top-left".
            bg_layers (bool): If True, background layers will be included in the control. Defaults to False.

        Returns:
            None
        """
        from maplibre.controls import LayerSwitcherControl

        if layer_ids is None:
            layer_ids = list(self.layer_dict.keys())
            if layer_ids[0] == "background":
                layer_ids = layer_ids[1:]

        if isinstance(bg_layers, list):
            layer_ids = bg_layers + layer_ids
        elif bg_layers:
            background_ids = list(self.style_dict.keys())
            layer_ids = background_ids + layer_ids

        if css_text is None:
            css_text = "padding: 5px; border: 1px solid darkgrey; border-radius: 4px;"

        if len(layer_ids) > 0:

            control = LayerSwitcherControl(
                layer_ids=layer_ids,
                theme=theme,
                css_text=css_text,
            )
            self.add_control(control, position=position)

    def add_3d_buildings(
        self,
        name: str = "buildings",
        min_zoom: int = 15,
        values: List[int] = [0, 200, 400],
        colors: List[str] = ["lightgray", "royalblue", "lightblue"],
        **kwargs: Any,
    ) -> None:
        """
        Adds a 3D buildings layer to the map.

        This function creates and adds a 3D buildings layer to the map using fill-extrusion. The buildings' heights
        are determined by the 'render_height' property, and their colors are interpolated based on specified values.
        The layer is only visible from a certain zoom level, specified by the 'min_zoom' parameter.

        Args:
            name (str): The name of the 3D buildings layer. Defaults to "buildings".
            min_zoom (int): The minimum zoom level at which the 3D buildings will start to be visible. Defaults to 15.
            values (List[int]): A list of height values (in meters) used for color interpolation. Defaults to [0, 200, 400].
            colors (List[str]): A list of colors corresponding to the 'values' list. Each color is applied to the
                building height range defined by the 'values'. Defaults to ["lightgray", "royalblue", "lightblue"].
            **kwargs: Additional keyword arguments to pass to the add_layer method.

        Raises:
            ValueError: If the lengths of 'values' and 'colors' lists do not match.

        Returns:
            None
        """

        MAPTILER_KEY = common.get_api_key("MAPTILER_KEY")
        source = {
            "url": f"https://api.maptiler.com/tiles/v3/tiles.json?key={MAPTILER_KEY}",
            "type": "vector",
        }

        if len(values) != len(colors):
            raise ValueError("The values and colors must have the same length.")

        value_color_pairs = []
        for i, value in enumerate(values):
            value_color_pairs.append(value)
            value_color_pairs.append(colors[i])

        layer = {
            "id": name,
            "source": "openmaptiles",
            "source-layer": "building",
            "type": "fill-extrusion",
            "min-zoom": min_zoom,
            "paint": {
                "fill-extrusion-color": [
                    "interpolate",
                    ["linear"],
                    ["get", "render_height"],
                ]
                + value_color_pairs,
                "fill-extrusion-height": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    15,
                    0,
                    16,
                    ["get", "render_height"],
                ],
                "fill-extrusion-base": [
                    "case",
                    [">=", ["get", "zoom"], 16],
                    ["get", "render_min_height"],
                    0,
                ],
            },
        }
        self.add_source("openmaptiles", source)
        self.add_layer(layer, **kwargs)

    def add_overture_3d_buildings(
        self,
        release: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None,
        values: Optional[List[int]] = None,
        colors: Optional[List[str]] = None,
        visible: bool = True,
        opacity: float = 1.0,
        tooltip: bool = True,
        template: str = "simple",
        fit_bounds: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add 3D buildings from Overture Maps to the map.

        Args:
            release (Optional[str], optional): The release date of the Overture Maps data.
                Defaults to the latest release. For more info, see
                https://github.com/OvertureMaps/overture-tiles.
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the buildings. Defaults to None.
            values (Optional[List[int]], optional): List of height values for
                color interpolation. Defaults to None.
            colors (Optional[List[str]], optional): List of colors corresponding
                to the height values. Defaults to None.
            visible (bool, optional): Whether the buildings layer is visible.
                Defaults to True.
            opacity (float, optional): The opacity of the buildings layer.
                Defaults to 1.0.
            tooltip (bool, optional): Whether to show tooltips on the buildings.
                Defaults to True.
            template (str, optional): The template for the tooltip. It can be
                "simple" or "all". Defaults to "simple".
            fit_bounds (bool, optional): Whether to fit the map bounds to the
                buildings layer. Defaults to False.

        Raises:
            ValueError: If the length of values and colors lists are not the same.
        """

        if release is None:
            release = common.get_overture_latest_release()

        url = f"https://overturemaps-tiles-us-west-2-beta.s3.amazonaws.com/{release}/buildings.pmtiles"

        if template == "simple":
            template = "Name: {{@name}}<br>Subtype: {{subtype}}<br>Class: {{class}}<br>Height: {{height}}"
        elif template == "all":
            template = None

        if style is None:
            if values is None:
                values = [0, 200, 400]
            if colors is None:
                colors = ["lightgray", "royalblue", "lightblue"]

            if len(values) != len(colors):
                raise ValueError("The values and colors must have the same length.")
            value_color_pairs = []
            for i, value in enumerate(values):
                value_color_pairs.append(value)
                value_color_pairs.append(colors[i])

            style = {
                "layers": [
                    {
                        "id": "Building",
                        "source": "buildings",
                        "source-layer": "building",
                        "type": "fill-extrusion",
                        "filter": [
                            ">",
                            ["get", "height"],
                            0,
                        ],  # only show buildings with height info
                        "paint": {
                            "fill-extrusion-color": [
                                "interpolate",
                                ["linear"],
                                ["get", "height"],
                            ]
                            + value_color_pairs,
                            "fill-extrusion-height": ["*", ["get", "height"], 1],
                        },
                    },
                    {
                        "id": "Building-part",
                        "source": "buildings",
                        "source-layer": "building_part",
                        "type": "fill-extrusion",
                        "filter": [
                            ">",
                            ["get", "height"],
                            0,
                        ],  # only show buildings with height info
                        "paint": {
                            "fill-extrusion-color": [
                                "interpolate",
                                ["linear"],
                                ["get", "height"],
                            ]
                            + value_color_pairs,
                            "fill-extrusion-height": ["*", ["get", "height"], 1],
                        },
                    },
                ],
            }

        self.add_pmtiles(
            url,
            style=style,
            visible=visible,
            opacity=opacity,
            tooltip=tooltip,
            template=template,
            fit_bounds=fit_bounds,
            **kwargs,
        )

    def add_overture_data(
        self,
        release: str = None,
        theme: str = "buildings",
        style: Optional[Dict[str, Any]] = None,
        visible: bool = True,
        opacity: float = 1.0,
        tooltip: bool = True,
        fit_bounds: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add Overture Maps data to the map.

        Args:
            release (str, optional): The release date of the data. Defaults to
                "2024-12-28". For more info, see https://github.com/OvertureMaps/overture-tiles
            theme (str, optional): The theme of the data. It can be one of the following:
                "addresses", "base", "buildings", "divisions", "places", "transportation".
                Defaults to "buildings".
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the data. Defaults to None.
            visible (bool, optional): Whether the data layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the data layer. Defaults to 1.0.
            tooltip (bool, optional): Whether to show tooltips on the data.
                Defaults to True.
            fit_bounds (bool, optional): Whether to fit the map bounds to the
                data layer. Defaults to False.
            **kwargs (Any): Additional keyword arguments for the add_pmtiles method.

        Raises:
            ValueError: If the theme is not one of the allowed themes.
        """
        if release is None:
            release = common.get_overture_latest_release()

        allowed_themes = [
            "addresses",
            "base",
            "buildings",
            "divisions",
            "places",
            "transportation",
        ]
        if theme not in allowed_themes:
            raise ValueError(
                f"The theme must be one of the following: {', '.join(allowed_themes)}"
            )

        styles = {
            "addresses": {
                "layers": [
                    {
                        "id": "Address",
                        "source": "addresses",
                        "source-layer": "address",
                        "type": "circle",
                        "paint": {
                            "circle-radius": 4,
                            "circle-color": "#8dd3c7",
                            "circle-stroke-color": "#8dd3c7",
                            "circle-stroke-width": 1,
                        },
                    },
                ]
            },
            "base": {
                "layers": [
                    {
                        "id": "Infrastructure",
                        "source": "base",
                        "source-layer": "infrastructure",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#8DD3C7",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                    {
                        "id": "Land",
                        "source": "base",
                        "source-layer": "land",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#FFFFB3",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                    {
                        "id": "Land_cover",
                        "source": "base",
                        "source-layer": "land_cover",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#BEBADA",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                    {
                        "id": "Land_use",
                        "source": "base",
                        "source-layer": "land_use",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#FB8072",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                    {
                        "id": "Water",
                        "source": "base",
                        "source-layer": "water",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#80B1D3",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                ]
            },
            "buildings": {
                "layers": [
                    {
                        "id": "Building",
                        "source": "buildings",
                        "source-layer": "building",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#6ea299",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                    {
                        "id": "Building_part",
                        "source": "buildings",
                        "source-layer": "building_part",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#fdfdb2",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                ]
            },
            "divisions": {
                "layers": [
                    {
                        "id": "Division",
                        "source": "divisions",
                        "source-layer": "division",
                        "type": "circle",
                        "paint": {
                            "circle-radius": 4,
                            "circle-color": "#8dd3c7",
                            "circle-stroke-color": "#8dd3c7",
                            "circle-stroke-width": 1,
                        },
                    },
                    {
                        "id": "Division_area",
                        "source": "divisions",
                        "source-layer": "division_area",
                        "type": "fill",
                        "paint": {
                            "fill-color": "#FFFFB3",
                            "fill-opacity": 1.0,
                            "fill-outline-color": "#888888",
                        },
                    },
                    {
                        "id": "Division_boundary",
                        "source": "divisions",
                        "source-layer": "division_boundary",
                        "type": "line",
                        "paint": {
                            "line-color": "#BEBADA",
                            "line-width": 1.0,
                        },
                    },
                ]
            },
            "places": {
                "layers": [
                    {
                        "id": "Place",
                        "source": "places",
                        "source-layer": "place",
                        "type": "circle",
                        "paint": {
                            "circle-radius": 4,
                            "circle-color": "#8dd3c7",
                            "circle-stroke-color": "#8dd3c7",
                            "circle-stroke-width": 1,
                        },
                    },
                ]
            },
            "transportation": {
                "layers": [
                    {
                        "id": "Segment",
                        "source": "transportation",
                        "source-layer": "segment",
                        "type": "line",
                        "paint": {
                            "line-color": "#ffffb3",
                            "line-width": 1.0,
                        },
                    },
                    {
                        "id": "Connector",
                        "source": "transportation",
                        "source-layer": "connector",
                        "type": "circle",
                        "paint": {
                            "circle-radius": 4,
                            "circle-color": "#8dd3c7",
                            "circle-stroke-color": "#8dd3c7",
                            "circle-stroke-width": 1,
                        },
                    },
                ]
            },
        }

        url = f"https://overturemaps-tiles-us-west-2-beta.s3.amazonaws.com/{release}/{theme}.pmtiles"
        if style is None:
            style = styles.get(theme, None)
        self.add_pmtiles(
            url,
            style=style,
            visible=visible,
            opacity=opacity,
            tooltip=tooltip,
            fit_bounds=fit_bounds,
            **kwargs,
        )

    def add_overture_buildings(
        self,
        release: str = None,
        style: Optional[Dict[str, Any]] = None,
        type: str = "line",
        visible: bool = True,
        opacity: float = 1.0,
        tooltip: bool = True,
        fit_bounds: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add Overture Maps data to the map.

        Args:
            release (str, optional): The release date of the data. Defaults to
                "2024-12-18". For more info, see https://github.com/OvertureMaps/overture-tiles
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the data. Defaults to None.
            type (str, optional): The type of the data. It can be "line" or "fill".
            visible (bool, optional): Whether the data layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the data layer. Defaults to 1.0.
            tooltip (bool, optional): Whether to show tooltips on the data.
                Defaults to True.
            fit_bounds (bool, optional): Whether to fit the map bounds to the
                data layer. Defaults to False.
            **kwargs (Any): Additional keyword arguments for the paint properties.
        """
        if release is None:
            release = common.get_overture_latest_release()

        url = f"https://overturemaps-tiles-us-west-2-beta.s3.amazonaws.com/{release}/buildings.pmtiles"

        kwargs = common.replace_underscores_in_keys(kwargs)

        if type == "line":
            if "line-color" not in kwargs:
                kwargs["line-color"] = "#ff0000"
            if "line-width" not in kwargs:
                kwargs["line-width"] = 1
            if "line-opacity" not in kwargs:
                kwargs["line-opacity"] = opacity
        elif type == "fill":
            if "fill-color" not in kwargs:
                kwargs["fill-color"] = "#6ea299"
            if "fill-opacity" not in kwargs:
                kwargs["fill-opacity"] = opacity

        if style is None:
            style = {
                "layers": [
                    {
                        "id": "Building",
                        "source": "buildings",
                        "source-layer": "building",
                        "type": type,
                        "paint": kwargs,
                    },
                    {
                        "id": "Building_part",
                        "source": "buildings",
                        "source-layer": "building_part",
                        "type": type,
                        "paint": kwargs,
                    },
                ]
            }

        self.add_pmtiles(
            url,
            style=style,
            visible=visible,
            opacity=opacity,
            tooltip=tooltip,
            fit_bounds=fit_bounds,
        )

    def add_video(
        self,
        urls: Union[str, List[str]],
        coordinates: List[List[float]],
        layer_id: str = "video",
        before_id: Optional[str] = None,
    ) -> None:
        """
        Adds a video layer to the map.

        This method allows embedding a video into the map by specifying the video URLs and the geographical coordinates
        that the video should cover. The video will be stretched and fitted into the specified coordinates.

        Args:
            urls (Union[str, List[str]]): A single video URL or a list of video URLs. These URLs must be accessible
                from the client's location.
            coordinates (List[List[float]]): A list of four coordinates in [longitude, latitude] format, specifying
                the corners of the video. The coordinates order should be top-left, top-right, bottom-right, bottom-left.
            layer_id (str): The ID for the video layer. Defaults to "video".
            before_id (Optional[str]): The ID of an existing layer to insert the new layer before. If None, the layer
                will be added on top. Defaults to None.

        Returns:
            None
        """

        if isinstance(urls, str):
            urls = [urls]
        source = {
            "type": "video",
            "urls": urls,
            "coordinates": coordinates,
        }
        self.add_source("video_source", source)
        layer = {
            "id": layer_id,
            "type": "raster",
            "source": "video_source",
        }
        self.add_layer(layer, before_id=before_id)

    def add_nlcd(self, years: list = [2023], add_legend: bool = True, **kwargs) -> None:
        """
        Adds National Land Cover Database (NLCD) data to the map.

        Args:
            years (list): A list of years to add. It can be any of 1985-2023. Defaults to [2023].
            add_legend (bool): Whether to add a legend to the map. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the add_cog_layer method.

        Returns:
            None
        """
        allowed_years = list(range(1985, 2024, 1))
        url = (
            "https://s3-us-west-2.amazonaws.com/mrlc/Annual_NLCD_LndCov_{}_CU_C1V0.tif"
        )

        if "colormap" not in kwargs:

            kwargs["colormap"] = {
                "11": "#466b9f",
                "12": "#d1def8",
                "21": "#dec5c5",
                "22": "#d99282",
                "23": "#eb0000",
                "24": "#ab0000",
                "31": "#b3ac9f",
                "41": "#68ab5f",
                "42": "#1c5f2c",
                "43": "#b5c58f",
                "51": "#af963c",
                "52": "#ccb879",
                "71": "#dfdfc2",
                "72": "#d1d182",
                "73": "#a3cc51",
                "74": "#82ba9e",
                "81": "#dcd939",
                "82": "#ab6c28",
                "90": "#b8d9eb",
                "95": "#6c9fb8",
            }

        if "zoom_to_layer" not in kwargs:
            kwargs["zoom_to_layer"] = False

        for year in years:
            if year not in allowed_years:
                raise ValueError(f"Year must be one of {allowed_years}.")
            year_url = url.format(year)
            self.add_cog_layer(year_url, name=f"NLCD {year}", **kwargs)
        if add_legend:
            self.add_legend(title="NLCD Land Cover Type", builtin_legend="NLCD")

    def add_gps_trace(
        self,
        data: Union[str, List[Dict[str, Any]]],
        x: str = None,
        y: str = None,
        columns: Optional[List[str]] = None,
        ann_column: Optional[str] = None,
        colormap: Optional[Dict[str, str]] = None,
        radius: int = 5,
        circle_color: Optional[Union[str, List[Any]]] = None,
        stroke_color: str = "#ffffff",
        opacity: float = 1.0,
        paint: Optional[Dict[str, Any]] = None,
        name: str = "GPS Trace",
        add_line: bool = True,
        sort_column: Optional[str] = None,
        line_args: Optional[Dict[str, Any]] = None,
        add_draw_control: bool = True,
        draw_control_args: Optional[Dict[str, Any]] = None,
        add_legend: bool = True,
        legend_args: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a GPS trace to the map.

        Args:
            data (Union[str, List[Dict[str, Any]]]): The GPS trace data. It can be a GeoJSON file path or a list of coordinates.
            x (str, optional): The column name for the x coordinates. Defaults to None,
                which assumes the x coordinates are in the "longitude", "lon", or "x" column.
            y (str, optional): The column name for the y coordinates. Defaults to None,
                which assumes the y coordinates are in the "latitude", "lat", or "y" column.
            columns (Optional[List[str]], optional): The list of columns to include in the GeoDataFrame. Defaults to None.
            ann_column (Optional[str], optional): The column name to use for coloring the GPS trace points. Defaults to None.
            colormap (Optional[Dict[str, str]], optional): The colormap for the GPS trace. Defaults to None.
            radius (int, optional): The radius of the GPS trace points. Defaults to 5.
            circle_color (Optional[Union[str, List[Any]]], optional): The color of the GPS trace points. Defaults to None.
            stroke_color (str, optional): The stroke color of the GPS trace points. Defaults to "#ffffff".
            opacity (float, optional): The opacity of the GPS trace points. Defaults to 1.0.
            paint (Optional[Dict[str, Any]], optional): The paint properties for the GPS trace points. Defaults to None.
            name (str, optional): The name of the GPS trace layer. Defaults to "GPS Trace".
            add_line (bool, optional): If True, adds a line connecting the GPS trace points. Defaults to True.
            sort_column (Optional[str], optional): The column name to sort the points before connecting them as a line. Defaults to None.
            line_args (Optional[Dict[str, Any]], optional): Additional keyword arguments for the add_gdf method for the line layer. Defaults to None.
            add_draw_control (bool, optional): If True, adds a draw control to the map. Defaults to True.
            draw_control_args (Optional[Dict[str, Any]], optional): Additional keyword arguments for the add_draw_control method. Defaults to None.
            add_legend (bool, optional): If True, adds a legend to the map. Defaults to True.
            legend_args (Optional[Dict[str, Any]], optional): Additional keyword arguments for the add_legend method. Defaults to None.
            **kwargs (Any): Additional keyword arguments to pass to the add_geojson method.

        Returns:
            None
        """

        from pathlib import Path

        if add_draw_control:
            if draw_control_args is None:
                draw_control_args = {
                    "controls": ["polygon", "point", "trash"],
                    "position": "top-right",
                }
            self.add_draw_control(**draw_control_args)

        if isinstance(data, Path):
            if data.exists():
                data = str(data)
            else:
                raise FileNotFoundError(f"File not found: {data}")

        if isinstance(data, str):
            tmp_file = os.path.splitext(data)[0] + "_tmp.csv"
            gdf = common.points_from_xy(data, x=x, y=y)
            # If the temporary file exists, read the annotations from it
            if os.path.exists(tmp_file):
                df = pd.read_csv(tmp_file)
                gdf[ann_column] = df[ann_column]
        elif isinstance(data, gpd.GeoDataFrame):
            gdf = data
        else:
            raise ValueError(
                "Invalid data type. Use a GeoDataFrame or a file path to a CSV file."
            )

        setattr(self, "gps_trace", gdf)

        if add_line:
            line_gdf = common.connect_points_as_line(
                gdf, sort_column=sort_column, single_line=True
            )
        else:
            line_gdf = None

        if colormap is None:
            colormap = {
                "selected": "#FFFF00",
            }

        if add_legend:
            if legend_args is None:
                legend_args = {
                    "legend_dict": colormap,
                    "shape_type": "circle",
                }
            self.add_legend(**legend_args)

        if (
            isinstance(list(colormap.values())[0], tuple)
            and len(list(colormap.values())[0]) == 2
        ):
            keys = list(colormap.keys())
            values = [value[1] for value in colormap.values()]
            colormap = dict(zip(keys, values))

        if ann_column is None:
            if "annotation" in gdf.columns:
                ann_column = "annotation"
            else:
                raise ValueError(
                    "Please specify the ann_column parameter or add an 'annotation' column to the GeoDataFrame."
                )

        ann_column_edited = f"{ann_column}_edited"
        gdf[ann_column_edited] = gdf[ann_column]

        if columns is None:
            columns = [
                ann_column,
                ann_column_edited,
                "geometry",
            ]

        if ann_column not in columns:
            columns.append(ann_column)

        if ann_column_edited not in columns:
            columns.append(ann_column_edited)
        if "geometry" not in columns:
            columns.append("geometry")
        gdf = gdf[columns]
        setattr(self, "gdf", gdf)
        if circle_color is None:
            circle_color = [
                "match",
                ["to-string", ["get", ann_column_edited]],
            ]
            # Add the color matches from the colormap
            for key, color in colormap.items():
                circle_color.extend([str(key), color])

            # Add the default color
            circle_color.append("#CCCCCC")  # Default color if annotation does not match

        geojson = gdf.__geo_interface__

        if paint is None:
            paint = {
                "circle-radius": radius,
                "circle-color": circle_color,
                "circle-stroke-width": 1,
                "circle-opacity": opacity,
            }
            if stroke_color is None:
                paint["circle-stroke-color"] = circle_color
            else:
                paint["circle-stroke-color"] = stroke_color

        if line_gdf is not None:
            if line_args is None:
                line_args = {}
            self.add_gdf(line_gdf, name=f"{name} Line", **line_args)

        if "fit_bounds_options" not in kwargs:
            kwargs["fit_bounds_options"] = {"animate": False}
        self.add_geojson(geojson, layer_type="circle", paint=paint, name=name, **kwargs)

    def add_data(
        self,
        data: Union[str, pd.DataFrame, "gpd.GeoDataFrame"],
        column: str,
        cmap: Optional[str] = None,
        colors: Optional[str] = None,
        labels: Optional[str] = None,
        scheme: Optional[str] = "Quantiles",
        k: int = 5,
        add_legend: Optional[bool] = True,
        legend_title: Optional[bool] = None,
        legend_position: Optional[str] = "bottom-right",
        legend_kwds: Optional[dict] = None,
        classification_kwds: Optional[dict] = None,
        legend_args: Optional[dict] = None,
        layer_type: Optional[str] = None,
        extrude: Optional[bool] = False,
        scale_factor: Optional[float] = 1.0,
        filter: Optional[Dict] = None,
        paint: Optional[Dict] = None,
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        opacity: float = 1.0,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """Add vector data to the map with a variety of classification schemes.

        Args:
            data (str | pd.DataFrame | gpd.GeoDataFrame): The data to classify.
                It can be a filepath to a vector dataset, a pandas dataframe, or
                a geopandas geodataframe.
            column (str): The column to classify.
            cmap (str, optional): The name of a colormap recognized by matplotlib. Defaults to None.
            colors (list, optional): A list of colors to use for the classification. Defaults to None.
            labels (list, optional): A list of labels to use for the legend. Defaults to None.
            scheme (str, optional): Name of a choropleth classification scheme (requires mapclassify).
                Name of a choropleth classification scheme (requires mapclassify).
                A mapclassify.MapClassifier object will be used
                under the hood. Supported are all schemes provided by mapclassify (e.g.
                'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
                'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
                'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
                'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
                'UserDefined'). Arguments can be passed in classification_kwds.
            k (int, optional): Number of classes (ignored if scheme is None or if
                column is categorical). Default to 5.
            add_legend (bool, optional): Whether to add a legend to the map. Defaults to True.
            legend_title (str, optional): The title of the legend. Defaults to None.
            legend_position (str, optional): The position of the legend. Can be 'top-left',
                'top-right', 'bottom-left', or 'bottom-right'. Defaults to 'bottom-right'.
            legend_kwds (dict, optional): Keyword arguments to pass to :func:`matplotlib.pyplot.legend`
                or `matplotlib.pyplot.colorbar`. Defaults to None.
                Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or
                Additional accepted keywords when `scheme` is specified:
                fmt : string
                    A formatting specification for the bin edges of the classes in the
                    legend. For example, to have no decimals: ``{"fmt": "{:.0f}"}``.
                labels : list-like
                    A list of legend labels to override the auto-generated labblels.
                    Needs to have the same number of elements as the number of
                    classes (`k`).
                interval : boolean (default False)
                    An option to control brackets from mapclassify legend.
                    If True, open/closed interval brackets are shown in the legend.
            classification_kwds (dict, optional): Keyword arguments to pass to mapclassify.
                Defaults to None.
            legend_args (dict, optional): Additional keyword arguments for the add_legend method. Defaults to None.
            layer_type (str, optional): The type of layer to add. Can be 'circle', 'line', or 'fill'. Defaults to None.
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
            **kwargs: Additional keyword arguments to pass to the GeoJSON class, such as
                fields, which can be a list of column names to be included in the popup.

        """

        gdf, legend_dict = common.classify(
            data=data,
            column=column,
            cmap=cmap,
            colors=colors,
            labels=labels,
            scheme=scheme,
            k=k,
            legend_kwds=legend_kwds,
            classification_kwds=classification_kwds,
        )

        if legend_title is None:
            legend_title = column

        geom_type = gdf.geometry.iloc[0].geom_type

        if geom_type == "Point" or geom_type == "MultiPoint":
            layer_type = "circle"
            if paint is None:
                paint = {
                    "circle-color": ["get", "color"],
                    "circle-radius": 5,
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1,
                    "circle-opacity": opacity,
                }
        elif geom_type == "LineString" or geom_type == "MultiLineString":
            layer_type = "line"
            if paint is None:
                paint = {
                    "line-color": ["get", "color"],
                    "line-width": 2,
                    "line-opacity": opacity,
                }
        elif geom_type == "Polygon" or geom_type == "MultiPolygon":
            if extrude:
                layer_type = "fill-extrusion"
                if paint is None:
                    # Initialize the interpolate format
                    paint = {
                        "fill-extrusion-color": [
                            "interpolate",
                            ["linear"],
                            ["get", column],
                        ]
                    }

                    # Parse the dictionary and append range and color values
                    for range_str, color in legend_dict.items():
                        # Extract the upper bound from the range string
                        upper_bound = float(range_str.split(",")[-1].strip(" ]"))
                        # Add to the formatted output
                        paint["fill-extrusion-color"].extend([upper_bound, color])

                    # Scale down the extrusion height
                    paint["fill-extrusion-height"] = [
                        "interpolate",
                        ["linear"],
                        ["get", column],
                    ]

                    # Add scaled values dynamically
                    for range_str in legend_dict.keys():
                        upper_bound = float(range_str.split(",")[-1].strip(" ]"))
                        scaled_value = upper_bound / scale_factor  # Apply scaling
                        paint["fill-extrusion-height"].extend(
                            [upper_bound, scaled_value]
                        )

            else:

                layer_type = "fill"
                if paint is None:
                    paint = {
                        "fill-color": ["get", "color"],
                        "fill-opacity": opacity,
                        "fill-outline-color": "#ffffff",
                    }
        else:
            raise ValueError("Geometry type not recognized.")

        self.add_gdf(
            gdf,
            layer_type,
            filter,
            paint,
            name,
            fit_bounds,
            visible,
            before_id,
            source_args,
            **kwargs,
        )
        if legend_args is None:
            legend_args = {}
        if add_legend:
            self.add_legend(
                title=legend_title,
                legend_dict=legend_dict,
                position=legend_position,
                **legend_args,
            )

    def add_mapillary(
        self,
        minzoom: int = 6,
        maxzoom: int = 14,
        sequence_lyr_name: str = "sequence",
        image_lyr_name: str = "image",
        before_id: str = None,
        sequence_paint: dict = None,
        image_paint: dict = None,
        image_minzoom: int = 17,
        add_popup: bool = True,
        access_token: str = None,
    ) -> None:
        """
        Adds Mapillary layers to the map.

        Args:
            minzoom (int): Minimum zoom level for the Mapillary tiles. Defaults to 6.
            maxzoom (int): Maximum zoom level for the Mapillary tiles. Defaults to 14.
            sequence_lyr_name (str): Name of the sequence layer. Defaults to "sequence".
            image_lyr_name (str): Name of the image layer. Defaults to "image".
            before_id (str): The ID of an existing layer to insert the new layer before. Defaults to None.
            sequence_paint (dict, optional): Paint properties for the sequence layer. Defaults to None.
            image_paint (dict, optional): Paint properties for the image layer. Defaults to None.
            image_minzoom (int): Minimum zoom level for the image layer. Defaults to 17.
            add_popup (bool): Whether to add popups to the layers. Defaults to True.
            access_token (str, optional): Access token for Mapillary API. Defaults to None.

        Raises:
            ValueError: If no access token is provided.

        Returns:
            None
        """

        if access_token is None:
            access_token = common.get_api_key("MAPILLARY_API_KEY")

        if access_token is None:
            raise ValueError("An access token is required to use Mapillary.")

        url = f"https://tiles.mapillary.com/maps/vtp/mly1_public/2/{{z}}/{{x}}/{{y}}?access_token={access_token}"

        source = {
            "type": "vector",
            "tiles": [url],
            "minzoom": minzoom,
            "maxzoom": maxzoom,
        }
        self.add_source("mapillary", source)

        if sequence_paint is None:
            sequence_paint = {
                "line-opacity": 0.6,
                "line-color": "#35AF6D",
                "line-width": 2,
            }
        if image_paint is None:
            image_paint = {
                "circle-radius": 4,
                "circle-color": "#3388ff",
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1,
            }

        sequence_lyr = {
            "id": sequence_lyr_name,
            "type": "line",
            "source": "mapillary",
            "source-layer": "sequence",
            "layout": {"line-cap": "round", "line-join": "round"},
            "paint": sequence_paint,
        }
        image_lyr = {
            "id": image_lyr_name,
            "type": "circle",
            "source": "mapillary",
            "source-layer": "image",
            "paint": image_paint,
            "minzoom": image_minzoom,
        }

        self.add_layer(sequence_lyr, name=sequence_lyr_name, before_id=before_id)
        self.add_layer(image_lyr, name=image_lyr_name, before_id=before_id)
        if add_popup:
            self.add_popup(sequence_lyr_name)
            self.add_popup(image_lyr_name)

    def create_mapillary_widget(
        self,
        lon: Optional[float] = None,
        lat: Optional[float] = None,
        radius: float = 0.00005,
        bbox: Optional[Union[str, List[float]]] = None,
        image_id: Optional[str] = None,
        style: str = "classic",
        width: int = 560,
        height: int = 600,
        frame_border: int = 0,
        link: bool = True,
        container: bool = True,
        column_widths: List[int] = [8, 1],
        **kwargs: Any,
    ) -> Union[widgets.HTML, v.Row]:
        """
        Creates a Mapillary widget.

        Args:
            lon (Optional[float]): Longitude of the location. Defaults to None.
            lat (Optional[float]): Latitude of the location. Defaults to None.
            radius (float): Search radius for Mapillary images. Defaults to 0.00005.
            bbox (Optional[Union[str, List[float]]]): Bounding box for the search. Defaults to None.
            image_id (Optional[str]): ID of the Mapillary image. Defaults to None.
            style (str): Style of the Mapillary image. Can be "classic", "photo", and "split". Defaults to "classic".
            height (int): Height of the iframe. Defaults to 600.
            frame_border (int): Frame border of the iframe. Defaults to 0.
            link (bool): Whether to link the widget to map clicks. Defaults to True.
            container (bool): Whether to return the widget in a container. Defaults to True.
            column_widths (List[int]): Widths of the columns in the container. Defaults to [8, 1].
            **kwargs: Additional keyword arguments for the widget.

        Returns:
            Union[widgets.HTML, v.Row]: The Mapillary widget or a container with the widget.
        """

        if image_id is None:
            if lon is None or lat is None:
                if "center" in self.view_state:
                    center = self.view_state
                    if len(center) > 0:
                        lon = center["lng"]
                        lat = center["lat"]
                else:
                    lon = 0
                    lat = 0
            image_ids = common.search_mapillary_images(lon, lat, radius, bbox, limit=1)
            if len(image_ids) > 0:
                image_id = image_ids[0]

        if image_id is None:
            widget = widgets.HTML()
        else:
            widget = common.get_mapillary_image_widget(
                image_id, style, width, height, frame_border, **kwargs
            )

        if link:

            def log_lng_lat(lng_lat):
                lon = lng_lat.new["lng"]
                lat = lng_lat.new["lat"]
                image_id = common.search_mapillary_images(
                    lon, lat, radius=radius, limit=1
                )
                if len(image_id) > 0:
                    content = f"""
                    <iframe
                        src="https://www.mapillary.com/embed?image_key={image_id[0]}&style={style}"
                        height="{height}"
                        width="{width}"
                        frameborder="{frame_border}">
                    </iframe>
                    """
                    widget.value = content
                else:
                    widget.value = "No Mapillary image found."

            self.observe(log_lng_lat, names="clicked")

        if container:
            left_col_layout = v.Col(
                cols=column_widths[0],
                children=[self],
                class_="pa-1",  # padding for consistent spacing
            )
            right_col_layout = v.Col(
                cols=column_widths[1],
                children=[widget],
                class_="pa-1",  # padding for consistent spacing
            )
            row = v.Row(
                children=[left_col_layout, right_col_layout],
            )
            return row
        else:

            return widget


class Container(v.Container):

    def __init__(self, host_map=None, *args, **kwargs):

        # Create the left column with the map
        left_col_layout = v.Col(
            cols=11, children=[], class_="pa-1"  # padding for consistent spacing
        )
        if host_map is not None:
            left_col_layout.children = [host_map]

        # Create the right column with some output
        right_col_layout = v.Col(
            cols=1,
            children=[v.Card(children=[v.CardText(children=["Output Content"])])],
            class_="pa-1",  # padding for consistent spacing
        )

        # Create a toggle button with an icon
        btn = v.Btn(
            children=[
                v.Icon(left=False, children=["mdi-layers"]),
            ],
            # class_='ma-1',
            v_model=False,
        )

        # Create the button toggle
        toggle = v.BtnToggle(v_model="toggle_exclusive", children=[btn])

        # Function to change column widths
        def change_column_widths(*args, **kwargs):
            if toggle.v_model == 0:
                left_col_layout.cols = 10
                right_col_layout.cols = 2
            else:
                left_col_layout.cols = 11
                right_col_layout.cols = 1

        # Observe changes in the v_model of the toggle button
        toggle.on_event("change", change_column_widths)

        # Update the right column to include the toggle button
        right_col_layout.children = [toggle]
        row = v.Row(
            class_="d-flex flex-wrap",
            children=[left_col_layout, right_col_layout],
            *args,
            **kwargs,
        )
        super().__init__(fluid=True, children=[row])


def construct_maptiler_style(style: str, api_key: Optional[str] = None) -> str:
    """
    Constructs a URL for a MapTiler style with an optional API key.

    This function generates a URL for accessing a specific MapTiler map style. If an API key is not provided,
    it attempts to retrieve one using a predefined method. If the request to MapTiler fails, it defaults to
    a "liberty" style.

    Args:
        style (str): The name of the MapTiler style to be accessed. It can be one of the following:
            aquarelle, backdrop, basic, bright, dataviz, landscape, ocean, openstreetmap, outdoor,
            satellite, streets, toner, topo, winter, etc.
        api_key (Optional[str]): An optional API key for accessing MapTiler services. If None, the function
            attempts to retrieve the API key using a predefined method. Defaults to None.

    Returns:
        str: The URL for the requested MapTiler style. If the request fails, returns a URL for the "liberty" style.

    Raises:
        requests.exceptions.RequestException: If the request to the MapTiler API fails.
    """

    if api_key is None:
        api_key = common.get_api_key("MAPTILER_KEY")

    url = f"https://api.maptiler.com/maps/{style}/style.json?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        print(
            "Failed to retrieve the MapTiler style. Defaulting to OpenFreeMap 'liberty' style."
        )
        url = "https://tiles.openfreemap.org/styles/liberty"

    return url


def maptiler_3d_style(
    style="satellite",
    exaggeration: float = 1,
    tile_size: int = 512,
    tile_type: str = None,
    max_zoom: int = 24,
    hillshade: bool = True,
    token: str = "MAPTILER_KEY",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the 3D terrain style for the map.

    This function generates a style dictionary for the map that includes 3D terrain features.
    The terrain exaggeration and API key can be specified. If the API key is not provided,
    it will be retrieved using the specified token.

    Args:
        style (str): The name of the MapTiler style to be accessed. It can be one of the following:
            aquarelle, backdrop, basic, bright, dataviz, hillshade, landscape, ocean, openstreetmap, outdoor,
            satellite, streets, toner, topo, winter, etc.
        exaggeration (float, optional): The terrain exaggeration. Defaults to 1.
        tile_size (int, optional): The size of the tiles. Defaults to 512.
        tile_type (str, optional): The type of the tiles. It can be one of the following:
            webp, png, jpg. Defaults to None.
        max_zoom (int, optional): The maximum zoom level. Defaults to 24.
        hillshade (bool, optional): Whether to include hillshade. Defaults to True.
        token (str, optional): The token to use to retrieve the API key. Defaults to "MAPTILER_KEY".
        api_key (Optional[str], optional): The API key. If not provided, it will be retrieved using the token.

    Returns:
        Dict[str, Any]: The style dictionary for the map.

    Raises:
        ValueError: If the API key is not provided and cannot be retrieved using the token.
    """

    if api_key is None:
        api_key = common.get_api_key(token)

    if api_key is None:
        print("An API key is required to use the 3D terrain feature.")
        return "dark-matter"

    if style == "terrain":
        style = "satellite"
    elif style == "hillshade":
        style = None

    if tile_type is None:

        image_types = {
            "aquarelle": "webp",
            "backdrop": "png",
            "basic": "png",
            "basic-v2": "png",
            "bright": "png",
            "bright-v2": "png",
            "dataviz": "png",
            "hybrid": "jpg",
            "landscape": "png",
            "ocean": "png",
            "openstreetmap": "jpg",
            "outdoor": "png",
            "outdoor-v2": "png",
            "satellite": "jpg",
            "toner": "png",
            "toner-v2": "png",
            "topo": "png",
            "topo-v2": "png",
            "winter": "png",
            "winter-v2": "png",
        }
        if style in image_types:
            tile_type = image_types[style]
        else:
            tile_type = "png"

    layers = []

    if isinstance(style, str):
        layers.append({"id": style, "type": "raster", "source": style})

    if hillshade:
        layers.append(
            {
                "id": "hillshade",
                "type": "hillshade",
                "source": "hillshadeSource",
                "layout": {"visibility": "visible"},
                "paint": {"hillshade-shadow-color": "#473B24"},
            }
        )

    if style == "ocean":
        sources = {
            "terrainSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/ocean-rgb/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
            "hillshadeSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/ocean-rgb/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
        }
    else:
        sources = {
            "terrainSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
            "hillshadeSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
        }
    if isinstance(style, str):
        sources[style] = {
            "type": "raster",
            "tiles": [
                "https://api.maptiler.com/maps/"
                + style
                + "/{z}/{x}/{y}."
                + tile_type
                + "?key="
                + api_key
            ],
            "tileSize": tile_size,
            "attribution": "&copy; MapTiler",
            "maxzoom": max_zoom,
        }

    style = {
        "version": 8,
        "sources": sources,
        "layers": layers,
        "terrain": {"source": "terrainSource", "exaggeration": exaggeration},
    }

    return style


def edit_gps_trace(
    filename: str,
    m: Any,
    ann_column: str,
    colormap: Dict[str, str],
    layer_name: str,
    default_features: Optional[List[str]] = None,
    ann_options: Optional[List[str]] = None,
    rows: int = 11,
    fig_width: str = "1550px",
    fig_height: str = "300px",
    time_format: str = "%Y%m%dT%H%M%S",
    stroke_color: str = "lightgray",
    circle_size: int = 48,
    webGL: bool = False,
    download: bool = False,
    sync_plots: bool = False,
    column_widths: Optional[List[int]] = (9, 3),
    **kwargs,
) -> Any:
    """
    Edits a GPS trace on the map and allows for annotation and export.

    Args:
        filename (str): The path to the GPS trace CSV file.
        m (Any): The map object containing the GPS trace.
        ann_column (str): The annotation column in the GPS trace.
        colormap (Dict[str, str]): The colormap for the GPS trace annotations.
        layer_name (str): The name of the GPS trace layer.
        default_features (Optional[str], optional): The default features to display.
            The first numerical column will be used if None. Defaults to None.
        ann_options (Optional[List[str]], optional): The annotation options for the dropdown. Defaults to None.
        rows (int, optional): The number of rows to display in the table. Defaults to 11.
        fig_width (str, optional): The width of the figure. Defaults to "1550px".
        fig_height (str, optional): The height of the figure. Defaults to "300px".
        time_format (str, optional): The time format for the timestamp. Defaults to "%Y-%m-%d %H:%M:%S".
        stroke_color (str, optional): The stroke color of the GPS trace points. Defaults to "lightgray".
        circle_size (int, optional): The size of the GPS trace points. Defaults to 48.
        webGL (bool, optional): Whether to use WebGL (bqplot-gl) for rendering. Defaults to False.
        download (bool, optional): Whether to generate links for downloading the edited GPS traces. Defaults to False.
        sync_plots (bool, optional): Whether to synchronize the zoom and pan of the plots. Defaults to False.
        column_widths (Optional[List[int]], optional): The column widths for the output widget. Defaults to (9, 3).
        **kwargs: Additional keyword arguments.

    Returns:
        Any: The main widget containing the map and the editing interface.
    """

    from pathlib import Path
    from datetime import datetime
    from bqplot import LinearScale, Figure, PanZoom
    import bqplot as bq

    if webGL:
        try:
            from bqplot_gl import ScatterGL as Scatter
        except ImportError:
            raise ImportError(
                "Please install bqplot_gl using 'pip install --pre bqplot-gl'"
            )
    else:
        from bqplot import Scatter

    if isinstance(filename, Path):
        if filename.exists():
            filename = str(filename)
        else:
            raise FileNotFoundError(f"File not found: {filename}")

    output = widgets.Output()
    download_widget = widgets.Output()

    fig_margin = {"top": 20, "bottom": 35, "left": 50, "right": 20}
    x_sc = LinearScale()
    y_sc = LinearScale()

    setattr(m, "_x_sc", x_sc)

    features = sorted(list(m.gps_trace.columns))
    if "geometry" in features:
        features.remove("geometry")

    # Use the first numerical column as the default feature
    if default_features is None:
        dtypes = m.gps_trace.dtypes
        for index, dtype in enumerate(dtypes):
            if "float64" in str(dtype):
                default_features = [features[index]]
                break

    default_index = features.index(default_features[0])
    feature = widgets.Dropdown(
        options=features, index=default_index, description="Primary"
    )

    column = feature.value
    ann_column_edited = f"{ann_column}_edited"
    x = m.gps_trace.index
    y = m.gps_trace[column]

    # Create scatter plots for each annotation category with the appropriate colors and labels
    scatters = []
    additonal_scatters = []

    if isinstance(list(colormap.values())[0], tuple):
        keys = list(colormap.keys())
        values = [value[1] for value in colormap.values()]
        colormap = dict(zip(keys, values))

    for cat, color in colormap.items():
        if (
            cat != "selected"
        ):  # Exclude 'selected' from data points (only for highlighting selection)
            mask = m.gps_trace[ann_column] == cat
            scatter = Scatter(
                x=x[mask],
                y=y[mask],
                scales={"x": x_sc, "y": y_sc},
                colors=[color],
                marker="circle",
                stroke=stroke_color,
                unselected_style={"opacity": 0.1},
                selected_style={"opacity": 1.0},
                default_size=circle_size,  # Set a smaller default marker size
                display_legend=False,
                labels=[str(cat)],  # Add the category label for the legend
            )
            scatters.append(scatter)

    # Create the figure and add the scatter plots
    fig = Figure(
        marks=scatters,
        fig_margin=fig_margin,
        layout={"width": fig_width, "height": fig_height},
    )
    fig.axes = [
        bq.Axis(scale=x_sc, label="Time"),
        bq.Axis(scale=y_sc, orientation="vertical", label=column),
    ]

    fig.legend_location = "top-right"

    # Add LassoSelector interaction
    selector = bq.interacts.LassoSelector(x_scale=x_sc, y_scale=y_sc, marks=scatters)
    fig.interaction = selector

    # Add PanZoom interaction for zooming and panning
    panzoom = PanZoom(scales={"x": [x_sc], "y": [y_sc]})
    fig.interaction = (
        panzoom  # Set PanZoom as the interaction to enable zooming initially
    )

    # Callback function to handle selected points with bounds check
    def on_select(*args):
        with output:
            selected_idx = []
            for index, scatter in enumerate(scatters):
                selected_indices = scatter.selected
                if selected_indices is not None:
                    selected_indices = [
                        int(i) for i in selected_indices if i < len(scatter.x)
                    ]  # Ensure integer indices
                    selected_x = scatter.x[selected_indices]
                    # selected_y = scatter.y[selected_indices]
                    selected_idx += selected_x.tolist()

                for scas in additonal_scatters:
                    scas[index].selected = selected_indices

            selected_idx = sorted(list(set(selected_idx)))
            m.gdf.loc[selected_idx, ann_column_edited] = "selected"
            m.set_data(layer_name, m.gdf.__geo_interface__)

    # Register the callback for each scatter plot
    for scatter in scatters:
        scatter.observe(on_select, names=["selected"])

    # Programmatic selection function based on common x values
    def select_points_by_common_x(x_values):
        """
        Select points based on a common list of x values across all categories.
        """
        for scatter in scatters:
            # Find indices of points in the scatter that match the given x values
            selected_indices = [
                i for i, x_val in enumerate(scatter.x) if x_val in x_values
            ]
            scatter.selected = (
                selected_indices  # Highlight points at the specified indices
            )

    # Programmatic selection function based on common x values
    def select_additional_points_by_common_x(x_values):
        """
        Select points based on a common list of x values across all categories.
        """
        for scas in additonal_scatters:
            for scatter in scas:
                # Find indices of points in the scatter that match the given x values
                selected_indices = [
                    i for i, x_val in enumerate(scatter.x) if x_val in x_values
                ]
                scatter.selected = (
                    selected_indices  # Highlight points at the specified indices
                )

    # Function to clear the lasso selection
    def clear_selection(b):
        for scatter in scatters:
            scatter.selected = None  # Clear selected points
        fig.interaction = panzoom
        fig.interaction = selector  # Re-enable the LassoSelector

        m.gdf[ann_column_edited] = m.gdf[ann_column]
        m.set_data(layer_name, m.gdf.__geo_interface__)

    # Button to clear selection and switch between interactions
    clear_button = widgets.Button(description="Clear Selection", button_style="primary")
    clear_button.on_click(clear_selection)

    # Toggle between LassoSelector and PanZoom interactions
    def toggle_interaction(button):
        if fig.interaction == selector:
            fig.interaction = panzoom  # Switch to PanZoom for zooming and panning
            button.description = "Enable Lasso"
        else:
            fig.interaction = selector  # Switch back to LassoSelector
            button.description = "Enable Zoom/Pan"

    toggle_button = widgets.Button(
        description="Enable Zoom/Pan", button_style="primary"
    )
    toggle_button.on_click(toggle_interaction)

    def feature_change(change):
        if change["new"]:
            categories = m.gdf[ann_column].value_counts()
            keys = list(colormap.keys())[:-1]
            for index, cat in enumerate(keys):

                fig.axes = [
                    bq.Axis(scale=x_sc, label="Time"),
                    bq.Axis(scale=y_sc, orientation="vertical", label=feature.value),
                ]

                mask = m.gdf[ann_column] == cat
                scatters[index].x = m.gps_trace.index[mask]
                scatters[index].y = m.gps_trace[feature.value][mask]
                scatters[index].colors = [colormap[cat]] * categories[cat]
            for scatter in scatters:
                scatter.selected = None

    feature.observe(feature_change, names="value")

    def draw_change(lng_lat):
        if lng_lat.new:
            output.clear_output()
            features = {
                "type": "FeatureCollection",
                "features": m.draw_features_selected,
            }
            geom_type = features["features"][0]["geometry"]["type"]
            m.gdf[ann_column_edited] = m.gdf[ann_column]
            gdf_draw = gpd.GeoDataFrame.from_features(features)
            # Select points within the drawn polygon
            if geom_type == "Polygon":
                points_within_polygons = gpd.sjoin(
                    m.gdf, gdf_draw, how="left", predicate="within"
                )
                points_within_polygons.loc[
                    points_within_polygons["index_right"].notna(), ann_column_edited
                ] = "selected"
                with output:
                    selected = points_within_polygons.loc[
                        points_within_polygons[ann_column_edited] == "selected"
                    ]
                    sel_idx = selected.index.tolist()
                select_points_by_common_x(sel_idx)
                select_additional_points_by_common_x(sel_idx)
                m.set_data(layer_name, points_within_polygons.__geo_interface__)
                if "index_right" in points_within_polygons.columns:
                    points_within_polygons = points_within_polygons.drop(
                        columns=["index_right"]
                    )
                m.gdf = points_within_polygons
            # Select the nearest point to the drawn point
            elif geom_type == "Point":
                single_point = gdf_draw.geometry.iloc[0]
                m.gdf["distance"] = m.gdf.geometry.distance(single_point)
                nearest_index = m.gdf["distance"].idxmin()
                sel_idx = [nearest_index]
                m.gdf.loc[sel_idx, ann_column_edited] = "selected"
                select_points_by_common_x(sel_idx)
                select_additional_points_by_common_x(sel_idx)
                m.set_data(layer_name, m.gdf.__geo_interface__)
                m.gdf = m.gdf.drop(columns=["distance"])

        else:
            for scatter in scatters:
                scatter.selected = None  # Clear selected points
            for scas in additonal_scatters:
                for scatter in scas:
                    scatter.selected = None
            fig.interaction = selector  # Re-enable the LassoSelector

            m.gdf[ann_column_edited] = m.gdf[ann_column]
            m.set_data(layer_name, m.gdf.__geo_interface__)

    m.observe(draw_change, names="draw_features_selected")

    widget = widgets.VBox(
        [],
    )
    if ann_options is None:
        ann_options = list(colormap.keys())

    multi_select = widgets.SelectMultiple(
        options=features,
        value=[],
        description="Secondary",
        rows=rows,
    )
    dropdown = widgets.Dropdown(
        options=ann_options, value=None, description="annotation"
    )
    button_layout = widgets.Layout(width="97px")
    save = widgets.Button(
        description="Save", button_style="primary", layout=button_layout
    )
    export = widgets.Button(
        description="Export", button_style="primary", layout=button_layout
    )
    reset = widgets.Button(
        description="Reset", button_style="primary", layout=button_layout
    )
    widget.children = [
        feature,
        multi_select,
        dropdown,
        widgets.HBox([save, export, reset]),
        output,
        download_widget,
    ]

    features_widget = widgets.VBox([])

    def features_change(change):
        if change["new"]:

            selected_features = multi_select.value
            children = []
            additonal_scatters.clear()
            if selected_features:
                for selected_feature in selected_features:

                    x = m.gps_trace.index
                    y = m.gps_trace[selected_feature]
                    if sync_plots:
                        x_sc = m._x_sc
                    else:
                        x_sc = LinearScale()
                    y_sc2 = LinearScale()

                    # Create scatter plots for each annotation category with the appropriate colors and labels
                    scatters = []
                    for cat, color in colormap.items():

                        if (
                            cat != "selected"
                        ):  # Exclude 'selected' from data points (only for highlighting selection)
                            mask = m.gps_trace[ann_column] == cat
                            scatter = Scatter(
                                x=x[mask],
                                y=y[mask],
                                scales={"x": x_sc, "y": y_sc2},
                                colors=[color],
                                marker="circle",
                                stroke=stroke_color,
                                unselected_style={"opacity": 0.1},
                                selected_style={"opacity": 1.0},
                                default_size=circle_size,  # Set a smaller default marker size
                                display_legend=False,
                                labels=[
                                    str(cat)
                                ],  # Add the category label for the legend
                            )
                            scatters.append(scatter)
                    additonal_scatters.append(scatters)

                    # Create the figure and add the scatter plots
                    fig = Figure(
                        marks=scatters,
                        fig_margin=fig_margin,
                        layout={"width": fig_width, "height": fig_height},
                    )
                    fig.axes = [
                        bq.Axis(scale=x_sc, label="Time"),
                        bq.Axis(
                            scale=y_sc2,
                            orientation="vertical",
                            label=selected_feature,
                        ),
                    ]

                    fig.legend_location = "top-right"

                    # Add LassoSelector interaction
                    selector = bq.interacts.LassoSelector(
                        x_scale=x_sc, y_scale=y_sc, marks=scatters
                    )
                    fig.interaction = selector

                    # Add PanZoom interaction for zooming and panning
                    panzoom = PanZoom(scales={"x": [x_sc], "y": [y_sc2]})
                    fig.interaction = panzoom  # Set PanZoom as the interaction to enable zooming initially
                    children.append(fig)
                features_widget.children = children

    multi_select.observe(features_change, names="value")
    multi_select.value = default_features[1:]

    def on_save_click(b):
        output.clear_output()
        download_widget.clear_output()

        m.gdf.loc[m.gdf[ann_column_edited] == "selected", ann_column] = dropdown.value
        m.gdf.loc[m.gdf[ann_column_edited] == "selected", ann_column_edited] = (
            dropdown.value
        )
        m.set_data(layer_name, m.gdf.__geo_interface__)
        categories = m.gdf[ann_column].value_counts()
        keys = list(colormap.keys())[:-1]
        for index, cat in enumerate(keys):
            mask = m.gdf[ann_column] == cat
            scatters[index].x = m.gps_trace.index[mask]
            scatters[index].y = m.gps_trace[feature.value][mask]
            scatters[index].colors = [colormap[cat]] * categories[cat]

        for idx, scas in enumerate(additonal_scatters):
            for index, cat in enumerate(keys):
                mask = m.gdf[ann_column] == cat
                scas[index].x = m.gps_trace.index[mask]
                scas[index].y = m.gps_trace[multi_select.value[idx]][mask]
                scas[index].colors = [colormap[cat]] * categories[cat]

        for scatter in scatters:
            scatter.selected = None  # Clear selected points
        fig.interaction = selector  # Re-enable the LassoSelector

        m.gdf[ann_column_edited] = m.gdf[ann_column]
        m.set_data(layer_name, m.gdf.__geo_interface__)

        # Save the annotation to a temporary file
        temp_file = os.path.splitext(filename)[0] + "_tmp.csv"
        m.gdf[[ann_column]].to_csv(temp_file, index=False)

    save.on_click(on_save_click)

    def on_export_click(b):
        output.clear_output()
        download_widget.clear_output()
        with output:
            print("Exporting annotated GPS trace...")
        changed_inx = m.gdf[m.gdf[ann_column] != m.gps_trace[ann_column]].index
        m.gps_trace.loc[changed_inx, "changed_timestamp"] = datetime.now().strftime(
            time_format
        )
        m.gps_trace[ann_column] = m.gdf[ann_column]
        gdf = m.gps_trace.drop(columns=[ann_column_edited])

        out_dir = os.path.dirname(filename)
        basename = os.path.basename(filename)
        current_time = datetime.now().strftime(time_format)

        output_csv = os.path.join(
            out_dir, basename.replace(".csv", f"_edited_{current_time}.csv")
        )
        output_geojson = output_csv.replace(".csv", ".geojson")

        gdf.to_file(output_geojson)
        gdf.to_csv(output_csv, index=False)

        if download:
            csv_link = common.create_download_link(
                output_csv, title="Download ", basename=output_csv.split("_")[-1]
            )
            geojson_link = common.create_download_link(
                output_geojson,
                title="Download ",
                basename=output_geojson.split("_")[-1],
            )

            with output:
                output.clear_output()
                display(csv_link)
            with download_widget:
                download_widget.clear_output()
                display(geojson_link)
        else:
            with output:
                output.clear_output()
                print(f"Saved CSV: {os.path.basename(output_csv)}")
                print(f"Saved GeoJSON: {os.path.basename(output_geojson)}")

        # Remove the temporary file if it exists
        tmp_file = os.path.splitext(filename)[0] + "_tmp.csv"
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

    export.on_click(on_export_click)

    def on_reset_click(b):
        multi_select.value = []
        features_widget.children = []
        output.clear_output()
        download_widget.clear_output()

    reset.on_click(on_reset_click)

    plot_widget = widgets.VBox([fig, widgets.HBox([clear_button, toggle_button])])

    left_col_layout = v.Col(
        cols=column_widths[0],
        children=[m],
        class_="pa-1",  # padding for consistent spacing
    )
    right_col_layout = v.Col(
        cols=column_widths[1],
        children=[widget],
        class_="pa-1",  # padding for consistent spacing
    )
    row1 = v.Row(
        class_="d-flex flex-wrap",
        children=[left_col_layout, right_col_layout],
    )
    row2 = v.Row(
        class_="d-flex flex-wrap",
        children=[plot_widget],
    )
    row3 = v.Row(
        class_="d-flex flex-wrap",
        children=[features_widget],
    )
    main_widget = v.Col(children=[row1, row2, row3])
    return main_widget


def open_gps_trace(
    columns: List[str] = None,
    ann_column: str = None,
    colormap: Dict[str, str] = None,
    layer_name: str = "GPS Trace",
    default_features: Optional[List[str]] = None,
    ann_options: Optional[List[str]] = None,
    rows: int = 11,
    fig_width: str = "1550px",
    fig_height: str = "300px",
    time_format: str = "%Y%m%dT%H%M%S",
    radius: int = 4,
    stroke_color: str = "lightgray",
    circle_size: int = 48,
    webGL: bool = False,
    download: bool = False,
    sync_plots: bool = False,
    column_widths: Optional[List[int]] = (9, 3),
    add_layer_args: Dict[str, Any] = None,
    arrow_args: Dict[str, Any] = None,
    map_height: str = "600px",
    **kwargs: Any,
) -> widgets.VBox:
    """
    Creates a widget for uploading and displaying a GPS trace on a map.

    Args:
        columns (List[str], optional): The columns to display in the GPS trace popup. Defaults to None.
        ann_column (str): The annotation column in the GPS trace.
        colormap (Dict[str, str]): The colormap for the GPS trace annotations.
        layer_name (str): The name of the GPS trace layer.
        default_features (Optional[str], optional): The default features to display.
            The first numerical column will be used if None. Defaults to None.
        ann_options (Optional[List[str]], optional): The annotation options for the dropdown. Defaults to None.
        rows (int, optional): The number of rows to display in the table. Defaults to 11.
        fig_width (str, optional): The width of the figure. Defaults to "1550px".
        fig_height (str, optional): The height of the figure. Defaults to "300px".
        time_format (str, optional): The time format for the timestamp. Defaults to "%Y-%m-%d %H:%M:%S".
        stroke_color (str, optional): The stroke color of the GPS trace points. Defaults to "lightgray".
        circle_size (int, optional): The size of the GPS trace points. Defaults to 48.
        webGL (bool, optional): Whether to use WebGL (bqplot-gl) for rendering. Defaults to False.
        download (bool, optional): Whether to generate links for downloading the edited GPS traces. Defaults to False.
        sync_plots (bool, optional): Whether to synchronize the zoom and pan of the plots. Defaults to False.
        column_widths (Optional[List[int]], optional): The column widths for the output widget. Defaults to (9, 3).
        add_layer_args (Dict[str, Any], optional): Additional keyword arguments to pass to the add_gps_trace method. Defaults to None.
        arrow_args (Dict[str, Any], optional): Additional keyword arguments to pass to the add_arrow method. Defaults to None.
        map_height (str, optional): The height of the map. Defaults to "600px".
        **kwargs: Additional keyword arguments to pass to the edit_gps_trace method.

    Returns:
        widgets.VBox: The widget containing the GPS trace upload and display interface.
    """

    main_widget = widgets.VBox()
    output = widgets.Output()

    if add_layer_args is None:
        add_layer_args = {}

    if arrow_args is None:
        arrow_args = {}

    uploader = widgets.FileUpload(
        accept=".csv",  # Accept GeoJSON files
        multiple=False,  # Only single file upload
        description="Open GPS Trace",
        layout=widgets.Layout(width="180px"),
        button_style="primary",
    )

    reset = widgets.Button(description="Reset", button_style="primary")

    def on_reset_clicked(b):
        main_widget.children = [widgets.HBox([uploader, reset]), output]

    reset.on_click(on_reset_clicked)

    def create_default_map():
        m = Map(style="liberty", height=map_height)
        m.add_basemap("Satellite")
        m.add_basemap("OpenStreetMap.Mapnik", visible=True)
        m.add_overture_buildings(visible=True)
        return m

    def on_upload(change):
        if len(uploader.value) > 0:
            content = uploader.value[0]["content"]
            filepath = common.temp_file_path(extension=".csv")
            with open(filepath, "wb") as f:
                f.write(content)
            with output:
                output.clear_output()

                if "m" in kwargs:
                    m = kwargs.pop("m")
                else:
                    m = create_default_map()

                if "add_line" not in add_layer_args:
                    add_layer_args["add_line"] = True

                try:
                    m.add_gps_trace(
                        filepath,
                        columns=columns,
                        radius=radius,
                        ann_column=ann_column,
                        colormap=colormap,
                        stroke_color=stroke_color,
                        name=layer_name,
                        **add_layer_args,
                    )
                    m.add_layer_control()

                    m.add_arrow(source=f"{layer_name} Line", **arrow_args)
                    edit_widget = edit_gps_trace(
                        filepath,
                        m,
                        ann_column,
                        colormap,
                        layer_name,
                        default_features,
                        ann_options,
                        rows,
                        fig_width,
                        fig_height,
                        time_format,
                        stroke_color,
                        circle_size,
                        webGL,
                        download,
                        sync_plots,
                        column_widths,
                        **kwargs,
                    )
                except Exception as e:
                    print(f"Error: {e}")
                    edit_widget = widgets.VBox()
                main_widget.children = [
                    widgets.HBox([uploader, reset]),
                    output,
                    edit_widget,
                ]
                uploader.value = ()
                uploader._counter = 0

    uploader.observe(on_upload, names="value")

    main_widget.children = [widgets.HBox([uploader, reset]), output]
    return main_widget


def open_gps_traces(
    filepaths,
    dirname: str = None,
    widget_width: str = "500px",
    columns: List[str] = None,
    ann_column: str = None,
    colormap: Dict[str, str] = None,
    layer_name: str = "GPS Trace",
    default_features: Optional[List[str]] = None,
    ann_options: Optional[List[str]] = None,
    rows: int = 11,
    fig_width: str = "1550px",
    fig_height: str = "300px",
    time_format: str = "%Y%m%dT%H%M%S",
    radius: int = 4,
    stroke_color: str = "lightgray",
    circle_size: int = 48,
    webGL: bool = False,
    download: bool = False,
    sync_plots: bool = False,
    column_widths: Optional[List[int]] = (9, 3),
    add_layer_args: Dict[str, Any] = None,
    arrow_args: Dict[str, Any] = None,
    map_height: str = "600px",
    **kwargs: Any,
) -> widgets.VBox:
    """
    Creates a widget for uploading and displaying multiple GPS traces on a map.

    Args:
        filepaths (List[str]): A list of file paths to the GPS traces.
        dirname (str, optional): The directory name for the GPS traces. Defaults to None.
        widget_width (str, optional): The width of the dropdown file path widget. Defaults to "500px".
        columns (List[str], optional): The columns to display in the GPS trace popup. Defaults to None.
        ann_column (str): The annotation column in the GPS trace.
        colormap (Dict[str, str]): The colormap for the GPS trace annotations.
        layer_name (str): The name of the GPS trace layer.
        default_features (Optional[str], optional): The default features to display.
            The first numerical column will be used if None. Defaults to None.
        ann_options (Optional[List[str]], optional): The annotation options for the dropdown. Defaults to None.
        rows (int, optional): The number of rows to display in the table. Defaults to 11.
        fig_width (str, optional): The width of the figure. Defaults to "1550px".
        fig_height (str, optional): The height of the figure. Defaults to "300px".
        time_format (str, optional): The time format for the timestamp. Defaults to "%Y-%m-%d %H:%M:%S".
        stroke_color (str, optional): The stroke color of the GPS trace points. Defaults to "lightgray".
        circle_size (int, optional): The size of the GPS trace points. Defaults to 48.
        webGL (bool, optional): Whether to use WebGL (bqplot-gl) for rendering. Defaults to False.
        download (bool, optional): Whether to generate links for downloading the edited GPS traces. Defaults to False.
        sync_plots (bool, optional): Whether to synchronize the zoom and pan of the plots. Defaults to False.
        column_widths (Optional[List[int]], optional): The column widths for the output widget. Defaults to (9, 3).
        add_layer_args (Dict[str, Any], optional): Additional keyword arguments to pass to the add_gps_trace method. Defaults to None.
        arrow_args (Dict[str, Any], optional): Additional keyword arguments to pass to the add_arrow method. Defaults to None.
        map_height (str, optional): The height of the map. Defaults to "600px".
        **kwargs: Additional keyword arguments to pass to the edit_gps_trace method.

    Returns:
        widgets.VBox: The widget containing the GPS traces upload and display interface.
    """

    main_widget = widgets.VBox()
    output = widgets.Output()

    if add_layer_args is None:
        add_layer_args = {}

    if arrow_args is None:
        arrow_args = {}

    filepaths = [
        str(filepath) for filepath in filepaths
    ]  # Support pathlib.Path objects
    filepath_widget = widgets.Dropdown(
        value=None,
        options=filepaths,
        description="Select file path:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width),
    )

    def create_default_map():
        m = Map(style="liberty", height=map_height)
        m.add_basemap("Satellite")
        m.add_basemap("OpenStreetMap.Mapnik", visible=True)
        m.add_overture_buildings(visible=True)
        return m

    def on_change(change):
        if change["new"]:
            filepath = change["new"]
            with output:
                if dirname is not None:
                    filepath = os.path.join(dirname, filepath)

                if "m" in kwargs:
                    m = kwargs.pop("m")
                else:
                    m = create_default_map()

                if "add_line" not in add_layer_args:
                    add_layer_args["add_line"] = True

                try:
                    m.add_gps_trace(
                        filepath,
                        columns=columns,
                        radius=radius,
                        ann_column=ann_column,
                        colormap=colormap,
                        stroke_color=stroke_color,
                        name=layer_name,
                        **add_layer_args,
                    )
                    m.add_layer_control()

                    m.add_arrow(source=f"{layer_name} Line", **arrow_args)
                    edit_widget = edit_gps_trace(
                        filepath,
                        m,
                        ann_column,
                        colormap,
                        layer_name,
                        default_features,
                        ann_options,
                        rows,
                        fig_width,
                        fig_height,
                        time_format,
                        stroke_color,
                        circle_size,
                        webGL,
                        download,
                        sync_plots,
                        column_widths,
                        **kwargs,
                    )
                except Exception as e:
                    print(f"Error: {e}")
                    edit_widget = widgets.VBox()

            main_widget.children = [filepath_widget, edit_widget, output]

    filepath_widget.observe(on_change, names="value")

    main_widget.children = [filepath_widget, output]
    filepath_widget.value = filepaths[0]

    return main_widget


def create_vector_data(
    m: Optional[Map] = None,
    properties: Optional[Dict[str, List[Any]]] = None,
    time_format: str = "%Y%m%dT%H%M%S",
    column_widths: Optional[List[int]] = (9, 3),
    map_height: str = "600px",
    out_dir: Optional[str] = None,
    filename_prefix: str = "",
    file_ext: str = "geojson",
    add_mapillary: bool = False,
    style: str = "photo",
    radius: float = 0.00005,
    width: int = 300,
    height: int = 420,
    frame_border: int = 0,
    **kwargs: Any,
) -> widgets.VBox:
    """Generates a widget-based interface for creating and managing vector data on a map.

    This function creates an interactive widget interface that allows users to draw features
    (points, lines, polygons) on a map, assign properties to these features, and export them
    as GeoJSON files. The interface includes a map, a sidebar for property management, and
    buttons for saving, exporting, and resetting the data.

    Args:
        m (Map, optional): An existing Map object. If not provided, a default map with
            basemaps and drawing controls will be created. Defaults to None.
        properties (Dict[str, List[Any]], optional): A dictionary where keys are property names
            and values are lists of possible values for each property. These properties can be
            assigned to the drawn features. Defaults to None.
        time_format (str, optional): The format string for the timestamp used in the exported
            filename. Defaults to "%Y%m%dT%H%M%S".
        column_widths (Optional[List[int]], optional): A list of two integers specifying the
            relative widths of the map and sidebar columns. Defaults to (9, 3).
        map_height (str, optional): The height of the map widget. Defaults to "600px".
        out_dir (str, optional): The directory where the exported GeoJSON files will be saved.
            If not provided, the current working directory is used. Defaults to None.
        filename_prefix (str, optional): A prefix to be added to the exported filename.
            Defaults to "".
        file_ext (str, optional): The file extension for the exported file. Defaults to "geojson".
        add_mapillary (bool, optional): Whether to add a Mapillary image widget that displays the
            nearest image to the clicked point on the map. Defaults to False.
        style (str, optional): The style of the Mapillary image widget. Can be "classic", "photo",
            or "split". Defaults to "photo".
        radius (float, optional): The radius (in degrees) used to search for the nearest Mapillary
            image. Defaults to 0.00005 degrees.
        width (int, optional): The width of the Mapillary image widget. Defaults to 300.
        height (int, optional): The height of the Mapillary image widget. Defaults to 420.
        frame_border (int, optional): The width of the frame border for the Mapillary image widget.
            Defaults to 0.
        **kwargs (Any): Additional keyword arguments that may be passed to the function.

    Returns:
        widgets.VBox: A vertical box widget containing the map, sidebar, and control buttons.

    Example:
        >>> properties = {
        ...     "Type": ["Residential", "Commercial", "Industrial"],
        ...     "Area": [100, 200, 300],
        ... }
        >>> widget = create_vector_data(properties=properties)
        >>> display(widget)  # Display the widget in a Jupyter notebook
    """
    from datetime import datetime

    main_widget = widgets.VBox()
    output = widgets.Output()

    if out_dir is None:
        out_dir = os.getcwd()

    def create_default_map():
        m = Map(style="liberty", height=map_height)
        m.add_basemap("Satellite")
        m.add_basemap("OpenStreetMap.Mapnik", visible=True)
        m.add_overture_buildings(visible=True)
        m.add_overture_data(theme="transportation")
        m.add_layer_control()
        m.add_draw_control(
            controls=["point", "polygon", "line_string", "trash"], position="top-right"
        )
        return m

    if m is None:
        m = create_default_map()

    setattr(m, "draw_features", {})

    sidebar_widget = widgets.VBox()

    prop_widgets = widgets.VBox()

    image_widget = widgets.HTML()

    if isinstance(properties, dict):
        for key, values in properties.items():

            if isinstance(values, list) or isinstance(values, tuple):
                prop_widget = widgets.Dropdown(
                    options=values,
                    # value=None,
                    description=key,
                )
                prop_widgets.children += (prop_widget,)
            elif isinstance(values, int):
                prop_widget = widgets.IntText(
                    value=values,
                    description=key,
                )
                prop_widgets.children += (prop_widget,)
            elif isinstance(values, float):
                prop_widget = widgets.FloatText(
                    value=values,
                    description=key,
                )
                prop_widgets.children += (prop_widget,)
            else:
                prop_widget = widgets.Text(
                    value=values,
                    description=key,
                )
                prop_widgets.children += (prop_widget,)

    def draw_change(lng_lat):
        if lng_lat.new:
            if len(m.draw_features_selected) > 0:
                feature_id = m.draw_features_selected[0]["id"]
                if feature_id not in m.draw_features:
                    m.draw_features[feature_id] = {}
                    for key, values in properties.items():
                        if isinstance(values, list) or isinstance(values, tuple):
                            m.draw_features[feature_id][key] = values[0]
                        else:
                            m.draw_features[feature_id][key] = values
                else:
                    for prop_widget in prop_widgets.children:
                        key = prop_widget.description
                        prop_widget.value = m.draw_features[feature_id][key]

        else:
            for prop_widget in prop_widgets.children:
                key = prop_widget.description
                if isinstance(properties[key], list) or isinstance(
                    properties[key], tuple
                ):
                    prop_widget.value = properties[key][0]
                else:
                    prop_widget.value = properties[key]

    m.observe(draw_change, names="draw_features_selected")

    def log_lng_lat(lng_lat):
        lon = lng_lat.new["lng"]
        lat = lng_lat.new["lat"]
        image_id = common.search_mapillary_images(lon, lat, radius=radius, limit=1)
        if len(image_id) > 0:
            content = f"""
            <iframe
                src="https://www.mapillary.com/embed?image_key={image_id[0]}&style={style}"
                height="{height}"
                width="{width}"
                frameborder="{frame_border}">
            </iframe>
            """
            image_widget.value = content
        else:
            image_widget.value = "No Mapillary image found."

    if add_mapillary:
        m.observe(log_lng_lat, names="clicked")

    button_layout = widgets.Layout(width="97px")
    save = widgets.Button(
        description="Save", button_style="primary", layout=button_layout
    )
    export = widgets.Button(
        description="Export", button_style="primary", layout=button_layout
    )
    reset = widgets.Button(
        description="Reset", button_style="primary", layout=button_layout
    )

    def on_save_click(b):

        output.clear_output()
        if len(m.draw_features_selected) > 0:
            feature_id = m.draw_features_selected[0]["id"]
            for prop_widget in prop_widgets.children:
                key = prop_widget.description
                m.draw_features[feature_id][key] = prop_widget.value
        else:
            with output:
                output.clear_output()
                print("Please select a feature to save.")

    save.on_click(on_save_click)

    def on_export_click(b):
        current_time = datetime.now().strftime(time_format)
        filename = os.path.join(out_dir, f"{filename_prefix}{current_time}.{file_ext}")

        for index, feature in enumerate(m.draw_feature_collection_all["features"]):
            feature_id = feature["id"]
            if feature_id in m.draw_features:
                m.draw_feature_collection_all["features"][index]["properties"] = (
                    m.draw_features[feature_id]
                )

        gdf = gpd.GeoDataFrame.from_features(
            m.draw_feature_collection_all, crs="EPSG:4326"
        )
        gdf.to_file(filename)
        with output:

            print(f"Exported: {filename}")

    export.on_click(on_export_click)

    def on_reset_click(b):
        output.clear_output()
        for prop_widget in prop_widgets.children:
            description = prop_widget.description
            if description in properties:
                if isinstance(properties[description], list) or isinstance(
                    properties[description], tuple
                ):
                    prop_widget.value = properties[description][0]
                else:
                    prop_widget.value = properties[description]

    reset.on_click(on_reset_click)

    sidebar_widget.children = [
        prop_widgets,
        widgets.HBox([save, export, reset]),
        output,
        image_widget,
    ]

    left_col_layout = v.Col(
        cols=column_widths[0],
        children=[m],
        class_="pa-1",  # padding for consistent spacing
    )
    right_col_layout = v.Col(
        cols=column_widths[1],
        children=[sidebar_widget],
        class_="pa-1",  # padding for consistent spacing
    )
    row1 = v.Row(
        class_="d-flex flex-wrap",
        children=[left_col_layout, right_col_layout],
    )
    main_widget = v.Col(children=[row1])
    return main_widget


class MapWidget(v.Row):

    def __init__(self, left_obj, right_obj, column_widths=(5, 1), **kwargs):

        self.left_obj = left_obj
        self.right_obj = right_obj

        left_col_layout = v.Col(
            cols=column_widths[0],
            children=[left_obj],
            class_="pa-1",  # padding for consistent spacing
        )
        right_col_layout = v.Col(
            cols=column_widths[1],
            children=[right_obj],
            class_="pa-1",  # padding for consistent spacing
        )

        # if "class_" not in kwargs:
        #     kwargs["class_"] = "d-flex flex-wrap"

        super().__init__(children=[left_col_layout, right_col_layout], **kwargs)
