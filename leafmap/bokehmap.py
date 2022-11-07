import os
from box import Box
import xyzservices.providers as xyz
from bokeh.models import WheelZoomTool, WMTSTileSource
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from .basemaps import xyz_to_bokeh
from .common import *

os.environ["OUTPUT_NOTEBOOK"] = "False"
basemaps = Box(xyz_to_bokeh(), frozen_box=True)


class Map:
    def __init__(
        self,
        center=[20, 0],
        zoom=2,
        width=800,
        height=400,
        basemap="OpenStreetMap",
        grid_visible=False,
        output_notebook=True,
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
            kwargs["x_range"] = (-18026376.39, 18026376.39)
        if "y_range" not in kwargs:
            kwargs["y_range"] = (-9470853.55, 14010601.53)

        fig = figure(**kwargs)
        self.figure = fig

        if basemap is not None:
            if basemap == "OpenStreetMap":
                fig.add_tile(xyz.OpenStreetMap.Mapnik)
            else:
                self.add_basemap(basemap)
        fig.toolbar.active_scroll = fig.select_one(WheelZoomTool)

        if not grid_visible:
            fig.grid.visible = False

        self.output_notebook = output_notebook
        self.output_notebook_done = False

    def _repr_mimebundle_(self, **kwargs):
        """Display the bokeh map. Reference: https://ipython.readthedocs.io/en/stable/config/integrating.html#MyObject._repr_mimebundle_"""
        if self.output_notebook and (os.environ["OUTPUT_NOTEBOOK"] == "False"):
            output_notebook()
            os.environ["OUTPUT_NOTEBOOK"] = "True"
        show(self.figure)

    def add_basemap(self, basemap="OpenStreetMap"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'OpenStreetMap'.
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
            self.figure.add_tile(tile_source)
        elif isinstance(basemap, WMTSTileSource):
            self.figure.add_tile(basemap)
        elif isinstance(basemap, str):
            if basemap in basemaps.keys():
                self.figure.add_tile(basemaps[basemap])
            else:
                try:
                    self.figure.add_tile(basemap)
                except Exception as e:
                    print(e)
                    raise ValueError(
                        f"Basemap {basemap} is not supported. Please choose one from {basemaps.keys()}"
                    )

    def add_cog_layer(
        self,
        url,
        attribution="",
        bands=None,
        titiler_endpoint="https://titiler.xyz",
        cog_args={},
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            attribution (str, optional): The attribution to use. Defaults to ''.
            bands (list, optional): A list of bands to use for the layer. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale,
                color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3].
                apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **cog_args)
        tile_options = {
            "url": tile_url,
            "attribution": attribution,
        }
        tile_source = WMTSTileSource(**tile_options)
        self.figure.add_tile(tile_source, **kwargs)

    def add_raster(
        self,
        source,
        band=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution="",
        layer_name="Local COG",
        **kwargs,
    ):
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try running the following code before calling this function:

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
            band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Local COG'.
        """

        tile_layer = get_local_tile_layer(
            source,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            layer_name=layer_name,
            return_client=False,
            **kwargs,
        )

        tile_options = {
            "url": tile_layer.url,
            "attribution": attribution,
        }
        tile_source = WMTSTileSource(**tile_options)
        self.figure.add_tile(tile_source, **kwargs)
