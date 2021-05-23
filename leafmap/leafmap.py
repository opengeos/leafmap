"""Main module."""

import os
import ipyleaflet


class Map(ipyleaflet.Map):
    """The Map class inherits ipyleaflet.Map. The arguments you can pass to the Map can be found at https://ipyleaflet.readthedocs.io/en/latest/api_reference/map.html. By default, the Map will add Google Maps as the basemap. Set add_google_map = False to use OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    def __init__(self, **kwargs):

        if "center" not in kwargs:
            kwargs["center"] = [40, -100]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 4

        if "scroll_wheel_zoom" not in kwargs:
            kwargs["scroll_wheel_zoom"] = True

        if "attribution_control" not in kwargs:
            kwargs["attribution_control"] = False

        super().__init__(**kwargs)

        if "height" not in kwargs:
            self.layout.height = "600px"
        else:
            self.layout.height = kwargs["height"]

        if "layers_control" not in kwargs:
            kwargs["layers_control"] = True
        if kwargs["layers_control"]:
            self.add_control(ipyleaflet.LayersControl(position="topright"))

        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True
        if kwargs["fullscreen_control"]:
            self.add_control(ipyleaflet.FullScreenControl())

        if "draw_control" not in kwargs:
            kwargs["draw_control"] = True
        if kwargs["draw_control"]:
            draw_control = ipyleaflet.DrawControl(
                marker={"shapeOptions": {"color": "#3388ff"}},
                rectangle={"shapeOptions": {"color": "#3388ff"}},
                circle={"shapeOptions": {"color": "#3388ff"}},
                circlemarker={},
                edit=True,
                remove=True,
                position="topleft",
            )
            self.add_control(draw_control)

        if "measure_control" not in kwargs:
            kwargs["measure_control"] = True
        if kwargs["measure_control"]:
            self.add_control(ipyleaflet.MeasureControl(position="topleft"))

        if "scale_control" not in kwargs:
            kwargs["scale_control"] = True
        if kwargs["scale_control"]:
            self.add_control(ipyleaflet.ScaleControl(position="bottomleft"))

        if "google_map" not in kwargs:
            layer = ipyleaflet.TileLayer(
                url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                attribution="Google",
                name="Google Maps",
            )
            self.add_layer(layer)
        else:
            if kwargs["google_map"].upper() == "ROADMAP":
                layer = ipyleaflet.TileLayer(
                    url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Maps",
                )
            elif kwargs["google_map"].upper() == "HYBRID":
                layer = ipyleaflet.TileLayer(
                    url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Satellite",
                )
            elif kwargs["google_map"].upper() == "TERRAIN":
                layer = ipyleaflet.TileLayer(
                    url="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Terrain",
                )
            elif kwargs["google_map"].upper() == "SATELLITE":
                layer = ipyleaflet.TileLayer(
                    url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Satellite",
                )
            else:
                layer = ipyleaflet.TileLayer(
                    url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                    attribution="Google",
                    name="Google Maps",
                )
            self.add_layer(layer)

    def add_geojson(self, in_geojson, style=None, layer_name="Untitled"):

        import json

        if isinstance(in_geojson, str):

            if not os.path.exists(in_geojson):
                raise FileNotFoundError("The provided GeoJSON file could not be found.")

            with open(in_geojson) as f:
                data = json.load(f)

        elif isinstance(in_geojson, dict):
            data = in_geojson

        else:
            raise TypeError("The input geojson must be a type of str or dict.")

        if style is None:
            style = {
                "stroke": True,
                "color": "#000000",
                "weight": 2,
                "opacity": 1,
                "fill": True,
                "fillColor": "#000000",
                "fillOpacity": 0.4,
            }

        geo_json = ipyleaflet.GeoJSON(data=data, style=style, name=layer_name)
        self.add_layer(geo_json)

    def add_shapefile(self, in_shp, style=None, layer_name="Untitled"):

        geojson = shp_to_geojson(in_shp)
        self.add_geojson(geojson, style=style, layer_name=layer_name)


def shp_to_geojson(in_shp, out_geojson=None):

    import json
    import shapefile

    in_shp = os.path.abspath(in_shp)

    if not os.path.exists(in_shp):
        raise FileNotFoundError("The provided shapefile could not be found.")

    sf = shapefile.Reader(in_shp)
    geojson = sf.__geo_interface__

    if out_geojson is None:
        return geojson
    else:
        out_geojson = os.path.abspath(out_geojson)
        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        with open(out_geojson, "w") as f:
            f.write(json.dumps(geojson))
