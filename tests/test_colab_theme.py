"""Tests for the hidden control that keeps maps legible in Colab dark mode."""

import unittest
from unittest import mock

import ipyleaflet

from leafmap import leafmap


def _theme_controls(m):
    """Returns the controls of a map that carry the Colab theme stylesheet.

    Args:
        m (leafmap.Map): The map to inspect.

    Returns:
        list: The matching widget controls.
    """
    return [
        c
        for c in m.controls
        if isinstance(c, ipyleaflet.WidgetControl)
        and "leafmap-colab-theme" in getattr(c.widget, "value", "")
    ]


class TestColabTheme(unittest.TestCase):
    """Tests for the Colab theme control."""

    def test_control_added_in_colab(self):
        """A single hidden theme control is added when running in Colab."""
        with mock.patch.object(leafmap.common, "_in_colab_shell", return_value=True):
            m = leafmap.Map()
        controls = _theme_controls(m)
        self.assertEqual(len(controls), 1)
        self.assertIn(".leaflet-container", controls[0].widget.value)

    def test_no_control_outside_colab(self):
        """No theme control is added outside Colab."""
        with mock.patch.object(leafmap.common, "_in_colab_shell", return_value=False):
            m = leafmap.Map()
        self.assertEqual(_theme_controls(m), [])


if __name__ == "__main__":
    unittest.main()
