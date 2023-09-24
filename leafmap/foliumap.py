import os
import folium
import folium.plugins as plugins
from box import Box

from .common import *
from .legends import builtin_legends
from .basemaps import xyz_to_folium
from .osm import *
from . import examples

from branca.element import Figure, JavascriptLink, MacroElement
from folium.elements import JSCSSMixin
from folium.map import Layer
from jinja2 import Template

basemaps = Box(xyz_to_folium(), frozen_box=True)
import pandas as pd
from typing import Optional, Union, Any, Callable, Dict, Tuple


class Map(folium.Map):
    """The Map class inherits folium.Map. By default, the Map will add OpenStreetMap as the basemap.

    Returns:
        object: folium map object.
    """

    def __init__(self, **kwargs):
        # Default map center location and zoom level
        latlon = [20, 0]
        zoom = 2

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
        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 24

        if "scale_control" not in kwargs:
            kwargs["scale_control"] = True

        if kwargs["scale_control"]:
            kwargs["control_scale"] = True
            kwargs.pop("scale_control")

        # if "control_scale" not in kwargs:
        #     kwargs["control_scale"] = True

        if "draw_export" not in kwargs:
            kwargs["draw_export"] = False

        if "height" in kwargs and isinstance(kwargs["height"], str):
            kwargs["height"] = float(kwargs["height"].replace("px", ""))

        if (
            "width" in kwargs
            and isinstance(kwargs["width"], str)
            and ("%" not in kwargs["width"])
        ):
            kwargs["width"] = float(kwargs["width"].replace("px", ""))

        height = None
        width = None

        if "height" in kwargs:
            height = kwargs.pop("height")
        else:
            height = 600

        if "width" in kwargs:
            width = kwargs.pop("width")
        else:
            width = "100%"

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
            kwargs["latlon_control"] = False
        if kwargs["latlon_control"]:
            folium.LatLngPopup().add_to(self)

        if "locate_control" not in kwargs:
            kwargs["locate_control"] = False
        if kwargs["locate_control"]:
            plugins.LocateControl().add_to(self)

        if "minimap_control" not in kwargs:
            kwargs["minimap_control"] = False
        if kwargs["minimap_control"]:
            plugins.MiniMap().add_to(self)

        if "search_control" not in kwargs:
            kwargs["search_control"] = True
        if kwargs["search_control"]:
            plugins.Geocoder(collapsed=True, position="topleft").add_to(self)

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

    def add_pmtiles(
        self,
        url,
        style=None,
        name=None,
        overlay=True,
        control=True,
        show=True,
        zoom_to_layer=True,
        **kwargs,
    ):
        """
        Adds a PMTiles layer to the map.

        Args:
            url (str): The URL of the PMTiles file.
            style (str, optional): The CSS style to apply to the layer. Defaults to None.
                See https://docs.mapbox.com/style-spec/reference/layers/ for more info.
            name (str, optional): The name of the layer. Defaults to None.
            overlay (bool, optional): Whether the layer should be added as an overlay. Defaults to True.
            control (bool, optional): Whether to include the layer in the layer control. Defaults to True.
            show (bool, optional): Whether the layer should be shown initially. Defaults to True.
            zoom_to_layer (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the PMTilesLayer constructor.

        Returns:
            None
        """

        try:
            layer = PMTilesLayer(
                url,
                style=style,
                name=name,
                overlay=overlay,
                control=control,
                show=show,
                **kwargs,
            )
            self.add_child(layer)

            if zoom_to_layer:
                metadata = pmtiles_metadata(url)
                bounds = metadata["bounds"]
                self.zoom_to_bounds(bounds)
        except Exception as e:
            print(e)

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
        """Adds Layer control to the map. Reference: https://ipython.readthedocs.io/en/stable/config/integrating.html#MyObject._repr_mimebundle_"""
        if self.options["layersControl"]:
            self.add_layer_control()

    def set_center(self, lon: float, lat: float, zoom: Optional[int] = 10):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to 10.
        """
        self.fit_bounds([[lat, lon], [lat, lon]], max_zoom=zoom)

        arc_zoom_to_extent(lon, lat, lon, lat)

    def zoom_to_bounds(
        self, bounds: Union[List[float], Tuple[float, float, float, float]]
    ):
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

    def add_basemap(
        self, basemap: Optional[str] = "HYBRID", show: Optional[bool] = True, **kwargs
    ):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
            show (bool, optional): Whether to show the basemap. Defaults to True.
            **kwargs: Additional keyword arguments to pass to folium.TileLayer.
        """
        import xyzservices

        try:
            if basemap in ["ROADMAP", "SATELLITE", "HYBRID", "TERRAIN"]:
                layer = get_google_map(basemap, backend="folium", **kwargs)
                layer.add_to(self)
                return

            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                attribution = basemap.attribution
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 22
                layer = folium.TileLayer(
                    tiles=url,
                    attr=attribution,
                    name=name,
                    max_zoom=max_zoom,
                    overlay=True,
                    control=True,
                    show=show,
                    **kwargs,
                )

                self.add_layer(layer)

                arc_add_layer(url, name)

            elif basemap in basemaps:
                bmap = basemaps[basemap]
                bmap.show = show
                bmap.add_to(self)
                if isinstance(basemaps[basemap], folium.TileLayer):
                    url = basemaps[basemap].tiles
                elif isinstance(basemaps[basemap], folium.WmsTileLayer):
                    url = basemaps[basemap].url
                arc_add_layer(url, basemap)
            else:
                print(
                    "Basemap can only be one of the following: {}".format(
                        ", ".join(basemaps.keys())
                    )
                )

        except Exception:
            raise Exception(
                "Basemap can only be one of the following: {}".format(
                    ", ".join(basemaps.keys())
                )
            )

    def add_wms_layer(
        self,
        url: str,
        layers: str,
        name: Optional[str] = None,
        attribution: Optional[str] = "",
        overlay: Optional[bool] = True,
        control: Optional[bool] = True,
        shown: Optional[bool] = True,
        format: Optional[str] = "image/png",
        transparent: Optional[bool] = True,
        version: Optional[str] = "1.1.1",
        styles: Optional[str] = "",
        **kwargs,
    ):
        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            overlay (bool, optional): Allows overlay. Defaults to True.
            control (bool, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/png'.
            transparent (bool, optional): Whether the layer shall allow transparency. Defaults to True.
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
        url: str,
        name: str,
        attribution: str,
        overlay: Optional[bool] = True,
        control: Optional[bool] = True,
        shown: Optional[bool] = True,
        opacity: Optional[float] = 1.0,
        API_key: Optional[str] = None,
        **kwargs,
    ):
        """Add a XYZ tile layer to the map.

        Args:
            url (str): The URL of the XYZ tile service.
            name (str): The layer name to use on the layer control.
            attribution (str): The attribution of the data layer.
            overlay (bool, optional): Allows overlay. Defaults to True.
            control (bool, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): Sets the opacity for the layer.
            API_key (str, optional): – API key for Cloudmade or Mapbox tiles. Defaults to True.
        """
        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 100
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 100

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

            arc_add_layer(url, name, shown, opacity)

        except Exception as e:
            raise Exception(e)

    def add_raster(
        self,
        source: str,
        band: Optional[int] = None,
        palette: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = "Local COG",
        **kwargs,
    ):
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try installing jupyter-server-proxy using `pip install jupyter-server-proxy`,
            then running the following code before calling this function. For more info, see https://bit.ly/3JbmF93.

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
            tile_format="folium",
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

        arc_add_layer(tile_layer.tiles, layer_name, True, 1.0)
        arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

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
        filename: str,
        variables: Optional[int] = None,
        port: str = "default",
        palette: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = "NetCDF layer",
        shift_lon: Optional[bool] = True,
        lat: Optional[str] = "lat",
        lon: Optional[str] = "lon",
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
        """

        tif, vars = netcdf_to_tif(
            filename, shift_lon=shift_lon, lat=lat, lon=lon, return_vars=True
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

    def add_heatmap(
        self,
        data: Union[str, List[List[float]], pd.DataFrame],
        latitude: Optional[str] = "latitude",
        longitude: Optional[str] = "longitude",
        value: Optional[str] = "value",
        name: Optional[str] = "Heat map",
        radius: Optional[int] = 25,
        **kwargs,
    ):
        """Adds a heat map to the map. Reference: https://stackoverflow.com/a/54756617

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

            plugins.HeatMap(data, name=name, radius=radius, **kwargs).add_to(
                folium.FeatureGroup(name=name).add_to(self)
            )
        except Exception as e:
            raise Exception(e)

    def add_markers_from_xy(
        self,
        data: Union[str, pd.DataFrame],
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        popup: Optional[List[str]] = None,
        min_width: Optional[int] = 100,
        max_width: Optional[int] = 200,
        layer_name: Optional[str] = "Markers",
        icon: Optional[str] = None,
        icon_shape: Optional[str] = "circle-dot",
        border_width: Optional[int] = 3,
        border_color: Optional[str] = "#0000ff",
        **kwargs,
    ):
        """Adds markers to the map from a csv or Pandas DataFrame containing x, y values.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            min_width (int, optional): The minimum width of the popup. Defaults to 100.
            max_width (int, optional): The maximum width of the popup. Defaults to 200.
            layer_name (str, optional): The name of the layer. Defaults to "Marker Cluster".
            icon (str, optional): The Font-Awesome icon name to use to render the marker. Defaults to None.
            icon_shape (str, optional): The shape of the marker, such as "retangle-dot", "circle-dot". Defaults to 'circle-dot'.
            border_width (int, optional): The width of the border. Defaults to 3.
            border_color (str, optional): The color of the border. Defaults to '#0000ff'.
            kwargs (dict, optional): Additional keyword arguments to pass to BeautifyIcon. See
                https://python-visualization.github.io/folium/plugins.html#folium.plugins.BeautifyIcon.

        """
        import pandas as pd
        from folium.plugins import BeautifyIcon

        layer_group = folium.FeatureGroup(name=layer_name)

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data)

        col_names = df.columns.values.tolist()

        if popup is None:
            popup = col_names

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        for row in df.itertuples():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(getattr(row, p)) + "<br>"
            popup_html = folium.Popup(html, min_width=min_width, max_width=max_width)

            marker_icon = BeautifyIcon(
                icon, icon_shape, border_width, border_color, **kwargs
            )
            folium.Marker(
                location=[getattr(row, y), getattr(row, x)],
                popup=popup_html,
                icon=marker_icon,
            ).add_to(layer_group)

        layer_group.add_to(self)

    def add_osm_from_geocode(
        self,
        query: Union[str, dict, List],
        which_result: Optional[int] = None,
        by_osmid: Optional[bool] = False,
        buffer_dist: Optional[float] = None,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        address: str,
        tags: dict,
        dist: Optional[int] = 1000,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        query: Union[str, dict, List],
        tags: dict,
        which_result: Optional[int] = None,
        buffer_dist: Optional[float] = None,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        center_point: Tuple[float, float],
        tags: dict,
        dist: Optional[int] = 1000,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        tags: dict,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        north: float,
        south: float,
        east: float,
        west: float,
        tags: dict,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        tags: dict,
        layer_name: Optional[str] = "Untitled",
        style: Optional[Dict] = {},
        hover_style: Optional[Dict] = {},
        style_callback: Optional[Callable[[Any], Any]] = None,
        fill_colors: Optional[List] = ["black"],
        info_mode: Optional[str] = "on_hover",
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
        url: str,
        name: Optional[str] = "Untitled",
        attribution: Optional[str] = ".",
        opacity: Optional[float] = 1.0,
        shown: Optional[bool] = True,
        bands: Optional[List] = None,
        titiler_endpoint: Optional[str] = None,
        zoom_to_layer=True,
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            bands (list, optional): A list of bands to use. Defaults to None.
            titiler_endpoint (str, optional): TiTiler endpoint. Defaults to "https://titiler.xyz".
            zoom_to_layer (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(
            url=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        if zoom_to_layer:
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

    def add_cog_mosaic(self, **kwargs):
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/opengeos/leafmap/issues/180."
        )

    def add_cog_mosaic_from_file(self, **kwargs):
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/opengeos/leafmap/issues/180."
        )

    def add_stac_layer(
        self,
        url: str = None,
        collection: str = None,
        item: str = None,
        assets: Union[str, List] = None,
        bands: List = None,
        titiler_endpoint: Optional[str] = None,
        name: Optional[str] = "STAC Layer",
        attribution: Optional[str] = ".",
        opacity: Optional[float] = 1.0,
        shown: Optional[bool] = True,
        fit_bounds: Optional[bool] = True,
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
            collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            fit_bounds (bool, optional): A flag indicating whether the map should be zoomed to the layer extent. Defaults to True.
        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(
            url=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )

        if fit_bounds:
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

    def add_mosaic_layer(
        self,
        url: str,
        titiler_endpoint: Optional[str] = None,
        name: Optional[str] = "Mosaic Layer",
        attribution: Optional[str] = ".",
        opacity: Optional[float] = 1.0,
        shown: Optional[bool] = True,
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
        self.add_tile_layer(
            url=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_legend(
        self,
        title: Optional[str] = "Legend",
        labels: Optional[List] = None,
        colors: Optional[List] = None,
        legend_dict: Optional[Dict] = None,
        builtin_legend: Optional[str] = None,
        opacity: Optional[float] = 1.0,
        position: Optional[str] = "bottomright",
        draggable: Optional[bool] = True,
        style: Optional[Dict] = {},
    ):
        """Adds a customized legend to the map. Reference: https://bit.ly/3oV6vnH.
            If you want to add multiple legends to the map, you need to set the `draggable` argument to False.

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'. Defaults to "Legend".
            colors (list, optional): A list of legend colors. Defaults to None.
            labels (list, optional): A list of legend labels. Defaults to None.
            legend_dict (dict, optional): A dictionary containing legend items as keys and color as values.
                If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.
            opacity (float, optional): The opacity of the legend. Defaults to 1.0.
            position (str, optional): The position of the legend, can be one of the following:
                "topleft", "topright", "bottomleft", "bottomright". Defaults to "bottomright".
            draggable (bool, optional): If True, the legend can be dragged to a new position. Defaults to True.
            style: Additional keyword arguments to style the legend, such as position, bottom, right, z-index,
                border, background-color, border-radius, padding, font-size, etc. The default style is:
                style = {
                    'position': 'fixed',
                    'z-index': '9999',
                    'border': '2px solid grey',
                    'background-color': 'rgba(255, 255, 255, 0.8)',
                    'border-radius': '5px',
                    'padding': '10px',
                    'font-size': '14px',
                    'bottom': '20px',
                    'right': '5px'
                }

        """
        content = create_legend(
            title,
            labels,
            colors,
            legend_dict,
            builtin_legend,
            opacity,
            position,
            draggable,
            style=style,
        )
        if draggable:
            from branca.element import Template, MacroElement

            content = (
                '"""\n{% macro html(this, kwargs) %}\n'
                + content
                + '\n{% endmacro %}"""'
            )

            macro = MacroElement()
            macro._template = Template(content)

            self.get_root().add_child(macro)
        else:
            self.add_html(content, position=position)

    def add_colorbar(
        self,
        colors: List,
        vmin: Optional[int] = 0,
        vmax: Optional[int] = 1,
        index: Optional[List] = None,
        caption: Optional[str] = "",
        categorical: Optional[bool] = False,
        step: Optional[int] = None,
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

    def add_shp(
        self,
        in_shp: str,
        layer_name: Optional[str] = "Untitled",
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = True,
        **kwargs,
    ):
        """Adds a shapefile to the map. See https://python-visualization.github.io/folium/modules.html#folium.features.GeoJson for more info about setting style.

        Args:
            in_shp (str): The input file path or HTTP URL (*.zip) to the shapefile.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer. Defaults to True.

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

        data = shp_to_geojson(in_shp)

        self.add_geojson(
            data,
            layer_name=layer_name,
            info_mode=info_mode,
            zoom_to_layer=zoom_to_layer,
            **kwargs,
        )

    def add_geojson(
        self,
        in_geojson: str,
        layer_name: Optional[str] = "Untitled",
        encoding: Optional[str] = "utf-8",
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = True,
        **kwargs,
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str): The input file path to the GeoJSON.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
            info_mode (str, optional): Displays the attributes by either on_hover or on_click.
                Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer. Defaults to True.

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """
        import json
        import requests
        import random

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

        # interchangeable parameters between ipyleaflet and folium.
        style_dict = {}
        if "style_function" not in kwargs:
            if "style" in kwargs:
                style_dict = kwargs["style"]
                if isinstance(kwargs["style"], dict) and len(kwargs["style"]) > 0:
                    kwargs["style_function"] = lambda x: style_dict
                kwargs.pop("style")
            else:
                style_dict = {
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
                kwargs["style_function"] = lambda x: style_dict

        if "style_callback" in kwargs:
            kwargs.pop("style_callback")

        if "hover_style" in kwargs:
            kwargs.pop("hover_style")

        if "fill_colors" in kwargs:
            fill_colors = kwargs["fill_colors"]

            def random_color(feature):
                style_dict["fillColor"] = random.choice(fill_colors)
                return style_dict

            kwargs["style_function"] = random_color
            kwargs.pop("fill_colors")

        if "weight" not in style_dict:
            style_dict["weight"] = 2

        if "highlight_function" not in kwargs:
            kwargs["highlight_function"] = lambda feat: {
                "weight": style_dict["weight"] + 2,
                "fillOpacity": 0,
            }

        tooltip = None
        popup = None
        if info_mode is not None:
            if "fields" in kwargs:
                props = kwargs["fields"]
                kwargs.pop("fields")
            else:
                props = list(data["features"][0]["properties"].keys())
            if info_mode == "on_hover":
                tooltip = folium.GeoJsonTooltip(fields=props)
            elif info_mode == "on_click":
                popup = folium.GeoJsonPopup(fields=props)

        geojson = folium.GeoJson(
            data=data, name=layer_name, tooltip=tooltip, popup=popup, **kwargs
        )
        geojson.add_to(self)

        if zoom_to_layer:
            bounds = get_bounds(data)
            self.zoom_to_bounds(bounds)

    def add_gdf(
        self,
        gdf,
        layer_name: Optional[str] = "Untitled",
        zoom_to_layer: Optional[bool] = True,
        info_mode: Optional[str] = "on_hover",
        **kwargs,
    ):
        """Adds a GeoPandas GeoDataFrameto the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """

        for col in gdf.columns:
            if gdf[col].dtype in ["datetime64[ns]", "datetime64[ns, UTC]"]:
                gdf[col] = gdf[col].astype(str)

        data = gdf_to_geojson(gdf, epsg="4326")

        self.add_geojson(
            data,
            layer_name=layer_name,
            info_mode=info_mode,
            zoom_to_layer=zoom_to_layer,
            **kwargs,
        )

        # if zoom_to_layer:
        #     import numpy as np

        #     bounds = gdf.to_crs(epsg="4326").bounds
        #     west = np.min(bounds["minx"])
        #     south = np.min(bounds["miny"])
        #     east = np.max(bounds["maxx"])
        #     north = np.max(bounds["maxy"])
        #     self.fit_bounds([[south, east], [north, west]])

    def add_gdf_from_postgis(
        self,
        sql: str,
        con,
        layer_name: Optional[str] = "Untitled",
        zoom_to_layer: Optional[bool] = True,
        info_mode: Optional[str] = "on_hover",
        **kwargs,
    ):
        """Adds a GeoPandas GeoDataFrameto the map.

        Args:
            sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
            con (sqlalchemy.engine.Engine): Active connection to the database to query.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        if "fill_colors" in kwargs:
            kwargs.pop("fill_colors")
        gdf = read_postgis(sql, con, **kwargs)
        data = gdf_to_geojson(gdf, epsg="4326")

        self.add_geojson(data, layer_name=layer_name, info_mode=info_mode, **kwargs)

        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            self.fit_bounds([[south, east], [north, west]])

    def add_kml(
        self,
        in_kml: str,
        layer_name: Optional[str] = "Untitled",
        info_mode: Optional[str] = "on_hover",
        **kwargs,
    ):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
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

        data = kml_to_geojson(in_kml)

        self.add_geojson(data, layer_name=layer_name, info_mode=info_mode, **kwargs)

    def add_vector(
        self,
        filename: str,
        layer_name: Optional[str] = "Untitled",
        bbox: Optional[Tuple] = None,
        mask: Optional[Dict] = None,
        rows: Optional[Union[int, slice]] = None,
        info_mode: Optional[str] = "on_hover",
        zoom_to_layer: Optional[bool] = True,
        **kwargs,
    ):
        """Adds any geopandas-supported vector dataset to the map.

        Args:
            filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
            layer_name (str, optional): The layer name to use. Defaults to "Untitled".
            bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
            mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
            rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer. Defaults to True.

        """
        if not filename.startswith("http"):
            filename = os.path.abspath(filename)

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".shp":
            self.add_shp(filename, layer_name, **kwargs)
        elif ext in [".json", ".geojson"]:
            self.add_geojson(filename, layer_name, **kwargs)
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
                info_mode=info_mode,
                zoom_to_layer=zoom_to_layer,
                **kwargs,
            )

    def add_planet_by_month(
        self,
        year: Optional[int] = 2016,
        month: Optional[int] = 1,
        layer_name: Optional[str] = None,
        api_key: Optional[str] = None,
        token_name: Optional[str] = "PLANET_API_KEY",
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
        layer = planet_tile_by_month(
            year, month, layer_name, api_key, token_name, tile_format="folium"
        )
        layer.add_to(self)

    def add_planet_by_quarter(
        self,
        year: Optional[int] = 2016,
        quarter: Optional[int] = 1,
        layer_name: Optional[str] = None,
        api_key: Optional[str] = None,
        token_name: Optional[str] = "PLANET_API_KEY",
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
        layer = planet_tile_by_quarter(
            year, quarter, layer_name, api_key, token_name, tile_format="folium"
        )
        layer.add_to(self)

    def publish(
        self,
        name: Optional[str] = "Folium Map",
        description: Optional[str] = "",
        source_url: Optional[str] = "",
        tags: Optional[List] = None,
        source_file: Optional[str] = None,
        open: Optional[bool] = True,
        formatting=None,
        token: Optional[str] = None,
        **kwargs,
    ):
        """Publish the map to datapane.com

        Args:
            name (str, optional): The document name - can include spaces, caps, symbols, etc., e.g. "Profit & Loss 2020". Defaults to "Folium Map".
            description (str, optional): A high-level description for the document, this is displayed in searches and thumbnails. Defaults to ''.
            source_url (str, optional): A URL pointing to the source code for the document, e.g. a GitHub repo or a Colab notebook. Defaults to ''.
            tags (list, optional): A list of tags (as strings) used to categorise your document. Defaults to None.
            source_file (str, optional): Path of jupyter notebook file to upload. Defaults to None.
            open (bool, optional): Whether to open the map. Defaults to True.
            formatting (ReportFormatting, optional): Set the basic styling for your report.
            token (str, optional): The token to use to datapane to publish the map. See https://docs.datapane.com/tut-getting-started. Defaults to None.
        """
        import webbrowser
        import warnings

        if os.environ.get("USE_MKDOCS") is not None:
            return

        warnings.filterwarnings("ignore")
        try:
            import datapane as dp
        except Exception:
            webbrowser.open_new_tab("https://docs.datapane.com/")
            raise ImportError(
                "The datapane Python package is not installed. You need to install and authenticate datapane first."
            )

        if token is None:
            try:
                _ = dp.ping(verbose=False)
            except Exception as e:
                if os.environ.get("DP_TOKEN") is not None:
                    dp.login(token=os.environ.get("DP_TOKEN"))
                else:
                    raise Exception(e)
        else:
            dp.login(token)

        try:
            dp.upload_report(
                dp.Plot(self),
                name=name,
                description=description,
                source_url=source_url,
                tags=tags,
                source_file=source_file,
                open=open,
                formatting=formatting,
                **kwargs,
            )

        except Exception as e:
            raise Exception(e)

    def to_html(self, outfile: Optional[str] = None, **kwargs) -> str:
        """Exports a map as an HTML file.

        Args:
            outfile (str, optional): File path to the output HTML. Defaults to None.

        Raises:
            ValueError: If it is an invalid HTML file.

        Returns:
            str: A string containing the HTML code.
        """

        if self.options["layersControl"]:
            self.add_layer_control()

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

    def to_streamlit(
        self,
        width: Optional[int] = None,
        height: Optional[int] = 600,
        scrolling: Optional[bool] = False,
        add_layer_control: Optional[bool] = True,
        bidirectional: Optional[bool] = False,
        **kwargs,
    ):
        """Renders `folium.Figure` or `folium.Map` in a Streamlit app. This method is a static Streamlit Component, meaning, no information is passed back from Leaflet on browser interaction.

        Args:
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to 600.
            scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.
            add_layer_control (bool, optional): Whether to add the layer control. Defaults to True.
            bidirectional (bool, optional): Whether to add bidirectional functionality to the map. The streamlit-folium package is required to use the bidirectional functionality. Defaults to False.

        Raises:
            ImportError: If streamlit is not installed.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit.components.v1 as components

            if add_layer_control:
                self.add_layer_control()

            if bidirectional:
                from streamlit_folium import st_folium

                output = st_folium(self, width=width, height=height)
                return output
            else:
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

    def st_map_center(self, st_component) -> Tuple:
        """Get the center of the map.

        Args:
            st_component (st_folium): The streamlit component.

        Returns:
            tuple: The center of the map.
        """

        bounds = st_component["bounds"]
        west = bounds["_southWest"]["lng"]
        south = bounds["_southWest"]["lat"]
        east = bounds["_northEast"]["lng"]
        north = bounds["_northEast"]["lat"]
        return (south + (north - south) / 2, west + (east - west) / 2)

    def st_map_bounds(self, st_component) -> Tuple:
        """Get the bounds of the map in the format of (miny, minx, maxy, maxx).

        Args:
            st_component (st_folium): The streamlit component.

        Returns:
            tuple: The bounds of the map.
        """

        bounds = st_component["bounds"]
        south = bounds["_southWest"]["lat"]
        west = bounds["_southWest"]["lng"]
        north = bounds["_northEast"]["lat"]
        east = bounds["_northEast"]["lng"]

        bounds = [[south, west], [north, east]]
        return bounds

    def st_fit_bounds(self):
        """Fit the map to the bounds of the map.

        Returns:
            folium.Map: The map.
        """

        try:
            import streamlit as st

            if "map_bounds" in st.session_state:
                bounds = st.session_state["map_bounds"]

                self.fit_bounds(bounds)

        except Exception as e:
            raise Exception(e)

    def st_last_draw(self, st_component):
        """Get the last draw feature of the map.

        Args:
            st_component (st_folium): The streamlit component.

        Returns:
            str: The last draw of the map.
        """

        return st_component["last_active_drawing"]

    def st_last_click(self, st_component):
        """Get the last click feature of the map.

        Args:
            st_component (st_folium): The streamlit component.

        Returns:
            str: The last click of the map.
        """

        coords = st_component["last_clicked"]
        return (coords["lat"], coords["lng"])

    def st_draw_features(self, st_component):
        """Get the draw features of the map.

        Args:
            st_component (st_folium): The streamlit component.

        Returns:
            list: The draw features of the map.
        """

        return st_component["all_drawings"]

    def add_title(
        self,
        title: str,
        align: Optional[str] = "center",
        font_size: Optional[str] = "16px",
        style=None,
    ):
        """Adds a title to the map.

        Args:
            title (str): The title to use.
            align (str, optional): The alignment of the title, can be ["center", "left", "right"]. Defaults to "center".
            font_size (str, optional): The font size in the unit of px. Defaults to "16px".
            style ([type], optional): The style to use. Defaults to None.
        """
        if style is None:
            title_html = """
                    <h3 align={} style="font-size:{}"><b>{}</b></h3>
                    """.format(
                align, font_size, title
            )
        else:
            title_html = """
                <h3 align={} style={}><b>{}</b></h3>
                """.format(
                align, style, title
            )
        self.get_root().html.add_child(folium.Element(title_html))

    def static_map(
        self,
        width: Optional[int] = 950,
        height: Optional[int] = 600,
        read_only: Optional[bool] = False,
        out_file: Optional[str] = None,
        **kwargs,
    ):
        """Display a folium static map in a Jupyter Notebook.

        Args
            m (folium.Map): A folium map.
            width (int, optional): Width of the map. Defaults to 950.
            height (int, optional): Height of the map. Defaults to 600.
            read_only (bool, optional): Whether to hide the side panel to disable map customization. Defaults to False.
            out_file (str, optional): Output html file path. Defaults to None.
        """
        if isinstance(self, folium.Map):
            if out_file is None:
                out_file = "./cache/" + "folium_" + random_string(3) + ".html"
            out_dir = os.path.abspath(os.path.dirname(out_file))
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            self.to_html(out_file)
            display_html(src=out_file, width=width, height=height)
        else:
            raise TypeError("The provided map is not a folium map.")

    def add_census_data(
        self, wms: str, layer: str, census_dict: Optional[Dict] = None, **kwargs
    ):
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

    def add_xyz_service(self, provider: str, **kwargs):
        """Add a XYZ tile layer to the map.

        Args:
            provider (str): A tile layer name starts with xyz or qms. For example, xyz.OpenTopoMap,

        Raises:
            ValueError: The provider is not valid. It must start with xyz or qms.
        """
        import xyzservices.providers as xyz
        from xyzservices import TileProvider

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
            qms_provider = TileProvider.from_qms(name)
            url = qms_provider.build_url()
            attribution = qms_provider.attribution
            if attribution.strip() == "":
                attribution = " "
            self.add_tile_layer(url=url, name=name, attribution=attribution)
        else:
            raise ValueError(
                f"The provider {provider} is not valid. It must start with xyz or qms."
            )

    def add_marker(
        self,
        location: Union[List, Tuple],
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        icon: Optional[str] = None,
        draggable: Optional[bool] = False,
        **kwargs,
    ):
        """Adds a marker to the map. More info about marker options at https://python-visualization.github.io/folium/modules.html#folium.map.Marker.

        Args:
            location (list | tuple): The location of the marker in the format of [lat, lng].
            popup (str, optional): The popup text. Defaults to None.
            tooltip (str, optional): The tooltip text. Defaults to None.
            icon (str, optional): The icon to use. Defaults to None.
            draggable (bool, optional): Whether the marker is draggable. Defaults to False.
        """
        if isinstance(location, list):
            location = tuple(location)
        if isinstance(location, tuple):
            folium.Marker(
                location=location,
                popup=popup,
                tooltip=tooltip,
                icon=icon,
                draggable=draggable,
                **kwargs,
            ).add_to(self)

        else:
            raise TypeError("The location must be a list or a tuple.")

    def add_colormap(
        self,
        width: Optional[float] = 4.0,
        height: Optional[float] = 0.3,
        vmin: Optional[float] = 0,
        vmax: Optional[float] = 1.0,
        palette: Optional[List] = None,
        vis_params: Optional[dict] = None,
        cmap: Optional[str] = "gray",
        discrete: Optional[bool] = False,
        label: Optional[str] = None,
        label_size: Optional[int] = 12,
        label_weight: Optional[str] = "normal",
        tick_size: Optional[int] = 10,
        bg_color: Optional[str] = "white",
        orientation: Optional[str] = "horizontal",
        dpi: Optional[Union[str, float]] = "figure",
        transparent: Optional[bool] = False,
        position: Optional[Tuple] = (70, 5),
        **kwargs,
    ):
        """Add a colorbar to the map. Under the hood, it uses matplotlib to generate the colorbar, save it as a png file, and add it to the map using m.add_image().

        Args:
            width (float): Width of the colorbar in inches. Default is 4.0.
            height (float): Height of the colorbar in inches. Default is 0.3.
            vmin (float): Minimum value of the colorbar. Default is 0.
            vmax (float): Maximum value of the colorbar. Default is 1.0.
            palette (list): List of colors to use for the colorbar. It can also be a cmap name, such as ndvi, ndwi, dem, coolwarm. Default is None.
            vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
            discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            label_size (int, optional): Font size for the colorbar label. Defaults to 12.
            label_weight (str, optional): Font weight for the colorbar label, can be "normal", "bold", etc. Defaults to "normal".
            tick_size (int, optional): Font size for the colorbar tick labels. Defaults to 10.
            bg_color (str, optional): Background color for the colorbar. Defaults to "white".
            orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
            dpi (float | str, optional): The resolution in dots per inch.  If 'figure', use the figure's dpi value. Defaults to "figure".
            transparent (bool, optional): Whether to make the background transparent. Defaults to False.
            position (tuple, optional): The position of the colormap in the format of (x, y),
                the percentage ranging from 0 to 100, starting from the lower-left corner. Defaults to (0, 0).
            **kwargs: Other keyword arguments to pass to matplotlib.pyplot.savefig().

        Returns:
            str: Path to the output image.
        """

        colorbar = save_colorbar(
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
            **kwargs,
        )

        self.add_image(colorbar, position=position)

    def add_points_from_xy(
        self,
        data: Union[str, pd.DataFrame],
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        popup: Optional[List] = None,
        min_width: Optional[int] = 100,
        max_width: Optional[int] = 200,
        layer_name: Optional[str] = "Marker Cluster",
        color_column: Optional[str] = None,
        marker_colors: Optional[List] = None,
        icon_colors: Optional[List] = ["white"],
        icon_names: Optional[List] = ["info"],
        angle: Optional[int] = 0,
        prefix: Optional[str] = "fa",
        add_legend: Optional[bool] = True,
        max_cluster_radius: Optional[int] = 80,
        **kwargs,
    ):
        """Adds a marker cluster to the map.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            min_width (int, optional): The minimum width of the popup. Defaults to 100.
            max_width (int, optional): The maximum width of the popup. Defaults to 200.
            layer_name (str, optional): The name of the layer. Defaults to "Marker Cluster".
            color_column (str, optional): The column name for the color values. Defaults to None.
            marker_colors (list, optional): A list of colors to be used for the markers. Defaults to None.
            icon_colors (list, optional): A list of colors to be used for the icons. Defaults to ['white'].
            icon_names (list, optional): A list of names to be used for the icons. More icons can be found
                at https://fontawesome.com/v4/icons or https://getbootstrap.com/docs/3.3/components/?utm_source=pocket_mylist. Defaults to ['info'].
            angle (int, optional): The angle of the icon. Defaults to 0.
            prefix (str, optional): The prefix states the source of the icon. 'fa' for font-awesome or 'glyphicon' for bootstrap 3. Defaults to 'fa'.
            add_legend (bool, optional): If True, a legend will be added to the map. Defaults to True.
            max_cluster_radius (int, optional): The maximum radius that a cluster will cover from the central marker (in pixels).
            **kwargs: Other keyword arguments to pass to folium.MarkerCluster(). For a list of available options,
                see https://github.com/Leaflet/Leaflet.markercluster. For example, to change the cluster radius, use options={"maxClusterRadius": 50}.
        """
        import pandas as pd

        if "maxClusterRadius" not in kwargs:
            kwargs["maxClusterRadius"] = max_cluster_radius

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

        if popup is None:
            popup = col_names

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        marker_cluster = plugins.MarkerCluster(name=layer_name, **kwargs).add_to(self)

        for idx, row in df.iterrows():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(row[p]) + "<br>"
            popup_html = folium.Popup(html, min_width=min_width, max_width=max_width)

            if items is not None:
                index = items.index(row[color_column])
                marker_icon = folium.Icon(
                    color=marker_colors[index],
                    icon_color=icon_colors[index],
                    icon=icon_names[index],
                    angle=angle,
                    prefix=prefix,
                )
            else:
                marker_icon = None

            folium.Marker(
                location=[row[y], row[x]],
                popup=popup_html,
                icon=marker_icon,
            ).add_to(marker_cluster)

        if items is not None and add_legend:
            marker_colors = [check_color(c) for c in marker_colors]
            self.add_legend(
                title=color_column.title(), colors=marker_colors, labels=items
            )

    def add_circle_markers_from_xy(
        self,
        data: Union[str, pd.DataFrame],
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        radius: Optional[int] = 10,
        popup: Optional[List] = None,
        tooltip: Optional[List] = None,
        min_width: Optional[int] = 100,
        max_width: Optional[int] = 200,
        **kwargs,
    ):
        """Adds a marker cluster to the map.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            radius (int, optional): The radius of the circle. Defaults to 10.
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            tooltip (list, optional): A list of column names to be used as the tooltip. Defaults to None.
            min_width (int, optional): The minimum width of the popup. Defaults to 100.
            max_width (int, optional): The maximum width of the popup. Defaults to 200.

        """
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data)

        col_names = df.columns.values.tolist()

        if "color" not in kwargs:
            kwargs["color"] = None
        if "fill" not in kwargs:
            kwargs["fill"] = True
        if "fill_color" not in kwargs:
            kwargs["fill_color"] = "blue"
        if "fill_opacity" not in kwargs:
            kwargs["fill_opacity"] = 0.7

        if popup is None:
            popup = col_names

        if not isinstance(popup, list):
            popup = [popup]

        if tooltip is not None:
            if not isinstance(tooltip, list):
                tooltip = [tooltip]

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        for idx, row in df.iterrows():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(row[p]) + "<br>"
            popup_html = folium.Popup(html, min_width=min_width, max_width=max_width)

            if tooltip is not None:
                html = ""
                for p in tooltip:
                    html = html + "<b>" + p + "</b>" + ": " + str(row[p]) + "<br>"

                tooltip_str = folium.Tooltip(html)
            else:
                tooltip_str = None

            folium.CircleMarker(
                location=[row[y], row[x]],
                radius=radius,
                popup=popup_html,
                tooltip=tooltip_str,
                **kwargs,
            ).add_to(self)

    def add_labels(
        self,
        data: Union[pd.DataFrame, str],
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
        """Adds a label layer to the map. Reference: https://python-visualization.github.io/folium/modules.html#folium.features.DivIcon

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
            layer_name (str, optional): The name of the layer. Defaults to "Labels".

        """
        import warnings
        import pandas as pd
        from folium.features import DivIcon

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
                except ImportError:
                    print("geopandas is required to read geojson.")
                    return
        else:
            raise ValueError("data must be a DataFrame or an ee.FeatureCollection.")

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

        layer_group = folium.FeatureGroup(name=layer_name)
        for index in df.index:
            html = f'<div style="font-size: {font_size};color:{font_color};font-family:{font_family};font-weight: {font_weight}">{df[column][index]}</div>'
            folium.Marker(
                location=[df[y][index], df[x][index]],
                icon=DivIcon(
                    icon_size=(1, 1),
                    icon_anchor=(size, size),
                    html=html,
                    **kwargs,
                ),
                draggable=draggable,
            ).add_to(layer_group)

        layer_group.add_to(self)

    def split_map(
        self,
        left_layer: Optional[str] = "TERRAIN",
        right_layer: Optional[str] = "OpenTopoMap",
        left_args: Optional[dict] = {},
        right_args: Optional[dict] = {},
        left_label: Optional[str] = None,
        right_label: Optional[str] = None,
        left_position: Optional[str] = "bottomleft",
        right_position: Optional[str] = "bottomright",
        **kwargs,
    ):
        """Adds a split-panel map.

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
                    left_layer = folium.raster_layers.TileLayer(
                        tiles=url,
                        name=left_name,
                        attr=" ",
                        overlay=True,
                    )

                elif left_layer.startswith("http") and left_layer.endswith(".json"):
                    left_tile_url = stac_tile(left_layer, **left_args)
                    bbox = stac_bounds(left_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    left_layer = folium.raster_layers.TileLayer(
                        tiles=left_tile_url,
                        name=left_name,
                        attr=" ",
                        overlay=True,
                    )

                elif os.path.exists(left_layer):
                    left_layer, left_client = get_local_tile_layer(
                        left_layer,
                        tile_format="folium",
                        return_client=True,
                        **left_args,
                    )
                    bounds = image_bounds(left_client)

                else:
                    left_layer = folium.raster_layers.TileLayer(
                        tiles=left_layer,
                        name=left_name,
                        attr=" ",
                        overlay=True,
                        **left_args,
                    )
            elif isinstance(left_layer, folium.raster_layers.TileLayer) or isinstance(
                left_layer, folium.WmsTileLayer
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
                    url = cog_tile(right_layer, **right_args)
                    bbox = cog_bounds(right_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    right_layer = folium.raster_layers.TileLayer(
                        tiles=url,
                        name=right_name,
                        attr=" ",
                        overlay=True,
                    )

                elif right_layer.startswith("http") and right_layer.endswith(".json"):
                    right_tile_url = stac_tile(right_layer, **left_args)
                    bbox = stac_bounds(right_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    right_layer = folium.raster_layers.TileLayer(
                        tiles=right_tile_url,
                        name=right_name,
                        attr=" ",
                        overlay=True,
                    )

                elif os.path.exists(right_layer):
                    right_layer, right_client = get_local_tile_layer(
                        right_layer,
                        tile_format="folium",
                        return_client=True,
                        **right_args,
                    )
                    bounds = image_bounds(right_client)
                else:
                    right_layer = folium.raster_layers.TileLayer(
                        tiles=right_layer,
                        name=right_name,
                        attr=" ",
                        overlay=True,
                        **right_args,
                    )
            elif isinstance(right_layer, folium.raster_layers.TileLayer) or isinstance(
                left_layer, folium.WmsTileLayer
            ):
                pass
            else:
                raise ValueError(
                    f"right_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            control = SideBySideLayers(layer_left=left_layer, layer_right=right_layer)
            left_layer.add_to(self)
            right_layer.add_to(self)
            control.add_to(self)

            if left_label is not None:
                if "<" not in left_label:
                    left_label = f"<h4>{left_label}</h4>"
                self.add_html(left_label, position=left_position)

            if right_label is not None:
                if "<" not in right_label:
                    right_label = f"<h4>{right_label}</h4>"
                self.add_html(right_label, position=right_position)
            if bounds is not None:
                self.fit_bounds(bounds)

        except Exception as e:
            print("The provided layers are invalid!")
            raise ValueError(e)

    def add_data(
        self,
        data: Union[str, pd.DataFrame],
        column: str,
        cmap: Optional[str] = None,
        colors: Optional[List] = None,
        labels: Optional[List] = None,
        scheme: Optional[str] = "Quantiles",
        k: Optional[int] = 5,
        add_legend: Optional[bool] = True,
        legend_title: Optional[str] = None,
        legend_position: Optional[str] = "bottomright",
        legend_kwds: Optional[dict] = None,
        classification_kwds: Optional[dict] = None,
        style_function: Optional[Callable] = None,
        highlight_function: Optional[Callable] = None,
        layer_name: Optional[str] = "Untitled",
        info_mode: Optional[str] = "on_hover",
        encoding: Optional[str] = "utf-8",
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
            style_function (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
                style_callback is a function that takes the feature as argument and should return a dictionary of the following form:
                style_callback = lambda feat: {"fillColor": feat["properties"]["color"]}
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
            hightlight_function (function, optional): Highlighting function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
                highlight_function is a function that takes the feature as argument and should return a dictionary of the following form:
                highlight_function = lambda feat: {"fillColor": feat["properties"]["color"]}
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
            **kwargs: Additional keyword arguments to pass to the GeoJSON class, such as fields, which can be a list of column names to be included in the popup.
        """

        import warnings

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

        if "style" in kwargs:
            warnings.warn(
                "The style arguments is for ipyleaflet only. ",
                UserWarning,
            )
            kwargs.pop("style")

        if "hover_style" in kwargs:
            warnings.warn(
                "The hover_style arguments is for ipyleaflet only. ",
                UserWarning,
            )
            kwargs.pop("hover_style")

        if "style_callback" in kwargs:
            warnings.warn(
                "The style_callback arguments is for ipyleaflet only. ",
                UserWarning,
            )
            kwargs.pop("style_callback")

        if style_function is None:
            style_function = lambda feat: {
                # "stroke": False,
                # "color": "#ff0000",
                "weight": 1,
                "opacity": 1,
                # "fill": True,
                # "fillColor": "#ffffff",
                "fillOpacity": 1.0,
                # "dashArray": "9"
                # "clickable": True,
                "fillColor": feat["properties"]["color"],
            }

        if highlight_function is None:
            highlight_function = lambda feat: {
                "weight": 2,
                "fillOpacity": 0.5,
            }

        self.add_gdf(
            gdf,
            layer_name=layer_name,
            style_function=style_function,
            highlight_function=highlight_function,
            info_mode=info_mode,
            encoding=encoding,
            **kwargs,
        )
        if add_legend:
            self.add_legend(title=legend_title, legend_dict=legend_dict)

    def add_image(
        self,
        image: str,
        position: Optional[Tuple] = (0, 0),
        **kwargs,
    ):
        """Add an image to the map.

        Args:
            image (str | ipywidgets.Image): The image to add.
            position (tuple, optional): The position of the image in the format of (x, y),
                the percentage ranging from 0 to 100, starting from the lower-left corner. Defaults to (0, 0).
        """
        import base64

        if isinstance(image, str):
            if image.startswith("http"):
                html = f'<img src="{image}">'
                if isinstance(position, tuple):
                    position = "bottomright"
                self.add_html(html, position=position, **kwargs)

            elif os.path.exists(image):
                if position == "bottomleft":
                    position = (5, 5)
                elif position == "bottomright":
                    position = (80, 5)
                elif position == "topleft":
                    position = (5, 60)
                elif position == "topright":
                    position = (80, 60)

                with open(image, "rb") as lf:
                    # open in binary mode, read bytes, encode, decode obtained bytes as utf-8 string
                    b64_content = base64.b64encode(lf.read()).decode("utf-8")
                    widget = plugins.FloatImage(
                        "data:image/png;base64,{}".format(b64_content),
                        bottom=position[1],
                        left=position[0],
                    )
                    widget.add_to(self)

        else:
            raise Exception("Invalid image")

    def add_widget(
        self, content: str, position: Optional[str] = "bottomright", **kwargs
    ):
        """Add a widget (e.g., text, HTML, figure) to the map.

        Args:
            content (str): The widget to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
        """

        from matplotlib import figure
        import base64
        from io import BytesIO

        allowed_positions = ["topleft", "topright", "bottomleft", "bottomright"]

        if position not in allowed_positions:
            raise Exception(f"position must be one of {allowed_positions}")

        try:
            if isinstance(content, str):
                widget = CustomControl(content, position=position)
                widget.add_to(self)
            elif isinstance(content, figure.Figure):
                buf = BytesIO()
                content.savefig(buf, format="png")
                buf.seek(0)
                b64_content = base64.b64encode(buf.read()).decode("utf-8")
                widget = CustomControl(
                    f"""<img src="data:image/png;base64,{b64_content}">""",
                    position=position,
                )
                widget.add_to(self)
            else:
                raise Exception("The content must be a string or a matplotlib figure")

        except Exception as e:
            raise Exception(f"Error adding widget: {e}")

    def add_html(self, html: str, position: Optional[str] = "bottomright", **kwargs):
        """Add HTML to the map.

        Args:
            html (str): The HTML to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
        """

        self.add_widget(html, position=position, **kwargs)

    def add_text(
        self,
        text: str,
        fontsize: Optional[int] = 20,
        fontcolor: Optional[str] = "black",
        bold: Optional[bool] = False,
        padding: Optional[str] = "5px",
        background: Optional[bool] = True,
        bg_color: Optional[str] = "white",
        border_radius: Optional[str] = "5px",
        position: Optional[str] = "bottomright",
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

    def add_vector_tile(
        self,
        url: Optional[str],
        attribution: Optional[str] = "",
        styles: Optional[dict] = {},
        layer_name: Optional[str] = "Vector Tile",
        **kwargs,
    ):
        """Adds a VectorTileLayer to the map. It wraps the folium.plugins.VectorGridProtobuf class. See
            https://github.com/python-visualization/folium/blob/main/folium/plugins/vectorgrid_protobuf.py#L7

        Args:
            url (str, optional): The URL of the tile layer, such as
                'https://tile.nextzen.org/tilezen/vector/v1/512/all/{z}/{x}/{y}.mvt?api_key=gCZXZglvRQa6sB2z7JzL1w'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            styles (dict,optional): Style dict, specific to the vector tile source.
            layer_name (str, optional): The layer name to use for the layer. Defaults to 'Vector Tile'.
            kwargs: Additional keyword arguments to pass to the ipyleaflet.VectorTileLayer class.
        """

        options = {}

        for key, value in kwargs.items():
            options[key] = value

        if "vector_tile_layer_styles" in options:
            styles = options["vector_tile_layer_styles"]
            del options["vector_tile_layer_styles"]

        if styles:
            options["vectorTileLayerStyles"] = styles

        vc = plugins.VectorGridProtobuf(url, layer_name, options)
        self.add_child(vc)

    def to_gradio(
        self, width: Optional[str] = "100%", height: Optional[str] = "500px", **kwargs
    ):
        """Converts the map to an HTML string that can be used in Gradio. Removes unsupported elements, such as
            attribution and any code blocks containing functions. See https://github.com/gradio-app/gradio/issues/3190

        Args:
            width (str, optional): The width of the map. Defaults to '100%'.
            height (str, optional): The height of the map. Defaults to '500px'.

        Returns:
            str: The HTML string to use in Gradio.
        """

        if isinstance(width, int):
            width = f"{width}px"
        if isinstance(height, int):
            height = f"{height}px"

        html = self.to_html()
        lines = html.split("\n")
        output = []
        skipped_lines = []
        for index, line in enumerate(lines):
            if index in skipped_lines:
                continue
            if line.lstrip().startswith('{"attribution":'):
                continue
            elif "on(L.Draw.Event.CREATED, function(e)" in line:
                for i in range(14):
                    skipped_lines.append(index + i)
            elif "L.Control.geocoder" in line:
                for i in range(5):
                    skipped_lines.append(index + i)
            elif "function(e)" in line:
                print(
                    f"Warning: The folium plotting backend does not support functions in code blocks. Please delete line {index + 1}."
                )
            else:
                output.append(line + "\n")

        return f"""<iframe style="width: {width}; height: {height}" name="result" allow="midi; geolocation; microphone; camera; 
        display-capture; encrypted-media;" sandbox="allow-modals allow-forms 
        allow-scripts allow-same-origin allow-popups 
        allow-top-navigation-by-user-activation allow-downloads" allowfullscreen="" 
        allowpaymentrequest="" frameborder="0" srcdoc='{"".join(output)}'></iframe>"""

    def oam_search(
        self,
        bbox: Optional[Union[List, str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = 100,
        info_mode: Optional[str] = "on_click",
        layer_args: Optional[dict] = {},
        add_image: Optional[bool] = True,
        **kwargs,
    ):
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

        if "highlight_function" not in layer_args:
            layer_args["highlight_function"] = lambda feat: {
                "weight": layer_args["style"]["weight"] + 2,
                "fillOpacity": 0,
            }

        if gdf is not None:
            self.add_gdf(gdf, info_mode=info_mode, **layer_args)
            setattr(self, "oam_gdf", gdf)

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

    def remove_labels(self, **kwargs):
        """Removes a layer from the map."""
        print("The folium plotting backend does not support removing labels.")

    def add_minimap(self, zoom=5, position="bottomright"):
        """Adds a minimap (overview) to the ipyleaflet map."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def add_point_layer(
        self, filename, popup=None, layer_name="Marker Cluster", **kwargs
    ):
        """Adds a point layer to the map with a popup attribute."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def add_raster_legacy(
        self,
        image,
        bands=None,
        layer_name=None,
        colormap=None,
        x_dim="x",
        y_dim="y",
    ):
        """Adds a local raster dataset to the map."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def add_time_slider(
        self,
        layers_dict={},
        labels=None,
        time_interval=1,
        position="bottomright",
        slider_length="150px",
        **kwargs,
    ):
        """Adds a time slider to the map."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def add_xy_data(
        self,
        in_csv,
        x="longitude",
        y="latitude",
        label=None,
        layer_name="Marker cluster",
    ):
        """Adds points from a CSV file containing lat/lon information and display data on the map."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def basemap_demo(self):
        """A demo for using leafmap basemaps."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def find_layer(self, name):
        """Finds layer by name."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def find_layer_index(self, name):
        """Finds layer index by name."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def get_layer_names(self):
        """Gets layer names as a list."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def get_scale(self):
        """Returns the approximate pixel scale of the current map view, in meters."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def image_overlay(self, url: str, bounds: Tuple, name: str):
        """Overlays an image from the Internet or locally on the map.

        Args:
            url (str): http URL or local file path to the image.
            bounds (tuple): bounding box of the image in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            name (str): name of the layer to show on the layer control.
        """
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def layer_opacity(self, name, value=1.0):
        """Changes layer opacity."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def to_image(self, outfile=None, monitor=1):
        """Saves the map as a PNG or JPG image."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def toolbar_reset(self):
        """Reset the toolbar so that no tool is selected."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def video_overlay(self, url, bounds, name):
        """Overlays a video from the Internet on the map."""
        raise NotImplementedError(
            "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
        )

    def add_search_control(
        self, url, marker=None, zoom=None, position="topleft", **kwargs
    ):
        """Adds a search control to the map."""
        print("The folium plotting backend does not support this function.")

    def save_draw_features(self, out_file: str, indent: Optional[int] = 4, **kwargs):
        """Save the draw features to a file.

        Args:
            out_file (str): The output file path.
            indent (int, optional): The indentation level when saving data as a GeoJSON. Defaults to 4.
        """
        print("The folium plotting backend does not support this function.")

    def edit_vector(self, data: Union[str, dict], **kwargs):
        """Edit a vector layer.

        Args:
            data (dict | str): The data to edit. It can be a GeoJSON dictionary or a file path.
        """
        print("The folium plotting backend does not support this function.")

    def add_velocity(
        self,
        data,
        zonal_speed,
        meridional_speed,
        latitude_dimension="lat",
        longitude_dimension="lon",
        velocity_scale=0.01,
        max_velocity=20,
        display_options={},
        name="Velocity",
    ):
        print(f"The folium plotting backend does not support this function.")

    def user_roi_bounds(self, decimals: Optional[int] = 4) -> List:
        """Get the bounds of the user drawn ROI as a tuple of (minx, miny, maxx, maxy).

        Args:
            decimals (int, optional): The number of decimals to round the coordinates to. Defaults to 4.

        Returns:
            list: The bounds of the user drawn ROI as a tuple of (minx, miny, maxx, maxy).
        """
        print(f"The folium plotting backend does not support this function.")


class SplitControl(Layer):
    """
    Creates a SplitControl that takes two Layers and adds a sliding control with the leaflet-side-by-side plugin.
    Uses the Leaflet leaflet-side-by-side plugin https://github.com/digidem/leaflet-side-by-side Parameters.
    The source code is adapted from https://github.com/python-visualization/folium/pull/1292
    ----------
    layer_left: Layer.
        The left Layer within the side by side control.
        Must  be created and added to the map before being passed to this class.
    layer_right: Layer.
        The left Layer within the side by side control.
        Must  be created and added to the map before being passed to this class.
    name : string, default None
        The name of the Layer, as it will appear in LayerControls.
    overlay : bool, default True
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls.
    show: bool, default True
        Whether the layer will be shown on opening (only for overlays).
    Examples
    --------
    >>> sidebyside = SideBySideLayers(layer_left, layer_right)
    >>> sidebyside.add_to(m)
    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.control.sideBySide(
                {{ this.layer_left.get_name() }}, {{ this.layer_right.get_name() }}
            ).addTo({{ this._parent.get_name() }});
        {% endmacro %}
        """
    )

    def __init__(
        self, layer_left, layer_right, name=None, overlay=True, control=True, show=True
    ):
        super(SplitControl, self).__init__(
            name=name, overlay=overlay, control=control, show=show
        )
        self._name = "SplitControl"
        self.layer_left = layer_left
        self.layer_right = layer_right

    def render(self, **kwargs):
        super(SplitControl, self).render()

        figure = self.get_root()
        assert isinstance(figure, Figure), (
            "You cannot render this Element " "if it is not in a Figure."
        )

        figure.header.add_child(
            JavascriptLink(
                "https://raw.githack.com/digidem/leaflet-side-by-side/gh-pages/leaflet-side-by-side.js"
            ),  # noqa
            name="leaflet.sidebyside",
        )


class SideBySideLayers(JSCSSMixin, Layer):
    """
    Creates a SideBySideLayers that takes two Layers and adds a sliding
    control with the leaflet-side-by-side plugin.
    Uses the Leaflet leaflet-side-by-side plugin https://github.com/digidem/leaflet-side-by-side.
    Adopted from https://github.com/python-visualization/folium/pull/1292/files.
    Parameters
    ----------
    layer_left: Layer.
        The left Layer within the side by side control.
        Must be created and added to the map before being passed to this class.
    layer_right: Layer.
        The right Layer within the side by side control.
        Must be created and added to the map before being passed to this class.
    Examples
    --------
    >>> sidebyside = SideBySideLayers(layer_left, layer_right)
    >>> sidebyside.add_to(m)
    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.control.sideBySide(
                {{ this.layer_left.get_name() }}, {{ this.layer_right.get_name() }}
            ).addTo({{ this._parent.get_name() }});
        {% endmacro %}
        """
    )

    default_js = [
        (
            "leaflet.sidebyside",
            "https://cdn.jsdelivr.net/gh/digidem/leaflet-side-by-side@gh-pages/leaflet-side-by-side.min.js",
        ),
    ]

    def __init__(self, layer_left, layer_right):
        super().__init__(control=False)
        self._name = "SideBySideLayers"
        self.layer_left = layer_left
        self.layer_right = layer_right


class CustomControl(MacroElement):
    """Put any HTML on the map as a Leaflet Control.
    Adopted from https://github.com/python-visualization/folium/pull/1662

    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        L.Control.CustomControl = L.Control.extend({
            onAdd: function(map) {
                let div = L.DomUtil.create('div');
                div.innerHTML = `{{ this.html }}`;
                return div;
            },
            onRemove: function(map) {
                // Nothing to do here
            }
        });
        L.control.customControl = function(opts) {
            return new L.Control.CustomControl(opts);
        }
        L.control.customControl(
            { position: "{{ this.position }}" }
        ).addTo({{ this._parent.get_name() }});
        {% endmacro %}
    """
    )

    def __init__(self, html, position="bottomleft"):
        def escape_backticks(text):
            """Escape backticks so text can be used in a JS template."""
            import re

            return re.sub(r"(?<!\\)`", r"\`", text)

        super().__init__()
        self.html = escape_backticks(html)
        self.position = position


class FloatText(MacroElement):
    """Adds a floating image in HTML canvas on top of the map."""

    _template = Template(
        """
            {% macro header(this,kwargs) %}
                <style>
                    #{{this.get_name()}} {
                        position:absolute;
                        bottom:{{this.bottom}}%;
                        left:{{this.left}}%;
                        }
                </style>
            {% endmacro %}

            {% macro html(this, kwargs) %}

            <!doctype html>
            <html lang="en">
            <head>
            </head>
            <body>

            <div id='{{this.get_name()}}' class='{{this.get_name()}}'
                style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
                border-radius:5px; padding: 5px; font-size:14px; '>

            <div class='text'>{{this.text}}</div>
            </div>

            </body>
            </html>

            <style type='text/css'>
            .{{this.get_name()}} .text {
                text-align: left;
                margin-bottom: 0px;
                font-size: 90%;
                float: left;
                }
            </style>
            {% endmacro %}
            """
    )

    def __init__(self, text, bottom=75, left=75):
        super(FloatText, self).__init__()
        self._name = "FloatText"
        self.text = text
        self.bottom = bottom
        self.left = left


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


def linked_maps(
    rows=2,
    cols=2,
    height="400px",
    layers=[],
    labels=[],
    label_position="topright",
    **kwargs,
):
    """Create linked maps of XYZ tile layers."""
    raise NotImplementedError(
        "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
    )


def split_map(
    left_layer="ROADMAP",
    right_layer="HYBRID",
    left_label=None,
    right_label=None,
    label_position="bottom",
    **kwargs,
):
    """Creates a split-panel map."""
    raise NotImplementedError(
        "The folium plotting backend does not support this function. Use the ipyleaflet plotting backend instead."
    )


def st_map_center(lat: float, lon: float):
    """Returns the map center coordinates for a given latitude and longitude. If the system variable 'map_center' exists, it is used. Otherwise, the default is returned.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.

    Raises:
        Exception: If streamlit is not installed.

    Returns:
        list: The map center coordinates.
    """
    try:
        import streamlit as st

        if "map_center" in st.session_state:
            return st.session_state["map_center"]
        else:
            return [lat, lon]

    except Exception as e:
        raise Exception(e)


def st_save_bounds(st_component: Map):
    """Saves the map bounds to the session state.

    Args:
        map (folium.folium.Map): The map to save the bounds from.
    """
    try:
        import streamlit as st

        if st_component is not None:
            bounds = st_component["bounds"]
            south = bounds["_southWest"]["lat"]
            west = bounds["_southWest"]["lng"]
            north = bounds["_northEast"]["lat"]
            east = bounds["_northEast"]["lng"]

            bounds = [[south, west], [north, east]]
            center = [south + (north - south) / 2, west + (east - west) / 2]

            st.session_state["map_bounds"] = bounds
            st.session_state["map_center"] = center
    except Exception as e:
        raise Exception(e)


def geojson_layer(
    in_geojson: str,
    layer_name: Optional[str] = "Untitled",
    encoding: Optional[str] = "utf-8",
    info_mode: Optional[str] = "on_hover",
    **kwargs,
):
    """Adds a GeoJSON file to the map.

    Args:
        in_geojson (str): The input file path to the GeoJSON.
        layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
        encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
        info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

    Raises:
        FileNotFoundError: The provided GeoJSON file could not be found.
    """
    import json
    import requests
    import random

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

                with open(in_geojson, encoding=encoding) as f:
                    data = json.load(f)
        elif isinstance(in_geojson, dict):
            data = in_geojson
        else:
            raise TypeError("The input geojson must be a type of str or dict.")
    except Exception as e:
        raise Exception(e)

    # interchangeable parameters between ipyleaflet and folium.
    if "style_function" not in kwargs:
        if "style" in kwargs:
            style_dict = kwargs["style"]
            if isinstance(kwargs["style"], dict) and len(kwargs["style"]) > 0:
                kwargs["style_function"] = lambda x: style_dict
            kwargs.pop("style")
        else:
            style_dict = {
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
            kwargs["style_function"] = lambda x: style_dict

    if "style_callback" in kwargs:
        kwargs.pop("style_callback")

    if "hover_style" in kwargs:
        kwargs.pop("hover_style")

    if "fill_colors" in kwargs:
        fill_colors = kwargs["fill_colors"]

        def random_color(feature):
            style_dict["fillColor"] = random.choice(fill_colors)
            return style_dict

        kwargs["style_function"] = random_color
        kwargs.pop("fill_colors")

    if "highlight_function" not in kwargs:
        kwargs["highlight_function"] = lambda feat: {
            "weight": 2,
            "fillOpacity": 0.5,
        }

    tooltip = None
    popup = None
    if info_mode is not None:
        props = list(data["features"][0]["properties"].keys())
        if info_mode == "on_hover":
            tooltip = folium.GeoJsonTooltip(fields=props)
        elif info_mode == "on_click":
            popup = folium.GeoJsonPopup(fields=props)

    geojson = folium.GeoJson(
        data=data, name=layer_name, tooltip=tooltip, popup=popup, **kwargs
    )
    return geojson


class PMTilesLayer(JSCSSMixin, Layer):
    """Creates a PMTilesLayer object for displaying PMTiles.
    Adapted from https://github.com/jtmiclat/folium-pmtiles. Credits to @jtmiclat.
    """

    _template = Template(
        """
            {% macro script(this, kwargs) -%}
            let protocol = new pmtiles.Protocol();
            maplibregl.addProtocol("pmtiles", protocol.tile);

           {{ this._parent.get_name() }}.createPane('overlay');
           {{ this._parent.get_name() }}.getPane('overlay').style.zIndex = 650;
           {{ this._parent.get_name() }}.getPane('overlay').style.pointerEvents = 'none';

            var {{ this.get_name() }} = L.maplibreGL({
            pane: 'overlay',
            style: {{ this.style|tojson}}
            }).addTo({{ this._parent.get_name() }});

            {%- endmacro %}
            """
    )
    default_css = [
        ("maplibre_css", "https://unpkg.com/maplibre-gl@2.4.0/dist/maplibre-gl.css")
    ]

    default_js = [
        ("pmtiles", "https://unpkg.com/pmtiles@2.7.1/dist/index.js"),
        ("maplibre-lib", "https://unpkg.com/maplibre-gl@2.2.1/dist/maplibre-gl.js"),
        (
            "maplibre-leaflet",
            "https://unpkg.com/@maplibre/maplibre-gl-leaflet@0.0.19/leaflet-maplibre-gl.js",
        ),
    ]

    def __init__(
        self,
        url,
        style=None,
        name=None,
        overlay=True,
        show=True,
        control=True,
        **kwargs,
    ):
        """
        Initializes a PMTilesLayer object.

        Args:
            url (str): The URL of the PMTiles file.
            style (dict, optional): The style to apply to the layer. Defaults to None.
            name (str, optional): The name of the layer. Defaults to None.
            overlay (bool, optional): Whether the layer should be added as an overlay. Defaults to True.
            show (bool, optional): Whether the layer should be shown initially. Defaults to True.
            control (bool, optional): Whether to include the layer in the layer control. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the Layer constructor.

        Returns:
            None
        """

        self.layer_name = name if name else "PMTilesVector"

        super().__init__(
            name=self.layer_name, overlay=overlay, show=show, control=control, **kwargs
        )

        self.url = url
        self._name = "PMTilesVector"

        if style is not None:
            self.style = style
        else:
            self.style = {}
