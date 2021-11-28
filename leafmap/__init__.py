"""Top-level package for leafmap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.6.0"

import os


def _in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def _use_folium():
    """Whether to use the folium or ipyleaflet plotting backend."""
    if os.environ.get("USE_FOLIUM") is not None:
        return True
    else:
        return False


if _use_folium():
    from .foliumap import *
else:
    from .leafmap import *

    if _in_colab_shell():
        from google.colab import output

        output.enable_custom_widget_manager()
