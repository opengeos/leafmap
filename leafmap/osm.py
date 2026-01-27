"""The module contains functions for downloading OpenStreetMap data. It wraps the geometries module of the osmnx package
(see https://osmnx.readthedocs.io/en/stable/osmnx.html#module-osmnx.geometries). Credits to Geoff Boeing, the developer of the osmnx package.
Most functions for downloading OpenStreetMap data require tags of map features. The list of commonly used tags can be found at
https://wiki.openstreetmap.org/wiki/Map_features
"""

import warnings
from typing import Dict, List, Optional, Tuple, Union

import geopandas as gpd

from .common import check_package

warnings.filterwarnings("ignore")


def osm_gdf_from_address(
    address: str, tags: Dict, dist: Optional[int] = 1000
) -> gpd.GeoDataFrame:
    """Create GeoDataFrame of OSM entities within some distance N, S, E, W of address.

    Args:
        address (str): The address to geocode and use as the central point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        dist (int, optional): Distance in meters. Defaults to 1000.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/#installation")

    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx package is required. Please install it using 'pip install osmnx'"
        )

    gdf = ox.features_from_address(address, tags, dist)
    return gdf


def osm_shp_from_address(
    address: str, tags: Dict, filepath: str, dist: Optional[int] = 1000
):
    """Download OSM entities within some distance N, S, E, W of address as a shapefile.

    Args:
        address (str): The address to geocode and use as the central point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        dist (int, optional): Distance in meters. Defaults to 1000.

    """
    gdf = osm_gdf_from_address(address, tags, dist)
    gdf.to_file(filepath)


def osm_geojson_from_address(
    address: str, tags: Dict, filepath: str = None, dist: Optional[int] = 1000
) -> Dict:
    """Download OSM entities within some distance N, S, E, W of address as a GeoJSON.

    Args:
        address (str): The address to geocode and use as the central point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str, optional): File path to the output GeoJSON. Defaults to None.
        dist (int, optional): Distance in meters. Defaults to 1000.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_address(address, tags, dist)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_place(
    query: Union[str, Dict, List],
    tags: Dict,
    which_result: Optional[int] = None,
    buffer_dist: Optional[float] = None,
) -> gpd.GeoDataFrame:
    """Create GeoDataFrame of OSM entities within boundaries of geocodable place(s).

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/#installation")
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx package is required. Please install it using 'pip install osmnx'"
        )

    ox.settings.use_cache = True
    ox.settings.log_console = False

    gdf = ox.features_from_place(query, tags, which_result, buffer_dist)
    return gdf


def osm_shp_from_place(
    query: Union[str, Dict, List],
    tags: Dict,
    filepath: str,
    which_result: Optional[int] = None,
    buffer_dist: Optional[float] = None,
):
    """Download OSM entities within boundaries of geocodable place(s) as a shapefile.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
    """
    gdf = osm_gdf_from_place(query, tags, which_result, buffer_dist)
    gdf.to_file(filepath)


def osm_geojson_from_place(
    query: Union[str, Dict, List],
    tags: Dict,
    filepath: str,
    which_result: Optional[int] = None,
    buffer_dist: Optional[float] = None,
) -> Dict:
    """Download OSM entities within boundaries of geocodable place(s) as a GeoJSON.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """

    gdf = osm_gdf_from_place(query, tags, which_result, buffer_dist)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_point(
    center_point: Tuple[float, float], tags: Dict, dist: Optional[int] = 1000
) -> gpd.GeoDataFrame:
    """Create GeoDataFrame of OSM entities within some distance N, S, E, W of a point.

    Args:
        center_point (tuple): The (lat, lng) center point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        dist (int, optional): Distance in meters. Defaults to 1000.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/#installation")
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx package is required. Please install it using 'pip install osmnx'"
        )

    gdf = ox.features_from_point(center_point, tags, dist)
    return gdf


def osm_shp_from_point(
    center_point: Tuple[float, float],
    tags: Dict,
    filepath: str,
    dist: Optional[int] = 1000,
):
    """Download OSM entities within some distance N, S, E, W of point as a shapefile.

    Args:
        center_point (tuple): The (lat, lng) center point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        dist (int, optional): Distance in meters. Defaults to 1000.
    """
    gdf = osm_gdf_from_point(center_point, tags, dist)
    gdf.to_file(filepath)


def osm_geojson_from_point(
    center_point: Tuple[float, float],
    tags: Dict,
    filepath: str,
    dist: Optional[int] = 1000,
) -> Dict:
    """Download OSM entities within some distance N, S, E, W of point as a GeoJSON.

    Args:
        center_point (tuple): The (lat, lng) center point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        dist (int, optional): Distance in meters. Defaults to 1000.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_point(center_point, tags, dist)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_polygon(polygon, tags: Dict) -> gpd.GeoDataFrame:
    """Create GeoDataFrame of OSM entities within boundaries of a (multi)polygon.

    Args:
        polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic boundaries to fetch geometries within
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/#installation")
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx package is required. Please install it using 'pip install osmnx'"
        )

    gdf = ox.features_from_polygon(polygon, tags)
    return gdf


def osm_shp_from_polygon(polygon, tags: Dict, filepath: str):
    """Download OSM entities within boundaries of a (multi)polygon as a shapefile.

    Args:
        polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic boundaries to fetch geometries within
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
    """
    gdf = osm_gdf_from_polygon(polygon, tags)
    gdf.to_file(filepath)


def osm_geojson_from_polygon(
    polygon, tags: Dict, filepath: Optional[str] = None
) -> Dict:
    """Download OSM entities within boundaries of a (multi)polygon as a GeoJSON.

    Args:
        polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic boundaries to fetch geometries within
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str, optional): File path to the output GeoJSON.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_polygon(polygon, tags)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_bbox(
    north: float, south: float, east: float, west: float, tags: Dict
) -> gpd.GeoDataFrame:
    """Create a GeoDataFrame of OSM entities within a N, S, E, W bounding box.

    Args:
        north (float): Northern latitude of bounding box.
        south (float): Southern latitude of bounding box.
        east (float): Eastern longitude of bounding box.
        west (float): Western longitude of bounding box.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/#installation")
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx package is required. Please install it using 'pip install osmnx'"
        )

    gdf = ox.features_from_bbox(
        north=north, south=south, east=east, west=west, tags=tags
    )
    return gdf


def osm_shp_from_bbox(
    north: float, south: float, east: float, west: float, tags: Dict, filepath: str
):
    """Download OSM entities within a N, S, E, W bounding box as a shapefile.

    Args:
        north (float): Northern latitude of bounding box.
        south (float): Southern latitude of bounding box.
        east (float): Eastern longitude of bounding box.
        west (float): Western longitude of bounding box.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
    """
    gdf = osm_gdf_from_bbox(north, south, east, west, tags)
    gdf.to_file(filepath)


def osm_geojson_from_bbox(
    north: float,
    south: float,
    east: float,
    west: float,
    tags: Dict,
    filepath: Optional[str] = None,
):
    """Download OSM entities within a N, S, E, W bounding box as a GeoJSON.

    Args:
        north (float): Northern latitude of bounding box.
        south (float): Southern latitude of bounding box.
        east (float): Eastern longitude of bounding box.
        west (float): Western longitude of bounding box.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str, optional): File path to the output GeoJSON.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_bbox(north, south, east, west, tags)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_xml(
    filepath: str, polygon=None, tags: Dict = None
) -> gpd.GeoDataFrame:
    """Create a GeoDataFrame of OSM entities in an OSM-formatted XML file.

    Args:
        filepath (str): File path to file containing OSM XML data
        polygon (shapely.geometry.Polygon, optional): Optional geographic boundary to filter objects. Defaults to None.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/#installation")
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx package is required. Please install it using 'pip install osmnx'"
        )

    gdf = ox.features_from_xml(filepath, polygon, tags)
    return gdf


def osm_gdf_from_geocode(
    query: Union[str, Dict, List],
    which_result: Optional[int] = None,
    by_osmid: Optional[bool] = False,
    buffer_dist: Optional[float] = None,
) -> gpd.GeoDataFrame:
    """Retrieves place(s) by name or ID from the Nominatim API as a GeoDataFrame.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        GeoDataFrame: A GeoPandas GeoDataFrame.
    """

    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/")

    import osmnx as ox

    gdf = ox.geocode_to_gdf(query, which_result, by_osmid, buffer_dist)
    return gdf


def osm_shp_from_geocode(
    query: Union[str, Dict, List],
    filepath: str,
    which_result: Optional[int] = None,
    by_osmid: Optional[bool] = False,
    buffer_dist: Optional[float] = None,
):
    """Download place(s) by name or ID from the Nominatim API as a shapefile.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        filepath (str): File path to the output shapefile.
        which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
    """
    gdf = osm_gdf_from_geocode(query, which_result, by_osmid, buffer_dist)
    gdf.to_file(filepath)


def osm_geojson_from_geocode(
    query: Union[str, Dict, List],
    filepath: str,
    which_result: Optional[int] = None,
    by_osmid: Optional[bool] = False,
    buffer_dist: Optional[float] = None,
):
    """Download place(s) by name or ID from the Nominatim API as a GeoJSON.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        filepath (str): File path to the output GeoJSON.
        which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_geocode(query, which_result, by_osmid, buffer_dist)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_tags_list() -> dict:
    """Open a browser to see all tags of OSM features."""
    import webbrowser

    webbrowser.open_new_tab("https://wiki.openstreetmap.org/wiki/Map_features")


# =============================================================================
# QuackOSM functions - High-performance OSM data download using DuckDB
# =============================================================================


def quackosm_gdf_from_place(
    query: str,
    tags: Optional[Dict] = None,
    osm_extract_source: Optional[str] = None,
    verbosity_mode: Optional[str] = "transient",
    **kwargs,
) -> gpd.GeoDataFrame:
    """Download OSM data for a place name using QuackOSM.

    QuackOSM is a high-performance library for reading OpenStreetMap data using DuckDB.
    It automatically downloads the required PBF files and converts them to GeoDataFrame.

    Args:
        query (str): Place name to geocode (e.g., "Vatican City", "Monaco", "Manhattan, New York").
        tags (dict, optional): Dict of tags used for filtering OSM features. The dict keys
            should be OSM tags (e.g., building, landuse, highway, etc) and the dict values
            should be either True to retrieve all items with the given tag, or a string to
            get a single tag-value combination, or a list of strings to get multiple values
            for the given tag. For example, tags = {'building': True} would return all
            building footprints in the area. tags = {'amenity': True, 'highway': 'bus_stop'}
            would return all amenities and highway=bus_stop features. Defaults to None (all features).
        osm_extract_source (str, optional): Source for OSM extracts. Options include "geofabrik",
            "osmfr", "bbbike", etc. If None, QuackOSM will automatically select the best source.
            Defaults to None.
        verbosity_mode (str, optional): Verbosity mode for progress output. Options are
            "verbose", "transient", or "silent". Defaults to "transient".
        **kwargs: Additional keyword arguments passed to QuackOSM's convert_osm_extract_to_geodataframe
            or convert_geometry_to_geodataframe functions.

    Returns:
        GeoDataFrame: A GeoDataFrame containing OSM features with 'tags' and 'geometry' columns.

    Example:
        >>> import leafmap.osm as osm
        >>> # Download all OSM features for Monaco
        >>> gdf = osm.quackosm_gdf_from_place("Monaco")
        >>> # Download only buildings
        >>> gdf = osm.quackosm_gdf_from_place("Monaco", tags={"building": True})
        >>> # Download amenities and shops
        >>> gdf = osm.quackosm_gdf_from_place("Monaco", tags={"amenity": True, "shop": True})
    """
    check_package("quackosm", "https://github.com/kraina-ai/quackosm")

    try:
        import quackosm as qosm
        from quackosm.osm_extracts import OsmExtractSource
    except ImportError:
        raise ImportError(
            "quackosm package is required. Please install it using "
            "'pip install quackosm' or 'conda install -c conda-forge quackosm'"
        )

    # Convert tags dict to QuackOSM format if provided
    tags_filter = _convert_tags_to_quackosm_filter(tags) if tags else None

    # Set verbosity mode
    kwargs["verbosity_mode"] = verbosity_mode

    # Try using osm_extract_source first if specified
    if osm_extract_source:
        source = getattr(
            OsmExtractSource, osm_extract_source.upper(), osm_extract_source
        )
        gdf = qosm.convert_osm_extract_to_geodataframe(
            query, osm_extract_source=source, tags_filter=tags_filter, **kwargs
        )
    else:
        # Try convert_osm_extract_to_geodataframe first, fall back to geometry-based approach
        try:
            gdf = qosm.convert_osm_extract_to_geodataframe(
                query, tags_filter=tags_filter, **kwargs
            )
        except Exception:
            # Fall back to geocoding + geometry-based download
            geometry = qosm.geocode_to_geometry(query)
            gdf = qosm.convert_geometry_to_geodataframe(
                geometry, tags_filter=tags_filter, **kwargs
            )

    return gdf


def quackosm_gdf_from_bbox(
    bbox: Union[Tuple[float, float, float, float], List[float]],
    tags: Optional[Dict] = None,
    verbosity_mode: Optional[str] = "transient",
    **kwargs,
) -> gpd.GeoDataFrame:
    """Download OSM data for a bounding box using QuackOSM.

    QuackOSM is a high-performance library for reading OpenStreetMap data using DuckDB.
    It automatically downloads the required PBF files and converts them to GeoDataFrame.

    Args:
        bbox (tuple or list): Bounding box as (west, south, east, north) or
            (minx, miny, maxx, maxy) in WGS84 coordinates.
        tags (dict, optional): Dict of tags used for filtering OSM features. The dict keys
            should be OSM tags (e.g., building, landuse, highway, etc) and the dict values
            should be either True to retrieve all items with the given tag, or a string to
            get a single tag-value combination, or a list of strings to get multiple values
            for the given tag. Defaults to None (all features).
        verbosity_mode (str, optional): Verbosity mode for progress output. Options are
            "verbose", "transient", or "silent". Defaults to "transient".
        **kwargs: Additional keyword arguments passed to QuackOSM's convert_geometry_to_geodataframe.

    Returns:
        GeoDataFrame: A GeoDataFrame containing OSM features with 'tags' and 'geometry' columns.

    Example:
        >>> import leafmap.osm as osm
        >>> # Download all OSM features in a bounding box (Monaco)
        >>> bbox = (7.409, 43.724, 7.439, 43.752)  # west, south, east, north
        >>> gdf = osm.quackosm_gdf_from_bbox(bbox)
        >>> # Download only roads
        >>> gdf = osm.quackosm_gdf_from_bbox(bbox, tags={"highway": True})
    """
    check_package("quackosm", "https://github.com/kraina-ai/quackosm")

    try:
        import quackosm as qosm
        from shapely.geometry import box
    except ImportError:
        raise ImportError(
            "quackosm package is required. Please install it using "
            "'pip install quackosm' or 'conda install -c conda-forge quackosm'"
        )

    # Create geometry from bbox (west, south, east, north)
    west, south, east, north = bbox
    geometry = box(west, south, east, north)

    # Convert tags dict to QuackOSM format if provided
    tags_filter = _convert_tags_to_quackosm_filter(tags) if tags else None

    # Set verbosity mode
    kwargs["verbosity_mode"] = verbosity_mode

    gdf = qosm.convert_geometry_to_geodataframe(
        geometry, tags_filter=tags_filter, **kwargs
    )

    return gdf


def quackosm_gdf_from_geometry(
    geometry,
    tags: Optional[Dict] = None,
    verbosity_mode: Optional[str] = "transient",
    **kwargs,
) -> gpd.GeoDataFrame:
    """Download OSM data for a geometry using QuackOSM.

    QuackOSM is a high-performance library for reading OpenStreetMap data using DuckDB.
    It automatically downloads the required PBF files and converts them to GeoDataFrame.

    Args:
        geometry: A Shapely geometry (Polygon, MultiPolygon), WKT string, GeoJSON dict,
            or a GeoDataFrame. The geometry defines the area of interest.
        tags (dict, optional): Dict of tags used for filtering OSM features. The dict keys
            should be OSM tags (e.g., building, landuse, highway, etc) and the dict values
            should be either True to retrieve all items with the given tag, or a string to
            get a single tag-value combination, or a list of strings to get multiple values
            for the given tag. Defaults to None (all features).
        verbosity_mode (str, optional): Verbosity mode for progress output. Options are
            "verbose", "transient", or "silent". Defaults to "transient".
        **kwargs: Additional keyword arguments passed to QuackOSM's convert_geometry_to_geodataframe.

    Returns:
        GeoDataFrame: A GeoDataFrame containing OSM features with 'tags' and 'geometry' columns.

    Example:
        >>> import leafmap.osm as osm
        >>> from shapely.geometry import box
        >>> # Download OSM features for a custom geometry
        >>> geometry = box(7.41, 43.73, 7.43, 43.75)  # Monaco area
        >>> gdf = osm.quackosm_gdf_from_geometry(geometry)
        >>> # Download only water features
        >>> gdf = osm.quackosm_gdf_from_geometry(geometry, tags={"natural": "water"})
    """
    check_package("quackosm", "https://github.com/kraina-ai/quackosm")

    try:
        import quackosm as qosm
        from shapely import wkt
        from shapely.geometry import shape
    except ImportError:
        raise ImportError(
            "quackosm package is required. Please install it using "
            "'pip install quackosm' or 'conda install -c conda-forge quackosm'"
        )

    # Convert various input types to Shapely geometry
    if isinstance(geometry, str):
        # Assume WKT string
        geometry = wkt.loads(geometry)
    elif isinstance(geometry, dict):
        # Assume GeoJSON dict
        geometry = shape(geometry)
    elif isinstance(geometry, gpd.GeoDataFrame):
        # Get the union of all geometries in the GeoDataFrame
        geometry = geometry.geometry.unary_union

    # Convert tags dict to QuackOSM format if provided
    tags_filter = _convert_tags_to_quackosm_filter(tags) if tags else None

    # Set verbosity mode
    kwargs["verbosity_mode"] = verbosity_mode

    gdf = qosm.convert_geometry_to_geodataframe(
        geometry, tags_filter=tags_filter, **kwargs
    )

    return gdf


def quackosm_gdf_from_pbf(
    pbf_path: str,
    tags: Optional[Dict] = None,
    geometry=None,
    verbosity_mode: Optional[str] = "transient",
    **kwargs,
) -> gpd.GeoDataFrame:
    """Load OSM data from a local PBF file using QuackOSM.

    QuackOSM is a high-performance library for reading OpenStreetMap data using DuckDB.
    This function reads a local PBF file and converts it to a GeoDataFrame.

    Args:
        pbf_path (str): Path to the local PBF file.
        tags (dict, optional): Dict of tags used for filtering OSM features. The dict keys
            should be OSM tags (e.g., building, landuse, highway, etc) and the dict values
            should be either True to retrieve all items with the given tag, or a string to
            get a single tag-value combination, or a list of strings to get multiple values
            for the given tag. Defaults to None (all features).
        geometry: Optional Shapely geometry to clip the data to. Defaults to None.
        verbosity_mode (str, optional): Verbosity mode for progress output. Options are
            "verbose", "transient", or "silent". Defaults to "transient".
        **kwargs: Additional keyword arguments passed to QuackOSM's convert_pbf_to_geodataframe.

    Returns:
        GeoDataFrame: A GeoDataFrame containing OSM features with 'tags' and 'geometry' columns.

    Example:
        >>> import leafmap.osm as osm
        >>> # Load OSM data from a PBF file
        >>> gdf = osm.quackosm_gdf_from_pbf("monaco.osm.pbf")
        >>> # Load only buildings
        >>> gdf = osm.quackosm_gdf_from_pbf("monaco.osm.pbf", tags={"building": True})
    """
    check_package("quackosm", "https://github.com/kraina-ai/quackosm")

    try:
        import quackosm as qosm
    except ImportError:
        raise ImportError(
            "quackosm package is required. Please install it using "
            "'pip install quackosm' or 'conda install -c conda-forge quackosm'"
        )

    # Convert tags dict to QuackOSM format if provided
    tags_filter = _convert_tags_to_quackosm_filter(tags) if tags else None

    # Set verbosity mode
    kwargs["verbosity_mode"] = verbosity_mode

    # Add geometry filter if provided
    if geometry is not None:
        kwargs["geometry_filter"] = geometry

    gdf = qosm.convert_pbf_to_geodataframe(pbf_path, tags_filter=tags_filter, **kwargs)

    return gdf


def _convert_tags_to_quackosm_filter(tags: Dict) -> Dict:
    """Convert osmnx-style tags dict to QuackOSM filter format.

    QuackOSM uses a similar but slightly different format for tag filtering.
    This function converts the osmnx-style dict to QuackOSM format.

    Args:
        tags (dict): Dict with OSM tags as keys and True, string, or list of strings as values.

    Returns:
        dict: Tags filter in QuackOSM format.
    """
    if tags is None:
        return None

    # QuackOSM expects the same format as osmnx:
    # {key: True} - match any value for the key
    # {key: value} - match specific value
    # {key: [value1, value2]} - match any of the values
    quackosm_filter = {}

    for key, value in tags.items():
        if value is True:
            # Match any value for this key
            quackosm_filter[key] = True
        elif isinstance(value, str):
            # Match specific value
            quackosm_filter[key] = value
        elif isinstance(value, list):
            # Match any of these values
            quackosm_filter[key] = value
        else:
            quackosm_filter[key] = value

    return quackosm_filter


def quackosm_to_parquet(
    source: Union[str, Tuple, gpd.GeoDataFrame],
    output_path: str,
    tags: Optional[Dict] = None,
    verbosity_mode: Optional[str] = "transient",
    **kwargs,
) -> str:
    """Download OSM data and save to GeoParquet format using QuackOSM.

    QuackOSM can efficiently save OSM data directly to GeoParquet format,
    which is optimized for cloud storage and analytical workflows.

    Args:
        source: The data source. Can be:
            - A place name string (e.g., "Monaco")
            - A bounding box tuple (west, south, east, north)
            - A Shapely geometry
            - A GeoDataFrame
        output_path (str): Path to save the output GeoParquet file.
        tags (dict, optional): Dict of tags used for filtering OSM features. Defaults to None.
        verbosity_mode (str, optional): Verbosity mode for progress output. Defaults to "transient".
        **kwargs: Additional keyword arguments passed to QuackOSM functions.

    Returns:
        str: Path to the saved GeoParquet file.

    Example:
        >>> import leafmap.osm as osm
        >>> # Save Monaco buildings to GeoParquet
        >>> path = osm.quackosm_to_parquet("Monaco", "monaco_buildings.parquet", tags={"building": True})
    """
    check_package("quackosm", "https://github.com/kraina-ai/quackosm")

    try:
        import quackosm as qosm
        from shapely.geometry import box
    except ImportError:
        raise ImportError(
            "quackosm package is required. Please install it using "
            "'pip install quackosm' or 'conda install -c conda-forge quackosm'"
        )

    # Convert tags dict to QuackOSM format if provided
    tags_filter = _convert_tags_to_quackosm_filter(tags) if tags else None

    # Set verbosity mode
    kwargs["verbosity_mode"] = verbosity_mode

    # Determine source type and convert
    if isinstance(source, str):
        # Place name - try extract first, then geometry
        try:
            parquet_path = qosm.convert_osm_extract_to_parquet(
                source, result_file_path=output_path, tags_filter=tags_filter, **kwargs
            )
        except Exception:
            geometry = qosm.geocode_to_geometry(source)
            parquet_path = qosm.convert_geometry_to_parquet(
                geometry,
                result_file_path=output_path,
                tags_filter=tags_filter,
                **kwargs,
            )
    elif isinstance(source, (tuple, list)) and len(source) == 4:
        # Bounding box
        west, south, east, north = source
        geometry = box(west, south, east, north)
        parquet_path = qosm.convert_geometry_to_parquet(
            geometry, result_file_path=output_path, tags_filter=tags_filter, **kwargs
        )
    elif isinstance(source, gpd.GeoDataFrame):
        # GeoDataFrame
        geometry = source.geometry.unary_union
        parquet_path = qosm.convert_geometry_to_parquet(
            geometry, result_file_path=output_path, tags_filter=tags_filter, **kwargs
        )
    else:
        # Assume Shapely geometry
        parquet_path = qosm.convert_geometry_to_parquet(
            source, result_file_path=output_path, tags_filter=tags_filter, **kwargs
        )

    return str(parquet_path)
