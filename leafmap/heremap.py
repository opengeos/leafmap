"""
This module defines here-map-widget-for-jupyter as backend for leafmap library.
For more details about Here Map Widget for Jupyter please check: https://github.com/heremaps/here-map-widget-for-jupyter
"""
import os
import json
import random
import requests
import here_map_widget
import ipywidgets as widgets
from .basemaps import here_basemaps

from here_map_widget import (
    FullscreenControl,
    MeasurementControl,
    ScaleBar,
    ZoomControl,
    ImageTileProvider,
    TileLayer,
    GeoJSON,
    WidgetControl,
    LayersControl,
)


class Map(here_map_widget.Map):
    """
    The Map class inherits here_map_widget.Map. The arguments you can pass to the Map can be found
    at https://here-map-widget-for-jupyter.readthedocs.io/en/latest/api_reference/map.html.

    Returns:
        object: here_map_widget map object.
    """

    def __init__(self, api_key, **kwargs):
        if "center" not in kwargs:
            kwargs["center"] = [40, -100]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 4

        if "basemap" in kwargs:
            kwargs["basemap"] = here_basemaps[kwargs["basemap"]]

        super().__init__(api_key=api_key, **kwargs)
        self.baseclass = "here_map_widget"

        if "height" not in kwargs:
            self.layout.height = "600px"
        else:
            self.layout.height = kwargs["height"]

        if kwargs.get("layers_control"):
            self.add_control(LayersControl(alignment="RIGHT_TOP"))

        if "zoom_control" not in kwargs:
            kwargs["zoom_control"] = True

        if kwargs["zoom_control"]:
            self.add_control(ZoomControl(alignment="LEFT_TOP"))
        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True
        if kwargs["fullscreen_control"]:
            self.add_control(FullscreenControl(alignment="LEFT_TOP"))

        if kwargs.get("measure_control"):
            self.add_control(MeasurementControl(alignment="LEFT_TOP"))
        if "scale_control" not in kwargs:
            kwargs["scale_control"] = True
        if kwargs["scale_control"]:
            self.add_control(ScaleBar(alignment="LEFT_BOTTOM"))

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

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
        """
        try:
            if basemap in here_basemaps and here_basemaps[basemap] not in self.layers:
                self.basemap = here_basemaps[basemap]
        except Exception:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(here_basemaps.keys())
                )
            )

    def add_tile_layer(
        self,
        url="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="Untitled",
        attribution="",
        opacity=1.0,
        **kwargs
    ):
        """Adds a TileLayer to the map.

        Args:
            url (str, optional): The URL of the tile layer. Defaults to 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """
        try:
            if "style" in kwargs:
                style = kwargs.pop("style")
            else:
                style = {}
            provider = ImageTileProvider(
                url=url, opacity=opacity, attribution=attribution, **kwargs
            )
            tile_layer = TileLayer(provider=provider, name=name, style=style)
            self.add_layer(tile_layer)
        except Exception as e:
            print("Failed to add the specified TileLayer.")
            raise Exception(e)

    def add_geojson(
        self,
        in_geojson,
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
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
        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """

        try:
            if isinstance(in_geojson, str):
                if in_geojson.startswith("http"):
                    data = requests.get(in_geojson).json()
                else:
                    in_geojson = os.path.abspath(in_geojson)
                    if not os.path.exists(in_geojson):
                        raise FileNotFoundError("The provided GeoJSON file could not be found.")

                    with open(in_geojson, encoding="utf-8") as f:
                        data = json.load(f)
            elif isinstance(in_geojson, dict):
                data = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        if not style:
            style = {
                "strokeColor": "black",
                "lineWidth": 1,
            }
        else:
            style.setdefault("lineWidth", 1)

        if not hover_style:
            hover_style = {
                "fillColor": random.choice(fill_colors) if fill_colors else ["rgba(0,0,0,0.5)"],
                "strokeColor": "black",
                "lineWidth": style["lineWidth"] + 1,
            }

        toolbar_button = widgets.ToggleButton(
            value=True,
            tooltip="Toolbar",
            icon="info",
            layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
        )

        close_button = widgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            # button_style="primary",
            layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
        )

        html = widgets.HTML()
        html.layout.margin = "0px 10px 0px 10px"
        html.layout.max_height = "250px"
        html.layout.max_width = "250px"

        output_widget = widgets.VBox([widgets.HBox([toolbar_button, close_button]), html])
        info_control = WidgetControl(widget=output_widget, position="bottomright")

        if info_mode in ["on_hover", "on_click"]:
            self.add_control(info_control)

        def _toolbar_btn_click(change):
            if change["new"]:
                close_button.value = False
                output_widget.children = [
                    widgets.VBox([widgets.HBox([toolbar_button, close_button]), html])
                ]
            else:
                output_widget.children = [widgets.HBox([toolbar_button, close_button])]

        toolbar_button.observe(_toolbar_btn_click, "value")

        def _close_btn_click(change):
            if change["new"]:
                toolbar_button.value = False
                if info_control in self.controls:
                    self.remove_control(info_control)
                output_widget.close()

        close_button.observe(_close_btn_click, "value")

        def _update_html(feature, **_):

            value = [
                "<h5><b>{}: </b>{}</h5>".format(prop, feature["properties"][prop])
                for prop in feature["properties"].keys()
            ][:-1]

            value = """{}""".format("".join(value))
            html.value = value

        geojson = GeoJSON(
            data=data,
            style=style if style else {},
            hover_style=hover_style if hover_style else {},
            style_callback=style_callback,
            name=layer_name,
        )

        if info_mode == "on_hover":
            geojson.on_hover(_update_html)
        elif info_mode == "on_click":
            geojson.on_click(_update_html)

        self.add_layer(geojson)
