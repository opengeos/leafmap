"""Compatibility helpers for ipyvuetify 1.x (Vuetify 2) and 3.x (Vuetify 3).

ipyvuetify 3 wraps Vuetify 3, which renamed several components and replaced
boolean size and style props (``small``, ``left``, ``dense``, ``dark``) with
string props (``size``, ``start``, ``density``, ``theme``). This module maps
the names and props leafmap uses so the widgets work with either version.
"""

from typing import Any, Dict

import ipyvuetify as v

try:
    VUETIFY3 = int(str(v.__version__).split(".")[0]) >= 3
except (AttributeError, ValueError):
    VUETIFY3 = hasattr(v, "ExpansionPanelTitle")

if VUETIFY3:
    ExpansionPanelTitle = v.ExpansionPanelTitle
    ExpansionPanelText = v.ExpansionPanelText
    TabsWindow = v.TabsWindow
    TabsWindowItem = v.TabsWindowItem
else:
    ExpansionPanelTitle = v.ExpansionPanelHeader
    ExpansionPanelText = v.ExpansionPanelContent
    TabsWindow = v.TabsItems
    TabsWindowItem = v.TabItem

# CSS selector of the padded wrapper inside an expansion panel's content.
EXPANSION_PANEL_WRAPPER_CLASS = (
    "v-expansion-panel-text__wrapper" if VUETIFY3 else "v-expansion-panel-content__wrap"
)


def small() -> Dict[str, Any]:
    """Returns the props for a small button or icon.

    Returns:
        ``{"size": "small"}`` for Vuetify 3, ``{"small": True}`` otherwise.
    """
    return {"size": "small"} if VUETIFY3 else {"small": True}


def icon_start() -> Dict[str, Any]:
    """Returns the props for an icon placed before a label.

    Returns:
        ``{"start": True}`` for Vuetify 3, ``{"left": True}`` otherwise.
    """
    return {"start": True} if VUETIFY3 else {"left": True}


def text_button() -> Dict[str, Any]:
    """Returns the props for a flat text button.

    In Vuetify 3 the ``text`` prop is the button label, so passing
    ``text=True`` would render the word "true".

    Returns:
        ``{"variant": "text"}`` for Vuetify 3, ``{"text": True}`` otherwise.
    """
    return {"variant": "text"} if VUETIFY3 else {"text": True}


def dense() -> Dict[str, Any]:
    """Returns the props for a compact toolbar.

    Returns:
        ``{"density": "compact"}`` for Vuetify 3, ``{"dense": True}`` otherwise.
    """
    return {"density": "compact"} if VUETIFY3 else {"dense": True}


def dark_theme(dark: bool) -> Dict[str, Any]:
    """Returns the props that switch a component to the dark theme.

    Args:
        dark (bool): Whether to use the dark theme.

    Returns:
        The theme props, or an empty dict when ``dark`` is False.
    """
    if not dark:
        return {}
    return {"theme": "dark"} if VUETIFY3 else {"dark": True}


def location_bottom() -> Dict[str, Any]:
    """Returns the props that place a snackbar at the bottom.

    Returns:
        ``{"location": "bottom"}`` for Vuetify 3, ``{"bottom": True}`` otherwise.
    """
    return {"location": "bottom"} if VUETIFY3 else {"bottom": True}


def tabs_background(color: str) -> Dict[str, Any]:
    """Returns the props that set the background color of tabs.

    Args:
        color (str): The background color.

    Returns:
        ``{"bg_color": color}`` for Vuetify 3, ``{"background_color": color}``
        otherwise.
    """
    return {"bg_color": color} if VUETIFY3 else {"background_color": color}


def icon_button() -> Dict[str, Any]:
    """Returns the props for a flat icon-only button.

    Vuetify 3 icon buttons default to the raised "elevated" variant, while
    Vuetify 2 icon buttons are flat.

    Returns:
        ``{"icon": True, "variant": "text"}`` for Vuetify 3, ``{"icon": True}``
        otherwise.
    """
    return {"icon": True, "variant": "text"} if VUETIFY3 else {"icon": True}
