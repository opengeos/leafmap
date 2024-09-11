import os
from box import Box
import xyzservices.providers as xyz
from bokeh.models import WheelZoomTool, WMTSTileSource, GeoJSONDataSource, HoverTool
from bokeh.plotting import figure, show, save
from bokeh.io import output_notebook
from .basemaps import xyz_to_bokeh
from .common import *
from typing import Optional, List, Dict

os.environ["OUTPUT_NOTEBOOK"] = "False"
basemaps = Box(xyz_to_bokeh(), frozen_box=True)


class Map:
    def __init__(
        self,
        center: List[float] = [10, 0],
        zoom: float = 2,
        width: float = 800,
        height: float = 400,
        basemap: Optional[str] = "OpenStreetMap",
        grid_visible: bool = False,
        output_notebook: bool = True,
        **kwargs,
    ):
        if "x_axis_type" not in kwargs:
            kwargs["x_axis_type"] = "mercator"
        if "y_axis_type" not in kwargs:
            kwargs["y_axis_type"] = "mercator"
        if "sizing_mode" not in kwargs:
            kwargs["sizing_mode"] = "scale_both"
        if "width" not in kwargs:
            kwargs["width"] = width
        if "height" not in kwargs:
            kwargs["height"] = height

        if "x_range" not in kwargs:
            kwargs["x_range"] = center_zoom_to_xy_range(center, zoom)[0]
        if "y_range" not in kwargs:
            kwargs["y_range"] = center_zoom_to_xy_range(center, zoom)[1]

        fig = figure(**kwargs)
        self.figure = fig

        if basemap is not None:
            if basemap == "OpenStreetMap":
                try:
                    fig.add_tile(xyz.OpenStreetMap.Mapnik, retina=True)
                except:
                    from bokeh.tile_providers import get_provider

                    fig.add_tile(get_provider(xyz.OpenStreetMap.Mapnik))
            else:
                self.add_basemap(basemap)
        fig.toolbar.active_scroll = fig.select_one(WheelZoomTool)

        if not grid_visible:
            fig.grid.visible = False

        self.output_notebook = output_notebook
        self.output_notebook_done = False

    def _repr_mimebundle_(self, **kwargs) -> None:
        """Display the bokeh map. Reference: https://ipython.readthedocs.io/en/stable/config/integrating.html#MyObject._repr_mimebundle_"""
        if self.output_notebook and (os.environ["OUTPUT_NOTEBOOK"] == "False"):
            output_notebook()
            os.environ["OUTPUT_NOTEBOOK"] = "True"
        show(self.figure)

    def add_basemap(
        self,
        basemap: Optional[str] = "OpenStreetMap",
        retina: Optional[bool] = True,
        **kwargs,
    ) -> None:
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'OpenStreetMap'.
            retina (bool, optional): Whether to use retina tiles. Defaults to True.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.add_tile() function, such as alpha, visible, etc.
        """
        import xyzservices

        if isinstance(basemap, xyzservices.TileProvider):
            url = basemap.build_url()
            attribution = basemap.attribution
            if "max_zoom" in basemap.keys():
                max_zoom = basemap["max_zoom"]
            else:
                max_zoom = 30
            tile_options = {
                "url": url,
                "attribution": attribution,
                "max_zoom": max_zoom,
            }
            tile_source = WMTSTileSource(**tile_options)
            self.add_tile(tile_source, retina=retina, **kwargs)
        elif isinstance(basemap, WMTSTileSource):
            self.add_tile(basemap, retina=retina, **kwargs)
        elif isinstance(basemap, str):
            if basemap in basemaps.keys():
                self.add_tile(basemaps[basemap], retina=retina, **kwargs)
            else:
                try:
                    self.add_tile(basemap, retina=retina, **kwargs)
                except Exception as e:
                    print(e)
                    raise ValueError(
                        f"Basemap {basemap} is not supported. Please choose one from {basemaps.keys()}"
                    )
        elif basemap is None:
            raise ValueError("Please specify a valid basemap")

    def add_tile(self, tile: str, **kwargs) -> None:
        """Adds a tile to the map.

        Args:
            tile (bokeh.models.tiles.WMTSTileSource): A bokeh tile.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.add_tile() function, such as alpha, visible, etc.
        """
        try:
            self.figure.add_tile(tile, **kwargs)
        except Exception as e:
            if "retina" in kwargs.keys():
                kwargs.pop("retina")
            self.figure.add_tile(tile, **kwargs)

    def add_cog_layer(
        self,
        url: str,
        attribution: str = "",
        bands: Optional[List[str]] = None,
        titiler_endpoint: Optional[str] = None,
        cog_args: Dict = {},
        fit_bounds: bool = True,
        **kwargs,
    ) -> None:
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            attribution (str, optional): The attribution to use. Defaults to ''.
            bands (list, optional): A list of bands to use for the layer. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
            cog_args: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.add_tile() function, such as alpha, visible, etc.
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **cog_args)
        tile_options = {
            "url": tile_url,
            "attribution": attribution,
        }
        tile_source = WMTSTileSource(**tile_options)
        self.figure.add_tile(tile_source, **kwargs)

        if fit_bounds:
            self.fit_bounds(cog_bounds(url, titiler_endpoint))

    def add_raster(
        self,
        source: str,
        indexes: Optional[List] = None,
        colormap: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = "",
        fit_bounds: bool = True,
        layer_name="Local COG",
        open_args={},
        **kwargs,
    ) -> None:
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try running the following code before calling this function:

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
            indexes (int, optional): The band(s) to use. Band indexing starts at 1. Defaults to None.
            colormap (str, optional): The name of the colormap from `matplotlib` to use when plotting a single band. See https://matplotlib.org/stable/gallery/color/colormap_reference.html. Default is greyscale.
            vmin (float, optional): The minimum value to use when colormapping the colormap when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the colormap when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Local COG'.
            fit_bounds (bool, optional): Whether to fit the map bounds to the raster bounds. Defaults to True.
            open_args: Arbitrary keyword arguments for get_local_tile_layer(). Defaults to {}.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.add_tile() function, such as alpha, visible, etc.
        """

        if source.startswith("http"):
            source = download_file(source)

        tile_layer, client = get_local_tile_layer(
            source,
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            layer_name=layer_name,
            return_client=True,
            **open_args,
        )

        tile_options = {
            "url": tile_layer.url,
            "attribution": attribution,
        }
        tile_source = WMTSTileSource(**tile_options)
        self.figure.add_tile(tile_source, **kwargs)

        if fit_bounds:
            bounds = client.bounds()
            bounds = [bounds[2], bounds[0], bounds[3], bounds[1]]
            self.fit_bounds(bounds)

    def add_stac_layer(
        self,
        url: str,
        collection: Optional[str] = None,
        item: Optional[str] = None,
        assets: Optional[str] = None,
        bands: Optional[List[str]] = None,
        titiler_endpoint: Optional[str] = None,
        attribution: Optional[str] = "",
        fit_bounds: Optional[bool] = True,
        open_args={},
        **kwargs,
    ) -> None:
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
            collection (str | Optional): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_endpoint (str, optional): TiTiler endpoint, e.g., "https://titiler.xyz", "https://planetarycomputer.microsoft.com/api/data/v1", "planetary-computer", "pc". Defaults to None.
            attribution (str, optional): The attribution to use. Defaults to ''.
            fit_bounds (bool, optional): Whether to fit the map bounds to the raster bounds. Defaults to True.
            open_args: Arbitrary keyword arguments for get_local_tile_layer(). Defaults to {}.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.add_tile() function, such as alpha, visible, etc.

        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **open_args
        )
        tile_options = {
            "url": tile_url,
            "attribution": attribution,
        }
        tile_source = WMTSTileSource(**tile_options)
        self.figure.add_tile(tile_source, **kwargs)

        if fit_bounds:
            self.fit_bounds(stac_bounds(url, collection, item, titiler_endpoint))

    def add_gdf(
        self,
        gdf,
        to_crs: Optional[str] = "epsg:3857",
        tooltips: Optional[list] = None,
        fit_bounds: bool = True,
        **kwargs,
    ) -> None:
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): The GeoDataFrame to add to the map.
            to_crs (str, optional): The CRS to use for the GeoDataFrame. Defaults to "epsg:3857".
            tooltips (list, optional): A list of column names to use for tooltips in the form of [(name, @column_name), ...]. Defaults to None, which uses all columns.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.circle, multi_line, and patches. For more info, see
                https://docs.bokeh.org/en/latest/docs/reference/plotting/figure.html#bokeh.plotting.figure
        """
        import geopandas as gpd

        if not isinstance(gdf, gpd.GeoDataFrame):
            raise TypeError("gdf must be a GeoDataFrame")

        geom_type = gdf_geom_type(gdf)
        gdf_new = gdf.to_crs(to_crs)

        columns = gdf_new.columns.to_list()
        if "geometry" in columns:
            columns.remove("geometry")

        if tooltips is None:
            tooltips = [(col, f"@{col}") for col in columns]

        source = GeoJSONDataSource(geojson=gdf_new.to_json())

        if geom_type in ["Point", "MultiPoint"]:
            self.figure.circle(x="x", y="y", source=source, **kwargs)
        elif geom_type in ["LineString", "MultiLineString"]:
            self.figure.multi_line(xs="xs", ys="ys", source=source, **kwargs)
        elif geom_type in ["Polygon", "MultiPolygon"]:
            if "fill_alpha" not in kwargs:
                kwargs["fill_alpha"] = 0.5
            self.figure.patches(xs="xs", ys="ys", source=source, **kwargs)

        if len(tooltips) > 0:
            hover = HoverTool(tooltips=tooltips)
            self.figure.add_tools(hover)

        if fit_bounds:
            self.fit_bounds(gdf.total_bounds.tolist())

    def add_geojson(
        self,
        filename: str,
        encoding: Optional[str] = "utf-8",
        read_file_args: Dict = {},
        to_crs: Optional[str] = "epsg:3857",
        tooltips: Optional[List] = None,
        fit_bounds: bool = True,
        **kwargs,
    ) -> None:
        """Adds a GeoJSON file to the map.

        Args:
            filename (str): The path to the GeoJSON file. Can be a local file or a URL.
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
            read_file_args (Dict, optional): A dictionary of arguments to pass to geopandas.read_file. Defaults to {}.
            to_crs (str, optional): The CRS to use for the GeoDataFrame. Defaults to "epsg:3857".
            tooltips (list, optional): A list of column names to use for tooltips in the form of [(name, @column_name), ...]. Defaults to None, which uses all columns.
            fit_bounds (bool, optional): A flag indicating whether to fit the map bounds to the GeoJSON. Defaults to True.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.circle, multi_line, and patches. For more info, see
                https://docs.bokeh.org/en/latest/docs/reference/plotting/figure.html#bokeh.plotting.figure
        """
        import geopandas as gpd

        if filename.startswith("http"):
            filename = github_raw_url(filename)

        gdf = gpd.read_file(filename, encoding=encoding, **read_file_args)
        self.add_gdf(
            gdf, to_crs=to_crs, tooltips=tooltips, fit_bounds=fit_bounds, **kwargs
        )

    def add_shp(
        self,
        filename: str,
        encoding: Optional[str] = "utf-8",
        read_file_args: Dict = {},
        to_crs: Optional[str] = "epsg:3857",
        tooltips: Optional[List] = None,
        fit_bounds: bool = True,
        **kwargs,
    ) -> None:
        """Adds a shapefile to the map.

        Args:
            filename (str): The path to the shapefile.
            encoding (str, optional): The encoding of the shapefile. Defaults to "utf-8".
            read_file_args (dict, optional): A dictionary of arguments to pass to geopandas.read_file. Defaults to {}.
            to_crs (str, optional): The CRS to use for the GeoDataFrame. Defaults to "epsg:3857".
            tooltips (list, optional): A list of column names to use for tooltips in the form of [(name, @column_name), ...]. Defaults to None, which uses all columns.
            fit_bounds (bool, optional): A flag indicating whether to fit the map bounds to the shapefile. Defaults to True.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.circle, multi_line, and patches. For more info, see
                https://docs.bokeh.org/en/latest/docs/reference/plotting/figure.html#bokeh.plotting.figure
        """
        import geopandas as gpd

        import glob

        if filename.startswith("http"):
            filename = github_raw_url(filename)

        if filename.startswith("http") and filename.endswith(".zip"):
            out_dir = os.path.abspath("./cache/shp")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            basename = os.path.basename(filename)
            output = os.path.join(out_dir, basename)
            download_file(filename, output)
            files = list(glob.glob(os.path.join(out_dir, "*.shp")))
            if len(files) > 0:
                filename = files[0]
            else:
                raise FileNotFoundError(
                    "The downloaded zip file does not contain any shapefile in the root directory."
                )
        else:
            filename = os.path.abspath(filename)
            if not os.path.exists(filename):
                raise FileNotFoundError("The provided shapefile could not be found.")

        gdf = gpd.read_file(filename, encoding=encoding, **read_file_args)
        self.add_gdf(
            gdf, to_crs=to_crs, tooltips=tooltips, fit_bounds=fit_bounds, **kwargs
        )

    def add_vector(
        self,
        filename: str,
        encoding: Optional[str] = "utf-8",
        read_file_args: Dict = {},
        to_crs: Optional[str] = "epsg:3857",
        tooltips: Optional[List] = None,
        fit_bounds: bool = True,
        **kwargs,
    ) -> None:
        """Adds a vector dataset to the map.

        Args:
            filename (str): The path to the vector dataset. Can be a local file or a URL.
            encoding (str, optional): The encoding of the vector dataset. Defaults to "utf-8".
            read_file_args (Dict, optional): A dictionary of arguments to pass to geopandas.read_file. Defaults to {}.
            to_crs (str, optional): The CRS to use for the GeoDataFrame. Defaults to "epsg:3857".
            tooltips (list, optional): A list of column names to use for tooltips in the form of [(name, @column_name), ...]. Defaults to None, which uses all columns.
            fit_bounds (bool, optional): A flag indicating whether to fit the map bounds to the vector dataset. Defaults to True.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.circle, multi_line, and patches. For more info, see
                https://docs.bokeh.org/en/latest/docs/reference/plotting/figure.html#bokeh.plotting.figure
        """
        import geopandas as gpd

        if filename.startswith("http"):
            filename = github_raw_url(filename)

        if isinstance(filename, gpd.GeoDataFrame):
            gdf = filename
        else:
            gdf = gpd.read_file(filename, encoding=encoding, **read_file_args)

        self.add_gdf(
            gdf, to_crs=to_crs, tooltips=tooltips, fit_bounds=fit_bounds, **kwargs
        )

    def to_html(
        self, filename: Optional[str] = None, title: Optional[str] = None, **kwargs
    ) -> None:
        """Converts the map to HTML.

        Args:
            filename (str, optional): The filename to save the HTML to. Defaults to None.
            title (str, optional): The title to use for the HTML. Defaults to None.
            **kwargs: Arbitrary keyword arguments for bokeh.figure.save().
        """
        save(self.figure, filename=filename, title=title, **kwargs)

    def fit_bounds(self, bounds: List[float]):
        """Fits the map to the specified bounds in the form of [xmin, ymin, xmax, ymax].

        Args:
            bounds (list): A list of bounds in the form of [xmin, ymin, xmax, ymax].
        """

        bounds = bounds_to_xy_range(bounds)

        self.figure.x_range.start = bounds[0][0]
        self.figure.x_range.end = bounds[0][1]
        self.figure.y_range.start = bounds[1][0]
        self.figure.y_range.end = bounds[1][1]

    def to_streamlit(
        self,
        width: Optional[int] = 800,
        height: Optional[int] = 600,
        use_container_width: bool = True,
        **kwargs,
    ) -> None:
        """Displays the map in a Streamlit app.

        Args:
            width (int, optional): The width of the map. Defaults to 800.
            height (int, optional): The height of the map. Defaults to 600.
            use_container_width (bool, optional): A flag indicating whether to use the full width of the container. Defaults to True.
            **kwargs: Arbitrary keyword arguments for bokeh.plotting.show().
        """
        import streamlit as st  # pylint: disable=E0401

        self.figure.width = width
        self.figure.height = height

        st.bokeh_chart(
            self.figure,
            use_container_width=use_container_width,
            **kwargs,
        )
