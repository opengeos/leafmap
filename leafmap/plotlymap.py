import os
import numpy as np
import pandas as pd
import ipywidgets as widgets
from .basemaps import xyz_to_plotly
from .common import *
from .osm import *
from . import examples

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    raise ImportError(
        "This module requires the plotly package. Please install it using 'pip install plotly'."
    )


basemaps = xyz_to_plotly()


class Canvas:
    """The widgets.HBox containing the map and a toolbar."""

    def __init__(
        self,
        map,
        map_min_width="90%",
        map_max_width="98%",
        map_refresh=False,
        **kwargs,
    ):
        """Initialize the Canvas.

        Args:
            map (go.FigureWidget): The map to display.
            map_min_width (str, optional): The minimum width of the map. Defaults to '90%'.
            map_max_width (str, optional): The maximum width of the map. Defaults to '98%'.
            map_refresh (bool, optional): Whether to refresh the map when the map is resized. Defaults to False.
        """
        from .toolbar import plotly_toolbar

        map_widget = widgets.Output(layout=widgets.Layout(width=map_max_width))
        with map_widget:
            display(map)

        self.map = map
        self.map_min_width = map_min_width
        self.map_max_width = map_max_width
        self.map_refresh = map_refresh
        self.map_widget = map_widget

        container_widget = widgets.VBox()
        self.container_widget = container_widget

        toolbar_widget = plotly_toolbar(self)
        sidebar_widget = widgets.VBox([toolbar_widget, container_widget])
        canvas = widgets.HBox([map_widget, sidebar_widget])

        self.canvas = canvas
        self.toolbar_widget = toolbar_widget

    def toolbar_reset(self):
        """Reset the toolbar so that no tool is selected."""
        if hasattr(self, "toolbar"):
            toolbar_grid = self.toolbar
            for tool in toolbar_grid.children:
                tool.value = False


class Map(go.FigureWidget):
    """The Map class inherits the Plotly FigureWidget class. More info at https://plotly.com/python/figurewidget."""

    def __init__(
        self, center=(20, 0), zoom=1, basemap="open-street-map", height=600, **kwargs
    ):
        """Initializes a map. More info at https://plotly.com/python/mapbox-layers/

        Args:
            center (tuple, optional): Center of the map. Defaults to (20, 0).
            zoom (int, optional): Zoom level of the map. Defaults to 1.
            basemap (str, optional): Can be one of string from "open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain", "stamen-toner" or "stamen-watercolor" . Defaults to 'open-street-map'.
            height (int, optional): Height of the map. Defaults to 600.
        """
        super().__init__(**kwargs)
        self.add_scattermapbox()
        self.update_layout(
            {
                "mapbox": {
                    "style": basemap,
                    "center": {"lat": center[0], "lon": center[1]},
                    "zoom": zoom,
                },
                "margin": {"r": 0, "t": 0, "l": 0, "b": 0},
                "height": height,
            }
        )

    def show(
        self,
        toolbar=True,
        map_min_width="91%",
        map_max_width="98%",
        refresh=False,
        **kwargs,
    ):
        """Shows the map.

        Args:
            toolbar (bool, optional): Whether to show the toolbar. Defaults to True.
            map_min_width (str, optional): The minimum width of the map. Defaults to '91%'.
            map_max_width (str, optional): The maximum width of the map. Defaults to '98%'.
            refresh (bool, optional): Whether to refresh the map when the map is resized. Defaults to False.

        Returns:
            Canvas: Map canvas.
        """
        if not toolbar:
            super().show(**kwargs)
        else:
            canvas = Canvas(
                self,
                map_min_width=map_min_width,
                map_max_width=map_max_width,
                map_refresh=refresh,
            )
            return canvas.canvas

    def clear_controls(self):
        """Removes all controls from the map."""
        config = {
            "scrollZoom": True,
            "displayModeBar": False,
            "editable": True,
            "showLink": False,
            "displaylogo": False,
        }
        self.show(toolbar=False, config=config)

    def add_controls(self, controls):
        """Adds controls to the map.

        Args:
            controls (list): List of controls to add, e.g., ['drawline', 'drawopenpath', 'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'] See https://bit.ly/33Tmqxr
        """
        if isinstance(controls, str):
            controls = [controls]
        elif not isinstance(controls, list):
            raise ValueError(
                "Controls must be a string or a list of strings. See https://bit.ly/33Tmqxr"
            )

        self.update_layout(modebar_add=controls)

    def remove_controls(self, controls):
        """Removes controls to the map.

        Args:
            controls (list): List of controls to remove, e.g., ["zoomin", "zoomout", "toimage", "pan", "resetview"]. See https://bit.ly/3Jk7wkb
        """
        if isinstance(controls, str):
            controls = [controls]
        elif not isinstance(controls, list):
            raise ValueError(
                "Controls must be a string or a list of strings. See https://bit.ly/3Jk7wkb"
            )

        self.update_layout(modebar_remove=controls)

    def set_center(self, lat, lon, zoom=None):
        """Sets the center of the map.

        Args:
            lat (float): Latitude.
            lon (float): Longitude.
            zoom (int, optional): Zoom level of the map. Defaults to None.
        """
        self.update_layout(
            mapbox=dict(
                center=dict(lat=lat, lon=lon),
                zoom=zoom if zoom is not None else self.layout.mapbox.zoom,
            )
        )

    def add_basemap(self, basemap="ROADMAP"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'ROADMAP'.
        """
        if basemap not in basemaps:
            raise ValueError(
                f"Basemap {basemap} not found. Choose from {','.join(basemaps.keys())}"
            )

        if basemap in self.get_tile_layers():
            self.remove_basemap(basemap)
        layers = list(self.layout.mapbox.layers) + [basemaps[basemap]]
        self.update_layout(mapbox_layers=layers)

    def remove_basemap(self, name):
        """Removes a basemap from the map.

        Args:
            name (str): Name of the basemap to remove.
        """
        layers = list(self.layout.mapbox.layers)
        layers = [layer for layer in layers if layer["name"] != name]
        self.layout.mapbox.layers = layers

    def add_mapbox_layer(self, style, access_token=None):
        """Adds a mapbox layer to the map.

        Args:
            layer (str | dict): Layer to add. Can be "basic", "streets", "outdoors", "light", "dark", "satellite", or "satellite-streets". See https://plotly.com/python/mapbox-layers/ and https://docs.mapbox.com/mapbox-gl-js/style-spec/
            access_token (str, optional): The Mapbox Access token. It can be set as an environment variable "MAPBOX_TOKEN". Defaults to None.
        """

        if access_token is None:
            access_token = os.environ.get("MAPBOX_TOKEN")

        self.update_layout(
            mapbox_style=style, mapbox_layers=[], mapbox_accesstoken=access_token
        )

    def add_layer(self, layer, name=None, **kwargs):
        """Adds a layer to the map.

        Args:
            layer (plotly.graph_objects): Layer to add.
            name (str, optional): Name of the layer. Defaults to None.
        """
        if isinstance(name, str):
            layer.name = name
        self.add_trace(layer, **kwargs)

    def remove_layer(self, name):
        """Removes a layer from the map.

        Args:
            name (str): Name of the layer to remove.
        """
        if name in self.get_data_layers():
            self.data = [layer for layer in self.data if layer.name != name]
        elif name in self.get_tile_layers():
            self.layout.mapbox.layers = [
                layer for layer in self.layout.mapbox.layers if layer["name"] != name
            ]

    def clear_layers(self, clear_basemap=False):
        """Clears all layers from the map.

        Args:
            clear_basemap (bool, optional): If True, clears the basemap. Defaults to False.
        """
        if clear_basemap:
            self.data = []
        else:
            if len(self.data) > 1:
                self.data = self.data[:1]

    def get_layers(self):
        """Returns a dictionary of all layers in the map.
        Returns:
            dict: A dictionary of all layers in the map.
        """
        layers = {}

        for layer in self.layout.mapbox.layers:
            if layer["name"] is not None:
                layers[layer["name"]] = layer

        for layer in self.data:
            if layer.name is not None and layer.name != "trace 0":
                layers[layer.name] = layer

        return layers

    def get_tile_layers(self):
        """Returns a dictionary of tile layers in the map.

        Returns:
            dict: A dictionary of tile layers in the map.
        """

        layers = {}

        for layer in self.layout.mapbox.layers:
            if layer["name"] is not None:
                layers[layer["name"]] = layer

        return layers

    def get_data_layers(self):
        """Returns a dictionary of data layers in the map.

        Returns:
            dict: A dictionary of data layers in the map.
        """

        layers = {}

        for layer in self.data:
            if layer.name is not None and layer.name != "trace 0":
                layers[layer.name] = layer

        return layers

    def find_layer_index(self, name):
        """Finds the index of a layer.

        Args:
            name (str): Name of the layer to find.

        Returns:
            int: Index of the layer.
        """
        for i, layer in enumerate(self.data):
            if layer.name == name:
                return i

        for i, layer in enumerate(self.layout.mapbox.layers):
            if layer["name"] == name:
                return i

        return None

    def set_layer_visibility(self, name, show=True):
        """Sets the visibility of a layer.

        Args:
            name (str): Name of the layer to set.
            show (bool, optional): If True, shows the layer. Defaults to True.
        """

        if name in self.get_tile_layers():
            index = self.find_layer_index(name)
            self.layout.mapbox.layers[index].visible = show
        elif name in self.get_data_layers():
            index = self.find_layer_index(name)
            self.data[index].visible = show
        else:
            print(f"Layer {name} not found.")

    def set_layer_opacity(self, name, opacity=1):
        """Sets the visibility of a layer.

        Args:
            name (str): Name of the layer to set.
            opacity (float, optional): Opacity of the layer. Defaults to 1.
        """

        if name in self.get_tile_layers():
            index = self.find_layer_index(name)
            self.layout.mapbox.layers[index].opacity = opacity
        elif name in self.get_data_layers():
            index = self.find_layer_index(name)
            layer = self.data[index]
            if hasattr(layer, "opacity"):
                layer.opacity = opacity
            elif hasattr(layer, "marker"):
                layer.marker.opacity = opacity
        else:
            print(f"Layer {name} not found.")

    def add_tile_layer(
        self,
        url,
        name="TileLayer",
        attribution="",
        opacity=1.0,
        **kwargs,
    ):
        """Adds a TileLayer to the map.

        Args:
            url (str): The URL of the tile layer.
            name (str, optional): Name of the layer. Defaults to 'TileLayer'.
            attribution (str): The attribution to use. Defaults to "".
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """

        layer = {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": attribution,
            "source": [url],
            "opacity": opacity,
            "name": name,
        }
        layers = list(self.layout.mapbox.layers) + [layer]
        self.update_layout(mapbox_layers=layers)

    def add_cog_layer(
        self,
        url,
        name="Untitled",
        attribution="",
        opacity=1.0,
        bands=None,
        titiler_endpoint=None,
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer, e.g., 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            bands (list, optional): The bands to use. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        center = cog_center(url, titiler_endpoint)  # (lon, lat)
        self.add_tile_layer(tile_url, name, attribution, opacity)
        self.set_center(lon=center[0], lat=center[1], zoom=10)

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
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
            collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
            items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        center = stac_center(url, collection, item, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity)
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_mosaic_layer(
        self,
        url,
        titiler_endpoint=None,
        name="Mosaic Layer",
        attribution="",
        opacity=1.0,
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a MosaicJSON.
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'Mosaic Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """
        tile_url = mosaic_tile(url, titiler_endpoint, **kwargs)
        center = mosaic_info(url, titiler_endpoint)["center"]
        self.add_tile_layer(tile_url, name, attribution, opacity)
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_planet_by_month(
        self,
        year=2016,
        month=1,
        api_key=None,
        token_name="PLANET_API_KEY",
        name=None,
        attribution="",
        opacity=1.0,
    ):
        """Adds Planet global mosaic by month to the map. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

        Args:
            year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
            api_key (str, optional): The Planet API key. Defaults to None.
            token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
            name (str, optional): Name of the layer. Defaults to 'TileLayer'.
            attribution (str): The attribution to use. Defaults to "".
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """
        if name is None:
            name = str(year) + "-" + str(month).zfill(2)
        tile_url = planet_by_month(year, month, api_key, token_name)
        self.add_tile_layer(
            tile_url, name=name, attribution=attribution, opacity=opacity
        )

    def add_planet_by_quarter(
        self,
        year=2016,
        quarter=1,
        api_key=None,
        token_name="PLANET_API_KEY",
        name=None,
        attribution="",
        opacity=1.0,
    ):
        """Adds Planet global mosaic by month to the map. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

        Args:
            year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
            api_key (str, optional): The Planet API key. Defaults to None.
            token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
            name (str, optional): Name of the layer. Defaults to 'TileLayer'.
            attribution (str): The attribution to use. Defaults to "".
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """
        if name is None:
            name = str(year) + "-" + "q" + str(quarter)
        tile_url = planet_by_quarter(year, quarter, api_key, token_name)
        self.add_tile_layer(
            tile_url, name=name, attribution=attribution, opacity=opacity
        )

    def save(self, file, format=None, width=None, height=None, scale=None, **kwargs):
        """Convert a map to a static image and write it to a file or writeable object

        Args:
            file (str): A string representing a local file path or a writeable object (e.g. a pathlib.Path object or an open file descriptor)
            format (str, optional): The desired image format. One of png, jpg, jpeg, webp, svg, pdf, eps. Defaults to None.
            width (int, optional): The width of the exported image in layout pixels. If the `scale` property is 1.0, this will also be the width of the exported image in physical pixels.. Defaults to None.
            height (int, optional): The height of the exported image in layout pixels. If the `scale` property is 1.0, this will also be the height of the exported image in physical pixels.. Defaults to None.
            scale (int, optional): The scale factor to use when exporting the figure. A scale factor larger than 1.0 will increase the image resolution with respect to the figure's layout pixel dimensions. Whereas as scale factor of less than 1.0 will decrease the image resolution.. Defaults to None.
        """
        self.write_image(
            file, format=format, width=width, height=height, scale=scale, **kwargs
        )

    def add_choropleth_map(
        self, data, name=None, z=None, colorscale="Viridis", **kwargs
    ):
        """Adds a choropleth map to the map.

        Args:
            data (str): File path to vector data, e.g., https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/countries.geojson
            name (str, optional): Name of the layer. Defaults to None.
            z (str, optional): Z value of the data. Defaults to None.
            colorscale (str, optional): Color scale of the data. Defaults to "Viridis".
        """
        check_package("geopandas")
        import json
        import geopandas as gpd

        gdf = gpd.read_file(data).to_crs(epsg=4326)
        geojson = json.loads(gdf.to_json())

        self.add_choroplethmapbox(
            geojson=geojson,
            locations=gdf.index,
            z=gdf[z],
            name=name,
            colorscale=colorscale,
            **kwargs,
        )

    def add_scatter_plot_demo(self, **kwargs):
        """Adds a scatter plot to the map."""
        lons = np.random.random(1000) * 360.0
        lats = np.random.random(1000) * 180.0 - 90.0
        z = np.random.random(1000) * 50.0
        self.add_scattermapbox(
            lon=lons, lat=lats, marker={"color": z}, name="Random points", **kwargs
        )

    def add_heatmap(
        self,
        data,
        latitude="latitude",
        longitude="longitude",
        z="value",
        radius=10,
        colorscale=None,
        name="Heat map",
        **kwargs,
    ):
        """Adds a heat map to the map. Reference: https://plotly.com/python/mapbox-density-heatmaps

        Args:
            data (str | pd.DataFrame): File path or HTTP URL to the input file or a . For example, https://raw.githubusercontent.com/plotly/datasets/master/earthquakes-23k.csv
            latitude (str, optional): The column name of latitude. Defaults to "latitude".
            longitude (str, optional): The column name of longitude. Defaults to "longitude".
            z (str, optional): The column name of z values. Defaults to "value".
            radius (int, optional): Radius of each “point” of the heatmap. Defaults to 25.
            colorscale (str, optional): Color scale of the data, e.g., Viridis. See https://plotly.com/python/builtin-colorscales. Defaults to None.
            name (str, optional): Layer name to use. Defaults to "Heat map".

        """

        if isinstance(data, str):
            df = pd.read_csv(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("data must be a DataFrame or a file path.")

        heatmap = go.Densitymapbox(
            lat=df[latitude],
            lon=df[longitude],
            z=df[z],
            radius=radius,
            colorscale=colorscale,
            name=name,
            **kwargs,
        )
        self.add_trace(heatmap)

    def add_heatmap_demo(self, **kwargs):
        """Adds a heatmap to the map."""
        quakes = pd.read_csv(
            "https://raw.githubusercontent.com/plotly/datasets/master/earthquakes-23k.csv"
        )
        heatmap = go.Densitymapbox(
            lat=quakes.Latitude,
            lon=quakes.Longitude,
            z=quakes.Magnitude,
            radius=10,
            name="Earthquake",
            **kwargs,
        )

        self.add_basemap("Stamen.Terrain")
        self.add_trace(heatmap)

    def add_gdf_demo(
        self,
        gdf,
        label_col,
        color_col,
        color_continuous_scale="Viridis",
        **kwargs,
    ):

        check_package("geopandas", "https://geopandas.org")
        import geopandas as gpd

        geojson_url = str(gdf)

        if isinstance(gdf, str):
            gdf = gpd.read_file(gdf).to_crs(epsg=4326)

        fig = go.Choroplethmapbox(
            geojson=geojson_url,
            featureidkey="properties.{}".format(label_col),
            locations=gdf[label_col],
            z=gdf[color_col],
            autocolorscale=False,
            colorscale=color_continuous_scale,
            marker_line_color="peachpuff",
            colorbar=dict(
                title={"text": "Legend"},
                thickness=15,
                len=0.35,
                bgcolor="rgba(255,255,255,0.6)",
                xanchor="left",
                x=0.02,
                yanchor="bottom",
                y=0.05,
            ),
        )
        self.add_trace(fig)

    def add_gdf(
        self,
        gdf,
        label_col=None,
        color_col=None,
        labels=None,
        opacity=1.0,
        zoom=None,
        color_continuous_scale="Viridis",
        **kwargs,
    ):
        """Adds a GeoDataFrame to the map.
        Args:
            gdf (GeoDataFrame): A GeoDataFrame.
            label_col (str, optional): The column name of locations. Defaults to None.
            color_col (str, optional): The column name of color. Defaults to None.
        """

        check_package("geopandas", "https://geopandas.org")
        import geopandas as gpd

        if isinstance(gdf, str):
            gdf = gpd.read_file(gdf)

        if not isinstance(gdf, gpd.GeoDataFrame):
            raise ValueError("gdf must be a GeoDataFrame.")

        gdf = gdf.to_crs(epsg=4326)
        # geom_type = gdf_geom_type(gdf)
        center_lon, center_lat = gdf_centroid(gdf)

        if isinstance(label_col, str):
            gdf = gdf.set_index(label_col)
            if label_col == color_col:
                gdf[label_col] = gdf.index
            label_col = gdf.index
        elif label_col is None:
            label_col = gdf.index

        if isinstance(color_col, str):
            if color_col not in gdf.columns:
                raise ValueError(
                    f"color must be a column name in the GeoDataFrame. Can be one of {','.join(gdf.columns)} "
                )
        fig = px.choropleth_mapbox(
            gdf,
            geojson=gdf.geometry,
            locations=label_col,
            color=color_col,
            color_continuous_scale=color_continuous_scale,
            opacity=opacity,
            labels=labels,
            # mapbox_style="carto-positron",
            **kwargs,
        )

        self.add_traces(fig.data)
        self.set_center(center_lat, center_lon, zoom)

    def add_geojson_layer(self, geojson_in, name, color="blue", opacity=1):
        """Prepare proper and give style for different type of Geometry

        Args:
            in_geojson (str | dict): The file path or http URL to the input GeoJSON or a dictionary containing the geojson.
            name (str): Name for the Layer
            color (str, optional): Plain name for color (e.g: blue) or color code (e.g: #FF0000)
            opacity(float, optional): opacity of the layer in Map
        """

        import json
        import requests

        if isinstance(geojson_in, dict):
            data = geojson_in
        elif geojson_in.startswith("http"):
            data = requests.get(geojson_in).json()
        elif geojson_in.lower().endswith((".json", ".geojson")):
            with open(geojson_in) as fp:
                data = json.load(fp)
        else:
            data = geojson_in

        """ Only Checking Geometry of first feature( todo : handle multiple type of Geometry in same geojson ) """
        first_feature = data["features"][0]
        geometry_type = first_feature["geometry"]["type"]

        if geometry_type.lower() in ["polygon", "multipolygon"]:
            type = "fill"
        elif geometry_type.lower() in ["linstring", "multilinestring"]:
            type = "line"
        elif geometry_type.lower() in ["point", "multipoint"]:
            type = "circle"
        else:
            type = "fill"

        self.add_geojson(data, name, type, color, opacity)

    def add_geojson(self, data, name, type, color, opacity):
        """Add layers to the Map

        Args:
            data (dict): Geojson in Dict form
            name (str): Name for the Layer
            color (str, optional): Plain name for color (e.g: blue) or color code (e.g: #FF0000)
            opacity(float, optional): opacity of the layer in Map
        """

        new_layer = {
            "source": data,
            "name": name,
            "type": type,
            "opacity": opacity,
            "color": color,
        }
        if type == "circle":
            new_layer["circle"] = {"radius": 5}
        existing_layers = list(self.layout.mapbox.layers)

        existing_layers.append(new_layer)

        self.update_layout(mapbox={"layers": tuple(existing_layers)})


def fix_widget_error():
    """
    Fix FigureWidget - 'mapbox._derived' Value Error.
    Adopted from: https://github.com/plotly/plotly.py/issues/2570#issuecomment-738735816
    """
    import shutil
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("plotly", "plotly.py"))

    basedatatypesPath = os.path.join(pkg_dir, "basedatatypes.py")

    backup_file = basedatatypesPath.replace(".py", "_bk.py")
    shutil.copyfile(basedatatypesPath, backup_file)

    # read basedatatypes.py
    with open(basedatatypesPath, "r") as f:
        lines = f.read()

    find = "if not BaseFigure._is_key_path_compatible(key_path_str, self.layout):"

    replace = """if not BaseFigure._is_key_path_compatible(key_path_str, self.layout):
                if key_path_str == "mapbox._derived":
                    return"""

    # add new text
    lines = lines.replace(find, replace)

    # overwrite old 'basedatatypes.py'
    with open(basedatatypesPath, "w") as f:
        f.write(lines)
