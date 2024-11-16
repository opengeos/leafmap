import os
import pathlib
import anywidget
import traitlets
from . import common


class Map(anywidget.AnyWidget):
    """Create a Mapbox map widget."""

    _cwd = os.path.dirname(os.path.abspath(__file__))
    _esm = pathlib.Path(os.path.join(_cwd, "javascript", "mapbox.js"))
    _css = pathlib.Path(os.path.join(_cwd, "styles", "mapbox.css"))
    default_token = common.get_api_key("MAPBOX_TOKEN")
    token = traitlets.Unicode(default_token).tag(sync=True)
    center = traitlets.List([-100, 40]).tag(sync=True, o=True)
    zoom = traitlets.Float(1.2).tag(sync=True, o=True)
    bounds = traitlets.List([0, 0, 0, 0]).tag(sync=True, o=True)
    width = traitlets.Unicode("100%").tag(sync=True, o=True)
    height = traitlets.Unicode("600px").tag(sync=True, o=True)
    clicked_lnglat = traitlets.List([None, None]).tag(sync=True, o=True)
    style = traitlets.Unicode("mapbox://styles/mapbox/streets-v12").tag(sync=True)

    def set_esm(self, esm, container="map"):
        """Set esm attribute. Can be a string, a file path, or a url.
            See examples at https://docs.mapbox.com/mapbox-gl-js/example/
            Open an example and click on the 'Edit in CodePen' button.
            Then copy the code from the 'JS' tab, and assign it to the esm parameter.

        Args:
            esm (str): The esm string, file path, or url.
            container (str, optional): The container name. Defaults to 'map'.

        Raises:
            TypeError: If esm is not a string.
        """
        if isinstance(esm, str):
            if os.path.isfile(esm):
                with open(esm, "r") as f:
                    content = f.read()
            elif esm.startswith("http"):
                import urllib.request

                with urllib.request.urlopen(esm) as response:
                    content = response.read().decode("utf-8")
            else:
                content = esm

            self._esm = self._create_esm(content, container=container)

        else:
            raise TypeError("esm must be a string")

    def set_css(self, css, container="map"):
        """Set css attribute. Can be a string, a file path, or a url.
            See examples at https://docs.mapbox.com/mapbox-gl-js/example/
            Open an example and click on the 'Edit in CodePen' button.
            Then copy the code from the 'CSS' tab, and assign it to the css parameter.
        Args:
            css (str): The css string, file path, or url.

        Raises:
            TypeError: If css is not a string.
        """
        if isinstance(css, str):
            if os.path.isfile(css):
                with open(css, "r") as f:
                    content = f.read()
            elif css.startswith("http"):
                import urllib.request

                with urllib.request.urlopen(css) as response:
                    content = response.read().decode("utf-8")
            else:
                content = css

            self._css = content.replace(f"#{container}", f"#div").replace(
                f".{container}", f".div"
            )
        else:
            raise TypeError("css must be a string")

    def _create_esm(self, esm, container="map"):
        """Create esm string by replacing the container name.

        Args:
            esm (str): The esm string.
            container (str, optional): The container name. Defaults to 'map'.

        Returns:
            str: The esm string with the container name replaced.
        """
        _cwd = os.path.dirname(os.path.abspath(__file__))
        _esm = pathlib.Path(os.path.join(_cwd, "javascript", "mapbox.js"))

        with open(_esm, "r") as f:
            lines = f.readlines()

        header = []
        footer = []

        for index, line in enumerate(lines):
            if line.strip() == "// Map content":
                header = lines[: index + 1]
                break

        for index, line in enumerate(lines):
            if line.strip() == "// Footer":
                footer = lines[index:]
                break

        content = esm.replace(f"'{container}'", "div").replace(f'"{container}"', "div")
        esm = "".join(header) + content + "".join(footer)

        return esm

    def _save_esm(self, output):
        """Save esm to file

        Args:
            output (str): The output file path.
        """

        with open(output, "w") as f:
            f.write(self._esm)
