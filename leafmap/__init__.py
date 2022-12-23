"""Top-level package for leafmap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.15.0"

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
    if os.environ.get("USE_MKDOCS") is not None:
        return True
    else:
        return False


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


from .report import Report
