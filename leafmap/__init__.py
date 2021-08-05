"""Top-level package for leafmap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.4.1"

import os


def __in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def __use_folium():
    """Whether to use the folium or ipyleaflet plotting backend."""
    if os.environ.get("USE_FOLIUM") is not None:
        return True
    else:
        return False


if __in_colab_shell() or __use_folium():
    from .foliumap import *
else:
    from .leafmap import *
