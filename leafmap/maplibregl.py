"""The maplibregl module provides the Map class for creating interactive maps using the maplibre.ipywidget module.
"""

from maplibre.ipywidget import MapWidget
from maplibre import Layer, LayerType, MapOptions


class Map(MapWidget):
    """The Map class inherits from the MapWidget class of the maplibre.ipywidget module."""

    def __init__(self, center=(20, 0), zoom=1, height="600px", **kwargs):
        """Create a Map object.

        Args:
            center (tuple, optional): The center of the map (lat, lon). Defaults to (20, 0).
            zoom (int, optional): The zoom level of the map. Defaults to 1.
            height (str, optional): The height of the map. Defaults to "600px".
            **kwargs: Additional keyword arguments that are passed to the MapOptions class.
                See https://maplibre.org/maplibre-gl-js/docs/API/types/MapOptions/ for more information.
        """
        center = (center[1], center[0])
        map_options = MapOptions(center=center, zoom=zoom, **kwargs)

        super().__init__(map_options, height=height)
