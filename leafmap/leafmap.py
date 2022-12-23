"""Main module."""

import os
import ipyleaflet
from box import Box
from IPython.display import display
from .basemaps import xyz_to_leaflet
from .common import *
from .legends import builtin_legends
from .osm import *
from .pc import *
from . import examples

basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(ipyleaflet.Map):
    """The Map class inherits ipyleaflet.Map. The arguments you can pass to the Map can be found at https://ipyleaflet.readthedocs.io/en/latest/api_reference/map.html. By default, the Map will add OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    def __init__(self, **kwargs):

        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 2

        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 24

        if "scroll_wheel_zoom" not in kwargs:
            kwargs["scroll_wheel_zoom"] = True

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
            self.add_control(ipyleaflet.LayersControl(position="topright"))

        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True
        if kwargs["fullscreen_control"]:
            self.add_control(ipyleaflet.FullScreenControl())

        if "draw_control" not in kwargs:
            kwargs["draw_control"] = True
        if kwargs["draw_control"]:
            draw_control = ipyleaflet.DrawControl(
                marker={"shapeOptions": {"color": "#3388ff"}},
                rectangle={"shapeOptions": {"color": "#3388ff"}},
                circle={"shapeOptions": {"color": "#3388ff"}},
                circlemarker={},
                edit=True,
                remove=True,
                position="topleft",
            )
            self.add_control(draw_control)
            self.draw_control = draw_control

            draw_output = widgets.Output()
            control = ipyleaflet.WidgetControl(
                widget=draw_output, position="bottomright"
            )
            self.add_control(control)

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
                        self.edit_output.clear_output()
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
            kwargs["measure_control"] = True
        if kwargs["measure_control"]:
            self.add_control(ipyleaflet.MeasureControl(position="topleft"))

        if "scale_control" not in kwargs:
            kwargs["scale_control"] = True
        if kwargs["scale_control"]:
            self.add_control(ipyleaflet.ScaleControl(position="bottomleft"))

        self.layers[0].name = "OpenStreetMap"

        if "google_map" not in kwargs:
            pass
        elif kwargs["google_map"] is not None:
            if kwargs["google_map"].upper() == "ROADMAP":
                layer = basemaps["ROADMAP"]
            elif kwargs["google_map"].upper() == "HYBRID":
                layer = basemaps["HYBRID"]
            elif kwargs["google_map"].upper() == "TERRAIN":
                layer = basemaps["TERRAIN"]
            elif kwargs["google_map"].upper() == "SATELLITE":
                layer = basemaps["SATELLITE"]
            else:
                print(
                    f'{kwargs["google_map"]} is invalid. google_map must be one of: ["ROADMAP", "HYBRID", "TERRAIN", "SATELLITE"]. Adding the default ROADMAP.'
                )
                layer = basemaps["ROADMAP"]
            self.add_layer(layer)

        if "toolbar_control" not in kwargs:
            kwargs["toolbar_control"] = True
        if kwargs["toolbar_control"]:
            from .toolbar import main_toolbar

            main_toolbar(self)

        if "use_voila" not in kwargs:
            kwargs["use_voila"] = False

    def set_center(self, lon, lat, zoom=None):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

    def zoom_to_bounds(self, bounds):
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

    def get_scale(self):
        """Returns the approximate pixel scale of the current map view, in meters.

        Returns:
            float: Map resolution in meters.
        """
        import math

        zoom_level = self.zoom
        # Reference: https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
        resolution = 156543.04 * math.cos(0) / math.pow(2, zoom_level)
        return resolution

    def get_layer_names(self):
        """Gets layer names as a list.

        Returns:
            list: A list of layer names.
        """
        layer_names = []

        for layer in list(self.layers):
            if len(layer.name) > 0:
                layer_names.append(layer.name)

        return layer_names

    def add_marker(self, location, **kwargs):
        """Adds a marker to the map. More info about marker at https://ipyleaflet.readthedocs.io/en/latest/api_reference/marker.html.

        Args:
            location (list | tuple): The location of the marker in the format of [lat, lng].

            **kwargs: Keyword arguments for the marker.
        """
        if isinstance(location, list):
            location = tuple(location)
        if isinstance(location, tuple):
            marker = ipyleaflet.Marker(location=location, **kwargs)
            self.add_layer(marker)
        else:
            raise TypeError("The location must be a list or a tuple.")

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'HYBRID'.
        """
        import xyzservices

        try:
            layer_names = self.get_layer_names()
            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                attribution = basemap.attribution
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 22
                layer = ipyleaflet.TileLayer(
                    url=url, name=name, max_zoom=max_zoom, attribution=attribution
                )
                self.add_layer(layer)
            elif basemap in basemaps and basemaps[basemap].name not in layer_names:
                self.add_layer(basemaps[basemap])
            elif basemap in basemaps and basemaps[basemap].name in layer_names:
                print(f"{basemap} has been already added before.")
            else:
                print(
                    "Basemap can only be one of the following:\n  {}".format(
                        "\n  ".join(basemaps.keys())
                    )
                )

        except Exception:
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

    def find_layer_index(self, name):
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

    def add_layer(self, layer):
        """Adds a layer to the map.

        Args:
            layer (ipyleaflet layer): The layer to be added.
        """
        existing_layer = self.find_layer(layer.name)
        if existing_layer is not None:
            self.remove_layer(existing_layer)
        super().add_layer(layer)

    def layer_opacity(self, name, value=1.0):
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
    ):
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
            self.add_layer(wms_layer)

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
        **kwargs,
    ):
        """Adds a TileLayer to the map.

        Args:
            url (str): The URL of the tile layer.
            name (str): The layer name to use for the layer.
            attribution (str): The attribution to use.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 100
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 100
        try:
            tile_layer = ipyleaflet.TileLayer(
                url=url,
                name=name,
                attribution=attribution,
                opacity=opacity,
                visible=shown,
                **kwargs,
            )
            self.add_layer(tile_layer)

        except Exception as e:
            print("Failed to add the specified TileLayer.")
            raise Exception(e)

    def add_vector_tile_layer(
        self,
        url="https://tile.nextzen.org/tilezen/vector/v1/512/all/{z}/{x}/{y}.mvt?api_key=gCZXZglvRQa6sB2z7JzL1w",
        attribution="",
        vector_tile_layer_styles=dict(),
        **kwargs,
    ):
        """Adds a VectorTileLayer to the map.

        Args:
            url (str, optional): The URL of the tile layer. Defaults to 'https://tile.nextzen.org/tilezen/vector/v1/512/all/{z}/{x}/{y}.mvt?api_key=gCZXZglvRQa6sB2z7JzL1w'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            vector_tile_layer_styles (dict,optional): Style dict, specific to the vector tile source.
        """
        try:
            vector_tile_layer = ipyleaflet.VectorTileLayer(
                url=url,
                attribution=attribution,
                vector_tile_layer_styles=vector_tile_layer_styles,
                **kwargs,
            )
            self.add_layer(vector_tile_layer)

        except Exception as e:
            print("Failed to add the specified VectorTileLayer.")
            raise Exception(e)

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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
        fill_colors=["black"],
        info_mode="on_hover",
    ):
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
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        params = {
            "url": url,
            "titizer_endpoint": titiler_endpoint,
            "bounds": bounds,
            "type": "COG",
        }
        self.cog_layer_dict[name] = params

    def add_cog_mosaic(self, **kwargs):
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/giswqs/leafmap/issues/180."
        )

    def add_cog_mosaic_from_file(self, **kwargs):
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/giswqs/leafmap/issues/180."
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
        **kwargs,
    ):
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
        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        if assets is None and bands is not None:
            assets = bands

        params = {
            "url": url,
            "collection": collection,
            "item": item,
            "assets": assets,
            "bounds": bounds,
            "titiler_endpoint": titiler_endpoint,
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
    ):
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

        minimap = ipyleaflet.Map(
            zoom_control=False,
            attribution_control=False,
            zoom=zoom,
            center=self.center,
            layers=[basemaps["ROADMAP"]],
        )
        minimap.layout.width = "150px"
        minimap.layout.height = "150px"
        ipyleaflet.link((minimap, "center"), (self, "center"))
        minimap_control = ipyleaflet.WidgetControl(widget=minimap, position=position)
        self.add_control(minimap_control)

    def add_marker_cluster(self, event="click", add_marker=True):
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
            self.add_layer(marker_cluster)

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
        x="longitude",
        y="latitude",
        radius=10,
        popup=None,
        **kwargs,
    ):
        """Adds a marker cluster to the map. For a list of options, see https://ipyleaflet.readthedocs.io/en/latest/api_reference/circle_marker.html

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            radius (int, optional): The radius of the circle. Defaults to 10.
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.

        """
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data)

        col_names = df.columns.values.tolist()

        if popup is None:
            popup = col_names

        if not isinstance(popup, list):
            popup = [popup]

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        for idx, row in df.iterrows():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(row[p]) + "<br>"
            popup_html = widgets.HTML(html)

            marker = ipyleaflet.CircleMarker(
                location=[row[y], row[x]],
                radius=radius,
                popup=popup_html,
                **kwargs,
            )
            super().add_layer(marker)

    def split_map(
        self,
        left_layer="TERRAIN",
        right_layer="OpenTopoMap",
        left_args={},
        right_args={},
        zoom_control=True,
        fullscreen_control=True,
        add_close_button=False,
        left_label=None,
        right_label=None,
        left_position="bottomleft",
        right_position="bottomright",
        widget_layout=None,
    ):
        """Adds split map.

        Args:
            left_layer (str, optional): The left tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'TERRAIN'.
            right_layer (str, optional): The right tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'OpenTopoMap'.
            left_args (dict, optional): The arguments for the left tile layer. Defaults to {}.
            right_args (dict, optional): The arguments for the right tile layer. Defaults to {}.
        """
        if "max_zoom" not in left_args:
            left_args["max_zoom"] = 100
        if "max_native_zoom" not in left_args:
            left_args["max_native_zoom"] = 100

        if "max_zoom" not in right_args:
            right_args["max_zoom"] = 100
        if "max_native_zoom" not in right_args:
            right_args["max_native_zoom"] = 100

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
                self.add_control(ipyleaflet.ZoomControl())
            if fullscreen_control:
                self.add_control(ipyleaflet.FullScreenControl())

            if left_label is not None:
                left_name = left_label
            else:
                left_name = "Left Layer"

            if right_label is not None:
                right_name = right_label
            else:
                right_name = "Right Layer"

            if left_layer in basemaps.keys():
                left_layer = basemaps[left_layer]
            elif isinstance(left_layer, str):
                if left_layer.startswith("http") and left_layer.endswith(".tif"):
                    url = cog_tile(left_layer, **left_args)
                    bbox = cog_bounds(left_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    left_layer = ipyleaflet.TileLayer(
                        url=url,
                        name=left_name,
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
                        name=left_name,
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
                right_layer = basemaps[right_layer]
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
                        name=right_name,
                        attribution=" ",
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
            else:
                raise ValueError(
                    f"right_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )
            control = ipyleaflet.SplitMapControl(
                left_layer=left_layer, right_layer=right_layer
            )
            self.add_control(control)

            if left_label is not None:
                if widget_layout is None:
                    widget_layout = widgets.Layout(padding="0px 4px 0px 4px")
                left_widget = widgets.HTML(value=left_label, layout=widget_layout)

                left_control = ipyleaflet.WidgetControl(
                    widget=left_widget, position=left_position
                )
                self.add_control(left_control)

            if right_label is not None:

                if widget_layout is None:
                    widget_layout = widgets.Layout(padding="0px 4px 0px 4px")
                right_widget = widgets.HTML(value=right_label, layout=widget_layout)
                right_control = ipyleaflet.WidgetControl(
                    widget=right_widget, position=right_position
                )
                self.add_control(right_control)

            if bounds is not None:
                self.fit_bounds(bounds)

        except Exception as e:
            print("The provided layers are invalid!")
            raise ValueError(e)

    def basemap_demo(self):
        """A demo for using leafmap basemaps."""
        dropdown = widgets.Dropdown(
            options=list(basemaps.keys()),
            value="HYBRID",
            description="Basemaps",
        )

        def on_click(change):
            basemap_name = change["new"]
            old_basemap = self.layers[-1]
            self.substitute_layer(old_basemap, basemaps[basemap_name])

        dropdown.observe(on_click, "value")
        basemap_control = ipyleaflet.WidgetControl(widget=dropdown, position="topright")
        self.add_control(basemap_control)

    def add_legend(
        self,
        title="Legend",
        legend_dict=None,
        labels=None,
        colors=None,
        position="bottomright",
        builtin_legend=None,
        layer_name=None,
        **kwargs,
    ):
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
            self.add_control(legend_control)

        except Exception as e:
            raise Exception(e)

    def add_colorbar(
        self,
        colors,
        vmin=0,
        vmax=1.0,
        index=None,
        caption="",
        categorical=False,
        step=None,
        height="45px",
        transparent_bg=False,
        position="bottomright",
        **kwargs,
    ):
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
            output.clear_output()
            display(colormap)

        self.colorbar = colormap_ctrl
        self.add_control(colormap_ctrl)

    def add_colormap(
        self,
        cmap="gray",
        colors=None,
        discrete=False,
        label=None,
        width=3,
        height=0.25,
        orientation="horizontal",
        vmin=0,
        vmax=1.0,
        axis_off=False,
        show_name=False,
        font_size=8,
        transparent_bg=False,
        position="bottomright",
        **kwargs,
    ):
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
            output.clear_output()
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
        self.add_control(colormap_ctrl)

    def image_overlay(self, url, bounds, name):
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
            self.add_layer(img)
        except Exception as e:
            raise Exception(e)

    def video_overlay(self, url, bounds, layer_name=None, **kwargs):
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
            self.add_layer(video)
        except Exception as e:
            raise Exception(e)

    def to_html(
        self,
        outfile=None,
        title="My Map",
        width="100%",
        height="880px",
        add_layer_control=True,
        **kwargs,
    ):
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
                self.add_control(layer_control)

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

    def to_image(self, outfile=None, monitor=1):
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

    def to_streamlit(self, width=None, height=600, scrolling=False, **kwargs):
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
            import streamlit.components.v1 as components

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

    def toolbar_reset(self):
        """Reset the toolbar so that no tool is selected."""
        toolbar_grid = self.toolbar
        for tool in toolbar_grid.children:
            tool.value = False

    def add_raster(
        self,
        source,
        band=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name="Local COG",
        **kwargs,
    ):
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try running the following code before calling this function:

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
            band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Local COG'.
        """

        tile_layer, tile_client = get_local_tile_layer(
            source,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            layer_name=layer_name,
            return_client=True,
            **kwargs,
        )

        self.add_layer(tile_layer)

        bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
        bounds = (
            bounds[2],
            bounds[0],
            bounds[3],
            bounds[1],
        )  # [minx, miny, maxx, maxy]
        self.zoom_to_bounds(bounds)

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}
        band_names = list(tile_client.metadata()["bands"].keys())
        params = {
            "tile_layer": tile_layer,
            "tile_client": tile_client,
            "band": band,
            "band_names": band_names,
            "bounds": bounds,
            "type": "LOCAL",
        }
        self.cog_layer_dict[layer_name] = params

    add_local_tile = add_raster

    def add_remote_tile(
        self,
        source,
        band=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name=None,
        **kwargs,
    ):
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
        filename,
        variables=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name="NetCDF layer",
        shift_lon=True,
        lat="lat",
        lon="lon",
        lev="lev",
        level_index=0,
        time=0,
        **kwargs,
    ):
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

    def add_raster_legacy(
        self,
        image,
        bands=None,
        layer_name=None,
        colormap=None,
        x_dim="x",
        y_dim="y",
        fit_bounds=True,
    ):
        """Adds a local raster dataset to the map.

        Args:
            image (str): The image file path.
            bands (int or list, optional): The image bands to use. It can be either a number (e.g., 1) or a list (e.g., [3, 2, 1]). Defaults to None.
            layer_name (str, optional): The layer name to use for the raster. Defaults to None.
            colormap (str, optional): The name of the colormap to use for the raster, such as 'gray' and 'terrain'. More can be found at https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html. Defaults to None.
            x_dim (str, optional): The x dimension. Defaults to 'x'.
            y_dim (str, optional): The y dimension. Defaults to 'y'.
            fit_bounds (bool, optional): Whether to fit map bounds to raster bounds.  Defaults to True.
        """
        try:
            import xarray_leaflet

        except Exception:
            # import platform
            # if platform.system() != "Windows":
            #     # install_from_github(
            #     #     url='https://github.com/davidbrochart/xarray_leaflet')
            #     check_install('xarray_leaflet')
            #     import xarray_leaflet
            # else:
            raise ImportError(
                "You need to install xarray_leaflet first. See https://github.com/davidbrochart/xarray_leaflet"
            )

        import warnings
        import numpy as np
        import rioxarray

        # import xarray as xr
        import matplotlib.pyplot as plt

        warnings.simplefilter("ignore")

        if not os.path.exists(image):
            print("The image file does not exist.")
            return

        if colormap is None:
            colormap = plt.cm.inferno

        if layer_name is None:
            layer_name = "Layer_" + random_string()

        if isinstance(colormap, str):
            colormap = plt.cm.get_cmap(name=colormap)

        da = rioxarray.open_rasterio(image, masked=True)

        # print(da.rio.nodata)

        multi_band = False
        if len(da.band) > 1:
            multi_band = True
            if bands is None:
                bands = [3, 2, 1]
        else:
            bands = 1

        if multi_band:
            da = da.rio.write_nodata(0)
        else:
            da = da.rio.write_nodata(np.nan)
        da = da.sel(band=bands)

        # crs = da.rio.crs
        # nan = da.attrs['nodatavals'][0]
        # da = da / da.max()
        # # if multi_band:
        # da = xr.where(da == nan, np.nan, da)
        # da = da.rio.write_nodata(0)
        # da = da.rio.write_crs(crs)

        if multi_band and type(bands) == list:
            layer = da.leaflet.plot(
                self, x_dim=x_dim, y_dim=y_dim, rgb_dim="band", fit_bounds=fit_bounds
            )
        else:
            layer = da.leaflet.plot(
                self, x_dim=x_dim, y_dim=y_dim, colormap=colormap, fit_bounds=fit_bounds
            )

        layer.name = layer_name

    def add_shp(
        self,
        in_shp,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        encoding="utf-8",
    ):
        """Adds a shapefile to the map.

        Args:
            in_shp (str): The input file path or HTTP URL (*.zip) to the shapefile.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """

        import glob

        if in_shp.startswith("http") and in_shp.endswith(".zip"):
            out_dir = os.path.abspath("./cache/shp")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            basename = os.path.basename(in_shp)
            filename = os.path.join(out_dir, basename)
            # download_from_url(in_shp, out_dir=out_dir, verbose=False)
            download_file(in_shp, filename)
            files = list(glob.glob(os.path.join(out_dir, "*.shp")))
            if len(files) > 0:
                in_shp = files[0]
            else:
                raise FileNotFoundError(
                    "The downloaded zip file does not contain any shapefile in the root directory."
                )
        else:
            in_shp = os.path.abspath(in_shp)
            if not os.path.exists(in_shp):
                raise FileNotFoundError("The provided shapefile could not be found.")

        geojson = shp_to_geojson(in_shp, encoding=encoding)
        self.add_geojson(
            geojson,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            encoding,
        )

    def add_geojson(
        self,
        in_geojson,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        encoding="utf-8",
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str | dict): The file path or http URL to the input GeoJSON or a dictionary containing the geojson.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
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

                    if is_jupyterlite():
                        import pyodide

                        output = os.path.basename(in_geojson)

                        output = os.path.abspath(output)
                        obj = pyodide.http.open_url(in_geojson)
                        with open(output, "w") as fd:
                            shutil.copyfileobj(obj, fd)
                        with open(output, "r") as fd:
                            data = json.load(fd)
                    else:
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
            self.add_control(info_control)

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

        def update_html(feature, **kwargs):

            value = [
                "<b>{}: </b>{}<br>".format(prop, feature["properties"][prop])
                for prop in feature["properties"].keys()
            ][:-1]

            value = """{}""".format("".join(value))
            html.value = value

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

        if info_mode == "on_hover":
            geojson.on_hover(update_html)
        elif info_mode == "on_click":
            geojson.on_click(update_html)

        self.add_layer(geojson)
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

    def add_search_control(
        self, url, marker=None, zoom=None, position="topleft", **kwargs
    ):
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
        self.add_control(search_control)
        self.search_control = search_control

    def add_gdf(
        self,
        gdf,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        zoom_to_layer=True,
        encoding="utf-8",
    ):
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
            encoding (str, optional): The encoding of the GeoDataFrame. Defaults to "utf-8".
        """

        data = gdf_to_geojson(gdf, epsg="4326")

        self.add_geojson(
            data,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            encoding,
        )

        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            self.fit_bounds([[south, east], [north, west]])

    def add_gdf_from_postgis(
        self,
        sql,
        con,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        zoom_to_layer=True,
        **kwargs,
    ):
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
        in_kml,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path or HTTP URL to the KML.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

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
        )

    def add_vector(
        self,
        filename,
        layer_name="Untitled",
        bbox=None,
        mask=None,
        rows=None,
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        encoding="utf-8",
        **kwargs,
    ):
        """Adds any geopandas-supported vector dataset to the map.

        Args:
            filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
            layer_name (str, optional): The layer name to use. Defaults to "Untitled".
            bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
            mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
            rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding to use to read the file. Defaults to "utf-8".

        """
        if not filename.startswith("http"):
            filename = os.path.abspath(filename)
        else:
            filename = github_raw_url(filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".shp":
            self.add_shp(
                filename,
                layer_name,
                style,
                hover_style,
                style_callback,
                fill_colors,
                info_mode,
                encoding,
            )
        elif ext in [".json", ".geojson"]:
            self.add_geojson(
                filename,
                layer_name,
                style,
                hover_style,
                style_callback,
                fill_colors,
                info_mode,
                encoding,
            )
        else:
            geojson = vector_to_geojson(
                filename,
                bbox=bbox,
                mask=mask,
                rows=rows,
                epsg="4326",
                **kwargs,
            )

            self.add_geojson(
                geojson,
                layer_name,
                style,
                hover_style,
                style_callback,
                fill_colors,
                info_mode,
                encoding,
            )

    def add_xy_data(
        self,
        in_csv,
        x="longitude",
        y="latitude",
        label=None,
        layer_name="Marker cluster",
    ):
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
        self.add_layer(marker_cluster)

        self.default_style = {"cursor": "default"}

    def add_point_layer(
        self, filename, popup=None, layer_name="Marker Cluster", **kwargs
    ):
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
        self.add_layer(marker_cluster)

        self.default_style = {"cursor": "default"}

    def add_points_from_xy(
        self,
        data,
        x="longitude",
        y="latitude",
        popup=None,
        layer_name="Marker Cluster",
        color_column=None,
        marker_colors=None,
        icon_colors=["white"],
        icon_names=["info"],
        spin=False,
        add_legend=True,
        **kwargs,
    ):
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
        else:
            df = pd.read_csv(data)

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

        marker_cluster = ipyleaflet.MarkerCluster(markers=markers, name=layer_name)
        self.add_layer(marker_cluster)

        if items is not None and add_legend:
            marker_colors = [check_color(c) for c in marker_colors]
            self.add_legend(
                title=color_column.title(), colors=marker_colors, labels=items
            )

        self.default_style = {"cursor": "default"}

    def add_heatmap(
        self,
        data,
        latitude="latitude",
        longitude="longitude",
        value="value",
        name="Heat map",
        radius=25,
        **kwargs,
    ):
        """Adds a heat map to the map. Reference: https://ipyleaflet.readthedocs.io/en/latest/api_reference/heatmap.html

        Args:
            data (str | list | pd.DataFrame): File path or HTTP URL to the input file or a list of data points in the format of [[x1, y1, z1], [x2, y2, z2]]. For example, https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/world_cities.csv
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
            self.add_layer(heatmap)

        except Exception as e:
            raise Exception(e)

    def add_labels(
        self,
        data,
        column,
        font_size="12pt",
        font_color="black",
        font_family="arial",
        font_weight="normal",
        x="longitude",
        y="latitude",
        draggable=True,
        layer_name="Labels",
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
        self.add_layer(layer_group)
        self.labels = layer_group

    def remove_labels(self):
        """Removes all labels from the map."""
        if hasattr(self, "labels"):
            self.remove_layer(self.labels)
            delattr(self, "labels")

    def add_planet_by_month(
        self,
        year=2016,
        month=1,
        layer_name=None,
        api_key=None,
        token_name="PLANET_API_KEY",
        **kwargs,
    ):
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
        self.add_layer(layer)

    def add_planet_by_quarter(
        self,
        year=2016,
        quarter=1,
        layer_name=None,
        api_key=None,
        token_name="PLANET_API_KEY",
        **kwargs,
    ):
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
        self.add_layer(layer)

    def add_time_slider(
        self,
        layers_dict={},
        labels=None,
        time_interval=1,
        position="bottomright",
        slider_length="150px",
    ):
        """Adds a time slider to the map.

        Args:
            layers_dict (dict, optional): The dictionary containing a set of XYZ tile layers.
            labels (list, optional): The list of labels to be used for the time series. Defaults to None.
            time_interval (int, optional): Time interval in seconds. Defaults to 1.
            position (str, optional): Position to place the time slider, can be any of ['topleft', 'topright', 'bottomleft', 'bottomright']. Defaults to "bottomright".
            slider_length (str, optional): Length of the time slider. Defaults to "150px".

        """
        from .toolbar import time_slider

        time_slider(self, layers_dict, labels, time_interval, position, slider_length)

    def static_map(self, width=950, height=600, out_file=None, **kwargs):
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
            display_html(src=out_file, width=width, height=height)
        else:
            raise TypeError("The provided map is not an ipyleaflet map.")

    def add_census_data(self, wms, layer, census_dict=None, **kwargs):
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

    def add_xyz_service(self, provider, **kwargs):
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

    def add_title(self, title, align="center", font_size="16px", style=None, **kwargs):
        print("The ipyleaflet map does not support titles.")

    def get_pc_collections(self):
        """Get the list of Microsoft Planetary Computer collections."""
        if not hasattr(self, "pc_collections"):
            setattr(self, "pc_collections", get_pc_collections())

    def save_draw_features(self, out_file, indent=4, **kwargs):
        """Save the draw features to a file.

        Args:
            out_file (str): The output file path.
            indent (int, optional): The indentation level when saving data as a GeoJSON. Defaults to 4.
        """
        import json

        out_file = check_file_path(out_file)
        ext = os.path.splitext(out_file)[1].lower()
        if ext == ".geojson":
            out_geojson = out_file
        else:
            out_geojson = os.path.splitext(out_file)[1] + ".geojson"

        self.update_draw_features()
        geojson = {
            "type": "FeatureCollection",
            "features": self.draw_features,
        }
        with open(out_geojson, "w") as f:
            if indent is None:
                json.dump(geojson, f, **kwargs)
            else:
                json.dump(geojson, f, indent=indent, **kwargs)

        if ext == ".geojson":
            pass
        elif ext in [".shp", ".gpkg"]:

            if ext == ".shp":
                geojson_to_shp(geojson, out_file)
            else:
                geojson_to_gpkg(geojson, out_file)
            os.remove(out_geojson)

    def update_draw_features(self):
        """Update the draw features by removing features that have been edited and no longer exist."""

        geometries = [feature["geometry"] for feature in self.draw_control.data]

        for feature in self.draw_features:
            if feature["geometry"] not in geometries:
                self.draw_features.remove(feature)

    def get_draw_props(self, n=None, return_df=False):
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

    def update_draw_props(self, df):
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

    def edit_vector(self, data, **kwargs):
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
        data,
        zonal_speed,
        meridional_speed,
        latitude_dimension="lat",
        longitude_dimension="lon",
        level_dimension="lev",
        level_index=0,
        time_index=0,
        velocity_scale=0.01,
        max_velocity=20,
        display_options={},
        name="Velocity",
    ):
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
        )
        self.add_layer(wind)

    def add_data(
        self,
        data,
        column,
        colors=None,
        labels=None,
        cmap=None,
        scheme="Quantiles",
        k=5,
        add_legend=True,
        legend_title=None,
        legend_position="bottomright",
        legend_kwds=None,
        classification_kwds=None,
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
        info_mode="on_hover",
        encoding="utf-8",
        **kwargs,
    ):
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

    def user_roi_bounds(self, decimals=4):
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

    def add_widget(self, content, position="bottomright", **kwargs):
        """Add a widget (e.g., text, HTML, figure) to the map.

        Args:
            content (str | ipywidgets.Widget | object): The widget to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
            **kwargs: Other keyword arguments for ipywidgets.HTML().
        """

        allowed_positions = ["topleft", "topright", "bottomleft", "bottomright"]

        if position not in allowed_positions:
            raise Exception(f"position must be one of {allowed_positions}")

        if "layout" not in kwargs:
            kwargs["layout"] = widgets.Layout(padding="0px 4px 0px 4px")
        try:
            if isinstance(content, str):
                widget = widgets.HTML(value=content, **kwargs)
                control = ipyleaflet.WidgetControl(widget=widget, position=position)
            else:
                output = widgets.Output(**kwargs)
                with output:
                    display(content)
                control = ipyleaflet.WidgetControl(widget=output, position=position)
            self.add_control(control)

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

    def add_html(self, html, position="bottomright", **kwargs):
        """Add HTML to the map.

        Args:
            html (str): The HTML to add.
            position (str, optional): The position of the HTML, can be one of "topleft",
                "topright", "bottomleft", "bottomright". Defaults to "bottomright".
        """
        self.add_widget(html, position=position, **kwargs)

    def add_text(
        self,
        text,
        fontsize=20,
        fontcolor="black",
        bold=False,
        padding="5px",
        background=True,
        bg_color="white",
        border_radius="5px",
        position="bottomright",
        **kwargs,
    ):
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
    rows=2,
    cols=2,
    height="400px",
    layers=[],
    labels=[],
    label_position="topright",
    layer_args=[],
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
                layers[index] = basemaps[layers[index]]
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

            m.add_layer(layers[index])

            if len(labels) > 0:
                label = widgets.Label(
                    labels[index], layout=widgets.Layout(padding="0px 5px 0px 5px")
                )
                control = ipyleaflet.WidgetControl(
                    widget=label, position=label_position
                )
                m.add_control(control)

            maps.append(m)
            widgets.jslink((maps[0], "center"), (m, "center"))
            widgets.jslink((maps[0], "zoom"), (m, "zoom"))

            output = widgets.Output()
            with output:
                display(m)
            grid[i, j] = output

    return grid


def split_map(
    left_layer="TERRAIN",
    right_layer="OpenTopoMap",
    left_args={},
    right_args={},
    **kwargs,
):
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

    m = Map(**kwargs)

    if "max_zoom" not in left_args:
        left_args["max_zoom"] = 100
    if "max_native_zoom" not in left_args:
        left_args["max_native_zoom"] = 100

    if "max_zoom" not in right_args:
        right_args["max_zoom"] = 100
    if "max_native_zoom" not in right_args:
        right_args["max_native_zoom"] = 100

    if "layer_name" not in left_args:
        left_args["layer_name"] = "Left Layer"

    if "layer_name" not in right_args:
        right_args["layer_name"] = "Right Layer"

    bounds = None

    try:
        if left_layer in basemaps.keys():
            left_layer = basemaps[left_layer]
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
            right_layer = basemaps[right_layer]
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
        m.add_control(control)
        if bounds is not None:
            m.fit_bounds(bounds)
        return m

    except Exception as e:
        print("The provided layers are invalid!")
        raise ValueError(e)


def ts_inspector(
    layers_dict=None,
    left_name=None,
    right_name=None,
    width="120px",
    center=[40, -100],
    zoom=4,
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
            if isinstance(basemaps[key], ipyleaflet.WMSLayer):
                pass
            else:
                layers_dict[key] = basemaps[key]

    keys = list(layers_dict.keys())
    if left_name is None:
        left_name = keys[0]
    if right_name is None:
        right_name = keys[-1]

    left_layer = layers_dict[left_name]
    right_layer = layers_dict[right_name]

    m = Map(center=center, zoom=zoom, **kwargs)
    control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    m.add_control(control)

    left_dropdown = widgets.Dropdown(
        options=keys, value=left_name, layout=widgets.Layout(width=width)
    )

    left_control = ipyleaflet.WidgetControl(widget=left_dropdown, position="topleft")
    m.add_control(left_control)

    right_dropdown = widgets.Dropdown(
        options=keys, value=right_name, layout=widgets.Layout(width=width)
    )

    right_control = ipyleaflet.WidgetControl(widget=right_dropdown, position="topright")
    m.add_control(right_control)

    if add_zoom:
        m.add_control(ipyleaflet.ZoomControl())
    if add_fullscreen:
        m.add_control(ipyleaflet.FullScreenControl())

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

    return m


def geojson_layer(
    in_geojson,
    layer_name="Untitled",
    style={},
    hover_style={},
    style_callback=None,
    fill_colors=["black"],
    encoding="utf-8",
):
    """Adds a GeoJSON file to the map.

    Args:
        in_geojson (str | dict): The file path or http URL to the input GeoJSON or a dictionary containing the geojson.
        layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
        style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
        hover_style (dict, optional): Hover style dictionary. Defaults to {}.
        style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
        fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
        info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
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
