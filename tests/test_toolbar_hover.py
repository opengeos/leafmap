"""Tests for the toolbar hover event that guards against flickering."""

import ipywidgets as widgets

from leafmap.toolbar import _pointer_inside, _toolbar_hover_event

RECT = {
    "boundingRectLeft": 100,
    "boundingRectRight": 200,
    "boundingRectTop": 50,
    "boundingRectBottom": 150,
}


def _event(event_type, x, y):
    """Builds a mouse event payload like the one ipyevents sends.

    Args:
        event_type (str): The DOM event type.
        x (float): The pointer's clientX.
        y (float): The pointer's clientY.

    Returns:
        dict: The event content.
    """
    return {"type": event_type, "clientX": x, "clientY": y, **RECT}


def _dispatch(event, content):
    """Feeds a message to the event as if it came from the frontend.

    Args:
        event (ipyevents.Event): The event widget.
        content (dict): The event content.
    """
    event._handle_mouse_msg(event, content, [])


def test_pointer_inside():
    assert _pointer_inside(_event("mouseleave", 150, 100))
    assert not _pointer_inside(_event("mouseleave", 250, 100))
    assert not _pointer_inside(_event("mouseleave", 150, 40))
    # Left/top edges are inside, right/bottom edges are outside.
    assert _pointer_inside(_event("mouseleave", 100, 50))
    assert not _pointer_inside(_event("mouseleave", 200, 100))
    assert not _pointer_inside(_event("mouseleave", 150, 150))
    # Events without position data are never treated as inside.
    assert not _pointer_inside({"type": "mouseleave"})


def test_spurious_mouseleave_is_ignored():
    received = []
    event = _toolbar_hover_event(widgets.VBox())
    event.on_dom_event(lambda e: received.append(e["type"]))

    _dispatch(event, _event("mouseenter", 150, 100))
    _dispatch(event, _event("mouseleave", 150, 100))  # re-render, pointer still in
    _dispatch(event, _event("mouseleave", 250, 100))  # pointer really left

    assert received == ["mouseenter", "mouseleave"]
