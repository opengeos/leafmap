"""Main module."""

import os
import ipyleaflet
import ipywidgets

from box import Box
from IPython.display import display
from .basemaps import xyz_to_leaflet
from .common import *
from .legends import builtin_legends
from .osm import *
from .pc import *
from . import examples
from .plot import *
from . import map_widgets
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type


basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(ipyleaflet.Map):
    """The Map class inherits ipyleaflet.Map. The arguments you can pass to the Map can be found at https://ipyleaflet.readthedocs.io/en/latest/api_reference/map.html. By default, the Map will add OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    @property
    def _layer_editor(self) -> Optional[map_widgets.LayerEditor]:
        return self._find_widget_of_type(map_widgets.LayerEditor)

    def __init__(self, **kwargs):
        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 2

        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 24

        if "scroll_wheel_zoom" not in kwargs:
            kwargs["scroll_wheel_zoom"] = True

        if "basemap" in kwargs:
            if isinstance(kwargs["basemap"], str):
                kwargs["basemap"] = get_basemap(kwargs["basemap"])

        super().__init__(**kwargs)
        self.baseclass = "ipyleaflet"
        self.toolbar = None
        self.toolbar_button = None
        self.tool_output = None
        self.tool_output_ctrl = None
        self.layer_control = None
        self.draw_control = None
        self.search_control = None
        self.user_roi = None
        self.user_rois = None
        self.draw_features = []
        self.api_keys = {}
        self.geojson_layers = []
        self.edit_mode = False
        self.edit_props = []
        self._layer_manager_widget = widgets.VBox()

        # sandbox path for Voila app to restrict access to system directories.
        if "sandbox_path" not in kwargs:
            if os.environ.get("USE_VOILA") is not None:
                self.sandbox_path = os.getcwd()
            else:
                self.sandbox_path = None
        else:
            if os.path.exists(os.path.abspath(kwargs["sandbox_path"])):
                self.sandbox_path = kwargs["sandbox_path"]
            else:
                print("The sandbox path is invalid.")
                self.sandbox_path = None

        if "height" not in kwargs:
            self.layout.height = "600px"
        else:
            if isinstance(kwargs["height"], int):
                kwargs["height"] = str(kwargs["height"]) + "px"
            self.layout.height = kwargs["height"]
        if "width" in kwargs:
            if isinstance(kwargs["width"], int):
                kwargs["width"] = str(kwargs["width"]) + "px"
            self.layout.width = kwargs["width"]

        if "layers_control" not in kwargs:
            kwargs["layers_control"] = False
        if kwargs["layers_control"]:
            self.add(ipyleaflet.LayersControl(position="topright"))

        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True
        if kwargs["fullscreen_control"]:
            self.add(ipyleaflet.FullScreenControl())

        if "search_control" not in kwargs:
            kwargs["search_control"] = False
        if kwargs["search_control"]:
            url = "https://nominatim.openstreetmap.org/search?format=json&q={s}"
            search_control = ipyleaflet.SearchControl(
                position="topleft",
                url=url,
                zoom=12,
                marker=None,
            )
            self.add(search_control)
            self.search_control = search_control

        if "draw_control" not in kwargs:
            kwargs["draw_control"] = True

        if "repeat_mode" not in kwargs:
            repeat_mode = False
        else:
            repeat_mode = kwargs["repeat_mode"]
            kwargs.pop("repeat_mode")

        if kwargs["draw_control"]:
            draw_control = ipyleaflet.DrawControl(
                polyline={"repeatMode": repeat_mode},
                polygon={"repeatMode": repeat_mode},
                marker={
                    "shapeOptions": {"color": "#3388ff"},
                    "repeatMode": repeat_mode,
                },
                rectangle={
                    "shapeOptions": {"color": "#3388ff"},
                    "repeatMode": repeat_mode,
                },
                circle={
                    "shapeOptions": {"color": "#3388ff"},
                    "repeatMode": repeat_mode,
                },
                # circlemarker={"repeatMode": repeat_mode},
                edit=True,
                remove=True,
                position="topleft",
            )
            draw_control.circlemarker = {}
            self.add(draw_control)
            self.draw_control = draw_control

            def handle_draw(target, action, geo_json):
                if "style" in geo_json["properties"]:
                    del geo_json["properties"]["style"]
                self.user_roi = geo_json

                if action in ["created", "edited"]:
                    # feature = {
                    #     "type": "Feature",
                    #     "geometry": geo_json["geometry"],
                    # }
                    self.draw_features.append(geo_json)

                elif action == "deleted":
                    geometries = [
                        feature["geometry"] for feature in self.draw_control.data
                    ]
                    for geom in geometries:
                        if geom == geo_json["geometry"]:
                            geometries.remove(geom)
                    for feature in self.draw_features:
                        if feature["geometry"] not in geometries:
                            self.draw_features.remove(feature)

                if self.edit_mode:
                    import ipysheet

                    with self.edit_output:
                        self.edit_output.outputs = ()
                        self.edit_sheet = ipysheet.from_dataframe(
                            self.get_draw_props(n=self.num_attributes, return_df=True)
                        )
                        display(self.edit_sheet)

                self.user_rois = {
                    "type": "FeatureCollection",
                    "features": self.draw_features,
                }

            draw_control.on_draw(handle_draw)

        if "measure_control" not in kwargs:
            kwargs["measure_control"] = False
        if kwargs["measure_control"]:
            self.add(ipyleaflet.MeasureControl(position="topleft"))

        if "scale_control" not in kwargs:
            kwargs["scale_control"] = True
        if kwargs["scale_control"]:
            self.add(ipyleaflet.ScaleControl(position="bottomleft"))

        self.layers[0].name = "OpenStreetMap"

        if "toolbar_control" not in kwargs:
            kwargs["toolbar_control"] = True
        if kwargs["toolbar_control"]:
            from .toolbar import main_toolbar

            main_toolbar(self)

        if "use_voila" not in kwargs:
            kwargs["use_voila"] = False

        if "catalog_source" in kwargs:
            self.set_catalog_source(kwargs["catalog_source"])

    def add(self, obj, index=None, **kwargs) -> None:
        """Adds a layer to the map.

        Args:
            layer (object): The layer to add to the map.
            index (int, optional): The index at which to add the layer. Defaults to None.
        """
        if isinstance(obj, str):
            if obj in basemaps.keys():
                obj = get_basemap(obj)
            else:
                if obj == "nasa_earth_data":
                    from .toolbar import nasa_data_gui

                    nasa_data_gui(self, **kwargs)
                elif obj == "inspector":
                    from .toolbar import inspector_gui

                    inspector_gui(self, **kwargs)

                elif obj == "stac":
                    self.add_stac_gui(**kwargs)
                elif obj == "basemap":
                    self.add_basemap_gui(**kwargs)
                elif obj == "inspector":
                    self.add_inspector_gui(**kwargs)
                elif obj == "layer_manager":
                    self.add_layer_manager(**kwargs)
                elif obj == "oam":
                    self.add_oam_gui(**kwargs)
                return

        super().add(obj, index=index)

        if hasattr(self, "_layer_manager_widget"):
            self.update_layer_manager()

    def set_center(self, lon, lat, zoom=None) -> None:
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

    def zoom_to_bounds(self, bounds) -> None:
        """Zooms to a bounding box in the form of [minx, miny, maxx, maxy].

        Args:
            bounds (list | tuple): A list/tuple containing minx, miny, maxx, maxy values for the bounds.
        """
        #  The ipyleaflet fit_bounds method takes lat/lon bounds in the form [[south, west], [north, east]].
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def zoom_to_gdf(self, gdf):
        """Zooms to the bounding box of a GeoPandas GeoDataFrame.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        """
        bounds = gdf.total_bounds
        self.zoom_to_bounds(bounds)

    def get_scale(self) -> float:
        """Returns the approximate pixel scale of the current map view, in meters.

        Returns:
            float: Map resolution in meters.
        """
        import math

        zoom_level = self.zoom
        # Reference: https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
        resolution = 156543.04 * math.cos(0) / math.pow(2, zoom_level)
        return resolution

    def get_layer_names(self) -> list:
        """Gets layer names as a list.

        Returns:
            list: A list of layer names.
        """
        layer_names = []

        for layer in list(self.layers):
            if len(layer.name) > 0:
                layer_names.append(layer.name)

        return layer_names

    def add_marker(self, location, **kwargs) -> None:
        """Adds a marker to the map. More info about marker at https://ipyleaflet.readthedocs.io/en/latest/api_reference/marker.html.

        Args:
            location (list | tuple): The location of the marker in the format of [lat, lng].

            **kwargs: Keyword arguments for the marker.
        """
        if isinstance(location, list):
            location = tuple(location)
        if isinstance(location, tuple):
            marker = ipyleaflet.Marker(location=location, **kwargs)
            self.add(marker)
        else:
            raise TypeError("The location must be a list or a tuple.")

    def add_basemap(self, basemap="HYBRID", show=True, **kwargs) -> None:
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'HYBRID'.
            visible (bool, optional): Whether the basemap is visible or not. Defaults to True.
            **kwargs: Keyword arguments for the TileLayer.
        """
        import xyzservices

        try:
            layer_names = self.get_layer_names()

            map_dict = {
                "ROADMAP": "Google Maps",
                "SATELLITE": "Google Satellite",
                "TERRAIN": "Google Terrain",
                "HYBRID": "Google Hybrid",
            }

            if isinstance(basemap, str):
                if basemap.upper() in map_dict:
                    layer = get_google_map(basemap.upper(), **kwargs)
                    layer.visible = show
                    self.add(layer)
                    return

            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                attribution = basemap.attribution
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 22
                layer = ipyleaflet.TileLayer(
                    url=url,
                    name=name,
                    max_zoom=max_zoom,
                    attribution=attribution,
                    visible=show,
                    **kwargs,
                )
                self.add(layer)
                arc_add_layer(url, name)
            elif basemap in basemaps and basemaps[basemap].name not in layer_names:
                self.add(basemap)
                self.layers[-1].visible = show
                for param in kwargs:
                    setattr(self.layers[-1], param, kwargs[param])
                arc_add_layer(basemaps[basemap].url, basemap)
            elif basemap in basemaps and basemaps[basemap].name in layer_names:
                print(f"{basemap} has been already added before.")
            else:
                print(
                    "Basemap can only be one of the following:\n  {}".format(
                        "\n  ".join(basemaps.keys())
                    )
                )

        except Exception as e:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )

    def find_layer(self, name):
        """Finds layer by name

        Args:
            name (str): Name of the layer to find.

        Returns:
            object: ipyleaflet layer object.
        """
        layers = self.layers

        for layer in layers:
            if layer.name == name:
                return layer
        return None

    def find_layer_index(self, name) -> int:
        """Finds layer index by name

        Args:
            name (str): Name of the layer to find.

        Returns:
            int: Index of the layer with the specified name
        """
        layers = self.layers

        for index, layer in enumerate(layers):
            if layer.name == name:
                return index

        return -1

    def add_layer(self, layer) -> None:
        """Adds a layer to the map.

        Args:
            layer (ipyleaflet layer): The layer to be added.
        """
        existing_layer = self.find_layer(layer.name)
        if existing_layer is not None:
            self.remove_layer(existing_layer)
        super().add(layer)

    def add_ee_layer(
        self,
        asset_id: str,
        name: str = None,
        attribution: str = "Google Earth Engine",
        shown: bool = True,
        opacity: float = 1.0,
        **kwargs,
    ) -> None:
        """
        Adds a Google Earth Engine tile layer to the map based on the tile layer URL from
            https://github.com/opengeos/ee-tile-layers/blob/main/datasets.tsv.

        Args:
            asset_id (str): The ID of the Earth Engine asset.
            name (str, optional): The name of the tile layer. If not provided, the asset ID will be used. Default is None.
            attribution (str, optional): The attribution text to be displayed. Default is "Google Earth Engine".
            shown (bool, optional): Whether the tile layer should be shown on the map. Default is True.
            opacity (float, optional): The opacity of the tile layer. Default is 1.0.
            **kwargs: Additional keyword arguments to be passed to the underlying `add_tile_layer` method.

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
                shown=shown,
                opacity=opacity,
                **kwargs,
            )
        else:
            print(f"The provided EE tile layer {asset_id} does not exist.")

    def add_layer_control(self, position="topright") -> None:
        """Adds a layer control to the map.

        Args:
            position (str, optional): The position of the layer control. Defaults to 'topright'.
        """

        self.add(ipyleaflet.LayersControl(position=position))

    def layer_opacity(self, name, value=1.0) -> None:
        """Changes layer opacity.

        Args:
            name (str): The name of the layer to change opacity.
            value (float, optional): The opacity value to set. Defaults to 1.0.
        """
        layer = self.find_layer(name)
        try:
            layer.opacity = value
        except Exception as e:
            raise Exception(e)

    def add_wms_layer(
        self,
        url,
        layers,
        name=None,
        attribution="",
        format="image/png",
        transparent=True,
        opacity=1.0,
        shown=True,
        **kwargs,
    ) -> None:
        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/png'.
            transparent (bool, optional): If True, the WMS service will return images with transparency. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """

        if name is None:
            name = str(layers)

        try:
            wms_layer = ipyleaflet.WMSLayer(
                url=url,
                layers=layers,
                name=name,
                attribution=attribution,
                format=format,
                transparent=transparent,
                opacity=opacity,
                visible=shown,
                **kwargs,
            )
            self.add(wms_layer)

        except Exception as e:
            print("Failed to add the specified WMS TileLayer.")
            raise Exception(e)

    def add_tile_layer(
        self,
        url,
        name,
        attribution,
        opacity=1.0,
        shown=True,
        layer_index=None,
        **kwargs,
    ) -> None:
        """Adds a TileLayer to the map.

        Args:
            url (str): The URL of the tile layer.
            name (str): The layer name to use for the layer.
            attribution (str): The attribution to use.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            layer_index (int, optional): The index at which to add the layer. Defaults to None.
        """
        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 30
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 30
        try:
            tile_layer = ipyleaflet.TileLayer(
                url=url,
                name=name,
                attribution=attribution,
                opacity=opacity,
                visible=shown,
                **kwargs,
            )
            self.add(tile_layer, index=layer_index)

            arc_add_layer(url, name, shown, opacity)

        except Exception as e:
            print("Failed to add the specified TileLayer.")
            raise Exception(e)

    def add_vector_tile(
        self,
        url,
        styles: Optional[dict] = {},
        layer_name: Optional[str] = "Vector Tile",
        **kwargs,
    ) -> None:
        """Adds a VectorTileLayer to the map. It wraps the ipyleaflet.VectorTileLayer class. See
            https://ipyleaflet.readthedocs.io/en/latest/layers/vector_tile.html

        Args:
            url (str, optional): The URL of the tile layer
            styles (dict,optional): Style dict, specific to the vector tile source.
            layer_name (str, optional): The layer name to use for the layer. Defaults to 'Vector Tile'.
            kwargs: Additional keyword arguments to pass to the ipyleaflet.VectorTileLayer class.
        """
        if "vector_tile_layer_styles" in kwargs:
            styles = kwargs["vector_tile_layer_styles"]
            del kwargs["vector_tile_layer_styles"]
        try:
            vector_tile_layer = ipyleaflet.VectorTileLayer(
                url=url,
                vector_tile_layer_styles=styles,
                **kwargs,
            )
            vector_tile_layer.name = layer_name
            self.add(vector_tile_layer)

        except Exception as e:
            print("Failed to add the specified VectorTileLayer.")
            raise Exception(e)

    add_vector_tile_layer = add_vector_tile

    def add_pmtiles(
        self,
        url,
        style=None,
        name="PMTiles",
        show=True,
        zoom_to_layer=True,
        **kwargs,
    ) -> None:
        """
        Adds a PMTiles layer to the map. This function is not officially supported yet by ipyleaflet yet.
        Install it with the following command:
        pip install git+https://github.com/giswqs/ipyleaflet.git@pmtiles

        Args:
            url (str): The URL of the PMTiles file.
            style (str, optional): The CSS style to apply to the layer. Defaults to None.
                See https://docs.mapbox.com/style-spec/reference/layers/ for more info.
            name (str, optional): The name of the layer. Defaults to None.
            show (bool, optional): Whether the layer should be shown initially. Defaults to True.
            zoom_to_layer (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the PMTilesLayer constructor.

        Returns:
            None
        """

        try:
            if "sources" in kwargs:
                del kwargs["sources"]

            if "version" in kwargs:
                del kwargs["version"]

            if style is None:
                style = pmtiles_style(url)

            layer = ipyleaflet.PMTilesLayer(
                url=url,
                style=style,
                name=name,
                visible=show,
                **kwargs,
            )
            self.add(layer)

            if zoom_to_layer:
                metadata = pmtiles_metadata(url)
                bounds = metadata["bounds"]
                self.zoom_to_bounds(bounds)
        except Exception as e:
            print(e)

    def add_osm_from_geocode(
        self,
        query,
        which_result=None,
        by_osmid=False,
        buffer_dist=None,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM data of place(s) by name or ID to the map.

        Args:
            query (str | dict | list): Query string(s) or structured dict(s) to geocode.
            which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
            by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
            buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """

        gdf = osm_gdf_from_geocode(
            query, which_result=which_result, by_osmid=by_osmid, buffer_dist=buffer_dist
        )
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_address(
        self,
        address,
        tags,
        dist=1000,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM entities within some distance N, S, E, W of address to the map.

        Args:
            address (str): The address to geocode and use as the central point around which to get the geometries.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            dist (int, optional): Distance in meters. Defaults to 1000.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_address(address, tags, dist)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_place(
        self,
        query,
        tags,
        which_result=None,
        buffer_dist=None,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM entities within boundaries of geocodable place(s) to the map.

        Args:
            query (str | dict | list): Query string(s) or structured dict(s) to geocode.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
            buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_place(query, tags, which_result, buffer_dist)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_point(
        self,
        center_point,
        tags,
        dist=1000,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM entities within some distance N, S, E, W of a point to the map.

        Args:
            center_point (tuple): The (lat, lng) center point around which to get the geometries.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            dist (int, optional): Distance in meters. Defaults to 1000.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_point(center_point, tags, dist)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_polygon(
        self,
        polygon,
        tags,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM entities within boundaries of a (multi)polygon to the map.

        Args:
            polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic boundaries to fetch geometries within
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_polygon(polygon, tags)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_bbox(
        self,
        north,
        south,
        east,
        west,
        tags,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM entities within a N, S, E, W bounding box to the map.


        Args:
            north (float): Northern latitude of bounding box.
            south (float): Southern latitude of bounding box.
            east (float): Eastern longitude of bounding box.
            west (float): Western longitude of bounding box.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_bbox(north, south, east, west, tags)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_view(
        self,
        tags,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
    ) -> None:
        """Adds OSM entities within the current map view to the map.

        Args:
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        bounds = self.bounds
        if len(bounds) == 0:
            bounds = (
                (40.74824858675827, -73.98933637940563),
                (40.75068694343106, -73.98364473187601),
            )
        north, south, east, west = (
            bounds[1][0],
            bounds[0][0],
            bounds[1][1],
            bounds[0][1],
        )

        gdf = osm_gdf_from_bbox(north, south, east, west, tags)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_cog_layer(
        self,
        url,
        name="Untitled",
        attribution="",
        opacity=1.0,
        shown=True,
        bands=None,
        titiler_endpoint=None,
        zoom_to_layer=True,
        layer_index=None,
        **kwargs,
    ) -> None:
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
            layer_index (int, optional): The index at which to add the layer. Defaults to None.
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
        """
        band_names = cog_bands(url, titiler_endpoint)

        if bands is not None:
            if not isinstance(bands, list):
                bands = [bands]

            if all(isinstance(x, str) for x in bands):
                kwargs["bidx"] = [band_names.index(x) + 1 for x in bands]

            elif all(isinstance(x, int) for x in bands):
                kwargs["bidx"] = bands
            else:
                raise ValueError("Bands must be a list of integers or strings.")
        elif "bidx" not in kwargs:
            if len(band_names) == 1:
                kwargs["bidx"] = [1]
            else:
                kwargs["bidx"] = [1, 2, 3]

        vis_bands = [band_names[idx - 1] for idx in kwargs["bidx"]]

        if len(kwargs["bidx"]) > 1:
            if "colormap_name" in kwargs:
                kwargs.pop("colormap_name")
            if "colormap" in kwargs:
                kwargs.pop("colormap")

        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown, layer_index)
        if zoom_to_layer:
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        vmin, vmax = cog_tile_vmin_vmax(
            url, bands=bands, titiler_endpoint=titiler_endpoint
        )

        if "colormap_name" in kwargs:
            colormap = kwargs["colormap_name"]
        else:
            colormap = None

        if "nodata" in kwargs:
            nodata = kwargs["nodata"]
        else:
            nodata = None

        params = {
            "url": url,
            "titiler_endpoint": titiler_endpoint,
            "tile_layer": self.find_layer(name),
            "bounds": bounds,
            "indexes": kwargs["bidx"],
            "vis_bands": vis_bands,
            "band_names": band_names,
            "vmin": vmin,
            "vmax": vmax,
            "nodata": nodata,
            "colormap": colormap,
            "opacity": opacity,
            "layer_name": name,
            "type": "COG",
        }
        self.cog_layer_dict[name] = params

    def add_cog_mosaic(self, **kwargs) -> None:
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/opengeos/leafmap/issues/180."
        )

    def add_cog_mosaic_from_file(self, **kwargs) -> None:
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/opengeos/leafmap/issues/180."
        )

    def add_stac_layer(
        self,
        url=None,
        collection=None,
        item=None,
        assets=None,
        bands=None,
        titiler_endpoint=None,
        name="STAC Layer",
        attribution="",
        opacity=1.0,
        shown=True,
        fit_bounds=True,
        layer_index=None,
        **kwargs,
    ) -> None:
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
            collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "https://planetarycomputer.microsoft.com/api/data/v1", "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            fit_bounds (bool, optional): A flag indicating whether the map should be zoomed to the layer extent. Defaults to True.
            layer_index (int, optional): The index at which to add the layer. Defaults to None.
        """
        if "colormap_name" in kwargs and kwargs["colormap_name"] is None:
            kwargs.pop("colormap_name")

        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown, layer_index)
        if fit_bounds:
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        if assets is None and bands is not None:
            assets = bands

        if isinstance(assets, str) and "," in assets:
            assets = assets.split(",")

        if "rescale" in kwargs:
            rescale = kwargs["rescale"]
            vmin, vmax = [float(v) for v in rescale.split(",")]
        else:
            vmin, vmax = stac_min_max(url, collection, item, assets, titiler_endpoint)

        if "nodata" in kwargs:
            nodata = kwargs["nodata"]
        else:
            nodata = None

        band_names = stac_bands(url, collection, item, titiler_endpoint)
        if assets is not None:
            indexes = [band_names.index(band) + 1 for band in assets]
        else:
            indexes = None

        params = {
            "url": url,
            "titiler_endpoint": titiler_endpoint,
            "collection": collection,
            "item": item,
            "assets": assets,
            "tile_layer": self.find_layer(name),
            "indexes": indexes,
            "vis_bands": assets,
            "band_names": band_names,
            "bounds": bounds,
            "vmin": vmin,
            "vmax": vmax,
            "nodata": nodata,
            "opacity": opacity,
            "layer_name": name,
            "type": "STAC",
        }

        self.cog_layer_dict[name] = params

    def add_mosaic_layer(
        self,
        url=None,
        titiler_endpoint=None,
        name="Mosaic Layer",
        attribution="",
        opacity=1.0,
        shown=True,
        **kwargs,
    ) -> None:
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a MosaicJSON.
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'Mosaic Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        tile_url = mosaic_tile(url, titiler_endpoint, **kwargs)

        bounds = mosaic_bounds(url, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_minimap(self, zoom=5, position="bottomright"):
        """Adds a minimap (overview) to the ipyleaflet map.

        Args:
            zoom (int, optional): Initial map zoom level. Defaults to 5.
            position (str, optional): Position of the minimap. Defaults to "bottomright".
        """
        layers = [get_basemap("Esri.WorldImagery")]
        minimap = ipyleaflet.Map(
            zoom_control=False,
            attribution_control=False,
            zoom=zoom,
            center=self.center,
            layers=layers,
        )
        minimap.layout.width = "150px"
        minimap.layout.height = "150px"
        ipyleaflet.link((minimap, "center"), (self, "center"))
        minimap_control = ipyleaflet.WidgetControl(widget=minimap, position=position)
        self.add(minimap_control)

    def marker_cluster(self, event="click", add_marker=True):
        """Captures user inputs and add markers to the map.

        Args:
            event (str, optional): [description]. Defaults to 'click'.
            add_marker (bool, optional): If True, add markers to the map. Defaults to True.

        Returns:
            object: a marker cluster.
        """
        coordinates = []
        markers = []
        marker_cluster = ipyleaflet.MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        if add_marker:
            self.add(marker_cluster)

        def handle_interaction(**kwargs):
            latlon = kwargs.get("coordinates")

            if event == "click" and kwargs.get("type") == "click":
                coordinates.append(latlon)
                self.last_click = latlon
                self.all_clicks = coordinates
                if add_marker:
                    markers.append(ipyleaflet.Marker(location=latlon))
                    marker_cluster.markers = markers
            elif kwargs.get("type") == "mousemove":
                pass

        # cursor style: https://www.w3schools.com/cssref/pr_class_cursor.asp
        self.default_style = {"cursor": "crosshair"}
        self.on_interaction(handle_interaction)

    def add_circle_markers_from_xy(
        self,
        data,
        x="lon",
        y="lat",
        radius=10,
        popup=None,
        font_size=2,
        stroke=True,
        color="#0033FF",
        weight=2,
        fill=True,
        fill_color=None,
        fill_opacity=0.2,
        opacity=1.0,
        layer_name="Circle Markers",
        **kwargs,
    ) -> None:
        """Adds a marker cluster to the map. For a list of options, see https://ipyleaflet.readthedocs.io/en/latest/_modules/ipyleaflet/leaflet.html#Path

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "lon".
            y (str, optional): The column name for the y values. Defaults to "lat".
            radius (int, optional): The radius of the circle. Defaults to 10.
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            font_size (int, optional): The font size of the popup. Defaults to 2.
            stroke (bool, optional): Whether to stroke the path. Defaults to True.
            color (str, optional): The color of the path. Defaults to "#0033FF".
            weight (int, optional): The weight of the path. Defaults to 2.
            fill (bool, optional): Whether to fill the path with color. Defaults to True.
            fill_color (str, optional): The fill color of the path. Defaults to None.
            fill_opacity (float, optional): The fill opacity of the path. Defaults to 0.2.
            opacity (float, optional): The opacity of the path. Defaults to 1.0.
            layer_name (str, optional): The layer name to use for the marker cluster. Defaults to "Circle Markers".

        """
        import pandas as pd
        import geopandas as gpd

        if isinstance(data, pd.DataFrame) or isinstance(data, gpd.GeoDataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        elif isinstance(data, str) and data.endswith(".csv"):
            df = pd.read_csv(data)
        else:
            df = gpd.read_file(data)

        col_names = df.columns.values.tolist()
        if "geometry" in col_names:
            col_names.remove("geometry")

        if popup is None:
            popup = col_names

        if not isinstance(popup, list):
            popup = [popup]

        if x not in col_names:
            if isinstance(df, gpd.GeoDataFrame):
                df[x] = df.geometry.x
            else:
                raise ValueError(
                    f"x must be one of the following: {', '.join(col_names)}"
                )

        if y not in col_names:
            if isinstance(df, gpd.GeoDataFrame):
                df[y] = df.geometry.y
            else:
                raise ValueError(
                    f"y must be one of the following: {', '.join(col_names)}"
                )

        if fill_color is None:
            fill_color = color

        if isinstance(color, str):
            colors = [color] * len(df)
        elif isinstance(color, list):
            colors = color
        else:
            raise ValueError("color must be either a string or a list.")

        if isinstance(fill_color, str):
            fill_colors = [fill_color] * len(df)
        elif isinstance(fill_color, list):
            fill_colors = fill_color
        else:
            raise ValueError("fill_color must be either a string or a list.")

        if isinstance(radius, int):
            radius = [radius] * len(df)
        elif isinstance(radius, list):
            radius = radius
        else:
            raise ValueError("radius must be either an integer or a list.")

        index = 0

        layers = []
        for idx, row in df.iterrows():
            html = ""
            for p in popup:
                html = (
                    html
                    + f"<font size='{font_size}'><b>"
                    + p
                    + "</b>"
                    + ": "
                    + str(row[p])
                    + "<br></font>"
                )
            popup_html = widgets.HTML(html)

            marker = ipyleaflet.CircleMarker(
                location=[row[y], row[x]],
                radius=radius[index],
                popup=popup_html,
                stroke=stroke,
                color=colors[index],
                weight=weight,
                fill=fill,
                fill_color=fill_colors[index],
                fill_opacity=fill_opacity,
                opacity=opacity,
                **kwargs,
            )
            layers.append(marker)
            index += 1

        group = ipyleaflet.LayerGroup(layers=tuple(layers), name=layer_name)
        self.add(group)

    def add_markers(
        self,
        markers: Union[List[List[Union[int, float]]], List[Union[int, float]]],
        x: str = "lon",
        y: str = "lat",
        radius: int = 10,
        popup: Optional[str] = None,
        font_size: int = 2,
        stroke: bool = True,
        color: str = "#0033FF",
        weight: int = 2,
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.2,
        opacity: float = 1.0,
        shape: str = "circle",
        layer_name: str = "Markers",
        **kwargs,
    ) -> None:
        """
        Adds markers to the map.

        Args:
            markers (Union[List[List[Union[int, float]]], List[Union[int, float]]]): List of markers.
                Each marker can be defined as a list of [x, y] coordinates or as a single [x, y] coordinate.
            x (str, optional): Name of the x-coordinate column in the marker data. Defaults to "lon".
            y (str, optional): Name of the y-coordinate column in the marker data. Defaults to "lat".
            radius (int, optional): Radius of the markers. Defaults to 10.
            popup (str, optional): Popup text for the markers. Defaults to None.
            font_size (int, optional): Font size of the popup text. Defaults to 2.
            stroke (bool, optional): Whether to display marker stroke. Defaults to True.
            color (str, optional): Color of the marker stroke. Defaults to "#0033FF".
            weight (int, optional): Weight of the marker stroke. Defaults to 2.
            fill (bool, optional): Whether to fill markers. Defaults to True.
            fill_color (str, optional): Fill color of the markers. Defaults to None.
            fill_opacity (float, optional): Opacity of the marker fill. Defaults to 0.2.
            opacity (float, optional): Opacity of the markers. Defaults to 1.0.
            shape (str, optional): Shape of the markers. Options are "circle" or "marker". Defaults to "circle".
            layer_name (str, optional): Name of the marker layer. Defaults to "Markers".
            **kwargs: Additional keyword arguments to pass to the marker plotting function.

        Returns:
            None: This function does not return any value.
        """
        import geopandas as gpd

        if (
            isinstance(markers, list)
            and len(markers) == 2
            and isinstance(markers[0], (int, float))
            and isinstance(markers[1], (int, float))
        ):
            markers = [markers]

        if isinstance(markers, list) and all(
            isinstance(item, list) and len(item) == 2 for item in markers
        ):
            df = pd.DataFrame(markers, columns=[y, x])
            markers = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y]))

        if shape == "circle":
            self.add_circle_markers_from_xy(
                markers,
                x,
                y,
                radius,
                popup,
                font_size,
                stroke,
                color,
                weight,
                fill,
                fill_color,
                fill_opacity,
                opacity,
                layer_name,
                **kwargs,
            )

        elif shape == "marker":
            self.add_gdf(markers, **kwargs)

    def split_map(
        self,
        left_layer: Optional[str] = "TERRAIN",
        right_layer: Optional[str] = "OpenTopoMap",
        left_args: Optional[dict] = {},
        right_args: Optional[dict] = {},
        left_array_args: Optional[dict] = {},
        right_array_args: Optional[dict] = {},
        zoom_control: Optional[bool] = True,
        fullscreen_control: Optional[bool] = True,
        layer_control: Optional[bool] = True,
        add_close_button: Optional[bool] = False,
        left_label: Optional[str] = None,
        right_label: Optional[str] = None,
        left_position: Optional[str] = "bottomleft",
        right_position: Optional[str] = "bottomright",
        widget_layout: Optional[dict] = None,
        draggable: Optional[bool] = True,
    ) -> None:
        """Adds split map.

        Args:
            left_layer (str, optional): The left tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'TERRAIN'.
            right_layer (str, optional): The right tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'OpenTopoMap'.
            left_args (dict, optional): The arguments for the left tile layer. Defaults to {}.
            right_args (dict, optional): The arguments for the right tile layer. Defaults to {}.
            left_array_args (dict, optional): The arguments for array_to_image for the left layer. Defaults to {}.
            right_array_args (dict, optional): The arguments for array_to_image for the right layer. Defaults to {}.
            zoom_control (bool, optional): Whether to add zoom control. Defaults to True.
            fullscreen_control (bool, optional): Whether to add fullscreen control. Defaults to True.
            layer_control (bool, optional): Whether to add layer control. Defaults to True.
            add_close_button (bool, optional): Whether to add a close button. Defaults to False.
            left_label (str, optional): The label for the left layer. Defaults to None.
            right_label (str, optional): The label for the right layer. Defaults to None.
            left_position (str, optional): The position for the left label. Defaults to "bottomleft".
            right_position (str, optional): The position for the right label. Defaults to "bottomright".
            widget_layout (dict, optional): The layout for the widget. Defaults to None.
            draggable (bool, optional): Whether the split map is draggable. Defaults to True.
        """
        if "max_zoom" not in left_args:
            left_args["max_zoom"] = 30
        if "max_native_zoom" not in left_args:
            left_args["max_native_zoom"] = 30

        if "max_zoom" not in right_args:
            right_args["max_zoom"] = 30
        if "max_native_zoom" not in right_args:
            right_args["max_native_zoom"] = 30

        if "layer_name" not in left_args:
            left_args["layer_name"] = "Left Layer"

        if "layer_name" not in right_args:
            right_args["layer_name"] = "Right Layer"

        bounds = None

        try:
            controls = self.controls
            layers = self.layers
            self.clear_controls()

            if zoom_control:
                self.add(ipyleaflet.ZoomControl())
            if fullscreen_control:
                self.add(ipyleaflet.FullScreenControl())

            if left_label is not None:
                left_name = left_label
            else:
                left_name = "Left Layer"

            if right_label is not None:
                right_name = right_label
            else:
                right_name = "Right Layer"

            if isinstance(left_layer, str):
                if left_layer in basemaps.keys():
                    left_layer = get_basemap(left_layer)
                elif left_layer.startswith("http") and left_layer.endswith(".tif"):
                    url = cog_tile(left_layer, **left_args)
                    bbox = cog_bounds(left_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    left_layer = ipyleaflet.TileLayer(
                        url=url,
                        name=left_name,
                        attribution=" ",
                        **left_args,
                    )
                elif left_layer.startswith("http") and left_layer.endswith(".json"):
                    left_tile_url = stac_tile(left_layer, **left_args)
                    bbox = stac_bounds(left_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    left_layer = ipyleaflet.TileLayer(
                        url=left_tile_url,
                        name=left_name,
                        attribution=" ",
                        **left_args,
                    )
                elif left_layer.startswith("http") and left_layer.endswith(".geojson"):
                    if "max_zoom" in left_args:
                        del left_args["max_zoom"]
                    if "max_native_zoom" in left_args:
                        del left_args["max_native_zoom"]
                    left_layer = geojson_layer(left_layer, **left_args)
                elif os.path.exists(left_layer):
                    if left_layer.endswith(".geojson"):
                        if "max_zoom" in left_args:
                            del left_args["max_zoom"]
                        if "max_native_zoom" in left_args:
                            del left_args["max_native_zoom"]
                        left_layer = geojson_layer(left_layer, **left_args)
                    else:
                        left_layer, left_client = get_local_tile_layer(
                            left_layer,
                            tile_format="ipyleaflet",
                            return_client=True,
                            **left_args,
                        )
                        bounds = image_bounds(left_client)
                else:
                    left_layer = ipyleaflet.TileLayer(
                        url=left_layer,
                        name=left_name,
                        attribution=" ",
                        **left_args,
                    )
            elif isinstance(left_layer, ipyleaflet.TileLayer) or isinstance(
                left_layer, ipyleaflet.GeoJSON
            ):
                pass
            elif is_array(left_layer):
                left_layer = array_to_image(left_layer, **left_array_args)
                left_layer, _ = get_local_tile_layer(
                    left_layer,
                    return_client=True,
                    **left_args,
                )
            else:
                raise ValueError(
                    f"left_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            if isinstance(right_layer, str):
                if right_layer in basemaps.keys():
                    right_layer = get_basemap(right_layer)
                elif right_layer.startswith("http") and right_layer.endswith(".tif"):
                    url = cog_tile(
                        right_layer,
                        **right_args,
                    )
                    bbox = cog_bounds(right_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    right_layer = ipyleaflet.TileLayer(
                        url=url,
                        name=right_name,
                        attribution=" ",
                        **right_args,
                    )

                elif right_layer.startswith("http") and right_layer.endswith(".json"):
                    right_tile_url = stac_tile(right_layer, **left_args)
                    bbox = stac_bounds(right_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    right_layer = ipyleaflet.TileLayer(
                        url=right_tile_url,
                        name=right_name,
                        attribution=" ",
                        **right_args,
                    )
                elif right_layer.startswith("http") and right_layer.endswith(
                    ".geojson"
                ):
                    if "max_zoom" in right_args:
                        del right_args["max_zoom"]
                    if "max_native_zoom" in right_args:
                        del right_args["max_native_zoom"]
                    right_layer = geojson_layer(right_layer, **right_args)
                elif os.path.exists(right_layer):
                    if "max_zoom" in right_args:
                        del right_args["max_zoom"]
                    if "max_native_zoom" in right_args:
                        del right_args["max_native_zoom"]
                    if right_layer.endswith(".geojson"):
                        right_layer = geojson_layer(right_layer, **right_args)
                    else:
                        right_layer, right_client = get_local_tile_layer(
                            right_layer,
                            tile_format="ipyleaflet",
                            return_client=True,
                            **right_args,
                        )
                        bounds = image_bounds(right_client)
                else:
                    right_layer = ipyleaflet.TileLayer(
                        url=right_layer,
                        name=right_name,
                        attribution=" ",
                        **right_args,
                    )
            elif isinstance(right_layer, ipyleaflet.TileLayer) or isinstance(
                right_layer, ipyleaflet.GeoJSON
            ):
                pass
            elif is_array(right_layer):
                right_layer = array_to_image(right_layer, **right_array_args)
                right_layer, _ = get_local_tile_layer(
                    right_layer,
                    return_client=True,
                    **right_args,
                )
            else:
                raise ValueError(
                    f"right_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )
            control = ipyleaflet.SplitMapControl(
                left_layer=left_layer, right_layer=right_layer
            )
            self.add(control)

            if left_label is not None:
                if widget_layout is None:
                    widget_layout = widgets.Layout(padding="0px 4px 0px 4px")
                left_widget = widgets.HTML(value=left_label, layout=widget_layout)

                left_control = ipyleaflet.WidgetControl(
                    widget=left_widget, position=left_position
                )
                self.add(left_control)

            if right_label is not None:
                if widget_layout is None:
                    widget_layout = widgets.Layout(padding="0px 4px 0px 4px")
                right_widget = widgets.HTML(value=right_label, layout=widget_layout)
                right_control = ipyleaflet.WidgetControl(
                    widget=right_widget, position=right_position
                )
                self.add(right_control)

            if bounds is not None:
                self.fit_bounds(bounds)

            self.dragging = draggable

            close_button = widgets.ToggleButton(
                value=False,
                tooltip="Close split-panel map",
                icon="times",
                layout=widgets.Layout(
                    height="28px", width="28px", padding="0px 0px 0px 4px"
                ),
            )

            def close_btn_click(change):
                if change["new"]:
                    self.controls = controls
                    self.layers = layers[:-1]
                    self.add(layers[-1])

                if left_label in self.controls:
                    self.remove_control(left_control)

                if right_label in self.controls:
                    self.remove_control(right_control)

                self.dragging = True

            close_button.observe(close_btn_click, "value")
            close_control = ipyleaflet.WidgetControl(
                widget=close_button, position="topright"
            )

            if add_close_button:
                self.add(close_control)

            if layer_control:
                self.add_layer_control()

        except Exception as e:
            print("The provided layers are invalid!")
            raise ValueError(e)

    def basemap_demo(self) -> None:
        """A demo for using leafmap basemaps."""
        dropdown = widgets.Dropdown(
            options=list(basemaps.keys()),
            value="Esri.WorldImagery",
            description="Basemaps",
        )

        def on_click(change):
            basemap_name = change["new"]
            old_basemap = self.layers[-1]
            self.substitute_layer(old_basemap, get_basemap(basemap_name))

        dropdown.observe(on_click, "value")
        basemap_control = ipyleaflet.WidgetControl(widget=dropdown, position="topright")
        self.add(basemap_control)

    def add_legend(
        self,
        title: Optional[str] = "Legend",
        legend_dict: Optional[dict] = None,
        labels: Optional[list] = None,
        colors: Optional[list] = None,
        position: Optional[str] = "bottomright",
        builtin_legend: Optional[str] = None,
        layer_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Adds a customized basemap to the map.

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'.
            legend_dict (dict, optional): A dictionary containing legend items as keys and color as values. If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            labels (list, optional): A list of legend keys. Defaults to None.
            colors (list, optional): A list of legend colors. Defaults to None.
            position (str, optional): Position of the legend. Defaults to 'bottomright'.
            builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.
            layer_name (str, optional): Layer name of the legend to be associated with. Defaults to None.

        """
        import pkg_resources
        from IPython.display import display

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("leafmap", "leafmap.py")
        )
        legend_template = os.path.join(pkg_dir, "data/template/legend.html")

        if "min_width" not in kwargs.keys():
            min_width = None
        if "max_width" not in kwargs.keys():
            max_width = None
        else:
            max_width = kwargs["max_width"]
        if "min_height" not in kwargs.keys():
            min_height = None
        else:
            min_height = kwargs["min_height"]
        if "max_height" not in kwargs.keys():
            max_height = None
        else:
            max_height = kwargs["max_height"]
        if "height" not in kwargs.keys():
            height = None
        else:
            height = kwargs["height"]
        if "width" not in kwargs.keys():
            width = None
        else:
            width = kwargs["width"]

        if width is None:
            max_width = "300px"
        if height is None:
            max_height = "400px"

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
                    colors = [rgb_to_hex(x) for x in colors]
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
                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        print(e)

        allowed_positions = [
            "topleft",
            "topright",
            "bottomleft",
            "bottomright",
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
            if not color.startswith("#"):
                color = "#" + color
            item = "      <li><span style='background:{};'></span>{}</li>\n".format(
                color, key
            )
            content.append(item)

        legend_html = header + content + footer
        legend_text = "".join(legend_html)

        try:
            legend_output_widget = widgets.Output(
                layout={
                    # "border": "1px solid black",
                    "max_width": max_width,
                    "min_width": min_width,
                    "max_height": max_height,
                    "min_height": min_height,
                    "height": height,
                    "width": width,
                    "overflow": "scroll",
                }
            )
            legend_control = ipyleaflet.WidgetControl(
                widget=legend_output_widget, position=position
            )
            legend_widget = widgets.HTML(value=legend_text)
            with legend_output_widget:
                display(legend_widget)

            self.legend_widget = legend_output_widget
            self.legend_control = legend_control
            self.add(legend_control)

        except Exception as e:
            raise Exception(e)

    def add_colorbar(
        self,
        colors: Union[list[int], tuple[int]],
        vmin: Optional[int] = 0,
        vmax: Optional[float] = 1.0,
        index: Optional[list] = None,
        caption: Optional[str] = "",
        categorical: Optional[bool] = False,
        step: Optional[int] = None,
        height: Optional[str] = "45px",
        transparent_bg: Optional[bool] = False,
        position: Optional[str] = "bottomright",
        **kwargs,
    ) -> None:
        """Add a branca colorbar to the map.

        Args:
            colors (list): The set of colors to be used for interpolation. Colors can be provided in the form: * tuples of RGBA ints between 0 and 255 (e.g: (255, 255, 0) or (255, 255, 0, 255)) * tuples of RGBA floats between 0. and 1. (e.g: (1.,1.,0.) or (1., 1., 0., 1.)) * HTML-like string (e.g: “#ffff00) * a color name or shortcut (e.g: “y” or “yellow”)
            vmin (int, optional): The minimal value for the colormap. Values lower than vmin will be bound directly to colors[0].. Defaults to 0.
            vmax (float, optional): The maximal value for the colormap. Values higher than vmax will be bound directly to colors[-1]. Defaults to 1.0.
            index (list, optional):The values corresponding to each color. It has to be sorted, and have the same length as colors. If None, a regular grid between vmin and vmax is created.. Defaults to None.
            caption (str, optional): The caption for the colormap. Defaults to "".
            categorical (bool, optional): Whether or not to create a categorical colormap. Defaults to False.
            step (int, optional): The step to split the LinearColormap into a StepColormap. Defaults to None.
            height (str, optional): The height of the colormap widget. Defaults to "45px".
            transparent_bg (bool, optional): Whether to use transparent background for the colormap widget. Defaults to True.
            position (str, optional): The position for the colormap widget. Defaults to "bottomright".

        """
        from box import Box
        from branca.colormap import LinearColormap

        output = widgets.Output()
        output.layout.height = height

        if "width" in kwargs.keys():
            output.layout.width = kwargs["width"]

        if isinstance(colors, Box):
            try:
                colors = list(colors["default"])
            except Exception as e:
                print("The provided color list is invalid.")
                raise Exception(e)

        if all(len(color) == 6 for color in colors):
            colors = ["#" + color for color in colors]

        colormap = LinearColormap(
            colors=colors, index=index, vmin=vmin, vmax=vmax, caption=caption
        )

        if categorical:
            if step is not None:
                colormap = colormap.to_step(step)
            elif index is not None:
                colormap = colormap.to_step(len(index) - 1)
            else:
                colormap = colormap.to_step(3)

        colormap_ctrl = ipyleaflet.WidgetControl(
            widget=output,
            position=position,
            transparent_bg=transparent_bg,
            **kwargs,
        )
        with output:
            output.outputs = ()
            display(colormap)

        self.colorbar = colormap_ctrl
        self.add(colormap_ctrl)

    def add_colormap(
        self,
        cmap: Optional[str] = "gray",
        colors: Optional[list] = None,
        discrete: Optional[bool] = False,
        label: Optional[str] = None,
        width: Optional[float] = 3,
        height: Optional[float] = 0.25,
        orientation: Optional[str] = "horizontal",
        vmin: Optional[float] = 0,
        vmax: Optional[float] = 1.0,
        axis_off: Optional[bool] = False,
        show_name: Optional[bool] = False,
        font_size: Optional[int] = 8,
        transparent_bg: Optional[bool] = False,
        position: Optional[str] = "bottomright",
        **kwargs,
    ) -> None:
        """Adds a matplotlib colormap to the map.

        Args:
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
            colors (list, optional): A list of custom colors to create a colormap. Defaults to None.
            discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            width (float, optional): The width of the colormap. Defaults to 8.0.
            height (float, optional): The height of the colormap. Defaults to 0.4.
            orientation (str, optional): The orientation of the colormap. Defaults to "horizontal".
            vmin (float, optional): The minimum value range. Defaults to 0.
            vmax (float, optional): The maximum value range. Defaults to 1.0.
            axis_off (bool, optional): Whether to turn axis off. Defaults to False.
            show_name (bool, optional): Whether to show the colormap name. Defaults to False.
            font_size (int, optional): Font size of the text. Defaults to 12.
            transparent_bg (bool, optional): Whether to use transparent background for the colormap widget. Defaults to True.
            position (str, optional): The position for the colormap widget. Defaults to "bottomright".
        """
        from .colormaps import plot_colormap

        output = widgets.Output()

        colormap_ctrl = ipyleaflet.WidgetControl(
            widget=output,
            position=position,
            transparent_bg=transparent_bg,
        )
        with output:
            output.outputs = ()
            plot_colormap(
                cmap,
                colors,
                discrete,
                label,
                width,
                height,
                orientation,
                vmin,
                vmax,
                axis_off,
                show_name,
                font_size,
                **kwargs,
            )

        self.colorbar = colormap_ctrl
        self.add(colormap_ctrl)

    def image_overlay(self, url: str, bounds: str, name: str) -> None:
        """Overlays an image from the Internet or locally on the map.

        Args:
            url (str): http URL or local file path to the image.
            bounds (tuple): bounding box of the image in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            name (str): name of the layer to show on the layer control.
        """
        from base64 import b64encode
        from PIL import Image, ImageSequence
        from io import BytesIO

        try:
            if not url.startswith("http"):
                if not os.path.exists(url):
                    print("The provided file does not exist.")
                    return

                ext = os.path.splitext(url)[1][1:]  # file extension
                image = Image.open(url)

                f = BytesIO()
                if ext.lower() == "gif":
                    frames = []
                    # Loop over each frame in the animated image
                    for frame in ImageSequence.Iterator(image):
                        frame = frame.convert("RGBA")
                        b = BytesIO()
                        frame.save(b, format="gif")
                        frame = Image.open(b)
                        frames.append(frame)
                    frames[0].save(
                        f,
                        format="GIF",
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                    )
                else:
                    image.save(f, ext)

                data = b64encode(f.getvalue())
                data = data.decode("ascii")
                url = "data:image/{};base64,".format(ext) + data
            img = ipyleaflet.ImageOverlay(url=url, bounds=bounds, name=name)
            self.add(img)
        except Exception as e:
            raise Exception(e)

    def video_overlay(
        self, url: str, bounds: Tuple, layer_name: str = None, **kwargs
    ) -> None:
        """Overlays a video from the Internet on the map.

        Args:
            url (str): http URL of the video, such as "https://www.mapbox.com/bites/00188/patricia_nasa.webm"
            bounds (tuple): bounding box of the video in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            layer_name (str): name of the layer to show on the layer control.
        """
        if layer_name is None and "name" in kwargs:
            layer_name = kwargs.pop("name")
        try:
            video = ipyleaflet.VideoOverlay(url=url, bounds=bounds, name=layer_name)
            self.add(video)
        except Exception as e:
            raise Exception(e)

    def to_html(
        self,
        outfile: Optional[str] = None,
        title: Optional[str] = "My Map",
        width: Optional[str] = "100%",
        height: Optional[str] = "880px",
        add_layer_control: Optional[bool] = True,
        **kwargs,
    ) -> None:
        """Saves the map as an HTML file.

        Args:
            outfile (str, optional): The output file path to the HTML file.
            title (str, optional): The title of the HTML file. Defaults to 'My Map'.
            width (str, optional): The width of the map in pixels or percentage. Defaults to '100%'.
            height (str, optional): The height of the map in pixels. Defaults to '880px'.
            add_layer_control (bool, optional): Whether to add the LayersControl. Defaults to True.

        """
        try:
            save = True
            if outfile is not None:
                if not outfile.endswith(".html"):
                    raise ValueError("The output file extension must be html.")
                outfile = os.path.abspath(outfile)
                out_dir = os.path.dirname(outfile)
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
            else:
                outfile = os.path.abspath(random_string() + ".html")
                save = False

            if add_layer_control and self.layer_control is None:
                layer_control = ipyleaflet.LayersControl(position="topright")
                self.layer_control = layer_control
                self.add(layer_control)

            before_width = self.layout.width
            before_height = self.layout.height

            if not isinstance(width, str):
                print("width must be a string.")
                return
            elif width.endswith("px") or width.endswith("%"):
                pass
            else:
                print("width must end with px or %")
                return

            if not isinstance(height, str):
                print("height must be a string.")
                return
            elif not height.endswith("px"):
                print("height must end with px")
                return

            self.layout.width = width
            self.layout.height = height

            self.save(outfile, title=title, **kwargs)

            self.layout.width = before_width
            self.layout.height = before_height

            if not save:
                out_html = ""
                with open(outfile) as f:
                    lines = f.readlines()
                    out_html = "".join(lines)
                os.remove(outfile)
                return out_html

        except Exception as e:
            raise Exception(e)

    def to_image(
        self, outfile: Optional[str] = None, monitor: Optional[int] = 1
    ) -> None:
        """Saves the map as a PNG or JPG image.

        Args:
            outfile (str, optional): The output file path to the image. Defaults to None.
            monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
        """
        if outfile is None:
            outfile = os.path.join(os.getcwd(), "my_map.png")

        if outfile.endswith(".png") or outfile.endswith(".jpg"):
            pass
        else:
            print("The output file must be a PNG or JPG image.")
            return

        work_dir = os.path.dirname(outfile)
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

        screenshot = screen_capture(outfile, monitor)
        self.screenshot = screenshot

    def to_streamlit(
        self,
        width: Optional[int] = None,
        height: Optional[int] = 600,
        scrolling: Optional[bool] = False,
        **kwargs,
    ):
        """Renders map figure in a Streamlit app.

        Args:
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to 600.
            responsive (bool, optional): Whether to make the map responsive. Defaults to True.
            scrolling (bool, optional): If True, show a scrollbar when the content is larger than the iframe. Otherwise, do not show a scrollbar. Defaults to False.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit.components.v1 as components  # pylint: disable=E0401

            # if responsive:
            #     make_map_responsive = """
            #     <style>
            #     [title~="st.iframe"] { width: 100%}
            #     </style>
            #     """
            #     st.markdown(make_map_responsive, unsafe_allow_html=True)
            return components.html(
                self.to_html(), width=width, height=height, scrolling=scrolling
            )

        except Exception as e:
            raise Exception(e)

    def toolbar_reset(self) -> None:
        """Reset the toolbar so that no tool is selected."""
        toolbar_grid = self.toolbar
        for tool in toolbar_grid.children:
            tool.value = False

    def add_raster(
        self,
        source: str,
        indexes: Optional[int] = None,
        colormap: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = "Raster",
        layer_index: Optional[int] = None,
        zoom_to_layer: Optional[bool] = True,
        visible: Optional[bool] = True,
        opacity: Optional[float] = 1.0,
        array_args: Optional[Dict] = {},
        client_args: Optional[Dict] = {"cors_all": False},
        **kwargs,
    ) -> None:
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try installing jupyter-server-proxy using `pip install jupyter-server-proxy`,
            then running the following code before calling this function. For more info, see https://bit.ly/3JbmF93.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
            indexes (int, optional): The band(s) to use. Band indexing starts at 1. Defaults to None.
            colormap (str, optional): The name of the colormap from `matplotlib` to use when plotting a single band. See https://matplotlib.org/stable/gallery/color/colormap_reference.html. Default is greyscale.
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Raster'.
            layer_index (int, optional): The index of the layer. Defaults to None.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to True.
            visible (bool, optional): Whether the layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            array_args (dict, optional): Additional arguments to pass to `array_to_memory_file` when reading the raster. Defaults to {}.
            client_args (dict, optional): Additional arguments to pass to localtileserver.TileClient. Defaults to { "cors_all": False }.
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
            layer_name=layer_name,
            client_args=client_args,
            return_client=True,
            **kwargs,
        )
        tile_layer.visible = visible

        self.add(tile_layer, index=layer_index)
        if zoom_to_layer:
            self.center = tile_client.center()
            try:
                self.zoom = tile_client.default_zoom
            except AttributeError:
                self.zoom = 15

        arc_add_layer(tile_layer.url, layer_name, True, 1.0)

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        if indexes is None:
            if len(tile_client.band_names) == 1:
                indexes = [1]
            else:
                indexes = [1, 2, 3]

        vis_bands = [tile_client.band_names[i - 1] for i in indexes]

        params = {
            "tile_layer": tile_layer,
            "tile_client": tile_client,
            "indexes": indexes,
            "vis_bands": vis_bands,
            "band_names": tile_client.band_names,
            "vmin": vmin,
            "vmax": vmax,
            "nodata": nodata,
            "colormap": colormap,
            "opacity": opacity,
            "layer_name": layer_name,
            "filename": tile_client.filename,
            "type": "LOCAL",
        }
        self.cog_layer_dict[layer_name] = params

    add_local_tile = add_raster

    def add_remote_tile(
        self,
        source: str,
        band: Optional[int] = None,
        palette: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Add a remote Cloud Optimized GeoTIFF (COG) to the map.

        Args:
            source (str): The path to the remote Cloud Optimized GeoTIFF.
            band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to None.
        """
        if isinstance(source, str) and source.startswith("http"):
            self.add_raster(
                source,
                band=band,
                palette=palette,
                vmin=vmin,
                vmax=vmax,
                nodata=nodata,
                attribution=attribution,
                layer_name=layer_name,
                **kwargs,
            )
        else:
            raise Exception("The source must be a URL.")

    def add_netcdf(
        self,
        filename: str,
        variables: Optional[int] = None,
        palette: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = "NetCDF layer",
        shift_lon: Optional[bool] = True,
        lat: Optional[str] = "lat",
        lon: Optional[str] = "lon",
        lev: Optional[str] = "lev",
        level_index: Optional[int] = 0,
        time: Optional[int] = 0,
        **kwargs,
    ) -> None:
        """Generate an ipyleaflet/folium TileLayer from a netCDF file.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer),
            try adding to following two lines to the beginning of the notebook if the raster does not render properly.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f'{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}'

        Args:
            filename (str): File path or HTTP URL to the netCDF file.
            variables (int, optional): The variable/band names to extract data from the netCDF file. Defaults to None. If None, all variables will be extracted.
            port (str, optional): The port to use for the server. Defaults to "default".
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to "netCDF layer".
            shift_lon (bool, optional): Flag to shift longitude values from [0, 360] to the range [-180, 180]. Defaults to True.
            lat (str, optional): Name of the latitude variable. Defaults to 'lat'.
            lon (str, optional): Name of the longitude variable. Defaults to 'lon'.
            lev (str, optional): Name of the level variable. Defaults to 'lev'.
            level_index (int, optional): Index of level to use. Defaults to 0'.
            time (int, optional): Index of time to use. Defaults to 0'.
        """

        tif, vars = netcdf_to_tif(
            filename,
            shift_lon=shift_lon,
            lat=lat,
            lon=lon,
            lev=lev,
            level_index=level_index,
            time=time,
            return_vars=True,
        )

        if variables is None:
            if len(vars) >= 3:
                band_idx = [1, 2, 3]
            else:
                band_idx = [1]
        else:
            if not set(variables).issubset(set(vars)):
                raise ValueError(f"The variables must be a subset of {vars}.")
            else:
                band_idx = [vars.index(v) + 1 for v in variables]

        self.add_raster(
            tif,
            band=band_idx,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            layer_name=layer_name,
            **kwargs,
        )

    def add_shp(
        self,
        in_shp: str,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable] = None,
        fill_colors: Optional[list[str]] = None,
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = False,
        encoding: Optional[str] = "utf-8",
        **kwargs,
    ) -> None:
        """Adds a shapefile to the map.

        Args:
            in_shp (str): The input file path or HTTP URL (*.zip) to the shapefile.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer after adding it to the map. Defaults to False.
            encoding (str, optional): The encoding of the shapefile. Defaults to "utf-8".

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """

        import geopandas as gpd

        gdf = gpd.read_file(in_shp, encoding=encoding)
        self.add_gdf(
            gdf,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            zoom_to_layer,
            encoding,
            **kwargs,
        )

    def add_geojson(
        self,
        in_geojson: Union[str, Dict],
        layer_name: Optional[str] = "Untitled",
        style: Optional[dict] = {},
        hover_style: Optional[dict] = {},
        style_callback: Optional[Callable] = None,
        fill_colors: Optional[list[str]] = None,
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = False,
        encoding: Optional[str] = "utf-8",
        **kwargs,
    ) -> None:
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str | dict): The file path or http URL to the input
                GeoJSON or a dictionary containing the geojson.
            layer_name (str, optional): The layer name to be used.. Defaults to
                "Untitled".
            style (dict, optional): A dictionary specifying the style to be used.
                Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called
                for each feature, and should return the feature style. This
                styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling
                polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover
                or on_click. Any value other than "on_hover" or "on_click" will
                be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer after
                adding it to the map. Defaults to False.
            encoding (str, optional): The encoding of the GeoJSON file. Defaults
                to "utf-8".

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """
        import json
        import random
        import geopandas as gpd

        gdf = None

        try:
            if isinstance(in_geojson, str):
                if in_geojson.startswith("http"):
                    if is_jupyterlite():
                        import pyodide  # pylint: disable=E0401

                        output = os.path.basename(in_geojson)

                        output = os.path.abspath(output)
                        obj = pyodide.http.open_url(in_geojson)
                        with open(output, "w") as fd:
                            shutil.copyfileobj(obj, fd)
                        with open(output, "r") as fd:
                            data = json.load(fd)
                    else:
                        gdf = gpd.read_file(in_geojson, encoding=encoding)

                else:
                    gdf = gpd.read_file(in_geojson, encoding=encoding)

            elif isinstance(in_geojson, dict):
                gdf = gpd.GeoDataFrame.from_features(in_geojson)
            elif isinstance(in_geojson, gpd.GeoDataFrame):
                gdf = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        if gdf.crs is None:
            print(
                f"Warning: The dataset does not have a CRS defined. Assuming EPSG:4326."
            )
            gdf.crs = "EPSG:4326"
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        data = gdf.__geo_interface__

        try:
            first_feature = data["features"][0]
            if isinstance(first_feature["properties"].get("style"), str):
                # Loop through the features and update the style
                for feature in data["features"]:
                    fstyle = feature["properties"].get("style")
                    if isinstance(fstyle, str):
                        feature["properties"]["style"] = json.loads(fstyle)
        except Exception as e:
            print(e)
            pass

        geom_type = gdf.reset_index().geom_type[0]

        if style is None and (style_callback is None):
            style = {
                # "stroke": True,
                "color": "#3388ff",
                "weight": 2,
                "opacity": 1,
                "fill": True,
                "fillColor": "#3388ff",
                "fillOpacity": 0.2,
                # "dashArray": "9"
                # "clickable": True,
            }

            if geom_type in ["LineString", "MultiLineString"]:
                style["fill"] = False

        elif "weight" not in style:
            style["weight"] = 1

        if not hover_style:
            hover_style = {
                "weight": style["weight"] + 2,
                "fillOpacity": 0,
                "color": "yellow",
            }

        def random_color(feature):
            return {
                "color": "black",
                "fillColor": random.choice(fill_colors),
            }

        toolbar_button = widgets.ToggleButton(
            value=True,
            tooltip="Toolbar",
            icon="info",
            layout=widgets.Layout(
                width="28px", height="28px", padding="0px 0px 0px 4px"
            ),
        )

        close_button = widgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            # button_style="primary",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 4px"
            ),
        )

        html = widgets.HTML()
        html.layout.margin = "0px 10px 0px 10px"
        html.layout.max_height = "250px"
        html.layout.max_width = "250px"

        output_widget = widgets.VBox(
            [widgets.HBox([toolbar_button, close_button]), html]
        )
        info_control = ipyleaflet.WidgetControl(
            widget=output_widget, position="bottomright"
        )

        if info_mode in ["on_hover", "on_click"]:
            self.add(info_control)

        def toolbar_btn_click(change):
            if change["new"]:
                close_button.value = False
                output_widget.children = [
                    widgets.VBox([widgets.HBox([toolbar_button, close_button]), html])
                ]
            else:
                output_widget.children = [widgets.HBox([toolbar_button, close_button])]

        toolbar_button.observe(toolbar_btn_click, "value")

        def close_btn_click(change):
            if change["new"]:
                toolbar_button.value = False
                if info_control in self.controls:
                    self.remove_control(info_control)
                output_widget.close()

        close_button.observe(close_btn_click, "value")

        if "fields" in kwargs:
            fields = kwargs["fields"]
            kwargs.pop("fields")
        else:
            fields = None

        def update_html(feature, fields=fields, **kwargs):
            if fields is None:
                fields = list(feature["properties"].keys())
                if "style" in fields:
                    fields.remove("style")

            value = [
                "<b>{}: </b>{}<br>".format(prop, feature["properties"][prop])
                for prop in fields
            ]

            value = """{}""".format("".join(value))
            html.value = value

        if fill_colors is not None:
            style_callback = random_color

        if style_callback is None:
            geojson = ipyleaflet.GeoJSON(
                data=data,
                style=style,
                hover_style=hover_style,
                name=layer_name,
            )
        else:
            geojson = ipyleaflet.GeoJSON(
                data=data,
                style=style,
                hover_style=hover_style,
                name=layer_name,
                style_callback=style_callback,
            )

        if info_mode == "on_hover":
            geojson.on_hover(update_html)
        elif info_mode == "on_click":
            geojson.on_click(update_html)

        self.add(geojson)
        self.geojson_layers.append(geojson)

        if not hasattr(self, "json_layer_dict"):
            self.json_layer_dict = {}

        params = {
            "data": geojson,
            "style": style,
            "hover_style": hover_style,
            "style_callback": style_callback,
        }
        self.json_layer_dict[layer_name] = params

        if zoom_to_layer:
            try:
                bounds = gdf.total_bounds
                west, south, east, north = bounds
                self.fit_bounds([[south, east], [north, west]])
            except Exception as e:
                print(e)

    def add_search_control(
        self,
        url: str,
        marker: Optional[ipyleaflet.Marker] = None,
        zoom: Optional[int] = None,
        position: Optional[str] = "topleft",
        **kwargs,
    ) -> None:
        """Adds a search control to the map.

        Args:
            url (str): The url to the search API. For example, "https://nominatim.openstreetmap.org/search?format=json&q={s}".
            marker (ipyleaflet.Marker, optional): The marker to be used for the search result. Defaults to None.
            zoom (int, optional): The zoom level to be used for the search result. Defaults to None.
            position (str, optional): The position of the search control. Defaults to "topleft".
            kwargs (dict, optional): Additional keyword arguments to be passed to the search control. See https://ipyleaflet.readthedocs.io/en/latest/api_reference/search_control.html
        """
        if marker is None:
            marker = ipyleaflet.Marker(
                icon=ipyleaflet.AwesomeIcon(
                    name="check", marker_color="green", icon_color="darkred"
                )
            )
        search_control = ipyleaflet.SearchControl(
            position=position,
            url=url,
            zoom=zoom,
            marker=marker,
        )
        self.add(search_control)
        self.search_control = search_control

    def add_gdf(
        self,
        gdf,
        layer_name: Optional[str] = "Untitled",
        style: Optional[dict] = {},
        hover_style: Optional[dict] = {},
        style_callback: Optional[Callable] = None,
        fill_colors: Optional[list[str]] = None,
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = False,
        encoding: Optional[str] = "utf-8",
        **kwargs,
    ) -> None:
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called
                for each feature, and should return the feature style. This
                styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling
                polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover
                or on_click. Any value other than "on_hover" or "on_click" will
                be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer. Defaults to False.
            encoding (str, optional): The encoding of the GeoDataFrame. Defaults to "utf-8".
        """
        for col in gdf.columns:
            try:
                if gdf[col].dtype in ["datetime64[ns]", "datetime64[ns, UTC]"]:
                    gdf[col] = gdf[col].astype(str)
            except:
                pass

        self.add_geojson(
            gdf,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            zoom_to_layer,
            encoding,
            **kwargs,
        )

    def add_gdf_from_postgis(
        self,
        sql: str,
        con,
        layer_name: Optional[str] = "Untitled",
        style: Optional[dict] = {},
        hover_style: Optional[dict] = {},
        style_callback: Optional[Callable] = None,
        fill_colors: Optional[list[str]] = ["black"],
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = True,
        **kwargs,
    ) -> None:
        """Reads a PostGIS database and returns data as a GeoDataFrame to be added to the map.

        Args:
            sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
            con (sqlalchemy.engine.Engine): Active connection to the database to query.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
        """
        gdf = read_postgis(sql, con, **kwargs)
        gdf = gdf.to_crs("epsg:4326")
        self.add_gdf(
            gdf,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            zoom_to_layer,
        )

    def add_kml(
        self,
        in_kml: str,
        layer_name: Optional[str] = "Untitled",
        style: Optional[dict] = {},
        hover_style: Optional[dict] = {},
        style_callback: Optional[Callable] = None,
        fill_colors: Optional[list[str]] = None,
        info_mode: Optional[str] = "on_hover",
        **kwargs,
    ) -> None:
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path or HTTP URL to the KML.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used.
                Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called
                for each feature, and should return the feature style. This
                styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling
                polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover
                or on_click. Any value other than "on_hover" or "on_click" will
                be treated as None. Defaults to "on_hover".

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """

        if in_kml.startswith("http") and in_kml.endswith(".kml"):
            out_dir = os.path.abspath("./cache")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            in_kml = download_file(in_kml)
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The downloaded kml file could not be found.")
        else:
            in_kml = os.path.abspath(in_kml)
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The provided KML could not be found.")

        self.add_vector(
            in_kml,
            layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
            **kwargs,
        )

    def add_vector(
        self,
        filename: str,
        layer_name: Optional[str] = "Untitled",
        bbox: Optional[tuple] = None,
        mask: Optional[dict] = None,
        rows: Optional[tuple[int]] = None,
        style: Optional[dict] = {},
        hover_style: Optional[dict] = {},
        style_callback: Optional[Callable] = None,
        fill_colors: list[str] = None,
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = False,
        encoding: Optional[str] = "utf-8",
        **kwargs,
    ) -> None:
        """Adds any geopandas-supported vector dataset to the map.

        Args:
            filename (str): Either the absolute or relative path to the file or
                URL to be opened, or any object with a read() method (such as
                an open file or StringIO).
            layer_name (str, optional): The layer name to use. Defaults to "Untitled".
            bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional):
                Filter features by given bounding box, GeoSeries, GeoDataFrame or
                a shapely geometry. CRS mis-matches are resolved if given a
                GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
            mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional):
                Filter for features that intersect with the given dict-like geojson
                geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches
                are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox.
                Defaults to None.
            rows (int or slice, optional): Load in specific rows by passing an
                integer (first n rows) or a slice() object.. Defaults to None.
            style (dict, optional): A dictionary specifying the style to be used.
                Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called
                for each feature, and should return the feature style. This
                styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons.
                Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover
                or on_click. Any value other than "on_hover" or "on_click" will
                be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding to use to read the file. Defaults to "utf-8".

        """
        import fiona
        import geopandas as gpd

        if isinstance(filename, str) and filename.endswith(".kml"):
            fiona.drvsupport.supported_drivers["KML"] = "rw"
            kwargs["driver"] = "KML"

        gdf = gpd.read_file(
            filename, bbox=bbox, mask=mask, rows=rows, encoding=encoding, **kwargs
        )

        self.add_gdf(
            gdf,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            zoom_to_layer,
            encoding,
            **kwargs,
        )

    def add_xy_data(
        self,
        in_csv: str,
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        label: Optional[str] = None,
        layer_name: Optional[str] = "Marker cluster",
    ) -> None:
        """Adds points from a CSV file containing lat/lon information and display data on the map.

        Args:
            in_csv (str): The file path to the input CSV file.
            x (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
            y (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
            label (str, optional): The name of the column containing label information to used for marker popup. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to "Marker cluster".

        Raises:
            FileNotFoundError: The specified input csv does not exist.
            ValueError: The specified x column does not exist.
            ValueError: The specified y column does not exist.
            ValueError: The specified label column does not exist.
        """
        import pandas as pd

        if isinstance(in_csv, pd.DataFrame):
            df = in_csv
        elif not in_csv.startswith("http") and (not os.path.exists(in_csv)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(in_csv)

        col_names = df.columns.values.tolist()

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        if label is not None and (label not in col_names):
            raise ValueError(
                f"label must be one of the following: {', '.join(col_names)}"
            )

        self.default_style = {"cursor": "wait"}

        points = list(zip(df[y], df[x]))

        if label is not None:
            labels = df[label]
            markers = [
                ipyleaflet.Marker(
                    location=point,
                    draggable=False,
                    popup=widgets.HTML(str(labels[index])),
                )
                for index, point in enumerate(points)
            ]
        else:
            markers = [
                ipyleaflet.Marker(location=point, draggable=False) for point in points
            ]

        marker_cluster = ipyleaflet.MarkerCluster(markers=markers, name=layer_name)
        self.add(marker_cluster)

        self.default_style = {"cursor": "default"}

    def add_point_layer(
        self,
        filename: str,
        popup: Optional[Union[list, str]] = None,
        layer_name: Optional[str] = "Marker Cluster",
        **kwargs,
    ) -> None:
        """Adds a point layer to the map with a popup attribute.

        Args:
            filename (str): str, http url, path object or file-like object. Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO)
            popup (str | list, optional): Column name(s) to be used for popup. Defaults to None.
            layer_name (str, optional): A layer name to use. Defaults to "Marker Cluster".

        Raises:
            ValueError: If the specified column name does not exist.
            ValueError: If the specified column names do not exist.
        """
        import warnings

        warnings.filterwarnings("ignore")
        check_package(name="geopandas", URL="https://geopandas.org")
        import geopandas as gpd
        import fiona

        self.default_style = {"cursor": "wait"}

        if isinstance(filename, gpd.GeoDataFrame):
            gdf = filename
        else:
            if not filename.startswith("http"):
                filename = os.path.abspath(filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".kml":
                fiona.drvsupport.supported_drivers["KML"] = "rw"
                gdf = gpd.read_file(filename, driver="KML", **kwargs)
            else:
                gdf = gpd.read_file(filename, **kwargs)
        df = gdf.to_crs(epsg="4326")
        col_names = df.columns.values.tolist()
        if popup is not None:
            if isinstance(popup, str) and (popup not in col_names):
                raise ValueError(
                    f"popup must be one of the following: {', '.join(col_names)}"
                )
            elif isinstance(popup, list) and (
                not all(item in col_names for item in popup)
            ):
                raise ValueError(
                    f"All popup items must be select from: {', '.join(col_names)}"
                )

        df["x"] = df.geometry.x
        df["y"] = df.geometry.y

        points = list(zip(df["y"], df["x"]))

        if popup is not None:
            if isinstance(popup, str):
                labels = df[popup]
                markers = [
                    ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(str(labels[index])),
                    )
                    for index, point in enumerate(points)
                ]
            elif isinstance(popup, list):
                labels = []
                for i in range(len(points)):
                    label = ""
                    for item in popup:
                        label = label + str(item) + ": " + str(df[item][i]) + "<br>"
                    labels.append(label)
                df["popup"] = labels

                markers = [
                    ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(labels[index]),
                    )
                    for index, point in enumerate(points)
                ]

        else:
            markers = [
                ipyleaflet.Marker(location=point, draggable=False) for point in points
            ]

        marker_cluster = ipyleaflet.MarkerCluster(markers=markers, name=layer_name)
        self.add(marker_cluster)

        self.default_style = {"cursor": "default"}

    def add_points_from_xy(
        self,
        data: Optional[Union[pd.DataFrame, str]],
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        popup: Optional[list] = None,
        layer_name: Optional[str] = "Marker Cluster",
        color_column: Optional[str] = None,
        marker_colors: Optional[str] = None,
        icon_colors: Optional[list[str]] = ["white"],
        icon_names: Optional[list[str]] = ["info"],
        spin: Optional[bool] = False,
        add_legend: Optional[bool] = True,
        max_cluster_radius: Optional[int] = 80,
        **kwargs,
    ) -> None:
        """Adds a marker cluster to the map.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            layer_name (str, optional): The name of the layer. Defaults to "Marker Cluster".
            color_column (str, optional): The column name for the color values. Defaults to None.
            marker_colors (list, optional): A list of colors to be used for the markers. Defaults to None.
            icon_colors (list, optional): A list of colors to be used for the icons. Defaults to ['white'].
            icon_names (list, optional): A list of names to be used for the icons. More icons can be found at https://fontawesome.com/v4/icons. Defaults to ['info'].
            spin (bool, optional): If True, the icon will spin. Defaults to False.
            add_legend (bool, optional): If True, a legend will be added to the map. Defaults to True.
            max_cluster_radius (int, optional): The maximum cluster radius. Defaults to 80.
            **kwargs: Other keyword arguments to pass to ipyleaflet.MarkerCluster(). For a list of available options,
                see https://github.com/Leaflet/Leaflet.markercluster.

        """
        import pandas as pd

        color_options = [
            "red",
            "blue",
            "green",
            "purple",
            "orange",
            "darkred",
            "lightred",
            "beige",
            "darkblue",
            "darkgreen",
            "cadetblue",
            "darkpurple",
            "white",
            "pink",
            "lightblue",
            "lightgreen",
            "gray",
            "black",
            "lightgray",
        ]

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        elif data.endswith(".csv"):
            df = pd.read_csv(data)
        else:
            import geopandas as gpd

            gdf = gpd.read_file(data)
            df = gdf_to_df(gdf)

        df = points_from_xy(df, x, y)

        col_names = df.columns.values.tolist()

        if color_column is not None and color_column not in col_names:
            raise ValueError(
                f"The color column {color_column} does not exist in the dataframe."
            )

        if color_column is not None:
            items = list(set(df[color_column]))

        else:
            items = None

        if color_column is not None and marker_colors is None:
            if len(items) > len(color_options):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is greater than the number of available colors."
                )
            else:
                marker_colors = color_options[: len(items)]
        elif color_column is not None and marker_colors is not None:
            if len(items) != len(marker_colors):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is not equal to the number of available colors."
                )

        if items is not None:
            if len(icon_colors) == 1:
                icon_colors = icon_colors * len(items)
            elif len(items) != len(icon_colors):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is not equal to the number of available colors."
                )

            if len(icon_names) == 1:
                icon_names = icon_names * len(items)
            elif len(items) != len(icon_names):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is not equal to the number of available colors."
                )

        if "geometry" in col_names:
            col_names.remove("geometry")

        if popup is not None:
            if isinstance(popup, str) and (popup not in col_names):
                raise ValueError(
                    f"popup must be one of the following: {', '.join(col_names)}"
                )
            elif isinstance(popup, list) and (
                not all(item in col_names for item in popup)
            ):
                raise ValueError(
                    f"All popup items must be select from: {', '.join(col_names)}"
                )
        else:
            popup = col_names

        df["x"] = df.geometry.x
        df["y"] = df.geometry.y

        points = list(zip(df["y"], df["x"]))

        if popup is not None:
            if isinstance(popup, str):
                labels = df[popup]

                markers = []
                for index, point in enumerate(points):
                    if items is not None:
                        marker_color = marker_colors[
                            items.index(df[color_column][index])
                        ]
                        icon_name = icon_names[items.index(df[color_column][index])]
                        icon_color = icon_colors[items.index(df[color_column][index])]
                        marker_icon = ipyleaflet.AwesomeIcon(
                            name=icon_name,
                            marker_color=marker_color,
                            icon_color=icon_color,
                            spin=spin,
                        )
                    else:
                        marker_icon = None

                    marker = ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(str(labels[index])),
                        icon=marker_icon,
                    )
                    markers.append(marker)

            elif isinstance(popup, list):
                labels = []
                for i in range(len(points)):
                    label = ""
                    for item in popup:
                        label = (
                            label
                            + "<b>"
                            + str(item)
                            + "</b>"
                            + ": "
                            + str(df[item][i])
                            + "<br>"
                        )
                    labels.append(label)
                df["popup"] = labels

                markers = []
                for index, point in enumerate(points):
                    if items is not None:
                        marker_color = marker_colors[
                            items.index(df[color_column][index])
                        ]
                        icon_name = icon_names[items.index(df[color_column][index])]
                        icon_color = icon_colors[items.index(df[color_column][index])]
                        marker_icon = ipyleaflet.AwesomeIcon(
                            name=icon_name,
                            marker_color=marker_color,
                            icon_color=icon_color,
                            spin=spin,
                        )
                    else:
                        marker_icon = None

                    marker = ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(labels[index]),
                        icon=marker_icon,
                    )
                    markers.append(marker)

        else:
            markers = []
            for point in points:
                if items is not None:
                    marker_color = marker_colors[items.index(df[color_column][index])]
                    icon_name = icon_names[items.index(df[color_column][index])]
                    icon_color = icon_colors[items.index(df[color_column][index])]
                    marker_icon = ipyleaflet.AwesomeIcon(
                        name=icon_name,
                        marker_color=marker_color,
                        icon_color=icon_color,
                        spin=spin,
                    )
                else:
                    marker_icon = None

                marker = ipyleaflet.Marker(
                    location=point, draggable=False, icon=marker_icon
                )
                markers.append(marker)

        marker_cluster = ipyleaflet.MarkerCluster(
            markers=markers,
            name=layer_name,
            max_cluster_radius=max_cluster_radius,
            **kwargs,
        )
        self.add(marker_cluster)

        if items is not None and add_legend:
            marker_colors = [check_color(c) for c in marker_colors]
            self.add_legend(
                title=color_column.title(), colors=marker_colors, labels=items
            )

        self.default_style = {"cursor": "default"}

    add_marker_cluster = add_points_from_xy

    def add_heatmap(
        self,
        data: Union[str, list, pd.DataFrame],
        latitude: Optional[str] = "latitude",
        longitude: Optional[str] = "longitude",
        value: Optional[str] = "value",
        name: Optional[str] = "Heat map",
        radius: Optional[int] = 25,
        **kwargs,
    ) -> None:
        """Adds a heat map to the map. Reference: https://ipyleaflet.readthedocs.io/en/latest/api_reference/heatmap.html

        Args:
            data (str | list | pd.DataFrame): File path or HTTP URL to the input file or a list of data points in the format of [[x1, y1, z1], [x2, y2, z2]]. For example, https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/world_cities.csv
            latitude (str, optional): The column name of latitude. Defaults to "latitude".
            longitude (str, optional): The column name of longitude. Defaults to "longitude".
            value (str, optional): The column name of values. Defaults to "value".
            name (str, optional): Layer name to use. Defaults to "Heat map".
            radius (int, optional): Radius of each “point” of the heatmap. Defaults to 25.

        Raises:
            ValueError: If data is not a list.
        """
        import pandas as pd
        from ipyleaflet import Heatmap

        try:
            if isinstance(data, str):
                df = pd.read_csv(data)
                data = df[[latitude, longitude, value]].values.tolist()
            elif isinstance(data, pd.DataFrame):
                data = data[[latitude, longitude, value]].values.tolist()
            elif isinstance(data, list):
                pass
            else:
                raise ValueError("data must be a list, a DataFrame, or a file path.")

            heatmap = Heatmap(locations=data, radius=radius, name=name, **kwargs)
            self.add(heatmap)

        except Exception as e:
            raise Exception(e)

    def add_labels(
        self,
        data: Union[str, pd.DataFrame],
        column: str,
        font_size: Optional[str] = "12pt",
        font_color: Optional[str] = "black",
        font_family: Optional[str] = "arial",
        font_weight: Optional[str] = "normal",
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        draggable: Optional[bool] = True,
        layer_name: Optional[str] = "Labels",
        **kwargs,
    ):
        """Adds a label layer to the map. Reference: https://ipyleaflet.readthedocs.io/en/latest/api_reference/divicon.html

        Args:
            data (pd.DataFrame | gpd.GeoDataFrame | str): The input data to label.
            column (str): The column name of the data to label.
            font_size (str, optional): The font size of the labels. Defaults to "12pt".
            font_color (str, optional): The font color of the labels. Defaults to "black".
            font_family (str, optional): The font family of the labels. Defaults to "arial".
            font_weight (str, optional): The font weight of the labels, can be normal, bold. Defaults to "normal".
            x (str, optional): The column name of the longitude. Defaults to "longitude".
            y (str, optional): The column name of the latitude. Defaults to "latitude".
            draggable (bool, optional): Whether the labels are draggable. Defaults to True.
            layer_name (str, optional): Layer name to use. Defaults to "Labels".

        """
        import warnings
        import pandas as pd

        warnings.filterwarnings("ignore")

        if isinstance(data, pd.DataFrame):
            df = data
            if "geometry" in data.columns or ("geom" in data.columns):
                df[x] = df.centroid.x
                df[y] = df.centroid.y

        elif isinstance(data, str):
            ext = os.path.splitext(data)[1]
            if ext == ".csv":
                df = pd.read_csv(data)
            elif ext in [".geojson", ".json", ".shp", ".gpkg"]:
                try:
                    import geopandas as gpd

                    df = gpd.read_file(data)
                    df[x] = df.centroid.x
                    df[y] = df.centroid.y
                except Exception as _:
                    print("geopandas is required to read geojson.")
                    return

        else:
            raise ValueError(
                "data must be a pd.DataFrame, gpd.GeoDataFrame, or an ee.FeatureCollection."
            )

        if column not in df.columns:
            raise ValueError(f"column must be one of {', '.join(df.columns)}.")
        if x not in df.columns:
            raise ValueError(f"column must be one of {', '.join(df.columns)}.")
        if y not in df.columns:
            raise ValueError(f"column must be one of {', '.join(df.columns)}.")

        try:
            size = int(font_size.replace("pt", ""))
        except:
            raise ValueError("font_size must be something like '10pt'")

        labels = []
        for index in df.index:
            html = f'<div style="font-size: {font_size};color:{font_color};font-family:{font_family};font-weight: {font_weight}">{df[column][index]}</div>'
            marker = ipyleaflet.Marker(
                location=[df[y][index], df[x][index]],
                icon=ipyleaflet.DivIcon(
                    icon_size=(1, 1),
                    icon_anchor=(size, size),
                    html=html,
                    **kwargs,
                ),
                draggable=draggable,
            )
            labels.append(marker)
        layer_group = ipyleaflet.LayerGroup(layers=labels, name=layer_name)
        self.add(layer_group)
        self.labels = layer_group

    def remove_labels(self):
        """Removes all labels from the map."""
        if hasattr(self, "labels"):
            self.remove_layer(self.labels)
            delattr(self, "labels")

    def add_planet_by_month(
        self,
        year: Optional[int] = 2016,
        month: Optional[int] = 1,
        layer_name: Optional[str] = None,
        api_key: Optional[str] = None,
        token_name: Optional[str] = "PLANET_API_KEY",
        **kwargs,
    ) -> None:
        """Adds a Planet global mosaic by month to the map. To get a Planet API key, see https://developers.planet.com/quickstart/apis

        Args:
            year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
            layer_name (str, optional): The layer name to use. Defaults to None.
            api_key (str, optional): The Planet API key. Defaults to None.
            token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        """
        if layer_name is None and "name" in kwargs:
            layer_name = kwargs.pop("name")
        layer = planet_tile_by_month(year, month, layer_name, api_key, token_name)
        self.add(layer)

    def add_planet_by_quarter(
        self,
        year: Optional[int] = 2016,
        quarter: Optional[int] = 1,
        layer_name: Optional[str] = None,
        api_key: Optional[str] = None,
        token_name: Optional[str] = "PLANET_API_KEY",
        **kwargs,
    ) -> None:
        """Adds a Planet global mosaic by quarter to the map. To get a Planet API key, see https://developers.planet.com/quickstart/apis

        Args:
            year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            quarter (int, optional): The quarter of Planet global mosaic, must be 1-12. Defaults to 1.
            layer_name (str, optional): The layer name to use. Defaults to None.
            api_key (str, optional): The Planet API key. Defaults to None.
            token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        """
        if layer_name is None and "name" in kwargs:
            layer_name = kwargs.pop("name")
        layer = planet_tile_by_quarter(year, quarter, layer_name, api_key, token_name)
        self.add(layer)

    def add_time_slider(
        self,
        layers: dict = {},
        labels: list = None,
        time_interval: int = 1,
        position: str = "bottomright",
        slider_length: str = "150px",
        zoom_to_layer: Optional[bool] = False,
        **kwargs,
    ) -> None:
        """Adds a time slider to the map.

        Args:
            layers (dict, optional): The dictionary containing a set of XYZ tile layers.
            labels (list, optional): The list of labels to be used for the time series. Defaults to None.
            time_interval (int, optional): Time interval in seconds. Defaults to 1.
            position (str, optional): Position to place the time slider, can be any of ['topleft', 'topright', 'bottomleft', 'bottomright']. Defaults to "bottomright".
            slider_length (str, optional): Length of the time slider. Defaults to "150px".
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the selected layer. Defaults to False.

        """
        from .toolbar import time_slider

        time_slider(
            self,
            layers,
            labels,
            time_interval,
            position,
            slider_length,
            zoom_to_layer,
            **kwargs,
        )

    def static_map(
        self,
        width: int = 950,
        height: int = 600,
        out_file: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Display an ipyleaflet static map in a Jupyter Notebook.

        Args
            m (ipyleaflet.Map): An ipyleaflet map.
            width (int, optional): Width of the map. Defaults to 950.
            height (int, optional): Height of the map. Defaults to 600.
            read_only (bool, optional): Whether to hide the side panel to disable map customization. Defaults to False.
            out_file (str, optional): Output html file path. Defaults to None.
        """
        if isinstance(self, ipyleaflet.Map):
            if out_file is None:
                out_file = "./cache/" + "leafmap_" + random_string(3) + ".html"
            out_dir = os.path.abspath(os.path.dirname(out_file))
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            self.to_html(out_file)
            display_html(out_file, width=width, height=height)
        else:
            raise TypeError("The provided map is not an ipyleaflet map.")

    def add_census_data(
        self, wms: str, layer: str, census_dict: Optional[dict] = None, **kwargs
    ) -> None:
        """Adds a census data layer to the map.

        Args:
            wms (str): The wms to use. For example, "Current", "ACS 2021", "Census 2020".  See the complete list at https://tigerweb.geo.census.gov/tigerwebmain/TIGERweb_wms.html
            layer (str): The layer name to add to the map.
            census_dict (dict, optional): A dictionary containing census data. Defaults to None. It can be obtained from the get_census_dict() function.
        """

        try:
            if census_dict is None:
                census_dict = get_census_dict()

            if wms not in census_dict.keys():
                raise ValueError(
                    f"The provided WMS is invalid. It must be one of {census_dict.keys()}"
                )

            layers = census_dict[wms]["layers"]
            if layer not in layers:
                raise ValueError(
                    f"The layer name is not valid. It must be one of {layers}"
                )

            url = census_dict[wms]["url"]
            if "name" not in kwargs:
                kwargs["name"] = layer
            if "attribution" not in kwargs:
                kwargs["attribution"] = "U.S. Census Bureau"
            if "format" not in kwargs:
                kwargs["format"] = "image/png"
            if "transparent" not in kwargs:
                kwargs["transparent"] = True

            self.add_wms_layer(url, layer, **kwargs)

        except Exception as e:
            raise Exception(e)

    def add_xyz_service(self, provider: str, **kwargs) -> None:
        """Add a XYZ tile layer to the map.

        Args:
            provider (str): A tile layer name starts with xyz or qms. For example, xyz.OpenTopoMap,

        Raises:
            ValueError: The provider is not valid. It must start with xyz or qms.
        """
        import xyzservices
        import xyzservices.providers as xyz

        if provider.startswith("xyz"):
            name = provider[4:]
            xyz_provider = xyz.flatten()[name]
            url = xyz_provider.build_url()
            attribution = xyz_provider.attribution
            if attribution.strip() == "":
                attribution = " "
            self.add_tile_layer(url, name, attribution)
        elif provider.startswith("qms"):
            name = provider[4:]
            qms_provider = xyzservices.TileProvider.from_qms(name)
            url = qms_provider.build_url()
            attribution = qms_provider.attribution
            if attribution.strip() == "":
                attribution = " "
            self.add_tile_layer(url, name, attribution)
        else:
            raise ValueError(
                f"The provider {provider} is not valid. It must start with xyz or qms."
            )

    def add_title(
        self,
        title: str,
        align: str = "center",
        font_size: str = "16px",
        style=None,
        **kwargs,
    ) -> None:
        print("The ipyleaflet map does not support titles.")

    def get_pc_collections(self) -> None:
        """Get the list of Microsoft Planetary Computer collections."""
        if not hasattr(self, "pc_collections"):
            setattr(self, "pc_collections", get_pc_collections())

    def save_draw_features(
        self, out_file: str, crs: Optional[str] = "EPSG:4326", **kwargs
    ) -> None:
        """Save the draw features to a file.

        Args:
            out_file (str): The output file path.
            crs (str, optional): The CRS of the output GeoJSON. Defaults to "EPSG:4326".
        """

        if self.user_rois is not None:
            import geopandas as gpd

            out_file = check_file_path(out_file)

            self.update_draw_features()
            geojson = {
                "type": "FeatureCollection",
                "features": self.draw_features,
            }

            gdf = gpd.GeoDataFrame.from_features(geojson, crs="EPSG:4326")
            if crs != "EPSG:4326":
                gdf = gdf.to_crs(crs)
            gdf.to_file(out_file, **kwargs)
        else:
            print("No draw features to save.")

    def update_draw_features(self) -> None:
        """Update the draw features by removing features that have been edited and no longer exist."""

        geometries = [feature["geometry"] for feature in self.draw_control.data]

        for feature in self.draw_features:
            if feature["geometry"] not in geometries:
                self.draw_features.remove(feature)

    def get_draw_props(
        self, n: Optional[int] = None, return_df: bool = False
    ) -> pd.DataFrame:
        """Get the properties of the draw features.

        Args:
            n (int, optional): The maximum number of attributes to return. Defaults to None.
            return_df (bool, optional): If True, return a pandas dataframe. Defaults to False.

        Returns:
            pd.DataFrame: A pandas dataframe containing the properties of the draw features.
        """

        import pandas as pd

        props = self.edit_props[:]

        for feature in self.draw_features:
            for prop in feature["properties"]:
                if prop not in self.edit_props:
                    self.edit_props.append(prop)
                    props.append(prop)

        if return_df:
            if isinstance(n, int) and n > len(props):
                props = props + [""] * (n - len(props))

            df = pd.DataFrame({"Key": props, "Value": [""] * len(props)})
            df.index += 1
            return df
        else:
            return props

    def update_draw_props(self, df: pd.DataFrame) -> None:
        """Update the draw features properties.

        Args:
            df (pd.DataFrame): A pandas dataframe containing the properties of the draw features.
        """

        df.dropna(inplace=True)
        df = df[df["Key"].astype(bool)]
        if len(df) > 0:
            props = df.set_index("Key").to_dict()["Value"]
            if self.draw_control.last_action == "edited":
                self.update_draw_features()
            if len(self.draw_features) > 0:
                if self.draw_control.last_action == "created":
                    self.draw_features[-1]["properties"] = props
                elif self.draw_control.last_action == "edited":
                    for feature in self.draw_features:
                        if (
                            self.draw_control.last_draw["geometry"]
                            == feature["geometry"]
                        ):
                            feature["properties"] = props
            for prop in list(props.keys()):
                if prop not in self.edit_props:
                    self.edit_props.append(prop)

    def edit_vector(self, data: Union[dict, str], **kwargs) -> None:
        """Edit a vector layer.

        Args:
            data (dict | str): The data to edit. It can be a GeoJSON dictionary or a file path.
        """
        if isinstance(data, str):
            check_package("geopandas", "https://geopandas.org")
            import geopandas as gpd

            gdf = gpd.read_file(data, **kwargs)
            geojson = gdf_to_geojson(gdf, epsg=4326, tuple_to_list=True)
        elif isinstance(data, dict):
            geojson = data
        else:
            raise ValueError(
                "The data must be a GeoJSON dictionary or a file path to a vector dataset."
            )
        self.draw_control.data = self.draw_control.data + (geojson["features"])
        self.draw_features = self.draw_features + (geojson["features"])

    def add_velocity(
        self,
        data: str,
        zonal_speed: str,
        meridional_speed: str,
        latitude_dimension: str = "lat",
        longitude_dimension: str = "lon",
        level_dimension: Optional[str] = "lev",
        level_index: int = 0,
        time_index: int = 0,
        velocity_scale: float = 0.01,
        max_velocity: int = 20,
        display_options: Optional[dict] = {},
        name: Optional[str] = "Velocity",
        color_scale: Optional[list] = None,
    ) -> None:
        """Add a velocity layer to the map.

        Args:
            data (str | xr.Dataset): The data to use for the velocity layer. It can be a file path to a NetCDF file or an xarray Dataset.
            zonal_speed (str): Name of the zonal speed in the dataset. See https://en.wikipedia.org/wiki/Zonal_and_meridional_flow.
            meridional_speed (str): Name of the meridional speed in the dataset. See https://en.wikipedia.org/wiki/Zonal_and_meridional_flow.
            latitude_dimension (str, optional): Name of the latitude dimension in the dataset. Defaults to 'lat'.
            longitude_dimension (str, optional): Name of the longitude dimension in the dataset. Defaults to 'lon'.
            level_dimension (str, optional): Name of the level dimension in the dataset. Defaults to 'lev'.
            level_index (int, optional): The index of the level dimension to display. Defaults to 0.
            time_index (int, optional): The index of the time dimension to display. Defaults to 0.
            velocity_scale (float, optional): The scale of the velocity. Defaults to 0.01.
            max_velocity (int, optional): The maximum velocity to display. Defaults to 20.
            display_options (dict, optional): The display options for the velocity layer. Defaults to {}. See https://bit.ly/3uf8t6w.
            name (str, optional): Layer name to use . Defaults to 'Velocity'.
            color_scale (list, optional): List of RGB color values for the velocity vector color scale. Defaults to []. See https://bit.ly/3uf8t6w.

        Raises:
            ImportError: If the xarray package is not installed.
            ValueError: If the data is not a NetCDF file or an xarray Dataset.
        """
        try:
            import xarray as xr
            from ipyleaflet.velocity import Velocity
        except ImportError:
            raise ImportError(
                "The xarray package is required to add a velocity layer. "
                "Please install it with `pip install xarray`."
            )

        if isinstance(data, str):
            if data.startswith("http"):
                data = download_file(data)
            ds = xr.open_dataset(data)

        elif isinstance(data, xr.Dataset):
            ds = data
        else:
            raise ValueError("The data must be a file path or xarray dataset.")

        coords = list(ds.coords.keys())

        # Rasterio does not handle time or levels. So we must drop them
        if "time" in coords:
            ds = ds.isel(time=time_index, drop=True)

        params = {level_dimension: level_index}
        if level_dimension in coords:
            ds = ds.isel(drop=True, **params)

        if color_scale is None:
            color_scale = [
                "rgb(36,104, 180)",
                "rgb(60,157, 194)",
                "rgb(128,205,193)",
                "rgb(151,218,168)",
                "rgb(198,231,181)",
                "rgb(238,247,217)",
                "rgb(255,238,159)",
                "rgb(252,217,125)",
                "rgb(255,182,100)",
                "rgb(252,150,75)",
                "rgb(250,112,52)",
                "rgb(245,64,32)",
                "rgb(237,45,28)",
                "rgb(220,24,32)",
                "rgb(180,0,35)",
            ]

        wind = Velocity(
            data=ds,
            zonal_speed=zonal_speed,
            meridional_speed=meridional_speed,
            latitude_dimension=latitude_dimension,
            longitude_dimension=longitude_dimension,
            velocity_scale=velocity_scale,
            max_velocity=max_velocity,
            display_options=display_options,
            name=name,
            color_scale=color_scale,
        )
        self.add(wind)

    def add_data(
        self,
        data: Union[str, pd.DataFrame],
        column: str,
        colors: Optional[str] = None,
        labels: Optional[str] = None,
        cmap: Optional[str] = None,
        scheme: Optional[str] = "Quantiles",
        k: int = 5,
        add_legend: Optional[bool] = True,
        legend_title: Optional[bool] = None,
        legend_position: Optional[str] = "bottomright",
        legend_kwds: Optional[dict] = None,
        classification_kwds: Optional[dict] = None,
        layer_name: Optional[str] = "Untitled",
        style: Optional[dict] = None,
        hover_style: Optional[dict] = None,
        style_callback: Optional[dict] = None,
        marker_radius: int = 10,
        marker_args=None,
        info_mode: Optional[str] = "on_hover",
        encoding: Optional[str] = "utf-8",
        **kwargs,
    ) -> None:
        """Add vector data to the map with a variety of classification schemes.

        Args:
            data (str | pd.DataFrame | gpd.GeoDataFrame): The data to classify. It can be a filepath to a vector dataset, a pandas dataframe, or a geopandas geodataframe.
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
            k (int, optional): Number of classes (ignored if scheme is None or if column is categorical). Default to 5.
            add_legend (bool, optional): Whether to add a legend to the map. Defaults to True.
            legend_title (str, optional): The title of the legend. Defaults to None.
            legend_position (str, optional): The position of the legend. Can be 'topleft', 'topright', 'bottomleft', or 'bottomright'. Defaults to 'bottomright'.
            legend_kwds (dict, optional): Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or `matplotlib.pyplot.colorbar`. Defaults to None.
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
            classification_kwds (dict, optional): Keyword arguments to pass to mapclassify. Defaults to None.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to None.
                style is a dictionary of the following form:
                    style = {
                    "stroke": False,
                    "color": "#ff0000",
                    "weight": 1,
                    "opacity": 1,
                    "fill": True,
                    "fillColor": "#ffffff",
                    "fillOpacity": 1.0,
                    "dashArray": "9"
                    "clickable": True,
                }
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
                hover_style is a dictionary of the following form:
                    hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
                style_callback is a function that takes the feature as argument and should return a dictionary of the following form:
                style_callback = lambda feat: {"fillColor": feat["properties"]["color"]}
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
            **kwargs: Additional keyword arguments to pass to the GeoJSON class, such as fields, which can be a list of column names to be included in the popup.

        """

        gdf, legend_dict = classify(
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

        if style is None:
            style = {
                # "stroke": False,
                # "color": "#ff0000",
                "weight": 1,
                "opacity": 1,
                # "fill": True,
                # "fillColor": "#ffffff",
                "fillOpacity": 1.0,
                # "dashArray": "9"
                # "clickable": True,
            }
            if colors is not None:
                style["color"] = "#000000"

        if hover_style is None:
            hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}

        if style_callback is None:
            style_callback = lambda feat: {"fillColor": feat["properties"]["color"]}

        if gdf.geometry.geom_type.unique().tolist()[0] == "Point":
            columns = gdf.columns.tolist()
            if "category" in columns:
                columns.remove("category")
            if "color" in columns:
                columns.remove("color")
            if marker_args is None:
                marker_args = {}
            if "fill_color" not in marker_args:
                marker_args["fill_color"] = gdf["color"].tolist()
            if "stroke" not in marker_args:
                marker_args["stroke"] = False
            if "fill_opacity" not in marker_args:
                marker_args["fill_opacity"] = 0.8

            marker_args["radius"] = marker_radius

            self.add_markers(gdf[columns], layer_name=layer_name, **marker_args)
        else:
            self.add_gdf(
                gdf,
                layer_name=layer_name,
                style=style,
                hover_style=hover_style,
                style_callback=style_callback,
                info_mode=info_mode,
                encoding=encoding,
                **kwargs,
            )
        if add_legend:
            self.add_legend(
                title=legend_title, legend_dict=legend_dict, position=legend_position
            )

    def user_roi_bounds(self, decimals: int = 4) -> list:
        """Get the bounds of the user drawn ROI as a tuple of (minx, miny, maxx, maxy).

        Args:
            decimals (int, optional): The number of decimals to round the coordinates to. Defaults to 4.

        Returns:
            list: The bounds of the user drawn ROI as a tuple of (minx, miny, maxx, maxy).
        """
        if self.user_roi is not None:
            return geometry_bounds(self.user_roi, decimals=decimals)
        else:
            return None

    def add_widget(
        self,
        content: str,
        position: Optional[str] = "bottomright",
        add_header: Optional[bool] = False,
        opened: Optional[bool] = True,
        show_close_button: Optional[bool] = True,
        widget_icon: Optional[str] = "gear",
        close_button_icon: Optional[str] = "times",
        widget_args: Optional[dict] = {},
        close_button_args: Optional[dict] = {},
        display_widget=None,
        **kwargs,
    ) -> None:
        """Add a widget (e.g., text, HTML, figure) to the map.

        Args:
            content (str | ipywidgets.Widget | object): The widget to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
            add_header (bool, optional): Whether to add a header with close buttons to the widget. Defaults to False.
            opened (bool, optional): Whether to open the toolbar. Defaults to True.
            show_close_button (bool, optional): Whether to show the close button. Defaults to True.
            widget_icon (str, optional): The icon name for the toolbar button. Defaults to 'gear'.
            close_button_icon (str, optional): The icon name for the close button. Defaults to "times".
            widget_args (dict, optional): Additional arguments to pass to the toolbar button. Defaults to {}.
            close_button_args (dict, optional): Additional arguments to pass to the close button. Defaults to {}.
            display_widget (ipywidgets.Widget, optional): The widget to be displayed when the toolbar is clicked.
            **kwargs: Additional arguments to pass to the HTML or Output widgets
        """

        allowed_positions = ["topleft", "topright", "bottomleft", "bottomright"]

        if position not in allowed_positions:
            raise Exception(f"position must be one of {allowed_positions}")

        if "layout" not in kwargs:
            kwargs["layout"] = widgets.Layout(padding="0px 4px 0px 4px")
        try:
            if add_header:
                if isinstance(content, str):
                    widget = widgets.HTML(value=content, **kwargs)
                else:
                    widget = content

                widget_template(
                    widget,
                    opened,
                    show_close_button,
                    widget_icon,
                    close_button_icon,
                    widget_args,
                    close_button_args,
                    display_widget,
                    self,
                    position,
                )
            else:
                if isinstance(content, str):
                    widget = widgets.HTML(value=content, **kwargs)
                else:
                    widget = widgets.Output(**kwargs)
                    with widget:
                        display(content)
                control = ipyleaflet.WidgetControl(widget=widget, position=position)
                self.add(control)

        except Exception as e:
            raise Exception(f"Error adding widget: {e}")

    def add_image(self, image, position="bottomright", **kwargs):
        """Add an image to the map.

        Args:
            image (str | ipywidgets.Image): The image to add.
            position (str, optional): The position of the image, can be one of "topleft",
                "topright", "bottomleft", "bottomright". Defaults to "bottomright".

        """

        if isinstance(image, str):
            if image.startswith("http"):
                image = widgets.Image(value=requests.get(image).content, **kwargs)
            elif os.path.exists(image):
                with open(image, "rb") as f:
                    image = widgets.Image(value=f.read(), **kwargs)
        elif isinstance(image, widgets.Image):
            pass
        else:
            raise Exception("Invalid image")

        self.add_widget(image, position=position)

    def add_html(
        self, html: str, position: Optional[str] = "bottomright", **kwargs
    ) -> None:
        """Add HTML to the map.

        Args:
            html (str): The HTML to add.
            position (str, optional): The position of the HTML, can be one of "topleft",
                "topright", "bottomleft", "bottomright". Defaults to "bottomright".
        """
        # Check if an HTML string contains local images and convert them to base64.
        html = check_html_string(html)
        self.add_widget(html, position=position, **kwargs)

    def add_text(
        self,
        text: str,
        fontsize: int = 20,
        fontcolor: int = "black",
        bold: Optional[bool] = False,
        padding: Optional[str] = "5px",
        background: Optional[bool] = True,
        bg_color: Optional[str] = "white",
        border_radius: Optional[str] = "5px",
        position: Optional[str] = "bottomright",
        **kwargs,
    ) -> None:
        """Add text to the map.

        Args:
            text (str): The text to add.
            fontsize (int, optional): The font size. Defaults to 20.
            fontcolor (str, optional): The font color. Defaults to "black".
            bold (bool, optional): Whether to use bold font. Defaults to False.
            padding (str, optional): The padding. Defaults to "5px".
            background (bool, optional): Whether to use background. Defaults to True.
            bg_color (str, optional): The background color. Defaults to "white".
            border_radius (str, optional): The border radius. Defaults to "5px".
            position (str, optional): The position of the widget. Defaults to "bottomright".
        """

        if background:
            text = f"""<div style="font-size: {fontsize}px; color: {fontcolor}; font-weight: {'bold' if bold else 'normal'};
            padding: {padding}; background-color: {bg_color};
            border-radius: {border_radius};">{text}</div>"""
        else:
            text = f"""<div style="font-size: {fontsize}px; color: {fontcolor}; font-weight: {'bold' if bold else 'normal'};
            padding: {padding};">{text}</div>"""

        self.add_html(text, position=position, **kwargs)

    def get_bbox(self) -> list:
        """Get the bounds of the map as a list of [(]minx, miny, maxx, maxy].

        Returns:
            list: The bounds of the map as a list of [(]minx, miny, maxx, maxy].
        """
        bounds = self.bounds
        bbox = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]
        return bbox

    def oam_search(
        self,
        bbox: Optional[Union[list, str]] = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100,
        info_mode: str = "on_click",
        layer_args: Optional[dict] = {},
        add_image: Optional[bool] = True,
        **kwargs,
    ) -> None:
        """Search OpenAerialMap for images within a bounding box and time range.

        Args:
            bbox (list | str, optional): The bounding box [xmin, ymin, xmax, ymax] to search within. Defaults to None.
            start_date (str, optional): The start date to search within, such as "2015-04-20T00:00:00.000Z". Defaults to None.
            end_date (str, optional): The end date to search within, such as "2015-04-21T00:00:00.000Z". Defaults to None.
            limit (int, optional): The maximum number of results to return. Defaults to 100.
            info_mode (str, optional): The mode to use for the info popup. Can be 'on_hover' or 'on_click'. Defaults to 'on_click'.
            layer_args (dict, optional): The layer arguments for add_gdf() function. Defaults to {}.
            add_image (bool, optional): Whether to add the first 10 images to the map. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the API. See https://hotosm.github.io/oam-api/
        """

        bounds = self.bounds
        if bbox is None:
            if self.user_roi is not None:
                bbox = self.user_roi_bounds()
            else:
                bbox = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]

        if self.zoom <= 4:
            print("Zoom in to search for images")
            return None

        gdf = oam_search(
            bbox=bbox, start_date=start_date, end_date=end_date, limit=limit, **kwargs
        )

        if "layer_name" not in layer_args:
            layer_args["layer_name"] = "Footprints"

        if "style" not in layer_args:
            layer_args["style"] = {
                # "stroke": True,
                "color": "#3388ff",
                "weight": 2,
                "opacity": 1,
                # "fill": True,
                # "fillColor": "#ffffff",
                "fillOpacity": 0,
                # "dashArray": "9"
                # "clickable": True,
            }

        if "hover_style" not in layer_args:
            layer_args["hover_style"] = {"weight": layer_args["style"]["weight"] + 2}

        if gdf is not None:
            setattr(self, "oam_gdf", gdf)
            self.add_gdf(gdf, info_mode=info_mode, **layer_args)

            if add_image:
                ids = gdf["_id"].tolist()
                images = gdf["tms"].tolist()

                if len(images) > 5:
                    print(f"Found {len(images)} images. \nShowing the first 5.")

                for index, image in enumerate(images):
                    if index == 5:
                        break
                    self.add_tile_layer(
                        url=image, name=ids[index], attribution="OpenAerialMap"
                    )
        else:
            print("No images found.")

    def set_catalog_source(self, source: Optional[str]) -> None:
        """Set the catalog source.

        Args:
            catalog_source (str, optional): The catalog source. Defaults to "landsat".
        """
        if not isinstance(source, dict):
            raise TypeError(
                "The source must be a dictionary in the format of {label: url, label2:url2}, \
                such as {'Element84': 'https://earth-search.aws.element84.com/v1'}"
            )
        if not hasattr(self, "_STAC_CATALOGS"):
            self.catalog_source = {}

        self._STAC_CATALOGS = source

    def clear_drawings(self) -> None:
        """Clear drawings on the map."""
        self.draw_control.clear()
        self.draw_features = []
        self.user_rois = None
        self.user_roi = None

    def add_layer_manager(
        self, position: Optional[str] = "topright", opened: bool = True
    ) -> None:
        """Add the Layer Manager to the map.

        Args:
            position (str, optional): The position of the Layer Manager. Defaults to "topright".
        """
        from .toolbar import layer_manager_gui

        layer_manager_gui(self, position, opened)

    def update_layer_manager(self) -> None:
        """Update the Layer Manager."""
        from .toolbar import layer_manager_gui

        self._layer_manager_widget.children = layer_manager_gui(
            self, return_widget=True
        )

    def add_oam_gui(
        self, position: Optional[str] = "topright", opened: bool = True
    ) -> None:
        """Add the OpenAerialMap search widget to the map.

        Args:
            position (str, optional): The position of the widget. Defaults to "topright".
            opened (bool, optional): Whether the widget is open. Defaults to True.
        """
        from .toolbar import oam_search_gui

        oam_search_gui(self, position, opened)

    def add_stac_gui(self, position: str = "topright", opened: bool = True) -> None:
        """Add the STAC search widget to the map.

        Args:
            position (str, optional): The position of the widget. Defaults to "topright".
            opened (bool, optional): Whether the widget is open. Defaults to True.
        """
        from .toolbar import stac_gui

        stac_gui(self, position, opened)

    def add_inspector_gui(
        self, position: Optional[str] = "topright", opened: bool = True
    ) -> None:
        """Add the Inspector widget to the map.

        Args:
            position (str, optional): The position of the widget. Defaults to "topright".
            opened (bool, optional): Whether the widget is open. Defaults to True.
        """

        from .toolbar import inspector_gui

        inspector_gui(self, position, opened)

    def add_basemap_gui(self, position: Optional[str] = "topright") -> None:
        """Add the basemap widget to the map.

        Args:
            position (str, optional): The position of the widget. Defaults to "topright".
        """
        from .toolbar import change_basemap

        change_basemap(self, position)

    def _add_layer_editor(self, position: str, **kwargs) -> None:
        if self._layer_editor:
            return

        widget = map_widgets.LayerEditor(self, **kwargs)
        widget.on_close = lambda: self.remove("layer_editor")
        control = ipyleaflet.WidgetControl(widget=widget, position=position)
        super().add(control)

    def _find_widget_of_type(
        self, widget_type: Type, return_control: bool = False
    ) -> Optional[Any]:
        """Finds a widget in the controls with the passed in type."""
        for widget in self.controls:
            if isinstance(widget, ipyleaflet.WidgetControl):
                if isinstance(widget.widget, widget_type):
                    return widget if return_control else widget.widget
            elif isinstance(widget, widget_type):
                return widget
        return None

    def remove(self, widget: Any) -> None:
        """Removes a widget to the map."""

        basic_controls: Dict[str, ipyleaflet.Control] = {
            "layer_editor": map_widgets.LayerEditor,
        }
        if widget_type := basic_controls.get(widget, None):
            if control := self._find_widget_of_type(widget_type, return_control=True):
                self.remove(control)
                control.close()
            return

        super().remove(widget)
        if isinstance(widget, ipywidgets.Widget):
            widget.close()

    def edit_points(
        self,
        data: Union[str, "gpd.GeoDataFrame", Dict[str, Any]],
        display_props: Optional[List[str]] = None,
        widget_width: str = "250px",
        name: str = "Points",
        radius: int = 5,
        color: str = "white",
        weight: int = 1,
        fill_color: str = "#3388ff",
        fill_opacity: float = 0.6,
        **kwargs: Any,
    ) -> None:
        """
        Edit points on a map by creating interactive circle markers with popups.

        Args:
            data (Union[str, gpd.GeoDataFrame, Dict[str, Any]]): The data source,
                which can be a file path, GeoDataFrame, or GeoJSON dictionary.
            display_props (Optional[List[str]], optional): List of properties to
                display in the popup. Defaults to None.
            widget_width (str, optional): Width of the widget in the popup.
                Defaults to "250px".
            name (str, optional): Name of the layer group. Defaults to "Points".
            radius (int, optional): Initial radius of the circle markers. Defaults to 5.
            color (str, optional): Outline color of the circle markers. Defaults to "white".
            weight (int, optional): Outline weight of the circle markers. Defaults to 1.
            fill_color (str, optional): Fill color of the circle markers. Defaults to "#3388ff".
            fill_opacity (float, optional): Fill opacity of the circle markers. Defaults to 0.6.
            **kwargs (Any): Additional arguments for the CircleMarker.

        Returns:
            None
        """

        import geopandas as gpd
        from ipyleaflet import CircleMarker, Popup

        if isinstance(data, gpd.GeoDataFrame):
            if data.crs != "EPSG:4326":
                data = data.to_crs("EPSG:4326")
            geojson_data = data.__geo_interface__
        elif isinstance(data, str):
            data = gpd.read_file(data)
            if data.crs != "EPSG:4326":
                data = data.to_crs("EPSG:4326")
            geojson_data = data.__geo_interface__
        elif isinstance(data, dict):
            geojson_data = data
        else:
            raise ValueError("The data must be a GeoDataFrame or a GeoJSON dictionary.")

        self._geojson_data = geojson_data

        def create_popup_widget(
            circle_marker, properties, original_properties, display_properties=None
        ):
            """Create a popup widget to change circle properties and edit feature attributes."""
            # Widgets for circle properties
            radius_slider = widgets.IntSlider(
                value=circle_marker.radius,
                min=1,
                max=50,
                description="Radius:",
                continuous_update=False,
                layout=widgets.Layout(width=widget_width),
            )

            color_picker = widgets.ColorPicker(
                value=circle_marker.color,
                description="Color:",
                continuous_update=False,
                layout=widgets.Layout(width=widget_width),
            )

            fill_color_picker = widgets.ColorPicker(
                value=circle_marker.fill_color,
                description="Fill color:",
                continuous_update=False,
                layout=widgets.Layout(width=widget_width),
            )

            # Widgets for feature properties
            property_widgets = {}
            display_properties = display_properties or properties.keys()
            for key in display_properties:
                value = properties.get(key, "")
                if isinstance(value, str):
                    widget = widgets.Text(
                        value=value,
                        description=f"{key}:",
                        continuous_update=False,
                        layout=widgets.Layout(width=widget_width),
                    )
                elif isinstance(value, (int, float)):
                    widget = widgets.FloatText(
                        value=value,
                        description=f"{key}:",
                        continuous_update=False,
                        layout=widgets.Layout(width=widget_width),
                    )
                else:
                    widget = widgets.Label(
                        value=f"{key}: {value}",
                        layout=widgets.Layout(width=widget_width),
                    )

                property_widgets[key] = widget

            def update_circle(change):
                """Update circle properties based on widget values."""
                circle_marker.radius = radius_slider.value
                circle_marker.color = color_picker.value
                circle_marker.fill_color = fill_color_picker.value
                for key, widget in property_widgets.items():
                    properties[key] = widget.value

            def reset_circle(change):
                """Reset circle properties to their original values."""
                circle_marker.radius = original_properties["radius"]
                circle_marker.color = original_properties["color"]
                circle_marker.fill_color = original_properties["fill_color"]
                radius_slider.value = original_properties["radius"]
                color_picker.value = original_properties["color"]
                fill_color_picker.value = original_properties["fill_color"]
                for key, widget in property_widgets.items():
                    widget.value = original_properties["properties"].get(key, "")

            # Link widgets to update the circle marker properties and point attributes
            radius_slider.observe(update_circle, "value")
            color_picker.observe(update_circle, "value")
            fill_color_picker.observe(update_circle, "value")
            for widget in property_widgets.values():
                widget.observe(update_circle, "value")

            # Reset button
            reset_button = widgets.Button(
                description="Reset", layout=widgets.Layout(width=widget_width)
            )
            reset_button.on_click(reset_circle)

            # Arrange widgets in a vertical box with increased width
            vbox = widgets.VBox(
                [radius_slider, color_picker, fill_color_picker]
                + list(property_widgets.values())
                + [reset_button],
                layout=widgets.Layout(
                    width="310px"
                ),  # Set the width of the popup widget
            )
            return vbox

        def create_on_click_handler(circle_marker, properties, display_properties=None):
            """Create an on_click handler with the circle_marker bound."""
            # Save the original properties for reset
            original_properties = {
                "radius": circle_marker.radius,
                "color": circle_marker.color,
                "fill_color": circle_marker.fill_color,
                "properties": properties.copy(),
            }

            def on_click(**kwargs):
                if kwargs.get("type") == "click":
                    # Create a popup widget with controls
                    popup_widget = create_popup_widget(
                        circle_marker,
                        properties,
                        original_properties,
                        display_properties,
                    )
                    popup = Popup(
                        location=circle_marker.location,
                        child=popup_widget,
                        close_button=True,
                        auto_close=False,
                        close_on_escape_key=True,
                        min_width=int(widget_width[:-2]) + 10,
                    )
                    self.add_layer(popup)
                    popup.open = True

            return on_click

        layers = []

        # Iterate over each feature in the GeoJSON data and create a CircleMarker
        for feature in geojson_data["features"]:
            coordinates = feature["geometry"]["coordinates"]
            properties = feature["properties"]

            circle_marker = CircleMarker(
                location=(coordinates[1], coordinates[0]),  # (lat, lon)
                radius=radius,  # Initial radius of the circle
                color=color,  # Outline color
                weight=weight,  # Outline
                fill_color=fill_color,  # Fill color
                fill_opacity=fill_opacity,
                **kwargs,
            )

            # Create and bind the on_click handler for each circle_marker
            circle_marker.on_click(
                create_on_click_handler(circle_marker, properties, display_props)
            )

            # Add the circle marker to the map
            layers.append(circle_marker)

        group = ipyleaflet.LayerGroup(layers=tuple(layers), name=name)
        self.add(group)

    def edit_polygons(
        self,
        data: Union[str, "gpd.GeoDataFrame", Dict[str, Any]],
        style: Optional[Dict[str, Any]] = None,
        hover_style: Optional[Dict[str, Any]] = None,
        name: str = "GeoJSON",
        widget_width: str = "250px",
        info_mode: str = "on_click",
        zoom_to_layer: bool = True,
        **kwargs: Any,
    ) -> None:
        """Edit polygons on the map.

        Args:
            data (Union[str, gpd.GeoDataFrame, Dict[str, Any]]): The data to be
                edited, either as a file path, GeoDataFrame, or GeoJSON dictionary.
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the polygons. Defaults to None.
            hover_style (Optional[Dict[str, Any]], optional): The hover style
                dictionary for the polygons. Defaults to None.
            name (str, optional): The name of the GeoJSON layer. Defaults to "GeoJSON".
            widget_width (str, optional): The width of the widgets. Defaults to "250px".
            info_mode (str, optional): The mode for displaying information,
                either "on_click" or "on_hover". Defaults to "on_click".
            zoom_to_layer (bool, optional): Whether to zoom to the layer bounds.
                Defaults to True.
            **kwargs (Any): Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data is not a GeoDataFrame or a GeoJSON dictionary.
        """
        from ipyleaflet import GeoJSON, Popup
        from shapely.geometry import shape
        import copy
        import geopandas as gpd
        import json

        bounds = None

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            bounds = gdf.total_bounds
            temp_geojson = temp_file_path("geojson")
            gdf.to_file(temp_geojson, driver="GeoJSON")
            with open(temp_geojson) as f:
                data = json.load(f)
        elif isinstance(data, gpd.GeoDataFrame):
            if data.crs != "EPSG:4326":
                data = data.to_crs("EPSG:4326")
            bounds = data.total_bounds
            temp_geojson = temp_file_path("geojson")
            data.to_file(temp_geojson, driver="GeoJSON")
            with open(temp_geojson) as f:
                data = json.load(f)

        if isinstance(data, dict):
            geojson_data = data
            if zoom_to_layer and (bounds is not None):
                bounds = gpd.GeoDataFrame.from_features(data).total_bounds
        else:
            raise ValueError("The data must be a GeoDataFrame or a GeoJSON dictionary.")

        layout = widgets.Layout(width=widget_width)

        if style is None:
            style = {"color": "#3388ff"}
        if hover_style is None:
            hover_style = {"color": "yellow", "weight": 5}

        def calculate_centroid(polygon_coordinates, geom_type):
            polygon = shape({"type": geom_type, "coordinates": polygon_coordinates})
            centroid = polygon.centroid
            return centroid.y, centroid.x  # Return as (lat, lon)

        def create_property_widgets(properties):
            """Dynamically create widgets for each property."""
            widgets_list = []
            for key, value in properties.items():
                if key == "style":
                    continue
                if isinstance(value, (int, float)):
                    widget = widgets.FloatText(
                        value=value, description=f"{key}:", layout=layout
                    )
                else:
                    widget = widgets.Text(
                        value=str(value), description=f"{key}:", layout=layout
                    )
                widget._property_key = (
                    key  # Store the key in the widget for easy access later
                )
                widgets_list.append(widget)
            return widgets_list

        def on_click(event, feature, **kwargs):
            # Dynamically create input widgets for each property
            property_widgets = create_property_widgets(feature["properties"])
            save_button = widgets.Button(description="Save", layout=layout)
            geom_type = feature["geometry"]["type"]
            centroid = calculate_centroid(feature["geometry"]["coordinates"], geom_type)

            # Create and open the popup
            popup_content = widgets.VBox(property_widgets + [save_button])

            popup = Popup(
                location=centroid,
                child=popup_content,
                close_button=True,
                auto_close=True,
                close_on_escape_key=True,
                min_width=int(widget_width[:-2]) + 5,
            )

            self.add_layer(popup)

            def save_changes(_):

                original_data = copy.deepcopy(geojson_layer.data)
                original_feature = copy.deepcopy(feature)
                # Update the properties with the new values
                for widget in property_widgets:
                    feature["properties"][widget._property_key] = widget.value

                for i, f in enumerate(original_data["features"]):
                    if f == original_feature:
                        original_data["features"][i] = feature
                        break

                # Update the GeoJSON layer to reflect the changes

                geojson_layer.data = original_data
                self._geojson_data = original_data

                self.remove_layer(popup)  # Close the popup by removing it from the map

            save_button.on_click(save_changes)

        # Add GeoJSON layer to the map
        geojson_layer = GeoJSON(
            data=geojson_data, style=style, hover_style=hover_style, name=name, **kwargs
        )

        # Attach event to the GeoJSON layer
        if info_mode == "on_click":
            geojson_layer.on_click(on_click)
        elif info_mode == "on_hover":
            geojson_layer.on_hover(on_click)

        # Add layers to map
        self.add_layer(geojson_layer)
        self._geojson_data = geojson_layer.data

        if bounds is not None and zoom_to_layer:
            west, south, east, north = bounds
            self.fit_bounds([[south, east], [north, west]])

    def edit_lines(
        self,
        data: Union[str, "gpd.GeoDataFrame", Dict[str, Any]],
        style: Optional[Dict[str, Any]] = None,
        hover_style: Optional[Dict[str, Any]] = None,
        name: str = "GeoJSON",
        widget_width: str = "250px",
        info_mode: str = "on_click",
        zoom_to_layer: bool = True,
        **kwargs: Any,
    ) -> None:
        """Edit lines on the map.

        Args:
            data (Union[str, gpd.GeoDataFrame, Dict[str, Any]]): The data to be
                edited, either as a file path, GeoDataFrame, or GeoJSON dictionary.
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the lines. Defaults to None.
            hover_style (Optional[Dict[str, Any]], optional): The hover style
                dictionary for the lines. Defaults to None.
            name (str, optional): The name of the GeoJSON layer. Defaults to "GeoJSON".
            widget_width (str, optional): The width of the widgets. Defaults to "250px".
            info_mode (str, optional): The mode for displaying information,
                either "on_click" or "on_hover". Defaults to "on_click".
            zoom_to_layer (bool, optional): Whether to zoom to the layer bounds.
                Defaults to True.
            **kwargs (Any): Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data is not a GeoDataFrame or a GeoJSON dictionary.
        """
        self.edit_polygons(
            data=data,
            style=style,
            hover_style=hover_style,
            name=name,
            widget_width=widget_width,
            info_mode=info_mode,
            zoom_to_layer=zoom_to_layer,
            **kwargs,
        )

    def save_edits(
        self, filename: str, drop_style: bool = True, crs="EPSG:4326", **kwargs: Any
    ) -> None:
        """
        Save the edited GeoJSON data to a file.

        Args:
            filename (str): The name of the file to save the edited GeoJSON data.
            drop_style (bool, optional): Whether to drop the style properties
                from the GeoJSON data. Defaults to True.
            crs (str, optional): The CRS of the GeoJSON data. Defaults to "EPSG:4326".
            **kwargs (Any): Additional arguments passed to the GeoDataFrame `to_file` method.

        Returns:
            None
        """
        import geopandas as gpd

        if not hasattr(self, "_geojson_data"):
            print("No GeoJSON data to save.")
            return

        gdf = gpd.GeoDataFrame.from_features(self._geojson_data)
        if drop_style and "style" in gdf.columns:
            gdf = gdf.drop(columns=["style"])
            gdf.crs = "EPSG:4326"

        if crs != "EPSG:4326":
            gdf = gdf.to_crs(crs)
        gdf.to_file(filename, **kwargs)

    def batch_edit_points(
        self,
        data: Union[str, dict],
        style: Optional[Dict[str, Any]] = None,
        hover_style: Optional[Dict[str, Any]] = None,
        changed_style: Optional[Dict[str, Any]] = None,
        display_props: Optional[List[str]] = None,
        name: str = "Points",
        text_width: str = "250px",
        zoom_to_layer: bool = True,
        **kwargs: Any,
    ) -> None:
        """Batch editing points (CircleMarkers) on the map from GeoJSON data.

        Args:
            data (Union[str, dict]): The GeoJSON data or path to the GeoJSON file.
            style (Optional[Dict[str, Any]]): Style for the CircleMarkers.
            hover_style (Optional[Dict[str, Any]]): Style for the CircleMarkers on hover.
            changed_style (Optional[Dict[str, Any]]): Style for the CircleMarkers when changed.
            display_props (Optional[List[str]]): List of properties to display in the attribute editor.
            name (str): Name of the layer group.
            text_width (str): Width of the text widgets in the attribute editor.
            zoom_to_layer (bool): Whether to zoom to the layer bounds.
            **kwargs (Any): Additional keyword arguments for the LayerGroup.

        Raises:
            ValueError: If the data is not a GeoDataFrame or a GeoJSON dictionary.
            ValueError: If the GeoJSON data does not contain only Point geometries.
        """
        import geopandas as gpd
        import json

        bounds = None

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            bounds = gdf.total_bounds
            temp_geojson = temp_file_path("geojson")
            gdf.to_file(temp_geojson, driver="GeoJSON")
            with open(temp_geojson) as f:
                data = json.load(f)
        elif isinstance(data, gpd.GeoDataFrame):
            if data.crs != "EPSG:4326":
                data = data.to_crs("EPSG:4326")
            bounds = data.total_bounds
            temp_geojson = temp_file_path("geojson")
            data.to_file(temp_geojson, driver="GeoJSON")
            with open(temp_geojson) as f:
                data = json.load(f)

        if isinstance(data, dict):
            geojson_data = data
            if zoom_to_layer and (bounds is not None):
                bounds = gpd.GeoDataFrame.from_features(data).total_bounds
        else:
            raise ValueError("The data must be a GeoDataFrame or a GeoJSON dictionary.")

        # Ensure the data contains Point geometries
        if not all(
            feature["geometry"]["type"] == "Point"
            for feature in geojson_data["features"]
        ):
            raise ValueError("The GeoJSON data must contain only Point geometries.")

        highlighted_markers = []
        attribute_widgets = {}

        # Create CircleMarker objects for each point in the GeoJSON data
        markers = []

        if style is None:
            style = {
                "radius": 5,
                "weight": 1,
                "color": "white",
                "fill_color": "#3388ff",
                "fill_opacity": 0.6,
            }

        if hover_style is None:
            hover_style = {"color": "purple", "fill_color": "yellow"}

        if changed_style is None:
            changed_style = {"color": "cyan", "fill_color": "red"}

        for feature in data["features"]:
            coords = feature["geometry"]["coordinates"]
            properties = feature["properties"]

            marker = ipyleaflet.CircleMarker(
                location=(
                    coords[1],
                    coords[0],
                ),  # GeoJSON coordinates are (longitude, latitude)
                radius=style.get("radius", 5),
                weight=style.get("weight", 1),
                color=style.get("color", "white"),
                fill_color=style.get("fill_color", "#3388ff"),
                fill_opacity=style.get("fill_opacity", 0.6),
            )
            setattr(marker, "properties", properties)
            markers.append(marker)

        # Create a LayerGroup to hold the markers
        layer_group = ipyleaflet.LayerGroup(layers=markers, name=name, **kwargs)

        # Get the keys from the first feature's properties
        first_feature = data["features"][0]["properties"]

        # If display_props is not provided, show all attributes
        if display_props is None:
            display_props = first_feature.keys()

        text_layout = widgets.Layout(width=text_width)

        # Loop through the specified properties in display_props
        for key in display_props:
            if key in first_feature:  # Ensure the property exists
                attribute_widgets[key] = widgets.Text(
                    description=f"{key}:", layout=text_layout
                )

        # Update button and clear selection button
        button_width = "80px"
        button_layout = widgets.Layout(width=button_width)
        update_button = widgets.Button(description="Update", layout=button_layout)
        clear_button = widgets.Button(description="Clear", layout=button_layout)
        close_button = widgets.Button(description="Close", layout=button_layout)
        output_widget = widgets.Output()

        # Function to highlight the clicked marker and clear attribute fields
        def highlight_marker(marker, **kwargs):
            nonlocal highlighted_markers

            if marker in highlighted_markers:
                highlighted_markers.remove(marker)
                marker.color = style.get("color", "white")
                marker.fill_color = style.get("fill_color", "#3388ff")

            else:
                highlighted_markers.append(marker)
                marker.color = hover_style.get("color", "purple")
                marker.fill_color = hover_style.get("fill_color", "yellow")

        # Function to clear the selection
        def clear_selection(_):
            for marker in highlighted_markers:
                if marker.color != changed_style.get(
                    "color", "cyan"
                ) and marker.fill_color != changed_style.get("fill_color", "red"):
                    marker.color = style.get("color", "white")
                    marker.fill_color = style.get("fill_color", "#3388ff")
            for key, widget in attribute_widgets.items():
                widget.value = ""
                widget.placeholder = ""
            highlighted_markers.clear()

        def get_geojson_data():
            geojson_data = {"type": "FeatureCollection", "features": []}
            for layer in layer_group.layers:
                feature = {
                    "type": "Feature",
                    "properties": layer.properties,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [layer.location[1], layer.location[0]],
                    },
                }

                geojson_data["features"].append(feature)
                self._geojson_data = geojson_data

        # Function to apply changes to highlighted markers
        def update_highlighted_markers(_):
            output_widget.clear_output()

            changed = False
            for index, marker in enumerate(highlighted_markers):
                for key, widget in attribute_widgets.items():
                    if widget.value.strip() != "":
                        changed = True
                        if isinstance(marker.properties[key], int):
                            try:
                                marker.properties[key] = int(widget.value)
                            except ValueError as e:
                                if index == 0:
                                    with output_widget:
                                        print(f"{key} must be an integer.")
                        elif isinstance(marker.properties[key], float):
                            try:
                                marker.properties[key] = float(widget.value)
                            except ValueError as e:
                                if index == 0:
                                    with output_widget:
                                        print(f"{key} must be a float.")
                        else:
                            marker.properties[key] = widget.value

                # Apply changed_style if defined
                if changed:
                    marker.color = changed_style.get("color", "cyan")
                    marker.fill_color = changed_style.get("fill_color", "red")
                else:
                    if index == 0:
                        with output_widget:
                            print("No changes to apply.")

            if changed:
                clear_selection(None)
                for key, widget in attribute_widgets.items():
                    widget.value = ""
                get_geojson_data()

        # Function to populate attribute fields on hover
        def populate_hover_attributes(marker, **kwargs):
            for key, widget in attribute_widgets.items():
                widget.value = ""
                widget.placeholder = str(marker.properties.get(key, ""))

        # Register click event to highlight markers
        for marker in markers:
            marker.on_click(lambda m=marker, **kwargs: highlight_marker(m))
            marker.on_mouseover(lambda m=marker, **kwargs: populate_hover_attributes(m))

        # Add the LayerGroup of markers to the map
        self.add_layer(layer_group)

        # Add event listeners to the buttons
        update_button.on_click(update_highlighted_markers)
        clear_button.on_click(clear_selection)

        # Create a VBox to hold the widgets for editing attributes and the buttons
        buttons = widgets.HBox([update_button, clear_button, close_button])
        attribute_editor = widgets.VBox(
            [*attribute_widgets.values(), buttons, output_widget]
        )

        # Embed the attribute editor inside the map using WidgetControl
        widget_control = ipyleaflet.WidgetControl(
            widget=attribute_editor, position="topright"
        )
        self.add_control(widget_control)

        def close_widget_control(_):
            self.remove(widget_control)

        close_button.on_click(close_widget_control)

        # Optionally zoom to the bounds of the points
        if zoom_to_layer:
            bounds = gpd.GeoDataFrame.from_features(data).total_bounds
            west, south, east, north = bounds
            self.fit_bounds([[south, west], [north, east]])

    def batch_edit_polygons(
        self,
        data: Union[str, "gpd.GeoDataFrame", Dict[str, Any]],
        style: Optional[Dict[str, Any]] = None,
        hover_style: Optional[Dict[str, Any]] = None,
        highlight_style: Optional[Dict[str, Any]] = None,
        changed_style: Optional[Dict[str, Any]] = None,
        display_props: Optional[List[str]] = None,
        name: str = "GeoJSON",
        text_width: str = "250px",
        zoom_to_layer: bool = True,
        **kwargs: Any,
    ) -> None:
        """Batch editing polygons on the map.

        Args:
            data (Union[str, gpd.GeoDataFrame, Dict[str, Any]]): The data to be
                edited, either as a file path, GeoDataFrame, or GeoJSON dictionary.
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the polygons. Defaults to None.
            hover_style (Optional[Dict[str, Any]], optional): The hover style
                dictionary for the polygons. Defaults to None.
            name (str, optional): The name of the GeoJSON layer. Defaults to "GeoJSON".
            widget_width (str, optional): The width of the widgets. Defaults to "250px".
            info_mode (str, optional): The mode for displaying information,
                either "on_click" or "on_hover". Defaults to "on_click".
            zoom_to_layer (bool, optional): Whether to zoom to the layer bounds.
                Defaults to True.
            **kwargs (Any): Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data is not a GeoDataFrame or a GeoJSON dictionary.
        """
        from ipyleaflet import GeoJSON
        import copy
        import geopandas as gpd
        import json

        bounds = None
        if isinstance(data, str):
            gdf = gpd.read_file(data)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            bounds = gdf.total_bounds
            temp_geojson = temp_file_path("geojson")
            gdf.to_file(temp_geojson, driver="GeoJSON")
            with open(temp_geojson) as f:
                data = json.load(f)
        elif isinstance(data, gpd.GeoDataFrame):
            if data.crs != "EPSG:4326":
                data = data.to_crs("EPSG:4326")
            bounds = data.total_bounds
            temp_geojson = temp_file_path("geojson")
            data.to_file(temp_geojson, driver="GeoJSON")
            with open(temp_geojson) as f:
                data = json.load(f)

        if isinstance(data, dict):
            data = data
            if zoom_to_layer and (bounds is not None):
                bounds = gpd.GeoDataFrame.from_features(data).total_bounds
        else:
            raise ValueError("The data must be a GeoDataFrame or a GeoJSON dictionary.")

        if style is None:
            style = {"color": "#3388ff"}

        if hover_style is None:
            hover_style = {"color": "yellow", "dashArray": "0", "fillOpacity": 0.3}

        if highlight_style is None:
            highlight_style = {
                "color": "#3388ff",
                "fillColor": "yellow",
                "weight": 3,
                "fillOpacity": 0.5,
            }

        if changed_style is None:
            changed_style = {
                "color": "#3388ff",
                "fillColor": "red",
                "weight": 3,
                "fillOpacity": 0.3,
            }

        # List to store the IDs of highlighted features
        highlighted_features = []

        # Create a dictionary to hold attribute widgets
        attribute_widgets = {}

        # Get the keys from the first feature to dynamically create widgets
        first_feature = data["features"][0]["properties"]

        # If display_props is not provided, show all attributes
        if display_props is None:
            display_props = first_feature.keys()

        text_layout = widgets.Layout(width=text_width)
        # Loop through only the specified properties in display_props
        for key in display_props:
            if key in first_feature:  # Ensure the property exists
                attribute_widgets[key] = widgets.Text(
                    description=f"{key.capitalize()}:", layout=text_layout
                )

        # Update button and clear selection button
        button_width = "80px"
        button_layout = widgets.Layout(width=button_width)
        update_button = widgets.Button(description="Update", layout=button_layout)
        clear_button = widgets.Button(description="Clear", layout=button_layout)
        close_button = widgets.Button(description="Close", layout=button_layout)
        output_widget = widgets.Output()

        # Function to highlight the clicked feature and clear attribute fields
        def highlight_feature(event, feature, **kwargs):
            nonlocal highlighted_features
            original_data = copy.deepcopy(geojson_layer.data)

            for index, f in enumerate(original_data["features"]):
                if f == feature:
                    if index in highlighted_features:
                        highlighted_features.remove(index)
                        original_data["features"][index]["properties"]["style"] = style
                    else:
                        highlighted_features.append(index)
                        original_data["features"][index]["properties"][
                            "style"
                        ] = highlight_style

            geojson_layer.data = original_data

        # Function to clear the selection
        def clear_selection(_):
            original_data = copy.deepcopy(geojson_layer.data)

            # Reset the style for all highlighted features
            for index in highlighted_features:
                if (
                    original_data["features"][index]["properties"]["style"]
                    != changed_style
                ):
                    original_data["features"][index]["properties"]["style"] = style

            highlighted_features.clear()
            geojson_layer.data = original_data

        # Function to apply changes to highlighted features
        def update_highlighted_features(_):
            output_widget.clear_output()
            original_data = copy.deepcopy(geojson_layer.data)

            # Update the properties for all highlighted features
            for index in highlighted_features:
                for key, widget in attribute_widgets.items():
                    if widget.value.strip() != "":
                        dtype = type(
                            original_data["features"][index]["properties"][key]
                        )
                        if dtype == str:
                            value = str(widget.value)
                        elif dtype == int:
                            try:
                                value = int(widget.value)
                            except ValueError:
                                with output_widget:
                                    print(f"Invalid value for {key}")
                                    continue
                        elif dtype == float:
                            try:
                                value = float(widget.value)
                            except ValueError:
                                with output_widget:
                                    print(f"Invalid value for {key}")
                                    continue
                        else:
                            value = widget.value
                        original_data["features"][index]["properties"][key] = value
                        original_data["features"][index]["properties"][
                            "style"
                        ] = changed_style

            geojson_layer.data = original_data
            self._geojson_data = original_data
            clear_selection(None)
            for key, widget in attribute_widgets.items():
                widget.value = ""

        # Function to populate attribute fields on hover
        def populate_hover_attributes(event, feature, **kwargs):
            # Populate the widget fields with the hovered feature's attributes
            for key, widget in attribute_widgets.items():
                if widget.value.strip() == "":
                    widget.value = ""
                    widget.placeholder = str(feature["properties"].get(key, ""))

        # Create the GeoJSON layer
        geojson_layer = GeoJSON(
            data=data,
            style=style,
            hover_style=hover_style,
            name=name,
        )

        # Add click event to highlight features and clear attribute fields
        geojson_layer.on_click(highlight_feature)

        # Add hover event to populate attribute fields
        geojson_layer.on_hover(populate_hover_attributes)

        # Add the GeoJSON layer to the map
        self.add_layer(geojson_layer)

        # Add event listeners to the buttons
        update_button.on_click(update_highlighted_features)
        clear_button.on_click(clear_selection)

        # Create a VBox to hold the widgets for editing attributes and the buttons
        buttons = widgets.HBox([update_button, clear_button, close_button])
        attribute_editor = widgets.VBox(
            [*attribute_widgets.values(), buttons, output_widget]
        )

        # Embed the attribute editor inside the map using WidgetControl
        widget_control = ipyleaflet.WidgetControl(
            widget=attribute_editor, position="topright"
        )
        self.add_control(widget_control)

        def close_widget_control(_):
            self.remove(widget_control)

        close_button.on_click(close_widget_control)

        # Add layers to map
        self._geojson_data = geojson_layer.data

        if bounds is not None and zoom_to_layer:
            west, south, east, north = bounds
            self.fit_bounds([[south, east], [north, west]])

    def batch_edit_lines(
        self,
        data: Union[str, "gpd.GeoDataFrame", Dict[str, Any]],
        style: Optional[Dict[str, Any]] = None,
        hover_style: Optional[Dict[str, Any]] = None,
        highlight_style: Optional[Dict[str, Any]] = None,
        changed_style: Optional[Dict[str, Any]] = None,
        display_props: Optional[List[str]] = None,
        name: str = "GeoJSON",
        text_width: str = "250px",
        zoom_to_layer: bool = True,
        **kwargs: Any,
    ) -> None:
        """Batch editing lines on the map.

        Args:
            data (Union[str, gpd.GeoDataFrame, Dict[str, Any]]): The data to be
                edited, either as a file path, GeoDataFrame, or GeoJSON dictionary.
            style (Optional[Dict[str, Any]], optional): The style dictionary for
                the polygons. Defaults to None.
            hover_style (Optional[Dict[str, Any]], optional): The hover style
                dictionary for the polygons. Defaults to None.
            name (str, optional): The name of the GeoJSON layer. Defaults to "GeoJSON".
            widget_width (str, optional): The width of the widgets. Defaults to "250px".
            info_mode (str, optional): The mode for displaying information,
                either "on_click" or "on_hover". Defaults to "on_click".
            zoom_to_layer (bool, optional): Whether to zoom to the layer bounds.
                Defaults to True.
            **kwargs (Any): Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data is not a GeoDataFrame or a GeoJSON dictionary.
        """
        self.batch_edit_polygons(
            data=data,
            style=style,
            hover_style=hover_style,
            highlight_style=highlight_style,
            changed_style=changed_style,
            display_props=display_props,
            name=name,
            text_width=text_width,
            zoom_to_layer=zoom_to_layer,
            **kwargs,
        )

    def add_nwi(
        self,
        data: Union[str, "gpd.GeoDataFrame"],
        col_name: str = "WETLAND_TY",
        add_legend: bool = True,
        style_callback: Optional[Callable[[dict], dict]] = None,
        layer_name: str = "Wetlands",
        **kwargs,
    ) -> None:
        """
        Adds National Wetlands Inventory (NWI) data to the map.

        Args:
            data (Union[str, gpd.GeoDataFrame]): The NWI data to add. It can be a file path or a GeoDataFrame.
            col_name (str): The column name in the GeoDataFrame that contains the wetland types.
            add_legend (bool): Whether to add a legend to the map. Defaults to True.
            style_callback (Optional[Callable[[dict], dict]]): A callback function to style the features. Defaults to None.
            layer_name (str): The name of the layer to add. Defaults to "Wetlands".
            **kwargs: Additional keyword arguments to pass to the add_vector or add_gdf method.

        Returns:
            None
        """

        nwi = {
            "Freshwater Forested/Shrub Wetland": "#008837",
            "Freshwater Emergent Wetland": "#7fc31c",
            "Freshwater Pond": "#688cc0",
            "Estuarine and Marine Wetland": "#66c2a5",
            "Riverine": "#0190bf",
            "Lake": "#13007c",
            "Estuarine and Marine Deepwater": "#007c88",
            "Other": "#b28656",
        }

        def nwi_color(feature):
            return {
                "color": "black",
                "fillColor": (
                    nwi[feature["properties"][col_name]]
                    if feature["properties"][col_name] in nwi
                    else "gray"
                ),
                "fillOpacity": 0.6,
                "weight": 1,
            }

        if style_callback is None:
            style_callback = nwi_color

        if isinstance(data, str):
            self.add_vector(
                data, style_callback=style_callback, layer_name=layer_name, **kwargs
            )
        else:
            self.add_gdf(
                data, style_callback=style_callback, layer_name=layer_name, **kwargs
            )
        if add_legend:
            self.add_legend(title="Wetland Type", builtin_legend="NWI")


# The functions below are outside the Map class.


class ImageOverlay(ipyleaflet.ImageOverlay):
    """ImageOverlay class.

    Args:
        url (str): http URL or local file path to the image.
        bounds (tuple): bounding box of the image in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
    """

    def __init__(self, **kwargs):
        from base64 import b64encode
        from PIL import Image, ImageSequence
        from io import BytesIO

        try:
            url = kwargs.get("url")
            if not url.startswith("http"):
                url = os.path.abspath(url)
                if not os.path.exists(url):
                    raise FileNotFoundError("The provided file does not exist.")

                ext = os.path.splitext(url)[1][1:]  # file extension
                image = Image.open(url)

                f = BytesIO()
                if ext.lower() == "gif":
                    frames = []
                    # Loop over each frame in the animated image
                    for frame in ImageSequence.Iterator(image):
                        frame = frame.convert("RGBA")
                        b = BytesIO()
                        frame.save(b, format="gif")
                        frame = Image.open(b)
                        frames.append(frame)
                    frames[0].save(
                        f,
                        format="GIF",
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                    )
                else:
                    image.save(f, ext)

                data = b64encode(f.getvalue())
                data = data.decode("ascii")
                url = "data:image/{};base64,".format(ext) + data
                kwargs["url"] = url
        except Exception as e:
            raise Exception(e)

        super().__init__(**kwargs)


def linked_maps(
    rows: int = 2,
    cols: int = 2,
    height: Optional[str] = "400px",
    layers: list = [],
    labels: list = [],
    label_position: Optional[str] = "topright",
    layer_args: list = [],
    **kwargs,
):
    """Create linked maps of XYZ tile layers.

    Args:
        rows (int, optional): The number of rows of maps to create. Defaults to 2.
        cols (int, optional): The number of columns of maps to create. Defaults to 2.
        height (str, optional): The height of each map in pixels. Defaults to "400px".
        layers (list, optional): The list of layers to use for each map. Defaults to [].
        labels (list, optional): The list of labels to show on the map. Defaults to [].
        label_position (str, optional): The position of the label, can be [topleft, topright, bottomleft, bottomright]. Defaults to "topright".

    Raises:
        ValueError: If the length of ee_objects is not equal to rows*cols.
        ValueError: If the length of labels is not equal to rows*cols.

    Returns:
        ipywidget: A GridspecLayout widget.
    """

    if skip_mkdocs_build():
        return

    grid = widgets.GridspecLayout(rows, cols, grid_gap="0px")
    count = rows * cols

    maps = []

    if len(layers) > 0:
        if len(layers) == 1:
            layers = layers * count
        elif len(layers) < count:
            raise ValueError(f"The length of layers must be equal to {count}.")

    if len(labels) > 0:
        labels = labels.copy()
        if len(labels) == 1:
            labels = labels * count
        elif len(labels) < count:
            raise ValueError(f"The length of labels must be equal to {count}.")

    if len(layer_args) > 0:
        if len(layer_args) == 1:
            layer_args = layer_args * count
        elif len(layer_args) < count:
            raise ValueError(f"The length of layer_args must be equal to {count}.")
    else:
        layer_args = [{}] * count

    for i in range(rows):
        for j in range(cols):
            index = i * cols + j

            if "draw_control" not in kwargs:
                kwargs["draw_control"] = False
            if "toolbar_control" not in kwargs:
                kwargs["toolbar_control"] = False
            if "measure_control" not in kwargs:
                kwargs["measure_control"] = False
            if "fullscreen_control" not in kwargs:
                kwargs["fullscreen_control"] = False

            m = Map(
                height=height,
                layout=widgets.Layout(margin="0px", padding="0px"),
                **kwargs,
            )

            if layers[index] in basemaps.keys():
                layers[index] = get_basemap(layers[index])
            elif isinstance(layers[index], str):
                if layers[index].startswith("http") and layers[index].endswith(".tif"):
                    url = cog_tile(layers[index], **layer_args[index])
                    layers[index] = ipyleaflet.TileLayer(
                        url=url,
                        name="Left Layer",
                        attribution=" ",
                    )
                elif os.path.exists(layers[index]):
                    layers[index], left_client = get_local_tile_layer(
                        layers[index],
                        tile_format="ipyleaflet",
                        return_client=True,
                        **layer_args[index],
                    )
                else:
                    layers[index] = ipyleaflet.TileLayer(
                        url=layers[index],
                        name="Left Layer",
                        attribution=" ",
                        **layer_args[index],
                    )
            elif isinstance(layers[index], ipyleaflet.TileLayer):
                pass
            else:
                raise ValueError(
                    f"layers[index] must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            m.add(layers[index])

            if len(labels) > 0:
                label = widgets.Label(
                    labels[index], layout=widgets.Layout(padding="0px 5px 0px 5px")
                )
                control = ipyleaflet.WidgetControl(
                    widget=label, position=label_position
                )
                m.add(control)

            maps.append(m)
            widgets.jslink((maps[0], "center"), (m, "center"))
            widgets.jslink((maps[0], "zoom"), (m, "zoom"))

            output = widgets.Output()
            with output:
                display(m)
            grid[i, j] = output

    return grid


def split_map(
    left_layer: Optional[str] = "TERRAIN",
    right_layer: Optional[str] = "OpenTopoMap",
    left_args: Optional[dict] = {},
    right_args: Optional[dict] = {},
    **kwargs,
) -> None:
    """Adds split map.

    Args:
        left_layer (str, optional): The left tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'TERRAIN'.
        right_layer (str, optional): The right tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'OpenTopoMap'.
        left_args (dict, optional): The arguments for the left tile layer. Defaults to {}.
        right_args (dict, optional): The arguments for the right tile layer. Defaults to {}.
        kwargs (dict, optional): The arguments for the Map widget. Defaults to {}.
    """

    if "draw_control" not in kwargs:
        kwargs["draw_control"] = False
    if "toolbar_control" not in kwargs:
        kwargs["toolbar_control"] = False
    if "measure_control" not in kwargs:
        kwargs["measure_control"] = False
    if "fullscreen_control" not in kwargs:
        kwargs["fullscreen_control"] = False
    if "scale_control" not in kwargs:
        kwargs["scale_control"] = False
    if "search_control" not in kwargs:
        kwargs["search_control"] = False

    m = Map(**kwargs)

    if "max_zoom" not in left_args:
        left_args["max_zoom"] = 30
    if "max_native_zoom" not in left_args:
        left_args["max_native_zoom"] = 30

    if "max_zoom" not in right_args:
        right_args["max_zoom"] = 30
    if "max_native_zoom" not in right_args:
        right_args["max_native_zoom"] = 30

    if "layer_name" not in left_args:
        left_args["layer_name"] = "Left Layer"

    if "layer_name" not in right_args:
        right_args["layer_name"] = "Right Layer"

    bounds = None

    try:
        if left_layer in basemaps.keys():
            left_layer = get_basemap(left_layer)
        elif isinstance(left_layer, str):
            if left_layer.startswith("http") and left_layer.endswith(".tif"):
                url = cog_tile(left_layer, **left_args)
                bbox = cog_bounds(left_layer)
                bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                left_layer = ipyleaflet.TileLayer(
                    url=url,
                    name="Left Layer",
                    attribution=" ",
                )
            elif left_layer.startswith("http") and left_layer.endswith(".geojson"):
                if "max_zoom" in left_args:
                    del left_args["max_zoom"]
                if "max_native_zoom" in left_args:
                    del left_args["max_native_zoom"]
                left_layer = geojson_layer(left_layer, **left_args)
            elif os.path.exists(left_layer):
                if left_layer.endswith(".geojson"):
                    if "max_zoom" in left_args:
                        del left_args["max_zoom"]
                    if "max_native_zoom" in left_args:
                        del left_args["max_native_zoom"]
                    left_layer = geojson_layer(left_layer, **left_args)
                else:
                    left_layer, left_client = get_local_tile_layer(
                        left_layer,
                        tile_format="ipyleaflet",
                        return_client=True,
                        **left_args,
                    )
                    bounds = image_bounds(left_client)
            else:
                left_layer = ipyleaflet.TileLayer(
                    url=left_layer,
                    name="Left Layer",
                    attribution=" ",
                    **left_args,
                )
        elif isinstance(left_layer, ipyleaflet.TileLayer) or isinstance(
            left_layer, ipyleaflet.GeoJSON
        ):
            pass
        else:
            raise ValueError(
                f"left_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
            )

        if right_layer in basemaps.keys():
            right_layer = get_basemap(right_layer)
        elif isinstance(right_layer, str):
            if right_layer.startswith("http") and right_layer.endswith(".tif"):
                url = cog_tile(
                    right_layer,
                    **right_args,
                )
                bbox = cog_bounds(right_layer)
                bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                right_layer = ipyleaflet.TileLayer(
                    url=url,
                    name="Right Layer",
                    attribution=" ",
                )
            elif right_layer.startswith("http") and right_layer.endswith(".geojson"):
                if "max_zoom" in right_args:
                    del right_args["max_zoom"]
                if "max_native_zoom" in right_args:
                    del right_args["max_native_zoom"]
                right_layer = geojson_layer(right_layer, **right_args)
            elif os.path.exists(right_layer):
                if "max_zoom" in right_args:
                    del right_args["max_zoom"]
                if "max_native_zoom" in right_args:
                    del right_args["max_native_zoom"]
                if right_layer.endswith(".geojson"):
                    right_layer = geojson_layer(right_layer, **right_args)
                else:
                    right_layer, right_client = get_local_tile_layer(
                        right_layer,
                        tile_format="ipyleaflet",
                        return_client=True,
                        **right_args,
                    )
                    bounds = image_bounds(right_client)
            else:
                right_layer = ipyleaflet.TileLayer(
                    url=right_layer,
                    name="Right Layer",
                    attribution=" ",
                    **right_args,
                )
        elif isinstance(right_layer, ipyleaflet.TileLayer) or isinstance(
            right_layer, ipyleaflet.GeoJSON
        ):
            pass
        else:
            raise ValueError(
                f"right_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
            )
        control = ipyleaflet.SplitMapControl(
            left_layer=left_layer, right_layer=right_layer
        )
        m.add(control)
        if bounds is not None:
            m.fit_bounds(bounds)
        m.dragging = False
        return m

    except Exception as e:
        print("The provided layers are invalid!")
        raise ValueError(e)


def ts_inspector(
    layers_dict: Optional[dict] = None,
    left_name: Optional[str] = None,
    right_name: Optional[str] = None,
    width: Optional[str] = "120px",
    center: list[int] = [40, -100],
    zoom: int = 4,
    **kwargs,
):
    """Creates a time series inspector.

    Args:
        layers_dict (dict, optional): A dictionary of layers to be shown on the map. Defaults to None.
        left_name (str, optional): A name for the left layer. Defaults to None.
        right_name (str, optional): A name for the right layer. Defaults to None.
        width (str, optional): Width of the dropdown list. Defaults to "120px".
        center (list, optional): Center of the map. Defaults to [40, -100].
        zoom (int, optional): Zoom level of the map. Defaults to 4.

    Returns:
        leafmap.Map: The Map instance.
    """
    import ipywidgets as widgets

    add_zoom = True
    add_fullscreen = True

    if "toolbar_control" not in kwargs:
        kwargs["toolbar_control"] = False
    if "draw_control" not in kwargs:
        kwargs["draw_control"] = False
    if "measure_control" not in kwargs:
        kwargs["measure_control"] = False
    if "zoom_control" not in kwargs:
        kwargs["zoom_control"] = False
    else:
        add_zoom = kwargs["zoom_control"]
    if "fullscreen_control" not in kwargs:
        kwargs["fullscreen_control"] = False
    else:
        add_fullscreen = kwargs["fullscreen_control"]

    if layers_dict is None:
        layers_dict = {}
        keys = dict(basemaps).keys()
        for key in keys:
            if basemaps[key]["type"] == "wms":
                pass
            else:
                layers_dict[key] = get_basemap(key)

    keys = list(layers_dict.keys())
    if left_name is None:
        left_name = keys[0]
    if right_name is None:
        right_name = keys[-1]

    left_layer = layers_dict[left_name]
    right_layer = layers_dict[right_name]

    m = Map(center=center, zoom=zoom, **kwargs)
    control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    m.add(control)

    left_dropdown = widgets.Dropdown(
        options=keys, value=left_name, layout=widgets.Layout(width=width)
    )

    left_control = ipyleaflet.WidgetControl(widget=left_dropdown, position="topleft")
    m.add(left_control)

    right_dropdown = widgets.Dropdown(
        options=keys, value=right_name, layout=widgets.Layout(width=width)
    )

    right_control = ipyleaflet.WidgetControl(widget=right_dropdown, position="topright")
    m.add(right_control)

    if add_zoom:
        m.add(ipyleaflet.ZoomControl())
    if add_fullscreen:
        m.add(ipyleaflet.FullScreenControl())

    split_control = None
    for ctrl in m.controls:
        if isinstance(ctrl, ipyleaflet.SplitMapControl):
            split_control = ctrl
            break

    def left_change(change):
        split_control.left_layer.url = layers_dict[left_dropdown.value].url

    left_dropdown.observe(left_change, "value")

    def right_change(change):
        split_control.right_layer.url = layers_dict[right_dropdown.value].url

    right_dropdown.observe(right_change, "value")

    m.dragging = False

    return m


def geojson_layer(
    in_geojson: Union[str, dict],
    layer_name: str = "Untitled",
    style: Optional[dict] = {},
    hover_style: Optional[dict] = {},
    style_callback: Optional[Callable] = None,
    fill_colors: Optional[list[str]] = None,
    encoding: Optional[str] = "utf-8",
) -> None:
    """Adds a GeoJSON file to the map.

    Args:
        in_geojson (str | dict): The file path or http URL to the input GeoJSON
            or a dictionary containing the geojson.
        layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
        style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
        hover_style (dict, optional): Hover style dictionary. Defaults to {}.
        style_callback (function, optional): Styling function that is called for
            each feature, and should return the feature style. This styling
            function takes the feature as argument. Defaults to None.
        fill_colors (list, optional): The random colors to use for filling polygons.
            Defaults to ["black"].
        info_mode (str, optional): Displays the attributes by either on_hover or
            on_click. Any value other than "on_hover" or "on_click" will be
            treated as None. Defaults to "on_hover".
        encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".

    Raises:
        FileNotFoundError: The provided GeoJSON file could not be found.
    """
    import json
    import random
    import requests

    style_callback_only = False

    if len(style) == 0 and style_callback is not None:
        style_callback_only = True

    try:
        if isinstance(in_geojson, str):
            if in_geojson.startswith("http"):
                in_geojson = github_raw_url(in_geojson)
                data = requests.get(in_geojson).json()
            else:
                in_geojson = os.path.abspath(in_geojson)
                if not os.path.exists(in_geojson):
                    raise FileNotFoundError(
                        "The provided GeoJSON file could not be found."
                    )

                with open(in_geojson, encoding=encoding) as f:
                    data = json.load(f)
        elif isinstance(in_geojson, dict):
            data = in_geojson
        else:
            raise TypeError("The input geojson must be a type of str or dict.")
    except Exception as e:
        raise Exception(e)

    if not style:
        style = {
            # "stroke": True,
            "color": "#000000",
            "weight": 1,
            "opacity": 1,
            # "fill": True,
            # "fillColor": "#ffffff",
            "fillOpacity": 0.1,
            # "dashArray": "9"
            # "clickable": True,
        }
    elif "weight" not in style:
        style["weight"] = 1

    if not hover_style:
        hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}

    def random_color(feature):
        return {
            "color": "black",
            "fillColor": random.choice(fill_colors),
        }

    if style_callback is None:
        style_callback = random_color

    if style_callback_only:
        geojson = ipyleaflet.GeoJSON(
            data=data,
            hover_style=hover_style,
            style_callback=style_callback,
            name=layer_name,
        )
    else:
        geojson = ipyleaflet.GeoJSON(
            data=data,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            name=layer_name,
        )

    return geojson


def get_basemap(name: str):
    """Gets a basemap tile layer by name.

    Args:
        name (str): The name of the basemap.

    Returns:
        ipylealfet.TileLayer | ipyleaflet.WMSLayer: The basemap layer.
    """

    if isinstance(name, str):
        if name in basemaps.keys():
            basemap = basemaps[name]
            if basemap["type"] == "xyz":
                layer = ipyleaflet.TileLayer(
                    url=basemap["url"],
                    name=basemap["name"],
                    max_zoom=24,
                    attribution=basemap["attribution"],
                )
            elif basemap["type"] == "wms":
                layer = ipyleaflet.WMSLayer(
                    url=basemap["url"],
                    layers=basemap["layers"],
                    name=basemap["name"],
                    attribution=basemap["attribution"],
                    format=basemap["format"],
                    transparent=basemap["transparent"],
                )
            return layer
        else:
            raise ValueError(
                "Basemap must be a string. Please choose from: "
                + str(list(basemaps.keys()))
            )
    else:
        raise ValueError(
            "Basemap must be a string. Please choose from: "
            + str(list(basemaps.keys()))
        )
