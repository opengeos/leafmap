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
            {"landcover": ["forest", "water", "forest"]},
            geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
            crs="EPSG:4326",
        )
        result, legend = common.classify(gdf, "landcover")
        self.assertEqual(len(result), 3)
        self.assertEqual(set(legend), {"forest", "water"})

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
        m = self.maplibregl.Map(style="positron")
        m.add_tile_layer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", name="T")
        m.add_tile_layer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", name="T")
        for name, info in m.layer_dict.items():
            if name.startswith("T"):
                self.assertEqual(info["layer"].id, name)

    def test_vector_tile_layer_references_source_name(self):
        """add_vector_tile must keep source_names hashable."""
        m = self.maplibregl.Map(style="positron")
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
            m = self.maplibregl.Map(style="positron")
            self.assertFalse(getattr(m, "_use_message_queue", False))
        finally:
            del os.environ["USE_MESSAGE_QUEUE"]


if __name__ == "__main__":
    unittest.main()
