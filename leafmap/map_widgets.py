import ipywidgets

from . import common


class Colorbar(ipywidgets.Output):
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

        super().__init__(layout=ipywidgets.Layout(width=max_width))
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


class Legend(ipywidgets.VBox):
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
        import os  # pylint: disable=import-outside-toplevel
        from IPython.display import display  # pylint: disable=import-outside-toplevel
        import pkg_resources  # pylint: disable=import-outside-toplevel
        from .legends import builtin_legends  # pylint: disable=import-outside-toplevel

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("leafmap", "leafmap.py")
        )
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
        legend_output = ipywidgets.Output(layout=Legend.__create_layout(**kwargs))
        legend_widget = ipywidgets.HTML(value=legend_text)

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
        with legend_output:
            display(legend_widget)

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


class LayerEditor(ipywidgets.VBox):
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

        self._toggle_button = ipywidgets.ToggleButton(
            value=True,
            tooltip="Layer editor",
            icon="gear",
            layout=ipywidgets.Layout(
                width="28px", height="28px", padding="0px 0 0 3px"
            ),
        )
        self._toggle_button.observe(self._on_toggle_click, "value")

        self._close_button = ipywidgets.Button(
            tooltip="Close the vis params dialog",
            icon="times",
            button_style="primary",
            layout=ipywidgets.Layout(width="28px", height="28px", padding="0"),
        )
        self._close_button.on_click(self._on_close_click)

        layout = ipywidgets.Layout(width="95px")
        self._import_button = ipywidgets.Button(
            description="Import",
            # button_style="primary",
            tooltip="Import vis params to notebook",
            layout=layout,
        )
        self._apply_button = ipywidgets.Button(
            description="Apply", tooltip="Apply vis params to the layer", layout=layout
        )

        self._layer_spinner = ipywidgets.Button(
            icon="check",
            layout=ipywidgets.Layout(width="28px", height="28px", padding="0px"),
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

        self._label = ipywidgets.Label(
            value=layer_dict["layer_name"],
            layout=ipywidgets.Layout(max_width="200px", padding="1px 4px 0 4px"),
        )
        self._embedded_widget = ipywidgets.Label(value="Vis params are uneditable")
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
                ipywidgets.HBox([self._close_button, self._toggle_button, self._label]),
                self._embedded_widget,
                ipywidgets.HBox(
                    [self._import_button, self._apply_button, self._layer_spinner]
                ),
            ]
        else:
            self.children = [
                ipywidgets.HBox([self._close_button, self._toggle_button, self._label]),
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


class RasterLayerEditor(ipywidgets.VBox):
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

        self._greyscale_radio_button = ipywidgets.RadioButtons(
            options=["1 band (Grayscale)"],
            layout={"width": "max-content", "margin": "0 15px 0 0"},
        )
        self._rgb_radio_button = ipywidgets.RadioButtons(
            options=["3 bands (RGB)"], layout={"width": "max-content"}
        )
        self._greyscale_radio_button.index = None
        self._rgb_radio_button.index = None

        band_dropdown_layout = ipywidgets.Layout(width="98px")
        self._band_1_dropdown = ipywidgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._band_2_dropdown = ipywidgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._band_3_dropdown = ipywidgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._bands_hbox = ipywidgets.HBox(layout=ipywidgets.Layout(margin="0 0 6px 0"))

        self._color_picker = ipywidgets.ColorPicker(
            concise=False,
            value="#000000",
            layout=ipywidgets.Layout(width="116px"),
            style={"description_width": "initial"},
        )

        self._add_color_button = ipywidgets.Button(
            icon="plus",
            tooltip="Add a hex color string to the palette",
            layout=ipywidgets.Layout(width="32px"),
        )
        self._del_color_button = ipywidgets.Button(
            icon="minus",
            tooltip="Remove a hex color string from the palette",
            layout=ipywidgets.Layout(width="32px"),
        )
        self._reset_color_button = ipywidgets.Button(
            icon="eraser",
            tooltip="Remove all color strings from the palette",
            layout=ipywidgets.Layout(width="34px"),
        )
        self._add_color_button.on_click(self._add_color_clicked)
        self._del_color_button.on_click(self._del_color_clicked)
        self._reset_color_button.on_click(self._reset_color_clicked)

        self._classes_dropdown = ipywidgets.Dropdown(
            options=["Any"] + [str(i) for i in range(3, 13)],
            description="Classes:",
            layout=ipywidgets.Layout(width="115px"),
            style={"description_width": "initial"},
        )
        self._classes_dropdown.observe(self._classes_changed, "value")

        self._colormap_dropdown = ipywidgets.Dropdown(
            options=self._get_colormaps(),
            value=None,
            description="Colormap:",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )
        self._colormap_dropdown.observe(self._colormap_changed, "value")

        self._palette_label = ipywidgets.Text(
            value=", ".join(self._layer_palette),
            placeholder="List of hex color code (RRGGBB)",
            description="Palette:",
            tooltip="Enter a list of hex color code (RRGGBB)",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._value_range_slider = ipywidgets.FloatRangeSlider(
            value=[self._min_value, self._max_value],
            min=self._left_value,
            max=self._right_value,
            step=(self._right_value - self._left_value) / 100,
            description="Range:",
            disabled=False,
            continuous_update=False,
            readout=True,
            readout_format=".2f",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "45px"},
        )

        self._opacity_slider = ipywidgets.FloatSlider(
            value=self._layer_opacity,
            min=0,
            max=1,
            step=0.01,
            description="Opacity:",
            continuous_update=False,
            readout=True,
            readout_format=".2f",
            layout=ipywidgets.Layout(width="310px"),
            style={"description_width": "50px"},
        )

        self._colorbar_output = ipywidgets.Output(
            layout=ipywidgets.Layout(height="60px", max_width="300px")
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
            layout=ipywidgets.Layout(
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
            ipywidgets.HBox([self._greyscale_radio_button, self._rgb_radio_button]),
            self._bands_hbox,
            self._value_range_slider,
            self._opacity_slider,
        ] + (
            [
                self._colormap_dropdown,
                # self._palette_label,
                self._colorbar_output,
                # ipywidgets.HBox(
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
