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
        if orientation in default_dims:
            default = default_dims[orientation]
            return (
                kwargs.get("width", default[0]),
                kwargs.get("height", default[1]),
            )
        raise ValueError(
            f"orientation must be one of [{', '.join(default_dims.keys())}]."
        )


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

    def __check_if_allowed(value, value_name, allowed_list):
        if value not in allowed_list:
            raise ValueError(
                "The "
                + value_name
                + " must be one of the following: {}.".format(", ".join(allowed_list))
            )
        return True

    def __convert_rgb_colors_to_hex(colors):
        try:
            return [common.rgb_to_hex(x) for x in colors]
        except:
            raise ValueError("Unable to convert rgb value to hex.")

    def __create_legend_items(keys, colors):
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

    def __create_layout(**kwargs):
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
