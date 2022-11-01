#!/usr/bin/env python

"""Tests for `leafmap` package."""

import os
import unittest
import geopandas
from leafmap.osm import *


class TestOsm(unittest.TestCase):
    """Tests for `common` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    # def test_osm_gdf_from_geocode(self):

    #     self.assertIsInstance(
    #         osm_gdf_from_geocode("New York City"), geopandas.GeoDataFrame
    #     )

    # def test_osm_gdf_from_place(self):

    #     place = "Bunker Hill, Los Angeles, California"
    #     tags = {"building": True}
    #     self.assertIsInstance(osm_gdf_from_place(place, tags), geopandas.GeoDataFrame)

    # def test_osm_gdf_from_address(self):

    #     address = "New York City"
    #     tags = {"amenity": "bar"}
    #     dist = 1500
    #     self.assertIsInstance(
    #         osm_gdf_from_address(address, tags, dist), geopandas.GeoDataFrame
    #     )

    # def test_osm_gdf_from_point(self):

    #     self.assertIsInstance(
    #         osm_gdf_from_point(
    #             center_point=(46.7808, -96.0156),
    #             tags={"natural": "water"},
    #             dist=10000,
    #         ),
    #         geopandas.GeoDataFrame,
    #     )


if __name__ == "__main__":
    unittest.main()
