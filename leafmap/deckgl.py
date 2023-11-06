from typing import Union, List, Dict, Optional, Tuple, Any

try:
    import lonboard
    import geopandas as gpd

except ImportError:
    raise (
        "lonboard needs to be installed to use this module. Use 'pip install lonboard' to install the package."
    )


class Map(lonboard.Map):
    """The Map class inherits lonboard.Map.

    Returns:
        object: lonboard.Map object.
    """

    def __init__(
        self,
        center: Tuple[float, float] = (20, 0),
        zoom: float = 1.2,
        height: int = 600,
        layers: List = [],
        show_tooltip: bool = True,
        **kwargs
    ) -> None:
        """Initialize a Map object.

        Args:
            center (tuple, optional): Center of the map in the format of (lat, lon). Defaults to (20, 0).
            zoom (float, optional): The map zoom level. Defaults to 1.2.
            height (int, optional): Height of the map. Defaults to 600.
            layers (list, optional): List of additional layers to add to the map. Defaults to [].
            show_tooltip (bool, optional): Flag to show tooltips on the map. Defaults to True.
            **kwargs: Additional keyword arguments to pass to lonboard.Map.

        Returns:
            None
        """

        kwargs["latitude"] = center[0]
        kwargs["longitude"] = center[1]
        kwargs["zoom"] = zoom

        super().__init__(
            _height=height,
            show_tooltip=show_tooltip,
            layers=layers,
            _initial_view_state=kwargs,
        )

    def add_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        zoom_to_layer: bool = True,
        pickable: bool = True,
        **kwargs: Any
    ) -> None:
        """Adds a GeoPandas GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame with geometry column.
            zoom_to_layer (bool, optional): Flag to zoom to the added layer. Defaults to True.
            pickable (bool, optional): Flag to enable picking on the added layer. Defaults to True.
            **kwargs: Additional keyword arguments that will be passed to the GeoDataFrame.

        Returns:
            None
        """

        from lonboard import ScatterplotLayer, PathLayer, SolidPolygonLayer

        geom_type = gdf.geometry.iloc[0].geom_type
        kwargs["pickable"] = pickable

        if geom_type in ["Point", "MultiPoint"]:
            if "get_radius" not in kwargs:
                kwargs["get_radius"] = 10
            if "get_fill_color" not in kwargs:
                kwargs["get_fill_color"] = [255, 0, 0, 180]
            layer = ScatterplotLayer.from_geopandas(gdf, **kwargs)
        elif geom_type in ["LineString", "MultiLineString"]:
            if "get_width" not in kwargs:
                kwargs["get_width"] = 5
            layer = PathLayer.from_geopandas(gdf, **kwargs)
        elif geom_type in ["Polygon", "MultiPolygon"]:
            if "get_fill_color" not in kwargs:
                kwargs["get_fill_color"] = [0, 0, 255, 128]
            layer = SolidPolygonLayer.from_geopandas(gdf, **kwargs)

        self.layers = self.layers + [layer]

        if zoom_to_layer:
            from lonboard._viewport import compute_view

            self._initial_view_state = compute_view([self.layers[-1].table])

    def add_vector(
        self,
        vector: Union[str, gpd.GeoDataFrame],
        zoom_to_layer: bool = True,
        pickable: bool = True,
        open_args: dict = {},
        **kwargs: Any
    ) -> None:
        """Adds a vector layer to the map.

        Args:
            vector (Union[str, GeoDataFrame]): The file path or URL to the vector data, or a GeoDataFrame.
            zoom_to_layer (bool, optional): Flag to zoom to the added layer. Defaults to True.
            pickable (bool, optional): Flag to enable picking on the added layer. Defaults to True.
            open_args (dict, optional): Additional keyword arguments that will be passed to gpd.read_file() if vector is a file path or URL. Defaults to {}.
            **kwargs: Additional keyword arguments that will be passed to the vector layer.

        Returns:
            None
        """

        if isinstance(vector, gpd.GeoDataFrame):
            gdf = vector
        else:
            gdf = gpd.read_file(vector, **open_args)
        self.add_gdf(gdf, zoom_to_layer=zoom_to_layer, pickable=pickable, **kwargs)

    def add_layer(
        self,
        layer: Any,
        zoom_to_layer: bool = True,
        pickable: bool = True,
        **kwargs: Any
    ) -> None:
        """Adds a layer to the map.

        Args:
            layer (Any): A lonboard layer object.
            zoom_to_layer (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            pickable (bool, optional): Flag to enable picking on the added layer if it's a vector layer. Defaults to True.
            **kwargs: Additional keyword arguments that will be passed to the vector layer if it's a vector layer.

        Returns:
            None
        """

        from lonboard import ScatterplotLayer, PathLayer, SolidPolygonLayer

        if type(layer) in [ScatterplotLayer, PathLayer, SolidPolygonLayer]:
            self.layers = self.layers + [layer]

            if zoom_to_layer:
                from lonboard._viewport import compute_view

                self._initial_view_state = compute_view([self.layers[-1].table])
        else:
            self.add_vector(
                layer, zoom_to_layer=zoom_to_layer, pickable=pickable, **kwargs
            )
