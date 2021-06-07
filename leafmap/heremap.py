import os
import json
import random
import requests
import here_map_widget
from .basemaps import here_basemaps
from .common import kml_to_geojson

from here_map_widget import (
    FullscreenControl,
    MeasurementControl,
    ScaleBar,
    ZoomControl,
    ImageTileProvider,
    TileLayer,
    GeoJSON
)


class Map(here_map_widget.Map):
    """
    The Map class inherits here_map_widget.Map. The arguments you can pass to the Map can be found at https://here-map-widget-for-jupyter.readthedocs.io/en/latest/api_reference/map.html.

    Returns:
        object: here_map_widget map object.
    """

    def __init__(self, apikey, **kwargs):
        if "center" not in kwargs:
            kwargs["center"] = [40, -100]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 4
        super().__init__(api_key=apikey, **kwargs)
        self.baseclass = "here_map_widget"

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
        if "toolbar_control" not in kwargs:
            kwargs["toolbar_control"] = True
        # if kwargs["toolbar_control"]:
        #     from .toolbar import main_toolbar
        #
        #     main_toolbar(self)

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

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
        """
        try:
            if basemap in here_basemaps and here_basemaps[basemap] not in self.layers:
                self.add_layer(here_basemaps[basemap])
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

    def add_kml(self, in_kml=None, layer_name="Untitled", **kwargs):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            url (str): The input KML data url.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """
        if in_kml:
            in_kml = os.path.abspath(in_kml)
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The provided KML file could not be found.")

            data = kml_to_geojson(in_kml)
            geo_json = GeoJSON(data=data, name=layer_name, **kwargs)
            self.add_layer(geo_json)

    def add_shape_file(self):
        pass

    def add_geojson(self,
        in_geojson,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",):

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
                "strokeColor": 'black',
                "fillColor": 'rgba(255, 255, 255, 0.5)',
                "lineWidth": 5,
                "lineCap": 'square',
                "lineJoin" : 'bevel'
            }

        if not hover_style:
            hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}

        def random_color(feature):
            return {
                "strokeColor": "black",
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
        info_control = WidgetControl(widget=output_widget, position="bottomright")

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
                        "<h5><b>{}: </b>{}</h5>".format(prop, feature["properties"][prop])
                        for prop in feature["properties"].keys()
                    ][:-1]

            value = """{}""".format("".join(value))
            html.value = value

        if style_callback is None:
            style_callback = random_color

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

    def add_COG_layer(self):
        pass

    def add_COG_mosaic(self):
        pass

    def add_STAC_layer(self):
        pass
