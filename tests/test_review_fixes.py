"""Regression tests for bugs fixed during a codebase review.

These tests run offline: they only exercise local logic, never the network.
"""

import math
import os
import tempfile
import unittest

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiLineString, Point, Polygon

from leafmap import common


class TestCommonFixes(unittest.TestCase):
    """Tests for fixes in leafmap.common."""

    def test_zoom_level_resolution_uses_radians(self):
        """Resolution must use the cosine of the latitude in radians."""
        res = common.zoom_level_resolution(10, latitude=40)
        expected = 156543.04 * math.cos(math.radians(40)) / 2**10
        self.assertAlmostEqual(res, expected, places=6)

    def test_points_from_xy_with_z_column(self):
        """The z argument is a column name, not a value."""
        df = pd.DataFrame({"x": [0.0, 1.0], "y": [0.0, 1.0], "elev": [5.0, 6.0]})
        gdf = common.points_from_xy(df, x="x", y="y", z="elev")
        self.assertTrue(gdf.geometry.has_z.all())
        self.assertEqual(gdf.geometry.iloc[1].z, 6.0)

    def test_geom_type_on_filtered_gdf(self):
        """Geometry type lookup must not depend on index label 0."""
        gdf = gpd.GeoDataFrame(
            {"a": [1, 2]}, geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:4326"
        )
        filtered = gdf[gdf["a"] == 2]
        self.assertEqual(common.gdf_geom_type(filtered), "Point")
        self.assertEqual(common.vector_geom_type(filtered), "Point")

    def test_numpy_to_image_float(self):
        """Float arrays are rescaled to uint8 before saving as PNG."""
        arr = np.random.rand(8, 8).astype(np.float32)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out.png")
            common.numpy_to_image(arr, out)
            self.assertTrue(os.path.exists(out))

    def test_classify_string_column(self):
        """Classifying a non-numeric column must not crash."""
        gdf = gpd.GeoDataFrame(
            {"landcover": pd.Series(["forest", "water", "forest"], dtype="string")},
            geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
            crs="EPSG:4326",
        )
        result, legend = common.classify(gdf, "landcover")
        self.assertEqual(len(result), 3)
        self.assertEqual(set(legend), {"forest", "water"})

    def test_classify_string_column_with_missing(self):
        """Missing values in a string column are left unclassified."""
        gdf = gpd.GeoDataFrame(
            {"lc": pd.Series(["a", None, "b"], dtype="string")},
            geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
            crs="EPSG:4326",
        )
        result, legend = common.classify(gdf, "lc")
        self.assertEqual(set(legend), {"a", "b"})
        self.assertTrue(pd.isna(result["category"].iloc[1]))

    def test_construct_bbox_returns_gdf(self):
        """construct_bbox must import geopandas itself."""
        gdf = common.construct_bbox(0, 0, 1, 1, return_gdf=True)
        self.assertIsInstance(gdf, gpd.GeoDataFrame)

    def test_get_geometry_coords_single_parts(self):
        """Single Polygon and MultiLineString geometries are supported."""
        row = pd.Series({"geometry": Polygon([(0, 0), (1, 0), (1, 1)])})
        xs = common.get_geometry_coords(row, "geometry", "x", "Polygon")
        self.assertEqual(len(xs), 4)
        row = pd.Series({"geometry": MultiLineString([[(0, 0), (1, 1)]])})
        ys = common.get_geometry_coords(row, "geometry", "y", "MultiLineString")
        self.assertEqual(ys, [0.0, 1.0])

    def test_get_geometry_coords_keeps_all_line_parts(self):
        """All MultiLineString parts are kept, separated by NaN."""
        row = pd.Series(
            {"geometry": MultiLineString([[(0, 0), (1, 1)], [(5, 5), (6, 6)]])}
        )
        xs = common.get_geometry_coords(row, "geometry", "x", "MultiLineString")
        self.assertEqual(len(xs), 5)
        self.assertTrue(math.isnan(xs[2]))
        self.assertEqual(xs[3:], [5.0, 6.0])

    def test_array_to_image_png_keeps_integer_inference(self):
        """PNG output cannot store floats, so float input is still narrowed."""
        import rasterio

        arr = np.linspace(10, 20, 16, dtype=np.float32).reshape(4, 4)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "img.png")
            common.array_to_image(
                arr,
                output=out,
                cellsize=1,
                crs="EPSG:4326",
                transform=(1, 0, 0, 0, -1, 0),
            )
            with rasterio.open(out) as src:
                self.assertEqual(src.dtypes[0], "uint8")

    def test_array_to_image_keeps_float(self):
        """Float data in [-1, 1] must not be truncated to integers."""
        import rasterio

        arr = np.linspace(-0.9, 0.9, 16, dtype=np.float32).reshape(4, 4)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "ndvi.tif")
            common.array_to_image(
                arr,
                output=out,
                cellsize=1,
                crs="EPSG:4326",
                transform=(1, 0, 0, 0, -1, 0),
            )
            with rasterio.open(out) as src:
                data = src.read(1)
        self.assertTrue(np.issubdtype(data.dtype, np.floating))
        self.assertAlmostEqual(float(data.min()), -0.9, places=5)

    def test_float_output_dtype(self):
        """Float data stays float for GeoTIFF only, and not with a colormap."""
        arr = np.zeros((2, 2), dtype=np.float32)
        self.assertEqual(common._float_output_dtype(arr, "COG"), np.float32)
        self.assertIsNone(common._float_output_dtype(arr, "PNG"))
        self.assertIsNone(common._float_output_dtype(arr, "GTiff", {1: (0, 0, 0)}))

    def test_buffer_gdf_near_pole(self):
        """Buffering works beyond UTM coverage."""
        from leafmap.osm import _buffer_gdf

        gdf = gpd.GeoDataFrame(geometry=[Point(0, 89.5)], crs="EPSG:4326")
        self.assertEqual(_buffer_gdf(gdf, 1000).geometry.iloc[0].geom_type, "Polygon")


class TestLeafletFixes(unittest.TestCase):
    """Tests for fixes in the ipyleaflet backend."""

    def test_basemap_alias_resolution(self):
        """Google-style aliases resolve to a basemap layer."""
        from leafmap.leafmap import get_basemap

        layer = get_basemap("TERRAIN")
        self.assertTrue(layer.url.startswith("http"))

    def test_add_popup_keeps_unnamed_layers(self):
        """Adding an unnamed layer must not remove another unnamed layer."""
        import ipyleaflet

        import leafmap.leafmap as leafmap

        m = leafmap.Map()
        marker = ipyleaflet.Marker(location=(0, 0))
        m.add(marker)
        m.add(ipyleaflet.Popup(location=(0, 0)))
        self.assertIn(marker, m.layers)

    def test_add_gdf_non_ns_datetime(self):
        """Datetime columns of any unit are converted to strings."""
        import leafmap.leafmap as leafmap

        gdf = gpd.GeoDataFrame(
            {"t": pd.to_datetime(["2024-01-01"]).astype("datetime64[ms]")},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        m = leafmap.Map()
        m.add_gdf(gdf, layer_name="pts", zoom_to_layer=False)
        layer = m.find_layer("pts")
        self.assertIsInstance(layer.data["features"][0]["properties"]["t"], str)
        # The caller's GeoDataFrame keeps its datetime dtype.
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(gdf["t"]))


class TestFoliumFixes(unittest.TestCase):
    """Tests for fixes in the folium backend."""

    def test_keyed_colormap_palette(self):
        """Keyed colormaps map each pixel value to its own color."""
        from leafmap.foliumap import _keyed_colormap_to_palette

        palette, value_range = _keyed_colormap_to_palette(
            {"11": "#466b9f", "13": (255, 0, 0, 128)}
        )
        self.assertEqual(value_range, [11.0, 13.0])
        self.assertEqual(palette[0], "#466b9f")
        self.assertIsNone(palette[1])
        self.assertTrue(palette[2].startswith("rgba(255, 0, 0, 0.5"))

    def test_keyed_colormap_layer_does_not_clamp(self):
        """Keyed colormaps render out-of-range values as nodata."""
        import leafmap.foliumap as foliumap

        layer = foliumap.GeoTIFFLayer(
            url="https://example.com/a.tif",
            palette=["#000000", "#ffffff"],
            value_range=[11, 12],
            clamp_palette=False,
        )
        self.assertFalse(layer.clamp_palette)


# A minimal inline style so the MapLibre tests never fetch a remote style.
EMPTY_STYLE = {"version": 8, "sources": {}, "layers": []}


class TestOverlayFixes(unittest.TestCase):
    """Tests for image overlay helpers."""

    def test_float_image_to_png(self):
        """Float (mode F) images are converted to a PNG-compatible mode."""
        from io import BytesIO

        from PIL import Image

        from leafmap.leafmap import _to_png_compatible

        image = Image.fromarray(np.linspace(0, 1, 16, dtype=np.float32).reshape(4, 4))
        self.assertEqual(image.mode, "F")
        converted = _to_png_compatible(image)
        self.assertEqual(converted.mode, "L")
        converted.save(BytesIO(), "PNG")


class TestMapLibreFixes(unittest.TestCase):
    """Tests for fixes in the MapLibre backend."""

    def setUp(self):
        """Skip when the MapLibre extras are unavailable."""
        try:
            import leafmap.maplibregl as maplibregl
        except ImportError:
            self.skipTest("maplibre is not installed")
        self.maplibregl = maplibregl

    def test_duplicate_layer_names_get_unique_ids(self):
        """A de-duplicated layer name is also used as the MapLibre layer id."""
        m = self.maplibregl.Map(style=EMPTY_STYLE)
        url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        m.add_tile_layer(url, name="T")
        m.add_tile_layer(url, name="T", visible=False, opacity=0.25)
        for name, info in m.layer_dict.items():
            if name.startswith("T"):
                self.assertEqual(info["layer"].id, name)
        # Settings apply to the new layer, not the original one.
        self.assertTrue(m.layer_dict["T"]["visible"])
        self.assertFalse(m.layer_dict["T_1"]["visible"])
        self.assertEqual(m.layer_dict["T_1"]["opacity"], 0.25)

    def test_vector_tile_layer_references_source_name(self):
        """add_vector_tile must keep source_names hashable."""
        m = self.maplibregl.Map(style=EMPTY_STYLE)
        m.add_vector_tile(
            "https://example.com/{z}/{x}/{y}.pbf",
            layer_id="vt",
            source_layer="layer",
        )
        self.assertIsInstance(m.source_names, (list, set))

    def test_message_queue_env_false(self):
        """USE_MESSAGE_QUEUE=False must not enable the message queue."""
        os.environ["USE_MESSAGE_QUEUE"] = "False"
        try:
            m = self.maplibregl.Map(style=EMPTY_STYLE)
            self.assertFalse(getattr(m, "_use_message_queue", False))
        finally:
            del os.environ["USE_MESSAGE_QUEUE"]


if __name__ == "__main__":
    unittest.main()
