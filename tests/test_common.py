#!/usr/bin/env python

"""Tests for `leafmap` package."""

import os
import unittest
import geopandas
import pandas
from leafmap.common import *


class TestCommon(unittest.TestCase):
    """Tests for `common` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.in_csv = os.path.abspath("examples/data/world_cities.csv")
        self.in_geojson = os.path.abspath("examples/data/cable_geo.geojson")
        self.in_shp = os.path.abspath("examples/data/countries.shp")
        self.in_kml = os.path.abspath("examples/data/states.kml")
        self.in_kmz = os.path.abspath("examples/data/states.kmz")
        self.in_cog = "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif"

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_basemap_xyz_tiles(self):

        self.assertIsInstance(basemap_xyz_tiles(), dict)

    def test_csv_to_gdf(self):

        self.assertIsInstance(csv_to_gdf(self.in_csv), geopandas.GeoDataFrame)

    def test_csv_to_geojson(self):

        self.assertIsInstance(csv_to_geojson(self.in_csv), dict)

    def test_csv_to_df(self):

        self.assertIsInstance(csv_to_df(self.in_csv), pandas.DataFrame)

    def test_gdf_to_geojson(self):

        self.assertIsInstance(gdf_to_geojson(csv_to_gdf(self.in_csv)), dict)

    def test_kml_to_geojson(self):

        self.assertIsInstance(kml_to_geojson(self.in_kml), dict)

    def test_shp_to_gdf(self):

        self.assertIsInstance(shp_to_gdf(self.in_shp), geopandas.GeoDataFrame)

    def test_shp_to_geojson(self):

        self.assertIsInstance(shp_to_geojson(self.in_shp), dict)

    def test_vector_to_geojson(self):

        self.assertIsInstance(vector_to_geojson(self.in_shp), dict)

    def test_cog_bounds(self):

        self.assertIsInstance(cog_bounds(self.in_cog), list)
        self.assertEqual(len(cog_bounds(self.in_cog)), 4)

    def test_cog_center(self):

        self.assertIsInstance(cog_center(self.in_cog), tuple)
        self.assertEqual(len(cog_center(self.in_cog)), 2)


if __name__ == "__main__":
    unittest.main()
