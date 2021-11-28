#!/usr/bin/env python

"""Tests for `toolbar` module."""

import unittest
from leafmap import leafmap
from leafmap.toolbar import *


class TestToolbar(unittest.TestCase):
    """Tests for `leafmap` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_change_basemap(self):
        """Check basemaps"""
        m = leafmap.Map()
        change_basemap(m)
        out_str = m.to_html()
        assert "Google Terrain" in out_str
        assert "OpenStreetMap" in out_str
        assert "FWS NWI Wetlands" in out_str
        assert "NLCD 2016 CONUS Land Cover" in out_str

    def test_main_toolbar(self):
        """Check main toolbar"""
        m = leafmap.Map()
        main_toolbar(m)
        out_str = m.to_html()
        assert "Change basemap" in out_str
        assert "Split-panel map" in out_str
        assert "Planet imagery" in out_str
        assert "Open local vector" in out_str
        assert "WhiteboxTools" in out_str
        assert "time slider" in out_str

    def test_open_data_widget(self):
        """Check open data widget"""
        m = leafmap.Map()
        open_data_widget(m)
        out_str = m.to_html()
        assert "Shapefile" in out_str
        assert "GeoJSON" in out_str
        assert "CSV" in out_str
        assert "Vector" in out_str
        assert "Raster" in out_str

    def test_save_map(self):
        """Check save map widget"""
        m = leafmap.Map()
        save_map(m)
        out_str = m.to_html()
        assert "HTML" in out_str
        assert "JPG" in out_str
        assert "PNG" in out_str

    def test_time_slider(self):
        """Check time slider widget"""
        m = leafmap.Map()
        time_slider(m)
        out_str = m.to_html()
        assert "Play the time slider" in out_str
        assert "Pause the time slider" in out_str
        assert "Close the time slider" in out_str

    def test_tool_template(self):
        """Check tool template widget"""
        m = leafmap.Map()
        tool_template(m)
        out_str = m.to_html()
        assert "Toolbar" in out_str
        assert "Checkbox" in out_str
        assert "Dropdown" in out_str
        assert "Int Slide" in out_str
        assert "Float Slider" in out_str
        assert "Color" in out_str
        assert "Textbox" in out_str
