import os
import folium
from folium import plugins
from .common import *
from .legends import builtin_legends
from .basemaps import folium_basemaps
from .osm import *


class Map(folium.Map):
    """The Map class inherits folium.Map. By default, the Map will add Google Maps as the basemap.

    Returns:
        object: folium map object.
    """

    def __init__(self, **kwargs):

        # Default map center location and zoom level
        latlon = [40, -100]
        zoom = 4

        # Interchangeable parameters between ipyleaflet and folium
        if "center" in kwargs:
            kwargs["location"] = kwargs["center"]
            kwargs.pop("center")
        if "location" in kwargs:
            latlon = kwargs["location"]
        else:
            kwargs["location"] = latlon

        if "zoom" in kwargs:
            kwargs["zoom_start"] = kwargs["zoom"]
            kwargs.pop("zoom")
        if "zoom_start" in kwargs:
            zoom = kwargs["zoom_start"]
        else:
            kwargs["zoom_start"] = zoom

        if "control_scale" not in kwargs:
            kwargs["control_scale"] = True

        if "draw_export" not in kwargs:
            kwargs["draw_export"] = False

        if "height" in kwargs and isinstance(kwargs["height"], str):
            kwargs["height"] = float(kwargs["height"].replace("px", ""))

        if "width" in kwargs and isinstance(kwargs["width"], str):
            kwargs["width"] = float(kwargs["width"].replace("px", ""))

        height = None
        width = None

        if "height" in kwargs:
            height = kwargs.pop("height")

        if "width" in kwargs:
            width = kwargs.pop("width")

        super().__init__(**kwargs)
        self.baseclass = "folium"

        if (height is not None) or (width is not None):
            f = folium.Figure(width=width, height=height)
            self.add_to(f)

        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True
        if kwargs["fullscreen_control"]:
            plugins.Fullscreen().add_to(self)

        if "draw_control" not in kwargs:
            kwargs["draw_control"] = True
        if kwargs["draw_control"]:
            plugins.Draw(export=kwargs.get("draw_export")).add_to(self)

        if "measure_control" not in kwargs:
            kwargs["measure_control"] = True
        if kwargs["measure_control"]:
            plugins.MeasureControl(position="bottomleft").add_to(self)

        if "latlon_control" not in kwargs:
            kwargs["latlon_control"] = True
        if kwargs["latlon_control"]:
            folium.LatLngPopup().add_to(self)

        if "minimap_control" not in kwargs:
            kwargs["minimap_control"] = False
        if kwargs["minimap_control"]:
            plugins.MiniMap().add_to(self)

        if "google_map" not in kwargs:
            layer = folium.TileLayer(
                tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                attr="Google",
                name="Google Maps",
                overlay=True,
                control=True,
            )
            layer.add_to(self)
        elif kwargs["google_map"] is None:
            pass
        else:
            if kwargs["google_map"].upper() == "ROADMAP":
                layer = folium.TileLayer(
                    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                    attr="Google",
                    name="Google Maps",
                    overlay=True,
                    control=True,
                )
            elif kwargs["google_map"].upper() == "HYBRID":
                layer = folium.TileLayer(
                    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                    attr="Google",
                    name="Google Satellite",
                    overlay=True,
                    control=True,
                )
            elif kwargs["google_map"].upper() == "TERRAIN":
                layer = folium.TileLayer(
                    tiles="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
                    attr="Google",
                    name="Google Terrain",
                    overlay=True,
                    control=True,
                )
            elif kwargs["google_map"].upper() == "SATELLITE":
                layer = folium.TileLayer(
                    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                    attr="Google",
                    name="Google Satellite",
                    overlay=True,
                    control=True,
                )
            else:
                print(
                    f'{kwargs["google_map"]} is invalid. google_map must be one of: ["ROADMAP", "HYBRID", "TERRAIN", "SATELLITE"]. Adding the default ROADMAP.'
                )
                layer = folium.TileLayer(
                    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                    attr="Google",
                    name="Google Maps",
                    overlay=True,
                    control=True,
                )
            layer.add_to(self)

        if "layers_control" not in kwargs:
            self.options["layersControl"] = True
        else:
            self.options["layersControl"] = kwargs["layers_control"]

        self.fit_bounds([latlon, latlon], max_zoom=zoom)

    def add_layer(self, layer):
        """Adds a layer to the map.

        Args:
            layer (TileLayer): A TileLayer instance.
        """        
        layer.add_to(self)

    def add_layer_control(self):
        """Adds layer control to the map."""
        layer_ctrl = False
        for item in self.to_dict()["children"]:
            if item.startswith("layer_control"):
                layer_ctrl = True
                break
        if not layer_ctrl:
            folium.LayerControl().add_to(self)

    def _repr_mimebundle_(self, **kwargs):
        """Adds Layer control to the map. Referece: https://ipython.readthedocs.io/en/stable/config/integrating.html#MyObject._repr_mimebundle_"""
        if self.options["layersControl"]:
            self.add_layer_control()

    def set_center(self, lon, lat, zoom=10):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to 10.
        """
        self.fit_bounds([[lat, lon], [lat, lon]], max_zoom=zoom)

    def zoom_to_bounds(self, bounds):
        """Zooms to a bounding box in the form of [minx, miny, maxx, maxy].

        Args:
            bounds (list | tuple): A list/tuple containing minx, miny, maxx, maxy values for the bounds.
        """
        #  The folium fit_bounds method takes lat/lon bounds in the form [[south, west], [north, east]].
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def zoom_to_gdf(self, gdf):
        """Zooms to the bounding box of a GeoPandas GeoDataFrame.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        """
        bounds = gdf.total_bounds
        self.zoom_to_bounds(bounds)

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
        """
        try:
            if basemap in folium_basemaps:
                folium_basemaps[basemap].add_to(self)
            else:
                print(
                    "Basemap can only be one of the following: {}".format(
                        ", ".join(folium_basemaps.keys())
                    )
                )
        except Exception:
            raise Exception(
                "Basemap can only be one of the following: {}".format(
                    ", ".join(folium_basemaps.keys())
                )
            )

    def add_wms_layer(
        self,
        url,
        layers,
        name=None,
        attribution="",
        overlay=True,
        control=True,
        shown=True,
        format="image/png",
        transparent=False,
        version="1.1.1",
        styles="",
        **kwargs,
    ):

        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/png'.
            transparent (bool, optional): Whether the layer shall allow transparency. Defaults to False.
            version (str, optional): Version of the WMS service to use. Defaults to "1.1.1".
            styles (str, optional): Comma-separated list of WMS styles. Defaults to "".
        """
        try:
            folium.raster_layers.WmsTileLayer(
                url=url,
                layers=layers,
                name=name,
                attr=attribution,
                overlay=overlay,
                control=control,
                show=shown,
                styles=styles,
                fmt=format,
                transparent=transparent,
                version=version,
                **kwargs,
            ).add_to(self)
        except Exception as e:
            raise Exception(e)

    def add_tile_layer(
        self,
        url,
        name="Untitled",
        attribution=".",
        overlay=True,
        control=True,
        shown=True,
        opacity=1.0,
        API_key=None,
        **kwargs,
    ):
        """Add a XYZ tile layer to the map.

        Args:
            url (str): The URL of the XYZ tile service.
            name (str, optional): The layer name to use on the layer control. Defaults to 'Untitled'.
            attribution (str, optional): The attribution of the data layer. Defaults to '.'.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): Sets the opacity for the layer.
            API_key (str, optional): – API key for Cloudmade or Mapbox tiles. Defaults to True.
        """

        try:
            folium.raster_layers.TileLayer(
                tiles=url,
                name=name,
                attr=attribution,
                overlay=overlay,
                control=control,
                show=shown,
                opacity=opacity,
                API_key=API_key,
                **kwargs,
            ).add_to(self)
        except Exception as e:
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
        pass  # folium can't get map bounds. See https://github.com/python-visualization/folium/issues/1118
        # bounds = self.get_bounds()
        # north, south, east, west = (
        #     bounds[1][0],
        #     bounds[0][0],
        #     bounds[1][1],
        #     bounds[0][1],
        # )

        # gdf = osm_gdf_from_bbox(north, south, east, west, tags)
        # geojson = gdf.__geo_interface__

        # self.add_geojson(
        #     geojson,
        #     layer_name=layer_name,
        #     style=style,
        #     hover_style=hover_style,
        #     style_callback=style_callback,
        #     fill_colors=fill_colors,
        #     info_mode=info_mode,
        # )
        # self.zoom_to_gdf(gdf)

    def add_cog_layer(
        self,
        url,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        titiler_endpoint="https://api.cogeo.xyz/",
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".
        """
        tile_url = get_cog_tile(url, titiler_endpoint, **kwargs)
        center = get_cog_center(url, titiler_endpoint)  # (lon, lat)
        self.add_tile_layer(
            url=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_cog_mosaic(
        self,
        links,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        titiler_endpoint="https://api.cogeo.xyz/",
        username="anonymous",
        overwrite=False,
        show_footprints=False,
        verbose=True,
        **kwargs,
    ):
        """Add a virtual mosaic of COGs to the map.

        Args:
            links (list): A list of links pointing to COGs.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".
            username (str, optional): The username to create mosaic using the titiler endpoint. Defaults to 'anonymous'.
            overwrite (bool, optional): Whether or not to replace existing layer with the same layer name. Defaults to False.
            show_footprints (bool, optional): Whether or not to show footprints of COGs. Defaults to False.
            verbose (bool, optional): Whether or not to print descriptions. Defaults to True.
        """
        layername = name.replace(" ", "_")
        tile = get_cog_mosaic(
            links,
            titiler_endpoint=titiler_endpoint,
            username=username,
            layername=layername,
            overwrite=overwrite,
            verbose=verbose,
        )
        self.add_tile_layer(tile, name, attribution, opacity, shown)

        if show_footprints:
            if verbose:
                print(
                    f"Generating footprints of {len(links)} COGs. This might take a while ..."
                )
            coords = []
            for link in links:
                coord = get_cog_bounds(link)
                if coord is not None:
                    coords.append(coord)
            fc = coords_to_geojson(coords)

            # style_function = lambda x: {'opacity': 1, 'dashArray': '1', 'fillOpacity': 0, 'weight': 1}

            folium.GeoJson(
                data=fc,
                # style_function=style_function,
                name="Footprints",
            ).add_to(self)

            center = get_center(fc)
            if verbose:
                print("The footprint layer has been added.")
        else:
            center = get_cog_center(links[0], titiler_endpoint)

        self.set_center(center[0], center[1], zoom=6)

    def add_stac_layer(
        self,
        url,
        bands=None,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        titiler_endpoint="https://api.cogeo.xyz/",
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".
        """
        tile_url = get_stac_tile(url, bands, titiler_endpoint, **kwargs)
        center = get_stac_center(url, titiler_endpoint)
        self.add_tile_layer(
            url=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_legend(
        self,
        title="Legend",
        colors=None,
        labels=None,
        legend_dict=None,
        builtin_legend=None,
        opacity=1.0,
        **kwargs,
    ):
        """Adds a customized legend to the map. Reference: https://bit.ly/3oV6vnH

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'. Defaults to "Legend".
            colors ([type], optional): A list of legend colors. Defaults to None.
            labels ([type], optional): A list of legend labels. Defaults to None.
            legend_dict ([type], optional): A dictionary containing legend items as keys and color as values. If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            builtin_legend ([type], optional): Name of the builtin legend to add to the map. Defaults to None.
            opacity (float, optional): The opacity of the legend. Defaults to 1.0.

        """

        import pkg_resources
        from branca.element import Template, MacroElement

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("leafmap", "leafmap.py")
        )
        legend_template = os.path.join(pkg_dir, "data/template/legend.txt")

        if not os.path.exists(legend_template):
            raise FileNotFoundError("The legend template does not exist.")

        if labels is not None:
            if not isinstance(labels, list):
                raise ValueError("The legend labels must be a list.")
        else:
            labels = ["One", "Two", "Three", "Four", "ect"]

        if colors is not None:
            if not isinstance(colors, list):
                raise ValueError("The legend colors must be a list.")
            elif all(isinstance(item, tuple) for item in colors):
                try:
                    colors = ["#" + rgb_to_hex(x) for x in colors]
                except Exception as e:
                    raise Exception(e)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                raise ValueError("The legend colors must be a list of tuples.")
        else:
            colors = ["#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3"]

        if len(labels) != len(colors):
            raise ValueError("The legend keys and values must be the same length.")

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            if builtin_legend not in allowed_builtin_legends:
                raise ValueError(
                    "The builtin legend must be one of the following: {}".format(
                        ", ".join(allowed_builtin_legends)
                    )
                )
            else:
                legend_dict = builtin_legends[builtin_legend]
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        raise Exception(e)
                elif all(isinstance(item, str) for item in colors):
                    colors = ["#" + color for color in colors]

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                raise ValueError("The legend dict must be a dictionary.")
            else:
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())

                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = ["#" + rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        raise Exception(e)
                elif all(isinstance(item, str) for item in colors):
                    colors = ["#" + color for color in colors]

        content = []

        with open(legend_template) as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                if index < 36:
                    content.append(line)
                elif index == 36:
                    line = lines[index].replace("Legend", title)
                    content.append(line)
                elif index < 39:
                    content.append(line)
                elif index == 39:
                    for i, color in enumerate(colors):
                        item = f"    <li><span style='background:{check_color(color)};opacity:{opacity};'></span>{labels[i]}</li>\n"
                        content.append(item)
                elif index > 41:
                    content.append(line)

        template = "".join(content)
        macro = MacroElement()
        macro._template = Template(template)

        self.get_root().add_child(macro)

    def add_colorbar(
        self,
        colors,
        vmin=0,
        vmax=1.0,
        index=None,
        caption="",
        categorical=False,
        step=None,
        **kwargs,
    ):
        """Add a colorbar to the map.

        Args:
            colors (list): The set of colors to be used for interpolation. Colors can be provided in the form: * tuples of RGBA ints between 0 and 255 (e.g: (255, 255, 0) or (255, 255, 0, 255)) * tuples of RGBA floats between 0. and 1. (e.g: (1.,1.,0.) or (1., 1., 0., 1.)) * HTML-like string (e.g: “#ffff00) * a color name or shortcut (e.g: “y” or “yellow”)
            vmin (int, optional): The minimal value for the colormap. Values lower than vmin will be bound directly to colors[0].. Defaults to 0.
            vmax (float, optional): The maximal value for the colormap. Values higher than vmax will be bound directly to colors[-1]. Defaults to 1.0.
            index (list, optional):The values corresponding to each color. It has to be sorted, and have the same length as colors. If None, a regular grid between vmin and vmax is created.. Defaults to None.
            caption (str, optional): The caption for the colormap. Defaults to "".
            categorical (bool, optional): Whether or not to create a categorical colormap. Defaults to False.
            step (int, optional): The step to split the LinearColormap into a StepColormap. Defaults to None.
        """
        from box import Box
        from branca.colormap import LinearColormap

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

        self.add_child(colormap)

    def add_shp(self, in_shp, layer_name="Untitled", **kwargs):
        """Adds a shapefile to the map. See https://python-visualization.github.io/folium/modules.html#folium.features.GeoJson for more info about setting style.

        Args:
            in_shp (str): The input file path to the shapefile.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """
        in_shp = os.path.abspath(in_shp)
        if not os.path.exists(in_shp):
            raise FileNotFoundError("The provided shapefile could not be found.")

        data = shp_to_geojson(in_shp)

        geo_json = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geo_json.add_to(self)

    def add_geojson(self, in_geojson, layer_name="Untitled", **kwargs):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str): The input file path to the GeoJSON.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """
        import json
        import requests

        try:

            if isinstance(in_geojson, str):

                if in_geojson.startswith("http"):
                    data = requests.get(in_geojson).json()
                else:
                    in_geojson = os.path.abspath(in_geojson)
                    if not os.path.exists(in_geojson):
                        raise FileNotFoundError(
                            "The provided GeoJSON file could not be found."
                        )

                    with open(in_geojson) as f:
                        data = json.load(f)
            elif isinstance(in_geojson, dict):
                data = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        # interchangable parameters between ipyleaflet and folium.
        if "style" in kwargs:
            kwargs.pop("style")
        if "style_callback" in kwargs:
            if kwargs["style_callback"] is not None:
                kwargs["style_function"] = kwargs["style_callback"]
            kwargs.pop("style_callback")

        if "hover_style" in kwargs:
            if len(kwargs["hover_style"]) > 0:
                kwargs["highlight_function"] = kwargs["hover_style"]
            kwargs.pop("hover_style")
        if "fill_colors" in kwargs:
            kwargs.pop("fill_colors")
        if "info_mode" in kwargs:
            kwargs.pop("info_mode")

        geojson = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geojson.add_to(self)

    def add_gdf(self, gdf, layer_name="Untitled", zoom_to_layer=True, **kwargs):
        """Adds a GeoPandas GeoDataFrameto the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.

        """

        data = gdf_to_geojson(gdf, epsg="4326")

        geojson = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geojson.add_to(self)

        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            self.fit_bounds([[south, east], [north, west]])

    def add_gdf_from_postgis(
        self, sql, con, layer_name="Untitled", zoom_to_layer=True, **kwargs
    ):
        """Adds a GeoPandas GeoDataFrameto the map.

        Args:
            sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
            con (sqlalchemy.engine.Engine): Active connection to the database to query.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.

        """
        if "fill_colors" in kwargs:
            kwargs.pop("fill_colors")
        gdf = read_postgis(sql, con, **kwargs)
        data = gdf_to_geojson(gdf, epsg="4326")

        geojson = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geojson.add_to(self)

        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            self.fit_bounds([[south, east], [north, west]])

    def add_kml(self, in_kml, layer_name="Untitled", **kwargs):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """

        in_kml = os.path.abspath(in_kml)
        if not os.path.exists(in_kml):
            raise FileNotFoundError("The provided KML file could not be found.")

        data = kml_to_geojson(in_kml)

        geo_json = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geo_json.add_to(self)

    def publish(
        self,
        name="Folium Map",
        description="",
        source_url="",
        visibility="PUBLIC",
        open=True,
        tags=None,
        **kwargs,
    ):
        """Publish the map to datapane.com

        Args:
            name (str, optional): The document name - can include spaces, caps, symbols, etc., e.g. "Profit & Loss 2020". Defaults to "Folium Map".
            description (str, optional): A high-level description for the document, this is displayed in searches and thumbnails. Defaults to ''.
            source_url (str, optional): A URL pointing to the source code for the document, e.g. a GitHub repo or a Colab notebook. Defaults to ''.
            visibility (str, optional): Visibility of the map. It can be one of the following: PUBLIC, PRIVATE. Defaults to 'PUBLIC'.
            open (bool, optional): Whether to open the map. Defaults to True.
            tags (bool, optional): A list of tags (as strings) used to categorise your document. Defaults to None.
        """
        import webbrowser

        try:
            import datapane as dp
        except Exception:
            webbrowser.open_new_tab("https://docs.datapane.com/tut-getting-started")
            raise ImportError(
                "The datapane Python package is not installed. You need to install and authenticate datapane first."
            )

        try:

            visibility = visibility.upper()

            if visibility not in ["PUBLIC", "PRIVATE"]:
                raise ValueError(
                    "The visibility argument must be either PUBLIC or PRIVATE."
                )

            if visibility == "PUBLIC":
                visibility = dp.Visibility.PUBLIC
            else:
                visibility = dp.Visibility.PRIVATE

            dp.Report(dp.Plot(self)).publish(
                name=name,
                description=description,
                source_url=source_url,
                visibility=visibility,
                open=open,
                tags=tags,
            )

        except Exception as e:
            raise Exception(e)

    def to_html(self, outfile=None, **kwargs):
        """Exports a map as an HTML file.

        Args:
            outfile (str, optional): File path to the output HTML. Defaults to None.

        Raises:
            ValueError: If it is an invalid HTML file.

        Returns:
            str: A string containing the HTML code.
        """
        if outfile is not None:
            if not outfile.endswith(".html"):
                raise ValueError("The output file extension must be html.")
            outfile = os.path.abspath(outfile)
            out_dir = os.path.dirname(outfile)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            self.save(outfile, **kwargs)
        else:
            outfile = os.path.abspath(random_string() + ".html")
            self.save(outfile, **kwargs)
            out_html = ""
            with open(outfile) as f:
                lines = f.readlines()
                out_html = "".join(lines)
            os.remove(outfile)
            return out_html


def delete_dp_report(name):
    """Deletes a datapane report.

    Args:
        name (str): Name of the report to delete.
    """
    try:
        import datapane as dp

        reports = dp.Report.list()
        items = list(reports)
        names = list(map(lambda item: item["name"], items))
        if name in names:
            report = dp.Report.get(name)
            url = report.blocks[0]["url"]
            # print('Deleting {}...'.format(url))
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        raise Exception(e)


def delete_dp_reports():
    """Deletes all datapane reports."""
    try:
        import datapane as dp

        reports = dp.Report.list()
        for item in reports:
            print(item["name"])
            report = dp.Report.get(item["name"])
            url = report.blocks[0]["url"]
            print("Deleting {}...".format(url))
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        raise Exception(e)
