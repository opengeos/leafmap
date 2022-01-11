"""A module for Microsoft Planetary Computer (PC).

"""
import json
import os
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


def get_pc_inventory(refresh=False, verbose=False):
    """Get the inventory of the Microsoft Planetary Computer catalog.

    Args:
        refresh (bool, optional): If True, refresh the inventory.
        verbose (bool, optional): If True, print the collections to the console.

    Returns:
        dict: A dictionary of collections and their bands.
    """
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("leafmap", "leafmap.py"))
    filepath = os.path.join(pkg_dir, "data/pc_inventory.json")

    if refresh:
        catalog = Client.open(PC_ENDPOINT)
        collections = catalog.get_children()
        data = {}
        for collection in collections:
            try:
                if verbose:
                    print(f"{collection.id} - {collection.title}")
                first_item = get_first_item(collection.id, return_id=True)
                bands = stac_bands(collection=collection.id, items=first_item)
                if isinstance(bands, list):
                    data[collection.id] = {}
                    data[collection.id]["title"] = collection.title
                    data[collection.id]["first_item"] = first_item
                    data[collection.id]["bands"] = bands
            except Exception as e:
                if verbose:
                    print(f"{collection.id} has no bands.")

        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    else:
        with open(filepath, "r") as f:
            data = json.load(f)

    return data


def get_collection_list():
    """Get a list of collections in the Microsoft Planetary Computer catalog.

    Returns:
        list: A list of collections.
    """
    inventory = get_pc_inventory()

    names = []

    for key in inventory:
        names.append(f"{key} - {inventory[key]['title']}")
    names.sort()

    return names
