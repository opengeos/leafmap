#!/usr/bin/env python

"""Tests for `leafmap` package."""

import unittest
from leafmap import leafmap


class TestLeafmap(unittest.TestCase):
    """Tests for `leafmap` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_basemap_tiles(self):

        self.assertIsInstance(leafmap.basemap_tiles.to_dict(), dict)

    def test_linked_maps(self):
        self.assertIsInstance(leafmap.split_map(), leafmap.Map)


if __name__ == "__main__":
    unittest.main()
