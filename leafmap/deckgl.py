from box import Box

from typing import Union, List, Dict, Optional, Tuple, Any
from .basemaps import xyz_to_leaflet
from . import common
from . import map_widgets
from . import plot

from .common import (
    add_crs,
    basemap_xyz_tiles,
    cog_bands,
    cog_bounds,
    cog_center,
    cog_tile,
    convert_lidar,
    create_legend,
    csv_to_df,
    csv_to_geojson,
    csv_to_shp,
    download_file,
    download_from_url,
    download_ned,
    gdf_to_geojson,
    geojson_to_pmtiles,
    get_api_key,
    get_census_dict,
    image_comparison,
    image_to_numpy,
    map_tiles_to_geotiff,
    netcdf_to_tif,
    numpy_to_cog,
    planet_monthly_tiles,
    planet_quarterly_tiles,
    planet_tiles,
    plot_raster,
    plot_raster_3d,
    pmtiles_metadata,
    pmtiles_style,
    read_lidar,
    read_netcdf,
    read_raster,
    read_rasters,
    save_colorbar,
    search_qms,
    search_xyz_services,
    set_api_key,
    show_html,
    show_youtube_video,
    stac_assets,
    stac_bands,
    stac_bounds,
    stac_center,
    stac_info,
    stac_search,
    stac_stats,
    stac_tile,
    start_server,
    vector_to_gif,
    view_lidar,
    write_lidar,
    zonal_stats,
)


try:
    import lonboard
    import geopandas as gpd

except ImportError:
    raise Exception(
        "lonboard needs to be installed to use this module. Use 'pip install lonboard' to install the package."
    )

basemaps = Box(xyz_to_leaflet(), frozen_box=True)


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
        view_state: Optional[Dict] = {},
        **kwargs,
    ) -> None:
        """Initialize a Map object.

        Args:
            center (tuple, optional): Center of the map in the format of (lat, lon). Defaults to (20, 0).
            zoom (float, optional): The map zoom level. Defaults to 1.2.
            height (int, optional): Height of the map. Defaults to 600.
            layers (list, optional): List of additional layers to add to the map. Defaults to [].
            show_tooltip (bool, optional): Flag to show tooltips on the map. Defaults to True.
            view_state (dict, optional): The view state of the map. Defaults to {}.
            **kwargs: Additional keyword arguments to pass to lonboard.Map.

        Returns:
            None
        """

        view_state["latitude"] = center[0]
        view_state["longitude"] = center[1]
        view_state["zoom"] = zoom
        kwargs["view_state"] = view_state

        super().__init__(
            _height=height,
            show_tooltip=show_tooltip,
            layers=layers,
            **kwargs,
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
        alpha: Optional[float] = 1.0,
        rescale: bool = True,
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
        import matplotlib.pyplot as plt

        geom_type = gdf.geometry.iloc[0].geom_type
        kwargs["pickable"] = pickable

        if geom_type in ["Point", "MultiPoint"]:
            if "get_radius" not in kwargs:
                kwargs["get_radius"] = 10
            if color_column is not None:
                if isinstance(color_map, str):
                    kwargs["get_fill_color"] = apply_continuous_cmap(
                        gdf[color_column], color_map, alpha, rescale
                    )
                elif isinstance(color_map, dict):
                    kwargs["get_fill_color"] = apply_categorical_cmap(
                        gdf[color_column], color_map, alpha
                    )

            if "get_fill_color" not in kwargs:
                kwargs["get_fill_color"] = [255, 0, 0, 180]
            layer = ScatterplotLayer.from_geopandas(gdf, **kwargs)
        elif geom_type in ["LineString", "MultiLineString"]:
            if "get_width" not in kwargs:
                kwargs["get_width"] = 5
            if color_column is not None:
                if isinstance(color_map, str):
                    cmap = plt.get_cmap(color_map)
                    kwargs["get_color"] = apply_continuous_cmap(
                        gdf[color_column], cmap, alpha, rescale
                    )
                elif isinstance(color_map, dict):
                    kwargs["get_color"] = apply_categorical_cmap(
                        gdf[color_column], color_map, alpha
                    )
            layer = PathLayer.from_geopandas(gdf, **kwargs)
        elif geom_type in ["Polygon", "MultiPolygon"]:
            if color_column is not None:
                if isinstance(color_map, str):
                    kwargs["get_fill_color"] = apply_continuous_cmap(
                        gdf[color_column], color_map, alpha, rescale
                    )
                elif isinstance(color_map, dict):
                    kwargs["get_fill_color"] = apply_categorical_cmap(
                        gdf[color_column], color_map, alpha
                    )
            if "get_fill_color" not in kwargs:
                kwargs["get_fill_color"] = [0, 0, 255, 128]
            layer = SolidPolygonLayer.from_geopandas(gdf, **kwargs)

        self.layers = self.layers + (layer,)

        if zoom_to_layer:
            try:
                bounds = gdf.total_bounds.tolist()
                x = (bounds[0] + bounds[2]) / 2
                y = (bounds[1] + bounds[3]) / 2

                src_crs = gdf.crs
                if src_crs is None:
                    src_crs = "EPSG:4326"

                lon, lat = common.convert_coordinates(x, y, src_crs, "EPSG:4326")

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

        from lonboard import (
            BitmapLayer,
            BitmapTileLayer,
            HeatmapLayer,
            PathLayer,
            PointCloudLayer,
            PolygonLayer,
            ScatterplotLayer,
            SolidPolygonLayer,
        )

        if type(layer) in [
            BitmapLayer,
            BitmapTileLayer,
            HeatmapLayer,
            ScatterplotLayer,
            PathLayer,
            PointCloudLayer,
            PolygonLayer,
            SolidPolygonLayer,
        ]:
            self.layers = self.layers + (layer,)

            if zoom_to_layer:
                from lonboard._viewport import compute_view

                if hasattr(layer, "table"):
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
            filename = common.temp_file_path("html")
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

    def add_basemap(self, basemap="HYBRID", visible=True, **kwargs) -> None:
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'HYBRID'.
            visible (bool, optional): Whether the basemap is visible or not. Defaults to True.
            **kwargs: Keyword arguments for the TileLayer.
        """
        import xyzservices

        try:

            map_dict = {
                "ROADMAP": "Google Maps",
                "SATELLITE": "Google Satellite",
                "TERRAIN": "Google Terrain",
                "HYBRID": "Google Hybrid",
            }

            if isinstance(basemap, str):
                if basemap.upper() in map_dict:
                    tile = common.get_google_map(basemap.upper())

                    layer = lonboard.BitmapTileLayer(
                        data=tile.url,
                        min_zoom=tile.min_zoom,
                        max_zoom=tile.max_zoom,
                        visible=visible,
                        **kwargs,
                    )

                    self.add_layer(layer)
                    return

            if isinstance(basemap, xyzservices.TileProvider):
                url = basemap.build_url()
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 22
                    layer = lonboard.BitmapTileLayer(
                        data=url,
                        min_zoom=tile.min_zoom,
                        max_zoom=max_zoom,
                        visible=visible,
                        **kwargs,
                    )

                    self.add_layer(layer)
            elif basemap in basemaps and basemaps[basemap].name:
                tile = basemaps[basemap]
                layer = lonboard.BitmapTileLayer(
                    data=tile.url,
                    min_zoom=tile.get("min_zoom", 0),
                    max_zoom=tile.get("max_zoom", 24),
                    visible=visible,
                    **kwargs,
                )
                self.add_layer(layer)
            else:
                print(
                    "Basemap can only be one of the following:\n  {}".format(
                        "\n  ".join(basemaps.keys())
                    )
                )

        except Exception as e:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )

    def add_tile_layer(
        self,
        url: str,
        opacity: float = 1.0,
        visible: bool = True,
        tile_size: int = 256,
        **kwargs: Any,
    ) -> None:
        """
        Adds a TileLayer to the map.

        This method adds a TileLayer to the map. The TileLayer is created from
            the specified URL, and it is added to the map with the specified
            name, attribution, visibility, and tile size.

        Args:
            url (str): The URL of the tile layer.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            visible (bool, optional): Whether the layer should be visible by
                default. Defaults to True.
            tile_size (int, optional): The size of the tiles in the layer.
                Defaults to 256.
            **kwargs: Additional keyword arguments that are passed to the lonboard.BitmapTileLayer class.
                See https://developmentseed.org/lonboard/latest/api/layers/bitmap-tile-layer/#lonboard.BitmapTileLayer.

        Returns:
            None
        """

        layer = lonboard.BitmapTileLayer(
            data=url,
            tile_size=tile_size,
            opacity=opacity,
            visible=visible,
            **kwargs,
        )
        self.add_layer(layer)

    def add_raster(
        self,
        source: str,
        indexes: Optional[int] = None,
        colormap: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        tile_size: Optional[int] = 256,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = "Raster",
        zoom_to_layer: Optional[bool] = True,
        visible: Optional[bool] = True,
        opacity: Optional[float] = 1.0,
        array_args: Optional[Dict] = {},
        client_args: Optional[Dict] = {"cors_all": True},
        **kwargs,
    ) -> None:
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try installing jupyter-server-proxy using `pip install jupyter-server-proxy`,
            then running the following code before calling this function. For more info, see https://bit.ly/3JbmF93.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
            indexes (int, optional): The band(s) to use. Band indexing starts at 1. Defaults to None.
            colormap (str, optional): The name of the colormap from `matplotlib` to use when plotting a single band. See https://matplotlib.org/stable/gallery/color/colormap_reference.html. Default is greyscale.
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Raster'.
            layer_index (int, optional): The index of the layer. Defaults to None.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to True.
            visible (bool, optional): Whether the layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            array_args (dict, optional): Additional arguments to pass to `array_to_memory_file` when reading the raster. Defaults to {}.
            client_args (dict, optional): Additional arguments to pass to localtileserver.TileClient. Defaults to { "cors_all": False }.
        """
        import numpy as np
        import xarray as xr

        if isinstance(source, np.ndarray) or isinstance(source, xr.DataArray):
            source = common.array_to_image(source, **array_args)

        tile_layer, tile_client = common.get_local_tile_layer(
            source,
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            opacity=opacity,
            attribution=attribution,
            layer_name=layer_name,
            client_args=client_args,
            return_client=True,
        )

        self.add_tile_layer(
            tile_layer.url,
            opacity=opacity,
            visible=visible,
            tile_size=tile_size,
            **kwargs,
        )
        if zoom_to_layer:
            center = tile_client.center()
            zoom = tile_client.default_zoom

            self.view_state = {
                "latitude": center[0],
                "longitude": center[1],
                "zoom": zoom,
            }


def apply_continuous_cmap(values, cmap, alpha=None, rescale=True, **kwargs):
    """
    Apply a continuous colormap to a set of values.

    This function rescales the input values to the range [0, 1] if `rescale` is True,
    and then applies the specified colormap.

    Args:
        values (array-like): The input values to which the colormap will be applied.
        cmap (str or Colormap): The colormap to apply. Can be a string name of a matplotlib colormap or a Colormap object.
        alpha (float, optional): The alpha transparency to apply to the colormap. Defaults to None.
        rescale (bool, optional): If True, rescales the input values to the range [0, 1]. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the colormap function.

    Returns:
        array: The colors mapped to the input values.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    if rescale:
        values = np.array(values)
        values = (values - values.min()) / (values.max() - values.min())

    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)

    return lonboard.colormap.apply_continuous_cmap(values, cmap, alpha=alpha, **kwargs)


def apply_categorical_cmap(values, cmap, alpha=None, **kwargs):
    """
    Apply a categorical colormap to a set of values.

    This function applies a specified categorical colormap to the input values.

    Args:
        values (array-like): The input values to which the colormap will be applied.
        cmap (str or Colormap): The colormap to apply. Can be a string name of a matplotlib colormap or a Colormap object.
        alpha (float, optional): The alpha transparency to apply to the colormap. Defaults to None.
        **kwargs: Additional keyword arguments to pass to the colormap function.

    Returns:
        array: The colors mapped to the input values.
    """
    return lonboard.colormap.apply_categorical_cmap(values, cmap, alpha=alpha, **kwargs)
