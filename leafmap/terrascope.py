"""
Terrascope STAC API integration for leafmap.

This module provides authentication and helper functions for accessing
Terrascope data services, including:
- OAuth2 token management with automatic refresh
- STAC catalog search helpers
- GDAL authentication for streaming COGs

Example:
    >>> import leafmap.terrascope as terrascope
    >>> terrascope.login()  # Uses TERRASCOPE_USERNAME/PASSWORD env vars
    >>> items = terrascope.search_ndvi(bbox=[5.0, 51.2, 5.1, 51.3], start="2025-05-01", end="2025-06-01")
    >>> m = leafmap.Map()
    >>> m.add_raster(items[0].assets["NDVI"].href, colormap="RdYlGn")
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:
    requests = None

try:
    from pystac_client import Client
    from pystac import ItemCollection
except ImportError:
    Client = None
    ItemCollection = None


# Constants
TOKEN_URL = (
    "https://sso.terrascope.be/auth/realms/terrascope/protocol/openid-connect/token"
)
STAC_URL = "https://stac.terrascope.be"
TOKEN_CACHE_PATH = os.path.expanduser("~/.terrascope_tokens.json")
HEADER_FILE_PATH = os.path.expanduser("~/.gdal_http_headers")
REFRESH_INTERVAL = 240  # Refresh every 4 minutes (token expires in 5)

# Module state
_token_cache: dict = {}
_refresh_thread: threading.Thread | None = None
_refresh_stop = threading.Event()
_stac_client: Any = None


def _check_dependencies():
    """Check that required dependencies are installed."""
    if requests is None:
        raise ImportError("requests is required: pip install requests")


def _check_stac_dependencies():
    """Check that STAC dependencies are installed."""
    if Client is None:
        raise ImportError("pystac-client is required: pip install pystac-client")


def _load_cached_tokens() -> dict:
    """Load tokens from disk cache."""
    global _token_cache
    if os.path.exists(TOKEN_CACHE_PATH):
        try:
            with open(TOKEN_CACHE_PATH, "r") as f:
                _token_cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _token_cache = {}
    return _token_cache


def _save_tokens(
    access_token: str,
    refresh_token: str,
    expires_in: int,
    refresh_expires_in: int,
) -> None:
    """Save tokens to disk and memory cache."""
    global _token_cache
    now = time.time()
    _token_cache = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_expires_at": now + expires_in - 30,  # 30s buffer
        "refresh_expires_at": now + refresh_expires_in - 60,  # 60s buffer
    }
    with open(TOKEN_CACHE_PATH, "w") as f:
        json.dump(_token_cache, f)
    os.chmod(TOKEN_CACHE_PATH, 0o600)


def _update_header_file(token: str) -> None:
    """Write token to GDAL header file."""
    with open(HEADER_FILE_PATH, "w") as f:
        f.write(f"Authorization: Bearer {token}\n")
    os.chmod(HEADER_FILE_PATH, 0o600)


def _get_token_with_password(username: str, password: str) -> str:
    """Get new tokens using password grant."""
    _check_dependencies()
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "password",
            "client_id": "public",
            "username": username,
            "password": password,
        },
    )
    response.raise_for_status()
    data = response.json()
    _save_tokens(
        data["access_token"],
        data["refresh_token"],
        data["expires_in"],
        data["refresh_expires_in"],
    )
    return data["access_token"]


def _refresh_access_token(refresh_token: str) -> str:
    """Get new access token using refresh token."""
    _check_dependencies()
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": "public",
            "refresh_token": refresh_token,
        },
    )
    response.raise_for_status()
    data = response.json()
    _save_tokens(
        data["access_token"],
        data["refresh_token"],
        data["expires_in"],
        data["refresh_expires_in"],
    )
    return data["access_token"]


def _background_refresher() -> None:
    """Background thread that refreshes token periodically."""
    while not _refresh_stop.wait(REFRESH_INTERVAL):
        try:
            token = get_token()
            _update_header_file(token)
        except Exception:
            pass  # Silent fail, will retry next interval


def get_token(
    username: str | None = None,
    password: str | None = None,
) -> str:
    """
    Get a valid Terrascope access token.

    Attempts to get a token in this order:
    1. Return cached token if still valid
    2. Refresh using refresh token if available
    3. Login with username/password

    Args:
        username: Terrascope username. Defaults to TERRASCOPE_USERNAME env var.
        password: Terrascope password. Defaults to TERRASCOPE_PASSWORD env var.

    Returns:
        Valid access token string.

    Raises:
        ValueError: If credentials are not provided and not in environment.
        requests.HTTPError: If authentication fails.
    """
    global _token_cache
    _check_dependencies()

    if not _token_cache:
        _load_cached_tokens()

    now = time.time()

    # Check if access token is still valid
    if _token_cache.get("access_expires_at", 0) > now:
        return _token_cache["access_token"]

    # Try to refresh if refresh token is still valid
    if _token_cache.get("refresh_expires_at", 0) > now:
        try:
            return _refresh_access_token(_token_cache["refresh_token"])
        except Exception:
            pass  # Fall through to password auth

    # Need fresh login with credentials
    username = username or os.environ.get("TERRASCOPE_USERNAME")
    password = password or os.environ.get("TERRASCOPE_PASSWORD")
    if not username or not password:
        raise ValueError(
            "Terrascope credentials required. Either pass username/password "
            "or set TERRASCOPE_USERNAME and TERRASCOPE_PASSWORD environment variables."
        )
    return _get_token_with_password(username, password)


def login(
    username: str | None = None,
    password: str | None = None,
    auto_refresh: bool = True,
    quiet: bool = False,
) -> str:
    """
    Authenticate with Terrascope and configure GDAL for COG streaming.

    This sets up the necessary environment variables and header files for
    GDAL/rasterio to authenticate with Terrascope when streaming COGs.

    Args:
        username: Terrascope username. Defaults to TERRASCOPE_USERNAME env var.
        password: Terrascope password. Defaults to TERRASCOPE_PASSWORD env var.
        auto_refresh: Start background thread to refresh token every 4 minutes.
        quiet: Suppress status messages.

    Returns:
        Access token string.

    Example:
        >>> import leafmap.terrascope as terrascope
        >>> terrascope.login()
        Authenticated as: your_username
        Background token refresh started (every 4 min)
    """
    global _refresh_thread, _refresh_stop

    token = get_token(username, password)
    _update_header_file(token)

    os.environ["GDAL_HTTP_HEADER_FILE"] = HEADER_FILE_PATH
    os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"

    # Start background refresher if not already running
    if auto_refresh and (_refresh_thread is None or not _refresh_thread.is_alive()):
        _refresh_stop.clear()
        _refresh_thread = threading.Thread(target=_background_refresher, daemon=True)
        _refresh_thread.start()
        if not quiet:
            print("Background token refresh started (every 4 min)")

    if not quiet:
        display_username = username or os.environ.get("TERRASCOPE_USERNAME", "(cached)")
        print(f"Authenticated as: {display_username}")

    return token


def logout() -> None:
    """
    Stop background token refresh and clear cached tokens.
    """
    global _refresh_thread, _token_cache
    _refresh_stop.set()
    if _refresh_thread:
        _refresh_thread.join(timeout=1)
        _refresh_thread = None

    _token_cache = {}
    if os.path.exists(TOKEN_CACHE_PATH):
        os.remove(TOKEN_CACHE_PATH)
    if os.path.exists(HEADER_FILE_PATH):
        os.remove(HEADER_FILE_PATH)

    print("Logged out from Terrascope")


def cleanup_tile_servers() -> None:
    """
    Kill stale localtileserver processes.

    This is useful when switching between visualizations to avoid
    authentication errors from old tile server processes that have
    cached expired tokens.
    """
    try:
        subprocess.run(["pkill", "-f", "localtileserver"], capture_output=True)
    except Exception:
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
