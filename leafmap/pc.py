"""A module for Microsoft Planetary Computer (PC).

"""

from pystac_client import Client
from .common import stac_bands


PC_ENDPOINT = "https://planetarycomputer.microsoft.com/api/stac/v1"


def get_pc_collections(verbose=False):
    """Get a list of all collections in the Microsoft Planetary Computer catalog.

    Args:
        verbose (bool, optional): If True, print the collections to the console.
    """
    catalog = Client.open(PC_ENDPOINT)
    collections = catalog.get_children()
    result = {}
    for collection in collections:
        result[collection.id] = collection.title
        if verbose:
            print(f"{collection.id} - {collection.title}")

    return result


def get_first_item(collection, return_id=False):
    """Get the first item in a collection.

    Args:
        collection (str): The collection to get the first item from.
        return_id (bool, optional): If True, return the item's ID instead of the item itself.

    Returns:
        pystac.Item: The first item in the collection.
    """
    catalog = Client.open(PC_ENDPOINT)
    col = catalog.get_child(collection)
    item = next(col.get_items())
    if return_id:
        return item.id
    else:
        return item


def get_bands(collection, item=None):
    """Get the bands of an item.

    Args:
        collection (str): The collection the item is in.
        item (str): The item to get the bands of.

    Returns:
        list: A list of bands.
    """
    if item is None:
        item = get_first_item(collection, return_id=True)
    return stac_bands(collection=collection, items=item)
