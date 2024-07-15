#!/usr/bin/env python

"""Tests for `colormaps` module."""

import unittest
import leafmap.colormaps as cm
import ipyleaflet
import ipywidgets as widgets
from unittest.mock import patch
from leafmap import leafmap


class TestColormaps(unittest.TestCase):
    """Tests for `colormaps` module."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # self.__palette_dict: dict = {
        #     "dem": ["#000000", "#FFFFFF"],
        #     "ndvi": ["#00FF00", "#FF0000"],
        #     "ndwi": ["#0000FF", "#00FFFF"],
        # }

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_get_palette(self):
        """Test the get_palette function."""
        # test the function with a valid palette
        palette = cm.get_palette("terrain", n_class=8)
        self.assertEqual(len(palette), 8)
        # self.assertEqual(palette[0], "333399")
        # self.assertEqual(palette[1], "0294fa")
        # self.assertEqual(palette[2], "24d36d")

        # test the function with an invalid palette
        # with self.assertRaises(ValueError):
        #     cm.get_palette("not_a_palette")

    def test_invalid_colormap(self):
        with self.assertRaises(KeyError):
            cm.get_palette("invd", 5, True)

    def test_colormap_with_n_class(self):
        res = cm.get_palette("viridis", 5, False)
        self.assertEqual(len(res), 5)
        for color in res:
            self.assertFalse(color.startswith("#"))

    # @patch("matplotlib.pyplot.show")
    # def test_get_colorbar(self, mock_show):
    #     """Test the get_colorbar function."""
    #     m = leafmap.Map()
    #     colors = cm.get_palette("terrain", n_class=8)
    #     output = widgets.Output()
    #     with output:
    #         output.outputs = ()
    #         cm.get_colorbar(colors, discrete=False)
    #         cm.get_colorbar(colors, discrete=True)
    #     control = ipyleaflet.WidgetControl(widget=output, position="bottomright")
    #     m.add(control)
    #     out_str = m.to_html()
    #     assert "image/png" in out_str

    # @patch("matplotlib.pyplot.show")
    # def test_list_colormaps(self, mock_show):
    #     """Test the get_colorbar function."""
    #     # test the function with a valid colorbar
    #     m = leafmap.Map()
    #     output = widgets.Output()
    #     with output:
    #         output.outputs = ()
    #         cm.list_colormaps()
    #     control = ipyleaflet.WidgetControl(widget=output, position="bottomright")
    #     m.add(control)
    #     out_str = m.to_html()
    #     assert "image/png" in out_str

    # @patch("matplotlib.pyplot.show")
    # def test_plot_colormap(self, mock_show):
    #     """Test the get_colorbar function."""
    #     # test the function with a valid colorbar
    #     m = leafmap.Map()
    #     output = widgets.Output()
    #     with output:
    #         output.outputs = ()
    #         cm.plot_colormap(
    #             cmap="gray",
    #             colors=None,
    #             discrete=False,
    #             label=None,
    #             width=8.0,
    #             height=0.4,
    #             orientation="horizontal",
    #             vmin=0,
    #             vmax=1.0,
    #             axis_off=False,
    #             show_name=False,
    #             font_size=12,
    #         )
    #     control = ipyleaflet.WidgetControl(widget=output, position="bottomright")
    #     m.add(control)
    #     out_str = m.to_html()
    #     assert "image/png" in out_str
    #     m.remove_control(control)

    #     with output:
    #         output.outputs = ()
    #         cm.plot_colormap(
    #             colors=[
    #                 "333399",
    #                 "0294fa",
    #                 "24d36d",
    #                 "b6f08a",
    #                 "dbd085",
    #                 "92735e",
    #                 "b6a29d",
    #                 "ffffff",
    #             ],
    #             discrete=False,
    #             label="Elevation",
    #             width=8.0,
    #             height=0.4,
    #             orientation="horizontal",
    #             vmin=0,
    #             vmax=1.0,
    #             axis_off=True,
    #             show_name=True,
    #             font_size=12,
    #         )
    #     control = ipyleaflet.WidgetControl(widget=output, position="bottomright")
    #     m.add(control)
    #     out_str = m.to_html()
    #     assert "image/png" in out_str

    # @patch("matplotlib.pyplot.show")
    # def test_plot_colormaps(self, mock_show):
    #     """Test the get_colorbar function."""
    #     # test the function with a valid colorbar
    #     m = leafmap.Map()
    #     output = widgets.Output()
    #     with output:
    #         output.outputs = ()
    #         cm.plot_colormaps(width=8.0, height=0.4)
    #     control = ipyleaflet.WidgetControl(widget=output, position="bottomright")
    #     m.add(control)
    #     out_str = m.to_html()
    #     assert "image/png" in out_str
