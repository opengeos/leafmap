import os
import pystac
import requests
from typing import Optional, Dict, List, Callable, Tuple, Union
from pandas import DataFrame


class TitilerEndpoint:
    """This class contains the methods for the titiler endpoint."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        name: Optional[str] = "stac",
        TileMatrixSetId: Optional[str] = "WebMercatorQuad",
    ):
        """Initialize the TitilerEndpoint object.

        Args:
            endpoint (str, optional): The endpoint of the titiler server. Defaults to "https://titiler.xyz".
            name (str, optional): The name to be used in the file path. Defaults to "stac".
            TileMatrixSetId (str, optional): The TileMatrixSetId to be used in the file path. Defaults to "WebMercatorQuad".
        """
        self.endpoint = endpoint
        self.name = name
        self.TileMatrixSetId = TileMatrixSetId

    def url_for_stac_item(self):
        return f"{self.endpoint}/{self.name}/{self.TileMatrixSetId}/tilejson.json"

    def url_for_stac_assets(self):
        return f"{self.endpoint}/{self.name}/assets"

    def url_for_stac_bounds(self):
        return f"{self.endpoint}/{self.name}/bounds"

    def url_for_stac_info(self):
        return f"{self.endpoint}/{self.name}/info"

    def url_for_stac_info_geojson(self):
        return f"{self.endpoint}/{self.name}/info.geojson"

    def url_for_stac_statistics(self):
        return f"{self.endpoint}/{self.name}/statistics"

    def url_for_stac_pixel_value(self, lon, lat):
        return f"{self.endpoint}/{self.name}/point/{lon},{lat}"

    def url_for_stac_wmts(self):
        return (
            f"{self.endpoint}/{self.name}/{self.TileMatrixSetId}/WMTSCapabilities.xml"
        )


class PlanetaryComputerEndpoint(TitilerEndpoint):
    """This class contains the methods for the Microsoft Planetary Computer endpoint."""

    def __init__(
        self,
        endpoint: Optional[str] = "https://planetarycomputer.microsoft.com/api/data/v1",
        name: Optional[str] = "item",
        TileMatrixSetId: Optional[str] = "WebMercatorQuad",
    ):
        """Initialize the PlanetaryComputerEndpoint object.

        Args:
            endpoint (str, optional): The endpoint of the titiler server. Defaults to "https://planetarycomputer.microsoft.com/api/data/v1".
            name (str, optional): The name to be used in the file path. Defaults to "item".
            TileMatrixSetId (str, optional): The TileMatrixSetId to be used in the file path. Defaults to "WebMercatorQuad".
        """
        super().__init__(endpoint, name, TileMatrixSetId)

    def url_for_stac_collection(self):
        return f"{self.endpoint}/collection/{self.TileMatrixSetId}/tilejson.json"

    def url_for_collection_assets(self):
        return f"{self.endpoint}/collection/assets"

    def url_for_collection_bounds(self):
        return f"{self.endpoint}/collection/bounds"

    def url_for_collection_info(self):
        return f"{self.endpoint}/collection/info"

    def url_for_collection_info_geojson(self):
        return f"{self.endpoint}/collection/info.geojson"

    def url_for_collection_pixel_value(self, lon, lat):
        return f"{self.endpoint}/collection/point/{lon},{lat}"

    def url_for_collection_wmts(self):
        return f"{self.endpoint}/collection/{self.TileMatrixSetId}/WMTSCapabilities.xml"

    def url_for_collection_lat_lon_assets(self, lng, lat):
        return f"{self.endpoint}/collection/{lng},{lat}/assets"

    def url_for_collection_bbox_assets(self, minx, miny, maxx, maxy):
        return f"{self.endpoint}/collection/{minx},{miny},{maxx},{maxy}/assets"

    def url_for_stac_mosaic(self, searchid):
        return f"{self.endpoint}/mosaic/{searchid}/{self.TileMatrixSetId}/tilejson.json"

    def url_for_mosaic_info(self, searchid):
        return f"{self.endpoint}/mosaic/{searchid}/info"

    def url_for_mosaic_lat_lon_assets(self, searchid, lon, lat):
        return f"{self.endpoint}/mosaic/{searchid}/{lon},{lat}/assets"


def check_titiler_endpoint(titiler_endpoint: Optional[str] = None):
    """Returns the default titiler endpoint.

    Returns:
        object: A titiler endpoint.
    """
    if titiler_endpoint is None:
        if os.environ.get("TITILER_ENDPOINT") is not None:
            titiler_endpoint = os.environ.get("TITILER_ENDPOINT")

            if titiler_endpoint == "planetary-computer":
                titiler_endpoint = PlanetaryComputerEndpoint()
        else:
            titiler_endpoint = "https://titiler.xyz"
    elif titiler_endpoint in ["planetary-computer", "pc"]:
        titiler_endpoint = PlanetaryComputerEndpoint()

    return titiler_endpoint


def cog_tile(
    url,
    bands: str = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> Tuple:
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG).
        Source code adapted from https://developmentseed.org/titiler/examples/notebooks/Working_with_CloudOptimizedGeoTIFF_simple/

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        bands (list, optional): List of bands to use. Defaults to None.
        titiler_endpoint (str, optional): TiTiler endpoint. Defaults to "https://titiler.xyz".
        **kwargs: Additional arguments to pass to the titiler endpoint. For more information about the available arguments, see https://developmentseed.org/titiler/endpoints/cog/#tiles.
            For example, to apply a rescaling to multiple bands, use something like `rescale=["164,223","130,211","99,212"]`.

    Returns:
        tuple: Returns the COG Tile layer URL and bounds.
    """
    import json

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    kwargs["url"] = url

    band_names = cog_bands(url, titiler_endpoint)

    if isinstance(bands, str):
        bands = [bands]

    if bands is None and "bidx" not in kwargs:
        if len(band_names) >= 3:
            kwargs["bidx"] = [1, 2, 3]
    elif isinstance(bands, list) and "bidx" not in kwargs:
        if all(isinstance(x, int) for x in bands):
            if len(set(bands)) == 1:
                bands = bands[0]
            kwargs["bidx"] = bands
        elif all(isinstance(x, str) for x in bands):
            if len(set(bands)) == 1:
                bands = bands[0]
            kwargs["bidx"] = [band_names.index(x) + 1 for x in bands]
        else:
            raise ValueError("Bands must be a list of integers or strings.")

    if "palette" in kwargs:
        kwargs["colormap_name"] = kwargs["palette"].lower()
        del kwargs["palette"]

    if "bidx" not in kwargs:
        kwargs["bidx"] = [1]
    elif isinstance(kwargs["bidx"], int):
        kwargs["bidx"] = [kwargs["bidx"]]

    if "rescale" not in kwargs and ("colormap" not in kwargs):
        stats = cog_stats(url, titiler_endpoint)

        if "message" not in stats:
            try:
                rescale = []
                for i in band_names:
                    rescale.append(
                        "{},{}".format(
                            stats[i]["percentile_2"],
                            stats[i]["percentile_98"],
                        )
                    )
                kwargs["rescale"] = rescale
            except Exception as e:
                pass

    if "colormap" in kwargs and isinstance(kwargs["colormap"], dict):
        kwargs["colormap"] = json.dumps(kwargs["colormap"])

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    if "default_vis" in kwargs.keys() and kwargs["default_vis"]:
        kwargs = {"url": url}

    r = requests.get(
        f"{titiler_endpoint}/cog/{TileMatrixSetId}/tilejson.json", params=kwargs
    ).json()
    return r["tiles"][0]


def cog_tile_vmin_vmax(
    url: str,
    bands: Optional[List] = None,
    titiler_endpoint: Optional[str] = None,
    percentile: Optional[bool] = True,
    **kwargs,
) -> Tuple:
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG) and return the minimum and maximum values.

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        bands (list, optional): List of bands to use. Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        percentile (bool, optional): Whether to use percentiles or not. Defaults to True.
    Returns:
        tuple: Returns the minimum and maximum values.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    stats = cog_stats(url, titiler_endpoint)

    if isinstance(bands, str):
        bands = [bands]

    if bands is not None:
        stats = {s: stats[s] for s in stats if s in bands}

    if percentile:
        vmin = min([stats[s]["percentile_2"] for s in stats])
        vmax = max([stats[s]["percentile_98"] for s in stats])
    else:
        vmin = min([stats[s]["min"] for s in stats])
        vmax = max([stats[s]["max"] for s in stats])

    return vmin, vmax


def cog_mosaic(
    links: List,
    titiler_endpoint: Optional[str] = None,
    username: Optional[str] = "anonymous",
    layername=None,
    overwrite: Optional[bool] = False,
    verbose: Optional[bool] = True,
    **kwargs,
) -> str:
    """Creates a COG mosaic from a list of COG URLs.

    Args:
        links (list): A list containing COG HTTP URLs.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        username (str, optional): User name for the titiler endpoint. Defaults to "anonymous".
        layername ([type], optional): Layer name to use. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the layer name if existing. Defaults to False.
        verbose (bool, optional): Whether to print out descriptive information. Defaults to True.

    Raises:
        Exception: If the COG mosaic fails to create.

    Returns:
        str: The tile URL for the COG mosaic.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if layername is None:
        layername = "layer_X"

    try:
        if verbose:
            print("Creating COG masaic ...")

        # Create token
        r = requests.post(
            f"{titiler_endpoint}/tokens/create",
            json={"username": username, "scope": ["mosaic:read", "mosaic:create"]},
        ).json()
        token = r["token"]

        # Create mosaic
        requests.post(
            f"{titiler_endpoint}/mosaicjson/create",
            json={
                "username": username,
                "layername": layername,
                "files": links,
                # "overwrite": overwrite
            },
            params={
                "access_token": token,
            },
        ).json()

        r2 = requests.get(
            f"{titiler_endpoint}/mosaicjson/{username}.{layername}/tilejson.json",
        ).json()

        return r2["tiles"][0]

    except Exception as e:
        raise Exception(e)


def cog_mosaic_from_file(
    filepath: str,
    skip_rows: Optional[int] = 0,
    titiler_endpoint: Optional[str] = None,
    username: Optional[str] = "anonymous",
    layername=None,
    overwrite: Optional[bool] = False,
    verbose: Optional[bool] = True,
    **kwargs,
) -> str:
    """Creates a COG mosaic from a csv/txt file stored locally for through HTTP URL.

    Args:
        filepath (str): Local path or HTTP URL to the csv/txt file containing COG URLs.
        skip_rows (int, optional): The number of rows to skip in the file. Defaults to 0.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        username (str, optional): User name for the titiler endpoint. Defaults to "anonymous".
        layername ([type], optional): Layer name to use. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the layer name if existing. Defaults to False.
        verbose (bool, optional): Whether to print out descriptive information. Defaults to True.

    Returns:
        str: The tile URL for the COG mosaic.
    """
    import urllib

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    links = []
    if filepath.startswith("http"):
        data = urllib.request.urlopen(filepath)
        for line in data:
            links.append(line.decode("utf-8").strip())

    else:
        with open(filepath) as f:
            links = [line.strip() for line in f.readlines()]

    links = links[skip_rows:]
    # print(links)
    mosaic = cog_mosaic(
        links, titiler_endpoint, username, layername, overwrite, verbose, **kwargs
    )
    return mosaic


def cog_bounds(
    url: str,
    titiler_endpoint: Optional[str] = None,
) -> List:
    """Get the bounding box of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    r = requests.get(f"{titiler_endpoint}/cog/bounds", params={"url": url}).json()

    if "bounds" in r.keys():
        bounds = r["bounds"]
    else:
        bounds = None
    return bounds


def cog_center(
    url: str,
    titiler_endpoint: Optional[str] = None,
) -> Tuple:
    """Get the centroid of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    bounds = cog_bounds(url, titiler_endpoint)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def cog_bands(
    url: str,
    titiler_endpoint: Optional[str] = None,
) -> List:
    """Get band names of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A list of band names
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    r = requests.get(
        f"{titiler_endpoint}/cog/info",
        params={
            "url": url,
        },
    ).json()

    bands = [b[0] for b in r["band_descriptions"]]
    return bands


def cog_stats(
    url: str,
    titiler_endpoint: Optional[str] = None,
) -> List:
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A dictionary of band statistics.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    r = requests.get(
        f"{titiler_endpoint}/cog/statistics",
        params={
            "url": url,
        },
    ).json()

    return r


def cog_info(
    url: str,
    titiler_endpoint: Optional[str] = None,
    return_geojson: Optional[bool] = False,
) -> List:
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A dictionary of band info.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    info = "info"
    if return_geojson:
        info = "info.geojson"

    r = requests.get(
        f"{titiler_endpoint}/cog/{info}",
        params={
            "url": url,
        },
    ).json()

    return r


def cog_pixel_value(
    lon: float,
    lat: float,
    url: str,
    bidx: Optional[str],
    titiler_endpoint: Optional[str] = None,
    verbose: Optional[bool] = True,
    **kwargs,
) -> List:
    """Get pixel value from COG.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a COG, e.g., 'https://github.com/opengeos/data/releases/download/raster/Libya-2023-07-01.tif'
        bidx (str, optional): Dataset band indexes (e.g bidx=1, bidx=1&bidx=2&bidx=3). Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        verbose (bool, optional): Print status messages. Defaults to True.

    Returns:
        list: A dictionary of band info.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    kwargs["url"] = url
    if bidx is not None:
        kwargs["bidx"] = bidx

    r = requests.get(f"{titiler_endpoint}/cog/point/{lon},{lat}", params=kwargs).json()
    bands = cog_bands(url, titiler_endpoint)
    # if isinstance(titiler_endpoint, str):
    #     r = requests.get(f"{titiler_endpoint}/cog/point/{lon},{lat}", params=kwargs).json()
    # else:
    #     r = requests.get(
    #         titiler_endpoint.url_for_stac_pixel_value(lon, lat), params=kwargs
    #     ).json()

    if "detail" in r:
        if verbose:
            print(r["detail"])
        return None
    else:
        values = r["values"]
        result = dict(zip(bands, values))
        return result


def stac_tile(
    url: str = None,
    collection: str = None,
    item: str = None,
    assets: Union[str, List] = None,
    bands: list = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> str:
    """Get a tile layer from a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "https://planetarycomputer.microsoft.com/api/data/v1", "planetary-computer", "pc". Defaults to None.

    Returns:
        str: Returns the STAC Tile layer URL.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    if "palette" in kwargs:
        kwargs["colormap_name"] = kwargs["palette"].lower()
        del kwargs["palette"]

    if isinstance(bands, list) and len(set(bands)) == 1:
        bands = bands[0]

    if isinstance(assets, list) and len(set(assets)) == 1:
        assets = assets[0]

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if "expression" in kwargs and ("asset_as_band" not in kwargs):
        kwargs["asset_as_band"] = True

    mosaic_json = False

    if isinstance(titiler_endpoint, PlanetaryComputerEndpoint):
        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")
        if assets is None and (bands is not None):
            assets = bands
        else:
            kwargs["bidx"] = bands

        kwargs["assets"] = assets

        if (
            (assets is not None)
            and ("asset_expression" not in kwargs)
            and ("expression" not in kwargs)
            and ("rescale" not in kwargs)
        ):
            stats = stac_stats(
                collection=collection,
                item=item,
                assets=assets,
                titiler_endpoint=titiler_endpoint,
            )
            if "detail" not in stats:
                try:
                    percentile_2 = min([stats[s]["percentile_2"] for s in stats])
                    percentile_98 = max([stats[s]["percentile_98"] for s in stats])
                except:
                    percentile_2 = min(
                        [
                            stats[s][list(stats[s].keys())[0]]["percentile_2"]
                            for s in stats
                        ]
                    )
                    percentile_98 = max(
                        [
                            stats[s][list(stats[s].keys())[0]]["percentile_98"]
                            for s in stats
                        ]
                    )
                kwargs["rescale"] = f"{percentile_2},{percentile_98}"
            else:
                print(stats["detail"])  # When operation times out.

    else:
        data = requests.get(url).json()
        if "mosaicjson" in data:
            mosaic_json = True

        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")

        if assets is None:
            if bands is not None:
                assets = bands
            else:
                bnames = stac_bands(url)
                if isinstance(bnames, list):
                    if len(bnames) >= 3:
                        assets = bnames[0:3]
                    else:
                        assets = bnames[0]
                else:
                    assets = None

        else:
            kwargs["asset_bidx"] = bands
        if assets is not None:
            kwargs["assets"] = assets

        if (
            (assets is not None)
            and ("asset_expression" not in kwargs)
            and ("expression" not in kwargs)
            and ("rescale" not in kwargs)
        ):
            stats = stac_stats(
                url=url,
                assets=assets,
                titiler_endpoint=titiler_endpoint,
            )
            if "detail" not in stats:
                try:
                    percentile_2 = min([stats[s]["percentile_2"] for s in stats])
                    percentile_98 = max([stats[s]["percentile_98"] for s in stats])
                except:
                    percentile_2 = min(
                        [
                            stats[s][list(stats[s].keys())[0]]["percentile_2"]
                            for s in stats
                        ]
                    )
                    percentile_98 = max(
                        [
                            stats[s][list(stats[s].keys())[0]]["percentile_98"]
                            for s in stats
                        ]
                    )
                kwargs["rescale"] = f"{percentile_2},{percentile_98}"
            else:
                print(stats["detail"])  # When operation times out.

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    if mosaic_json:
        r = requests.get(
            f"{titiler_endpoint}/mosaicjson/tilejson.json", params=kwargs
        ).json()
    else:
        if isinstance(titiler_endpoint, str):
            r = requests.get(
                f"{titiler_endpoint}/stac/{TileMatrixSetId}/tilejson.json",
                params=kwargs,
            ).json()
        else:
            r = requests.get(titiler_endpoint.url_for_stac_item(), params=kwargs).json()

    return r["tiles"][0]


def stac_bounds(
    url: str = None,
    collection: str = None,
    item: str = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get the bounding box of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
        response = requests.get(url)
        r = response.json()
        if "mosaicjson" in r:
            if "bounds" in r:
                return r["bounds"]

    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/bounds", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_bounds(), params=kwargs).json()

    bounds = r["bounds"]
    return bounds


def stac_center(
    url: str = None,
    collection: str = None,
    item: str = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> Tuple[float, float]:
    """Get the centroid of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    bounds = stac_bounds(url, collection, item, titiler_endpoint, **kwargs)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lon, lat)
    return center


def stac_bands(
    url: str = None,
    collection: str = None,
    item: str = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get band names of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of band names
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/assets", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_assets(), params=kwargs).json()

    return r


def stac_stats(
    url: str = None,
    collection: str = None,
    item: str = None,
    assets: Union[str, List] = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get band statistics of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band statistics.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/statistics", params=kwargs).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_statistics(), params=kwargs
        ).json()

    return r


def stac_min_max(
    url: str = None,
    collection: str = None,
    item: str = None,
    assets: Union[str, List] = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get the min and max values of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band statistics.
    """

    stats = stac_stats(url, collection, item, assets, titiler_endpoint, **kwargs)

    values = stats.values()

    try:
        min_values = [v["min"] for v in values]
        max_values = [v["max"] for v in values]

        return min(min_values), max(max_values)
    except Exception as e:
        return None, None


def stac_info(
    url: str = None,
    collection: str = None,
    item: str = None,
    assets: Union[str, List] = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get band info of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band info.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/info", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_info(), params=kwargs).json()

    return r


def stac_info_geojson(
    url: str = None,
    collection: str = None,
    item: str = None,
    assets: Union[str, List] = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get band info of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band info.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/info.geojson", params=kwargs).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_info_geojson(), params=kwargs
        ).json()

    return r


def stac_assets(
    url: str = None,
    collection: str = None,
    item: str = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get all assets of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of assets.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/assets", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_assets(), params=kwargs).json()

    return r


def stac_pixel_value(
    lon: float,
    lat: float,
    url: str = None,
    collection: str = None,
    item: str = None,
    assets: Union[str, List] = None,
    titiler_endpoint: Optional[str] = None,
    verbose: Optional[bool] = True,
    **kwargs,
):
    """Get pixel value from STAC assets.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        verbose (bool, optional): Print out the error message. Defaults to True.

    Returns:
        list: A dictionary of pixel values for each asset.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    if assets is None:
        assets = stac_assets(
            url=url,
            collection=collection,
            item=item,
            titiler_endpoint=titiler_endpoint,
        )
    kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):

        r = requests.get(
            f"{titiler_endpoint}/stac/point/{lon},{lat}", params=kwargs
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_pixel_value(lon, lat), params=kwargs
        ).json()

    if "detail" in r:
        if verbose:
            print(r["detail"])
        return None
    else:
        values = r["values"]
        if isinstance(assets, str):
            assets = assets.split(",")
        result = dict(zip(assets, values))
        return result


def stac_object_type(url: str, **kwargs) -> str:
    """Get the STAC object type.

    Args:
        url (str): The STAC object URL.
        **kwargs: Keyword arguments for pystac.STACObject.from_file(). Defaults to None.

    Returns:
        str: The STAC object type, can be catalog, collection, or item.
    """
    try:
        obj = pystac.STACObject.from_file(url, **kwargs)

        if isinstance(obj, pystac.Collection):
            return "collection"
        elif isinstance(obj, pystac.Item):
            return "item"
        elif isinstance(obj, pystac.Catalog):
            return "catalog"

    except Exception as e:
        print(e)
        return None


def stac_root_link(url: str, return_col_id: Optional[bool] = False, **kwargs) -> str:
    """Get the root link of a STAC object.

    Args:
        url (str): The STAC object URL.
        return_col_id (bool, optional): Return the collection ID if the STAC object is a collection. Defaults to False.
        **kwargs: Keyword arguments for pystac.STACObject.from_file(). Defaults to None.

    Returns:
        str: The root link of the STAC object.
    """
    collection_id = None
    try:
        obj = pystac.STACObject.from_file(url, **kwargs)
        if isinstance(obj, pystac.Collection):
            collection_id = obj.id
        href = obj.get_root_link().get_href()

        if not url.startswith(href):
            href = obj.get_self_href()

        if return_col_id:
            return href, collection_id
        else:
            return href

    except Exception as e:
        print(e)
        if return_col_id:
            return None, None
        else:
            return None


def stac_client(
    url: str,
    headers: Optional[Dict] = None,
    parameters: Optional[Dict] = None,
    ignore_conformance: Optional[bool] = False,
    modifier: Optional[Callable] = None,
    request_modifier: Optional[Callable] = None,
    stac_io=None,
    return_col_id: Optional[bool] = False,
    get_root: Optional[bool] = True,
    **kwargs,
):
    """Get the STAC client. It wraps the pystac.Client.open() method. See
        https://pystac-client.readthedocs.io/en/stable/api.html#pystac_client.Client.open

    Args:
        url (str): The URL of a STAC Catalog.
        headers (dict, optional):  A dictionary of additional headers to use in all requests
            made to any part of this Catalog/API. Defaults to None.
        parameters (dict, optional): Optional dictionary of query string parameters to include in all requests.
            Defaults to None.
        ignore_conformance (bool, optional): Ignore any advertised Conformance Classes in this Catalog/API.
            This means that functions will skip checking conformance, and may throw an unknown error
            if that feature is not supported, rather than a NotImplementedError. Defaults to False.
        modifier (function, optional): A callable that modifies the children collection and items
            returned by this Client. This can be useful for injecting authentication parameters
            into child assets to access data from non-public sources. Defaults to None.
        request_modifier (function, optional): A callable that either modifies a Request instance or returns
            a new one. This can be useful for injecting Authentication headers and/or signing fully-formed
            requests (e.g. signing requests using AWS SigV4). The callable should expect a single argument,
            which will be an instance of requests.Request. If the callable returns a requests.Request, that
            will be used. Alternately, the callable may simply modify the provided request object and
            return None.
        stac_io (pystac.stac_io, optional): A StacApiIO object to use for I/O requests. Generally, leave
            this to the default. However in cases where customized I/O processing is required, a custom
            instance can be provided here.
        return_col_id (bool, optional): Return the collection ID. Defaults to False.
        get_root (bool, optional): Get the root link of the STAC object. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the pystac.Client.open() method.

    Returns:
        pystac.Client: The STAC client.
    """
    from pystac_client import Client

    collection_id = None

    if not get_root:
        return_col_id = False

    try:
        if get_root:
            root = stac_root_link(url, return_col_id=return_col_id)
        else:
            root = url

        if return_col_id:
            client = Client.open(
                root[0],
                headers,
                parameters,
                ignore_conformance,
                modifier,
                request_modifier,
                stac_io,
                **kwargs,
            )
            collection_id = root[1]
            return client, collection_id
        else:
            client = Client.open(
                root,
                headers,
                parameters,
                ignore_conformance,
                modifier,
                request_modifier,
                stac_io,
                **kwargs,
            )
            return client, client.id

    except Exception as e:
        print(e)
        return None


def stac_collections(
    url: str, return_ids: Optional[bool] = False, get_root=True, **kwargs
) -> List:
    """Get the collection IDs of a STAC catalog.

    Args:
        url (str): The STAC catalog URL.
        return_ids (bool, optional): Return collection IDs. Defaults to False.
        get_root (bool, optional): Get the root link of the STAC object. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the stac_client() method.

    Returns:
        list: A list of collection IDs.
    """
    try:
        client, _ = stac_client(url, get_root=get_root, **kwargs)
        collections = client.get_all_collections()

        if return_ids:
            return [c.id for c in collections]
        else:
            return collections

    except Exception as e:
        print(e)
        return None


def stac_search(
    url: str,
    method: Optional[str] = "POST",
    max_items: Optional[int] = None,
    limit: Optional[int] = 100,
    ids: Optional[List] = None,
    collections: Optional[List] = None,
    bbox: Optional[Union[List, Tuple]] = None,
    intersects: Optional[Union[str, Dict]] = None,
    datetime: Optional[str] = None,
    query: Optional[List] = None,
    filter: Optional[Dict] = None,
    filter_lang: Optional[str] = None,
    sortby: Optional[Union[List, str]] = None,
    fields: Optional[List] = None,
    get_collection: Optional[bool] = False,
    get_items: Optional[bool] = False,
    get_assets: Optional[bool] = False,
    get_links: Optional[bool] = False,
    get_gdf: Optional[bool] = False,
    get_info: Optional[bool] = False,
    get_root: Optional[bool] = True,
    **kwargs,
) -> List:
    """Search a STAC API. The function wraps the pysatc_client.Client.search() method. See
        https://pystac-client.readthedocs.io/en/stable/api.html#pystac_client.Client.search

    Args:
        url (str): The STAC API URL.
        method (str, optional): The HTTP method to use when making a request to the service.
            This must be either "GET", "POST", or None. If None, this will default to "POST".
            If a "POST" request receives a 405 status for the response, it will automatically
            retry with "GET" for all subsequent requests. Defaults to "POST".
        max_items (init, optional): The maximum number of items to return from the search,
            even if there are more matching results. This client to limit the total number of
            Items returned from the items(), item_collections(), and items_as_dicts methods().
            The client will continue to request pages of items until the number of max items
            is reached. This parameter defaults to 100. Setting this to None will allow iteration
            over a possibly very large number of results.. Defaults to None.
        limit (int, optional): A recommendation to the service as to the number of items to
            return per page of results. Defaults to 100.
        ids (list, optional): List of one or more Item ids to filter on. Defaults to None.
        collections (list, optional): List of one or more Collection IDs or pystac.Collection instances.
            Only Items in one of the provided Collections will be searched. Defaults to None.
        bbox (list | tuple, optional): A list, tuple, or iterator representing a bounding box of 2D
            or 3D coordinates. Results will be filtered to only those intersecting the bounding box.
            Defaults to None.
        intersects (str | dict, optional):  A string or dictionary representing a GeoJSON geometry, or
            an object that implements a __geo_interface__ property, as supported by several
            libraries including Shapely, ArcPy, PySAL, and geojson. Results filtered to only
            those intersecting the geometry. Defaults to None.
        datetime (str, optional): Either a single datetime or datetime range used to filter results.
            You may express a single datetime using a datetime.datetime instance, a RFC 3339-compliant
            timestamp, or a simple date string (see below). Instances of datetime.datetime may be either
            timezone aware or unaware. Timezone aware instances will be converted to a UTC timestamp
            before being passed to the endpoint. Timezone unaware instances are assumed to represent
            UTC timestamps. You may represent a datetime range using a "/" separated string as described
            in the spec, or a list, tuple, or iterator of 2 timestamps or datetime instances.
            For open-ended ranges, use either ".." ('2020-01-01:00:00:00Z/..', ['2020-01-01:00:00:00Z', '..'])
            or a value of None (['2020-01-01:00:00:00Z', None]). If using a simple date string,
            the datetime can be specified in YYYY-mm-dd format, optionally truncating to
            YYYY-mm or just YYYY. Simple date strings will be expanded to include the entire
            time period. Defaults to None.
        query (list, optional): List or JSON of query parameters as per the STAC API query extension.
            such as {"eo:cloud_cover":{"lt":10}}. Defaults to None.
        filter (dict, optional): JSON of query parameters as per the STAC API filter extension. Defaults to None.
        filter_lang (str, optional): Language variant used in the filter body. If filter is a dictionary
            or not provided, defaults to ‘cql2-json’. If filter is a string, defaults to cql2-text. Defaults to None.
        sortby (str | list, optional): A single field or list of fields to sort the response by.
            such as [{ 'field': 'properties.eo:cloud_cover', 'direction': 'asc' }]. Defaults to None.
        fields (list, optional): A list of fields to include in the response. Note this may result in
            invalid STAC objects, as they may not have required fields. Use items_as_dicts to avoid object
            unmarshalling errors. Defaults to None.
        get_collection (bool, optional): True to return a pystac.ItemCollection. Defaults to False.
        get_items (bool, optional): True to return a list of pystac.Item. Defaults to False.
        get_assets (bool, optional): True to return a list of pystac.Asset. Defaults to False.
        get_links (bool, optional): True to return a list of links. Defaults to False.
        get_gdf (bool, optional): True to return a GeoDataFrame. Defaults to False.
        get_info (bool, optional): True to return a dictionary of STAC items. Defaults to False.
        get_root (bool, optional): Get the root link of the STAC object. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the stac_client() function.

    Returns:
        list | pystac.ItemCollection : The search results as a list of links or a pystac.ItemCollection.
    """

    client, collection_id = stac_client(
        url, return_col_id=True, get_root=get_root, **kwargs
    )

    if client is None:
        return None
    else:
        if isinstance(intersects, dict) and "geometry" in intersects:
            intersects = intersects["geometry"]

        if collection_id is not None and collections is None:
            collections = [collection_id]

        search = client.search(
            method=method,
            max_items=max_items,
            limit=limit,
            ids=ids,
            collections=collections,
            bbox=bbox,
            intersects=intersects,
            datetime=datetime,
            query=query,
            filter=filter,
            filter_lang=filter_lang,
            sortby=sortby,
            fields=fields,
        )

        if get_collection:
            return search.item_collection()
        elif get_items:
            return list(search.items())
        elif get_assets:
            assets = {}
            for item in search.items():
                assets[item.id] = {}
                for key, value in item.get_assets().items():
                    assets[item.id][key] = value.href
            return assets
        elif get_links:
            return [item.get_self_href() for item in search.items()]
        elif get_gdf:
            import geopandas as gpd

            gdf = gpd.GeoDataFrame.from_features(
                search.item_collection().to_dict(), crs="EPSG:4326"
            )
            return gdf
        elif get_info:
            items = search.items()
            info = {}
            for item in items:
                info[item.id] = {
                    "id": item.id,
                    "href": item.get_self_href(),
                    "bands": list(item.get_assets().keys()),
                    "assets": item.get_assets(),
                }
            return info
        else:
            return search


def stac_search_to_gdf(search, **kwargs):
    """Convert STAC search result to a GeoDataFrame.

    Args:
        search (pystac_client.item_search): The search result returned by leafmap.stac_search().
        **kwargs: Additional keyword arguments to pass to the GeoDataFrame.from_features() function.

    Returns:
        GeoDataFrame: A GeoPandas GeoDataFrame object.
    """
    import geopandas as gpd

    gdf = gpd.GeoDataFrame.from_features(
        search.item_collection().to_dict(), crs="EPSG:4326", **kwargs
    )
    return gdf


def stac_search_to_df(search, **kwargs) -> DataFrame:
    """Convert STAC search result to a DataFrame.

    Args:
        search (pystac_client.item_search): The search result returned by leafmap.stac_search().
        **kwargs: Additional keyword arguments to pass to the DataFrame.drop() function.

    Returns:
        DataFrame: A Pandas DataFrame object.
    """
    gdf = stac_search_to_gdf(search)
    return gdf.drop(columns=["geometry"], **kwargs)


def stac_search_to_dict(search, **kwargs) -> Dict:
    """Convert STAC search result to a dictionary.

    Args:
        search (pystac_client.item_search): The search result returned by leafmap.stac_search().

    Returns:
        dict: A dictionary of STAC items, with the stac item id as the key, and the stac item as the value.
    """

    items = list(search.item_collection())
    info = {}
    for item in items:
        info[item.id] = {
            "id": item.id,
            "href": item.get_self_href(),
            "bands": list(item.get_assets().keys()),
            "assets": item.get_assets(),
        }
        links = {}
        assets = item.get_assets()
        for key, value in assets.items():
            links[key] = value.href
        info[item.id]["links"] = links
    return info


def stac_search_to_list(search, **kwargs) -> List:
    """Convert STAC search result to a list.

    Args:
        search (pystac_client.item_search): The search result returned by leafmap.stac_search().

    Returns:
        list: A list of STAC items.
    """

    return search.item_collections()


def download_data_catalogs(
    out_dir: Optional[str] = None,
    quiet: Optional[bool] = True,
    overwrite: Optional[bool] = False,
) -> str:
    """Download geospatial data catalogs from https://github.com/giswqs/geospatial-data-catalogs.

    Args:
        out_dir (str, optional): The output directory. Defaults to None.
        quiet (bool, optional): Whether to suppress the download progress bar. Defaults to True.
        overwrite (bool, optional): Whether to overwrite the existing data catalog. Defaults to False.

    Returns:
        str: The path to the downloaded data catalog.
    """
    import tempfile
    import gdown
    import zipfile

    if out_dir is None:
        out_dir = tempfile.gettempdir()
    elif not os.path.exists(out_dir):
        os.makedirs(out_dir)

    url = "https://github.com/giswqs/geospatial-data-catalogs/archive/refs/heads/master.zip"

    out_file = os.path.join(out_dir, "geospatial-data-catalogs.zip")
    work_dir = os.path.join(out_dir, "geospatial-data-catalogs-master")

    if os.path.exists(work_dir) and not overwrite:
        return work_dir
    else:
        gdown.download(url, out_file, quiet=quiet)
        with zipfile.ZipFile(out_file, "r") as zip_ref:
            zip_ref.extractall(out_dir)
        return work_dir


def set_default_bands(bands):
    excluded = [
        "index",
        "metadata",
        "mtl.json",
        "mtl.txt",
        "mtl.xml",
        "qa",
        "qa-browse",
        "QA",
        "rendered_preview",
        "tilejson",
        "tir-browse",
        "vnir-browse",
        "xml",
        "documentation",
    ]

    for band in excluded:
        if band in bands:
            bands.remove(band)

    if len(bands) == 0:
        return [None, None, None]

    if isinstance(bands, str):
        bands = [bands]

    if not isinstance(bands, list):
        raise ValueError("bands must be a list or a string.")

    if set(["nir", "red", "green"]) <= set(bands):
        return ["nir", "red", "green"]
    elif set(["nir08", "red", "green"]) <= set(bands):
        return ["nir08", "red", "green"]
    elif set(["red", "green", "blue"]) <= set(bands):
        return ["red", "green", "blue"]
    elif set(["B8", "B4", "B3"]) <= set(bands):
        return ["B8", "B4", "B3"]
    elif set(["B4", "B3", "B2"]) <= set(bands):
        return ["B4", "B3", "B2"]
    elif set(["B3", "B2", "B1"]) <= set(bands):
        return ["B3", "B2", "B1"]
    elif set(["B08", "B04", "B03"]) <= set(bands):
        return ["B08", "B04", "B03"]
    elif set(["B04", "B03", "B02"]) <= set(bands):
        return ["B04", "B03", "B02"]
    elif len(bands) < 3:
        return [bands[0]] * 3
    else:
        return bands[:3]


def maxar_collections(return_ids: Optional[bool] = True, **kwargs) -> List:
    """Get a list of Maxar collections.

    Args:
        return_ids (bool, optional): Whether to return the collection ids. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the pystac Catalog.from_file() method.

    Returns:
        list : A list of Maxar collections.
    """

    import tempfile
    from pystac import Catalog
    import pandas as pd

    if return_ids:
        url = "https://raw.githubusercontent.com/giswqs/maxar-open-data/master/datasets.csv"
        df = pd.read_csv(url)
        return df["dataset"].tolist()

    file_path = os.path.join(tempfile.gettempdir(), "maxar-collections.txt")
    if return_ids:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return [line.strip() for line in f.readlines()]

    if "MAXAR_STAC_API" in os.environ:
        url = os.environ["MAXAR_STAC_API"]
    else:
        url = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"

    root_catalog = Catalog.from_file(url, **kwargs)

    collections = root_catalog.get_collections()

    # if return_ids:
    #     collection_ids = [collection.id for collection in collections]
    #     with open(file_path, "w") as f:
    #         f.write("\n".join(collection_ids))

    #     return collection_ids
    # else:
    return collections


def maxar_child_collections(
    collection_id: str, return_ids: Optional[bool] = True, **kwargs
) -> List:
    """Get a list of Maxar child collections.

    Args:
        collection_id (str): The collection ID, e.g., Kahramanmaras-turkey-earthquake-23
            Use maxar_collections() to retrieve all available collection IDs.
        return_ids (bool, optional): Whether to return the collection ids. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the pystac Catalog.from_file() method.

    Returns:
        list: A list of Maxar child collections.
    """

    import tempfile
    from pystac import Catalog

    file_path = os.path.join(tempfile.gettempdir(), f"maxar-{collection_id}.txt")
    if return_ids:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return [line.strip() for line in f.readlines()]

    if "MAXAR_STAC_API" in os.environ:
        url = os.environ["MAXAR_STAC_API"]
    else:
        url = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"

    root_catalog = Catalog.from_file(url, **kwargs)

    collections = root_catalog.get_child(collection_id).get_collections()

    if return_ids:
        collection_ids = [collection.id for collection in collections]
        with open(file_path, "w") as f:
            f.write("\n".join(collection_ids))
        return collection_ids

    else:
        return collections


def maxar_items(
    collection_id: str,
    child_id: str,
    return_gdf: Optional[bool] = True,
    assets: Optional[List] = ["visual"],
    **kwargs,
):
    """Retrieve STAC items from Maxar's public STAC API.

    Args:
        collection_id (str): The collection ID, e.g., Kahramanmaras-turkey-earthquake-23
            Use maxar_collections() to retrieve all available collection IDs.
        child_id (str): The child collection ID, e.g., 1050050044DE7E00
            Use maxar_child_collections() to retrieve all available child collection IDs.
        return_gdf (bool, optional): If True, return a GeoDataFrame. Defaults to True.
        assets (list, optional): A list of asset names to include in the GeoDataFrame.
            It can be "visual", "ms_analytic", "pan_analytic", "data-mask". Defaults to ['visual'].
        **kwargs: Additional keyword arguments to pass to the pystac Catalog.from_file() method.

    Returns:
        GeoDataFrame | pystac.ItemCollection: If return_gdf is True, return a GeoDataFrame.
    """

    import pickle
    import tempfile
    from pystac import Catalog, ItemCollection

    file_path = os.path.join(
        tempfile.gettempdir(), f"maxar-{collection_id}-{child_id}.pkl"
    )

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            items = pickle.load(f)
        if return_gdf:
            import geopandas as gpd

            gdf = gpd.GeoDataFrame.from_features(
                pystac.ItemCollection(items).to_dict(), crs="EPSG:4326"
            )
            # convert bbox column type from list to string
            gdf["proj:bbox"] = [",".join(map(str, l)) for l in gdf["proj:bbox"]]
            if assets is not None:
                if isinstance(assets, str):
                    assets = [assets]
                elif not isinstance(assets, list):
                    raise ValueError("assets must be a list or a string.")

                for asset in assets:
                    links = []
                    for item in items:
                        if asset in item.get_assets():
                            link = item.get_assets()[asset].get_absolute_href()
                            links.append(link)
                        else:
                            links.append("")

                    gdf[asset] = links

            return gdf
        else:
            return items

    if "MAXAR_STAC_API" in os.environ:
        url = os.environ["MAXAR_STAC_API"]
    else:
        url = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"

    root_catalog = Catalog.from_file(url, **kwargs)

    collection = root_catalog.get_child(collection_id)
    child = collection.get_child(child_id)

    items = ItemCollection(child.get_all_items())

    with open(file_path, "wb") as f:
        pickle.dump(items, f)

    if return_gdf:
        import geopandas as gpd

        gdf = gpd.GeoDataFrame.from_features(
            pystac.ItemCollection(items).to_dict(), crs="EPSG:4326"
        )
        # convert bbox column type from list to string
        gdf["proj:bbox"] = [",".join(map(str, l)) for l in gdf["proj:bbox"]]
        if assets is not None:
            if isinstance(assets, str):
                assets = [assets]
            elif not isinstance(assets, list):
                raise ValueError("assets must be a list or a string.")

            for asset in assets:
                links = []
                for item in items:
                    if asset in item.get_assets():
                        link = item.get_assets()[asset].get_absolute_href()
                        links.append(link)
                    else:
                        links.append("")

                gdf[asset] = links

        return gdf
    else:
        return items


def maxar_all_items(
    collection_id: str,
    return_gdf: Optional[bool] = True,
    assets: Optional[List] = ["visual"],
    verbose: Optional[bool] = True,
    **kwargs,
):
    """Retrieve STAC items from Maxar's public STAC API.

    Args:
        collection_id (str): The collection ID, e.g., Kahramanmaras-turkey-earthquake-23
            Use maxar_collections() to retrieve all available collection IDs.
        return_gdf (bool, optional): If True, return a GeoDataFrame. Defaults to True.
        assets (list, optional): A list of asset names to include in the GeoDataFrame.
            It can be "visual", "ms_analytic", "pan_analytic", "data-mask". Defaults to ['visual'].
        verbose (bool, optional): If True, print progress. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the pystac Catalog.from_file() method.

    Returns:
        GeoDataFrame | pystac.ItemCollection: If return_gdf is True, return a GeoDataFrame.
    """

    child_ids = maxar_child_collections(collection_id, **kwargs)
    for index, child_id in enumerate(child_ids):
        if verbose:
            print(
                f"Processing ({str(index+1).zfill(len(str(len(child_ids))))} out of {len(child_ids)}): {child_id} ..."
            )
        items = maxar_items(collection_id, child_id, return_gdf, assets, **kwargs)
        if return_gdf:
            if child_id == child_ids[0]:
                gdf = items
            else:
                gdf = gdf.append(items)
        else:
            if child_id == child_ids[0]:
                items_all = items
            else:
                items_all.extend(items)

    if return_gdf:
        return gdf
    else:
        return items_all


def maxar_refresh():
    """Refresh the cached Maxar STAC items."""
    import tempfile

    temp_dir = tempfile.gettempdir()
    for f in os.listdir(temp_dir):
        if f.startswith("maxar-"):
            os.remove(os.path.join(temp_dir, f))

    print("Maxar STAC items cache has been refreshed.")


def maxar_search(
    collection, start_date=None, end_date=None, bbox=None, within=False, align=True
):
    """Search Maxar Open Data by collection ID, date range, and/or bounding box.

    Args:
        collection (str): The collection ID, e.g., Kahramanmaras-turkey-earthquake-23.
            Use maxar_collections() to retrieve all available collection IDs.
        start_date (str, optional): The start date, e.g., 2023-01-01. Defaults to None.
        end_date (str, optional): The end date, e.g., 2023-12-31. Defaults to None.
        bbox (list | GeoDataFrame): The bounding box to filter by. Can be a list of 4 coordinates or a file path or a GeoDataFrame.
        within (bool, optional): Whether to filter by the bounding box or the bounding box's interior. Defaults to False.
        align (bool, optional): If True, automatically aligns GeoSeries based on their indices. If False, the order of elements is preserved.

    Returns:
        GeoDataFrame: A GeoDataFrame containing the search results.
    """
    import datetime
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Polygon

    collections = maxar_collections()
    if collection not in collections:
        raise ValueError(
            f"Invalid collection name. Use maxar_collections() to retrieve all available collection IDs."
        )

    url = f"https://raw.githubusercontent.com/giswqs/maxar-open-data/master/datasets/{collection}.geojson"
    data = gpd.read_file(url)

    if bbox is not None:
        bbox = gpd.GeoDataFrame(
            geometry=[Polygon.from_bounds(*bbox)],
            crs="epsg:4326",
        )
        if within:
            data = data[data.within(bbox.unary_union, align=align)]
        else:
            data = data[data.intersects(bbox.unary_union, align=align)]

    date_field = "datetime"
    new_field = f"{date_field}_temp"
    data[new_field] = pd.to_datetime(data[date_field])

    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    if start_date is None:
        start_date = data[new_field].min()

    mask = (data[new_field] >= start_date) & (data[new_field] <= end_date)
    result = data.loc[mask]
    return result.drop(columns=[new_field], axis=1)


def maxar_collection_url(collection, dtype="geojson", raw=True):
    """Retrieve the URL to a Maxar Open Data collection.

    Args:
        collection (str): The collection ID, e.g., Kahramanmaras-turkey-earthquake-23.
            Use maxar_collections() to retrieve all available collection IDs.
        dtype (str, optional): The data type. It can be 'geojson' or 'tsv'. Defaults to 'geojson'.
        raw (bool, optional): If True, return the raw URL. Defaults to True.

    Returns:
        str: The URL to the collection.
    """
    collections = maxar_collections()
    if collection not in collections:
        raise ValueError(
            f"Invalid collection name. Use maxar_collections() to retrieve all available collection IDs."
        )

    if dtype not in ["geojson", "tsv"]:
        raise ValueError(f"Invalid dtype. It can be 'geojson' or 'tsv'.")

    if raw:
        url = f"https://raw.githubusercontent.com/giswqs/maxar-open-data/master/datasets/{collection}.{dtype}"
    else:
        url = f"https://github.com/giswqs/maxar-open-data/blob/master/datasets/{collection}.{dtype}"
    return url


def maxar_tile_url(collection, tile, dtype="geojson", raw=True):
    """Retrieve the URL to a Maxar Open Data tile.

    Args:

        collection (str): The collection ID, e.g., Kahramanmaras-turkey-earthquake-23.
            Use maxar_collections() to retrieve all available collection IDs.
        tile (str): The tile ID, e.g., 10300500D9F8E600.
        dtype (str, optional): The data type. It can be 'geojson', 'json' or 'tsv'. Defaults to 'geojson'.
        raw (bool, optional): If True, return the raw URL. Defaults to True.

    Returns:
        str: The URL to the tile.
    """

    collections = maxar_collections()
    if collection not in collections:
        raise ValueError(
            f"Invalid collection name. Use maxar_collections() to retrieve all available collection IDs."
        )

    if dtype not in ["geojson", "json", "tsv"]:
        raise ValueError(f"Invalid dtype. It can be 'geojson', 'json' or 'tsv'.")

    if raw:
        url = f"https://raw.githubusercontent.com/giswqs/maxar-open-data/master/datasets/{collection}/{tile}.{dtype}"
    else:
        url = f"https://github.com/giswqs/maxar-open-data/blob/master/datasets/{collection}/{tile}.{dtype}"

    return url


def maxar_download(
    images,
    out_dir=None,
    quiet=False,
    proxy=None,
    speed=None,
    use_cookies=True,
    verify=True,
    id=None,
    fuzzy=False,
    resume=False,
    overwrite=False,
):
    """Download Mxar Open Data images.

    Args:
        images (str | images): The list of image links or a file path to a geojson or tsv containing the Maxar download links.
        out_dir (str, optional): The output directory. Defaults to None.
        quiet (bool, optional): Suppress terminal output. Default is False.
        proxy (str, optional): Proxy. Defaults to None.
        speed (float, optional): Download byte size per second (e.g., 256KB/s = 256 * 1024). Defaults to None.
        use_cookies (bool, optional): Flag to use cookies. Defaults to True.
        verify (bool | str, optional): Either a bool, in which case it controls whether the server's TLS certificate is verified, or a string,
            in which case it must be a path to a CA bundle to use. Default is True.. Defaults to True.
        id (str, optional): Google Drive's file ID. Defaults to None.
        fuzzy (bool, optional): Fuzzy extraction of Google Drive's file Id. Defaults to False.
        resume (bool, optional): Resume the download from existing tmp file if possible. Defaults to False.
        overwrite (bool, optional): Overwrite the file if it already exists. Defaults to False.

    """
    import gdown

    if out_dir is None:
        out_dir = os.getcwd()

    if isinstance(images, str):
        if images.endswith(".geojson"):
            import geopandas as gpd

            data = gpd.read_file(images)
            images = data["visual"].tolist()
        elif images.endswith(".tsv"):
            import pandas as pd

            data = pd.read_csv(images, sep="\t")
            images = data["visual"].tolist()
        else:
            raise ValueError(f"Invalid file type. It can be 'geojson' or 'tsv'.")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    for index, image in enumerate(images):
        items = image.split("/")
        file_name = items[7] + ".tif"
        dir_name = items[-1].split("-")[0]
        if not os.path.exists(os.path.join(out_dir, dir_name)):
            os.makedirs(os.path.join(out_dir, dir_name))
        out_file = os.path.join(out_dir, dir_name, file_name)
        if os.path.exists(out_file) and (not overwrite):
            print(f"{out_file} already exists. Skipping...")
            continue
        if not quiet:
            print(
                f"Downloading {str(index+1).zfill(len(str(len(images))))} out of {len(images)}: {dir_name}/{file_name}"
            )

        gdown.download(
            image, out_file, quiet, proxy, speed, use_cookies, verify, id, fuzzy, resume
        )


def create_mosaicjson(images, output):
    """Create a mosaicJSON file from a list of images.

    Args:
        images (str | list): A list of image URLs or a URL to a text file containing a list of image URLs.
        output (str): The output mosaicJSON file path.

    """
    try:
        from cogeo_mosaic.mosaic import MosaicJSON
        from cogeo_mosaic.backends import MosaicBackend
    except ImportError:
        raise ImportError(
            "cogeo-mosaic is required to use this function. "
            "Install with `pip install cogeo-mosaic`."
        )

    if isinstance(images, str):
        if images.startswith("http"):
            import urllib.request

            with urllib.request.urlopen(images) as f:
                file_contents = f.read().decode("utf-8")
                images = file_contents.strip().split("\n")
        elif not os.path.exists(images):
            raise FileNotFoundError(f"{images} does not exist.")

    elif not isinstance(images, list):
        raise ValueError("images must be a list or a URL.")

    mosaic = MosaicJSON.from_urls(images)
    with MosaicBackend(output, mosaic_def=mosaic) as f:
        f.write(overwrite=True)


def flatten_dict(my_dict, parent_key=False, sep="."):
    """Flattens a nested dictionary.

    Args:
        my_dict (dict): The dictionary to flatten.
        parent_key (bool, optional): Whether to include the parent key. Defaults to False.
        sep (str, optional): The separator to use. Defaults to '.'.

    Returns:
        dict: The flattened dictionary.
    """

    flat_dict = {}
    for key, value in my_dict.items():
        if not isinstance(value, dict):
            flat_dict[key] = value
        else:
            sub_dict = flatten_dict(value)
            for sub_key, sub_value in sub_dict.items():
                if parent_key:
                    flat_dict[parent_key + sep + sub_key] = sub_value
                else:
                    flat_dict[sub_key] = sub_value

    return flat_dict


def oam_search(
    bbox=None, start_date=None, end_date=None, limit=100, return_gdf=True, **kwargs
):
    """Search OpenAerialMap (https://openaerialmap.org) and return a GeoDataFrame or list of image metadata.

    Args:
        bbox (list | str, optional): The bounding box [xmin, ymin, xmax, ymax] to search within. Defaults to None.
        start_date (str, optional): The start date to search within, such as "2015-04-20T00:00:00.000Z". Defaults to None.
        end_date (str, optional): The end date to search within, such as "2015-04-21T00:00:00.000Z". Defaults to None.
        limit (int, optional): The maximum number of results to return. Defaults to 100.
        return_gdf (bool, optional): If True, return a GeoDataFrame, otherwise return a list. Defaults to True.
        **kwargs: Additional keyword arguments to pass to the API. See https://hotosm.github.io/oam-api/

    Returns:
        GeoDataFrame | list: If return_gdf is True, return a GeoDataFrame. Otherwise, return a list.
    """

    import pandas as pd
    from shapely.geometry import Polygon
    import geopandas as gpd

    url = "https://api.openaerialmap.org/meta"
    if bbox is not None:
        if isinstance(bbox, str):
            bbox = [float(x) for x in bbox.split(",")]
        if not isinstance(bbox, list):
            raise ValueError("bbox must be a list.")
        if len(bbox) != 4:
            raise ValueError("bbox must be a list of 4 numbers.")
        bbox = ",".join(map(str, bbox))
        kwargs["bbox"] = bbox

    if start_date is not None:
        kwargs["acquisition_from"] = start_date

    if end_date is not None:
        kwargs["acquisition_to"] = end_date

    if limit is not None:
        kwargs["limit"] = limit

    try:
        r = requests.get(url, params=kwargs).json()
        if "results" in r:
            results = []
            for result in r["results"]:
                if "geojson" in result:
                    del result["geojson"]
                if "projection" in result:
                    del result["projection"]
                if "footprint" in result:
                    del result["footprint"]
                result = flatten_dict(result)
                results.append(result)

            if not return_gdf:
                return results
            else:
                df = pd.DataFrame(results)

                polygons = [Polygon.from_bounds(*bbox) for bbox in df["bbox"]]
                gdf = gpd.GeoDataFrame(geometry=polygons, crs="epsg:4326")

                return pd.concat([gdf, df], axis=1)

        else:
            print("No results found.")
            return None

    except Exception as e:
        return None
