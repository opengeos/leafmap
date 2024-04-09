from typing import Union, List, Dict, Optional, Tuple, Any
from .common import *
from .map_widgets import *
from .plot import *

try:
    import lonboard
    import geopandas as gpd

except ImportError:
    raise Exception(
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
        **kwargs,
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
            view_state=kwargs,
        )

    def add_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        zoom_to_layer: bool = True,
        pickable: bool = True,
        color_column: Optional[str] = None,
        color_scheme: Optional[str] = "Quantiles",
        color_map: Optional[Union[str, Dict]] = None,
        color_k: Optional[int] = 5,
        color_args: dict = {},
        zoom: Optional[float] = 10.0,
        **kwargs: Any,
    ) -> None:
        """Adds a GeoPandas GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame with geometry column.
            zoom_to_layer (bool, optional): Flag to zoom to the added layer. Defaults to True.
            pickable (bool, optional): Flag to enable picking on the added layer. Defaults to True.
            color_column (Optional[str], optional): The column to be used for color encoding. Defaults to None.
            color_map (Optional[Union[str, Dict]], optional): The color map to use for color encoding. It can be a string or a dictionary. Defaults to None.
            color_scheme (Optional[str], optional): The color scheme to use for color encoding. Defaults to "Quantiles".
                Name of a choropleth classification scheme (requires mapclassify).
                A mapclassify.MapClassifier object will be used
                under the hood. Supported are all schemes provided by mapclassify (e.g.
                'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
                'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
                'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
                'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
                'UserDefined'). Arguments can be passed in classification_kwds.
            color_k (Optional[int], optional): The number of classes to use for color encoding. Defaults to 5.
            color_args (dict, optional): Additional keyword arguments that will be passed to assign_continuous_colors(). Defaults to {}.
            zoom (Optional[float], optional): The zoom level to zoom to. Defaults to 10.0.
            **kwargs: Additional keyword arguments that will be passed to lonboard.Layer.from_geopandas()

        Returns:
            None
        """

        from lonboard import ScatterplotLayer, PathLayer, SolidPolygonLayer

        geom_type = gdf.geometry.iloc[0].geom_type
        kwargs["pickable"] = pickable

        if geom_type in ["Point", "MultiPoint"]:
            if "get_radius" not in kwargs:
                kwargs["get_radius"] = 10
            if color_column is not None:
                if isinstance(color_map, str):
                    kwargs["get_fill_color"] = assign_continuous_colors(
                        gdf,
                        color_column,
                        color_map,
                        scheme=color_scheme,
                        k=color_k,
                        **color_args,
                    )
                elif isinstance(color_map, dict):
                    kwargs["get_fill_color"] = assign_discrete_colors(
                        gdf, color_column, color_map, to_rgb=True, return_type="array"
                    )
            if "get_fill_color" not in kwargs:
                kwargs["get_fill_color"] = [255, 0, 0, 180]
            layer = ScatterplotLayer.from_geopandas(gdf, **kwargs)
        elif geom_type in ["LineString", "MultiLineString"]:
            if "get_width" not in kwargs:
                kwargs["get_width"] = 5
            if color_column is not None:
                if isinstance(color_map, str):
                    kwargs["get_color"] = assign_continuous_colors(
                        gdf,
                        color_column,
                        color_map,
                        scheme=color_scheme,
                        k=color_k,
                        **color_args,
                    )
                elif isinstance(color_map, dict):
                    kwargs["get_color"] = assign_discrete_colors(
                        gdf, color_column, color_map, to_rgb=True, return_type="array"
                    )
            layer = PathLayer.from_geopandas(gdf, **kwargs)
        elif geom_type in ["Polygon", "MultiPolygon"]:
            if color_column is not None:
                if isinstance(color_map, str):
                    kwargs["get_fill_color"] = assign_continuous_colors(
                        gdf,
                        color_column,
                        color_map,
                        scheme=color_scheme,
                        k=color_k,
                        **color_args,
                    )
                elif isinstance(color_map, dict):
                    kwargs["get_fill_color"] = assign_discrete_colors(
                        gdf, color_column, color_map, to_rgb=True, return_type="array"
                    )
            if "get_fill_color" not in kwargs:
                kwargs["get_fill_color"] = [0, 0, 255, 128]
            layer = SolidPolygonLayer.from_geopandas(gdf, **kwargs)

        self.layers = self.layers + [layer]

        if zoom_to_layer:
            try:
                bounds = gdf.total_bounds.tolist()
                x = (bounds[0] + bounds[2]) / 2
                y = (bounds[1] + bounds[3]) / 2

                src_crs = gdf.crs
                if src_crs is None:
                    src_crs = "EPSG:4326"

                lon, lat = convert_coordinates(x, y, src_crs, "EPSG:4326")

                self.view_state = {
                    "latitude": lat,
                    "longitude": lon,
                    "zoom": zoom,
                }
            except Exception as e:
                print(e)

    def add_vector(
        self,
        vector: Union[str, gpd.GeoDataFrame],
        zoom_to_layer: bool = True,
        pickable: bool = True,
        color_column: Optional[str] = None,
        color_scheme: Optional[str] = "Quantiles",
        color_map: Optional[Union[str, Dict]] = None,
        color_k: Optional[int] = 5,
        color_args: dict = {},
        open_args: dict = {},
        **kwargs: Any,
    ) -> None:
        """Adds a vector layer to the map.

        Args:
            vector (Union[str, GeoDataFrame]): The file path or URL to the vector data, or a GeoDataFrame.
            zoom_to_layer (bool, optional): Flag to zoom to the added layer. Defaults to True.
            pickable (bool, optional): Flag to enable picking on the added layer. Defaults to True.
            color_column (Optional[str], optional): The column to be used for color encoding. Defaults to None.
            color_map (Optional[Union[str, Dict]], optional): The color map to use for color encoding. It can be a string or a dictionary. Defaults to None.
            color_scheme (Optional[str], optional): The color scheme to use for color encoding. Defaults to "Quantiles".
                Name of a choropleth classification scheme (requires mapclassify).
                A mapclassify.MapClassifier object will be used
                under the hood. Supported are all schemes provided by mapclassify (e.g.
                'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
                'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
                'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
                'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
                'UserDefined'). Arguments can be passed in classification_kwds.
            color_k (Optional[int], optional): The number of classes to use for color encoding. Defaults to 5.
            color_args (dict, optional): Additional keyword arguments that will be passed to assign_continuous_colors(). Defaults to {}.
            open_args (dict, optional): Additional keyword arguments that will be passed to geopandas.read_file(). Defaults to {}.
            **kwargs: Additional keyword arguments that will be passed to lonboard.Layer.from_geopandas()

        Returns:
            None
        """

        if isinstance(vector, gpd.GeoDataFrame):
            gdf = vector
        else:
            gdf = gpd.read_file(vector, **open_args)
        self.add_gdf(
            gdf,
            zoom_to_layer,
            pickable,
            color_column,
            color_scheme,
            color_map,
            color_k,
            color_args,
            **kwargs,
        )

    def add_layer(
        self,
        layer: Any,
        zoom_to_layer: bool = True,
        pickable: bool = True,
        **kwargs: Any,
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

                try:
                    self.view_state = compute_view([self.layers[-1].table])
                except Exception as e:
                    print(e)
        else:
            self.add_vector(
                layer, zoom_to_layer=zoom_to_layer, pickable=pickable, **kwargs
            )

    def to_html(self, filename: Optional[str] = None) -> None:
        """Saves the map as an HTML file.

        Args:
            filename (Optional[str], optional): The output file path to the HTML file. Defaults to None.

        Returns:
            str: The HTML content if filename is None.
        """

        if filename is None:
            filename = temp_file_path("html")
            super().to_html(filename)
            with open(filename) as f:
                html = f.read()
            return html
        else:
            super().to_html(filename)

    def to_streamlit(
        self,
        width: Optional[int] = None,
        height: Optional[int] = 600,
        scrolling: Optional[bool] = False,
        **kwargs,
    ):
        """Renders `deckgl.Map`in a Streamlit app. This method is a static Streamlit Component, meaning, no information is passed back from Leaflet on browser interaction.

        Args:
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to 600.
            scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit.components.v1 as components

            return components.html(
                self.to_html(), width=width, height=height, scrolling=scrolling
            )

        except Exception as e:
            raise e
