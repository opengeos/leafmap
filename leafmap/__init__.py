"""Top-level package for leafmap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.40.1"

import os
from .report import Report


def _in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def _in_marimo():
    """Tests if the code is being executed within a marimo notebook."""
    try:
        import marimo

        return marimo.running_in_notebook()
    except (ImportError, ModuleNotFoundError):
        # marimo not installed
        return False


def _use_folium():
    """Whether to use the folium or ipyleaflet plotting backend."""
    if os.environ.get("USE_MKDOCS") is not None:
        return True
    elif _in_marimo():
        return True
    else:
        return False


def view_vector(
    vector,
    zoom_to_layer=True,
    pickable=True,
    color_column=None,
    color_scheme="Quantiles",
    color_map=None,
    color_k=5,
    color_args={},
    open_args={},
    map_args={},
    **kwargs,
):
    """Visualize a vector dataset on the map.

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
        map_args (dict, optional): Additional keyword arguments that will be passed to lonboard.Map. Defaults to {}.
        **kwargs: Additional keyword arguments that will be passed to lonboard.Layer.from_geopandas()

    Returns:
        lonboard.Map: A lonboard Map object.
    """
    from .deckgl import Map

    m = Map(**map_args)
    m.add_vector(
        vector,
        zoom_to_layer,
        pickable,
        color_column,
        color_scheme,
        color_map,
        color_k,
        color_args,
        open_args,
        **kwargs,
    )
    return m


def view_pmtiles(
    url,
    style=None,
    name=None,
    tooltip=True,
    overlay=True,
    control=True,
    show=True,
    zoom_to_layer=True,
    map_args={},
    **kwargs,
):
    """Visualize PMTiles the map.

    Args:
        url (str): The URL of the PMTiles file.
        style (str, optional): The CSS style to apply to the layer. Defaults to None.
            See https://docs.mapbox.com/style-spec/reference/layers/ for more info.
        name (str, optional): The name of the layer. Defaults to None.
        tooltip (bool, optional): Whether to show a tooltip when hovering over the layer. Defaults to True.
        overlay (bool, optional): Whether the layer should be added as an overlay. Defaults to True.
        control (bool, optional): Whether to include the layer in the layer control. Defaults to True.
        show (bool, optional): Whether the layer should be shown initially. Defaults to True.
        zoom_to_layer (bool, optional): Whether to zoom to the layer extent. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the PMTilesLayer constructor.

    Returns:
        folium.Map: A folium Map object.
    """

    from .foliumap import Map

    m = Map(**map_args)
    m.add_pmtiles(
        url, style, name, tooltip, overlay, control, show, zoom_to_layer, **kwargs
    )
    return m


if _use_folium():
    from .foliumap import *
else:
    try:
        from .leafmap import *
    except Exception as e:
        if _in_colab_shell():
            print(
                "Please restart Colab runtime after installation if you encounter any errors when importing leafmap."
            )
        else:
            print(
                "Please restart Jupyter kernel after installation if you encounter any errors when importing leafmap."
            )
        raise Exception(e)
