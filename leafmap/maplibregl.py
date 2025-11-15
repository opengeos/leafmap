"""The maplibregl module provides the Map class for creating interactive maps using the maplibre.ipywidget module."""

import json
import logging
import os
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import geopandas as gpd
import ipyvuetify as v
import ipywidgets as widgets
import pandas as pd
import requests
import xyzservices
from box import Box
from IPython.display import display

logging.getLogger("maplibre").setLevel(logging.ERROR)

from maplibre import Layer, LayerType, MapOptions
from maplibre.basemaps import background, construct_carto_basemap_url
from maplibre.controls import (
    AttributionControl,
    FullscreenControl,
    GeolocateControl,
    GlobeControl,
    Marker,
    NavigationControl,
    ScaleControl,
)
from maplibre.ipywidget import MapWidget
from maplibre.sources import GeoJSONSource, RasterTileSource
from maplibre.utils import get_bounds

from . import common
from .basemaps import xyz_to_leaflet
from .common import (
    _in_colab_shell,
    configure_jupyterhub,
    df_to_gdf,
    download_file,
    download_files,
    ee_initialize,
    execute_maplibre_notebook_dir,
    filter_geom_type,
    find_files,
    gdb_to_vector,
    generate_index_html,
    generate_latlon_grid,
    geojson_bounds,
    geojson_to_gdf,
    geojson_to_pmtiles,
    get_api_key,
    get_bounds,
    get_ee_tile_url,
    get_overture_data,
    get_overture_latest_release,
    init_duckdb_tiles,
    nasa_data_download,
    nasa_data_login,
    pandas_to_geojson,
    pmtiles_metadata,
    pmtiles_style,
    random_string,
    read_geojson,
    read_vector,
    run_titiler,
    sort_files,
    stac_assets,
    start_duckdb_tile_server,
    start_martin,
    start_server,
    stop_martin,
)
from .map_widgets import TabWidget
from .plot import bar_chart, histogram, line_chart, pie_chart

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
            "globe": "top-right",
        },
        projection: str = "mercator",
        use_message_queue: bool = None,
        add_sidebar: Optional[bool] = None,
        add_floating_sidebar: Optional[bool] = None,
        sidebar_visible: bool = False,
        sidebar_width: int = 360,
        sidebar_args: Optional[Dict] = None,
        layer_manager_expanded: bool = True,
        **kwargs: Any,
    ):
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
            projection (str, optional): The projection of the map. It can be
                "mercator" or "globe". Defaults to "mercator".
            use_message_queue (bool, optional): Whether to use the message queue.
                Defaults to None. If None, it will check the environment variable
                "USE_MESSAGE_QUEUE". If it is set to "True", it will use the message queue, which
                is needed to export the map to HTML. If it is set to "False", it will not use the message
                queue, which is needed to display the map multiple times in the same notebook.
            add_sidebar (bool, optional): Whether to add a sidebar to the map.
                Defaults to False. If True, the map will be displayed in a sidebar.
            add_floating_sidebar (bool, optional): Whether to add a floating sidebar to the map.
                Defaults to True. If True, the map will be displayed in a floating sidebar.
            sidebar_visible (bool, optional): Whether the sidebar is visible. Defaults to False.
            sidebar_width (int, optional): The width of the sidebar in pixels. Defaults to 360.
            sidebar_args (dict, optional): The arguments for the sidebar. It can
                be a dictionary with the following keys: "sidebar_visible", "min_width",
                "max_width", and "sidebar_content". Defaults to None. If None, it will
                use the default values for the sidebar.
            layer_manager_expanded (bool, optional): Whether the layer manager is expanded. Defaults to True.
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

            if style.startswith("http"):
                response = requests.get(style)
                if response.status_code != 200:
                    print(
                        "The provided style URL is invalid. Falling back to 'dark-matter'."
                    )
                    style = "dark-matter"
                else:
                    style = json.loads(response.text)
            elif style.startswith("3d-"):
                style = maptiler_3d_style(
                    style=style.replace("3d-", "").lower(),
                    exaggeration=kwargs.pop("exaggeration", 1),
                    tile_size=kwargs.pop("tile_size", 512),
                    hillshade=kwargs.pop("hillshade", True),
                )
            elif style.startswith("amazon-"):
                style = construct_amazon_style(
                    map_style=style.replace("amazon-", "").lower(),
                    region=kwargs.pop("region", "us-east-1"),
                    api_key=kwargs.pop("api_key", None),
                    token=kwargs.pop("token", "AWS_MAPS_API_KEY"),
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
        if use_message_queue is None:
            use_message_queue = os.environ.get("USE_MESSAGE_QUEUE", False)
        self.use_message_queue(use_message_queue)

        self.controls = {}
        for control, position in controls.items():
            self.add_control(control, position)
            self.controls[control] = position

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
        self._deck_layers = []
        self._deck_layer_ids = []
        self._deck_layer_tooltips = {}
        self._duckdb_databases = []  # Track database paths for cleanup

        if projection.lower() == "globe":
            self.add_globe_control()
            self.set_projection(
                type=[
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    10,
                    "vertical-perspective",
                    12,
                    "mercator",
                ]
            )

        if add_sidebar is None and add_floating_sidebar is None:
            add_sidebar = False
            add_floating_sidebar = True
        elif add_sidebar:
            add_floating_sidebar = False
        elif add_floating_sidebar:
            add_sidebar = False
        else:
            add_sidebar = False
            add_floating_sidebar = False

        if sidebar_args is None:
            sidebar_args = {}
        if "sidebar_visible" not in sidebar_args:
            sidebar_args["sidebar_visible"] = sidebar_visible
        if "sidebar_width" not in sidebar_args:
            if isinstance(sidebar_width, str):
                sidebar_width = int(sidebar_width.replace("px", ""))
            sidebar_args["min_width"] = sidebar_width
            sidebar_args["max_width"] = sidebar_width
        if "expanded" not in sidebar_args:
            sidebar_args["expanded"] = layer_manager_expanded
        self.sidebar_args = sidebar_args
        self.layer_manager = None
        self.container = None
        self.add_floating_sidebar_flag = add_floating_sidebar
        self.floating_sidebar_widget = None
        if add_sidebar or add_floating_sidebar:
            self._ipython_display_ = self._patched_display

    def show(
        self,
        sidebar_visible: bool = False,
        min_width: int = 360,
        max_width: int = 360,
        sidebar_content: Optional[Any] = None,
        **kwargs: Any,
    ):
        """
        Displays the map with an optional sidebar.

        Args:
            sidebar_visible (bool): Whether the sidebar is visible. Defaults to False.
            min_width (int): Minimum width of the sidebar in pixels. Defaults to 250.
            max_width (int): Maximum width of the sidebar in pixels. Defaults to 300.
            sidebar_content (Optional[Any]): Content to display in the sidebar. Defaults to None.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None
        """
        return Container(
            self,
            sidebar_visible=sidebar_visible,
            min_width=min_width,
            max_width=max_width,
            sidebar_content=sidebar_content,
            **kwargs,
        )

    def create_container(
        self,
        sidebar_visible: bool = None,
        min_width: int = None,
        max_width: int = None,
        expanded: bool = None,
        **kwargs: Any,
    ) -> v.Container:
        """
        Creates a container widget for the map with an optional sidebar.

        This method initializes a `LayerManagerWidget` and a `Container` widget to display the map
        alongside a sidebar. The sidebar can be customized with visibility, width, and additional content.

        Args:
            sidebar_visible (bool): Whether the sidebar is visible. Defaults to False.
            min_width (int): Minimum width of the sidebar in pixels. Defaults to 360.
            max_width (int): Maximum width of the sidebar in pixels. Defaults to 360.
            expanded (bool): Whether the `LayerManagerWidget` is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments passed to the `Container` widget.

        Returns:
            v.Container: The created container widget with the map and sidebar.
        """

        # Use regular container sidebar

        if sidebar_visible is None:
            sidebar_visible = self.sidebar_args.get("sidebar_visible", False)
        if min_width is None:
            min_width = self.sidebar_args.get("min_width", 360)
        if max_width is None:
            max_width = self.sidebar_args.get("max_width", 360)
        if expanded is None:
            expanded = self.sidebar_args.get("expanded", True)
        if self.layer_manager is None:
            self.layer_manager = LayerManagerWidget(self, expanded=expanded)

        container = Container(
            host_map=self,
            sidebar_visible=sidebar_visible,
            min_width=min_width,
            max_width=max_width,
            sidebar_content=[self.layer_manager],
            **kwargs,
        )
        self.container = container
        self.container.sidebar_widgets["Layers"] = self.layer_manager

        if self.add_floating_sidebar_flag:
            # Use floating sidebar
            if self.floating_sidebar_widget is not None:
                widget = self.floating_sidebar_widget
            else:
                sidebar_visible = self.sidebar_args.get("sidebar_visible", False)
                expanded = self.sidebar_args.get("expanded", True)
                position = self.sidebar_args.get("position", "top-left")
                width = self.sidebar_args.get("width", "370px")
                max_height = self.sidebar_args.get("max_height", "80vh")
                sidebar_content = self.sidebar_args.get("sidebar_content", None)

                widget = self.add_floating_sidebar(
                    position=position,
                    width=width,
                    max_height=max_height,
                    expanded=expanded,
                    sidebar_visible=sidebar_visible,
                    sidebar_content=sidebar_content,
                )
                self.floating_sidebar_widget = widget

        return container

    def _repr_html_(self, **kwargs: Any) -> None:
        """
        Displays the map in an IPython environment.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None
        """

        filename = os.environ.get("MAPLIBRE_OUTPUT", None)
        replace_key = os.environ.get("MAPTILER_REPLACE_KEY", False)
        if filename is not None:
            self.to_html(filename, replace_key=replace_key)

    def _patched_display(
        self,
        **kwargs: Any,
    ):
        """
        Displays the map in an IPython environment with a patched display method.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            None
        """

        if self.add_floating_sidebar_flag:
            # Use floating sidebar
            if self.floating_sidebar_widget is not None:
                widget = self.floating_sidebar_widget
            else:
                sidebar_visible = self.sidebar_args.get("sidebar_visible", False)
                expanded = self.sidebar_args.get("expanded", True)
                position = self.sidebar_args.get("position", "top-left")
                width = self.sidebar_args.get("width", "370px")
                max_height = self.sidebar_args.get("max_height", "80vh")
                sidebar_content = self.sidebar_args.get("sidebar_content", None)

                widget = self.add_floating_sidebar(
                    position=position,
                    width=width,
                    max_height=max_height,
                    expanded=expanded,
                    sidebar_visible=sidebar_visible,
                    sidebar_content=sidebar_content,
                )
                self.floating_sidebar_widget = widget

            if "google.colab" in sys.modules:
                import ipyvue as vue

                display(vue.Html(children=[]), widget)
            else:
                display(widget)
        else:
            # Use regular container sidebar
            if self.container is not None:
                container = self.container
            else:
                sidebar_visible = self.sidebar_args.get("sidebar_visible", False)
                min_width = self.sidebar_args.get("min_width", 360)
                max_width = self.sidebar_args.get("max_width", 360)
                expanded = self.sidebar_args.get("expanded", True)
                if self.layer_manager is None:
                    self.layer_manager = LayerManagerWidget(self, expanded=expanded)
                container = Container(
                    host_map=self,
                    sidebar_visible=sidebar_visible,
                    min_width=min_width,
                    max_width=max_width,
                    sidebar_content=[self.layer_manager],
                    **kwargs,
                )
                container.sidebar_widgets["Layers"] = self.layer_manager
                self.container = container

            if "google.colab" in sys.modules:
                import ipyvue as vue

                display(vue.Html(children=[]), container)
            else:
                display(container)

    def add_layer_manager(
        self,
        expanded: bool = True,
        height: str = "40px",
        layer_icon: str = "mdi-layers",
        close_icon: str = "mdi-close",
        label="Layers",
        background_color: str = "#f5f5f5",
        *args: Any,
        **kwargs: Any,
    ):
        if self.layer_manager is None:
            self.layer_manager = LayerManagerWidget(
                self,
                expanded=expanded,
                height=height,
                layer_icon=layer_icon,
                close_icon=close_icon,
                label=label,
                background_color=background_color,
                *args,
                **kwargs,
            )

    def set_sidebar_content(
        self, content: Union[widgets.VBox, List[widgets.Widget]]
    ) -> None:
        """
        Replaces all content in the sidebar (except the toggle button).

        Args:
            content (Union[widgets.VBox, List[widgets.Widget]]): The new content for the sidebar.
        """

        if self.container is not None:
            self.container.set_sidebar_content(content)

    def add_to_sidebar(
        self,
        widget: widgets.Widget,
        add_header: bool = True,
        widget_icon: str = "mdi-tools",
        close_icon: str = "mdi-close",
        label: str = "My Tools",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Appends a widget to the sidebar content.

        Args:
            widget (Optional[Union[widgets.Widget, List[widgets.Widget]]]): Initial widget(s) to display in the content box.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """
        # Initialize floating sidebar state if needed and we're using floating sidebar
        if (
            hasattr(self, "add_floating_sidebar_flag")
            and self.add_floating_sidebar_flag
            and not hasattr(self, "floating_sidebar_content_box")
        ):
            self.floating_sidebar_content_box = widgets.VBox(children=[])
            self._floating_sidebar_widgets = {}

        # Check if floating sidebar is being used
        if hasattr(self, "floating_sidebar_content_box"):
            # Handle floating sidebar case
            if label in self._floating_sidebar_widgets:
                self.remove_from_sidebar(name=label)

            if add_header:
                widget = CustomWidget(
                    widget,
                    widget_icon=widget_icon,
                    close_icon=close_icon,
                    label=label,
                    background_color=background_color,
                    height=height,
                    expanded=expanded,
                    host_map=self,
                    **kwargs,
                )

            self.floating_sidebar_content_box.children += (widget,)
            self._floating_sidebar_widgets[label] = widget
        else:
            # Handle regular container sidebar case
            if self.container is None:
                self.create_container(**self.sidebar_args)
            self.container.add_to_sidebar(
                widget,
                add_header=add_header,
                widget_icon=widget_icon,
                close_icon=close_icon,
                label=label,
                background_color=background_color,
                height=height,
                expanded=expanded,
                host_map=self,
                **kwargs,
            )

    def remove_from_sidebar(
        self, widget: widgets.Widget = None, name: str = None
    ) -> None:
        """
        Removes a widget from the sidebar content.

        Args:
            widget (widgets.Widget): The widget to remove from the sidebar.
            name (str): The name of the widget to remove from the sidebar.
        """
        # Check if floating sidebar is being used
        if hasattr(self, "floating_sidebar_content_box"):
            # Handle floating sidebar case
            key = None
            for key, value in self._floating_sidebar_widgets.items():
                if value == widget or key == name:
                    if widget is None:
                        widget = self._floating_sidebar_widgets[key]
                    break

            if key is not None and key in self._floating_sidebar_widgets:
                self._floating_sidebar_widgets.pop(key)
            self.floating_sidebar_content_box.children = tuple(
                child
                for child in self.floating_sidebar_content_box.children
                if child != widget
            )
        elif self.container is not None:
            # Handle regular container sidebar case
            self.container.remove_from_sidebar(widget, name)

    def set_sidebar_width(self, min_width: int = None, max_width: int = None) -> None:
        """
        Dynamically updates the sidebar's minimum and maximum width.

        Args:
            min_width (int, optional): New minimum width in pixels. If None, keep current.
            max_width (int, optional): New maximum width in pixels. If None, keep current.
        """
        if self.container is None:
            self.create_container()
        self.container.set_sidebar_width(min_width, max_width)
        self.sidebar_args["min_width"] = min_width
        self.sidebar_args["max_width"] = max_width

    def add_to_map_container(
        self, *items: Union[widgets.Widget, Iterable[widgets.Widget], None]
    ) -> None:
        """
        Append one or more widgets beneath the map (in insertion order).

        This method adds widgets to the map container while ensuring the sidebar
        remains visible and properly positioned.

        Args:
            *items: One or more widgets to add beneath the map. Can be individual
                   widgets or iterables of widgets. None values are ignored.

        Example:
            >>> import ipywidgets as widgets
            >>> m = leafmap.Map()
            >>> button = widgets.Button(description="Click me")
            >>> slider = widgets.IntSlider(value=5, min=0, max=10)
            >>> m.add_to_map_container(button, slider)
        """
        if self.container is None:
            self.create_container()
        self.container.add_to_map_container(*items)

    @property
    def sidebar_widgets(self) -> Dict[str, widgets.Widget]:
        """
        Returns a dictionary of widgets currently in the sidebar.

        Returns:
            Dict[str, widgets.Widget]: A dictionary where keys are the labels of the widgets and values are the widgets themselves.
        """
        if self.container is None:
            self.create_container()
        return self.container.sidebar_widgets

    def add(self, obj: Union[str, Any], **kwargs) -> None:
        """
        Adds a widget or layer to the map based on the type of obj.

        If obj is a string and equals "NASA_OPERA", it adds a NASA OPERA data GUI widget to the sidebar.
        Otherwise, it attempts to add obj as a layer to the map.

        Args:
            obj (Union[str, Any]): The object to add to the map. Can be a string or any other type.
            **kwargs (Any): Additional keyword arguments to pass to the widget or layer constructor.

        Returns:
            None
        """
        if isinstance(obj, str):
            if obj.upper() == "NASA_OPERA":
                from .toolbar import nasa_opera_gui

                widget = nasa_opera_gui(self, backend="maplibre", **kwargs)
                self.add_to_sidebar(
                    widget, widget_icon="mdi-satellite-variant", label="NASA OPERA"
                )

    def add_layer(
        self,
        layer: "Layer",
        before_id: Optional[str] = None,
        name: Optional[str] = None,
        opacity: float = 1.0,
        visible: bool = True,
        overwrite: bool = False,
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
            overwrite (bool, optional): If True, the function will return the
                original name even if it exists in the list. Defaults to False.

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

        name = common.get_unique_name(name, self.get_layer_names(), overwrite=overwrite)

        if name in self.get_layer_names():
            self.remove_layer(name)

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

        if self.layer_manager is not None:
            self.layer_manager.refresh()

    def remove_layer(self, name: str, **kwargs: Any) -> None:
        """
        Removes a layer from the map.

        This method removes a layer from the map using the layer's name.

        Args:
            name (str): The name of the layer to remove.

        Returns:
            None
        """
        if name in self.layer_dict:
            layer = self.layer_dict[name]
            if "type" in layer and layer["type"].startswith("Deck"):
                self.remove_deck_layers(layer_ids=[name], **kwargs)
                if self.layer_manager is not None:
                    self.layer_manager.refresh()
                return

        super().add_call("removeLayer", name)
        if name in self.layer_dict:
            if isinstance(self.layer_dict[name]["layer"], Layer):
                if hasattr(self.layer_dict[name]["layer"], "source"):
                    source = self.layer_dict[name]["layer"].source
                    self.layer_dict.pop(name)
                    if source in self.source_dict:
                        self.remove_source(source)
            else:
                self.layer_dict.pop(name)

        if self.layer_manager is not None:
            self.layer_manager.refresh()

    def add_deck_layers(
        self,
        layers: list[dict],
        tooltip: Union[str, dict] = None,
        columns: list[str] = None,
    ) -> None:
        """Add Deck.GL layers to the layer stack

        Args:
            layers (list[dict]): A list of dictionaries containing the Deck.GL layers to be added.
            tooltip (str | dict): Either a single mustache template string applied to all layers
                or a dictionary where keys are layer ids and values are mustache template strings.
            columns (list[str]): A list of column names to be used for the tooltip.
        """
        if isinstance(columns, list) and (tooltip is None):
            tooltip = "<br>".join([f"<b>{col}:</b> {{{{ {col} }}}}" for col in columns])
        if not hasattr(self, "_deck_initialized"):
            setattr(self, "_deck_initialized", True)
            super().add_deck_layers(layers, tooltip)
        else:
            super().set_deck_layers(layers, tooltip)
        self._deck_layers = layers
        self._deck_layer_ids = [layer["id"] for layer in layers]
        self._deck_layer_tooltips = tooltip

        for layer in layers:

            self.layer_dict[layer["id"]] = {
                "layer": layer,
                "opacity": layer.get("opacity", 1.0),
                "visible": layer.get("visible", True),
                "type": "Deck-" + layer.get("@@type"),
                "color": layer.get("getFillColor", "#ffffff"),
                # "tooltip": tooltip.get(layer["id"], None),
            }

        if self.layer_manager is not None:
            self.layer_manager.refresh()

    def remove_deck_layers(
        self, layer_ids: List[str] = None, tooltip: bool = None
    ) -> None:
        """Remove a list of Deck.GL layers from the map.

        Args:
            layer_ids (List[str]): A list of layer IDs to remove.
            tooltip (bool): Tooltip for the remaining layers.
        """
        if tooltip is None:
            tooltip = {}
        deck_layers = []
        deck_layer_ids = []
        for layer_id in self.layer_dict:
            layer = self.layer_dict[layer_id]["layer"]
            layer_type = self.layer_dict[layer_id]["type"]
            if layer_type.startswith("Deck"):
                deck_layers.append(layer)
                deck_layer_ids.append(layer["id"])

        if layer_ids is None:
            super().set_deck_layers([])
            for layer_id in deck_layer_ids:
                self.layer_dict.pop(layer_id)
        else:
            remaining_layers = []
            remaining_layer_ids = []
            for layer_id in deck_layer_ids:
                if layer_id not in layer_ids:
                    remaining_layers.append(self.layer_dict[layer_id]["layer"])
                    remaining_layer_ids.append(layer_id)
                else:
                    self.layer_dict.pop(layer_id)
            super().set_deck_layers(remaining_layers, tooltip=tooltip)
            self._deck_layers = remaining_layers
            self._deck_layer_ids = remaining_layer_ids
            self._deck_layer_tooltips = tooltip

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
    ):
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
        tooltip_content = "<br>".join(
            [f"<b>{col}:</b> {{{{ {col} }}}}" for col in columns]
        )

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

    def get_deck_layer(self, layer_id: str) -> dict:
        """Get a Deck.GL layer from the map.

        Args:
            layer_id (str): The ID of the layer to get.
        """
        deck_layers = self._deck_layers
        for layer in deck_layers:
            if layer["id"] == layer_id:
                return layer
        return None

    def set_deck_layer_opacity(self, layer_id: str, opacity: float) -> None:
        """Set the opacity of a Deck.GL layer.

        Args:
            layer_id (str): The ID of the layer to set the opacity of.
            opacity (float): The opacity of the layer.
        """
        deck_layer = self.get_deck_layer(layer_id)
        deck_layer_index = self._deck_layers.index(deck_layer)
        deck_layer["opacity"] = opacity
        self._deck_layers[deck_layer_index] = deck_layer
        self.layer_dict[layer_id]["opacity"] = opacity

        self.set_deck_layers(self._deck_layers, tooltip=self._deck_layer_tooltips)

    def set_deck_layer_property(self, layer_id: str, property: str, value: Any) -> None:
        """Set the property of a Deck.GL layer.

        Args:
            layer_id (str): The ID of the layer to set the property of.
            property (str): The property to set.
            value (Any): The value of the property.
        """
        deck_layer = self.get_deck_layer(layer_id)
        deck_layer_index = self._deck_layers.index(deck_layer)
        deck_layer[property] = value
        self._deck_layers[deck_layer_index] = deck_layer
        self.layer_dict[layer_id][property] = value
        self.set_deck_layers(self._deck_layers, tooltip=self._deck_layer_tooltips)

    def set_deck_layer_properties(self, layer_id: str, properties: dict) -> None:
        """Set the properties of a Deck.GL layer.

        Args:
            layer_id (str): The ID of the layer to set the properties of.
            properties (dict): The properties to set.
        """
        deck_layer = self.get_deck_layer(layer_id)
        deck_layer_index = self._deck_layers.index(deck_layer)
        deck_layer.update(properties)
        self._deck_layers[deck_layer_index] = deck_layer
        self.layer_dict[layer_id].update(properties)
        self.set_deck_layers(self._deck_layers, tooltip=self._deck_layer_tooltips)

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
            if control in self.controls:
                return

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
            elif control == "globe":
                control = GlobeControl(**kwargs)
            elif control == "draw":
                self.add_draw_control(position=position, **kwargs)
                return
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
        position: str = "top-right",
        geojson: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
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
                to "top-right".
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

        self.controls["draw"] = position

    def add_globe_control(self, position: str = "top-right", **kwargs: Any) -> None:
        """
        Adds a globe control to the map.

        This method adds a globe control to the map, allowing users to switch
        between 2D and 3D views. The position of the control can be customized.

        Args:
            position (str): The position of the control on the map. Defaults
                to "top-right".
            **kwargs (Any): Additional keyword arguments to be passed to the
                globe control.

        Returns:
            None
        """
        if "globe" not in self.controls:
            self.add_control(GlobeControl(), position=position, **kwargs)

    def add_search_control(
        self,
        position: str = "top-right",
        api_key: str = None,
        collapsed: bool = True,
        **kwargs: Any,
    ):
        """
        Adds a search control to the map.

        Args:
            position (str): The position of the control on the map. Defaults to "top-right".
            api_key (str): The API key for the search control. Defaults to None.
                If not provided, it will be retrieved from the environment variable MAPTILER_KEY.
            collapsed (bool): Whether the control is collapsed. Defaults to True.
            **kwargs: Additional keyword arguments to be passed to the search control.
                See https://eoda-dev.github.io/py-maplibregl/api/controls/#maplibre.controls.MapTilerGeocodingControl
        """
        from maplibre.controls import MapTilerGeocodingControl

        if api_key is None:
            api_key = common.get_api_key("MAPTILER_KEY")
            if api_key is None:
                print(
                    "An MapTiler API key is required. Please set the MAPTILER_KEY environment variable."
                )
                return

        control = MapTilerGeocodingControl(
            api_key=api_key, collapsed=collapsed, **kwargs
        )
        self.add_control(control, position=position)

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

    def remove_source(self, id: str) -> None:
        """
        Removes a source from the map.
        """
        super().add_call("removeSource", id)
        if id in self.source_dict:
            self.source_dict.pop(id)
        if id in self.source_names:
            self.source_names.remove(id)

    def set_data(self, id: str, data: Union[str, Dict]) -> None:
        """
        Sets the data for a source.

        Args:
            id (str): The ID of the source.
            data (str or dict): The data to set for the source.

        Returns:
            None
        """
        if id in self.layer_names:
            id = self.layer_dict[id]["layer"].source
        elif id in self.source_names:
            pass
        else:
            raise ValueError(f"Source {id} not found.")

        super().set_data(id, data)

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

    def set_terrain(
        self,
        source: str = "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png",
        exaggeration: float = 1.0,
        tile_size: int = 256,
        encoding: str = "terrarium",
        source_id: str = "terrain-dem",
    ) -> None:
        """Add terrain visualization to the map.

        Args:
            source: URL template for terrain tiles. Defaults to AWS elevation tiles.
            exaggeration: Terrain exaggeration factor. Defaults to 1.0.
            tile_size: Tile size in pixels. Defaults to 256.
            encoding: Encoding for the terrain tiles. Defaults to "terrarium".
            source_id: Unique identifier for the terrain source. Defaults to "terrain-dem".
        """
        # Add terrain source
        if source is None:
            super().add_call("setTerrain", None)
            return
        self.add_source(
            source_id,
            {
                "type": "raster-dem",
                "tiles": [source],
                "tileSize": tile_size,
                "encoding": encoding,
            },
        )

        # Set terrain on the map
        terrain_config = {"source": source_id, "exaggeration": exaggeration}

        # Store terrain configuration in persistent state
        super().add_call("setTerrain", terrain_config)

    def remove_terrain(self) -> None:
        """Remove terrain visualization from the map."""
        super().add_call("setTerrain", None)

    def add_basemap(
        self,
        basemap: Union[str, xyzservices.TileProvider] = None,
        layer_name: Optional[str] = None,
        opacity: float = 1.0,
        visible: bool = True,
        attribution: Optional[str] = None,
        before_id: Optional[str] = None,
        **kwargs: Any,
    ):
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
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
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
        elif basemap == "amazon-satellite":
            region = kwargs.pop("region", "us-east-1")
            token = kwargs.pop("token", "AWS_MAPS_API_KEY")
            url = f"https://maps.geo.{region}.amazonaws.com/v2/tiles/raster.satellite/{{z}}/{{x}}/{{y}}?key={os.getenv(token)}"
            attribution = "© Amazon"
        elif basemap == "USGS.Imagery":
            url = "https://basemap.nationalmap.gov/arcgis/services/USGSImageryOnly/MapServer/WMSServer?service=WMS&request=GetMap&layers=0&styles=&format=image%2Fpng&transparent=true&version=1.1.1&height=256&width=256&srs=EPSG%3A3857&bbox={bbox-epsg-3857}"
            attribution = "© USGS"
            name = "USGS.Imagery"
            if before_id is None:
                before_id = self.first_symbol_layer_id
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
            # tile_size=256,
            **kwargs,
        )

        if layer_name is None:
            if name == "OpenStreetMap.Mapnik":
                layer_name = "OpenStreetMap"
            else:
                layer_name = name

        source_name = common.get_unique_name("source", self.source_names)
        self.add_source(source_name, raster_source)
        layer = Layer(id=layer_name, source=source_name, type=LayerType.RASTER)
        self.add_layer(layer, before_id=before_id)
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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
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
                if fit_bounds:
                    bounds = get_bounds(data)
                source = GeoJSONSource(data=data, **source_args)
            else:
                raise ValueError("The data must be a URL or a GeoJSON dictionary.")
        elif isinstance(data, dict):
            source = GeoJSONSource(data=data, **source_args)

            if fit_bounds:
                bounds = get_bounds(data)
        else:
            raise ValueError("The data must be a URL or a GeoJSON dictionary.")

        source_name = common.get_unique_name("source", self.source_names)
        self.add_source(source_name, source)
        if name is None:
            name = "GeoJSON"
        name = common.get_unique_name(name, self.layer_names, overwrite)

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
                        "circle-radius": 4,
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
            source=source_name,
            **kwargs,
        )
        self.add_layer(
            layer, before_id=before_id, name=name, visible=visible, overwrite=overwrite
        )
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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
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
            overwrite=overwrite,
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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
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
            overwrite=overwrite,
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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.

        Returns:
            None
        """

        if overwrite and name in self.get_layer_names():
            self.remove_layer(name)

        raster_source = RasterTileSource(
            tiles=[url.strip()],
            attribution=attribution,
            tile_size=tile_size,
            **source_args,
        )
        source_name = common.get_unique_name("source", self.source_names)
        self.add_source(source_name, raster_source)
        layer = Layer(id=name, source=source_name, type=LayerType.RASTER, **kwargs)
        self.add_layer(layer, before_id=before_id, name=name, overwrite=overwrite)
        self.set_visibility(name, visible)
        self.set_opacity(name, opacity)

    def add_vector_tile(
        self,
        url: str,
        layer_id: str,
        layer_type: str = "fill",
        source_layer: Optional[str] = None,
        name: Optional[str] = None,
        paint: Optional[Dict] = None,
        layout: Optional[Dict] = None,
        filter: Optional[Dict] = None,
        minzoom: Optional[int] = None,
        maxzoom: Optional[int] = None,
        visible: bool = True,
        opacity: float = 1.0,
        add_popup: bool = True,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        overwrite: bool = False,
        **kwargs: Any,
    ):
        """
        Adds a vector tile layer to the map.

        This method adds a vector tile layer to the map using a vector tile source.
        Vector tiles are a data format for efficiently storing and transmitting
        vector map data.

        Args:
            url (str): The URL template for the vector tiles. Should contain {z}, {x},
                and {y} placeholders for tile coordinates.
            layer_id (str): The ID of the layer within the vector tile source.
            layer_type (str, optional): The type of layer to create. Can be 'fill',
                'line', 'symbol', 'circle', etc. Defaults to 'fill'.
            source_layer (str, optional): The name of the source layer within the
                vector tiles. If None, uses layer_id.
            name (str, optional): The name to use for the layer. If None, uses layer_id.
            paint (dict, optional): Paint properties for the layer. If None, uses
                default styling based on layer_type.
            layout (dict, optional): Layout properties for the layer.
            filter (dict, optional): Filter expression for the layer.
            minzoom (int, optional): Minimum zoom level for the layer.
            maxzoom (int, optional): Maximum zoom level for the layer.
            visible (bool, optional): Whether the layer should be visible by default.
                Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            add_popup (bool, optional): Whether to add a popup to the layer. Defaults to True.
            before_id (str, optional): The ID of an existing layer before which the
                new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments passed to the
                vector tile source.
            overwrite (bool, optional): Whether to overwrite an existing layer with
                the same name. Defaults to False.
            **kwargs: Additional keyword arguments passed to the Layer class.

        Returns:
            None

        Example:
            >>> m = Map()
            >>> m.add_vector_tile(
            ...     url="https://api.maptiler.com/tiles/contours/tiles.json?key={api_key}",
            ...     layer_id="contour-lines",
            ...     layer_type="line",
            ...     source_layer="contour",
            ...     paint={"line-color": "#ff69b4", "line-width": 1}
            ... )
        """

        if name is None:
            name = layer_id

        if source_layer is None:
            source_layer = layer_id

        if overwrite and name in self.get_layer_names():
            self.remove_layer(name)

        # Create vector tile source
        vector_source = {
            "type": "vector",
            "url": url,
            **source_args,
        }

        # If URL doesn't contain tiles.json, assume it's a direct tile URL template
        if not url.endswith("tiles.json") and "{z}" in url:
            vector_source = {
                "type": "vector",
                "tiles": [url],
                **source_args,
            }

        source_name = common.get_unique_name("source", self.source_names)

        self.add_source(source_name, vector_source)

        # Set default paint properties based on layer type
        if paint is None:
            if layer_type == "fill":
                paint = {
                    "fill-color": "#3388ff",
                    "fill-opacity": 0.8,
                    "fill-outline-color": "#ffffff",
                }
            elif layer_type == "line":
                paint = {"line-color": "#3388ff", "line-width": 2}
            elif layer_type == "circle":
                paint = {
                    "circle-radius": 5,
                    "circle-color": "#3388ff",
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1,
                }
            elif layer_type == "symbol":
                paint = {
                    "text-color": "#000000",
                    "text-halo-color": "#ffffff",
                    "text-halo-width": 1,
                }

        # Build layer configuration
        layer_config = {
            "id": name,
            "type": layer_type,
            "source": vector_source,
            "source-layer": source_layer,
        }

        if paint is not None:
            layer_config["paint"] = paint
        if layout is not None:
            layer_config["layout"] = layout
        if filter is not None:
            layer_config["filter"] = filter
        if minzoom is not None:
            layer_config["minzoom"] = minzoom
        if maxzoom is not None:
            layer_config["maxzoom"] = maxzoom

        # Add any additional kwargs
        layer_config.update(kwargs)
        self.add_layer(
            layer_config,
            before_id=before_id,
            name=name,
            opacity=opacity,
            visible=visible,
            overwrite=overwrite,
        )

        if add_popup:
            self.add_popup(name)

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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
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
            overwrite=overwrite,
            **kwargs,
        )

    def add_nwi_basemap(
        self,
        name: str = "NWI Wetlands",
        format: str = "image/png",
        attribution: str = "USFWS",
        opacity: float = 1.0,
        visible: bool = True,
        tile_size: int = 256,
        before_id: Optional[str] = None,
        overwrite: bool = False,
        **kwargs: Any,
    ):
        """
        Adds a NWI Wetlands basemap to the map.

        This method adds a NWI Wetlands basemap to the map. The NWI Wetlands basemap is created from
            the specified URL, and it is added to the map with the specified
            name, attribution, visibility, and tile size.

        Args:
            name (str, optional): The name to use for the layer. Defaults to
                'NWI Wetlands'.
            format (str, optional): The format of the tiles in the layer.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            visible (bool, optional): Whether the layer should be visible by
                default. Defaults to True.
            tile_size (int, optional): The size of the tiles in the layer.
                Defaults to 256.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.

        Returns:
            None
        """

        url = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer"
        layers = "1"
        self.add_wms_layer(
            url,
            layers=layers,
            format=format,
            attribution=attribution,
            name=name,
            opacity=opacity,
            visible=visible,
            tile_size=tile_size,
            before_id=before_id,
            overwrite=overwrite,
            **kwargs,
        )

    def add_nwi(self, data: Union[str, Dict], name: str = "NWI Wetlands", **kwargs):
        """Adds a National Wetlands Inventory (NWI) layer to the map.

        Args:
            data (Union[str, Dict]): The data to add. It can be a URL or a dictionary.
            name (str, optional): The name of the layer. Defaults to "NWI Wetlands".
            **kwargs: Additional keyword arguments to pass to the add_vector method.

        Returns:
            None
        """

        color_map = {
            "Freshwater Forested/Shrub Wetland": (0, 136, 55),
            "Freshwater Emergent Wetland": (127, 195, 28),
            "Freshwater Pond": (104, 140, 192),
            "Estuarine and Marine Wetland": (102, 194, 165),
            "Riverine": (1, 144, 191),
            "Lake": (19, 0, 124),
            "Estuarine and Marine Deepwater": (0, 124, 136),
            "Other": (178, 134, 86),
        }

        def rgba(rgb, a=0.85):
            r, g, b = rgb
            return f"rgba({r},{g},{b},{a})"

        # Build a proper match expression WITH a default
        fill_match = ["match", ["get", "WETLAND_TYPE"]]
        for k, v in color_map.items():
            fill_match += [k, rgba(v)]
        fill_match += ["rgba(200,200,200,0.6)"]  # <-- REQUIRED default

        paint = {
            "fill-color": fill_match,
            "fill-outline-color": "rgba(0,0,0,0.25)",
        }
        self.add_vector(data, layer_type="fill", paint=paint, name=name, **kwargs)

    def add_ee_layer(
        self,
        ee_object=None,
        vis_params={},
        name: str = None,
        asset_id: str = None,
        opacity: float = 1.0,
        attribution: str = "Google Earth Engine",
        visible: bool = True,
        before_id: Optional[str] = None,
        ee_initialize: bool = False,
        overwrite: bool = False,
        **kwargs: Any,
    ):
        """
        Adds a Google Earth Engine tile layer to the map based on the tile layer URL from
            https://github.com/opengeos/ee-tile-layers/blob/main/datasets.tsv.

        Args:
            ee_object (object): The Earth Engine object to display.
            vis_params (dict): Visualization parameters. For example, {'min': 0, 'max': 100}.
            name (str, optional): The name of the tile layer. If not provided,
                the asset ID will be used. Default is None.
            asset_id (str): The ID of the Earth Engine asset.
            opacity (float, optional): The opacity of the tile layer (0 to 1).
                Default is 1.
            attribution (str, optional): The attribution text to be displayed.
                Default is "Google Earth Engine".
            visible (bool, optional): Whether the tile layer should be shown on
                the map. Default is True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            ee_initialize (bool, optional): Whether to initialize the Earth Engine
                account. Default is False.
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
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
                    overwrite=overwrite,
                    **kwargs,
                )
            else:
                print(f"The provided EE tile layer {asset_id} does not exist.")
        elif ee_object is not None:
            if isinstance(ee_object, str):
                url = get_ee_tile_url(ee_object, vis_params)
                if url is None:
                    print(f"The provided EE tile layer {ee_object} does not exist.")
                    return

                if name is None:
                    name = "EE Layer"
                self.add_tile_layer(
                    url,
                    name,
                    attribution=attribution,
                    opacity=opacity,
                    visible=visible,
                    before_id=before_id,
                    overwrite=overwrite,
                    **kwargs,
                )
            else:

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
                        overwrite=overwrite,
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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
                Defaults to "https://giswqs-titiler-endpoint.hf.space".
            fit_bounds (bool, optional): Whether to adjust the viewport of
                the map to fit the bounds of the layer. Defaults to True.
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
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

        if os.environ.get("USE_MKDOCS") is not None:
            return

        if name is None:
            name = "COG_" + common.random_string()

        if "vmin" in kwargs and "vmax" in kwargs:
            vmin = kwargs.pop("vmin")
            vmax = kwargs.pop("vmax")
            kwargs["rescale"] = f"{vmin},{vmax}"

        tile_url = common.cog_tile(
            url, bands, titiler_endpoint, nodata=nodata, **kwargs
        )
        self.add_tile_layer(
            tile_url,
            name,
            attribution,
            opacity,
            visible,
            before_id=before_id,
            overwrite=overwrite,
        )
        if fit_bounds:
            bounds = common.cog_bounds(url, titiler_endpoint)
            if bounds is not None:
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
        overwrite: bool = False,
        **kwargs: Any,
    ):
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
            nodata (int | float, optional): The nodata value to use for the layer.
            titiler_endpoint (str, optional): TiTiler endpoint, e.g., "https://giswqs-titiler-endpoint.hf.space",
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
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to False.
            **kwargs: Arbitrary keyword arguments, including bidx, expression,
                nodata, unscale, resampling, rescale, color_formula, colormap,
                colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select
                a certain bands, use bidx=[1, 2, 3]. apply a rescaling to multiple
                bands, use something like `rescale=["164,223","130,211","99,212"]`.

        Returns:
            None
        """

        if os.environ.get("USE_MKDOCS") is not None:
            return

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
            tile_url,
            name,
            attribution,
            opacity,
            visible,
            before_id=before_id,
            overwrite=overwrite,
        )
        if fit_bounds and bounds is not None:
            self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

    def add_raster(
        self,
        source,
        indexes=None,
        colormap=None,
        vmin=None,
        vmax=None,
        nodata=None,
        name="Raster",
        before_id=None,
        fit_bounds=True,
        visible=True,
        opacity=1.0,
        array_args={},
        client_args={"cors_all": True},
        overwrite: bool = True,
        **kwargs: Any,
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
            name (str, optional): The layer name to use. Defaults to 'Raster'.
            before_id (str, optional): The layer id to insert the layer before. Defaults to None.
            fit_bounds (bool, optional): Whether to zoom to the extent of the
                layer. Defaults to True.
            visible (bool, optional): Whether the layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            array_args (dict, optional): Additional arguments to pass to
                `array_to_memory_file` when reading the raster. Defaults to {}.
            client_args (dict, optional): Additional arguments to pass to
                localtileserver.TileClient. Defaults to { "cors_all": False }.
            overwrite (bool, optional): Whether to overwrite an existing layer with the same name.
                Defaults to True.
            **kwargs: Additional keyword arguments to be passed to the underlying
                `add_tile_layer` method.
        """
        import numpy as np
        import xarray as xr

        if "zoom_to_layer" in kwargs:
            fit_bounds = kwargs.pop("zoom_to_layer")

        if "layer_name" in kwargs:
            name = kwargs.pop("layer_name")

        if isinstance(source, np.ndarray) or isinstance(source, xr.DataArray):
            source = common.array_to_image(source, **array_args)

        if "colormap_name" in kwargs:
            colormap = kwargs.pop("colormap_name")

        url, tile_client = common.get_local_tile_url(
            source,
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            opacity=opacity,
            client_args=client_args,
            return_client=True,
            **kwargs,
        )

        if overwrite and name in self.get_layer_names():
            self.remove_layer(name)

        self.add_tile_layer(
            url,
            name=name,
            opacity=opacity,
            visible=visible,
            before_id=before_id,
            overwrite=overwrite,
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
        **kwargs: Any,
    ) -> str:
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
        Set the paint property of a layer.

        This method sets the opacity of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            prop (str): The paint property to set.
            value (Any): The value to set.

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
        if name == "background":
            for layer in self.get_style_layers():
                layer_type = layer.get("type")
                if layer_type != "symbol":
                    super().set_paint_property(
                        layer["id"], f"{layer_type}-opacity", opacity
                    )
                else:
                    super().set_paint_property(layer["id"], "icon-opacity", opacity)
                    super().set_paint_property(layer["id"], "text-opacity", opacity)
            return

        if name in self.layer_dict:
            if name in self._deck_layer_ids:
                self.set_deck_layer_opacity(name, opacity)
                return
            if isinstance(self.layer_dict[name]["layer"], Layer):
                layer_type = self.layer_dict[name]["layer"].to_dict()["type"]
            elif isinstance(self.layer_dict[name]["layer"], dict):
                layer_type = self.layer_dict[name]["type"]
            else:
                layer_type = self.layer_dict[name]["type"]
            prop_name = f"{layer_type}-opacity"
            self.layer_dict[name]["opacity"] = opacity
        elif name in self.style_dict:
            layer = self.style_dict[name]
            layer_type = layer.get("type")
            prop_name = f"{layer_type}-opacity"
            if "paint" in layer:
                layer["paint"][prop_name] = opacity
        if layer_type != "symbol":
            super().set_paint_property(name, prop_name, opacity)
            # if layer_type == "circle":
            #     super().set_paint_property(name, "circle-stroke-opacity", opacity)
        else:
            super().set_paint_property(name, "icon-opacity", opacity)
            super().set_paint_property(name, "text-opacity", opacity)

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

        if name == "background":
            for layer in self.get_style_layers():
                super().set_visibility(layer["id"], visible)
        else:
            super().set_visibility(name, visible)
        if name in self.layer_dict:
            self.layer_dict[name]["visible"] = visible

    def layer_interact(self, name=None) -> widgets.Widget:
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

    def style_layer_interact(self, id=None) -> widgets.Widget:
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
        source_name = common.get_unique_name("source", self.source_names)
        self.add_source(source_name, raster_source)
        layer = Layer(id=name, source=source_name, type=LayerType.RASTER)
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
            source_name = common.get_unique_name("source", self.source_names)
            self.add_source(source_name, raster_source)
            layer = Layer(id=name, source=source_name, type=LayerType.RASTER)
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
    ):
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

    def add_duckdb_layer(
        self,
        data=None,
        layer_name: Optional[str] = None,
        layer_type: str = "fill",
        paint: Optional[Dict] = None,
        layout: Optional[Dict] = None,
        filter: Optional[Dict] = None,
        database_path: str = None,
        table_name: str = "features",
        geom_column: str = "geom",
        properties: Optional[List[str]] = None,
        port: int = 8000,
        minzoom: Optional[int] = 0,
        maxzoom: Optional[int] = 22,
        min_zoom: Optional[int] = None,
        visible: bool = True,
        opacity: float = 1.0,
        fit_bounds: bool = True,
        tooltip: bool = True,
        quiet: bool = False,
        use_view: bool = False,
        src_crs: str = None,
        **kwargs: Any,
    ):
        """
        Adds a layer served from a DuckDB database via vector tiles.

        This method enables visualization of large vector datasets by serving them
        as vector tiles through a local Flask server backed by DuckDB. The data can
        either be loaded from various sources into a new/existing database, or you
        can connect to an existing database that already contains the data.

        Supports all vector formats that DuckDB's ST_Read can handle, including
        GeoJSON, Shapefile, GeoPackage, FlatGeobuf, GeoParquet, and many more
        GDAL-supported formats.

        For remote Jupyter environments, you need to configure leafmap with your JupyterHub URL:
        ```python
        import leafmap
        leafmap.configure_jupyterhub("https://your-jupyterhub-domain.com")
        ```

        Args:
            data (optional): The spatial data to visualize. Can be:
                - Path to a vector file (any format supported by DuckDB's ST_Read:
                  GeoJSON, Shapefile, GeoPackage, FlatGeobuf, GeoParquet, etc.)
                - GeoJSON dictionary
                - GeoDataFrame
                - None (if using an existing database with data already loaded)
            layer_name (str, optional): Name for the layer. If None, generates a unique name.
            layer_type (str, optional): MapLibre layer type ('fill', 'line', 'circle', 'symbol').
                Defaults to 'fill'.
            paint (dict, optional): Paint properties for the layer. If None, uses defaults
                based on layer_type.
            layout (dict, optional): Layout properties for the layer.
            filter (dict, optional): Filter expression for the layer.
            database_path (str, optional): Path to DuckDB database file.
                - If None and data is provided: creates a temporary database
                - If provided with data: loads data into this database
                - If provided without data: uses existing database (data must already be loaded)
            table_name (str, optional): Name of the table in DuckDB. Defaults to "features".
            geom_column (str, optional): Name of geometry column. Defaults to "geom".
            properties (list, optional): List of property columns to include in tiles.
                If None, includes all columns.
            port (int, optional): Port for the tile server. Defaults to 8000.
                If port is in use, automatically selects next available port.
            minzoom (int, optional): Minimum zoom level for the MapLibre layer. Defaults to 0.
            maxzoom (int, optional): Maximum zoom level for the MapLibre layer. Defaults to 22.
            min_zoom (int, optional): Minimum zoom level at which to query and serve tiles.
                Below this zoom level, empty tiles will be returned, preventing memory issues
                with large datasets. Use this to defer data loading until users zoom in closer.
                If None, tiles will be served at all zoom levels. Defaults to None.
            visible (bool, optional): Whether layer is visible initially. Defaults to True.
            opacity (float, optional): Layer opacity (0-1). Defaults to 1.0.
            fit_bounds (bool, optional): Whether to zoom to layer extent. Defaults to True.
            tooltip (bool, optional): Whether to add tooltips. Defaults to True.
            quiet (bool, optional): If True, suppress progress messages. Defaults to False.
            use_view (bool, optional): If True and data is a parquet file, create a view instead
                of a table. Views avoid data duplication but may be slower for tile serving as they
                query the source file on each tile request. Only applies to parquet files. Defaults to False.
            src_crs (str, optional): Source CRS of the input data as an EPSG code (e.g., 'EPSG:5070',
                'EPSG:4326'). If None, will attempt to auto-detect. Specify this parameter if the data
                is in a projected CRS that is not Web Mercator to ensure proper transformation. Defaults to None.
            **kwargs: Additional arguments passed to the layer configuration.

        Returns:
            None

        Raises:
            ImportError: If duckdb, flask, or flask-cors are not installed.
            ValueError: If neither data nor database_path is provided.

        Example:
            >>> import leafmap.maplibregl as leafmap
            >>> m = leafmap.Map()
            >>>
            >>> # Example 1: Load GeoJSON (creates temporary database)
            >>> m.add_duckdb_layer(
            ...     data="large_dataset.geojson",
            ...     layer_name="buildings",
            ...     layer_type="fill",
            ...     paint={"fill-color": "#3388ff", "fill-opacity": 0.7}
            ... )
            >>>
            >>> # Example 2: Load Shapefile
            >>> m.add_duckdb_layer(
            ...     data="boundaries.shp",
            ...     layer_name="boundaries",
            ...     layer_type="line",
            ...     paint={"line-color": "#ff0000", "line-width": 2}
            ... )
            >>>
            >>> # Example 3: Load GeoPackage
            >>> m.add_duckdb_layer(
            ...     data="data.gpkg",
            ...     layer_name="parcels",
            ...     database_path="parcels.db"
            ... )
            >>>
            >>> # Example 4: Load GeoParquet (very efficient for large datasets)
            >>> m.add_duckdb_layer(
            ...     data="large_dataset.parquet",
            ...     layer_name="large_layer"
            ... )
            >>>
            >>> # Example 5: Load from GeoDataFrame
            >>> import geopandas as gpd
            >>> gdf = gpd.read_file("data.geojson")
            >>> m.add_duckdb_layer(
            ...     data=gdf,
            ...     layer_name="from_gdf"
            ... )
            >>>
            >>> # Example 6: Use existing database (no data loading)
            >>> m.add_duckdb_layer(
            ...     database_path="existing_data.db",
            ...     table_name="my_table",
            ...     geom_column="geometry",
            ...     layer_name="existing_layer"
            ... )
            >>>
            >>> # Example 7: Large parquet file with min_zoom to prevent memory issues
            >>> m.add_duckdb_layer(
            ...     data="huge_dataset.parquet",
            ...     layer_name="huge_layer",
            ...     min_zoom=8,  # Only load tiles at zoom level 8 and above
            ...     layer_type="fill",
            ...     paint={"fill-color": "#ff0000", "fill-opacity": 0.5}
            ... )
        """

        try:
            # Validate inputs
            if data is None and database_path is None:
                raise ValueError(
                    "Either 'data' or 'database_path' must be provided. "
                    "Provide 'data' to load new data, or 'database_path' to use an existing database."
                )

            # Generate layer name if not provided
            if layer_name is None:
                layer_name = f"duckdb_layer_{random_string(3)}"

            # Determine the database path
            db_path = database_path

            # If data is provided, we need to load it into the database
            if data is not None:
                # For tile serving, we need a persistent database (not in-memory)
                # because the Flask server needs to access it from background threads
                if database_path is None:
                    import tempfile
                    import os

                    # Create a temporary database file path (don't create the file yet)
                    temp_fd, db_path = tempfile.mkstemp(
                        suffix=".db", prefix="leafmap_duckdb_"
                    )
                    os.close(temp_fd)  # Close the file descriptor
                    os.unlink(db_path)  # Remove the empty file
                    if not quiet:
                        print(
                            f"Note: Using temporary database file for tile serving: {db_path}"
                        )

                # Initialize database and load data
                if not quiet:
                    print(f"Initializing DuckDB database for layer '{layer_name}'...")
                db_path = init_duckdb_tiles(
                    data=data,
                    database_path=db_path,
                    table_name=table_name,
                    geom_column=geom_column,
                    quiet=quiet,
                    use_view=use_view,
                    src_crs=src_crs,
                )
            else:
                # Using existing database - verify it exists
                import os

                if not os.path.exists(db_path):
                    raise FileNotFoundError(
                        f"Database file not found: {db_path}. "
                        "Provide 'data' to create a new database, or ensure the database file exists."
                    )

                if not quiet:
                    print(f"Using existing database: {db_path} (table: {table_name})")

            # Start the tile server if not already running
            if not quiet:
                print(f"Starting DuckDB tile server on port {port}...")
            actual_port = start_duckdb_tile_server(
                database_path=db_path,
                table_name=table_name,
                geom_column=geom_column,
                properties=properties,
                port=port,
                background=True,
                quiet=quiet,
                min_zoom=min_zoom,
                src_crs=src_crs,
            )

            # Track the database path for cleanup
            if db_path not in self._duckdb_databases:
                self._duckdb_databases.append(db_path)

            # Create tile URL
            # Auto-configure for JupyterHub (like get_local_tile_url does)
            import os as _os
            from .common import _get_jupyterhub_client_params, configure_jupyterhub

            # Auto-detect and configure JupyterHub environment
            if _os.environ.get("JUPYTERHUB_SERVICE_PREFIX") is not None:
                configure_jupyterhub()

            client_host, client_port, client_prefix = _get_jupyterhub_client_params()

            # Build the tile URL based on environment
            if client_prefix:
                # JupyterHub or remote Jupyter with proxy
                # Replace {port} placeholder with actual port
                prefix = client_prefix.replace("{port}", str(actual_port))

                # Check if a base URL was provided
                import os as _os

                base_url = _os.environ.get("LEAFMAP_BASE_URL", "")

                if base_url:
                    # Use full absolute URL with the provided base
                    base_url = base_url.rstrip("/")
                    if not prefix.startswith("/"):
                        prefix = "/" + prefix
                    prefix = prefix.rstrip("/")
                    tile_url = f"{base_url}{prefix}/tiles/{{z}}/{{x}}/{{y}}.pbf"
                else:
                    # Use protocol-relative URL  which uses the same protocol as the page
                    # This is the approach that works like localtileserver
                    # First ensure prefix starts with /
                    if not prefix.startswith("/"):
                        prefix = "/" + prefix
                    prefix = prefix.rstrip("/")
                    # Use protocol-relative URL starting with //
                    # The browser will automatically use http:// or https:// based on the page
                    # But we need to detect the hostname - we'll get it from the request
                    # For now, use a JavaScript approach by passing it through ipywidget
                    tile_url = f"{prefix}/tiles/{{z}}/{{x}}/{{y}}.pbf"

                if not quiet:
                    print(
                        f"Running in remote Jupyter environment. Using proxy URL: {prefix}"
                    )
                    print(f"Full tile URL template: {tile_url}")
                    # Also print an example URL for debugging
                    example_url = (
                        tile_url.replace("{z}", "0")
                        .replace("{x}", "0")
                        .replace("{y}", "0")
                    )
                    print(f"Example tile URL: {example_url}")
                    if not base_url:
                        print(
                            "\n⚠️  WARNING: MapLibre vector tiles require absolute URLs."
                        )
                        print(
                            "If tiles don't load, configure with your JupyterHub URL:"
                        )
                        print("    import leafmap")
                        print(
                            '    leafmap.configure_jupyterhub("https://your-jupyterhub-domain.com")'
                        )
                        print("Then re-run this cell.\n")
                        print(
                            "Note: Raster tiles (add_raster) work without this, but vector tiles need it."
                        )
            elif _in_colab_shell():
                # Google Colab - use localhost with the port - Colab automatically proxies it
                tile_url = f"http://localhost:{actual_port}/tiles/{{z}}/{{x}}/{{y}}.pbf"
                if not quiet:
                    print(
                        f"Running in Google Colab. Tile server accessible at: http://localhost:{actual_port}"
                    )
            else:
                # Local environment - direct connection
                tile_url = f"http://127.0.0.1:{actual_port}/tiles/{{z}}/{{x}}/{{y}}.pbf"

            # Set default paint properties based on layer type if not provided
            if paint is None:
                if layer_type == "fill":
                    paint = {
                        "fill-color": "#3388ff",
                        "fill-opacity": 0.7,
                        "fill-outline-color": "#ffffff",
                    }
                elif layer_type == "line":
                    paint = {"line-color": "#3388ff", "line-width": 2}
                elif layer_type == "circle":
                    paint = {
                        "circle-radius": 5,
                        "circle-color": "#3388ff",
                        "circle-stroke-color": "#ffffff",
                        "circle-stroke-width": 1,
                    }
                elif layer_type == "symbol":
                    paint = {
                        "text-color": "#000000",
                        "text-halo-color": "#ffffff",
                        "text-halo-width": 1,
                    }

            # Use the existing add_vector_tile method to add the layer
            self.add_vector_tile(
                url=tile_url,
                layer_id=layer_name,
                layer_type=layer_type,
                source_layer="layer",  # DuckDB ST_AsMVT uses 'layer' as default
                name=layer_name,
                paint=paint,
                layout=layout,
                filter=filter,
                minzoom=minzoom,
                maxzoom=maxzoom,
                visible=visible,
                opacity=opacity,
                add_popup=tooltip,
                **kwargs,
            )

            # Fit bounds if requested and data is available
            if fit_bounds and db_path:
                try:
                    import duckdb

                    # Use read_only=True only for file-based databases
                    con = duckdb.connect(db_path, read_only=True)
                    con.execute("LOAD spatial;")

                    # Get bounds from the data
                    # Determine source CRS for transformation
                    if src_crs and src_crs.upper() not in ["EPSG:4326", "4326"]:
                        # User specified a source CRS that's not WGS84, transform from it to WGS84
                        bounds_query = f"""
                            SELECT
                                ST_XMin(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), '{src_crs}', 'EPSG:4326', true)) as min_lon,
                                ST_YMin(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), '{src_crs}', 'EPSG:4326', true)) as min_lat,
                                ST_XMax(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), '{src_crs}', 'EPSG:4326', true)) as max_lon,
                                ST_YMax(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), '{src_crs}', 'EPSG:4326', true)) as max_lat
                            FROM {table_name}
                        """
                    else:
                        # No src_crs specified or it's already WGS84, auto-detect based on coordinates
                        sample_coords = con.execute(
                            f"SELECT ST_X(ST_Centroid({geom_column})), ST_Y(ST_Centroid({geom_column})) FROM {table_name} LIMIT 1"
                        ).fetchone()

                        if sample_coords and sample_coords[0] is not None:
                            x, y = sample_coords[0], sample_coords[1]
                            # Web Mercator coordinates are typically > 180 or < -180
                            # WGS84 coordinates are in range [-180, 180] for X and [-90, 90] for Y
                            is_web_mercator = abs(x) > 180 or abs(y) > 90

                            if is_web_mercator:
                                # Data is in Web Mercator (EPSG:3857), transform to WGS84 (EPSG:4326)
                                bounds_query = f"""
                                    SELECT
                                        ST_XMin(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), 'EPSG:3857', 'EPSG:4326', true)) as min_lon,
                                        ST_YMin(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), 'EPSG:3857', 'EPSG:4326', true)) as min_lat,
                                        ST_XMax(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), 'EPSG:3857', 'EPSG:4326', true)) as max_lon,
                                        ST_YMax(ST_Transform(ST_GeomFromWKB(ST_AsWKB(ST_Extent({geom_column}))), 'EPSG:3857', 'EPSG:4326', true)) as max_lat
                                    FROM {table_name}
                                """
                            else:
                                # Data is in WGS84 (EPSG:4326), use directly
                                bounds_query = f"""
                                    SELECT
                                        MIN(ST_XMin({geom_column})) as min_lon,
                                        MIN(ST_YMin({geom_column})) as min_lat,
                                        MAX(ST_XMax({geom_column})) as max_lon,
                                        MAX(ST_YMax({geom_column})) as max_lat
                                    FROM {table_name}
                                """
                        else:
                            con.close()
                            if not quiet:
                                print(
                                    "Could not determine bounds: no valid geometry found"
                                )
                            bounds_query = None

                    if bounds_query:
                        result = con.execute(bounds_query).fetchone()
                        con.close()

                        if result and all(x is not None for x in result):
                            min_lon, min_lat, max_lon, max_lat = result
                            # MapLibre expects [[west, south], [east, north]] = [[minLon, minLat], [maxLon, maxLat]]
                            self.fit_bounds([[min_lon, min_lat], [max_lon, max_lat]])
                except Exception as e:
                    if not quiet:
                        print(f"Could not fit bounds: {e}")

            if not quiet:
                print(f"Layer '{layer_name}' added successfully!")

        except ImportError as e:
            if not quiet:
                print(f"Missing required package: {e}")
                print(
                    "Please install required packages: pip install duckdb flask flask-cors"
                )
        except (ValueError, FileNotFoundError):
            # Re-raise validation errors so users can handle them
            raise
        except Exception as e:
            if not quiet:
                print(f"Error adding DuckDB layer: {e}")
                import traceback

                traceback.print_exc()

    def close_db_connections(self, database_path: str = None, quiet: bool = False):
        """
        Close DuckDB connections for databases used by this map.

        This method closes all connections in the connection pool for the specified
        database or all databases used by this map instance, allowing other programs
        to access the database files. This is useful when you're done using the
        database and want to release the file lock.

        Args:
            database_path (str, optional): Path to the DuckDB database file.
                If None, closes connections for all databases used by this map.
                Defaults to None.
            quiet (bool, optional): If True, suppress status messages. Defaults to False.

        Returns:
            None

        Example:
            >>> import leafmap.maplibregl as leafmap
            >>> m = leafmap.Map()
            >>> m.add_duckdb_layer("tiles.db")
            >>> # Later, close the connections
            >>> m.close_db_connections()
            >>> # Or close connections for a specific database
            >>> m.close_db_connections("tiles.db")
        """
        from .common import close_duckdb_connections

        if database_path is None:
            # Close connections for all databases used by this map
            for db_path in self._duckdb_databases:
                close_duckdb_connections(db_path, quiet=quiet)
        else:
            # Close connections for specific database
            if database_path in self._duckdb_databases:
                close_duckdb_connections(database_path, quiet=quiet)
            else:
                if not quiet:
                    print(f"Database not tracked by this map: {database_path}")

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
    ):
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

        import numpy as np
        from PIL import Image

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
    ):
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

    def add_image_to_sidebar(
        self,
        image: Union[str, Dict] = None,
        width: int = None,
        height: int = None,
        add_header: bool = True,
        widget_icon: str = "mdi-image",
        close_icon: str = "mdi-close",
        label: str = "Image",
        background_color: str = "#f5f5f5",
        header_height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """Add an image to the map.

        Args:
            id (str): The layer ID of the image.
            image (Union[str, Dict, np.ndarray]): The URL or local file path to
                the image, or a dictionary containing image data, or a numpy
                array representing the image.
            width (int, optional): The width of the image. Defaults to None.
            height (int, optional): The height of the image. Defaults to None.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            header_height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the parent class.

        Returns:
            None
        """

        style = ""
        if isinstance(width, int):
            style += f"width: {width}px; "
        elif isinstance(width, str) and width.endswith("px"):
            style += f"width: {width}; "
        if isinstance(height, int):
            style += f"height: {height}px; "
        elif isinstance(height, str) and height.endswith("px"):
            style += f"height: {height}; "

        if style == "":
            html = f'<img src="{image}">'
        else:
            html = f'<img src="{image}" style="{style}">'
        self.add_html_to_sidebar(
            html,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            header_height=header_height,
            expanded=expanded,
            **kwargs,
        )

    def add_symbol(
        self,
        source: Union[str, Dict],
        image: str,
        icon_size: int = 1,
        symbol_placement: str = "line",
        minzoom: Optional[float] = None,
        maxzoom: Optional[float] = None,
        filter: Optional[Any] = None,
        name: Optional[str] = "Symbols",
        overwrite: bool = False,
        **kwargs: Any,
    ):
        """
        Adds a symbol to the map.

        Args:
            source (Union[str, Dict]): The source of the symbol.
            image (str): The URL or local file path to the image. Default to the arrow image.
                at https://assets.gishub.org/images/right-arrow.png.
                Find more icons from https://www.veryicon.com.
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

        image_id = f"image_{common.random_string(3)}"
        self.add_image(image_id, image)

        name = common.get_unique_name(name, self.layer_names, overwrite)

        if isinstance(source, str):
            if source in self.layer_names:
                source_name = self.layer_dict[source]["layer"].source
            elif source in self.source_names:
                source_name = source
            else:
                geojson = gpd.read_file(source).__geo_interface__
                geojson_source = {"type": "geojson", "data": geojson}
                source_name = common.get_unique_name(
                    "source", self.source_names, overwrite=False
                )
                self.add_source(source_name, geojson_source)
        elif isinstance(source, dict):
            source_name = common.get_unique_name("source", self.source_names)
            geojson_source = {"type": "geojson", "data": source}
            self.add_source(source_name, geojson_source)
        else:
            raise ValueError("The source must be a string or a dictionary.")

        layer = {
            "id": name,
            "type": "symbol",
            "source": source_name,
            "layout": {
                "icon-image": image_id,
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
        name: Optional[str] = "Arrow",
        overwrite: bool = False,
        **kwargs: Any,
    ):
        """
        Adds an arrow symbol to the map.

        Args:
            source (str): The source layer to which the arrow symbol will be added.
            image (Optional[str], optional): The URL of the arrow image.
                Defaults to "https://assets.gishub.org/images/right-arrow.png".
                Find more icons from https://www.veryicon.com.
            icon_size (int, optional): The size of the icon. Defaults to 0.1.
            minzoom (Optional[float], optional): The minimum zoom level at which
                the arrow symbol will be visible. Defaults to 19.
            **kwargs: Additional keyword arguments to pass to the add_symbol method.

        Returns:
            None
        """
        if image is None:
            image = "https://assets.gishub.org/images/right-arrow.png"

        self.add_symbol(
            source,
            image,
            icon_size,
            minzoom=minzoom,
            name=name,
            overwrite=overwrite,
            **kwargs,
        )

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
            import base64

            import streamlit.components.v1 as components  # pylint: disable=E0401

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
        super().add_call("rotateTo", bearing, options)

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
    ):
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
        super().add_call("panTo", lnglat, options)

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
        super().add_call("setPitch", pitch)

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
        super().add_call("jumpTo", options)

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

    def get_style(self) -> Dict:
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
        super().add_call("zoomTo", zoom, options)

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

    @property
    def first_symbol_layer_id(self) -> Optional[str]:
        """
        Get the ID of the first symbol layer in the map's current style.
        """
        layer = self.find_first_symbol_layer()
        if layer is not None:
            return layer["id"]
        else:
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
    ):
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

    def add_text_to_sidebar(
        self,
        text: str,
        add_header: bool = True,
        widget_icon: str = "mdi-format-text",
        close_icon: str = "mdi-close",
        label: str = "Text",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        widget_args: Optional[Dict] = None,
        **kwargs: Any,
    ):
        """
        Adds text to the sidebar.

        Args:
            text (str): The text to add to the sidebar.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """

        if widget_args is None:
            widget_args = {}
        widget = widgets.Label(text, **widget_args)

        self.add_to_sidebar(
            widget,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
            **kwargs,
        )

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

    def add_html_to_sidebar(
        self,
        html: str,
        add_header: bool = True,
        widget_icon: str = "mdi-language-html5",
        close_icon: str = "mdi-close",
        label: str = "HTML",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Add HTML content to the map.

        This method allows for the addition of arbitrary HTML content to the sidebar, which can be used to display
        custom information or controls.

        Args:
            html (str): The HTML content to add.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the parent class.

        Returns:
            None
        """
        # Check if an HTML string contains local images and convert them to base64.
        html = common.check_html_string(html)
        widget = widgets.HTML(html)
        self.add_to_sidebar(
            widget,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
            **kwargs,
        )

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

    def add_legend_to_sidebar(
        self,
        title: str = "Legend",
        legend_dict: Optional[Dict[str, str]] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        builtin_legend: Optional[str] = None,
        shape_type: str = "rectangle",
        add_header: bool = True,
        widget_icon: str = "mdi-view-sequential",
        close_icon: str = "mdi-close",
        label: str = "Legend",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
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
            builtin_legend (Optional[str], optional): The name of a built-in legend to use. Defaults to None.
            shape_type (str, optional): The shape type of the legend items. Can be one of "rectangle", "circle", or "line".
            add_header (bool, optional): If True, adds a header to the legend. Defaults to True.
            widget_icon (str, optional): The icon for the legend widget. Defaults to "mdi-view-sequential".
            close_icon (str, optional): The icon for the close button. Defaults to "mdi-close".
            label (str, optional): The label for the legend widget. Defaults to "Legend".
            background_color (str, optional): The background color of the legend widget. Defaults to "#f5f5f5".
            height (str, optional): The height of the legend widget. Defaults to "40px".
            expanded (bool, optional): If True, the legend widget is expanded by default. Defaults to True.
            **kwargs: Additional keyword arguments for future use.

        Returns:
            None
        """
        from .map_widgets import Legend

        legend = Legend(
            title=title,
            legend_dict=legend_dict,
            keys=labels,
            colors=colors,
            builtin_legend=builtin_legend,
            shape_type=shape_type,
            add_header=False,
        )

        self.add_to_sidebar(
            legend,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
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
        colorbar_args: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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
            colorbar_args (Optional[Dict[str, Any]]): Additional keyword arguments passed to the colorbar.
                Can be colorbar_args={"ticks": list(range(0, 101, 10))}. Defaults to None.
            **kwargs: Additional keyword arguments passed to matplotlib.pyplot.savefig().

        Returns:
            str: Path to the generated colorbar image.
        """

        if transparent:
            bg_color = "transparent"

        if colorbar_args is None:
            colorbar_args = {}

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
            **colorbar_args,
        )

        html = f'<img src="{colorbar}">'

        self.add_html(html, bg_color=bg_color, position=position, **kwargs)

    def add_colorbar_to_sidebar(
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
        add_header: bool = True,
        widget_icon: str = "mdi-format-color-fill",
        close_icon: str = "mdi-close",
        header_label: str = "Colorbar",
        header_color: str = "#f5f5f5",
        header_height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        Add a colorbar to the sidebar.

        This function uses matplotlib to generate a colorbar, saves it as a PNG file, and adds it to the map using
        the Map.add_html_to_sidebar() method. The colorbar can be customized in various ways including its size, color palette,
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
            add_header (bool): If True, adds a header to the colorbar. Defaults to True.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the parent class.

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

        self.add_html_to_sidebar(
            html,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=header_label,
            background_color=header_color,
            height=header_height,
            expanded=expanded,
            **kwargs,
        )

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

    def add_floating_sidebar(
        self,
        position: str = "top-left",
        width: str = "370px",
        max_height: str = "80vh",
        expanded: bool = True,
        sidebar_visible: bool = False,
        sidebar_content: Optional[List[widgets.Widget]] = None,
        **kwargs: Any,
    ) -> "widgets.Widget":
        """
        Adds a floating sidebar panel overlaid on the map with a toggle button.

        This method creates a floating sidebar that appears as an overlay on the map canvas.
        The sidebar includes a toggle button to show/hide it, along with the layer manager
        and any additional content you specify.

        Args:
            position (str): Position on the map. Can be "top-right", "top-left",
                "bottom-right", or "bottom-left". Defaults to "top-left".
            width (str): Width of the sidebar (e.g., "370px", "25%"). Defaults to "370px".
            max_height (str): Maximum height of the sidebar (e.g., "80vh", "500px").
                Defaults to "80vh".
            expanded (bool): Whether the layer manager starts expanded. Defaults to True.
            sidebar_visible (bool): Whether the sidebar content is initially visible.
                Defaults to False. The toggle button is always visible.
            sidebar_content (Optional[List[widgets.Widget]]): Additional widgets to include
                in the sidebar. Defaults to None (only layer manager).
            **kwargs: Additional keyword arguments passed to LayerManagerWidget.

        Returns:
            widgets.Widget: A widget containing the map with the floating sidebar overlay.
                Display this instead of the map object.

        Example:
            >>> m = leafmap.Map()
            >>> m.add_basemap("Esri.WorldImagery")
            >>> widget = m.add_floating_sidebar(position="top-left", width="360px")
            >>> widget  # Display the returned widget
        """
        # Position styles mapping
        position_styles = {
            "top-right": "top: 10px; right: 10px;",
            "top-left": "top: 10px; left: 10px;",
            "bottom-right": "bottom: 50px; right: 10px;",
            "bottom-left": "bottom: 50px; left: 10px;",
        }

        pos_style = position_styles.get(position, position_styles["top-left"])

        # Create layer manager if it doesn't exist
        if self.layer_manager is None:
            self.layer_manager = LayerManagerWidget(self, expanded=expanded, **kwargs)

        # Initialize floating sidebar state
        if not hasattr(self, "floating_sidebar_content_box"):
            self.floating_sidebar_content_box = widgets.VBox(children=[])

        if not hasattr(self, "_floating_sidebar_widgets"):
            self._floating_sidebar_widgets = {}

        # Create sidebar content list
        content_widgets = [self.layer_manager]
        if sidebar_content:
            content_widgets.extend(sidebar_content)

        # Create main sidebar box with layer manager and additional content
        main_sidebar_box = widgets.VBox(children=content_widgets)

        # Create toggle button
        toggle_icon = v.Icon(
            children=["mdi-chevron-left"] if sidebar_visible else ["mdi-chevron-right"],
            small=True,
        )
        toggle_btn = v.Btn(
            icon=True,
            children=[toggle_icon],
            style_="width: 22px; height: 22px; min-width: 22px; padding: 0;",
        )

        # Create settings/wrench button
        settings_icon = v.Icon(children=["mdi-wrench"], small=True)
        settings_btn = v.Btn(
            icon=True,
            children=[settings_icon],
            style_="width: 22px; height: 22px; min-width: 22px; padding: 0;",
        )

        # Create header row with toggle and settings buttons
        header_row = v.Row(
            class_="ma-0 pa-0 d-flex justify-space-between align-center mb-1",
            children=[toggle_btn, settings_btn],
        )

        # State tracking for sidebar visibility
        class SidebarState:
            visible = sidebar_visible
            settings_visible = False

        # Convert width string to number for calculation
        if isinstance(width, str):
            if width.endswith("px"):
                width_num = int(width[:-2])
            elif width.endswith("%"):
                # Assume parent container is 1440px wide if not available
                parent_width = 1440
                percent = int(width[:-1])
                width_num = int(parent_width * percent / 100)
            else:
                width_num = 360
        else:
            width_num = 360

        # Create width adjustment slider
        width_slider = widgets.IntSlider(
            value=width_num,
            min=200,
            max=800,
            step=10,
            description="Width:",
            continuous_update=True,
            layout=widgets.Layout(width="100%"),
        )

        # Width change handler
        def on_width_change(change):
            new_width = change["new"]
            if SidebarState.visible:
                overlay.style_ = f"""
                    position: absolute;
                    {pos_style}
                    width: {new_width}px;
                    max-height: {max_height};
                    overflow-y: auto;
                    overflow-x: hidden;
                    z-index: 1000;
                    background-color: white;
                    border-radius: 4px;
                """

        width_slider.observe(on_width_change, names="value")

        # Create settings widget wrapped in CustomWidget for proper header
        settings_widget = CustomWidget(
            width_slider,
            widget_icon="mdi-cog",
            label="Sidebar Settings",
            host_map=self,
            expanded=True,
        )

        # Settings button handler - toggle settings widget visibility
        def on_settings_click(widget, event, data):
            SidebarState.settings_visible = not SidebarState.settings_visible
            if SidebarState.settings_visible:
                # Add settings widget to floating sidebar content box
                if settings_widget not in self.floating_sidebar_content_box.children:
                    self.floating_sidebar_content_box.children = (
                        settings_widget,
                    ) + self.floating_sidebar_content_box.children
            else:
                # Remove settings widget from floating sidebar content box
                self.floating_sidebar_content_box.children = tuple(
                    child
                    for child in self.floating_sidebar_content_box.children
                    if child != settings_widget
                )

        settings_btn.on_event("click", on_settings_click)

        # Combine main sidebar with dynamic content box for layer settings and other widgets
        sidebar_box = widgets.VBox(
            children=[main_sidebar_box, self.floating_sidebar_content_box]
        )

        # Toggle function
        def toggle_sidebar(widget, event, data):
            SidebarState.visible = not SidebarState.visible
            toggle_icon.children = [
                "mdi-chevron-left" if SidebarState.visible else "mdi-chevron-right"
            ]

            if SidebarState.visible:
                # Show sidebar content
                overlay.children = [header_row, sidebar_box]
                overlay.class_ = "pa-2 ma-0"
                current_width = width_slider.value
                overlay.style_ = f"""
                    position: absolute;
                    {pos_style}
                    width: {current_width}px;
                    max-height: {max_height};
                    overflow-y: auto;
                    overflow-x: hidden;
                    z-index: 1000;
                    background-color: white;
                    border-radius: 4px;
                """
            else:
                # Hide sidebar content, only show toggle button
                overlay.children = [toggle_btn]
                overlay.class_ = "ma-0"
                overlay.style_ = f"""
                    position: absolute;
                    {pos_style}
                    width: auto;
                    height: auto;
                    max-height: none;
                    overflow: visible;
                    z-index: 1000;
                    background-color: white;
                    border-radius: 4px;
                    padding: 4px;
                """

        toggle_btn.on_event("click", toggle_sidebar)

        # Create floating overlay container
        initial_children = (
            [header_row, sidebar_box] if sidebar_visible else [toggle_btn]
        )
        if sidebar_visible:
            initial_style = f"""
                position: absolute;
                {pos_style}
                width: {width_num}px;
                max-height: {max_height};
                overflow-y: auto;
                overflow-x: hidden;
                z-index: 1000;
                background-color: white;
                border-radius: 4px;
            """
        else:
            initial_style = f"""
                position: absolute;
                {pos_style}
                width: auto;
                height: auto;
                max-height: none;
                overflow: visible;
                z-index: 1000;
                background-color: white;
                border-radius: 4px;
                padding: 4px;
            """

        overlay = v.Card(
            class_="ma-0" if not sidebar_visible else "pa-2 ma-0",
            elevation=4,
            flat=False,
            style_=initial_style,
            children=initial_children,
        )

        # Create wrapper with the map and overlay
        wrapper = v.Html(
            tag="div",
            style_="position: relative; width: 100%; height: 100%;",
            children=[self, overlay],
        )

        return wrapper

    def add_3d_buildings(
        self,
        name: str = "buildings",
        min_zoom: int = 15,
        values: List[int] = [0, 200, 400],
        colors: List[str] = ["lightgray", "royalblue", "lightblue"],
        **kwargs: Any,
    ):
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
    ):
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
    ):
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
                            "circle-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "fill-opacity": opacity,
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
                            "circle-opacity": opacity,
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
                            "line-opacity": opacity,
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
                            "circle-opacity": opacity,
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
    ):
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

    def add_video_to_sidebar(
        self,
        src: str,
        width: int = 600,
        add_header: bool = True,
        widget_icon: str = "mdi-video",
        close_icon: str = "mdi-close",
        label: str = "Video",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Adds a video to the sidebar.

        Args:
            src (str): The URL of the video to be added.
            width (int): Width of the video in pixels. Defaults to 600.
            add_header (bool): If True, adds a header to the video. Defaults to True.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """
        video_html = f"""
        <video width="{width}" controls>
        <source src="{src}" type="video/mp4">
        Your browser does not support the video tag.
        </video>
        """
        self.add_html_to_sidebar(
            video_html,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
            **kwargs,
        )

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
    ):
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
        outline_color: Optional[str] = "rgba(255, 255, 255, 255)",
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        opacity: float = 1.0,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ):
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
            outline_color (str, optional): The color of the outline of the layer. Defaults to "rgba(255, 255, 255, 255)".
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
        setattr(self, "legend_dict", legend_dict)

        if legend_title is None:
            legend_title = column

        geom_type = gdf.geometry.iloc[0].geom_type

        if geom_type == "Point" or geom_type == "MultiPoint":
            layer_type = "circle"
            if paint is None:
                paint = {
                    "circle-color": ["get", "color"],
                    "circle-radius": 5,
                    "circle-stroke-color": outline_color,
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
                        "fill-outline-color": outline_color,
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
        opacity: float = 1.0,
        visible: bool = True,
        add_to_sidebar: bool = False,
        style: str = "photo",
        radius: float = 0.00005,
        height: int = 420,
        frame_border: int = 0,
        default_message: str = "No Mapillary image found",
        widget_icon: str = "mdi-image",
        widget_label: str = "Mapillary StreetView",
        **kwargs: Any,
    ):
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
            opacity (float): Opacity of the Mapillary layers. Defaults to 1.0.
            visible (bool): Whether the Mapillary layers are visible. Defaults to True.

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

        self.add_layer(
            sequence_lyr,
            name=sequence_lyr_name,
            before_id=before_id,
            opacity=opacity,
            visible=visible,
        )
        self.add_layer(
            image_lyr,
            name=image_lyr_name,
            before_id=before_id,
            opacity=opacity,
            visible=visible,
        )
        if add_popup:
            self.add_popup(sequence_lyr_name)
            self.add_popup(image_lyr_name)

        if add_to_sidebar:
            self._mapillary_widget = widgets.HTML()

            self.add_to_sidebar(
                self._mapillary_widget,
                label=widget_label,
                widget_icon=widget_icon,
                expanded=False,
                **kwargs,
            )

            def log_lng_lat(lng_lat):
                width = int(self.sidebar_args["min_width"] - 60)
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
                    self._mapillary_widget.value = content
                else:
                    self._mapillary_widget.value = default_message

            self._mapillary_function = log_lng_lat

            def _on_panel_toggle(change):
                if 0 in change["new"]:
                    self._mapillary_widget.value = (
                        "Click on the map to view Mapillary StreetView"
                    )
                    self.observe(log_lng_lat, names="clicked")
                else:
                    self._mapillary_widget.value = ""
                    self.unobserve_mapillary()

            # Get the widget from the appropriate sidebar type
            if hasattr(self, "floating_sidebar_content_box"):
                # Floating sidebar
                sidebar_widget = self._floating_sidebar_widgets.get(widget_label)
            elif self.container is not None:
                # Container sidebar
                sidebar_widget = self.container.sidebar_widgets.get(widget_label)
            else:
                sidebar_widget = None

            if sidebar_widget is not None:
                sidebar_widget.observe(_on_panel_toggle, names="v_model")

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

    def add_labels(
        self,
        source: Union[str, Dict[str, Any]],
        column: str,
        name: Optional[str] = None,
        text_size: int = 14,
        text_anchor: str = "center",
        text_color: str = "black",
        min_zoom: Optional[float] = None,
        max_zoom: Optional[float] = None,
        layout: Optional[Dict[str, Any]] = None,
        paint: Optional[Dict[str, Any]] = None,
        before_id: Optional[str] = None,
        opacity: float = 1.0,
        visible: bool = True,
        **kwargs: Any,
    ):
        """
        Adds a label layer to the map.

        This method adds a label layer to the map using the specified source and column for text values.

        Args:
            source (Union[str, Dict[str, Any]]): The data source for the labels. It can be a GeoJSON file path
                or a dictionary containing GeoJSON data.
            column (str): The column name in the source data to use for the label text.
            name (Optional[str]): The name of the label layer. If None, a random name is generated. Defaults to None.
            text_size (int): The size of the label text. Defaults to 14.
            text_anchor (str): The anchor position of the text. Can be "center", "left", "right", etc. Defaults to "center".
            text_color (str): The color of the label text. Defaults to "black".
            min_zoom (Optional[float]): The minimum zoom level at which the labels are visible. Defaults to None.
            max_zoom (Optional[float]): The maximum zoom level at which the labels are visible. Defaults to None.
            layout (Optional[Dict[str, Any]]): Additional layout properties for the label layer. Defaults to None.
                For more information, refer to https://maplibre.org/maplibre-style-spec/layers/#symbol.
            paint (Optional[Dict[str, Any]]): Additional paint properties for the label layer. Defaults to None.
            before_id (Optional[str]): The ID of an existing layer before which the new layer should be inserted. Defaults to None.
            opacity (float): The opacity of the label layer. Defaults to 1.0.
            visible (bool): Whether the label layer is visible by default. Defaults to True.
            **kwargs (Any): Additional keyword arguments to customize the label layer.

        Returns:
            None
        """

        if name is None:
            name = "Labels"
        name = common.get_unique_name(name, self.layer_names)

        if isinstance(source, str):
            gdf = common.read_vector(source)
            geojson = gdf.__geo_interface__
        elif isinstance(source, dict):
            geojson = source
        elif isinstance(source, gpd.GeoDataFrame):
            geojson = source.__geo_interface__
        else:
            raise ValueError(
                "Invalid source type. Use a GeoDataFrame, a file path to a GeoJSON file, or a dictionary."
            )

        source = {
            "type": "geojson",
            "data": geojson,
        }
        source_name = common.get_unique_name("source", self.source_names)
        self.add_source(source_name, source)

        if layout is None:
            layout = {
                "text-field": ["get", column],
                "text-size": text_size,
                "text-anchor": text_anchor,
            }

        if paint is None:
            paint = {
                "text-color": text_color,
            }

        layer = {
            "id": name,
            "type": "symbol",
            "source": source_name,
            "layout": layout,
            "paint": paint,
            "min_zoom": min_zoom,
            "max_zoom": max_zoom,
            **kwargs,
        }

        self.add_layer(
            layer, before_id=before_id, name=name, opacity=opacity, visible=visible
        )

    @property
    def user_roi(self) -> Optional[dict]:
        """Gets the first user-drawn ROI feature.

        Returns:
            Optional[dict]: The first user-drawn ROI feature or None if no features are drawn.
        """
        if len(self.draw_features_created) > 0:
            return self.draw_features_created[0]
        else:
            return None

    @property
    def user_rois(self) -> list:
        """Gets all user-drawn ROI features.

        Returns:
            list: A list of all user-drawn ROI features.
        """
        return self.draw_feature_collection_all

    def user_roi_bounds(self, decimals: int = 4) -> Optional[list]:
        """Gets the bounds of the user drawn ROI as a tuple of (minx, miny, maxx, maxy).

        Args:
            decimals (int, optional): The number of decimals to round the coordinates to. Defaults to 4.

        Returns:
            Optional[list]: The bounds of the user drawn ROI as a tuple of (minx, miny, maxx, maxy), or None if no ROI is drawn.
        """
        if self.user_roi is not None:
            return common.geometry_bounds(self.user_roi, decimals=decimals)
        else:
            return None

    @property
    def bounds(self) -> tuple:
        """Gets the bounds of the map view state.

        Returns:
            tuple: A tuple of two tuples, each containing (lat, lng) coordinates for the southwest and northeast corners of the map view.
        """
        sw = self.view_state["bounds"]["_sw"]
        ne = self.view_state["bounds"]["_ne"]
        coords = ((sw["lat"], sw["lng"]), (ne["lat"], ne["lng"]))
        return coords

    def get_layer_names(self) -> list:
        """Gets layer names as a list.

        Returns:
            list: A list of layer names.
        """
        layer_names = list(self.layer_dict.keys())
        return layer_names

    @property
    def layer_names(self) -> list:
        """Gets layer names as a list.

        Returns:
            list: A list of layer names.
        """
        return self.get_layer_names()

    @property
    def source_names(self) -> list:
        """Gets source as a list.

        Returns:
            list: A list of sources.
        """
        sources = list(
            set(
                [
                    layer["layer"].source
                    for layer in self.layer_dict.values()
                    if hasattr(layer["layer"], "source")
                    and (layer["layer"].source is not None)
                ]
            )
        )
        sources.sort()
        return sources

    def add_annotation_widget(
        self,
        properties: Optional[Dict[str, List[Any]]] = None,
        geojson: Optional[Union[str, dict]] = None,
        time_format: str = "%Y%m%dT%H%M%S",
        out_dir: Optional[str] = None,
        filename_prefix: str = "",
        file_ext: str = "geojson",
        add_mapillary: bool = False,
        style: str = "photo",
        radius: float = 0.00005,
        width: int = 300,
        height: int = 420,
        frame_border: int = 0,
        download: bool = True,
        name: str = None,
        paint: Dict[str, Any] = None,
        options: Optional[Dict[str, Any]] = None,
        controls: Optional[Dict[str, Any]] = None,
        position: str = "top-right",
        callback: Callable = None,
        add_header: bool = True,
        widget_icon: str = "mdi-drawing",
        close_icon: str = "mdi-close",
        label: str = "Annotation",
        background_color: str = "#f5f5f5",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Adds an annotation widget to the map.

        This method creates a vector data widget for annotations and adds it to the map's sidebar.

        Args:
            properties (Optional[Dict[str, List[Any]]], optional): Properties of the annotation. Defaults to None.
            time_format (str, optional): Format for the timestamp. Defaults to "%Y%m%dT%H%M%S".
            out_dir (Optional[str], optional): Output directory for the annotation data. Defaults to None.
            filename_prefix (str, optional): Prefix for the filename of the annotation data. Defaults to "".
            file_ext (str, optional): File extension for the annotation data. Defaults to "geojson".
            add_mapillary (bool, optional): Whether to add Mapillary data. Defaults to False.
            style (str, optional): Style of the annotation. Defaults to "photo".
            radius (float, optional): Radius of the annotation. Defaults to 0.00005.
            width (int, optional): Width of the annotation widget. Defaults to 300.
            height (int, optional): Height of the annotation widget. Defaults to 420.
            frame_border (int, optional): Border width of the annotation widget frame. Defaults to 0.
            download (bool, optional): Whether to allow downloading the annotation data. Defaults to True.
            name (str, optional): Name of the annotation widget. Defaults to None.
            paint (Dict[str, Any], optional): Paint properties for the annotation. Defaults to None.
            add_header (bool, optional): Whether to add a header to the annotation widget. Defaults to True.
            widget_icon (str, optional): Icon for the annotation widget. Defaults to "mdi-drawing".
            close_icon (str, optional): Icon for closing the annotation widget. Defaults to "mdi-close".
            label (str, optional): Label for the annotation widget. Defaults to "Annotation".
            background_color (str, optional): Background color of the annotation widget. Defaults to "#f5f5f5".
            expanded (bool, optional): Whether the annotation widget is expanded by default. Defaults to True.
            callback (Callable, optional): A callback function to be called when the export button is clicked.
                Defaults to None.
            **kwargs (Any, optional): Additional keyword arguments for the add_to_sidebar method.
        """
        widget = create_vector_data(
            self,
            properties=properties,
            geojson=geojson,
            time_format=time_format,
            out_dir=out_dir,
            filename_prefix=filename_prefix,
            file_ext=file_ext,
            add_mapillary=add_mapillary,
            style=style,
            radius=radius,
            width=width,
            height=height,
            frame_border=frame_border,
            download=download,
            name=name,
            paint=paint,
            options=options,
            controls=controls,
            position=position,
            return_sidebar=True,
            callback=callback,
        )
        self.add_to_sidebar(
            widget,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            expanded=expanded,
            **kwargs,
        )

    def add_date_filter_widget(
        self,
        sources: List[Dict[str, Any]],
        names: List[str] = None,
        styles: Dict[str, Any] = None,
        start_date_col: str = "startDate",
        end_date_col: str = "endDate",
        date_col: str = None,
        date_format: str = "%Y-%m-%d",
        min_date: str = None,
        max_date: str = None,
        file_index: int = 0,
        group_col: str = None,
        freq: str = "D",
        interval: int = 1,
        add_header: bool = True,
        widget_icon: str = "mdi-filter",
        close_icon: str = "mdi-close",
        label: str = "Date Filter",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the DateFilterWidget.

        Args:
            sources (List[Dict[str, Any]]): List of data sources.
            names (List[str], optional): List of names for the data sources. Defaults to None.
            styles (Dict[str, Any], optional): Dictionary of styles for the data sources. Defaults to None.
            start_date_col (str, optional): Name of the column containing the start date. Defaults to "startDate".
            end_date_col (str, optional): Name of the column containing the end date. Defaults to "endDate".
            date_col (str, optional): Name of the column containing the date. Defaults to None.
            date_format (str, optional): Format of the date. Defaults to "%Y-%m-%d".
            min_date (str, optional): Minimum date. Defaults to None.
            max_date (str, optional): Maximum date. Defaults to None.
            file_index (int, optional): Index of the main file. Defaults to 0.
            group_col (str, optional): Name of the column containing the group. Defaults to None.
            freq (str, optional): Frequency of the date range. Defaults to "D".
            unit (str, optional): Unit of the date. Defaults to "ms".
            interval (int, optional): Interval of the date range. Defaults to 1.
            add_header (bool, optional): Whether to add a header to the widget. Defaults to True.
            widget_icon (str, optional): Icon of the widget. Defaults to "mdi-filter".
            close_icon (str, optional): Icon of the close button. Defaults to "mdi-close".
            label (str, optional): Label of the widget. Defaults to "Date Filter".
            background_color (str, optional): Background color of the widget. Defaults to "#f5f5f5".
            height (str, optional): Height of the widget. Defaults to "40px".
            expanded (bool, optional): Whether the widget is expanded by default. Defaults to True.
            **kwargs (Any, optional): Additional keyword arguments for the add_to_sidebar method.
        """

        widget = DateFilterWidget(
            sources=sources,
            names=names,
            styles=styles,
            start_date_col=start_date_col,
            end_date_col=end_date_col,
            date_col=date_col,
            date_format=date_format,
            min_date=min_date,
            max_date=max_date,
            file_index=file_index,
            group_col=group_col,
            freq=freq,
            interval=interval,
            map_widget=self,
        )

        self.add_to_sidebar(
            widget,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
            **kwargs,
        )

    def add_select_data_widget(
        self,
        default_path: str = ".",
        widget_width: str = "360px",
        callback: Optional[Callable[[str], None]] = None,
        reset_callback: Optional[Callable[[], None]] = None,
        add_header: bool = True,
        widget_icon: str = "mdi-folder",
        close_icon: str = "mdi-close",
        label: str = "Data Selection",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Adds a select data widget to the map.

        This method creates a widget for selecting and uploading data to be added to a map.
        It includes a folder chooser, a file uploader, and buttons to apply or reset the selection.

        Args:
            default_path (str, optional): The default path for the folder chooser. Defaults to ".".
            widget_width (str, optional): The width of the widget. Defaults to "360px".
            callback (Optional[Callable[[str], None]], optional): A callback function to be
                called when data is applied. Defaults to None.
            reset_callback (Optional[Callable[[], None]], optional): A callback function to
                be called when the selection is reset. Defaults to None.
            add_header (bool, optional): Whether to add a header to the widget. Defaults to True.
            widget_icon (str, optional): The icon for the widget. Defaults to "mdi-folder".
            close_icon (str, optional): The icon for the close button. Defaults to "mdi-close".
            label (str, optional): The label for the widget. Defaults to "Data Selection".
            background_color (str, optional): The background color of the widget. Defaults to "#f5f5f5".
            height (str, optional): The height of the widget. Defaults to "40px".
            expanded (bool, optional): Whether the widget is expanded by default. Defaults to True.
            **kwargs (Any, optional): Additional keyword arguments for the add_to_sidebar method.
        """
        widget = SelectDataWidget(
            default_path=default_path,
            widget_width=widget_width,
            callback=callback,
            reset_callback=reset_callback,
            map_widget=self,
        )

        self.add_to_sidebar(
            widget,
            add_header=add_header,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
            **kwargs,
        )

    def to_solara(self, map_only: bool = False, **kwargs):
        """
        Converts the widget to a Solara widget.

        Args:
            map_only (bool, optional): Whether to only return the map widget. Defaults to False.
        """

        try:
            import reacton.ipyvuetify as rv
        except ImportError:
            print(
                "solara is not installed. Please install it with `pip install solara`."
            )
            return None

        if map_only:
            return rv.Row(children=[self], **kwargs)
        else:
            if self.container is None:
                self.create_container()
            return rv.Row(children=[self.container], **kwargs)

    def add_stac_gui(
        self,
        label="STAC Search",
        widget_icon="mdi-search-web",
        sidebar_width="515px",
        **kwargs: Any,
    ):
        """
        Adds a STAC GUI to the map.
        """
        from .toolbar import stac_gui

        widget = stac_gui(m=self, backend="maplibre")
        self.add_to_sidebar(widget, label=label, widget_icon=widget_icon, **kwargs)
        self.set_sidebar_width(min_width=sidebar_width)
        self.sidebar_args["min_width"] = sidebar_width
        self.sidebar_args["max_width"] = sidebar_width

    def add_alphaearth_gui(
        self,
        start_year: int = 2017,
        end_year: int = 2024,
        label: str = "AlphaEarth",
        widget_icon: str = "mdi-earth",
        **kwargs: Any,
    ):
        """
        Adds a AlphaEarth GUI to the map.
        Earth Engine Dataset: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL

        Args:
            start_year (int, optional): The start year. Defaults to 2017.
            end_year (int, optional): The end year. Defaults to 2024.
            label (str, optional): The label of the widget. Defaults to "AlphaEarth".
            widget_icon (str, optional): The icon of the widget. Defaults to "mdi-earth".
            **kwargs (Any, optional): Additional keyword arguments for the add_to_sidebar method.
        """
        import ee

        band_names = (
            ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
            .first()
            .bandNames()
            .getInfo()
        )

        style = {"description_width": "initial"}
        year_slider = widgets.IntSlider(
            value=2020,
            min=start_year,
            max=end_year,
            step=1,
            description="Year:",
            continuous_update=True,
            style=style,
        )

        red_band = widgets.Dropdown(
            options=band_names, value="A01", description="Red:", style=style
        )

        green_band = widgets.Dropdown(
            options=band_names, value="A02", description="Green:", style=style
        )

        blue_band = widgets.Dropdown(
            options=band_names, value="A03", description="Blue:", style=style
        )

        min_max_slider = widgets.FloatRangeSlider(
            value=[-0.3, 0.3],
            min=-1.0,
            max=1.0,
            step=0.01,
            description="Min-Max:",
            style=style,
        )

        layer_name_widget = widgets.Text(
            value=f"Embeddings {year_slider.value}",
            description="Layer Name:",
            style=style,
        )

        add_label_widget = widgets.Checkbox(
            value=True, description="Add labels on top", style=style
        )

        terrain_exaggeration_slider = widgets.FloatSlider(
            value=2,
            min=1,
            max=10,
            step=0.1,
            description="Terrain exaggeration:",
            style=style,
        )

        apply_button = widgets.Button(
            description="Apply",
            button_style="primary",
            tooltip="Apply changes",
        )

        reset_button = widgets.Button(
            description="Reset",
            button_style="primary",
            tooltip="Reset to default",
        )

        close_button = widgets.Button(
            description="Close",
            button_style="primary",
            tooltip="Close the app",
        )

        def update_year(change):
            if change["new"]:
                year = change.new
                layer_name_widget.value = f"Embeddings {year}"

        year_slider.observe(update_year, names="value")

        def terrain_exaggeration_changed(change):
            if change["new"]:
                self.set_terrain(exaggeration=terrain_exaggeration_slider.value)

        terrain_exaggeration_slider.observe(terrain_exaggeration_changed, names="value")

        def apply_button_clicked(change):
            layer_name = layer_name_widget.value
            if layer_name in self.get_layer_names():
                self.remove_layer(layer_name)

            if add_label_widget.value:
                before_id = self.first_symbol_layer_id
            else:
                before_id = None

            dataset = (
                ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
                .filterDate(f"{year_slider.value}-01-01", f"{year_slider.value}-12-31")
                .mosaic()
            )
            vis_params = {
                "min": min_max_slider.value[0],
                "max": min_max_slider.value[1],
                "bands": [red_band.value, green_band.value, blue_band.value],
            }
            self.add_ee_layer(
                dataset, vis_params, name=layer_name, opacity=1.0, before_id=before_id
            )
            self.set_terrain(exaggeration=terrain_exaggeration_slider.value)

        apply_button.on_click(apply_button_clicked)

        def reset_button_clicked(change):
            year_slider.value = 2020
            terrain_exaggeration_slider.value = 2
            min_max_slider.value = [-0.3, 0.3]
            red_band.value = "A01"
            green_band.value = "A02"
            blue_band.value = "A03"
            add_label_widget.value = True
            layer_name_widget.value = f"Embeddings {year_slider.value}"
            if layer_name_widget.value in self.get_layer_names():
                self.remove_layer(layer_name_widget.value)

        reset_button.on_click(reset_button_clicked)

        def close_button_clicked(change):
            self.remove_from_sidebar(name=label)

        close_button.on_click(close_button_clicked)

        widget = widgets.VBox(
            [
                year_slider,
                widgets.HBox([red_band, green_band, blue_band]),
                min_max_slider,
                terrain_exaggeration_slider,
                add_label_widget,
                layer_name_widget,
                widgets.HBox([apply_button, reset_button, close_button]),
            ]
        )

        self.add_to_sidebar(widget, label=label, widget_icon=widget_icon, **kwargs)

    def add_similarity_search(
        self,
        before_id: str = None,
        default_year: int = 2024,
        default_color: str = "#0000ff",
        default_threshold: float = 0.8,
        widget_icon: str = "mdi-map-search",
        widget_label: str = "Similarity Search",
        **kwargs: Any,
    ):
        """
        Adds a similarity search widget to the map.

        Args:
            before_id: The ID of the layer to add the widget to.
            default_year: The default year to use for the widget. Defaults to 2024.
            default_color: The default color to use for the widget. Defaults to "#0000ff".
            default_threshold: The default threshold to use for the widget. Defaults to 0.8.
            widget_icon: The icon for the widget. Defaults to "mdi-map-search".
            widget_label: The label for the widget. Defaults to "Similarity Search".
            **kwargs: Additional keyword arguments to be passed to the add_to_sidebar method.
        """
        from .map_widgets import SimilaritySearch

        widget = SimilaritySearch(
            self,
            before_id=before_id,
            default_year=default_year,
            default_color=default_color,
            default_threshold=default_threshold,
        )
        self.add_to_sidebar(
            widget, widget_icon=widget_icon, label=widget_label, **kwargs
        )

    def add_time_slider(
        self,
        images: Optional[Union[Dict, List, str]] = None,
        labels: Optional[List] = None,
        time_interval: Optional[int] = 1,
        label_width: Optional[str] = "150px",
        slider_width: Optional[str] = "150px",
        button_width: Optional[str] = "45px",
        layer_name: Optional[str] = "Image",
        before_id: Optional[str] = None,
        default_index: Optional[int] = 0,
        zoom_to_layer: Optional[bool] = True,
        widget_icon: str = "mdi-image",
        close_icon: str = "mdi-close",
        label: str = "Time Slider",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        **kwargs: Any,
    ):
        """
        Adds a time slider to the map.

        Args:
            images (dict, optional): The dictionary containing a set of images.
            labels (list, optional): The list of labels to be used for the time series. Defaults to None.
            time_interval (int, optional): Time interval in seconds. Defaults to 1.
            layer_name (str, optional): The name of the layer. Defaults to "Image".
            before_id (str, optional): The ID of an existing layer before which the new layer should be inserted. Defaults to None.
            default_index (int, optional): The index of the default layer. Defaults to 0.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to False.
            label_width (str, optional): Width of the label. Defaults to "150px".
            slider_width (str, optional): Width of the slider. Defaults to "150px".
            button_width (str, optional): Width of the buttons. Defaults to "45px".
            widget_icon (str, optional): The icon for the widget. Defaults to "mdi-image".
            close_icon (str, optional): The icon for the close button. Defaults to "mdi-close".
            label (str, optional): The label for the widget. Defaults to "Time Slider".
            background_color (str, optional): The background color of the widget. Defaults to "#f5f5f5".
            height (str, optional): The height of the widget. Defaults to "40px".
            expanded (bool, optional): Whether the widget is expanded by default. Defaults to True.
            **kwargs: Additional keyword arguments to be passed to the add_raster or add_cog_layer function.
        """
        if before_id is None:
            before_id = self.first_symbol_layer_id
        widget = TimeSliderWidget(
            self,
            images,
            labels,
            time_interval,
            layer_name,
            before_id,
            default_index,
            zoom_to_layer,
            label_width,
            slider_width,
            button_width,
            **kwargs,
        )

        self.add_to_sidebar(
            widget,
            widget_icon=widget_icon,
            close_icon=close_icon,
            label=label,
            background_color=background_color,
            height=height,
            expanded=expanded,
        )

    def observe_mapillary(
        self,
        html_widget: widgets.HTML,
        style: str = "photo",
        radius: float = 0.00005,
        height: int = 420,
        frame_border: int = 0,
        default_message: str = "No Mapillary image found",
    ):
        """
        Observes the mapillary data and updates the html widget.

        Args:
            html_widget (widgets.HTML): The html widget to display the mapillary data.
            style (str, optional): The style of the Mapillary image widget. Can be "classic", "photo",
                or "split". Defaults to "photo".
            radius (float, optional): The radius (in degrees) used to search for the nearest Mapillary
                image. Defaults to 0.00005 degrees.
            height (int, optional): The height of the Mapillary image widget. Defaults to 420.
            frame_border (int, optional): The width of the frame border for the Mapillary image widget.
                Defaults to 0.
            default_message (str, optional): The message to display when no Mapillary image is found.
        """

        def log_lng_lat(lng_lat):
            width = int(self.sidebar_args["min_width"] - 60)
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
                html_widget.value = content
            else:
                html_widget.value = default_message

        self._mapillary_function = log_lng_lat

        self.observe(log_lng_lat, names="clicked")

    def unobserve_mapillary(self):
        """
        Unobserves the mapillary street view.
        """
        self.unobserve(self._mapillary_function, names="clicked")

    def add_vector_editor(
        self,
        filename: str = None,
        properties: Optional[Dict[str, List[Any]]] = None,
        time_format: str = "%Y%m%dT%H%M%S",
        out_dir: Optional[str] = None,
        filename_prefix: str = "",
        file_ext: str = "geojson",
        add_mapillary: bool = False,
        style: str = "photo",
        radius: float = 0.00005,
        width: int = 300,
        height: int = 420,
        frame_border: int = 0,
        controls: Optional[List[str]] = None,
        position: str = "top-right",
        fit_bounds_options: Optional[Dict] = None,
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
            filename (str or gpd.GeoDataFrame): The path to a GeoJSON file or a GeoDataFrame
                containing the vector data to be edited. Defaults to None.
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
            controls (Optional[List[str]], optional): The drawing controls to be added to the map.
                Defaults to ["point", "polygon", "line_string", "trash"].
            position (str, optional): The position of the drawing controls on the map. Defaults to "top-right".
            **kwargs (Any): Additional keyword arguments that may be passed to the function.

        Returns:
            widgets.VBox: A vertical box widget containing the map, sidebar, and control buttons.
        """
        from datetime import datetime

        main_widget = widgets.VBox()
        output = widgets.Output()

        if controls is None:
            controls = ["point", "polygon", "line_string", "trash"]

        if isinstance(filename, str):
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext in [".parquet", ".pq", ".geoparquet"]:
                gdf = gpd.read_parquet(filename)
            else:
                gdf = gpd.read_file(filename)
        elif isinstance(filename, dict):
            gdf = gpd.GeoDataFrame.from_features(filename, crs="EPSG:4326")
        elif isinstance(filename, gpd.GeoDataFrame):
            gdf = filename
        else:
            raise ValueError("filename must be a string, dict, or GeoDataFrame.")

        gdf = gdf.to_crs(epsg=4326)

        if out_dir is None:
            out_dir = os.getcwd()

        if properties is None:
            properties = {}
            dtypes = gdf.dtypes.to_dict()
            for key, value in dtypes.items():
                if key != "geometry":
                    if value == "object":
                        if gdf[key].nunique() < 10:
                            properties[key] = gdf[key].unique().tolist()
                        else:
                            properties[key] = ""
                    elif value == "int32":
                        properties[key] = 0
                    elif value == "float64":
                        properties[key] = 0.0
                    elif value == "bool":
                        properties[key] = gdf[key].unique().tolist()
                    else:
                        properties[key] = ""

        columns = properties.keys()
        gdf = gdf[list(columns) + ["geometry"]]
        geojson = gdf.__geo_interface__
        bounds = get_bounds(geojson)

        self.add_draw_control(
            controls=controls,
            position=position,
            geojson=geojson,
        )
        self.fit_bounds(bounds, fit_bounds_options)

        draw_features = {}
        for row in gdf.iterrows():
            draw_feature = {}
            for prop in properties.keys():
                if prop in gdf.columns:
                    draw_feature[prop] = row[1][prop]
                else:
                    draw_feature[prop] = properties[prop][0]
            draw_features[str(row[0])] = draw_feature
        setattr(self, "draw_features", draw_features)
        self.draw_feature_collection_all = geojson

        # Expand dropdown options to include values from the GeoJSON
        for key, values in properties.items():
            if isinstance(values, list) or isinstance(values, tuple):
                # Collect unique values from the loaded features
                existing_values = set()
                for feature_data in draw_features.values():
                    if key in feature_data:
                        val = feature_data[key]
                        if val is not None:
                            existing_values.add(val)

                # Merge existing values with provided options
                options_set = set(values)
                merged_options = options_set.union(existing_values)
                # Convert back to list, maintaining order (original options first)
                merged_list = [val for val in values if val in merged_options]
                for val in sorted(existing_values):
                    if val not in options_set:
                        merged_list.append(val)
                properties[key] = merged_list

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
                if len(self.draw_features_selected) > 0:
                    output.clear_output()
                    output.outputs = ()
                    feature_id = self.draw_features_selected[0]["id"]
                    if feature_id not in self.draw_features:
                        self.draw_features[feature_id] = {}
                        for key, values in properties.items():
                            if isinstance(values, list) or isinstance(values, tuple):
                                self.draw_features[feature_id][key] = values[0]
                            else:
                                self.draw_features[feature_id][key] = values
                    else:
                        for prop_widget in prop_widgets.children:
                            key = prop_widget.description
                            value = self.draw_features[feature_id][key]
                            # For dropdown widgets, only set value if it's in options
                            if hasattr(prop_widget, "options"):
                                if value in prop_widget.options:
                                    prop_widget.value = value
                                elif len(prop_widget.options) > 0:
                                    # Fall back to first option if value not found
                                    prop_widget.value = prop_widget.options[0]
                            else:
                                prop_widget.value = value

            else:
                for prop_widget in prop_widgets.children:
                    key = prop_widget.description
                    if isinstance(properties[key], list) or isinstance(
                        properties[key], tuple
                    ):
                        prop_widget.value = properties[key][0]
                    else:
                        prop_widget.value = properties[key]

        self.observe(draw_change, names="draw_features_selected")

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
            self.observe(log_lng_lat, names="clicked")

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
            if len(self.draw_features_selected) > 0:
                feature_id = self.draw_features_selected[0]["id"]
                for prop_widget in prop_widgets.children:
                    key = prop_widget.description
                    self.draw_features[feature_id][key] = prop_widget.value
                with output:
                    output.clear_output()
                    output.outputs = ()
                    output.append_stdout("Feature saved.")
            else:
                with output:
                    output.clear_output()
                    output.outputs = ()
                    output.append_stdout("Please select a feature to save.")

        save.on_click(on_save_click)

        def on_export_click(b):
            current_time = datetime.now().strftime(time_format)
            filename = os.path.join(
                out_dir, f"{filename_prefix}{current_time}.{file_ext}"
            )

            for index, feature in enumerate(
                self.draw_feature_collection_all["features"]
            ):
                feature_id = feature["id"]
                if feature_id in self.draw_features:
                    self.draw_feature_collection_all["features"][index][
                        "properties"
                    ] = self.draw_features[feature_id]

            gdf = gpd.GeoDataFrame.from_features(
                self.draw_feature_collection_all, crs="EPSG:4326"
            )
            gdf.to_file(filename)
            with output:
                output.clear_output()
                output.outputs = ()
                output.append_stdout(f"Exported: {os.path.basename(filename)}")

        export.on_click(on_export_click)

        def on_reset_click(b):
            output.clear_output()
            output.outputs = ()
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
        self.add_to_sidebar(
            sidebar_widget,
            label="Vector Editor",
            widget_icon="mdi-shape-polygon-plus",
            **kwargs,
        )

    def add_wayback_layer(
        self,
        date: str = None,
        name: str = None,
        attribution: str = "Esri",
        before_id: Optional[str] = None,
        quiet: bool = False,
        **kwargs,
    ):
        """Adds a Wayback layer to the map.

        Args:
            date (str, optional): The date of the layer. Defaults to None.
            name (str, optional): The name of the layer. Defaults to None.
            attribution (str, optional): The attribution of the layer. Defaults to "Esri".
            **kwargs: Additional keyword arguments to pass to the add_tile_layer method.
        """
        layers = common.get_wayback_layers()
        if date not in layers.keys():
            new_date = common.find_closest_date(date, layers.keys())
            if not quiet:
                print(f"{date} is not available. Using the closest date: {new_date}")
            date = new_date

        url = common.get_wayback_tile_url(date, layers)
        if name is None:
            name = date

        if before_id is None:
            before_id = self.first_symbol_layer_id
        self.add_tile_layer(
            url, name=name, attribution=attribution, before_id=before_id, **kwargs
        )

    def add_wayback_time_slider(self, default_index: Optional[int] = 0, **kwargs):
        """Add a time slider for Wayback layers."""
        tile_dict = common.get_wayback_tile_dict()
        images = list(tile_dict.values())
        labels = list(tile_dict.keys())

        self.add_time_slider(
            images, labels=labels, default_index=default_index, **kwargs
        )


class Container(v.Container):
    """
    A container widget for displaying a map with an optional sidebar.

    This class creates a layout with a map on the left and a sidebar on the right.
    The sidebar can be toggled on or off and can display additional content.

    Attributes:
        sidebar_visible (bool): Whether the sidebar is visible.
        min_width (int): Minimum width of the sidebar in pixels.
        max_width (int): Maximum width of the sidebar in pixels.
        map_container (v.Col): The container for the map.
        sidebar_content_box (widgets.VBox): The container for the sidebar content.
        toggle_icon (v.Icon): The icon for the toggle button.
        toggle_btn (v.Btn): The button to toggle the sidebar.
        sidebar (v.Col): The container for the sidebar.
        row (v.Row): The main layout row containing the map and sidebar.
    """

    def __init__(
        self,
        host_map: Optional[Any] = None,
        sidebar_visible: bool = True,
        min_width: int = 250,
        max_width: int = 300,
        sidebar_content: Optional[Union[widgets.VBox, List[widgets.Widget]]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initializes the Container widget.

        Args:
            host_map (Optional[Any]): The map object to display in the container. Defaults to None.
            sidebar_visible (bool): Whether the sidebar is visible. Defaults to True.
            min_width (int): Minimum width of the sidebar in pixels. Defaults to 250.
            max_width (int): Maximum width of the sidebar in pixels. Defaults to 300.
            sidebar_content (Optional[Union[widgets.VBox, List[widgets.Widget]]]):
                The content to display in the sidebar. Defaults to None.
            *args (Any): Additional positional arguments for the parent class.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """
        self.sidebar_visible = sidebar_visible
        self.min_width = min_width
        self.max_width = max_width
        self.host_map = host_map
        self.sidebar_widgets = {}

        # Map column (left)
        self.map_container = v.Col(
            class_="pa-1",
            style_="flex-grow: 1; flex-shrink: 1; flex-basis: 0;",
        )

        # --- NEW: a vertical stack inside the map column ---
        # Everything under the map (including the map itself) goes here.
        self.map_stack = v.Col(
            class_="ma-0 pa-0 d-flex flex-column",
            style_="overflow-x: auto; max-width: 100%;",
        )
        self.map_container.children = [self.map_stack]

        # Ensure the map exists and is visible
        m = host_map or self.create_map()

        # Put the map as the first child of the stack
        self.map_stack.children = [m]

        # Sidebar content container
        self.sidebar_content_box = widgets.VBox()
        if sidebar_content:
            self.set_sidebar_content(sidebar_content)

        # Toggle button
        self.toggle_icon = v.Icon(
            children=["mdi-chevron-right"] if sidebar_visible else ["mdi-chevron-left"]
        )
        self.toggle_btn = v.Btn(
            icon=True,
            children=[self.toggle_icon],
            style_="width: 48px; height: 48px; min-width: 48px;",
        )
        self.toggle_btn.on_event("click", self.toggle_sidebar)

        # Settings icon
        self.settings_icon = v.Icon(children=["mdi-wrench"])
        self.settings_btn = v.Btn(
            icon=True,
            children=[self.settings_icon],
            style_="width: 36px; height: 36px;",
        )
        self.settings_btn.on_event("click", self.toggle_width_slider)

        # Sidebar controls row
        self.sidebar_controls = v.Row(
            class_="ma-0 pa-0", children=[self.toggle_btn, self.settings_btn]
        )

        # Sidebar width slider
        self.width_slider = widgets.IntSlider(
            value=self.max_width,
            min=200,
            max=1000,
            step=10,
            description="Width:",
            continuous_update=True,
        )
        self.width_slider.observe(self.on_width_change, names="value")

        self.settings_widget = CustomWidget(
            self.width_slider,
            widget_icon="mdi-cog",
            label="Sidebar Settings",
            host_map=self.host_map,
        )

        # Sidebar (right column)
        self.sidebar = v.Col(class_="pa-1", style_="overflow-y: hidden;")
        self.update_sidebar_content()

        # Main layout row
        self.row = v.Row(
            class_="d-flex flex-nowrap", children=[self.map_container, self.sidebar]
        )

        super().__init__(fluid=True, children=[self.row], *args, **kwargs)

    # --- NEW: method to add widgets beneath the map dynamically ---
    def add_to_map_container(
        self, *items: Union[widgets.Widget, Iterable[widgets.Widget], None]
    ) -> None:
        """Append one or more widgets beneath the map (in insertion order)."""
        new_items: List[widgets.Widget] = []
        for it in items:
            if it is None:
                continue
            if isinstance(it, (list, tuple)):
                new_items.extend([w for w in it if w is not None])
            else:
                new_items.append(it)
        if not new_items:
            return

        # Apply width constraints to prevent widgets from exceeding container width
        for item in new_items:
            if hasattr(item, "layout"):
                # Ensure widgets don't exceed the available width
                if (
                    not hasattr(item.layout, "max_width")
                    or item.layout.max_width is None
                ):
                    item.layout.max_width = "100%"
                if not hasattr(item.layout, "width") or item.layout.width is None:
                    item.layout.width = "auto"
                # Enable overflow handling for wide content
                item.layout.overflow = "auto"

        # IMPORTANT: reassign, don't mutate in place
        self.map_stack.children = [*self.map_stack.children, *new_items]

        # Ensure sidebar remains visible after adding items to map container
        # Force a refresh of the sidebar content to prevent it from disappearing
        if hasattr(self, "sidebar") and hasattr(self, "sidebar_visible"):
            # Trigger a refresh of the sidebar content
            self.update_sidebar_content()
            # Ensure the main row layout is properly maintained
            if hasattr(self, "row") and hasattr(self, "map_container"):
                # Reassign children to force layout refresh
                self.row.children = [self.map_container, self.sidebar]

    def create_map(self) -> Any:
        """
        Creates a default map object.

        Returns:
            Any: A default map object.
        """
        return Map(center=[20, 0], zoom=2)

    def toggle_sidebar(self, *args: Any, **kwargs: Any) -> None:
        """
        Toggles the visibility of the sidebar.

        Args:
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.
        """
        self.sidebar_visible = not self.sidebar_visible
        self.toggle_icon.children = [
            "mdi-chevron-right" if self.sidebar_visible else "mdi-chevron-left"
        ]
        self.update_sidebar_content()

    def update_sidebar_content(self) -> None:
        """
        Updates the content of the sidebar based on its visibility.
        If the sidebar is visible, it displays the toggle button and the sidebar content.
        If the sidebar is hidden, it only displays the toggle button.
        """
        if self.sidebar_visible:
            # Header row: toggle on the left, settings on the right
            header_row = v.Row(
                class_="ma-0 pa-0",
                align="center",
                justify="space-between",
                children=[self.toggle_btn, self.settings_btn],
            )

            children = [header_row]

            children.append(self.sidebar_content_box)

            self.sidebar.children = children
            self.sidebar.style_ = (
                f"min-width: {self.min_width}px; max-width: {self.max_width}px;"
            )
        else:
            self.sidebar.children = [self.toggle_btn]
            self.sidebar.style_ = "width: 48px; min-width: 48px; max-width: 48px;"

    def set_sidebar_content(
        self, content: Union[widgets.VBox, List[widgets.Widget]]
    ) -> None:
        """
        Replaces all content in the sidebar (except the toggle button).

        Args:
            content (Union[widgets.VBox, List[widgets.Widget]]): The new content for the sidebar.
        """
        if isinstance(content, (list, tuple)):
            self.sidebar_content_box.children = content
        else:
            self.sidebar_content_box.children = [content]

    def add_to_sidebar(
        self,
        widget: widgets.Widget,
        add_header: bool = True,
        widget_icon: str = "mdi-tools",
        close_icon: str = "mdi-close",
        label: str = "My Tools",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        host_map: Optional[Any] = None,
        **kwargs: Any,
    ):
        """
        Appends a widget to the sidebar content.

        Args:
            widget (Optional[Union[widgets.Widget, List[widgets.Widget]]]): Initial widget(s) to display in the content box.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            *args (Any): Additional positional arguments for the parent class.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """

        if label in self.sidebar_widgets:
            self.remove_from_sidebar(name=label)

        if add_header:
            widget = CustomWidget(
                widget,
                widget_icon=widget_icon,
                close_icon=close_icon,
                label=label,
                background_color=background_color,
                height=height,
                expanded=expanded,
                host_map=host_map,
                **kwargs,
            )

        self.sidebar_content_box.children += (widget,)
        self.sidebar_widgets[label] = widget

    def remove_from_sidebar(
        self, widget: widgets.Widget = None, name: str = None
    ) -> None:
        """
        Removes a widget from the sidebar content.

        Args:
            widget (widgets.Widget): The widget to remove from the sidebar.
            name (str): The name of the widget to remove from the sidebar.
        """
        key = None
        for key, value in self.sidebar_widgets.items():
            if value == widget or key == name:
                if widget is None:
                    widget = self.sidebar_widgets[key]
                break

        if key is not None and key in self.sidebar_widgets:
            self.sidebar_widgets.pop(key)
        self.sidebar_content_box.children = tuple(
            child for child in self.sidebar_content_box.children if child != widget
        )

    def set_sidebar_width(self, min_width: int = None, max_width: int = None) -> None:
        """
        Dynamically updates the sidebar's minimum and maximum width.

        Args:
            min_width (int, optional): New minimum width in pixels. If None, keep current.
            max_width (int, optional): New maximum width in pixels. If None, keep current.
        """
        if min_width is not None:
            if isinstance(min_width, str):
                min_width = int(min_width.replace("px", ""))
            self.min_width = min_width
        if max_width is not None:
            if isinstance(max_width, str):
                max_width = int(max_width.replace("px", ""))
            self.max_width = max_width
        self.update_sidebar_content()

    def toggle_width_slider(self, *args: Any) -> None:

        if self.settings_widget not in self.sidebar_content_box.children:
            self.add_to_sidebar(self.settings_widget, add_header=False)

    def on_width_change(self, change: dict) -> None:
        new_width = change["new"]
        self.set_sidebar_width(min_width=new_width, max_width=new_width)
        self.host_map.sidebar_args["min_width"] = new_width
        self.host_map.sidebar_args["max_width"] = new_width


def construct_amazon_style(
    map_style: str = "standard",
    region: str = "us-east-1",
    api_key: str = None,
    token: str = "AWS_MAPS_API_KEY",
) -> str:
    """
    Constructs a URL for an Amazon Map style.

    Args:
        map_style (str): The name of the MapTiler style to be accessed. It can be one of the following:
            standard, monochrome, satellite, hybrid.
        region (str): The region of the Amazon Map. It can be one of the following:
            us-east-1, us-west-2, eu-central-1, eu-west-1, ap-northeast-1, ap-northeast-2, ap-southeast-1, etc.
        api_key (str): The API key for the Amazon Map. If None, the function attempts to retrieve the API key using a predefined method.
        token (str): The token for the Amazon Map. If None, the function attempts to retrieve the API key using a predefined method.

    Returns:
        str: The URL for the requested Amazon Map style.
    """

    if map_style.lower() not in ["standard", "monochrome", "satellite", "hybrid"]:
        print(
            "Invalid map style. Please choose from amazon-standard, amazon-monochrome, amazon-satellite, or amazon-hybrid."
        )
        return None

    if api_key is None:
        api_key = common.get_api_key(token)
        if api_key is None:
            print("An API key is required to use the Amazon Map style.")
            return None

    url = f"https://maps.geo.{region}.amazonaws.com/v2/styles/{map_style.title()}/descriptor?key={api_key}"
    return url


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
        # print(
        #     "Failed to retrieve the MapTiler style. Defaulting to OpenFreeMap 'liberty' style."
        # )
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

    from datetime import datetime
    from pathlib import Path

    import bqplot as bq
    from bqplot import Figure, LinearScale, PanZoom

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
            output.outputs = ()
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
        output.outputs = ()
        download_widget.clear_output()
        download_widget.outputs = ()

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
        output.outputs = ()
        download_widget.clear_output()
        download_widget.outputs = ()
        with output:
            output.append_stdout("Exporting annotated GPS trace...")
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
                output.outputs = ()
                output.append_display_data(csv_link)
            with download_widget:
                download_widget.clear_output()
                download_widget.outputs = ()
                download_widget.append_display_data(geojson_link)
        else:
            with output:
                output.clear_output()
                output.outputs = ()
                output.append_stdout(f"Saved CSV: {os.path.basename(output_csv)}")
                output.append_stdout(
                    f"Saved GeoJSON: {os.path.basename(output_geojson)}"
                )

        # Remove the temporary file if it exists
        tmp_file = os.path.splitext(filename)[0] + "_tmp.csv"
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

    export.on_click(on_export_click)

    def on_reset_click(b):
        multi_select.value = []
        features_widget.children = []
        output.clear_output()
        output.outputs = ()
        download_widget.clear_output()
        download_widget.outputs = ()

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
                output.outputs = ()

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
                    output.outputs = ()
                    output.append_stdout(f"Error: {e}")
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
                    output.outputs = ()
                    output.append_stdout(f"Error: {e}")
                    edit_widget = widgets.VBox()

            main_widget.children = [filepath_widget, edit_widget, output]

    filepath_widget.observe(on_change, names="value")

    main_widget.children = [filepath_widget, output]
    filepath_widget.value = filepaths[0]

    return main_widget


def create_vector_data(
    m: Optional[Map] = None,
    properties: Optional[Dict[str, List[Any]]] = None,
    geojson: Optional[Union[str, dict]] = None,
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
    download: bool = True,
    name: str = None,
    paint: Dict[str, Any] = None,
    options: Optional[Dict[str, Any]] = None,
    controls: Optional[Dict[str, Any]] = None,
    position: str = "top-right",
    callback: Callable = None,
    return_sidebar: bool = False,
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
        download (bool, optional): Whether to generate a download link for the exported file.
            Defaults to True.
        name (str, optional): The name of the drawn feature layer to be added to the map.
            Defaults to None.
        paint (Dict[str, Any], optional): A dictionary specifying the paint properties for the
            drawn features. This can include properties like "circle-radius", "circle-color",
            "circle-opacity", "circle-stroke-color", and "circle-stroke-width". Defaults to None.
        callback (Callable, optional): A callback function to be called when the export button is clicked.
            Defaults to None.
        return_sidebar (bool, optional): Whether to return the sidebar widget. Defaults to False.

        **kwargs (Any): Additional keyword arguments that may be passed to the add_geojson method.

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

    if paint is None:
        paint = {
            "circle-radius": 6,
            "circle-color": "#FFFF00",
            "circle-opacity": 1.0,
            "circle-stroke-color": "#000000",
            "circle-stroke-width": 1,
        }

    if geojson is not None and isinstance(geojson, str):
        geojson = gpd.read_file(geojson).__geo_interface__
        setattr(m, "geojson", geojson)

    setattr(m, "draw_feature_collection_initial", geojson)

    def create_default_map():
        m = Map(style="liberty", height=map_height)
        m.add_basemap("Satellite")
        m.add_overture_buildings(visible=True)
        m.add_overture_data(theme="transportation")
        m.add_layer_control()
        m.add_draw_control(
            controls=["point", "polygon", "line_string", "trash"], position="top-right"
        )
        return m

    if m is None:
        m = create_default_map()

    m.add_draw_control(
        options=options, controls=controls, position=position, geojson=geojson
    )

    setattr(m, "draw_features", {})

    sidebar_widget = widgets.VBox()

    prop_widgets = widgets.VBox()

    image_widget = widgets.HTML()

    if isinstance(properties, dict):
        for key, values in properties.items():

            if isinstance(values, list) or isinstance(values, tuple):
                prop_widget = widgets.Dropdown(
                    options=values,
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

    if geojson is not None:
        for feature in geojson["features"]:
            feature_id = feature["id"]
            if feature_id not in m.draw_features:
                m.draw_features[feature_id] = {}
                for prop_widget in prop_widgets.children:
                    key = prop_widget.description
                    m.draw_features[feature_id][key] = feature["properties"][key]

    def draw_change(lng_lat):
        if lng_lat.new:
            if len(m.draw_features_selected) > 0:
                feature_id = m.draw_features_selected[0]["id"]
                if feature_id not in m.draw_features:
                    m.draw_features[feature_id] = {}
                    for prop_widget in prop_widgets.children:
                        key = prop_widget.description
                        m.draw_features[feature_id][key] = prop_widget.value
                else:
                    for prop_widget in prop_widgets.children:
                        key = prop_widget.description
                        prop_widget.value = m.draw_features[feature_id][key]

        for index, feature in enumerate(m.draw_feature_collection_all["features"]):
            feature_id = feature["id"]
            if feature_id in m.draw_features:
                m.draw_feature_collection_all["features"][index]["properties"] = (
                    m.draw_features[feature_id]
                )

        if isinstance(name, str):

            if name not in m.layer_dict.keys():

                m.add_geojson(
                    m.draw_feature_collection_all,
                    layer_type="circle",
                    name=name,
                    paint=paint,
                    fit_bounds=False,
                    **kwargs,
                )

            else:
                m.set_data(name, m.draw_feature_collection_all)

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
            image_widget.value = ""

    if add_mapillary:
        m.observe(log_lng_lat, names="clicked")

    filename_widget = widgets.Text(
        description="Filename:", placeholder="filename.geojson"
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

    def on_save_click(b):

        output.clear_output()
        output.outputs = ()
        if len(m.draw_features_selected) > 0:
            feature_id = m.draw_features_selected[0]["id"]
            for prop_widget in prop_widgets.children:
                key = prop_widget.description
                m.draw_features[feature_id][key] = prop_widget.value
        else:
            with output:
                output.clear_output()
                output.outputs = ()
                output.append_stdout("Please select a feature to save.")

    save.on_click(on_save_click)

    def on_export_click(b):
        output.clear_output()
        output.outputs = ()
        current_time = datetime.now().strftime(time_format)
        if filename_widget.value:
            filename = filename_widget.value
            if not filename.endswith(f".{file_ext}"):
                filename = f"{filename}.{file_ext}"
        else:
            filename = os.path.join(
                out_dir, f"{filename_prefix}{current_time}.{file_ext}"
            )

        for index, feature in enumerate(m.draw_feature_collection_all["features"]):
            feature_id = feature["id"]
            if feature_id in m.draw_features:
                m.draw_feature_collection_all["features"][index]["properties"] = (
                    m.draw_features[feature_id]
                )
        if callback is not None:
            with output:
                gdf = callback(m)
        else:
            gdf = gpd.GeoDataFrame.from_features(
                m.draw_feature_collection_all, crs="EPSG:4326"
            )
        gdf.to_file(filename)
        with output:
            if download:
                download_link = common.create_download_link(filename, title="⬇️")
                output.outputs = ()
                output.append_display_data(download_link)
            else:
                output.outputs = ()
                output.append_stdout(f"Exported: {os.path.basename(filename)}")

    export.on_click(on_export_click)

    def on_reset_click(b):
        output.clear_output()
        output.outputs = ()
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
        filename_widget,
        widgets.HBox([save, export, reset]),
        output,
        image_widget,
    ]

    if return_sidebar:
        return sidebar_widget
    else:

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


def edit_vector_data(
    m: Optional[Map] = None,
    filename: str = None,
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
    controls: Optional[List[str]] = None,
    position: str = "top-right",
    fit_bounds_options: Dict = None,
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
        filename (str or gpd.GeoDataFrame): The path to a GeoJSON file or a GeoDataFrame
            containing the vector data to be edited. Defaults to None.
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
        controls (Optional[List[str]], optional): The drawing controls to be added to the map.
            Defaults to ["point", "polygon", "line_string", "trash"].
        position (str, optional): The position of the drawing controls on the map. Defaults to "top-right".
        **kwargs (Any): Additional keyword arguments that may be passed to the function.

    Returns:
        widgets.VBox: A vertical box widget containing the map, sidebar, and control buttons.
    """
    from datetime import datetime

    main_widget = widgets.VBox()
    output = widgets.Output()

    if controls is None:
        controls = ["point", "polygon", "line_string", "trash"]

    if isinstance(filename, str):
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in [".parquet", ".pq", ".geoparquet"]:
            gdf = gpd.read_parquet(filename)
        else:
            gdf = gpd.read_file(filename)
    elif isinstance(filename, dict):
        gdf = gpd.GeoDataFrame.from_features(filename, crs="EPSG:4326")
    elif isinstance(filename, gpd.GeoDataFrame):
        gdf = filename
    else:
        raise ValueError("filename must be a string or a GeoDataFrame.")

    gdf = gdf.to_crs(epsg=4326)

    if out_dir is None:
        out_dir = os.getcwd()

    def create_default_map():
        m = Map(style="liberty", height=map_height)
        m.add_basemap("Satellite")
        m.add_basemap("OpenStreetMap.Mapnik", visible=True)
        m.add_overture_buildings(visible=True)
        m.add_overture_data(theme="transportation")
        return m

    if m is None:
        m = create_default_map()

    if properties is None:
        properties = {}
        dtypes = gdf.dtypes.to_dict()
        for key, value in dtypes.items():
            if key != "geometry":
                if value == "object":
                    if gdf[key].nunique() < 10:
                        properties[key] = gdf[key].unique().tolist()
                    else:
                        properties[key] = ""
                elif value == "int32":
                    properties[key] = 0
                elif value == "float64":
                    properties[key] = 0.0
                elif value == "bool":
                    properties[key] = gdf[key].unique().tolist()
                else:
                    properties[key] = ""

    columns = properties.keys()
    gdf = gdf[list(columns) + ["geometry"]]
    geojson = gdf.__geo_interface__
    bounds = get_bounds(geojson)

    m.add_draw_control(
        controls=controls,
        position=position,
        geojson=geojson,
    )
    m.fit_bounds(bounds, fit_bounds_options)

    draw_features = {}
    for row in gdf.iterrows():
        draw_feature = {}
        for prop in properties.keys():
            if prop in gdf.columns:
                draw_feature[prop] = row[1][prop]
            else:
                draw_feature[prop] = properties[prop][0]
        draw_features[str(row[0])] = draw_feature
    setattr(m, "draw_features", draw_features)
    m.draw_feature_collection_all = geojson

    # Expand dropdown options to include values from the GeoJSON
    for key, values in properties.items():
        if isinstance(values, list) or isinstance(values, tuple):
            # Collect unique values from the loaded features
            existing_values = set()
            for feature_data in draw_features.values():
                if key in feature_data:
                    val = feature_data[key]
                    if val is not None:
                        existing_values.add(val)

            # Merge existing values with provided options
            options_set = set(values)
            merged_options = options_set.union(existing_values)
            # Convert back to list, maintaining order (original options first)
            merged_list = [val for val in values if val in merged_options]
            for val in sorted(existing_values):
                if val not in options_set:
                    merged_list.append(val)
            properties[key] = merged_list

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
                output.clear_output()
                output.outputs = ()
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
                        value = m.draw_features[feature_id][key]
                        # For dropdown widgets, only set value if it's in options
                        if hasattr(prop_widget, "options"):
                            if value in prop_widget.options:
                                prop_widget.value = value
                            elif len(prop_widget.options) > 0:
                                # Fall back to first option if value not found
                                prop_widget.value = prop_widget.options[0]
                        else:
                            prop_widget.value = value

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
            with output:
                output.clear_output()
                output.outputs = ()
                output.append_stdout("Faeature saved.")
        else:
            with output:
                output.clear_output()
                output.outputs = ()
                output.append_stdout("Please select a feature to save.")

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
            output.clear_output()
            output.outputs = ()
            output.append_stdout(f"Exported: {filename}")

    export.on_click(on_export_click)

    def on_reset_click(b):
        output.clear_output()
        output.outputs = ()
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
    """
    A widget that combines a map and a secondary object (e.g., a sidebar) into a single layout.

    This class creates a two-column layout using ipyvuetify, where the left column typically contains
    a map, and the right column contains a secondary object such as a widget or control panel.

    Attributes:
        left_obj (object): The object to be displayed in the left column (e.g., a map).
        right_obj (object): The object to be displayed in the right column (e.g., a widget or control panel).

    Args:
        left_obj (object): The object to be displayed in the left column.
        right_obj (object): The object to be displayed in the right column.
        column_widths (tuple, optional): A tuple specifying the width of the left and right columns.
            Defaults to (5, 1).
        **kwargs: Additional keyword arguments passed to the parent `v.Row` class.
    """

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


class LayerManagerWidget(v.ExpansionPanels):
    """
    A widget for managing map layers.

    This widget provides controls for toggling the visibility, adjusting the opacity,
    and removing layers from a map. It also includes a master toggle to turn all layers
    on or off.

    Attributes:
        m (Map): The map object to manage layers for.
        layer_items (Dict[str, Dict[str, widgets.Widget]]): A dictionary mapping layer names
            to their corresponding control widgets (checkbox and slider).
        _building (bool): A flag indicating whether the widget is currently being built.
        master_toggle (widgets.Checkbox): A checkbox to toggle all layers on or off.
        layers_box (widgets.VBox): A container for individual layer controls.
    """

    def __init__(
        self,
        m: Any,
        expanded: bool = True,
        height: str = "40px",
        layer_icon: str = "mdi-layers",
        close_icon: str = "mdi-close",
        label="Layers",
        background_color: str = "#f5f5f5",
        groups: dict = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initializes the LayerManagerWidget.

        Args:
            m (Any): The map object to manage layers for.
            expanded (bool): Whether the expansion panel should be expanded by default. Defaults to True.
            height (str): The height of the header. Defaults to "40px".
            layer_icon (str): The icon for the layer manager. Defaults to "mdi-layers".
            close_icon (str): The icon for the close button. Defaults to "mdi-close".
            label (str): The label for the layer manager. Defaults to "Layers".
            background_color (str): The background color of the header. Defaults to "#f5f5f5".
            groups (dict): A dictionary of layer groups, such as {"Group 1": ["layer1", "layer2"],
                "Group 2": ["layer3", "layer4"]}. A group layer toggle will be created for each group.
                Defaults to None.
            *args (Any): Additional positional arguments for the parent class.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """
        self.m = m
        self.layer_items = {}
        self.groups = groups
        self._building = False

        # Master toggle
        style = {"description_width": "initial"}
        self.master_toggle = widgets.Checkbox(
            value=True, description="All layers on/off", style=style
        )
        self.master_toggle.observe(self.toggle_all_layers, names="value")

        self.group_toggles = widgets.VBox()
        if isinstance(groups, dict):
            for group_name, group_layers in groups.items():
                group_toggle = widgets.Checkbox(
                    value=True,
                    description=f"{group_name} group layers on/off",
                    style=style,
                )
                group_toggle.observe(self.toggle_group_layers, names="value")
                self.group_toggles.children += (group_toggle,)

        # Build individual layer rows
        self.layers_box = widgets.VBox()
        self.build_layer_controls()

        # Close icon button
        close_btn = v.Btn(
            icon=True,
            small=True,
            class_="ma-0",
            style_="min-width: 24px; width: 24px;",
            children=[v.Icon(children=[close_icon])],
        )
        close_btn.on_event("click", self._handle_close)

        header = v.ExpansionPanelHeader(
            style_=f"height: {height}; min-height: {height}; background-color: {background_color};",
            children=[
                v.Row(
                    align="center",
                    class_="d-flex flex-grow-1 align-center",
                    children=[
                        v.Icon(children=[layer_icon], class_="ml-1"),
                        v.Spacer(),  # push title to center
                        v.Html(tag="span", children=[label], class_="text-subtitle-2"),
                        v.Spacer(),  # push close to right
                        close_btn,
                        v.Spacer(),
                    ],
                )
            ],
        )

        panel = v.ExpansionPanel(
            children=[
                header,
                v.ExpansionPanelContent(
                    children=[
                        widgets.VBox(
                            [self.master_toggle, self.group_toggles, self.layers_box]
                        )
                    ]
                ),
            ]
        )

        if expanded:
            super().__init__(
                children=[panel], v_model=[0], multiple=True, *args, **kwargs
            )
        else:
            super().__init__(children=[panel], multiple=True, *args, **kwargs)

    def _handle_close(self, widget=None, event=None, data=None):
        """Calls the on_close callback if provided."""

        self.m.remove_from_sidebar(self)
        # self.close()

    def build_layer_controls(self) -> None:
        """
        Builds the controls for individual layers.

        This method creates checkboxes for toggling visibility, sliders for adjusting opacity,
        and buttons for removing layers.
        """
        self._building = True
        self.layer_items.clear()
        rows = []

        style = {"description_width": "initial"}
        padding = "0px 5px 0px 5px"

        for name, info in list(self.m.layer_dict.items()):
            # if name == "background":
            #     continue

            visible = info.get("visible", True)
            opacity = info.get("opacity", 1.0)

            if isinstance(opacity, list) and "match" in opacity and len(opacity) >= 5:
                opacity = opacity[3]

            checkbox = widgets.Checkbox(value=visible, description=name, style=style)
            checkbox.layout.flex = "1 1 auto"
            checkbox.layout.max_width = "200px"
            checkbox.layout.min_width = "120px"

            slider = widgets.FloatSlider(
                value=opacity,
                min=0,
                max=1,
                step=0.01,
                readout=False,
                tooltip="Change layer opacity",
                layout=widgets.Layout(
                    flex="1 1 auto", min_width="120px", padding=padding
                ),
            )

            settings = widgets.Button(
                icon="gear",
                tooltip="Change layer style",
                layout=widgets.Layout(width="38px", height="25px", padding=padding),
            )

            remove = widgets.Button(
                icon="times",
                tooltip="Remove layer",
                layout=widgets.Layout(width="38px", height="25px", padding=padding),
            )

            def on_visibility_change(change, layer_name=name):
                self.set_layer_visibility(layer_name, change["new"])

            def on_opacity_change(change, layer_name=name):
                self.set_layer_opacity(layer_name, change["new"])

            def on_remove_clicked(btn, layer_name=name, row_ref=None):
                if layer_name == "background":
                    for layer in self.m.get_style_layers():
                        self.m.add_call("removeLayer", layer["id"])
                else:
                    self.m.remove_layer(layer_name)
                if row_ref in self.layers_box.children:
                    self.layers_box.children = tuple(
                        c for c in self.layers_box.children if c != row_ref
                    )
                self.layer_items.pop(layer_name, None)
                # Check if style widget exists in either floating sidebar or regular sidebar
                style_label = f"Style {layer_name}"
                if (
                    hasattr(self.m, "_floating_sidebar_widgets")
                    and style_label in self.m._floating_sidebar_widgets
                ):
                    self.m.remove_from_sidebar(name=style_label)
                elif (
                    hasattr(self.m, "sidebar_widgets")
                    and style_label in self.m.sidebar_widgets
                ):
                    self.m.remove_from_sidebar(name=style_label)

            def on_settings_clicked(btn, layer_name=name):
                # if isinstance(self.m.layer_dict[layer_name]["layer"], dict):
                #     return
                style_widget = LayerStyleWidget(self.m.layer_dict[layer_name], self.m)
                self.m.add_to_sidebar(
                    style_widget,
                    widget_icon="mdi-palette",
                    label=f"Style {layer_name}",
                )

            checkbox.observe(on_visibility_change, names="value")
            slider.observe(on_opacity_change, names="value")

            row = widgets.HBox(
                [checkbox, slider, settings, remove],
                layout=widgets.Layout(width="100%", display="flex"),
            )

            remove.on_click(
                lambda btn, r=row, n=name: on_remove_clicked(
                    btn, layer_name=n, row_ref=r
                )
            )

            settings.on_click(
                lambda btn, n=name: on_settings_clicked(btn, layer_name=n)
            )

            rows.append(row)
            self.layer_items[name] = {"checkbox": checkbox, "slider": slider}

        self.layers_box.children = rows
        self._building = False

    def toggle_all_layers(self, change: Dict[str, Any]) -> None:
        """
        Toggles the visibility of all layers.

        Args:
            change (Dict[str, Any]): The change event from the master toggle checkbox.
        """
        if self._building:
            return
        for name, controls in self.layer_items.items():
            controls["checkbox"].value = change["new"]

        for widget in self.group_toggles.children:
            widget.value = change["new"]

    def toggle_group_layers(self, change: Dict[str, Any]) -> None:
        """
        Toggles the visibility of a group of layers.
        """
        if self._building:
            return
        group_name = change["owner"].description.split(" ")[0]
        group_layers = self.groups[group_name]
        for layer_name in group_layers:
            self.set_layer_visibility(layer_name, change["new"])
        self.refresh()

    def set_layer_visibility(self, name: str, visible: bool) -> None:
        """
        Sets the visibility of a specific layer.

        Args:
            name (str): The name of the layer.
            visible (bool): Whether the layer should be visible.
        """
        self.m.set_visibility(name, visible)

    def set_layer_opacity(self, name: str, opacity: float) -> None:
        """
        Sets the opacity of a specific layer.

        Args:
            name (str): The name of the layer.
            opacity (float): The opacity value (0 to 1).
        """
        self.m.set_opacity(name, opacity)

    def refresh(self) -> None:
        """
        Rebuilds the UI to reflect the current layers in the map.
        """
        """Rebuild the UI to reflect current layers in the map."""
        self.build_layer_controls()


class CustomWidget(v.ExpansionPanels):
    """
    A custom expansion panel widget with dynamic widget management.

    This widget allows for the creation of an expandable panel with a customizable header
    and dynamic content. Widgets can be added, removed, or replaced in the content box.

    Attributes:
        content_box (widgets.VBox): A container for holding the widgets displayed in the panel.
        panel (v.ExpansionPanel): The main expansion panel containing the header and content.
    """

    def __init__(
        self,
        widget: Optional[Union[widgets.Widget, List[widgets.Widget]]] = None,
        widget_icon: str = "mdi-tools",
        close_icon: str = "mdi-close",
        label: str = "My Tools",
        background_color: str = "#f5f5f5",
        height: str = "40px",
        expanded: bool = True,
        host_map: Optional[Any] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initializes the CustomWidget.

        Args:
            widget (Optional[Union[widgets.Widget, List[widgets.Widget]]]): Initial widget(s) to display in the content box.
            widget_icon (str): Icon for the header. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            close_icon (str): Icon for the close button. See https://pictogrammers.github.io/@mdi/font/2.0.46/ for available icons.
            background_color (str): Background color of the header. Defaults to "#f5f5f5".
            label (str): Text label for the header. Defaults to "My Tools".
            height (str): Height of the header. Defaults to "40px".
            expanded (bool): Whether the panel is expanded by default. Defaults to True.
            *args (Any): Additional positional arguments for the parent class.
            **kwargs (Any): Additional keyword arguments for the parent class.
        """
        # Wrap content in a mutable VBox
        self.content_box = widgets.VBox()
        self.host_map = host_map
        if widget:
            if isinstance(widget, (list, tuple)):
                self.content_box.children = widget
            else:
                self.content_box.children = [widget]

        # Close icon button
        close_btn = v.Btn(
            icon=True,
            small=True,
            class_="ma-0",
            style_="min-width: 24px; width: 24px;",
            children=[v.Icon(children=[close_icon])],
        )
        close_btn.on_event("click", self._handle_close)

        header = v.ExpansionPanelHeader(
            style_=f"height: {height}; min-height: {height}; background-color: {background_color};",
            children=[
                v.Row(
                    align="center",
                    class_="d-flex flex-grow-1 align-center",
                    children=[
                        v.Icon(children=[widget_icon], class_="ml-1"),
                        v.Spacer(),  # push title to center
                        v.Html(tag="span", children=[label], class_="text-subtitle-2"),
                        v.Spacer(),  # push close to right
                        close_btn,
                        v.Spacer(),
                    ],
                )
            ],
        )

        self.panel = v.ExpansionPanel(
            children=[
                header,
                v.ExpansionPanelContent(children=[self.content_box]),
            ]
        )

        super().__init__(
            children=[self.panel],
            v_model=[0] if expanded else [],
            multiple=True,
            *args,
            **kwargs,
        )

    def _handle_close(self, widget=None, event=None, data=None):
        """Calls the on_close callback if provided."""

        if self.host_map is not None:
            self.host_map.remove_from_sidebar(self)
        # self.close()

    def add_widget(self, widget: widgets.Widget) -> None:
        """
        Adds a widget to the content box.

        Args:
            widget (widgets.Widget): The widget to add to the content box.
        """
        self.content_box.children += (widget,)

    def remove_widget(self, widget: widgets.Widget) -> None:
        """
        Removes a widget from the content box.

        Args:
            widget (widgets.Widget): The widget to remove from the content box.
        """
        self.content_box.children = tuple(
            w for w in self.content_box.children if w != widget
        )

    def set_widgets(self, widgets_list: List[widgets.Widget]) -> None:
        """
        Replaces all widgets in the content box.

        Args:
            widgets_list (List[widgets.Widget]): A list of widgets to set as the content of the content box.
        """
        self.content_box.children = widgets_list

    @property
    def expanded(self) -> bool:
        """
        Returns whether the panel is expanded.
        """
        if len(self.v_model) > 0:
            return True
        else:
            return False


class LayerStyleWidget(widgets.VBox):
    """
    A widget for styling map layers interactively.

    Args:
        layer (dict): The layer to style.
        map_widget (ipyleaflet.Map or folium.Map): The map widget to update.
        widget_width (str, optional): The width of the widget. Defaults to "270px".
        label_width (str, optional): The width of the label. Defaults to "130px".
    """

    def __init__(
        self,
        layer: dict,
        map_widget: Map,
        widget_width: str = "270px",
        label_width: str = "130px",
    ):
        super().__init__()
        self.layer = layer
        self.map = map_widget
        self.layer_type = self._get_layer_type()
        if isinstance(layer["layer"], dict):
            self.layer_id = layer["layer"]["id"]
            if "paint" in layer["layer"]:
                self.layer_paint = layer["layer"]["paint"]
            else:
                self.layer_paint = {}
        else:
            self.layer_id = layer["layer"].id
            self.layer_paint = layer["layer"].paint
        self.original_style = self._get_current_style()
        self.widget_width = widget_width
        self.label_width = label_width

        # Create the styling widgets based on layer type
        self.style_widgets = self._create_style_widgets()

        # Create buttons
        self.apply_btn = widgets.Button(
            description="Apply",
            button_style="primary",
            tooltip="Apply style changes",
            layout=widgets.Layout(width="auto"),
        )

        self.reset_btn = widgets.Button(
            description="Reset",
            button_style="warning",
            tooltip="Reset to original style",
            layout=widgets.Layout(width="auto"),
        )

        self.close_btn = widgets.Button(
            description="Close",
            button_style="",
            tooltip="Close the widget",
            layout=widgets.Layout(width="auto"),
        )

        self.output_widget = widgets.Output()

        # Button container
        self.button_box = widgets.HBox([self.apply_btn, self.reset_btn, self.close_btn])

        # Add button callbacks
        self.apply_btn.on_click(self._apply_style)
        self.reset_btn.on_click(self._reset_style)
        self.close_btn.on_click(self._close_widget)

        # Layout
        self.layout = widgets.Layout(width="300px", padding="10px")

        # Combine all widgets
        self.children = [*self.style_widgets, self.button_box, self.output_widget]

    def _get_layer_type(self) -> str:
        """Determine the layer type."""
        return self.layer["type"]

    def _get_current_style(self) -> dict:
        """Get the current layer style."""
        return self.layer_paint

    def _create_style_widgets(self) -> List[widgets.Widget]:
        """Create style widgets based on layer type."""
        widgets_list = []

        if self.layer_type == "circle":
            widgets_list.extend(
                [
                    self._create_color_picker(
                        "Circle Color", "circle-color", "#3388ff"
                    ),
                    self._create_number_slider(
                        "Circle Radius", "circle-radius", 6, 1, 20
                    ),
                    self._create_number_slider(
                        "Circle Opacity", "circle-opacity", 0.8, 0, 1, 0.05
                    ),
                    self._create_number_slider(
                        "Circle Blur", "circle-blur", 0, 0, 1, 0.05
                    ),
                    self._create_color_picker(
                        "Circle Stroke Color", "circle-stroke-color", "#3388ff"
                    ),
                    self._create_number_slider(
                        "Circle Stroke Width", "circle-stroke-width", 1, 0, 5
                    ),
                    self._create_number_slider(
                        "Circle Stroke Opacity",
                        "circle-stroke-opacity",
                        1.0,
                        0,
                        1,
                        0.05,
                    ),
                ]
            )

        elif self.layer_type == "line":
            widgets_list.extend(
                [
                    self._create_color_picker("Line Color", "line-color", "#3388ff"),
                    self._create_number_slider("Line Width", "line-width", 2, 1, 10),
                    self._create_number_slider(
                        "Line Opacity", "line-opacity", 1.0, 0, 1, 0.05
                    ),
                    self._create_number_slider("Line Blur", "line-blur", 0, 0, 1, 0.05),
                    self._create_dropdown(
                        "Line Style",
                        "line-dasharray",
                        [
                            ("Solid", [1]),
                            ("Dashed", [2, 4]),
                            ("Dotted", [1, 4]),
                            ("Dash-dot", [2, 4, 8, 4]),
                        ],
                    ),
                ]
            )

        elif self.layer_type == "fill":
            widgets_list.extend(
                [
                    self._create_color_picker("Fill Color", "fill-color", "#3388ff"),
                    self._create_number_slider(
                        "Fill Opacity", "fill-opacity", 0.8, 0, 1, 0.05
                    ),
                    self._create_color_picker(
                        "Fill Outline Color", "fill-outline-color", "#3388ff"
                    ),
                ]
            )
        else:
            widgets_list.extend(
                [widgets.HTML(value=f"Layer type {self.layer_type} is not supported.")]
            )

        return widgets_list

    def _create_color_picker(
        self, description: str, property_name: str, default_color: str
    ) -> widgets.ColorPicker:
        """Create a color picker widget."""
        value = self.original_style.get(property_name, default_color)
        if isinstance(value, list) and "match" in value and len(value) >= 5:
            value = value[3]
        return widgets.ColorPicker(
            description=description,
            value=value,
            layout=widgets.Layout(
                width=self.widget_width, description_width=self.label_width
            ),
            style={"description_width": "initial"},
        )

    def _create_number_slider(
        self,
        description: str,
        property_name: str,
        default_value: float,
        min_val: float,
        max_val: float,
        step: float = 1,
    ) -> widgets.FloatSlider:
        """Create a number slider widget."""
        value = self.original_style.get(property_name, default_value)
        if isinstance(value, list) and "match" in value and len(value) >= 5:
            value = value[3]
        return widgets.FloatSlider(
            description=description,
            value=value,
            min=min_val,
            max=max_val,
            step=step,
            layout=widgets.Layout(
                width=self.widget_width, description_width=self.label_width
            ),
            style={"description_width": "initial"},
            continuous_update=False,
        )

    def _create_dropdown(
        self,
        description: str,
        property_name: str,
        options: List[Tuple[str, List[float]]],
    ) -> widgets.Dropdown:
        """Create a dropdown widget."""
        return widgets.Dropdown(
            description=description,
            options=options,
            value=self.original_style.get(property_name, options[0][1]),
            layout=widgets.Layout(
                width=self.widget_width, description_width=self.label_width
            ),
            style={"description_width": "initial"},
        )

    def _apply_style(self, _) -> None:
        """Apply the style changes to the layer."""
        new_style = {}

        for widget in self.style_widgets:
            if isinstance(widget, widgets.ColorPicker):
                property_name = widget.description.lower().replace(" ", "-")
                new_style[property_name] = widget.value
            elif isinstance(widget, widgets.FloatSlider):
                property_name = widget.description.lower().replace(" ", "-")
                new_style[property_name] = widget.value
            elif isinstance(widget, widgets.Dropdown):
                property_name = widget.description.lower().replace(" ", "-")
                new_style[property_name] = widget.value

        with self.output_widget:
            try:
                for key, value in new_style.items():
                    if key == "line-style":
                        key = "line-dasharray"
                    self.map.set_paint_property(self.layer["layer"].id, key, value)
            except Exception as e:
                print(e)

        self.map.layer_manager.refresh()

    def _reset_style(self, _) -> None:
        """Reset to original style."""

        # Update widgets to reflect original style
        for widget in self.style_widgets:
            if isinstance(
                widget, (widgets.ColorPicker, widgets.FloatSlider, widgets.Dropdown)
            ):
                property_name = widget.description.lower().replace(" ", "-")
                if property_name in self.original_style:
                    widget.value = self.original_style[property_name]

    def _close_widget(self, _) -> None:
        """Close the widget."""
        # self.close()
        self.map.remove_from_sidebar(name=f"Style {self.layer_id}")


class DateFilterWidget(widgets.VBox):
    """
    A widget for filtering data based on time range.
    """

    def __init__(
        self,
        sources: List[Dict[str, Any]],
        names: List[str] = None,
        styles: Dict[str, Any] = None,
        start_date_col: str = "startDatetime",
        end_date_col: str = "endDatetime",
        date_col: str = None,
        date_format: str = "%Y-%m-%d",
        min_date: str = None,
        max_date: str = None,
        file_index: int = 0,
        group_col: str = None,
        match: str = "partial",
        freq: str = "D",
        interval: int = 1,
        map_widget: Map = None,
    ) -> None:
        """
        Initialize the DateFilterWidget.

        Args:
            sources (List[Dict[str, Any]]): List of data sources.
            names (List[str], optional): List of names for the data sources. Defaults to None.
            styles (Dict[str, Any], optional): Dictionary of styles for the data sources. Defaults to None.
            start_date_col (str, optional): Name of the column containing the start date. Defaults to "startDatetime".
            end_date_col (str, optional): Name of the column containing the end date. Defaults to "endDatetime".
            date_col (str, optional): Name of the column containing the date. Defaults to None.
            date_format (str, optional): Format of the date. Defaults to "%Y-%m-%d".
            min_date (str, optional): Minimum date. Defaults to None.
            max_date (str, optional): Maximum date. Defaults to None.
            file_index (int, optional): Index of the main file. Defaults to 0.
            group_col (str, optional): Name of the column containing the group. Defaults to None.
            match (str, optional): Match type. Can be "partial" or "exact". Defaults to "partial".
            freq (str, optional): Frequency of the date range. Defaults to "D".
            interval (int, optional): Interval of the date range. Defaults to 1.
            map_widget (Map, optional): Map widget. Defaults to None.
        """
        from datetime import datetime

        super().__init__()

        if names is None:
            names = [f"layer_{i}" for i in range(len(sources))]

        gdfs = []
        if map_widget is not None:
            for index, source in enumerate(sources):
                if index == file_index:
                    fit_bounds = True
                else:
                    fit_bounds = False
                if source is None:
                    gdfs.append(None)
                    continue
                gdf = gpd.read_file(source)
                gdfs.append(gdf)

                style = styles[names[index]]
                layer_type = style["layer_type"]
                paint = style["paint"]
                map_widget.add_gdf(
                    gdf,
                    name=names[index],
                    layer_type=layer_type,
                    paint=paint,
                    fit_bounds=fit_bounds,
                    fit_bounds_options={"animate": False},
                )

            map_widget.add_arrow(
                names[file_index],
                name="arrow",
            )

        gdf = gdfs[file_index]

        if min_date is None:
            min_date = gdf["startDatetime"].min().normalize()
        elif isinstance(min_date, str):
            min_date = datetime.strptime(min_date, date_format)
        elif isinstance(min_date, pd.Timestamp):
            pass
        else:
            raise ValueError("min_date must be a string, pd.Timestamp, or None")

        if max_date is None:
            max_date = gdf["endDatetime"].max().normalize()
        elif isinstance(max_date, str):
            max_date = datetime.strptime(max_date, date_format)
        elif isinstance(max_date, pd.Timestamp):
            pass
        else:
            raise ValueError("max_date must be a string, pd.Timestamp, or None")

        date_range = pd.date_range(min_date, max_date, freq=freq)
        if len(date_range) < 2:
            date_range = pd.date_range(min_date, max_date, freq=freq)

        group_dropdown = widgets.Dropdown(
            description=group_col,
            options=sorted(gdf[group_col].unique()),
            value=None,
            layout=widgets.Layout(width="250px"),
            style={"description_width": "initial"},
        )

        dropdown_reset_btn = widgets.Button(
            icon="eraser",
            tooltip="Clear selection",
            layout=widgets.Layout(width="38px"),
        )

        def on_dropdown_reset_btn_click(_):
            group_dropdown.value = None

        dropdown_reset_btn.on_click(on_dropdown_reset_btn_click)

        dropdown_box = widgets.HBox([group_dropdown, dropdown_reset_btn])

        slider = widgets.SelectionRangeSlider(
            options=list(date_range),
            index=(0, len(date_range) - 1),
            description="Date range:",
            orientation="horizontal",
            continuous_update=True,
            readout=False,
            style={"description_width": "initial"},
            layout=widgets.Layout(width="95%"),
        )

        range_label = widgets.Label()

        date_picker = widgets.DatePicker(
            value=min_date.date(),
            layout=widgets.Layout(width="130px"),
        )

        # Buttons with valid FontAwesome icons
        start_btn = widgets.Button(
            icon="fast-backward",
            tooltip="Go to start date",
            layout=widgets.Layout(width="38px"),
        )
        end_btn = widgets.Button(
            icon="fast-forward",
            tooltip="Go to end date",
            layout=widgets.Layout(width="38px"),
        )
        forward_btn = widgets.Button(
            icon="forward",
            tooltip="Forward one day",
            layout=widgets.Layout(width="38px"),
        )
        backward_btn = widgets.Button(
            icon="backward",
            tooltip="Back one day",
            layout=widgets.Layout(width="38px"),
        )

        nav_box = widgets.HBox(
            [backward_btn, start_btn, date_picker, end_btn, forward_btn]
        )

        output = widgets.Output()

        def clamp_end(start: pd.Timestamp) -> pd.Timestamp:
            """Ensure the end is at least one day after the start."""
            next_day = start + pd.Timedelta(days=interval)
            return next_day if next_day <= max_date else max_date

        def update_date_picker():
            start, end = slider.value
            date_picker.value = start.date()

        def on_date_picker_change(change):
            if change["name"] == "value" and change["type"] == "change":
                new_start = pd.Timestamp(change["new"])
                _, end = slider.value
                # Do not clamp unless end <= new_start
                if new_start > end:
                    slider.value = (new_start, new_start + pd.Timedelta(days=1))
                else:
                    slider.value = (new_start, end)

        def on_start_btn_click(_):
            start = min_date
            end = clamp_end(start)
            slider.value = (start, end)

        def on_end_btn_click(_):
            start = max_date - pd.Timedelta(days=1)
            if start < min_date:
                start = min_date
            end = clamp_end(start)
            slider.value = (start, end)

        def on_forward_btn_click(_):
            start, _ = slider.value
            next_start = start + pd.Timedelta(days=1)
            if next_start <= max_date - pd.Timedelta(days=1):
                slider.value = (next_start, clamp_end(next_start))

        def on_backward_btn_click(_):
            start, _ = slider.value
            prev_start = start - pd.Timedelta(days=1)
            if prev_start >= min_date:
                slider.value = (prev_start, clamp_end(prev_start))

        def on_slider_change(change):
            if slider.value:
                start, end = slider.value
                range_label.value = f"Selected range: {start.strftime(date_format)} to {end.strftime(date_format)}"
                filtered_gdf = gdf[
                    (gdf["startDatetime"] >= start) & (gdf["endDatetime"] <= end)
                ]
                if group_dropdown.value is not None:
                    filtered_gdf = filtered_gdf[
                        filtered_gdf[group_col] == group_dropdown.value
                    ]
                map_widget.set_data(names[file_index], filtered_gdf.__geo_interface__)
                if "arrow" in map_widget.get_layer_names():
                    map_widget.set_data("arrow", filtered_gdf.__geo_interface__)

                for index, point_gdf in enumerate(gdfs[file_index + 1 :]):
                    if point_gdf is None:
                        continue
                    if date_col in point_gdf.columns:
                        filtered = point_gdf[
                            (point_gdf[date_col] >= start)
                            & (point_gdf[date_col] <= end)
                        ]
                    else:
                        filtered = point_gdf
                    if (
                        group_dropdown.value is not None
                        and group_col in point_gdf.columns
                    ):
                        if match == "exact":
                            filtered = filtered[
                                filtered[group_col] == group_dropdown.value
                            ]
                        elif match == "partial":
                            filtered = filtered[
                                filtered[group_col].str.contains(group_dropdown.value)
                            ]
                        else:
                            raise ValueError(f"Invalid match type: {match}")

                    map_widget.set_data(
                        names[index + file_index + 1], filtered.__geo_interface__
                    )
                update_date_picker()

        def on_group_dropdown_change(change):
            if change["name"] == "value" and change["type"] == "change":
                on_slider_change(None)

        group_dropdown.observe(on_group_dropdown_change, names="value")

        slider.observe(on_slider_change, names="value")
        date_picker.observe(on_date_picker_change)
        start_btn.on_click(on_start_btn_click)
        end_btn.on_click(on_end_btn_click)
        forward_btn.on_click(on_forward_btn_click)
        backward_btn.on_click(on_backward_btn_click)

        # Initial trigger
        on_slider_change(None)

        self.children = [dropdown_box, slider, range_label, nav_box, output]


class SelectDataWidget(widgets.VBox):
    """
    A widget for selecting and uploading data to be added to a map.

    This widget allows users to select a folder or upload files to be added to a map.
    It includes a folder chooser, a file uploader, and buttons to apply or reset the selection.
    """

    def __init__(
        self,
        default_path: str = ".",
        widget_width: str = "360px",
        callback: Optional[Callable[[str], None]] = None,
        reset_callback: Optional[Callable[[], None]] = None,
        map_widget: Optional[Map] = None,
    ):
        """
        Initializes the SelectDataWidget.

        Args:
            default_path (str, optional): The default path for the folder chooser. Defaults to ".".
            widget_width (str, optional): The width of the widget. Defaults to "360px".
            callback (Optional[Callable[[str], None]], optional): A callback function
                to be called when data is applied. Defaults to None.
            reset_callback (Optional[Callable[[], None]], optional): A callback function
                to be called when the selection is reset. Defaults to None.
            map_widget (Optional[Map], optional): The map widget to which the data will be added. Defaults to None.
        """
        import tempfile

        import ipyfilechooser

        super().__init__(layout=widgets.Layout(max_width=widget_width))

        temp_dirs = []
        layer_names = []
        source_names = []

        if map_widget is not None:
            layer_names = map_widget.layer_names
            source_names = map_widget.source_names

        folder_chooser = ipyfilechooser.FileChooser(
            default_path=default_path,
            select_dirs=True,
            show_only_dirs=True,
            select_desc="Select Folder",
        )

        folder_chooser._select.layout.min_width = "100px"
        folder_chooser._select.layout.width = "100px"

        uploader = widgets.FileUpload(
            accept=".geojson,.json,.parquet,.csv,.shp,dbf,shx,prj,.gpkg",
            multiple=True,
            description="Upload",
            layout=widgets.Layout(width="120px"),
        )
        output = widgets.Output()

        def on_upload(change):
            folder_chooser.reset()
            with output:
                output.clear_output()
                output.outputs = ()
                output.append_stdout("Uploading ...")
            temp_dir = tempfile.mkdtemp()
            temp_dirs.clear()
            for value in uploader.value:
                filename = value["name"]
                content = value["content"]
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(content)
            temp_dirs.append(temp_dir)
            output.clear_output()
            with output:
                output.outputs = ()
                output.append_stdout("Click Apply to add files to map")

        uploader.observe(on_upload, names="value")

        def on_folder_chooser_change(change):
            uploader.value = ()
            temp_dirs.clear()
            temp_dirs.append(folder_chooser.selected)

        folder_chooser.register_callback(on_folder_chooser_change)

        apply_btn = widgets.Button(
            description="Apply",
            tooltip="Apply selection",
            layout=widgets.Layout(width="80px"),
            style={"description_width": "initial"},
            button_style="primary",
        )

        def default_callback(temp_dir: str):
            """
            The default callback function to add data to the map.

            This function is called when the Apply button is clicked. It finds
                all .geojson files in the selected directory,
            adds them to the map, and fits the bounds to the first file.

            Args:
                temp_dir (str): The temporary directory containing the uploaded files.
            """
            files = common.find_files(temp_dir, ext="geojson", recursive=False)
            if map_widget is not None:
                with output:
                    output.clear_output()
                    output.outputs = ()
                    output.append_stdout("Adding data to the map ...")
                    for index, file in enumerate(files):
                        if index == 0:
                            fit_bounds = True
                        else:
                            fit_bounds = False
                        basename = os.path.basename(file)
                        source_name = os.path.splitext(basename)[0]
                        map_widget.add_geojson(
                            file,
                            name=source_name,
                            fit_bounds=fit_bounds,
                            fit_bounds_options={"animate": False},
                            overwrite=True,
                        )
                    output.clear_output()
                    output.outputs = ()

        def on_apply(change):
            """
            Handles the Apply button click event.

            This function checks if there are any temporary directories containing
                uploaded files. If there are, it calls the callback function
            (either the default or a custom one) to add the data to the map. If not,
                it prompts the user to select a folder or upload files.

            Args:
                change (Any): The change event triggered by the Apply button click.
            """
            with output:
                if callback is None:
                    if len(temp_dirs) > 0:
                        print("Adding data to the map ...")
                        default_callback(temp_dirs[-1])
                        output.clear_output()
                        output.outputs = ()
                    else:
                        output.clear_output()
                        output.outputs = ()
                        output.append_stdout("Select a folder or upload files")
                else:
                    with output:
                        if len(temp_dirs) > 0:
                            output.outputs = ()
                            output.append_stdout("Adding data to the map ...")
                            callback(temp_dirs[-1])
                            output.clear_output()
                            output.outputs = ()
                        else:
                            output.clear_output()
                            output.outputs = ()
                            output.append_stdout("Select a folder or upload files")

            folder_chooser.reset()
            uploader.value = ()
            temp_dirs.clear()

        apply_btn.on_click(on_apply)

        reset_btn = widgets.Button(
            description="Reset",
            tooltip="Clear selection",
            layout=widgets.Layout(width="80px"),
            style={"description_width": "initial"},
            button_style="warning",
        )

        def on_reset(change):
            """
            Handles the Reset button click event.

            This function resets the folder chooser and uploader, clears the temporary
            directories, and removes any layers or sources not in the original list.
            If a reset callback function is provided, it calls that function.

            Args:
                change (Any): The change event triggered by the Reset button click.
            """
            folder_chooser.reset()
            uploader.value = ()
            temp_dirs.clear()

            if map_widget is not None:
                for layer_name in map_widget.layer_names:
                    if layer_name not in layer_names:
                        map_widget.remove_layer(layer_name)
                for source_name in map_widget.source_names:
                    if source_name not in source_names:
                        map_widget.remove_source(source_name)

            if reset_callback is not None:
                reset_callback()
            output.clear_output()
            output.outputs = ()

        reset_btn.on_click(on_reset)
        folder_chooser.layout.width = (
            str(abs(int(widget_width.replace("px", "")) - 60)) + "px"
        )

        self.children = [
            folder_chooser,
            widgets.HBox([uploader, apply_btn, reset_btn]),
            output,
        ]


def TimeSliderWidget(
    m,
    images: Optional[Union[Dict, List, str]] = None,
    labels: Optional[List] = None,
    time_interval: Optional[int] = 1,
    layer_name: Optional[str] = "Image",
    before_id: Optional[str] = None,
    default_index: Optional[int] = 0,
    zoom_to_layer: Optional[bool] = True,
    label_width: Optional[str] = "150px",
    slider_width: Optional[str] = "150px",
    button_width: Optional[str] = "45px",
    **kwargs,
):
    """Adds a time slider to the map.

    Args:
        images (dict, optional): The dictionary containing a set of images.
        labels (list, optional): The list of labels to be used for the time series. Defaults to None.
        time_interval (int, optional): Time interval in seconds. Defaults to 1.
        layer_name (str, optional): The name of the layer. Defaults to "Image".
        before_id (str, optional): The ID of an existing layer before which the new layer should be inserted. Defaults to None.
        default_index (int, optional): The index of the default layer. Defaults to 0.
        zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to False.
        label_width (str, optional): Width of the label. Defaults to "150px".
        slider_width (str, optional): Width of the slider. Defaults to "150px".
        button_width (str, optional): Width of the buttons. Defaults to "45px".
        **kwargs: Additional keyword arguments to be passed to the add_raster or add_cog_layer function.
    """
    import threading
    import time

    import xarray as xr

    if isinstance(images, str):
        images = find_files(images, ext="*.tif", recursive=False)

    if labels is None:
        labels = list(range(1, len(images) + 1))
        labels = [str(label) for label in labels]

    if len(labels) != len(images):
        raise ValueError("The length of labels is not equal to that of layers.")

    if default_index >= 0:
        default_value = default_index + 1
    else:
        default_value = len(labels) + default_index + 1

    slider = widgets.IntSlider(
        min=1,
        max=len(labels),
        readout=False,
        value=default_value,
        continuous_update=False,
        layout=widgets.Layout(width=slider_width),
    )
    label = widgets.Label(
        value=labels[default_index],
        layout=widgets.Layout(padding="0px 5px 0px 5px", width=label_width),
    )

    play_btn = widgets.Button(
        icon="play",
        tooltip="Play the time slider",
        button_style="primary",
        layout=widgets.Layout(width=button_width),
    )

    pause_btn = widgets.Button(
        icon="pause",
        tooltip="Pause the time slider",
        button_style="primary",
        layout=widgets.Layout(width=button_width),
    )

    play_chk = widgets.Checkbox(value=False)

    slider_widget = widgets.HBox([label, slider, play_btn, pause_btn])

    def play_click(b):
        play_chk.value = True

        def work(slider):
            while play_chk.value:
                if slider.value < len(labels):
                    slider.value += 1
                else:
                    slider.value = 1
                time.sleep(time_interval)

        thread = threading.Thread(target=work, args=(slider,))
        thread.start()

    def pause_click(b):
        play_chk.value = False

    play_btn.on_click(play_click)
    pause_btn.on_click(pause_click)

    first_image = images[default_index]
    if isinstance(first_image, str) and first_image.startswith("http"):
        if "{z}/{y}/{x}" in first_image:
            m.add_tile_layer(
                first_image,
                name=layer_name,
                overwrite=True,
                before_id=before_id,
                **kwargs,
            )
        else:
            m.add_cog_layer(
                first_image,
                name=layer_name,
                before_id=before_id,
                overwrite=True,
                fit_bounds=zoom_to_layer,
                **kwargs,
            )
    else:
        m.add_raster(
            first_image,
            name=layer_name,
            overwrite=True,
            fit_bounds=zoom_to_layer,
            before_id=before_id,
            **kwargs,
        )

    def slider_changed(change):
        if change["new"]:
            index = slider.value - 1
            label.value = labels[index]

            if isinstance(images[index], str) and images[index].startswith("http"):
                if "{z}/{y}/{x}" in images[index]:
                    m.add_tile_layer(
                        images[index],
                        name=layer_name,
                        overwrite=True,
                        before_id=before_id,
                        **kwargs,
                    )
                else:
                    m.add_cog_layer(
                        images[index],
                        name=layer_name,
                        overwrite=True,
                        fit_bounds=False,
                        before_id=before_id,
                        **kwargs,
                    )
            else:
                m.add_raster(
                    images[index],
                    name=layer_name,
                    overwrite=True,
                    fit_bounds=False,
                    before_id=before_id,
                    **kwargs,
                )

    slider.observe(slider_changed, "value")

    return slider_widget


def create_arc_layer(
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
) -> dict:
    """
    Create a DeckGL ArcLayer.

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

    return deck_arc_layer
