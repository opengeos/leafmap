"""Regression tests for fixes to Overture URLs, date filtering, and read_vector."""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from leafmap import common


def test_get_overture_pmtiles_url_adds_patch_number():
    """A release without a patch number gets '.0' appended."""
    url = common.get_overture_pmtiles_url("places", "2026-10-21")
    assert url == "https://tiles.overturemaps.org/2026-10-21.0/places.pmtiles"


def test_get_overture_pmtiles_url_keeps_full_release():
    """A full release version is used as is."""
    url = common.get_overture_pmtiles_url("buildings", "2026-09-23.1")
    assert url == "https://tiles.overturemaps.org/2026-09-23.1/buildings.pmtiles"


def test_filter_date_drops_temp_column():
    """filter_date works with pandas versions that reject columns= plus axis=."""
    df = pd.DataFrame({"date": ["2023-01-01", "2023-06-01", "2024-01-01"]})
    result = common.filter_date(df, start_date="2023-03-01", end_date="2023-12-31")
    assert list(result["date"]) == ["2023-06-01"]
    assert "date_temp" not in result.columns


def test_read_vector_gpkg_without_layer(tmp_path):
    """read_vector picks the first layer of a GeoPackage without fiona."""
    path = tmp_path / "points.gpkg"
    gdf = gpd.GeoDataFrame({"id": [1, 2]}, geometry=[Point(0, 0), Point(1, 1)])
    gdf.to_file(path, layer="pts", driver="GPKG")
    result = common.read_vector(str(path))
    assert len(result) == 2
