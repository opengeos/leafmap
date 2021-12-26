import os
import numpy as np
import plotly.graph_objects as go
from .basemaps import xyz_to_plotly

plotly_basemaps = xyz_to_plotly()


class Map(go.FigureWidget):
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

    def add_scatter_plot_demo(self, **kwargs):
        """Adds a scatter plot to the map."""
        lons = np.random.random(1000) * 360.0
        lats = np.random.random(1000) * 180.0 - 90.0
        z = np.random.random(1000) * 50.0
        self.add_scattermapbox(lon=lons, lat=lats, marker={"color": z})

    def add_basemap(self, basemap="ROADMAP"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from plotly_basemaps. Defaults to 'ROADMAP'.
        """
        if basemap not in plotly_basemaps:
            raise ValueError(
                f"Basemap {basemap} not found. Choose from {','.join(plotly_basemaps.keys())}"
            )

        self.update_layout(mapbox_layers=[plotly_basemaps[basemap]])

    def add_mapbox_layer(self, style, access_token=None):
        """Adds a mapbox layer to the map.

        Args:
            layer (str | dict): Layer to add. Can be "basic", "streets", "outdoors", "light", "dark", "satellite", or "satellite-streets". See https://plotly.com/python/mapbox-layers/ and https://docs.mapbox.com/mapbox-gl-js/style-spec/
        """

        if access_token is None:
            access_token = os.environ.get("MAPBOX_TOKEN")

        self.update_layout(mapbox_style=style, mapbox_accesstoken=access_token)


def fix_widget_error():
    """
    Fix FigureWidget - 'mapbox._derived' Value Error.
    Adopted from: https://github.com/plotly/plotly.py/issues/2570#issuecomment-738735816
    """
    basedatatypesPath = os.path.join(
        os.path.dirname(os.__file__), "site-packages", "plotly", "basedatatypes.py"
    )

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
