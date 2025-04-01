"""This module provides functions to download data, including NAIP imagery and building data from Overture Maps."""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer as pc
import pystac
import requests
import rioxarray as rxr
import xarray as xr
from pystac_client import Client
from shapely.geometry import box
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_naip(
    bbox: Tuple[float, float, float, float],
    output_dir: str,
    year: Optional[int] = None,
    max_items: int = 10,
    overwrite: bool = False,
    preview: bool = False,
    **kwargs: Any,
) -> List[str]:
    """Download NAIP imagery from Planetary Computer based on a bounding box.

    This function searches for NAIP (National Agriculture Imagery Program) imagery
    from Microsoft's Planetary Computer that intersects with the specified bounding box.
    It downloads the imagery and saves it as GeoTIFF files.

    Args:
        bbox: Bounding box in the format (min_lon, min_lat, max_lon, max_lat) in WGS84 coordinates.
        output_dir: Directory to save the downloaded imagery.
        year: Specific year of NAIP imagery to download (e.g., 2020). If None, returns imagery from all available years.
        max_items: Maximum number of items to download.
        overwrite: If True, overwrite existing files with the same name.
        preview: If True, display a preview of the downloaded imagery.

    Returns:
        List of downloaded file paths.

    Raises:
        Exception: If there is an error downloading or saving the imagery.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create a geometry from the bounding box
    geometry = box(*bbox)

    # Connect to Planetary Computer STAC API
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

    # Build query for NAIP data
    search_params = {
        "collections": ["naip"],
        "intersects": geometry,
        "limit": max_items,
    }

    # Add year filter if specified
    if year:
        search_params["query"] = {"naip:year": {"eq": year}}

    for key, value in kwargs.items():
        search_params[key] = value

    # Search for NAIP imagery
    search_results = catalog.search(**search_params)
    items = list(search_results.items())

    if len(items) > max_items:
        items = items[:max_items]

    if not items:
        print("No NAIP imagery found for the specified region and parameters.")
        return []

    print(f"Found {len(items)} NAIP items.")

    # Download and save each item
    downloaded_files = []
    for i, item in enumerate(items):
        # Sign the assets (required for Planetary Computer)
        signed_item = pc.sign(item)

        # Get the RGB asset URL
        rgb_asset = signed_item.assets.get("image")
        if not rgb_asset:
            print(f"No RGB asset found for item {i+1}")
            continue

        # Use the original filename from the asset
        original_filename = os.path.basename(
            rgb_asset.href.split("?")[0]
        )  # Remove query parameters
        output_path = os.path.join(output_dir, original_filename)
        if not overwrite and os.path.exists(output_path):
            print(f"Skipping existing file: {output_path}")
            downloaded_files.append(output_path)
            continue

        print(f"Downloading item {i+1}/{len(items)}: {original_filename}")

        try:
            # Open and save the data with progress bar
            # For direct file download with progress bar
            if rgb_asset.href.startswith("http"):
                download_with_progress(rgb_asset.href, output_path)
                #
            else:
                # Fallback to direct rioxarray opening (less common case)
                data = rxr.open_rasterio(rgb_asset.href)
                data.rio.to_raster(output_path)

            downloaded_files.append(output_path)
            print(f"Successfully saved to {output_path}")

            # Optional: Display a preview (uncomment if needed)
            if preview:
                data = rxr.open_rasterio(output_path)
                preview_raster(data)

        except Exception as e:
            print(f"Error downloading item {i+1}: {str(e)}")

    return downloaded_files


def download_with_progress(url: str, output_path: str) -> None:
    """Download a file with a progress bar.

    Args:
        url: URL of the file to download.
        output_path: Path where the file will be saved.
    """
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 Kibibyte

    with (
        open(output_path, "wb") as file,
        tqdm(
            desc=os.path.basename(output_path),
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar,
    ):
        for data in response.iter_content(block_size):
            size = file.write(data)
            bar.update(size)


def preview_raster(data: Any, title: str = None) -> None:
    """Display a preview of the downloaded imagery.

    This function creates a visualization of the downloaded NAIP imagery
    by converting it to an RGB array and displaying it with matplotlib.

    Args:
        data: The raster data as a rioxarray object.
        title: The title for the preview plot.
    """
    # Convert to 8-bit RGB for display
    rgb_data = data.transpose("y", "x", "band").values[:, :, 0:3]
    rgb_data = np.where(rgb_data > 255, 255, rgb_data).astype(np.uint8)

    plt.figure(figsize=(10, 10))
    plt.imshow(rgb_data)
    if title is not None:
        plt.title(title)
    plt.axis("off")
    plt.show()


# Helper function to convert NumPy types to native Python types for JSON serialization
def json_serializable(obj: Any) -> Any:
    """Convert NumPy types to native Python types for JSON serialization.

    Args:
        obj: Any object to convert.

    Returns:
        JSON serializable version of the object.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def get_overture_latest_release(patch=True) -> str:
    """
    Retrieves the value of the 'latest' key from the Overture Maps release JSON file.

    Args:
        patch (bool): If True, returns the full version string (e.g., "2025-02-19.0").

    Returns:
        str: The value of the 'latest' key from the releases.json file.

    Raises:
        requests.RequestException: If there's an issue with the HTTP request.
        KeyError: If the 'latest' key is not found in the JSON data.
        json.JSONDecodeError: If the response cannot be parsed as JSON.
    """
    url = "https://labs.overturemaps.org/data/releases.json"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        if patch:
            latest_release = data.get("latest")
        else:
            latest_release = data.get("latest").split(".")[
                0
            ]  # Extract the version number

        if latest_release is None:
            raise KeyError("The 'latest' key was not found in the releases.json file")

        return latest_release

    except requests.RequestException as e:
        print(f"Error making the request: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        raise
    except KeyError as e:
        print(f"Key error: {e}")
        raise


def get_all_overture_types():
    """Get a list of all available Overture Maps data types.

    Returns:
        list: List of available Overture Maps data types.
    """
    from overturemaps import core

    return core.get_all_overture_types()


def download_overture_buildings(
    bbox: Tuple[float, float, float, float],
    output: str = None,
    overture_type: str = "building",
    **kwargs: Any,
) -> str:
    """Download building data from Overture Maps for a given bounding box using the overturemaps CLI tool.

    Args:
        bbox: Bounding box in the format (min_lon, min_lat, max_lon, max_lat) in WGS84 coordinates.
        output: Path to save the output file.
        overture_type: The Overture Maps data type to download (building, place, etc.).

    Returns:
        Path to the output file.
    """

    return get_overture_data(
        overture_type=overture_type, bbox=bbox, output=output, **kwargs
    )


def get_overture_data(
    overture_type: str,
    bbox: Tuple[float, float, float, float] = None,
    columns: List[str] = None,
    output: str = None,
    **kwargs: Any,
) -> "gpd.GeoDataFrame":
    """Fetches overture data and returns it as a GeoDataFrame.

    Args:
        overture_type (str): The type of overture data to fetch.It can be one of the following:
            address|building|building_part|division|division_area|division_boundary|place|
            segment|connector|infrastructure|land|land_cover|land_use|water
        bbox (Tuple[float, float, float, float], optional): The bounding box to
            filter the data. Defaults to None.
        columns (List[str], optional): The columns to include in the output.
            Defaults to None.
        output (str, optional): The file path to save the output GeoDataFrame.
            Defaults to None.

    Returns:
        gpd.GeoDataFrame: The fetched overture data as a GeoDataFrame.

    Raises:
        ImportError: If the overture package is not installed.
    """

    try:
        from overturemaps import core
    except ImportError:
        raise ImportError("The overturemaps package is required to use this function")

    gdf = core.geodataframe(overture_type, bbox=bbox)
    if columns is not None:
        gdf = gdf[columns]

    gdf.crs = "EPSG:4326"

    if output is not None:
        out_dir = os.path.dirname(os.path.abspath(output))
        os.makedirs(out_dir, exist_ok=True)
        gdf.to_file(output, **kwargs)

    return gdf


def convert_vector_format(
    input_file: str,
    output_format: str = "geojson",
    filter_expression: Optional[str] = None,
) -> str:
    """Convert the downloaded data to a different format or filter it.

    Args:
        input_file: Path to the input file.
        output_format: Format to convert to, one of "geojson", "parquet", "shapefile", "csv".
        filter_expression: Optional GeoDataFrame query expression to filter the data.

    Returns:
        Path to the converted file.
    """
    try:
        # Read the input file
        logger.info(f"Reading {input_file}")
        gdf = gpd.read_file(input_file)

        # Apply filter if specified
        if filter_expression:
            logger.info(f"Filtering data using expression: {filter_expression}")
            gdf = gdf.query(filter_expression)
            logger.info(f"After filtering: {len(gdf)} features")

        # Define output file path
        base_path = os.path.splitext(input_file)[0]

        if output_format == "geojson":
            output_file = f"{base_path}.geojson"
            logger.info(f"Converting to GeoJSON: {output_file}")
            gdf.to_file(output_file, driver="GeoJSON")
        elif output_format == "parquet":
            output_file = f"{base_path}.parquet"
            logger.info(f"Converting to Parquet: {output_file}")
            gdf.to_parquet(output_file)
        elif output_format == "shapefile":
            output_file = f"{base_path}.shp"
            logger.info(f"Converting to Shapefile: {output_file}")
            gdf.to_file(output_file)
        elif output_format == "csv":
            output_file = f"{base_path}.csv"
            logger.info(f"Converting to CSV: {output_file}")

            # For CSV, we need to convert geometry to WKT
            gdf["geometry_wkt"] = gdf.geometry.apply(lambda g: g.wkt)

            # Save to CSV with geometry as WKT
            gdf.drop(columns=["geometry"]).to_csv(output_file, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        return output_file

    except Exception as e:
        logger.error(f"Error converting data: {str(e)}")
        raise


def extract_building_stats(data: str) -> Dict[str, Any]:
    """Extract statistics from the building data.

    Args:
        data: Path to the GeoJSON file or GeoDataFrame containing building data.

    Returns:
        Dictionary with statistics.
    """
    try:
        # Read the GeoJSON file

        if isinstance(data, gpd.GeoDataFrame):
            gdf = data
        else:

            gdf = gpd.read_file(data)

        # Calculate statistics
        bbox = gdf.total_bounds.tolist()
        # Convert numpy values to Python native types
        bbox = [float(x) for x in bbox]

        stats = {
            "total_buildings": int(len(gdf)),
            "has_height": (
                int(gdf["height"].notna().sum()) if "height" in gdf.columns else 0
            ),
            "has_name": (
                int(gdf["names.common.value"].notna().sum())
                if "names.common.value" in gdf.columns
                else 0
            ),
            "bbox": bbox,
        }

        return stats

    except Exception as e:
        logger.error(f"Error extracting statistics: {str(e)}")
        return {"error": str(e)}


def download_pc_stac_item(
    item_url,
    bands=None,
    output_dir=None,
    show_progress=True,
    merge_bands=False,
    merged_filename=None,
    overwrite=False,
    cell_size=None,
):
    """
    Downloads a STAC item from Microsoft Planetary Computer with specified bands.

    This function fetches a STAC item by URL, signs the assets using Planetary Computer
    credentials, and downloads the specified bands with a progress bar. Can optionally
    merge bands into a single multi-band GeoTIFF.

    Args:
        item_url (str): The URL of the STAC item to download.
        bands (list, optional): List of specific bands to download (e.g., ['B01', 'B02']).
                               If None, all available bands will be downloaded.
        output_dir (str, optional): Directory to save downloaded bands. If None,
                                   bands are returned as xarray DataArrays.
        show_progress (bool, optional): Whether to display a progress bar. Default is True.
        merge_bands (bool, optional): Whether to merge downloaded bands into a single
                                     multi-band GeoTIFF file. Default is False.
        merged_filename (str, optional): Filename for the merged bands. If None and
                                        merge_bands is True, uses "{item_id}_merged.tif".
        overwrite (bool, optional): Whether to overwrite existing files. Default is False.
        cell_size (float, optional): Resolution in meters for the merged output. If None,
                                    uses the resolution of the first band.

    Returns:
        dict: Dictionary mapping band names to their corresponding xarray DataArrays
              or file paths if output_dir is provided. If merge_bands is True, also
              includes a 'merged' key with the path to the merged file.

    Raises:
        ValueError: If the item cannot be retrieved or a requested band is not available.
    """
    from rasterio.enums import Resampling

    # Get the item ID from the URL
    item_id = item_url.split("/")[-1]
    collection = item_url.split("/collections/")[1].split("/items/")[0]

    # Connect to the Planetary Computer STAC API
    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace,
    )

    # Search for the specific item
    search = catalog.search(collections=[collection], ids=[item_id])

    # Get the first item from the search results
    items = list(search.get_items())
    if not items:
        raise ValueError(f"Item with ID {item_id} not found")

    item = items[0]

    # Determine which bands to download
    available_assets = list(item.assets.keys())

    if bands is None:
        # If no bands specified, download all band assets
        bands_to_download = [
            asset for asset in available_assets if asset.startswith("B")
        ]
    else:
        # Verify all requested bands exist
        missing_bands = [band for band in bands if band not in available_assets]
        if missing_bands:
            raise ValueError(
                f"The following bands are not available: {missing_bands}. "
                f"Available assets are: {available_assets}"
            )
        bands_to_download = bands

    # Create output directory if specified and doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = {}
    band_data_arrays = []
    resampled_arrays = []
    band_names = []  # Track band names in order

    # Set up progress bar
    progress_iter = (
        tqdm(bands_to_download, desc="Downloading bands")
        if show_progress
        else bands_to_download
    )

    # Download each requested band
    for band in progress_iter:
        if band not in item.assets:
            if show_progress and not isinstance(progress_iter, list):
                progress_iter.write(
                    f"Warning: Band {band} not found in assets, skipping."
                )
            continue

        band_url = item.assets[band].href

        if output_dir:
            file_path = os.path.join(output_dir, f"{item.id}_{band}.tif")

            # Check if file exists and skip if overwrite is False
            if os.path.exists(file_path) and not overwrite:
                if show_progress and not isinstance(progress_iter, list):
                    progress_iter.write(
                        f"File {file_path} already exists, skipping (use overwrite=True to force download)."
                    )
                # Still need to open the file to get the data for merging
                if merge_bands:
                    band_data = rxr.open_rasterio(file_path)
                    band_data_arrays.append((band, band_data))
                    band_names.append(band)
                result[band] = file_path
                continue

        if show_progress and not isinstance(progress_iter, list):
            progress_iter.set_description(f"Downloading {band}")

        band_data = rxr.open_rasterio(band_url)

        # Store the data array for potential merging later
        if merge_bands:
            band_data_arrays.append((band, band_data))
            band_names.append(band)

        if output_dir:
            file_path = os.path.join(output_dir, f"{item.id}_{band}.tif")
            band_data.rio.to_raster(file_path)
            result[band] = file_path
        else:
            result[band] = band_data

    # Merge bands if requested
    if merge_bands and output_dir:
        if merged_filename is None:
            merged_filename = f"{item.id}_merged.tif"

        merged_path = os.path.join(output_dir, merged_filename)

        # Check if merged file exists and skip if overwrite is False
        if os.path.exists(merged_path) and not overwrite:
            if show_progress:
                print(
                    f"Merged file {merged_path} already exists, skipping (use overwrite=True to force creation)."
                )
            result["merged"] = merged_path
        else:
            if show_progress:
                print("Resampling and merging bands...")

            # Determine target cell size if not provided
            if cell_size is None and band_data_arrays:
                # Use the resolution of the first band (usually 10m for B02, B03, B04, B08)
                # Get the affine transform (containing resolution info)
                first_band_data = band_data_arrays[0][1]
                # Extract resolution from transform
                cell_size = abs(first_band_data.rio.transform()[0])
                if show_progress:
                    print(f"Using detected resolution: {cell_size}m")
            elif cell_size is None:
                # Default to 10m if no bands are available
                cell_size = 10
                if show_progress:
                    print(f"Using default resolution: {cell_size}m")

            # Process bands in memory-efficient way
            for i, (band_name, data_array) in enumerate(band_data_arrays):
                if show_progress:
                    print(f"Processing band: {band_name}")

                # Get current resolution
                current_res = abs(data_array.rio.transform()[0])

                # Resample if needed
                if (
                    abs(current_res - cell_size) > 0.01
                ):  # Small tolerance for floating point comparison
                    if show_progress:
                        print(
                            f"Resampling {band_name} from {current_res}m to {cell_size}m"
                        )

                    # Use bilinear for downsampling (higher to lower resolution)
                    # Use nearest for upsampling (lower to higher resolution)
                    resampling_method = (
                        Resampling.bilinear
                        if current_res < cell_size
                        else Resampling.nearest
                    )

                    resampled = data_array.rio.reproject(
                        data_array.rio.crs,
                        resolution=(cell_size, cell_size),
                        resampling=resampling_method,
                    )
                    resampled_arrays.append(resampled)
                else:
                    resampled_arrays.append(data_array)

            if show_progress:
                print("Stacking bands...")

            # Concatenate all resampled arrays along the band dimension
            try:
                merged_data = xr.concat(resampled_arrays, dim="band")

                if show_progress:
                    print(f"Writing merged data to {merged_path}...")

                # Add description metadata
                merged_data.attrs["description"] = (
                    f"Multi-band image containing {', '.join(band_names)}"
                )

                # Create a dictionary mapping band indices to band names
                band_descriptions = {}
                for i, name in enumerate(band_names):
                    band_descriptions[i + 1] = name

                # Write the merged data to file with band descriptions
                merged_data.rio.to_raster(
                    merged_path,
                    tags={"BAND_NAMES": ",".join(band_names)},
                    descriptions=band_names,
                )

                result["merged"] = merged_path

                if show_progress:
                    print(f"Merged bands saved to: {merged_path}")
                    print(f"Band order in merged file: {', '.join(band_names)}")
            except Exception as e:
                if show_progress:
                    print(f"Error during merging: {str(e)}")
                    print(f"Error details: {type(e).__name__}: {str(e)}")
                raise

    return result


def pc_collection_list(
    endpoint="https://planetarycomputer.microsoft.com/api/stac/v1",
    detailed=False,
    filter_by=None,
    sort_by="id",
):
    """
    Retrieves and displays the list of available collections from Planetary Computer.

    This function connects to the Planetary Computer STAC API and retrieves the
    list of all available collections, with options to filter and sort the results.

    Args:
        endpoint (str, optional): STAC API endpoint URL.
            Defaults to "https://planetarycomputer.microsoft.com/api/stac/v1".
        detailed (bool, optional): Whether to return detailed information for each
            collection. If False, returns only basic info. Defaults to False.
        filter_by (dict, optional): Dictionary of field:value pairs to filter
            collections. For example, {"license": "CC-BY-4.0"}. Defaults to None.
        sort_by (str, optional): Field to sort the collections by.
            Defaults to "id".

    Returns:
        pandas.DataFrame: DataFrame containing collection information.

    Raises:
        ConnectionError: If there's an issue connecting to the API.
    """
    # Initialize the STAC client
    try:
        catalog = Client.open(endpoint)
    except Exception as e:
        raise ConnectionError(f"Failed to connect to STAC API at {endpoint}: {str(e)}")

    # Get all collections
    try:
        collections = list(catalog.get_collections())
    except Exception as e:
        raise Exception(f"Error retrieving collections: {str(e)}")

    # Basic info to extract from all collections
    collection_info = []

    # Extract information based on detail level
    for collection in collections:
        # Basic information always included
        info = {
            "id": collection.id,
            "title": collection.title or "No title",
            "description": (
                collection.description[:100] + "..."
                if collection.description and len(collection.description) > 100
                else collection.description
            ),
        }

        # Add detailed information if requested
        if detailed:
            # Get temporal extent if available
            temporal_extent = "Unknown"
            if collection.extent and collection.extent.temporal:
                interval = (
                    collection.extent.temporal.intervals[0]
                    if collection.extent.temporal.intervals
                    else None
                )
                if interval:
                    start = interval[0] or "Unknown Start"
                    end = interval[1] or "Present"
                    if isinstance(start, datetime.datetime):
                        start = start.strftime("%Y-%m-%d")
                    if isinstance(end, datetime.datetime):
                        end = end.strftime("%Y-%m-%d")
                    temporal_extent = f"{start} to {end}"

            # Add additional details
            info.update(
                {
                    "license": collection.license or "Unknown",
                    "keywords": (
                        ", ".join(collection.keywords)
                        if collection.keywords
                        else "None"
                    ),
                    "temporal_extent": temporal_extent,
                    "asset_count": len(collection.assets) if collection.assets else 0,
                    "providers": (
                        ", ".join([p.name for p in collection.providers])
                        if collection.providers
                        else "Unknown"
                    ),
                }
            )

            # Add spatial extent if available
            if collection.extent and collection.extent.spatial:
                info["bbox"] = (
                    str(collection.extent.spatial.bboxes[0])
                    if collection.extent.spatial.bboxes
                    else "Unknown"
                )

        collection_info.append(info)

    # Convert to DataFrame for easier filtering and sorting
    df = pd.DataFrame(collection_info)

    # Apply filtering if specified
    if filter_by:
        for field, value in filter_by.items():
            if field in df.columns:
                df = df[df[field].astype(str).str.contains(value, case=False, na=False)]

    # Apply sorting
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by)

    print(f"Retrieved {len(df)} collections from Planetary Computer")

    # # Print a nicely formatted table
    # if not df.empty:
    #     print("\nAvailable collections:")
    #     print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

    return df


def pc_stac_search(
    collection,
    bbox=None,
    time_range=None,
    query=None,
    limit=10,
    max_items=None,
    endpoint="https://planetarycomputer.microsoft.com/api/stac/v1",
):
    """
    Search for STAC items in the Planetary Computer catalog.

    This function queries the Planetary Computer STAC API to find items matching
    the specified criteria, including collection, bounding box, time range, and
    additional query parameters.

    Args:
        collection (str): The STAC collection ID to search within.
        bbox (list, optional): Bounding box coordinates [west, south, east, north].
            Defaults to None.
        time_range (str or tuple, optional): Time range as a string "start/end" or
            a tuple of (start, end) datetime objects. Defaults to None.
        query (dict, optional): Additional query parameters for filtering.
            Defaults to None.
        limit (int, optional): Number of items to return per page. Defaults to 10.
        max_items (int, optional): Maximum total number of items to return.
            Defaults to None (returns all matching items).
        endpoint (str, optional): STAC API endpoint URL.
            Defaults to "https://planetarycomputer.microsoft.com/api/stac/v1".

    Returns:
        list: List of STAC Item objects matching the search criteria.

    Raises:
        ValueError: If invalid parameters are provided.
        ConnectionError: If there's an issue connecting to the API.
    """
    import datetime

    # Initialize the STAC client
    try:
        catalog = Client.open(endpoint)
    except Exception as e:
        raise ConnectionError(f"Failed to connect to STAC API at {endpoint}: {str(e)}")

    # Process time_range if provided
    if time_range:
        if isinstance(time_range, tuple) and len(time_range) == 2:
            # Convert datetime objects to ISO format strings
            start, end = time_range
            if isinstance(start, datetime.datetime):
                start = start.isoformat()
            if isinstance(end, datetime.datetime):
                end = end.isoformat()
            time_str = f"{start}/{end}"
        elif isinstance(time_range, str):
            time_str = time_range
        else:
            raise ValueError(
                "time_range must be a 'start/end' string or tuple of (start, end)"
            )
    else:
        time_str = None

    # Create the search object
    search = catalog.search(
        collections=[collection], bbox=bbox, datetime=time_str, query=query, limit=limit
    )

    # Collect the items
    items = []
    try:
        # Use max_items if specified, otherwise get all items
        if max_items:
            items_gen = search.get_items()
            for item in items_gen:
                items.append(item)
                if len(items) >= max_items:
                    break
        else:
            items = list(search.get_items())
    except Exception as e:
        raise Exception(f"Error retrieving search results: {str(e)}")

    print(f"Found {len(items)} items matching search criteria")

    return items


def pc_stac_download(
    items,
    output_dir=".",
    assets=None,
    max_workers=4,
    skip_existing=True,
):
    """
    Download assets from STAC items retrieved from the Planetary Computer.

    This function downloads specified assets from a list of STAC items to the
    specified output directory. It supports parallel downloads and can skip
    already downloaded files.

    Args:
        items (list or pystac.Item): STAC Item object or list of STAC Item objects.
        output_dir (str, optional): Directory where assets will be saved.
            Defaults to current directory.
        assets (list, optional): List of asset keys to download. If None,
            downloads all available assets. Defaults to None.
        max_workers (int, optional): Maximum number of concurrent download threads.
            Defaults to 4.
        skip_existing (bool, optional): Skip download if the file already exists.
            Defaults to True.
        sign_urls (bool, optional): Whether to sign URLs for authenticated access.
            Defaults to True.

    Returns:
        dict: Dictionary mapping STAC item IDs to dictionaries of their downloaded
            assets {asset_key: file_path}.

    Raises:
        TypeError: If items is not a STAC Item or list of STAC Items.
        IOError: If there's an error writing the downloaded assets to disk.
    """

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Handle single item case
    if isinstance(items, pystac.Item) or isinstance(items, str):
        items = [items]
    elif not isinstance(items, list):
        raise TypeError("items must be a STAC Item or list of STAC Items")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Function to download a single asset
    def download_asset(item, asset_key, asset):
        item = pc.sign(item)
        item_id = item.id

        # Get the asset URL and sign it if needed
        asset_url = item.assets[asset_key].href
        # Determine output filename
        if asset.media_type:
            # Use appropriate file extension based on media type
            if "tiff" in asset.media_type or "geotiff" in asset.media_type:
                ext = ".tif"
            elif "jpeg" in asset.media_type:
                ext = ".jpg"
            elif "png" in asset.media_type:
                ext = ".png"
            elif "json" in asset.media_type:
                ext = ".json"
            else:
                # Default extension based on the original URL
                ext = os.path.splitext(asset_url.split("?")[0])[1] or ".data"
        else:
            # Default extension based on the original URL
            ext = os.path.splitext(asset_url.split("?")[0])[1] or ".data"

        output_path = os.path.join(output_dir, f"{item_id}_{asset_key}{ext}")

        # Skip if file exists and skip_existing is True
        if skip_existing and os.path.exists(output_path):
            print(f"Skipping existing asset: {asset_key} -> {output_path}")
            return asset_key, output_path

        try:
            # Download the asset with progress bar
            with requests.get(asset_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                with open(output_path, "wb") as f:
                    with tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=f"Downloading {item_id}_{asset_key}",
                        ncols=100,
                    ) as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))

            return asset_key, output_path
        except Exception as e:
            print(f"Error downloading {asset_key} for item {item_id}: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)  # Clean up partial download
            return asset_key, None

    # Process all items and their assets
    results = {}

    for item in items:
        item_assets = {}
        if isinstance(item, str):
            item = pystac.Item.from_file(item)
        item_id = item.id
        print(f"Processing STAC item: {item_id}")

        # Determine which assets to download
        if assets:
            assets_to_download = {k: v for k, v in item.assets.items() if k in assets}
            if not assets_to_download:
                print(
                    f"Warning: None of the specified asset keys {assets} found in item {item_id}"
                )
                print(f"Available asset keys: {list(item.assets.keys())}")
                continue
        else:
            assets_to_download = item.assets

        # Download assets concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_asset = {
                executor.submit(download_asset, item, asset_key, asset): (
                    asset_key,
                    asset,
                )
                for asset_key, asset in assets_to_download.items()
            }

            # Process results as they complete
            for future in as_completed(future_to_asset):
                asset_key, asset = future_to_asset[future]
                try:
                    key, path = future.result()
                    if path:
                        item_assets[key] = path
                except Exception as e:
                    print(
                        f"Error processing asset {asset_key} for item {item_id}: {str(e)}"
                    )

        results[item_id] = item_assets

    # Count total downloaded assets
    total_assets = sum(len(assets) for assets in results.values())
    print(f"\nDownloaded {total_assets} assets for {len(results)} items")

    return results


def pc_item_asset_list(item):
    """
    Retrieve the list of asset keys from a STAC item in the Planetary Computer catalog.

    Args:
        item (str): The URL of the STAC item.

    Returns:
        list: A list of asset keys available in the signed STAC item.
    """
    if isinstance(item, str):
        item = pystac.Item.from_file(item)

    if not isinstance(item, pystac.Item):
        raise ValueError("item_url must be a string (URL) or a pystac.Item object")

    return list(item.assets.keys())


def sign_pc_item(item, asset=None, return_href=True):
    """
    Sign a STAC item using Planetary Computer credentials.

    Args:
        item (pystac.Item or str): The STAC item to sign, or its URL.

    Returns:
        pystac.Item: The signed STAC item with authenticated asset URLs.
    """
    if isinstance(item, str):
        item = pystac.Item.from_file(item)

    if not isinstance(item, pystac.Item):
        raise ValueError("item must be a string (URL) or a pystac.Item object")

    signed_item = pc.sign_inplace(item)
    if return_href and asset is not None:
        asset_url = signed_item.assets[asset].href
        return asset_url
    else:
        return signed_item


def read_pc_item_asset(item, asset, output=None, as_cog=True, **kwargs):
    """
    Read a specific asset from a STAC item in the Planetary Computer catalog.

    Args:
        item (str): The URL of the STAC item.
        asset (str): The key of the asset to read.
        output (str, optional): If specified, the path to save the asset as a raster file.
        as_cog (bool, optional): If True, save the asset as a Cloud Optimized GeoTIFF (COG).

    Returns:
        xarray.DataArray: The data array for the specified asset.
    """
    if isinstance(item, str):
        item = pystac.Item.from_file(item)

    if not isinstance(item, pystac.Item):
        raise ValueError("item must be a string (URL) or a pystac.Item object")

    signed_item = pc.sign(item)

    if asset not in signed_item.assets:
        raise ValueError(
            f"Asset '{asset}' not found in item '{item.id}'. It has available assets: {list(signed_item.assets.keys())}"
        )

    asset_url = signed_item.assets[asset].href
    ds = rxr.open_rasterio(asset_url)

    if as_cog:
        kwargs["driver"] = "COG"  # Ensure the output is a Cloud Optimized GeoTIFF

    if output:
        print(f"Saving asset '{asset}' to {output}...")
        ds.rio.to_raster(output, **kwargs)
        print(f"Asset '{asset}' saved successfully.")
    return ds
