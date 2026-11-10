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


def test_add_carto_api_key_appends_key():
    """CARTO URLs get the key appended with the right separator."""
    tile = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
    assert common.add_carto_api_key(tile, key="abc") == tile + "?key=abc"
    style = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json?foo=1"
    assert common.add_carto_api_key(style, key="abc") == style + "&key=abc"


def test_add_carto_api_key_leaves_other_urls(monkeypatch):
    """Non-CARTO URLs and URLs that already have a key are unchanged."""
    monkeypatch.setenv("CARTO_API_KEY", "abc")
    osm = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    assert common.add_carto_api_key(osm) == osm
    keyed = "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key=xyz"
    assert common.add_carto_api_key(keyed) == keyed


def test_add_carto_api_key_reads_env(monkeypatch):
    """The key is read from the CARTO_API_KEY environment variable."""
    monkeypatch.setenv("CARTO_API_KEY", "envkey")
    url = "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
    assert common.add_carto_api_key(url).endswith("?key=envkey")


def test_add_carto_api_key_without_key(monkeypatch):
    """Without a key the URL is returned unchanged."""
    monkeypatch.delenv("CARTO_API_KEY", raising=False)
    url = "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
    assert common.add_carto_api_key(url, warn=False) == url


def test_read_parquet_keeps_geoparquet_crs(tmp_path):
    """read_parquet keeps the CRS stored in GeoParquet metadata."""
    path = tmp_path / "projected.parquet"
    gdf = gpd.GeoDataFrame(
        {"id": [1]}, geometry=[Point(1620000, 1920000)], crs="EPSG:5070"
    )
    gdf.to_parquet(path)
    result = common.read_parquet(str(path))
    assert result.crs.to_epsg() == 5070


def test_read_parquet_custom_sql_has_no_file_crs(tmp_path):
    """A custom SQL query does not get the file's CRS assigned."""
    path = tmp_path / "projected.parquet"
    gdf = gpd.GeoDataFrame(
        {"id": [1]}, geometry=[Point(1620000, 1920000)], crs="EPSG:5070"
    )
    gdf.to_parquet(path)
    sql = f"SELECT id, ST_AsText(geometry) AS geometry FROM '{path}'"
    result = common.read_parquet(str(path), sql=sql)
    assert result.crs is None


def test_add_carto_api_key_ignores_similar_params():
    """Parameters such as apikey are not mistaken for an existing key."""
    url = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json?apikey=1"
    assert common.add_carto_api_key(url, key="abc") == url + "&key=abc"


def test_add_carto_api_key_matches_host_only():
    """The key is only added for CARTO hosts, not URLs that mention them."""
    url = "https://example.com/tiles?u=basemaps.cartocdn.com"
    assert common.add_carto_api_key(url, key="abc") == url
    url = "https://basemaps.cartocdn.com.example.com/{z}/{x}/{y}.png"
    assert common.add_carto_api_key(url, key="abc") == url


def test_ipyleaflet_add_basemap_adds_carto_key(monkeypatch):
    """ipyleaflet basemaps get the key, but other TileLayers are untouched."""
    import ipyleaflet

    from leafmap import leafmap as ipyl

    monkeypatch.setenv("CARTO_API_KEY", "abc")
    m = ipyl.Map()
    m.add_basemap("CartoDB.Positron")
    assert m.layers[-1].url.endswith("?key=abc")

    url = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
    layer = ipyleaflet.TileLayer(url=url, name="custom")
    m.add(layer)
    assert layer.url == url


def test_folium_add_basemap_does_not_mutate_shared_layer(monkeypatch):
    """folium basemaps get the key without changing the shared basemap object."""
    import leafmap.foliumap as fm

    monkeypatch.setenv("CARTO_API_KEY", "abc")
    shared = fm.basemaps["CartoDB.Positron"]
    original = shared.tiles
    m = fm.Map()
    m.add_basemap("CartoDB.Positron")
    assert shared.tiles == original
    added = [
        child
        for child in m._children.values()
        if getattr(child, "tiles", "").endswith("?key=abc")
    ]
    assert len(added) == 1
    assert added[0] is not shared
    assert added[0].get_name() != shared.get_name()
    assert added[0].options == shared.options
    assert "basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key=abc" in (
        m.get_root().render()
    )


def test_maplibre_style_url_gets_carto_key_before_fetch(monkeypatch):
    """A user-supplied CARTO style URL is keyed before it is fetched."""
    import leafmap.maplibregl as ml

    monkeypatch.setenv("CARTO_API_KEY", "abc")
    requested = []

    class Response:
        status_code = 200
        text = '{"version": 8, "sources": {}, "layers": []}'

    def fake_get(url, *args, **kwargs):
        requested.append(url)
        return Response()

    monkeypatch.setattr(ml.requests, "get", fake_get)
    ml.Map(style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json")
    assert requested[0].endswith("style.json?key=abc")


def _new_style_carto_provider():
    """Builds a CARTO provider the way xyzservices >= 2026.9.0 defines it."""
    import xyzservices

    return xyzservices.TileProvider(
        name="CartoDB.Positron",
        url="https://{s}.basemaps.cartocdn.com/{variant}/{z}/{x}/{y}{r}.png?key={apikey}",
        attribution="(C) OpenStreetMap contributors (C) CARTO",
        subdomains="abcd",
        max_zoom=20,
        variant="light_all",
        apikey="<insert your API key here>",
    )


def test_xyz_provider_url_replaces_carto_placeholder(monkeypatch):
    """A CARTO provider with the xyzservices key placeholder gets the real key."""
    monkeypatch.setenv("CARTO_API_KEY", "abc")
    provider = _new_style_carto_provider()
    assert provider.requires_token()
    normalized = common.normalize_carto_provider(provider)
    assert not normalized.requires_token()
    assert "apikey" in provider  # the original provider is not modified
    url = common.xyz_provider_url(provider)
    assert url == "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key=abc"


def test_get_xyz_dict_keeps_carto_providers():
    """CARTO basemaps stay available even when xyzservices marks them as keyed."""
    from leafmap.basemaps import get_xyz_dict

    xyz_dict = get_xyz_dict()
    assert "CartoDB.Positron" in xyz_dict
    assert "{apikey}" not in xyz_dict["CartoDB.Positron"]["url"]


def test_is_carto_provider_matches_host_only():
    """Only providers hosted on basemaps.cartocdn.com count as CARTO."""
    assert common.is_carto_provider(_new_style_carto_provider())
    assert not common.is_carto_provider(
        {"url": "https://example.com/?u=basemaps.cartocdn.com"}
    )
    assert not common.is_carto_provider({"url": None})


def test_add_carto_api_key_encodes_key():
    """Special characters in the key are URL-encoded."""
    url = "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
    assert common.add_carto_api_key(url, key="a&b c") == url + "?key=a%26b%20c"


def test_normalize_carto_provider_keeps_other_params():
    """Removing the key placeholder keeps other query parameters valid."""
    import xyzservices

    base = {
        "name": "C",
        "attribution": "a",
        "variant": "v",
        "apikey": "<insert your API key here>",
    }
    prefix = "https://basemaps.cartocdn.com/{variant}/{z}/{x}/{y}.png"
    cases = {
        "?key={apikey}&other=1": "?other=1",
        "?other=1&key={apikey}": "?other=1",
        "?a=1&key={apikey}&b=2": "?a=1&b=2",
    }
    for query, expected in cases.items():
        provider = xyzservices.TileProvider(url=prefix + query, **base)
        assert common.normalize_carto_provider(provider)["url"] == prefix + expected


def test_add_carto_api_key_respects_blank_key():
    """An existing blank key parameter is not duplicated."""
    url = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key="
    assert common.add_carto_api_key(url, key="abc") == url
