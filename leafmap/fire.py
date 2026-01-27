"""A module for accessing NASA Fire Datasets from OpenVEDA OGC API Features.

This module provides functions to search and retrieve fire perimeter data from the
Fire Event Data Suite (FEDs) algorithm, which processes VIIRS sensor data from
Suomi NPP and NOAA-20 satellites.

Data Source: https://openveda.cloud/api/features
"""

from typing import Any, Dict, List, Optional, Union
import os

# Base API endpoint for OpenVEDA OGC API Features
OPENVEDA_ENDPOINT = os.getenv("OPENVEDA_API_ENDPOINT", "https://openveda.cloud/api/features")

# Available fire collections with descriptions
# The full collection IDs use the prefix "public.eis_fire_"
FIRE_COLLECTIONS = {
    "public.eis_fire_snapshot_perimeter_nrt": "20-day recent fire perimeters from VIIRS",
    "public.eis_fire_lf_perimeter_nrt": "Current year large fires (>5 km²)",
    "public.eis_fire_lf_perimeter_archive": "2018-2021 Western US archived large fires",
    "public.eis_fire_lf_fireline_nrt": "Active fire lines for large fires",
    "public.eis_fire_lf_newfirepix_nrt": "New fire pixels detected",
    "public.eis_fire_snapshot_fireline_nrt": "20-day recent fire lines from VIIRS",
    "public.eis_fire_snapshot_newfirepix_nrt": "20-day recent new fire pixels from VIIRS",
}

# Short aliases for convenience
FIRE_COLLECTION_ALIASES = {
    "snapshot_perimeter_nrt": "public.eis_fire_snapshot_perimeter_nrt",
    "lf_perimeter_nrt": "public.eis_fire_lf_perimeter_nrt",
    "lf_perimeter_archive": "public.eis_fire_lf_perimeter_archive",
    "lf_fireline_nrt": "public.eis_fire_lf_fireline_nrt",
    "lf_newfirepix_nrt": "public.eis_fire_lf_newfirepix_nrt",
    "snapshot_fireline_nrt": "public.eis_fire_snapshot_fireline_nrt",
    "snapshot_newfirepix_nrt": "public.eis_fire_snapshot_newfirepix_nrt",
}


def _resolve_collection(collection: str) -> str:
    """Resolve a collection name to its full API collection ID.

    Args:
        collection: Either a short alias or full collection ID.

    Returns:
        The full collection ID for the API.
    """
    return FIRE_COLLECTION_ALIASES.get(collection, collection)


# Default styling for fire perimeters
DEFAULT_FIRE_STYLE = {
    "color": "#FF4500",
    "weight": 2,
    "fillColor": "#FF6347",
    "fillOpacity": 0.5,
}


def get_fire_collections(verbose: bool = False) -> Dict[str, str]:
    """Get available fire collections from OpenVEDA.

    Args:
        verbose: If True, print collection details to console.

    Returns:
        A dictionary mapping collection IDs to their descriptions.

    Example:
        >>> collections = get_fire_collections(verbose=True)
        >>> print(collections.keys())
    """
    import requests

    url = f"{OPENVEDA_ENDPOINT}/collections"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    collections = {}

    for collection in data.get("collections", []):
        col_id = collection.get("id", "")
        title = collection.get("title", "")
        description = collection.get("description", "")

        # Filter for fire-related collections
        if any(
            keyword in col_id.lower()
            for keyword in ["fire", "perimeter", "fireline", "firepix"]
        ):
            collections[col_id] = title or description
            if verbose:
                print(f"{col_id}: {title or description}")

    # Include known fire collections even if not returned
    for col_id, desc in FIRE_COLLECTIONS.items():
        if col_id not in collections:
            collections[col_id] = desc

    return collections


def _normalize_datetime(datetime_str: str) -> str:
    """Normalize datetime string to ISO 8601 format required by the API.

    The OpenVEDA API requires full ISO 8601 datetime format with time components.
    This function converts simple date formats like "2024-07-01/2024-09-30" to
    "2024-07-01T00:00:00Z/2024-09-30T23:59:59Z".

    Args:
        datetime_str: Date/time string, either a single date or an interval.

    Returns:
        Normalized ISO 8601 datetime string.
    """
    import re

    # Pattern for simple date format (YYYY-MM-DD)
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"

    if "/" in datetime_str:
        # It's an interval
        parts = datetime_str.split("/")
        normalized_parts = []
        for i, part in enumerate(parts):
            part = part.strip()
            if re.match(date_pattern, part):
                # Add time component
                if i == 0:
                    # Start date: beginning of day
                    part = f"{part}T00:00:00Z"
                else:
                    # End date: end of day
                    part = f"{part}T23:59:59Z"
            normalized_parts.append(part)
        return "/".join(normalized_parts)
    else:
        # Single datetime
        if re.match(date_pattern, datetime_str):
            return f"{datetime_str}T00:00:00Z"
        return datetime_str


def _fetch_fire_features(
    collection_id: str,
    bbox: Optional[List[float]] = None,
    datetime: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
) -> Dict[str, Any]:
    """Fetch features from OGC API with pagination support.

    Args:
        collection_id: The collection to query (alias or full ID).
        bbox: Bounding box [west, south, east, north] in EPSG:4326.
        datetime: ISO 8601 date/time or interval (e.g., "2024-07-01/2024-07-31").
        limit: Maximum number of features to return per request.
        offset: Number of features to skip (for pagination).

    Returns:
        GeoJSON FeatureCollection dictionary.
    """
    import requests

    # Resolve collection alias to full ID
    resolved_collection = _resolve_collection(collection_id)
    url = f"{OPENVEDA_ENDPOINT}/collections/{resolved_collection}/items"

    params = {"limit": min(limit, 1000), "offset": offset}

    if bbox:
        params["bbox"] = ",".join(map(str, bbox))

    if datetime:
        # Normalize datetime to full ISO 8601 format
        params["datetime"] = _normalize_datetime(datetime)

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    return response.json()


def _apply_client_filters(
    gdf: "gpd.GeoDataFrame",
    farea_min: Optional[float] = None,
    farea_max: Optional[float] = None,
    duration_min: Optional[float] = None,
    duration_max: Optional[float] = None,
    meanfrp_min: Optional[float] = None,
    fire_id: Optional[Union[str, int]] = None,
) -> "gpd.GeoDataFrame":
    """Apply filters to a GeoDataFrame on the client side.

    Args:
        gdf: GeoDataFrame to filter.
        farea_min: Minimum fire area in km².
        farea_max: Maximum fire area in km².
        duration_min: Minimum fire duration in days.
        duration_max: Maximum fire duration in days.
        meanfrp_min: Minimum mean Fire Radiative Power.
        fire_id: Specific fire ID to filter by.

    Returns:
        Filtered GeoDataFrame.
    """
    if gdf.empty:
        return gdf

    mask = [True] * len(gdf)

    if farea_min is not None and "farea" in gdf.columns:
        mask = mask & (gdf["farea"] >= farea_min)
    if farea_max is not None and "farea" in gdf.columns:
        mask = mask & (gdf["farea"] <= farea_max)
    if duration_min is not None and "duration" in gdf.columns:
        mask = mask & (gdf["duration"] >= duration_min)
    if duration_max is not None and "duration" in gdf.columns:
        mask = mask & (gdf["duration"] <= duration_max)
    if meanfrp_min is not None and "meanfrp" in gdf.columns:
        mask = mask & (gdf["meanfrp"] >= meanfrp_min)
    if fire_id is not None and "fireid" in gdf.columns:
        # Support both string and numeric fire IDs
        mask = mask & (gdf["fireid"].astype(str) == str(fire_id))

    return gdf[mask].reset_index(drop=True)


def fire_gdf_from_bbox(
    bbox: List[float],
    collection: str = "snapshot_perimeter_nrt",
    datetime: Optional[str] = None,
    farea_min: Optional[float] = None,
    farea_max: Optional[float] = None,
    duration_min: Optional[float] = None,
    duration_max: Optional[float] = None,
    meanfrp_min: Optional[float] = None,
    limit: int = 1000,
    max_requests: int = 10,
) -> "gpd.GeoDataFrame":
    """Get fire perimeter data for a bounding box.

    Args:
        bbox: Bounding box [west, south, east, north] in EPSG:4326.
        collection: Fire collection ID. One of:
            - "snapshot_perimeter_nrt": 20-day recent fire perimeters
            - "lf_perimeter_nrt": Current year large fires (>5 km²)
            - "lf_perimeter_archive": 2018-2021 Western US archived fires
            - "lf_fireline_nrt": Active fire lines
            - "lf_newfirepix_nrt": New fire pixels
        datetime: ISO 8601 date/time or interval (e.g., "2024-07-01/2024-07-31").
        farea_min: Minimum fire area in km².
        farea_max: Maximum fire area in km².
        duration_min: Minimum fire duration in days.
        duration_max: Maximum fire duration in days.
        meanfrp_min: Minimum mean Fire Radiative Power.
        limit: Maximum total number of features to return.
        max_requests: Maximum number of API requests for pagination.

    Returns:
        A GeoDataFrame containing fire perimeter features.

    Raises:
        ImportError: If geopandas is not installed.
        ValueError: If no features are found.

    Example:
        >>> # Get fires in California for July 2024
        >>> bbox = [-124.48, 32.53, -114.13, 42.01]
        >>> gdf = fire_gdf_from_bbox(bbox, datetime="2024-07-01/2024-07-31")
        >>> print(f"Found {len(gdf)} fires")
    """
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError(
            "geopandas is required for this function. "
            "Install it with: pip install geopandas"
        )

    # Determine if we need client-side filtering
    has_filters = any(
        x is not None
        for x in [farea_min, farea_max, duration_min, duration_max, meanfrp_min]
    )

    # If filtering, fetch more data to account for filtering
    fetch_limit = limit * 3 if has_filters else limit

    all_features = []
    offset = 0
    # Use smaller page size when datetime filtering is used (API limitation)
    max_page_size = 500 if datetime else 1000
    page_limit = min(fetch_limit, max_page_size)
    requests_made = 0

    while len(all_features) < fetch_limit and requests_made < max_requests:
        data = _fetch_fire_features(
            collection_id=collection,
            bbox=bbox,
            datetime=datetime,
            limit=page_limit,
            offset=offset,
        )

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        offset += len(features)
        requests_made += 1

        # Check if we got fewer features than requested (last page)
        if len(features) < page_limit:
            break

    if not all_features:
        # Return empty GeoDataFrame with expected columns
        return gpd.GeoDataFrame(
            columns=["geometry", "fireid", "farea", "duration", "t"],
            crs="EPSG:4326",
        )

    geojson = {"type": "FeatureCollection", "features": all_features}
    gdf = gpd.GeoDataFrame.from_features(geojson, crs="EPSG:4326")

    # Apply client-side filters
    gdf = _apply_client_filters(
        gdf,
        farea_min=farea_min,
        farea_max=farea_max,
        duration_min=duration_min,
        duration_max=duration_max,
        meanfrp_min=meanfrp_min,
    )

    # Limit to requested number after filtering
    if len(gdf) > limit:
        gdf = gdf.head(limit)

    return gdf


def fire_gdf_from_place(
    place: str,
    collection: str = "snapshot_perimeter_nrt",
    datetime: Optional[str] = None,
    farea_min: Optional[float] = None,
    farea_max: Optional[float] = None,
    duration_min: Optional[float] = None,
    meanfrp_min: Optional[float] = None,
    limit: int = 1000,
    buffer_dist: Optional[float] = None,
) -> "gpd.GeoDataFrame":
    """Get fire perimeter data for a place by name.

    Uses OpenStreetMap Nominatim for geocoding the place name.

    Args:
        place: Place name to geocode (e.g., "California", "Los Angeles County").
        collection: Fire collection ID. Defaults to "snapshot_perimeter_nrt".
        datetime: ISO 8601 date/time or interval (e.g., "2024-07-01/2024-07-31").
        farea_min: Minimum fire area in km².
        farea_max: Maximum fire area in km².
        duration_min: Minimum fire duration in days.
        meanfrp_min: Minimum mean Fire Radiative Power.
        limit: Maximum number of features to return.
        buffer_dist: Distance to buffer around the place geometry, in meters.

    Returns:
        A GeoDataFrame containing fire perimeter features.

    Raises:
        ImportError: If required packages are not installed.
        ValueError: If place cannot be geocoded.

    Example:
        >>> gdf = fire_gdf_from_place("California", datetime="2024-07-01/2024-07-31")
        >>> print(f"Found {len(gdf)} fires")
    """
    try:
        import geopandas as gpd
        from shapely.geometry import box
    except ImportError:
        raise ImportError(
            "geopandas and shapely are required. "
            "Install with: pip install geopandas shapely"
        )

    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx is required for geocoding. " "Install with: pip install osmnx"
        )

    # Geocode the place name
    place_gdf = ox.geocode_to_gdf(place)
    if place_gdf.empty:
        raise ValueError(f"Could not geocode place: {place}")

    # Apply buffer if specified
    if buffer_dist is not None and buffer_dist > 0:
        # Buffer in meters requires projecting to a metric CRS
        place_gdf_proj = place_gdf.to_crs(epsg=3857)
        place_gdf_proj["geometry"] = place_gdf_proj.buffer(buffer_dist)
        place_gdf = place_gdf_proj.to_crs(epsg=4326)

    # Get bounding box from place geometry
    bounds = place_gdf.total_bounds  # [minx, miny, maxx, maxy]
    bbox = [bounds[0], bounds[1], bounds[2], bounds[3]]

    # Fetch fire data for the bounding box
    gdf = fire_gdf_from_bbox(
        bbox=bbox,
        collection=collection,
        datetime=datetime,
        farea_min=farea_min,
        farea_max=farea_max,
        duration_min=duration_min,
        meanfrp_min=meanfrp_min,
        limit=limit,
    )

    return gdf


def get_fire_by_id(
    fire_id: Union[str, int],
    collection: str = "snapshot_perimeter_nrt",
    datetime: Optional[str] = None,
) -> "gpd.GeoDataFrame":
    """Get a specific fire by its ID.

    Args:
        fire_id: The fire ID to retrieve (can be string or numeric).
        collection: Fire collection ID. Defaults to "snapshot_perimeter_nrt".
        datetime: ISO 8601 date/time or interval to filter by.

    Returns:
        A GeoDataFrame containing the fire perimeter.

    Example:
        >>> gdf = get_fire_by_id(101)
    """
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError("geopandas is required. Install with: pip install geopandas")

    # Fetch all features and filter client-side
    data = _fetch_fire_features(
        collection_id=collection,
        datetime=datetime,
        limit=1000,
    )

    features = data.get("features", [])
    if not features:
        return gpd.GeoDataFrame(
            columns=["geometry", "fireid", "farea", "duration", "t"],
            crs="EPSG:4326",
        )

    geojson = {"type": "FeatureCollection", "features": features}
    gdf = gpd.GeoDataFrame.from_features(geojson, crs="EPSG:4326")

    # Apply client-side filter for fire_id
    gdf = _apply_client_filters(gdf, fire_id=fire_id)

    return gdf


def fire_timeseries(
    fire_id: str,
    collection: str = "snapshot_perimeter_nrt",
    datetime: Optional[str] = None,
) -> "gpd.GeoDataFrame":
    """Get fire perimeter evolution over time for a specific fire.

    Returns multiple perimeters showing how the fire grew over time.

    Args:
        fire_id: The fire ID to track.
        collection: Fire collection ID. Defaults to "snapshot_perimeter_nrt".
        datetime: ISO 8601 date/time or interval to filter by.

    Returns:
        A GeoDataFrame with perimeters sorted by time.

    Example:
        >>> gdf = fire_timeseries("2024_CA_001")
        >>> print(f"Found {len(gdf)} perimeter snapshots")
    """
    gdf = get_fire_by_id(fire_id=fire_id, collection=collection, datetime=datetime)

    # Sort by time if available
    if not gdf.empty and "t" in gdf.columns:
        gdf = gdf.sort_values("t").reset_index(drop=True)

    return gdf


def search_fires(
    bbox: Optional[List[float]] = None,
    place: Optional[str] = None,
    collection: str = "snapshot_perimeter_nrt",
    datetime: Optional[str] = None,
    farea_min: Optional[float] = None,
    farea_max: Optional[float] = None,
    duration_min: Optional[float] = None,
    duration_max: Optional[float] = None,
    meanfrp_min: Optional[float] = None,
    limit: int = 1000,
) -> "gpd.GeoDataFrame":
    """Search for fires with flexible filters.

    This is a convenience function that combines bbox and place-based search.
    Either bbox or place must be provided.

    Args:
        bbox: Bounding box [west, south, east, north] in EPSG:4326.
        place: Place name to geocode (e.g., "California").
        collection: Fire collection ID. Defaults to "snapshot_perimeter_nrt".
        datetime: ISO 8601 date/time or interval (e.g., "2024-07-01/2024-07-31").
        farea_min: Minimum fire area in km².
        farea_max: Maximum fire area in km².
        duration_min: Minimum fire duration in days.
        duration_max: Maximum fire duration in days.
        meanfrp_min: Minimum mean Fire Radiative Power.
        limit: Maximum number of features to return.

    Returns:
        A GeoDataFrame containing fire perimeter features.

    Raises:
        ValueError: If neither bbox nor place is provided.

    Example:
        >>> # Search by place name
        >>> gdf = search_fires(place="California", datetime="2024-07-01/2024-07-31")

        >>> # Search by bounding box with filters
        >>> bbox = [-124.48, 32.53, -114.13, 42.01]
        >>> gdf = search_fires(bbox=bbox, farea_min=10, datetime="2024-07-01/2024-07-31")
    """
    if bbox is None and place is None:
        raise ValueError("Either bbox or place must be provided")

    if place is not None:
        return fire_gdf_from_place(
            place=place,
            collection=collection,
            datetime=datetime,
            farea_min=farea_min,
            farea_max=farea_max,
            duration_min=duration_min,
            meanfrp_min=meanfrp_min,
            limit=limit,
        )
    else:
        return fire_gdf_from_bbox(
            bbox=bbox,
            collection=collection,
            datetime=datetime,
            farea_min=farea_min,
            farea_max=farea_max,
            duration_min=duration_min,
            duration_max=duration_max,
            meanfrp_min=meanfrp_min,
            limit=limit,
        )
