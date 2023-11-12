"""Top-level package for leafmap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.28.1"

import os
from .report import Report


def _in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def _use_folium():
    """Whether to use the folium or ipyleaflet plotting backend."""
    if os.environ.get("USE_MKDOCS") is not None:
        return True
    else:
        return False


def view_vector(vector, zoom_to_layer=True, pickable=True, open_args={}, **kwargs):
    """Visualize a vector dataset on the map.

    Args:
        vector (Union[str, GeoDataFrame]): The file path or URL to the vector data, or a GeoDataFrame.
        zoom_to_layer (bool, optional): Flag to zoom to the added layer. Defaults to True.
        pickable (bool, optional): Flag to enable picking on the added layer. Defaults to True.
        open_args (dict, optional): Additional keyword arguments that will be passed to gpd.read_file() if vector is a file path or URL. Defaults to {}.
        **kwargs: Additional keyword arguments that will be passed to the vector layer.

    Returns:
        None
    """
    from .deckgl import Map

    m = Map()
    m.add_vector(vector, zoom_to_layer, pickable, open_args, **kwargs)
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
