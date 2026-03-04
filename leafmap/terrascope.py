"""
Terrascope STAC API integration for leafmap.

This module provides authentication and helper functions for accessing
Terrascope data services, including:
- HTTP Basic Authentication for GDAL
- STAC catalog search helpers
- GDAL authentication for streaming COGs

Example:
    >>> import leafmap.terrascope as terrascope
    >>> terrascope.login()  # Uses TERRASCOPE_USERNAME/PASSWORD env vars
    >>> items = terrascope.search_ndvi(bbox=[5.0, 51.2, 5.1, 51.3], start="2025-05-01", end="2025-06-01")
    >>> m = leafmap.Map()
    >>> m.add_raster(items[0].assets["NDVI"].href, colormap="RdYlGn")

Note:
    Authentication uses HTTP Basic Auth via GDAL environment variables.
    Credentials are set in GDAL_HTTP_USERPWD for authenticated COG streaming.
"""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any

try:
    from pystac_client import Client
except ImportError:
    Client = None


# Constants
STAC_URL = "https://stac.terrascope.be"

# Module state
_logged_in: bool = False
_stac_client: Any = None

# Logger for this module
_logger = logging.getLogger(__name__)


def _check_stac_dependencies():
    """Check that STAC dependencies are installed."""
    if Client is None:
        raise ImportError("pystac-client is required: pip install pystac-client")


def login(
    username: str | None = None,
    password: str | None = None,
    auto_refresh: bool = True,  # Kept for API compatibility, ignored
    quiet: bool = False,
) -> None:
    """
    Authenticate with Terrascope using HTTP Basic Auth.

    This sets up the necessary GDAL environment variables for
    GDAL/rasterio to authenticate with Terrascope when streaming COGs.

    Args:
        username: Terrascope username. Defaults to TERRASCOPE_USERNAME env var.
        password: Terrascope password. Defaults to TERRASCOPE_PASSWORD env var.
        auto_refresh: Kept for API compatibility, ignored.
        quiet: Suppress status messages.

    Example:
        >>> import leafmap.terrascope as terrascope
        >>> terrascope.login()
        Authenticated as: your_username
    """
    global _logged_in

    username = username or os.environ.get("TERRASCOPE_USERNAME")
    password = password or os.environ.get("TERRASCOPE_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Terrascope credentials required. Either pass username/password "
            "or set TERRASCOPE_USERNAME and TERRASCOPE_PASSWORD environment variables."
        )

    # Set GDAL environment variables for Basic Auth
    os.environ["GDAL_HTTP_AUTH"] = "BASIC"
    os.environ["GDAL_HTTP_USERPWD"] = f"{username}:{password}"
    os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"

    _logged_in = True

    if not quiet:
        print(f"Authenticated as: {username}")


def logout() -> None:
    """
    Clear GDAL authentication configuration.

    Unsets GDAL environment variables and cleans up any legacy OAuth2 files.
    """
    global _logged_in

    # Unset GDAL environment variables
    for var in [
        "GDAL_HTTP_AUTH",
        "GDAL_HTTP_USERPWD",
        "GDAL_DISABLE_READDIR_ON_OPEN",
        "GDAL_HTTP_HEADER_FILE",
    ]:
        os.environ.pop(var, None)

    # Clean up legacy OAuth2 files
    for filepath in [
        os.path.expanduser("~/.terrascope_tokens.json"),
        os.path.expanduser("~/.gdal_http_headers"),
    ]:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    _logged_in = False
    print("Logged out from Terrascope")


def cleanup_tile_servers() -> None:
    """
    Kill stale localtileserver processes.

    This is useful when switching between visualizations to avoid
    authentication errors from old tile server processes that have
    cached expired tokens.

    Note:
        This uses pkill which is Unix-specific and will terminate all
        localtileserver processes for the current user, not just those
        started by this session.
    """
    try:
        subprocess.run(["pkill", "-f", "localtileserver"], capture_output=True)
    except Exception:
        # Ignore errors: pkill may not exist on all platforms (e.g., Windows),
        # or no matching processes may be found. This cleanup is best-effort.
        pass


def get_stac_client() -> Any:
    """
    Get a pystac_client Client for the Terrascope STAC catalog.

    Returns:
        pystac_client.Client instance.
    """
    global _stac_client
    _check_stac_dependencies()
    if _stac_client is None:
        _stac_client = Client.open(STAC_URL)
    return _stac_client


def list_collections() -> list[str]:
    """
    List available collections in the Terrascope STAC catalog.

    Returns:
        List of collection IDs.
    """
    client = get_stac_client()
    return [c.id for c in client.get_collections()]


def search(
    collection: str,
    bbox: list[float] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    max_cloud_cover: float | None = None,
    limit: int | None = None,
    unique_dates: bool = True,
    **kwargs,
) -> list:
    """
    Search for items in a Terrascope STAC collection.

    Args:
        collection: Collection ID (e.g., "terrascope-s2-ndvi-v2").
        bbox: Bounding box [west, south, east, north] in WGS84.
        start: Start date (string "YYYY-MM-DD" or datetime).
        end: End date (string "YYYY-MM-DD" or datetime).
        max_cloud_cover: Maximum cloud cover percentage (0-100).
        limit: Maximum number of items to return.
        unique_dates: If True, return only one item per unique date.
        **kwargs: Additional arguments passed to pystac_client search.

    Returns:
        List of pystac Item objects, sorted by date.

    Example:
        >>> items = terrascope.search(
        ...     collection="terrascope-s2-ndvi-v2",
        ...     bbox=[5.0, 51.2, 5.1, 51.3],
        ...     start="2025-05-01",
        ...     end="2025-06-01",
        ...     max_cloud_cover=10,
        ... )
    """
    _check_stac_dependencies()
    client = get_stac_client()

    # Parse dates
    datetime_filter = None
    if start or end:
        if isinstance(start, str):
            start = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        if isinstance(end, str):
            end = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
        datetime_filter = [start, end]

    # Build filter for cloud cover
    filter_expr = None
    if max_cloud_cover is not None:
        filter_expr = {
            "op": "<=",
            "args": [{"property": "properties.eo:cloud_cover"}, max_cloud_cover],
        }

    # Execute search
    search_kwargs = {
        "collections": [collection],
        **kwargs,
    }
    if bbox:
        search_kwargs["bbox"] = bbox
    if datetime_filter:
        search_kwargs["datetime"] = datetime_filter
    if filter_expr:
        search_kwargs["filter"] = filter_expr
    if limit and not unique_dates:
        search_kwargs["limit"] = limit

    search_result = client.search(**search_kwargs)
    items = list(search_result.items())

    # Sort by date
    items.sort(key=lambda i: i.datetime)

    # Filter to unique dates if requested
    if unique_dates:
        unique_items = {}
        for item in items:
            date_str = item.datetime.strftime("%Y-%m-%d")
            if date_str not in unique_items:
                unique_items[date_str] = item
        items = list(unique_items.values())

    # Apply limit after unique filtering
    if limit and len(items) > limit:
        items = items[:limit]

    return items


def search_ndvi(
    bbox: list[float],
    start: str | datetime,
    end: str | datetime,
    max_cloud_cover: float = 10.0,
    **kwargs,
) -> list:
    """
    Search for Sentinel-2 NDVI products.

    Convenience wrapper around search() for the terrascope-s2-ndvi-v2 collection.

    Args:
        bbox: Bounding box [west, south, east, north] in WGS84.
        start: Start date (string "YYYY-MM-DD" or datetime).
        end: End date (string "YYYY-MM-DD" or datetime).
        max_cloud_cover: Maximum cloud cover percentage. Default 10%.
        **kwargs: Additional arguments passed to search().

    Returns:
        List of pystac Item objects with NDVI assets.

    Example:
        >>> items = terrascope.search_ndvi(
        ...     bbox=[5.0, 51.2, 5.1, 51.3],
        ...     start="2025-05-01",
        ...     end="2025-06-01",
        ... )
        >>> print(f"Found {len(items)} NDVI scenes")
    """
    return search(
        collection="terrascope-s2-ndvi-v2",
        bbox=bbox,
        start=start,
        end=end,
        max_cloud_cover=max_cloud_cover,
        **kwargs,
    )


def get_asset_urls(items: list, asset_key: str = "NDVI") -> list[str]:
    """
    Extract asset URLs from a list of STAC items.

    Args:
        items: List of pystac Item objects.
        asset_key: Asset key to extract (default "NDVI").

    Returns:
        List of asset URLs.
    """
    return [item.assets[asset_key].href for item in items if asset_key in item.assets]


def get_item_dates(items: list) -> list[str]:
    """
    Extract dates from a list of STAC items.

    Args:
        items: List of pystac Item objects.

    Returns:
        List of date strings in "YYYY-MM-DD" format.
    """
    return [item.datetime.strftime("%Y-%m-%d") for item in items]


def create_time_layers(
    items: list,
    asset_key: str = "NDVI",
    colormap: str = "RdYlGn",
    vmin: float = 0,
    vmax: float = 250,
) -> dict:
    """
    Create tile layers for time slider visualization.

    Args:
        items: List of pystac Item objects.
        asset_key: Asset key to use (default "NDVI").
        colormap: Colormap name (default "RdYlGn").
        vmin: Minimum value for colormap.
        vmax: Maximum value for colormap.

    Returns:
        Dictionary of {date_string: tile_layer} for use with Map.add_time_slider().

    Example:
        >>> items = terrascope.search_ndvi(bbox, start, end)
        >>> layers = terrascope.create_time_layers(items)
        >>> m = leafmap.Map()
        >>> m.add_time_slider(layers)
    """
    try:
        import leafmap
    except ImportError:
        raise ImportError("leafmap is required: pip install leafmap")

    layers = {}
    for item in items:
        if asset_key not in item.assets:
            continue
        date_str = item.datetime.strftime("%Y-%m-%d")
        tile_layer = leafmap.get_local_tile_layer(
            item.assets[asset_key].href,
            layer_name=date_str,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
        )
        layers[date_str] = tile_layer

    return layers
