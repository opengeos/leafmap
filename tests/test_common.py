#!/usr/bin/env python

"""Tests for `leafmap` package."""

import os
import unittest
from unittest.mock import MagicMock, patch

import geopandas
import pandas
import requests
from pmtiles.tile import MagicNumberNotFound

from leafmap.common import *


class TestCommon(unittest.TestCase):
    """Tests for `common` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

        self.in_csv = os.path.abspath("examples/data/world_cities.csv")
        self.in_geojson = os.path.abspath("examples/data/cable_geo.geojson")
        self.in_shp = os.path.abspath("examples/data/countries.shp")
        self.in_kml = os.path.abspath("examples/data/us_states.kml")
        self.in_kmz = os.path.abspath("examples/data/us_states.kmz")
        self.in_cog = "https://github.com/opengeos/data/releases/download/raster/Libya-2023-07-01.tif"

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

    # def test_cog_bounds(self):
    #     self.assertIsInstance(cog_bounds(self.in_cog), list)
    #     self.assertEqual(len(cog_bounds(self.in_cog)), 4)

    # def test_cog_center(self):
    #     self.assertIsInstance(cog_center(self.in_cog), tuple)
    #     self.assertEqual(len(cog_center(self.in_cog)), 2)

    @patch("os.environ", {})
    @patch("requests.get")
    def test_set_proxy_successful_request(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        set_proxy(port=8080, ip="192.168.0.1")
        self.assertEqual(os.environ["HTTP_PROXY"], "http://192.168.0.1:8080")
        self.assertEqual(os.environ["HTTPS_PROXY"], "http://192.168.0.1:8080")
        mock_get.assert_called_once_with("https://google.com")

    def _mock_localtileserver(self):
        """Return a fake ``localtileserver`` module with a mocked TileClient."""
        fake_client = MagicMock()
        fake_client.get_tile_url.return_value = (
            "http://127.0.0.1:0/api/tiles/{z}/{x}/{y}.png"
        )
        fake_module = MagicMock()
        fake_module.TileClient.return_value = fake_client
        return fake_module, fake_client

    @patch.dict(os.environ, {}, clear=True)
    def test_get_local_tile_url_enables_jupyter_loopback(self):
        """enable_jupyter_loopback is invoked when the client supports it."""
        fake_module, fake_client = self._mock_localtileserver()
        with patch.dict("sys.modules", {"localtileserver": fake_module}):
            url = get_local_tile_url("test.tif")
        fake_client.enable_jupyter_loopback.assert_called_once()
        self.assertEqual(url, "http://127.0.0.1:0/api/tiles/{z}/{x}/{y}.png")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_local_tile_url_without_loopback_support(self):
        """A client lacking enable_jupyter_loopback must not raise."""
        fake_client = MagicMock(spec=["get_tile_url"])
        fake_client.get_tile_url.return_value = "http://tile"
        fake_module = MagicMock()
        fake_module.TileClient.return_value = fake_client
        with patch.dict("sys.modules", {"localtileserver": fake_module}):
            url = get_local_tile_url("test.tif")
        self.assertFalse(hasattr(fake_client, "enable_jupyter_loopback"))
        self.assertEqual(url, "http://tile")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_local_tile_url_prefix_precedence(self):
        """The prefix kwarg takes final precedence over the env var."""
        fake_module, _ = self._mock_localtileserver()
        with patch.dict("sys.modules", {"localtileserver": fake_module}):
            get_local_tile_url("test.tif", prefix="proxy/{port}")
        self.assertEqual(os.environ["LOCALTILESERVER_CLIENT_PREFIX"], "proxy/{port}")

    @patch.dict(
        os.environ, {"LOCALTILESERVER_CLIENT_PREFIX": "keep/{port}"}, clear=True
    )
    def test_get_local_tile_url_prefix_none_ignored(self):
        """prefix=None is ignored and does not overwrite an existing env var."""
        fake_module, _ = self._mock_localtileserver()
        with patch.dict("sys.modules", {"localtileserver": fake_module}):
            get_local_tile_url("test.tif", prefix=None)
        self.assertEqual(os.environ["LOCALTILESERVER_CLIENT_PREFIX"], "keep/{port}")

    # def test_pmtile_metadata_validates_pmtiles_suffix(self):
    #     with self.assertRaises(ValueError) as cm:
    #         pmtiles_metadata("/some/path/to/pmtiles.pmtiles")
    #         assert cm.exception.message != "Input file must be a .pmtiles file."
    #     with self.assertRaises(MagicNumberNotFound):
    #         pmtiles_metadata("https://mywebsite.com/some/path/to/pmtiles.pmtiles")
    #         assert cm.exception.message != "Input file must be a .pmtiles file."
    #     with self.assertRaises(MagicNumberNotFound):
    #         pmtiles_metadata(
    #             "https://mywebsite.com/some/path/to/pmtiles.pmtiles?query=param"
    #         )
    #         assert cm.exception.message != "Input file must be a .pmtiles file."


if __name__ == "__main__":
    unittest.main()
