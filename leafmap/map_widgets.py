from typing import Callable, Iterable, List, Optional

import ipyvuetify as v
import ipywidgets as widgets

from . import common


class Colorbar(widgets.Output):
    """A matplotlib colorbar widget that can be added to the map."""

    def __init__(
        self,
        vmin=0,
        vmax=1,
        cmap="gray",
        discrete=False,
        label=None,
        orientation="horizontal",
        transparent_bg=False,
        font_size=9,
        axis_off=False,
        max_width=None,
        **kwargs,
    ):
        """Add a matplotlib colorbar to the map.

        Args:
            vis_params (dict): Visualization parameters as a dictionary. See
                https://developers.google.com/earth-engine/guides/image_visualization # noqa
                for options.
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See
                https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py # noqa
                for options.
            discrete (bool, optional): Whether to create a discrete colorbar.
                Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            orientation (str, optional): Orientation of the colorbar, such as
                "vertical" and "horizontal". Defaults to "horizontal".
            transparent_bg (bool, optional): Whether to use transparent
                background. Defaults to False.
            font_size (int, optional): Font size for the colorbar. Defaults
                to 9.
            axis_off (bool, optional): Whether to turn off the axis. Defaults
                to False.
            max_width (str, optional): Maximum width of the colorbar in pixels.
                Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            ValueError: If the provided min value is not convertible to float.
            ValueError: If the provided max value is not convertible to float.
            ValueError: If the provided opacity value is not convertible to float.
            ValueError: If cmap or palette is not provided.
        """

        import matplotlib  # pylint: disable=import-outside-toplevel
        import numpy  # pylint: disable=import-outside-toplevel

        if max_width is None:
            if orientation == "horizontal":
                max_width = "270px"
            else:
                max_width = "100px"

        vis_params = {
            "min": vmin,
            "max": vmax,
        }

        if not isinstance(vis_params, dict):
            raise TypeError("The vis_params must be a dictionary.")

        if isinstance(kwargs.get("colors"), (list, tuple)):
            vis_params["palette"] = list(kwargs["colors"])

        width, height = self._get_dimensions(orientation, kwargs)

        vmin = vis_params.get("min", kwargs.pop("vmin", 0))
        try:
            vmin = float(vmin)
        except ValueError as err:
            raise ValueError("The provided min value must be scalar type.")

        vmax = vis_params.get("max", kwargs.pop("vmax", 1))
        try:
            vmax = float(vmax)
        except ValueError as err:
            raise ValueError("The provided max value must be scalar type.")

        alpha = vis_params.get("opacity", kwargs.pop("alpha", 1))
        try:
            alpha = float(alpha)
        except ValueError as err:
            raise ValueError("opacity or alpha value must be scalar type.")

        if "palette" in vis_params.keys():
            hexcodes = common.to_hex_colors(common.check_cmap(vis_params["palette"]))
            if discrete:
                cmap = matplotlib.colors.ListedColormap(hexcodes)
                linspace = numpy.linspace(vmin, vmax, cmap.N + 1)
                norm = matplotlib.colors.BoundaryNorm(linspace, cmap.N)
            else:
                cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
                    "custom", hexcodes, N=256
                )
                norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        elif cmap:
            cmap = matplotlib.colormaps[cmap]
            norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        else:
            raise ValueError(
                'cmap keyword or "palette" key in vis_params must be provided.'
            )

        fig, ax = matplotlib.pyplot.subplots(figsize=(width, height))
        cb = matplotlib.colorbar.ColorbarBase(
            ax,
            norm=norm,
            alpha=alpha,
            cmap=cmap,
            orientation=orientation,
            **kwargs,
        )

        label = label or vis_params.get("bands") or kwargs.pop("caption", None)
        if label:
            cb.set_label(label, fontsize=font_size)

        if axis_off:
            ax.set_axis_off()
        ax.tick_params(labelsize=font_size)

        # Set the background color to transparent.
        if transparent_bg:
            fig.patch.set_alpha(0.0)

        super().__init__(layout=widgets.Layout(width=max_width))
        with self:
            self.outputs = ()
            matplotlib.pyplot.show()

    def _get_dimensions(self, orientation, kwargs):
        default_dims = {"horizontal": (3.0, 0.3), "vertical": (0.3, 3.0)}
        if orientation not in default_dims:
            valid_orientations = ", ".join(default_dims.keys())
            raise ValueError(
                f"orientation must be one of [{', '.join(valid_orientations)}]"
            )
        default_width, default_height = default_dims[orientation]
        width = kwargs.get("width", default_width)
        height = kwargs.get("height", default_height)
        return width, height


class Legend(widgets.VBox):
    """A legend widget that can be added to the map."""

    ALLOWED_POSITIONS = ["topleft", "topright", "bottomleft", "bottomright"]
    DEFAULT_COLORS = ["#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3"]
    DEFAULT_KEYS = ["One", "Two", "Three", "Four", "etc"]
    DEFAULT_MAX_HEIGHT = "400px"
    DEFAULT_MAX_WIDTH = "300px"

    def __init__(
        self,
        title="Legend",
        legend_dict=None,
        keys=None,
        colors=None,
        position="bottomright",
        builtin_legend=None,
        add_header=True,
        shape_type="rectangle",
        widget_args={},
        **kwargs,
    ):
        """Adds a customized legend to the map.

         Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'.
            legend_dict (dict, optional): A dictionary containing legend items
                as keys and color as values. If provided, keys and colors will
                be ignored. Defaults to None.
            keys (list, optional): A list of legend keys. Defaults to None.
            colors (list, optional): A list of legend colors. Defaults to None.
            position (str, optional): Position of the legend. Defaults to
                'bottomright'.
            builtin_legend (str, optional): Name of the builtin legend to add
                to the map. Defaults to None.
            add_header (bool, optional): Whether the legend can be closed or
                not. Defaults to True.
            shape_type (str, optional): The shape type of the legend item.
            widget_args (dict, optional): Additional arguments passed to the
                widget_template() function. Defaults to {}.

        Raises:
            TypeError: If the keys are not a list.
            TypeError: If the colors are not list.
            TypeError: If the colors are not a list of tuples.
            TypeError: If the legend_dict is not a dictionary.
            ValueError: If the legend template does not exist.
            ValueError: If a rgb value cannot to be converted to hex.
            ValueError: If the keys and colors are not the same length.
            ValueError: If the builtin_legend is not allowed.
            ValueError: If the position is not allowed.

        """
        import importlib.resources  # pylint: disable=import-outside-toplevel
        import os  # pylint: disable=import-outside-toplevel

        from IPython.display import display  # pylint: disable=import-outside-toplevel

        from .legends import builtin_legends  # pylint: disable=import-outside-toplevel

        pkg_dir = os.path.dirname(importlib.resources.files("leafmap") / "leafmap.py")
        legend_template = os.path.join(pkg_dir, "data/template/legend.html")

        if not os.path.exists(legend_template):
            raise ValueError("The legend template does not exist.")

        if "labels" in kwargs:
            keys = kwargs["labels"]
            kwargs.pop("labels")

        if keys is not None:
            if not isinstance(keys, list):
                raise TypeError("The legend keys must be a list.")
        else:
            keys = Legend.DEFAULT_KEYS

        if colors is not None:
            if not isinstance(colors, list):
                raise TypeError("The legend colors must be a list.")
            elif all(isinstance(item, tuple) for item in colors):
                colors = Legend.__convert_rgb_colors_to_hex(colors)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                raise TypeError("The legend colors must be a list of tuples.")
        else:
            colors = Legend.DEFAULT_COLORS

        if len(keys) != len(colors):
            raise ValueError("The legend keys and colors must be the same length.")

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            builtin_legend_allowed = Legend.__check_if_allowed(
                builtin_legend, "builtin legend", allowed_builtin_legends
            )
            if builtin_legend_allowed:
                legend_dict = builtin_legends[builtin_legend]
                keys = list(legend_dict.keys())
                colors = list(legend_dict.values())

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                raise TypeError("The legend dict must be a dictionary.")
            else:
                keys = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in colors):
                    colors = Legend.__convert_rgb_colors_to_hex(colors)

        Legend.__check_if_allowed(position, "position", Legend.ALLOWED_POSITIONS)

        header = []
        footer = []
        content = Legend.__create_legend_items(keys, colors)

        with open(legend_template) as f:
            lines = f.readlines()
            lines[3] = lines[3].replace("Legend", title)
            header = lines[:6]
            footer = lines[11:]

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
        legend_output = widgets.Output(layout=Legend.__create_layout(**kwargs))
        legend_widget = widgets.HTML(value=legend_text)

        if add_header:
            if "show_close_button" not in widget_args:
                widget_args["show_close_button"] = False
            if "widget_icon" not in widget_args:
                widget_args["widget_icon"] = "bars"

            legend_output_widget = common.widget_template(
                legend_output,
                position=position,
                display_widget=legend_widget,
                **widget_args,
            )
        else:
            legend_output_widget = legend_widget

        super().__init__(children=[legend_output_widget])

        legend_output.clear_output()
        legend_output.outputs = ()
        with legend_output:
            legend_output.append_display_data(legend_widget)

    def __check_if_allowed(value, value_name, allowed_list):  # pylint: disable=E0213
        if value not in allowed_list:
            raise ValueError(
                "The "
                + value_name
                + " must be one of the following: {}.".format(", ".join(allowed_list))
            )
        return True

    def __convert_rgb_colors_to_hex(colors):  # pylint: disable=E0213
        try:
            return [common.rgb_to_hex(x) for x in colors]
        except:
            raise ValueError("Unable to convert rgb value to hex.")

    def __create_legend_items(keys, colors):  # pylint: disable=E0213
        legend_items = []
        for index, key in enumerate(keys):
            color = colors[index]
            if not color.startswith("#"):
                color = "#" + color
            item = "<li><span style='background:{};'></span>{}</li>\n".format(
                color, key
            )
            legend_items.append(item)
        return legend_items

    def __create_layout(**kwargs):  # pylint: disable=E0213
        height = Legend.__create_layout_property("height", None, **kwargs)

        min_height = Legend.__create_layout_property("min_height", None, **kwargs)

        if height is None:
            max_height = Legend.DEFAULT_MAX_HEIGHT
        else:
            max_height = Legend.__create_layout_property("max_height", None, **kwargs)

        width = Legend.__create_layout_property("width", None, **kwargs)

        if "min_width" not in kwargs:
            min_width = None

        if width is None:
            max_width = Legend.DEFAULT_MAX_WIDTH
        else:
            max_width = Legend.__create_layout_property(
                "max_width", Legend.DEFAULT_MAX_WIDTH, **kwargs
            )

        return {
            "height": height,
            "max_height": max_height,
            "max_width": max_width,
            "min_height": min_height,
            "min_width": min_width,
            "overflow": "scroll",
            "width": width,
        }

    def __create_layout_property(name, default_value, **kwargs):
        return default_value if name not in kwargs else kwargs[name]


class LayerEditor(widgets.VBox):
    """Widget for displaying and editing layer visualization properties."""

    def __init__(self, host_map, layer_dict):
        """Initializes a layer editor widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (dict): The layer object to edit.
        """

        # self.on_close = None

        self._host_map = host_map
        self._layer_dict = layer_dict
        if not host_map:
            raise ValueError(
                f"Must pass a valid map when creating a {self.__class__.__name__} widget."
            )

        self._toggle_button = widgets.ToggleButton(
            value=True,
            tooltip="Layer editor",
            icon="gear",
            layout=widgets.Layout(width="28px", height="28px", padding="0px 0 0 3px"),
        )
        self._toggle_button.observe(self._on_toggle_click, "value")

        self._close_button = widgets.Button(
            tooltip="Close the vis params dialog",
            icon="times",
            button_style="primary",
            layout=widgets.Layout(width="28px", height="28px", padding="0"),
        )
        self._close_button.on_click(self._on_close_click)

        layout = widgets.Layout(width="95px")
        self._import_button = widgets.Button(
            description="Import",
            # button_style="primary",
            tooltip="Import vis params to notebook",
            layout=layout,
        )
        self._apply_button = widgets.Button(
            description="Apply", tooltip="Apply vis params to the layer", layout=layout
        )

        self._layer_spinner = widgets.Button(
            icon="check",
            layout=widgets.Layout(width="28px", height="28px", padding="0px"),
            tooltip="Loaded",
        )

        def loading_change(change):
            if change["new"]:
                self._layer_spinner.tooltip = "Loading ..."
                self._layer_spinner.icon = "spinner spin lg"
            else:
                self._layer_spinner.tooltip = "Loaded"
                self._layer_spinner.icon = "check"

        self._import_button.on_click(self._on_import_click)
        self._apply_button.on_click(self._on_apply_click)

        self._label = widgets.Label(
            value=layer_dict["layer_name"],
            layout=widgets.Layout(max_width="200px", padding="1px 4px 0 4px"),
        )
        self._embedded_widget = widgets.Label(value="Vis params are uneditable")
        if layer_dict is not None:
            if layer_dict["type"] in ["LOCAL", "COG", "STAC", "XARRAY"]:
                self._embedded_widget = RasterLayerEditor(
                    host_map=host_map, layer_dict=layer_dict
                )

                layer_dict["tile_layer"].observe(loading_change, "loading")

        super().__init__(children=[])
        self._on_toggle_click({"new": True})

    def _on_toggle_click(self, change):
        if change["new"]:
            self.children = [
                widgets.HBox([self._close_button, self._toggle_button, self._label]),
                self._embedded_widget,
                widgets.HBox(
                    [self._import_button, self._apply_button, self._layer_spinner]
                ),
            ]
        else:
            self.children = [
                widgets.HBox([self._close_button, self._toggle_button, self._label]),
            ]

    def _on_import_click(self, _):
        self._embedded_widget.on_import_click()

    def _on_apply_click(self, _):

        def loading_change(change):
            if change["new"]:
                self._layer_spinner.tooltip = "Loading ..."
                self._layer_spinner.icon = "spinner spin lg"
            else:
                self._layer_spinner.tooltip = "Loaded"
                self._layer_spinner.icon = "check"

        self._layer_spinner.icon = "spinner spin lg"
        self._layer_spinner.unobserve(loading_change, "loading")
        self._embedded_widget.on_apply_click()
        self._host_map.cog_layer_dict[self._layer_dict["layer_name"]][
            "tile_layer"
        ].observe(loading_change, "loading")

    def _on_close_click(self, _):
        # if self.on_close:
        self._layer_editor = None
        self.on_close()


class RasterLayerEditor(widgets.VBox):
    """Widget for displaying and editing layer visualization properties for raster layers."""

    def __init__(self, host_map, layer_dict):
        """Initializes a raster layer editor widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (dict): The layer object to edit.
        """
        self._host_map = host_map
        self._layer_dict = layer_dict

        self._layer_name = self._layer_dict["layer_name"]
        self._layer_opacity = self._layer_dict["opacity"]
        self._min_value = self._layer_dict["vmin"]
        self._max_value = self._layer_dict["vmax"]
        self._band_indexes = self._layer_dict["indexes"]
        self._nodata = self._layer_dict["nodata"]

        if self._layer_dict["type"] == "LOCAL":
            self._tile_client = self._layer_dict["tile_client"]
            self._filename = self._layer_dict["filename"]
        if "xds" in self._layer_dict:
            self._xds = self._layer_dict["xds"]
        else:
            self._xds = None

        if self._min_value is None or self._max_value is None:
            try:
                self._min_value, self._max_value = common.image_min_max(
                    self._filename, self._band_indexes
                )
            except Exception as e:
                self._min_value = 0
                self._max_value = 1

        self._sel_bands = self._layer_dict["vis_bands"]
        self._layer_palette = []
        self._layer_gamma = 1
        self._left_value = min(self._min_value, 0)
        self._right_value = self._max_value * 1.5

        band_names = self._layer_dict["band_names"]
        self._band_count = len(band_names)

        self._greyscale_radio_button = widgets.RadioButtons(
            options=["1 band (Grayscale)"],
            layout={"width": "max-content", "margin": "0 15px 0 0"},
        )
        self._rgb_radio_button = widgets.RadioButtons(
            options=["3 bands (RGB)"], layout={"width": "max-content"}
        )
        self._greyscale_radio_button.index = None
        self._rgb_radio_button.index = None

        band_dropdown_layout = widgets.Layout(width="98px")
        self._band_1_dropdown = widgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._band_2_dropdown = widgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._band_3_dropdown = widgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._bands_hbox = widgets.HBox(layout=widgets.Layout(margin="0 0 6px 0"))

        self._color_picker = widgets.ColorPicker(
            concise=False,
            value="#000000",
            layout=widgets.Layout(width="116px"),
            style={"description_width": "initial"},
        )

        self._add_color_button = widgets.Button(
            icon="plus",
            tooltip="Add a hex color string to the palette",
            layout=widgets.Layout(width="32px"),
        )
        self._del_color_button = widgets.Button(
            icon="minus",
            tooltip="Remove a hex color string from the palette",
            layout=widgets.Layout(width="32px"),
        )
        self._reset_color_button = widgets.Button(
            icon="eraser",
            tooltip="Remove all color strings from the palette",
            layout=widgets.Layout(width="34px"),
        )
        self._add_color_button.on_click(self._add_color_clicked)
        self._del_color_button.on_click(self._del_color_clicked)
        self._reset_color_button.on_click(self._reset_color_clicked)

        self._classes_dropdown = widgets.Dropdown(
            options=["Any"] + [str(i) for i in range(3, 13)],
            description="Classes:",
            layout=widgets.Layout(width="115px"),
            style={"description_width": "initial"},
        )
        self._classes_dropdown.observe(self._classes_changed, "value")

        self._colormap_dropdown = widgets.Dropdown(
            options=self._get_colormaps(),
            value=None,
            description="Colormap:",
            layout=widgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )
        self._colormap_dropdown.observe(self._colormap_changed, "value")

        self._palette_label = widgets.Text(
            value=", ".join(self._layer_palette),
            placeholder="List of hex color code (RRGGBB)",
            description="Palette:",
            tooltip="Enter a list of hex color code (RRGGBB)",
            layout=widgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._value_range_slider = widgets.FloatRangeSlider(
            value=[self._min_value, self._max_value],
            min=self._left_value,
            max=self._right_value,
            step=(self._right_value - self._left_value) / 100,
            description="Range:",
            disabled=False,
            continuous_update=False,
            readout=True,
            readout_format=".2f",
            layout=widgets.Layout(width="300px"),
            style={"description_width": "45px"},
        )

        self._opacity_slider = widgets.FloatSlider(
            value=self._layer_opacity,
            min=0,
            max=1,
            step=0.01,
            description="Opacity:",
            continuous_update=False,
            readout=True,
            readout_format=".2f",
            layout=widgets.Layout(width="310px"),
            style={"description_width": "50px"},
        )

        self._colorbar_output = widgets.Output(
            layout=widgets.Layout(height="60px", max_width="300px")
        )

        children = []
        if self._band_count < 3:
            self._greyscale_radio_button.index = 0
            self._band_1_dropdown.layout.width = "300px"
            self._bands_hbox.children = [self._band_1_dropdown]
            children = self._get_tool_layout(grayscale=True)

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                colors = common.to_hex_colors(
                    [color.strip() for color in self._palette_label.value.split(",")]
                )
                self._render_colorbar(colors)
        else:
            self._rgb_radio_button.index = 0
            sel_bands = self._sel_bands
            if (sel_bands is None) or (len(sel_bands) < 2):
                sel_bands = band_names[0:3]
            self._band_1_dropdown.value = sel_bands[0]
            self._band_2_dropdown.value = sel_bands[1]
            self._band_3_dropdown.value = sel_bands[2]
            self._bands_hbox.children = [
                self._band_1_dropdown,
                self._band_2_dropdown,
                self._band_3_dropdown,
            ]
            children = self._get_tool_layout(grayscale=False)

        self._greyscale_radio_button.observe(self._radio1_observer, names=["value"])
        self._rgb_radio_button.observe(self._radio2_observer, names=["value"])

        super().__init__(
            layout=widgets.Layout(
                padding="5px 0px 5px 8px",  # top, right, bottom, left
                # width="330px",
                max_height="305px",
                overflow="auto",
                display="block",
            ),
            children=children,
        )

    def _get_tool_layout(self, grayscale):
        return [
            widgets.HBox([self._greyscale_radio_button, self._rgb_radio_button]),
            self._bands_hbox,
            self._value_range_slider,
            self._opacity_slider,
        ] + (
            [
                self._colormap_dropdown,
                # self._palette_label,
                self._colorbar_output,
                # widgets.HBox(
                #     [
                #         self._color_picker,
                #         self._add_color_button,
                #         self._del_color_button,
                #         self._reset_color_button,
                #     ]
                # ),
            ]
            if grayscale
            else []
        )

    def _get_colormaps(self):
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colormap_options = pyplot.colormaps()
        colormap_options = [
            item
            for item in colormap_options
            if not (item[0].isupper() or "cet" in item.lower())
        ]
        colormap_options.sort()
        return colormap_options

    def _render_colorbar(self, colors):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colors = common.to_hex_colors(colors)

        _, ax = pyplot.subplots(figsize=(4, 0.3))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "custom", colors, N=256
        )
        norm = matplotlib.colors.Normalize(
            vmin=self._value_range_slider.value[0],
            vmax=self._value_range_slider.value[1],
        )
        matplotlib.colorbar.ColorbarBase(
            ax, norm=norm, cmap=cmap, orientation="horizontal"
        )

        self._palette_label.value = ", ".join(colors)

        self._colorbar_output.clear_output()
        with self._colorbar_output:
            pyplot.show()

    def _classes_changed(self, change):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if not change["new"]:
            return

        selected = change["owner"].value
        if self._colormap_dropdown.value is not None:
            n_class = None
            if selected != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]

    def _add_color_clicked(self, _):
        if self._color_picker.value is not None:
            if len(self._palette_label.value) == 0:
                self._palette_label.value = self._color_picker.value
            else:
                self._palette_label.value += ", " + self._color_picker.value

    def _del_color_clicked(self, _):
        if "," in self._palette_label.value:
            items = [item.strip() for item in self._palette_label.value.split(",")]
            self._palette_label.value = ", ".join(items[:-1])
        else:
            self._palette_label.value = ""

    def _reset_color_clicked(self, _):
        self._palette_label.value = ""

    def _colormap_changed(self, change):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            n_class = None
            if self._classes_dropdown.value != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]

    def on_import_click(self):
        vis = {}
        if self._greyscale_radio_button.index == 0:
            vis["indexes"] = [self._band_1_dropdown.index + 1]
        else:
            vis["indexes"] = [
                self._band_1_dropdown.index + 1,
                self._band_2_dropdown.index + 1,
                self._band_3_dropdown.index + 1,
            ]
            self._colormap_dropdown.value = None

        vis["vmin"] = self._value_range_slider.value[0]
        vis["vmax"] = self._value_range_slider.value[1]
        vis["opacity"] = self._opacity_slider.value
        vis["colormap"] = self._colormap_dropdown.value

        if self._layer_dict["type"] in ["COG", "STAC"]:
            if self._layer_dict["type"] == "COG":
                vis["bidx"] = vis["indexes"]
                if len(vis["bidx"]) == 1:
                    vis["colormap_name"] = vis["colormap"]
            elif self._layer_dict["type"] == "STAC":
                vis["assets"] = self._layer_dict["assets"]
                if len(vis["assets"]) == 1:
                    vis["colormap_name"] = vis["colormap"]
            vis["rescale"] = f'{vis["vmin"]},{vis["vmax"]}'
            vis.pop("vmin", None)
            vis.pop("vmax", None)
            vis.pop("indexes", None)
            vis.pop("colormap", None)

        if "colormap" in vis and vis["colormap"] is None:
            vis.pop("colormap", None)
        common.create_code_cell(f"vis_params = {str(vis)}")
        print(f"vis_params = {str(vis)}")

    def on_apply_click(self):
        from rio_tiler.colormap import cmap

        vis = {}
        if self._greyscale_radio_button.index == 0:
            vis["indexes"] = [self._band_1_dropdown.index + 1]
        else:
            vis["indexes"] = [
                self._band_1_dropdown.index + 1,
                self._band_2_dropdown.index + 1,
                self._band_3_dropdown.index + 1,
            ]
            self._colormap_dropdown.value = None

        vis["vmin"] = self._value_range_slider.value[0]
        vis["vmax"] = self._value_range_slider.value[1]
        vis["opacity"] = self._opacity_slider.value
        vis["colormap"] = self._colormap_dropdown.value

        if vis["colormap"] is not None:
            try:
                cmap.get(vis["colormap"])
            except:
                vis["colormap"] = "gray"
                self._colormap_dropdown.value = "gray"

        old_layer = self._host_map.find_layer(self._layer_name)
        layer_index = self._host_map.find_layer_index(self._layer_name)

        self._host_map.remove(old_layer)

        # Add support for hyperspectral data via HyperCoast
        if self._xds is not None:

            r_index = self._band_1_dropdown.index
            g_index = self._band_2_dropdown.index
            b_index = self._band_3_dropdown.index

            if (r_index >= g_index and g_index >= b_index) or (
                r_index <= g_index and g_index <= b_index
            ):
                pass
            else:
                sorted_indexes = sorted([r_index, g_index, b_index], reverse=True)
                self._band_1_dropdown.index = sorted_indexes[0]
                self._band_2_dropdown.index = sorted_indexes[1]
                self._band_3_dropdown.index = sorted_indexes[2]
                vis["indexes"] = [
                    self._band_1_dropdown.index + 1,
                    self._band_2_dropdown.index + 1,
                    self._band_3_dropdown.index + 1,
                ]
            self._host_map.add_hyper(
                self._xds,
                dtype=self._layer_dict["hyper"],
                wvl_indexes=[index - 1 for index in vis["indexes"]],
                colormap=vis["colormap"],
                vmin=vis["vmin"],
                vmax=vis["vmax"],
                opacity=vis["opacity"],
                nodata=self._nodata,
                layer_name=self._layer_name,
                zoom_to_layer=False,
                layer_index=layer_index,
            )

        elif self._layer_dict["type"] == "LOCAL":
            self._host_map.add_raster(
                self._filename,
                indexes=vis["indexes"],
                colormap=vis["colormap"],
                vmin=vis["vmin"],
                vmax=vis["vmax"],
                opacity=vis["opacity"],
                nodata=self._nodata,
                layer_name=self._layer_name,
                zoom_to_layer=False,
                layer_index=layer_index,
            )

        elif self._layer_dict["type"] == "COG":
            self._host_map.add_cog_layer(
                self._layer_dict["url"],
                bidx=vis["indexes"],
                colormap_name=vis["colormap"],
                rescale=f'{vis["vmin"]},{vis["vmax"]}',
                opacity=vis["opacity"],
                name=self._layer_name,
                zoom_to_layer=False,
                layer_index=layer_index,
            )
        elif self._layer_dict["type"] == "STAC":
            self._host_map.add_stac_layer(
                self._layer_dict["url"],
                titiler_endpoint=self._layer_dict["titiler_endpoint"],
                collection=self._layer_dict["collection"],
                item=self._layer_dict["item"],
                assets=[self._layer_dict["band_names"][i - 1] for i in vis["indexes"]],
                colormap_name=vis["colormap"],
                rescale=f'{vis["vmin"]},{vis["vmax"]}',
                opacity=vis["opacity"],
                name=self._layer_name,
                fit_bounds=False,
                layer_index=layer_index,
            )

        def _remove_control(key):
            if widget := self._layer_dict.get(key, None):
                if widget in self._host_map.controls:
                    self._host_map.remove(widget)
                del self._layer_dict[key]

    def _radio1_observer(self, _):
        self._rgb_radio_button.unobserve(self._radio2_observer, names=["value"])
        self._rgb_radio_button.index = None
        self._rgb_radio_button.observe(self._radio2_observer, names=["value"])
        self._band_1_dropdown.layout.width = "300px"
        self._colormap_dropdown.value = "gray"
        self._bands_hbox.children = [self._band_1_dropdown]
        self._palette_label.value = ", ".join(self._layer_palette)
        self._palette_label.disabled = False
        self._color_picker.disabled = False
        self._add_color_button.disabled = False
        self._del_color_button.disabled = False
        self._reset_color_button.disabled = False
        self.children = self._get_tool_layout(grayscale=True)

        if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
            colors = [color.strip() for color in self._palette_label.value.split(",")]
            self._render_colorbar(colors)

    def _radio2_observer(self, _):
        dropdown_width = "98px"
        self._greyscale_radio_button.unobserve(self._radio1_observer, names=["value"])
        self._greyscale_radio_button.index = None
        self._greyscale_radio_button.observe(self._radio1_observer, names=["value"])
        self._band_1_dropdown.layout.width = dropdown_width
        self._colormap_dropdown.value = None
        self._bands_hbox.children = [
            self._band_1_dropdown,
            self._band_2_dropdown,
            self._band_3_dropdown,
        ]
        self._palette_label.value = ""
        self._palette_label.disabled = True
        self._color_picker.disabled = True
        self._add_color_button.disabled = True
        self._del_color_button.disabled = True
        self._reset_color_button.disabled = True
        self.children = self._get_tool_layout(grayscale=False)
        self._colorbar_output.clear_output()


class TabWidget:
    """
    Reusable ipyvuetify tab widget.

    - Optional tab header bar
    - Optional per-panel titles (bold text inside each card)
    - Toolbar with title and working Refresh/Help buttons
    - Built‑in **Help dialog**; provide your own content via `set_help_content()`
    - Add/remove/rename tabs, set content, observe selection
    """

    def __init__(
        self,
        title: str = "Dashboard",
        tabs: Iterable[str] = ("Overview", "Data", "Settings"),
        icons: Iterable[str] = ("mdi-view-dashboard", "mdi-table", "mdi-cog"),
        contents: Optional[Iterable[widgets.Widget]] = None,
        dark_topbar: bool = True,
        show_tab_header: bool = True,
        show_panel_titles: bool = True,
        wrap_in_card: bool = True,
        elevation: int = 2,
        on_refresh: Optional[Callable[[], None]] = None,
        on_help: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Initialize the TabWidget.

        Args:
            title: The title of the dashboard.
            tabs: The tabs to display.
            icons: The icons to display.
            contents: The contents of the tabs.
            dark_topbar: Whether to use a dark topbar.
            show_tab_header: Whether to show the tab header.
            show_panel_titles: Whether to show the panel titles.
            wrap_in_card: Whether to wrap the contents in a card.
            elevation: The elevation of the tabs.
            on_refresh: The function to call when the refresh button is clicked.
            on_help: The function to call when the help button is clicked.
        """
        self._labels: List[str] = list(tabs)
        self._icons: List[str] = list(icons)
        self._wrap_in_card = wrap_in_card
        self._elevation = elevation
        self._show_titles = show_panel_titles
        self._header_visible = show_tab_header

        # Toolbar
        self._title = v.ToolbarTitle(children=[title])
        self._refresh_btn = v.Btn(
            icon=True, children=[v.Icon(children=["mdi-refresh"])], tooltip="Refresh"
        )
        self._help_btn = v.Btn(
            icon=True,
            children=[v.Icon(children=["mdi-help-circle-outline"])],
            tooltip="Help",
        )
        self._toolbar = v.Toolbar(
            dense=True,
            flat=True,
            color="primary" if dark_topbar else "white",
            dark=dark_topbar,
            children=[self._title, v.Spacer(), self._refresh_btn, self._help_btn],
        )

        # Tabs header & items (linked by jslink)
        self._tabs_header = v.Tabs(
            v_model=0,
            background_color="transparent",
            slider_color="primary",
            class_="px-4" if show_tab_header else "px-4 d-none",
            children=[],
        )
        self._tabs_items = v.TabsItems(v_model=0, children=[])
        widgets.jslink((self._tabs_header, "v_model"), (self._tabs_items, "v_model"))

        # Snackbar for quick feedback
        self._snackbar = v.Snackbar(
            v_model=False, timeout=1400, color="primary", bottom=True, children=[""]
        )

        # Help dialog (default content)
        default_help = widgets.HTML(
            """
            <div style="line-height:1.5">
              <h3 style="margin:0 0 .5rem 0">Help</h3>
              <p>Add your own help content via <code>set_help_content(widget)</code>.</p>
            </div>
            """
        )
        self._help_title = v.CardTitle(class_="text-h6", children=["Help"])
        self._help_cardtext = v.CardText(class_="py-4", children=[default_help])
        self._help_close_btn = v.Btn(text=True, color="primary", children=["Close"])
        self._help_card = v.Card(
            class_="rounded-xl",
            children=[
                self._help_title,
                v.Divider(),
                self._help_cardtext,
                v.CardActions(children=[v.Spacer(), self._help_close_btn]),
            ],
        )
        self._help_dialog = v.Dialog(
            v_model=False, max_width=720, scrollable=True, children=[self._help_card]
        )
        self._help_close_btn.on_event("click", lambda *_: self.close_help_dialog())

        # Global style
        self._style = v.Html(
            tag="style",
            children=[
                """
                .rounded-xl { border-radius: 16px; }
                .v-tab { border-radius: 8px; margin-right: 6px; }
                .v-tab--active { background: rgba(33,150,243,.08); }
                .v-data-table { background: white; }
                .mdi-spin { -webkit-animation: mdi-spin 2s infinite linear; animation: mdi-spin 2s infinite linear; }
                @-webkit-keyframes mdi-spin { 0% { -webkit-transform: rotate(0deg); } 100% { -webkit-transform: rotate(360deg); } }
                @keyframes mdi-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                """
            ],
        )

        # Build initial tabs
        contents_list = list(contents) if contents is not None else []
        for i, label in enumerate(self._labels):
            icon = self._icons[i] if i < len(self._icons) else "mdi-tab"
            body = (
                contents_list[i]
                if i < len(contents_list)
                else widgets.HTML(f"<em>{label}</em> content")
            )
            self._append_tab(label, icon, body)

        # Root
        self._surface = v.Sheet(
            class_="pa-2",
            color="#fafafa",
            children=[
                self._toolbar,
                self._tabs_header,
                self._tabs_items,
                self._snackbar,
                self._help_dialog,
            ],
        )
        self._root = v.Container(
            fluid=True, class_="pa-0", children=[self._style, self._surface]
        )

        # Event plumbing
        self._change_handlers: List[Callable[[int], None]] = []
        self._refresh_handlers: List[Callable[[], None]] = []
        self._help_handlers: List[Callable[[], None]] = []
        if on_refresh:
            self._refresh_handlers.append(on_refresh)
        if on_help:
            self._help_handlers.append(on_help)

        self._tabs_header.observe(self._forward_tab_change, "v_model")
        self._refresh_btn.on_event("click", lambda *_: self._emit_refresh())
        self._help_btn.on_event("click", lambda *_: self._emit_help())

    # Public API
    @property
    def widget(self) -> widgets.Widget:
        return self._root

    @property
    def selected_index(self) -> int:
        return int(self._tabs_header.v_model)

    @selected_index.setter
    def selected_index(self, idx: int) -> None:
        self.select(idx)

    def select(self, index: int) -> None:
        n = len(self._tabs_header.children)
        if not (0 <= index < n):
            raise IndexError(f"index {index} out of range (0..{n-1})")
        self._tabs_header.v_model = int(index)

    def on_tab_change(self, handler: Callable[[int], None]) -> None:
        self._change_handlers.append(handler)

    def on_refresh(self, handler: Callable[[], None]) -> None:
        self._refresh_handlers.append(handler)

    def on_help(self, handler: Callable[[], None]) -> None:
        self._help_handlers.append(handler)

    def set_title(self, title: str) -> None:
        self._title.children = [title]

    def add_tab(
        self,
        label: str,
        icon: str = "mdi-tab",
        content: Optional[widgets.Widget] = None,
        index: Optional[int] = None,
    ) -> None:
        """
        Add a tab to the dashboard.

        Args:
            label: The label of the tab.
            icon: The icon of the tab.
            content: The content of the tab.
            index: The index of the tab.
        """
        if content is None:
            content = widgets.HTML(f"<em>{label}</em> content")
        self._insert_tab(label, icon, content, index)

    def remove_tab(self, index: int) -> None:
        """
        Remove a tab from the dashboard.

        Args:
            index: The index of the tab.
        """
        hdr = list(self._tabs_header.children)
        items = list(self._tabs_items.children)
        n = len(hdr)
        if not (0 <= index < n):
            raise IndexError(f"index {index} out of range (0..{n-1})")
        del hdr[index]
        del items[index]
        self._tabs_header.children = tuple(hdr)
        self._tabs_items.children = tuple(items)
        del self._labels[index]
        if index < len(self._icons):
            del self._icons[index]
        if hdr:
            if self.selected_index >= len(hdr):
                self.select(len(hdr) - 1)
        else:
            self._tabs_header.v_model = 0

    def set_tab_label(self, index: int, label: str) -> None:
        """
        Set the label of a tab.

        Args:
            index: The index of the tab.
            label: The label of the tab.
        """
        tab = self._tabs_header.children[index]
        if len(tab.children) == 2 and isinstance(tab.children[0], v.Icon):
            tab.children = [tab.children[0], label]
        else:
            tab.children = [label]
        self._labels[index] = label
        try:
            item = self._tabs_items.children[index]
            if self._wrap_in_card and isinstance(item.children[0], v.Card):
                card = item.children[0]
                kids = list(card.children)
                if kids and isinstance(kids[0], v.CardTitle):
                    kids[0].children = [label]
                    card.children = kids
        except Exception:
            pass

    def set_tab_icon(self, index: int, icon: Optional[str]) -> None:
        """
        Set the icon of a tab.

        Args:
            index: The index of the tab.
            icon: The icon of the tab.
        """
        tab = self._tabs_header.children[index]
        label = self._labels[index]
        if icon:
            tab.children = [v.Icon(left=True, small=True, children=[icon]), label]
        else:
            tab.children = [label]
        if index < len(self._icons):
            self._icons[index] = icon or ""
        else:
            self._icons.append(icon or "")

    def set_tab_content(self, index: int, content: widgets.Widget) -> None:
        """
        Set the content of a tab.

        Args:
            index: The index of the tab.
            content: The content of the tab.
        """
        item = self._tabs_items.children[index]
        if self._wrap_in_card and isinstance(item.children[0], v.Card):
            card = item.children[0]
            kids = list(card.children)
            replaced = False
            for i, k in enumerate(kids):
                if isinstance(k, v.CardText):
                    kids[i] = v.CardText(class_="py-4", children=[content])
                    card.children = kids
                    replaced = True
                    break
            if not replaced:
                if self._show_titles:
                    card.children = [
                        v.CardTitle(class_="text-h6", children=[self._labels[index]]),
                        v.Divider(),
                        v.CardText(class_="py-4", children=[content]),
                    ]
                else:
                    card.children = [v.CardText(class_="py-4", children=[content])]
        else:
            item.children = [content]

    # Help dialog controls
    def set_help_title(self, title: str) -> None:
        """
        Set the title of the help dialog.

        Args:
            title: The title of the help dialog.
        """
        self._help_title.children = [title]

    def set_help_content(self, content: widgets.Widget) -> None:
        """
        Set the content of the help dialog.

        Args:
            content: The content of the help dialog.
        """
        self._help_cardtext.children = [content]

    def open_help_dialog(self) -> None:
        """
        Open the help dialog.
        """
        self._help_dialog.v_model = True

    def close_help_dialog(self) -> None:
        """
        Close the help dialog.
        """
        self._help_dialog.v_model = False

    @property
    def tab_header_visible(self) -> bool:
        """
        Get the visibility of the tab header.
        """
        return bool(self._header_visible)

    @tab_header_visible.setter
    def tab_header_visible(self, visible: bool) -> None:
        self.set_tab_header_visible(visible)

    def set_tab_header_visible(self, visible: bool) -> None:
        """
        Set the visibility of the tab header.

        Args:
            visible: Whether to show the tab header.
        """
        self._header_visible = bool(visible)
        self._tabs_header.class_ = "px-4" if self._header_visible else "px-4 d-none"

    @property
    def panel_titles_visible(self) -> bool:
        """
        Get the visibility of the panel titles.
        """
        return bool(self._show_titles)

    @panel_titles_visible.setter
    def panel_titles_visible(self, visible: bool) -> None:
        self.set_panel_titles_visible(visible)

    def set_panel_titles_visible(self, visible: bool) -> None:
        """
        Set the visibility of the panel titles.

        Args:
            visible: Whether to show the panel titles.
        """
        self._show_titles = bool(visible)
        for i, item in enumerate(self._tabs_items.children):
            if not self._wrap_in_card or not isinstance(item.children[0], v.Card):
                continue
            card = item.children[0]
            kids = list(card.children)
            if self._show_titles:
                if not kids or not isinstance(kids[0], v.CardTitle):
                    card.children = [
                        v.CardTitle(class_="text-h6", children=[self._labels[i]]),
                        v.Divider(),
                    ] + kids
                else:
                    card.children = kids
            else:
                if kids and isinstance(kids[0], v.CardTitle):
                    if len(kids) > 1 and isinstance(kids[1], v.Divider):
                        card.children = kids[2:]
                    else:
                        card.children = kids[1:]

    # Private helpers
    def _toast(self, message: str, color: str = "primary") -> None:
        """
        Show a snackbar message.

        Args:
            message: The message to show.
            color: The color of the snackbar.
        """
        self._snackbar.color = color
        self._snackbar.children = [message]
        self._snackbar.v_model = False
        self._snackbar.v_model = True

    def _card(self, title_text: str, body: widgets.Widget) -> v.Card:
        """
        Create a card with a title and body.

        Args:
            title_text: The text of the title.
            body: The body of the card.
        """
        if self._show_titles:
            kids = [
                v.CardTitle(class_="text-h6", children=[title_text]),
                v.Divider(),
                v.CardText(class_="py-4", children=[body]),
            ]
        else:
            kids = [v.CardText(class_="py-4", children=[body])]
        return v.Card(
            class_="ma-4 elevation-{} rounded-xl".format(self._elevation),
            children=kids,
        )

    def _append_tab(self, label: str, icon: str, body: widgets.Widget) -> None:
        """
        Append a tab to the dashboard.

        Args:
            label: The label of the tab.
            icon: The icon of the tab.
            body: The body of the tab.
        """
        hdr_children = list(self._tabs_header.children)
        items_children = list(self._tabs_items.children)
        tab_hdr = (
            v.Tab(children=[v.Icon(left=True, small=True, children=[icon]), label])
            if icon
            else v.Tab(children=[label])
        )
        hdr_children.append(tab_hdr)
        content = self._card(label, body) if self._wrap_in_card else body
        items_children.append(v.TabItem(children=[content]))
        self._tabs_header.children = tuple(hdr_children)
        self._tabs_items.children = tuple(items_children)

    def _insert_tab(
        self, label: str, icon: str, body: widgets.Widget, index: Optional[int]
    ) -> None:
        """
        Insert a tab into the dashboard.

        Args:
            label: The label of the tab.
            icon: The icon of the tab.
            body: The body of the tab.
            index: The index of the tab.
        """
        hdr_children = list(self._tabs_header.children)
        items_children = list(self._tabs_items.children)
        n = len(hdr_children)
        if index is None:
            index = n
        if not (0 <= index <= n):
            raise IndexError(f"index {index} out of range (0..{n})")
        tab_hdr = (
            v.Tab(children=[v.Icon(left=True, small=True, children=[icon]), label])
            if icon
            else v.Tab(children=[label])
        )
        hdr_children.insert(index, tab_hdr)
        content = self._card(label, body) if self._wrap_in_card else body
        items_children.insert(index, v.TabItem(children=[content]))
        self._tabs_header.children = tuple(hdr_children)
        self._tabs_items.children = tuple(items_children)
        self._labels.insert(index, label)
        self._icons.insert(index, icon)

    def _forward_tab_change(self, change):
        """
        Forward the tab change event.

        Args:
            change: The change event.
        """
        if change.get("name") == "v_model":
            idx = int(change.get("new", 0) or 0)
            for h in list(self._change_handlers):
                try:
                    h(idx)
                except Exception:
                    pass

    def _emit_refresh(self):
        """
        Emit the refresh event.
        """
        original = self._refresh_btn.children
        try:
            self._refresh_btn.children = [
                v.Icon(children=["mdi-loading"], class_="mdi-spin")
            ]
            if self._refresh_handlers:
                for h in list(self._refresh_handlers):
                    try:
                        h()
                    except Exception as e:
                        self._toast(f"Refresh error: {e}", color="error")
                self._toast("Refreshed")
            else:
                self._toast("Refreshed")
        finally:
            self._refresh_btn.children = original

    def _emit_help(self):
        """
        Emit the help event.
        """
        # Run custom handlers (if any), then open the dialog
        if self._help_handlers:
            for h in list(self._help_handlers):
                try:
                    h()
                except Exception as e:
                    self._toast(f"Help error: {e}", color="error")
        self.open_help_dialog()


class SimilaritySearch(widgets.VBox):
    """A widget for similarity search."""

    def __init__(
        self,
        m: "leafmap.Map",
        before_id: str = None,
        default_year: int = 2024,
        default_color: str = "#0000ff",
        default_threshold: float = 0.8,
    ):
        """
        A widget for similarity search.

        Args:
            m: The map to add the widget to.
            before_id: The ID of the layer to add the widget to.
            default_year: The default year to use for the widget. Defaults to 2024.
            default_color: The default color to use for the widget. Defaults to "#0000ff".
            default_threshold: The default threshold to use for the widget. Defaults to 0.8.

        Returns:
            None
        """
        import ee

        super().__init__()

        style = {"description_width": "initial"}
        year_widget = widgets.IntSlider(
            description="Year",
            value=default_year,
            min=2017,
            max=2024,
            step=1,
            style=style,
        )
        threshold_widget = widgets.FloatSlider(
            description="Threshold",
            value=default_threshold,
            min=0,
            max=1,
            step=0.01,
            style=style,
        )
        color_widget = widgets.ColorPicker(
            description="Color", value=default_color, concise=False, style=style
        )
        layer_name_widget = widgets.Text(
            value=f"Similarity {default_year}",
            description="Layer Name",
            style={"description_width": "initial"},
        )
        apply_button = widgets.Button(
            description="Apply",
            button_style="primary",
            style={"description_width": "initial"},
        )
        reset_button = widgets.Button(
            description="Reset",
            button_style="primary",
            style={"description_width": "initial"},
        )
        output = widgets.Output()
        self.children = [
            year_widget,
            threshold_widget,
            color_widget,
            layer_name_widget,
            widgets.HBox([apply_button, reset_button]),
            output,
        ]
        # m.add_to_sidebar(self, label="Similarity Search", widget_icon="mdi-map-search")

        def year_change(change):
            year = year_widget.value
            layer_name_widget.value = f"Similarity {year}"

        year_widget.observe(year_change, names="value")

        def apply_button_click(change):

            with output:
                if len(m.draw_features_selected) == 0:
                    print("Please create a point on the map")
                    return
                else:
                    try:
                        lon, lat = m.draw_features_selected[0]["geometry"][
                            "coordinates"
                        ]
                        point = ee.Geometry.Point([lon, lat])

                        embeddings = ee.ImageCollection(
                            "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
                        )
                        s2 = ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
                        csPlus = ee.ImageCollection(
                            "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
                        )

                        year = year_widget.value

                        palette = [
                            "000004",
                            "2C105C",
                            "711F81",
                            "B63679",
                            "EE605E",
                            "FDAE78",
                            "FCFDBF",
                            "FFFFFF",
                        ]

                        date_filter = ee.Filter.date(
                            str(year) + "-01-01", str(year + 1) + "-01-01"
                        )

                        mosaic = embeddings.filter(date_filter).mosaic()
                        band_names = mosaic.bandNames()

                        similarity = ee.ImageCollection(
                            mosaic.sample(**{"region": point, "scale": 10}).map(
                                lambda f: ee.Image(f.toArray(band_names))
                                .arrayFlatten(ee.List([band_names]))
                                .multiply(mosaic)
                                .reduce("sum")
                            )
                        )

                        binary = (
                            similarity.mosaic().gt(threshold_widget.value).selfMask()
                        )

                        def magic(i, lo, hi, sat):
                            i = i.add(1).log().divide(10).subtract(lo).divide(hi - lo)
                            grey_axis = (
                                ee.Image(0.57735026919)
                                .addBands(ee.Image(0.57735026919))
                                .addBands(ee.Image(0.57735026919))
                            )
                            grey_level = grey_axis.multiply(
                                i.multiply(grey_axis).reduce("sum")
                            )
                            return i.subtract(grey_level).multiply(sat).add(grey_level)

                        composite = (
                            s2.filter(date_filter)
                            .filterBounds(point)
                            .linkCollection(csPlus, ["cs_cdf"])
                            .map(
                                lambda img: img.updateMask(
                                    img.select("cs_cdf").gte(0.5)
                                )
                            )
                            .median()
                        )

                        composite = magic(
                            composite.select(["B4", "B3", "B2"]), 0.58, 0.9, 1.8
                        )

                        if layer_name_widget.value in m.layer_names:
                            m.remove_layer(layer_name_widget.value)
                        if f"Sentinel-2 {year}" in m.layer_names:
                            m.remove_layer(f"Sentinel-2 {year}")
                        if f"Segmentation {year}" in m.layer_names:
                            m.remove_layer(f"Segmentation {year}")

                        m.add_ee_layer(
                            composite,
                            {"min": 0, "max": 1, "bands": ["B4", "B3", "B2"]},
                            name=f"Sentinel-2 {year}",
                            before_id=before_id,
                        )
                        m.add_ee_layer(
                            similarity,
                            {"min": 0, "max": 1, "palette": palette},
                            name=layer_name_widget.value,
                            before_id=before_id,
                        )
                        m.add_ee_layer(
                            binary,
                            {"min": 0, "max": 1, "palette": [color_widget.value]},
                            name=f"Segmentation {year}",
                            before_id=before_id,
                        )
                    except Exception as e:
                        print(e)
                        print("Error: Please try again")

        apply_button.on_click(apply_button_click)
