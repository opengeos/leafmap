"""Tests for leafmap.Map.fit_bounds."""

import asyncio

import pytest

from leafmap import leafmap


def test_fit_bounds_rejects_malformed_bounds():
    m = leafmap.Map()
    with pytest.raises(ValueError):
        m.fit_bounds([1, 2, 3, 4])


def test_fit_bounds_cancels_previous_fit():
    async def run():
        m = leafmap.Map()
        # The map is never rendered, so each fit waits for bounds forever.
        m.fit_bounds([[0, 0], [1, 1]])
        first = m._fit_bounds_task
        m.fit_bounds([[10, 10], [11, 11]])
        second = m._fit_bounds_task
        for _ in range(3):
            await asyncio.sleep(0)
        assert first.cancelled()
        assert not second.done()
        second.cancel()
        with pytest.raises(asyncio.CancelledError):
            await second

    asyncio.run(run())
