from IPython.core.display import display, HTML

try:
    import keplergl
except ImportError:
    raise ImportError(
        "Kepler needs to be installed to use this module. See https://docs.kepler.gl/docs/keplergl-jupyter"
    )


class Map(keplergl.KeplerGl):
    """The Map class inherits keplergl.KeperGl.

    Returns:
        object: keplergl.KeperGl map object.
    """

    def __init__(self, **kwargs):

        if "center" not in kwargs:
            kwargs["center"] = [40, -100]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 2.97

        if "height" not in kwargs:
            kwargs["height"] = 600

        if "widescreen" not in kwargs:
            kwargs["widescreen"] = False

        if kwargs["widescreen"]:
            display(HTML("<style>.container { width:100% !important; }</style>"))

        config = {
            "version": "v1",
            "config": {
                "mapState": {
                    "latitude": kwargs["center"][0],
                    "longitude": kwargs["center"][1],
                    "zoom": kwargs["zoom"],
                }
            },
        }

        kwargs.pop("widescreen")
        kwargs.pop("center")
        kwargs.pop("zoom")
        # if "show_docs" not in kwargs:
        #     kwargs["show_docs"] = False

        super().__init__(**kwargs)
        self.config = config