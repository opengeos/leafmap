import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import rasterio
import rioxarray
import xarray as xr
from rasterio.transform import Affine, from_origin

from leafmap.common import plot_raster

NODATA = -9999.0


@pytest.fixture(autouse=True)
def _enable_plot_raster(monkeypatch):
    # CI sets USE_MKDOCS, which makes plot_raster return without plotting.
    monkeypatch.delenv("USE_MKDOCS", raising=False)


# British National Grid (EPSG:27700) origin and pixel size used by the tests.
ORIGIN_X = 530000
ORIGIN_Y = 180000
RES = 10


def _make_dataarray(size=10):
    """Build a small in-memory EPSG:27700 raster with realistic coordinates."""
    data = xr.DataArray(
        np.arange(size * size, dtype=np.float32).reshape(size, size),
        dims=("y", "x"),
        coords={
            "y": ORIGIN_Y - RES * (np.arange(size) + 0.5),
            "x": ORIGIN_X + RES * (np.arange(size) + 0.5),
        },
    )
    data = data.rio.write_crs("EPSG:27700")
    data = data.rio.write_transform(from_origin(ORIGIN_X, ORIGIN_Y, RES, RES))
    return data


def _write_dem(path):
    """Write a small EPSG:27700 GeoTIFF with nodata cells and one outlier.

    Returns the array of valid (non-nodata) values.
    """
    height, width = 20, 30
    data = np.arange(height * width, dtype="float32").reshape(height, width) / 10.0
    data[0, :5] = NODATA  # nodata cells that must not affect the color stretch
    data[10, 10] = 5000.0  # outlier that the percentile stretch should ignore

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:27700",
        transform=from_origin(ORIGIN_X, ORIGIN_Y, RES, RES),
        nodata=NODATA,
    ) as dst:
        dst.write(data, 1)

    return data[data != NODATA]


def test_plot_raster_defaults_to_native_projection():
    """Plotting without a target CRS should preserve the source extent."""
    data = _make_dataarray()

    try:
        plot_raster(data)
        axes = plt.gcf().axes[0]

        np.testing.assert_allclose(axes.get_xlim(), (ORIGIN_X, ORIGIN_X + 10 * RES))
        np.testing.assert_allclose(
            sorted(axes.get_ylim()), (ORIGIN_Y - 10 * RES, ORIGIN_Y)
        )
    finally:
        plt.close("all")


def test_plot_raster_supports_explicit_reprojection():
    """An explicitly requested target CRS should still be applied."""
    data = _make_dataarray()
    left, bottom, right, top = data.rio.reproject("EPSG:3857").rio.bounds()

    try:
        plot_raster(data, proj="EPSG:3857")
        axes = plt.gcf().axes[0]

        np.testing.assert_allclose(axes.get_xlim(), (left, right), rtol=1e-6, atol=1e-3)
        np.testing.assert_allclose(
            sorted(axes.get_ylim()), (bottom, top), rtol=1e-6, atol=1e-3
        )
    finally:
        plt.close("all")


def test_plot_raster_file_keeps_native_extent_and_aspect(tmp_path):
    """A file in EPSG:27700 should plot in its own grid with equal aspect."""
    path = tmp_path / "dem.tif"
    _write_dem(path)

    try:
        plot_raster(str(path), band=0)
        axes = plt.gcf().axes[0]

        np.testing.assert_allclose(axes.get_xlim(), (ORIGIN_X, ORIGIN_X + 30 * RES))
        np.testing.assert_allclose(
            sorted(axes.get_ylim()), (ORIGIN_Y - 20 * RES, ORIGIN_Y)
        )
        assert axes.get_aspect() in (1, 1.0, "equal")
    finally:
        plt.close("all")


def test_plot_raster_masks_nodata_and_uses_percentile_stretch(tmp_path):
    """Nodata must not affect the color limits, and the stretch is 2-98 percentile."""
    path = tmp_path / "dem.tif"
    valid = _write_dem(path)

    try:
        plot_raster(str(path), band=0)
        mesh = plt.gcf().axes[0].collections[0]
        vmin, vmax = mesh.get_clim()

        np.testing.assert_allclose(
            (vmin, vmax), np.percentile(valid, [2, 98]), rtol=1e-4
        )
        assert vmin >= 0  # would be NODATA (-9999) if nodata were not masked
        assert vmax < 5000  # the outlier is ignored by the percentile stretch
    finally:
        plt.close("all")


def test_plot_raster_explicit_vmin_vmax_take_priority(tmp_path):
    """Explicit vmin/vmax must override the automatic stretch."""
    path = tmp_path / "dem.tif"
    _write_dem(path)

    try:
        plot_raster(str(path), band=0, vmin=0, vmax=150)
        mesh = plt.gcf().axes[0].collections[0]

        assert mesh.get_clim() == (0, 150)
    finally:
        plt.close("all")


def test_plot_raster_does_not_mutate_open_kwargs(tmp_path):
    """The caller's open_kwargs dict must be left untouched."""
    path = tmp_path / "dem.tif"
    _write_dem(path)
    open_kwargs = {}

    try:
        plot_raster(str(path), band=0, open_kwargs=open_kwargs)

        assert open_kwargs == {}
    finally:
        plt.close("all")


def test_plot_raster_rotated_raster_uses_map_coordinates(tmp_path):
    """A rotated raster should be plotted in map coordinates, not pixel indices."""
    path = tmp_path / "rotated.tif"
    height, width = 20, 30
    data = np.arange(height * width, dtype="float32").reshape(height, width)

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:27700",
        transform=Affine(RES, 3, ORIGIN_X, 3, -RES, ORIGIN_Y),
    ) as dst:
        dst.write(data, 1)

    try:
        plot_raster(str(path), band=0)
        axes = plt.gcf().axes[0]
        xmin, xmax = axes.get_xlim()
        ymin, ymax = sorted(axes.get_ylim())

        # Pixel indices would give limits of roughly 0-30; map coordinates
        # stay close to the raster origin.
        assert ORIGIN_X - 100 < xmin < xmax < ORIGIN_X + 1000
        assert ORIGIN_Y - 1000 < ymin < ymax < ORIGIN_Y + 1000
    finally:
        plt.close("all")
