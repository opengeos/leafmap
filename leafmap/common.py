"""This module contains some common functions for both folium and ipyleaflet.
"""

import csv
import json
import os
import requests
import shutil
import tarfile
import urllib.request
import zipfile
import folium
import ipyleaflet
import ipywidgets as widgets
import whitebox
from typing import Union, List, Dict, Tuple, Optional
from .stac import *

try:
    from IPython.display import display, IFrame
except ImportError:
    pass


class WhiteboxTools(whitebox.WhiteboxTools):
    """This class inherits the whitebox WhiteboxTools class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


def whiteboxgui(verbose=True, tree=False, reset=False, sandbox_path=None):
    """Shows the WhiteboxTools GUI.

    Args:
        verbose (bool, optional): Whether to show progress info when the tool is running. Defaults to True.
        tree (bool, optional): Whether to use the tree mode toolbox built using ipytree rather than ipywidgets. Defaults to False.
        reset (bool, optional): Whether to regenerate the json file with the dictionary containing the information for all tools. Defaults to False.
        sandbox_path (str, optional): The path to the sandbox folder. Defaults to None.

    Returns:
        object: A toolbox GUI.
    """
    import whiteboxgui

    return whiteboxgui.show(verbose, tree, reset, sandbox_path)


def _in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def _is_drive_mounted():
    """Checks whether Google Drive is mounted in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    drive_path = "/content/drive/My Drive"
    if os.path.exists(drive_path):
        return True
    else:
        return False


def set_proxy(port=1080, ip="http://127.0.0.1"):
    """Sets proxy if needed. This is only needed for countries where Google services are not available.

    Args:
        port (int, optional): The proxy port number. Defaults to 1080.
        ip (str, optional): The IP address. Defaults to 'http://127.0.0.1'.
    """

    try:
        if not ip.startswith("http"):
            ip = "http://" + ip
        proxy = "{}:{}".format(ip, port)

        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy

        a = requests.get("https://google.com")

        if a.status_code != 200:
            print(
                "Failed to connect to Google services. Please double check the port number and ip address."
            )

    except Exception as e:
        raise Exception(e)


def _check_install(package):
    """Checks whether a package is installed. If not, it will install the package.

    Args:
        package (str): The name of the package to check.
    """
    import subprocess

    try:
        __import__(package)
        # print('{} is already installed.'.format(package))
    except ImportError:
        print("{} is not installed. Installing ...".format(package))
        try:
            subprocess.check_call(["python", "-m", "pip", "install", package])
        except Exception as e:
            print("Failed to install {}".format(package))
            print(e)
        print("{} has been installed successfully.".format(package))


def update_package():
    """Updates the leafmap package from the leafmap GitHub repository without the need to use pip or conda.
    In this way, I don't have to keep updating pypi and conda-forge with every minor update of the package.

    """

    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        _clone_repo(out_dir=download_dir)

        pkg_dir = os.path.join(download_dir, "leafmap-master")
        work_dir = os.getcwd()
        os.chdir(pkg_dir)

        if shutil.which("pip") is None:
            cmd = "pip3 install ."
        else:
            cmd = "pip install ."

        os.system(cmd)
        os.chdir(work_dir)

        print(
            "\nPlease comment out 'leafmap.update_package()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output"
        )

    except Exception as e:
        raise Exception(e)


def check_package(name, URL=""):
    try:
        __import__(name.lower())
    except Exception:
        raise ImportError(
            f"{name} is not installed. Please install it before proceeding. {URL}"
        )


def _clone_repo(out_dir=".", unzip=True):
    """Clones the leafmap GitHub repository.

    Args:
        out_dir (str, optional): Output folder for the repo. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the repository. Defaults to True.
    """
    url = "https://github.com/opengeos/leafmap/archive/master.zip"
    filename = "leafmap-master.zip"
    download_from_url(url, out_file_name=filename, out_dir=out_dir, unzip=unzip)


def __install_from_github(url):
    """Install a package from a GitHub repository.

    Args:
        url (str): The URL of the GitHub repository.
    """

    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        repo_name = os.path.basename(url)
        zip_url = os.path.join(url, "archive/master.zip")
        filename = repo_name + "-master.zip"
        download_from_url(
            url=zip_url, out_file_name=filename, out_dir=download_dir, unzip=True
        )

        pkg_dir = os.path.join(download_dir, repo_name + "-master")
        pkg_name = os.path.basename(url)
        work_dir = os.getcwd()
        os.chdir(pkg_dir)
        print("Installing {}...".format(pkg_name))
        cmd = "pip install ."
        os.system(cmd)
        os.chdir(work_dir)
        print("{} has been installed successfully.".format(pkg_name))
        # print("\nPlease comment out 'install_from_github()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        raise Exception(e)


def _check_git_install():
    """Checks if Git is installed.

    Returns:
        bool: Returns True if Git is installed, otherwise returns False.
    """
    import webbrowser

    cmd = "git --version"
    output = os.popen(cmd).read()

    if "git version" in output:
        return True
    else:
        url = "https://git-scm.com/downloads"
        print(
            "Git is not installed. Please download Git from {} and install it.".format(
                url
            )
        )
        webbrowser.open_new_tab(url)
        return False


def _clone_github_repo(url, out_dir):
    """Clones a GitHub repository.

    Args:
        url (str): The link to the GitHub repository
        out_dir (str): The output directory for the cloned repository.
    """

    repo_name = os.path.basename(url)
    # url_zip = os.path.join(url, 'archive/master.zip')
    url_zip = url + "/archive/master.zip"

    if os.path.exists(out_dir):
        print(
            "The specified output directory already exists. Please choose a new directory."
        )
        return

    parent_dir = os.path.dirname(out_dir)
    out_file_path = os.path.join(parent_dir, repo_name + ".zip")

    try:
        urllib.request.urlretrieve(url_zip, out_file_path)
    except Exception:
        print("The provided URL is invalid. Please double check the URL.")
        return

    with zipfile.ZipFile(out_file_path, "r") as zip_ref:
        zip_ref.extractall(parent_dir)

    src = out_file_path.replace(".zip", "-master")
    os.rename(src, out_dir)
    os.remove(out_file_path)


def _is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    return shutil.which(name) is not None


def random_string(string_length=3):
    """Generates a random string of fixed length.

    Args:
        string_length (int, optional): Fixed length. Defaults to 3.

    Returns:
        str: A random string
    """
    import random
    import string

    # random.seed(1001)
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(string_length))


def open_image_from_url(url):
    """Loads an image from the specified URL.

    Args:
        url (str): URL of the image.

    Returns:
        object: Image object.
    """
    from PIL import Image

    from io import BytesIO

    # from urllib.parse import urlparse

    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        print(e)


def show_image(img_path, width=None, height=None):
    """Shows an image within Jupyter notebook.

    Args:
        img_path (str): The image file path.
        width (int, optional): Width of the image in pixels. Defaults to None.
        height (int, optional): Height of the image in pixels. Defaults to None.

    """
    from IPython.display import display

    try:
        out = widgets.Output()
        # layout={'border': '1px solid black'})
        # layout={'border': '1px solid black', 'width': str(width + 20) + 'px', 'height': str(height + 10) + 'px'},)
        out.outputs = ()
        display(out)
        with out:
            file = open(img_path, "rb")
            image = file.read()
            if (width is None) and (height is None):
                display(widgets.Image(value=image))
            elif (width is not None) and (height is not None):
                display(widgets.Image(value=image, width=width, height=height))
            else:
                print("You need set both width and height.")
                return
    except Exception as e:
        print(e)


def show_html(html):
    """Shows HTML within Jupyter notebook.

    Args:
        html (str): File path or HTML string.

    Raises:
        FileNotFoundError: If the file does not exist.

    Returns:
        ipywidgets.HTML: HTML widget.
    """
    if os.path.exists(html):
        with open(html, "r") as f:
            content = f.read()

        widget = widgets.HTML(value=content)
        return widget
    else:
        try:
            widget = widgets.HTML(value=html)
            return widget
        except Exception as e:
            raise Exception(e)


def has_transparency(img):
    """Checks whether an image has transparency.

    Args:
        img (object):  a PIL Image object.

    Returns:
        bool: True if it has transparency, False otherwise.
    """

    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False


def upload_to_imgur(in_gif):
    """Uploads an image to imgur.com

    Args:
        in_gif (str): The file path to the image.
    """
    import subprocess

    pkg_name = "imgur-uploader"
    if not _is_tool(pkg_name):
        _check_install(pkg_name)

    try:
        IMGUR_API_ID = os.environ.get("IMGUR_API_ID", None)
        IMGUR_API_SECRET = os.environ.get("IMGUR_API_SECRET", None)
        credentials_path = os.path.join(
            os.path.expanduser("~"), ".config/imgur_uploader/uploader.cfg"
        )

        if (
            (IMGUR_API_ID is not None) and (IMGUR_API_SECRET is not None)
        ) or os.path.exists(credentials_path):
            proc = subprocess.Popen(["imgur-uploader", in_gif], stdout=subprocess.PIPE)
            for _ in range(0, 2):
                line = proc.stdout.readline()
                print(line.rstrip().decode("utf-8"))
            # while True:
            #     line = proc.stdout.readline()
            #     if not line:
            #         break
            #     print(line.rstrip().decode("utf-8"))
        else:
            print(
                "Imgur API credentials could not be found. Please check https://pypi.org/project/imgur-uploader/ for instructions on how to get Imgur API credentials"
            )
            return

    except Exception as e:
        raise Exception(e)


def rgb_to_hex(rgb=(255, 255, 255)):
    """Converts RGB to hex color. In RGB color R stands for Red, G stands for Green, and B stands for Blue, and it ranges from the decimal value of 0 – 255.

    Args:
        rgb (tuple, optional): RGB color code as a tuple of (red, green, blue). Defaults to (255, 255, 255).

    Returns:
        str: hex color code
    """
    return "%02x%02x%02x" % rgb


def hex_to_rgb(value="FFFFFF"):
    """Converts hex color to RGB color.

    Args:
        value (str, optional): Hex color code as a string. Defaults to 'FFFFFF'.

    Returns:
        tuple: RGB color as a tuple.
    """
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def check_color(in_color):
    """Checks the input color and returns the corresponding hex color code.

    Args:
        in_color (str or tuple): It can be a string (e.g., 'red', '#ffff00', 'ffff00', 'ff0') or RGB tuple (e.g., (255, 127, 0)).

    Returns:
        str: A hex color code.
    """
    import colour

    out_color = "#000000"  # default black color
    if isinstance(in_color, tuple) and len(in_color) == 3:
        # rescale color if necessary
        if all(isinstance(item, int) for item in in_color):
            in_color = [c / 255.0 for c in in_color]

        return colour.Color(rgb=tuple(in_color)).hex_l

    else:
        # try to guess the color system
        try:
            return colour.Color(in_color).hex_l

        except Exception as e:
            pass

        # try again by adding an extra # (GEE handle hex codes without #)
        try:
            return colour.Color(f"#{in_color}").hex_l

        except Exception as e:
            print(
                f"The provided color ({in_color}) is invalid. Using the default black color."
            )
            print(e)

        return out_color


def system_fonts(show_full_path=False):
    """Gets a list of system fonts

        # Common font locations:
        # Linux: /usr/share/fonts/TTF/
        # Windows: C:/Windows/Fonts
        # macOS:  System > Library > Fonts

    Args:
        show_full_path (bool, optional): Whether to show the full path of each system font. Defaults to False.

    Returns:
        list: A list of system fonts.
    """
    try:
        import matplotlib.font_manager

        font_list = matplotlib.font_manager.findSystemFonts(
            fontpaths=None, fontext="ttf"
        )
        font_list.sort()

        font_names = [os.path.basename(f) for f in font_list]
        font_names.sort()

        if show_full_path:
            return font_list
        else:
            return font_names

    except Exception as e:
        raise Exception(e)


def download_from_url(url, out_file_name=None, out_dir=".", unzip=True, verbose=True):
    """Download a file from a URL (e.g., https://github.com/opengeos/whitebox-python/raw/master/examples/testdata.zip)

    Args:
        url (str): The HTTP URL to download.
        out_file_name (str, optional): The output file name to use. Defaults to None.
        out_dir (str, optional): The output directory to use. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the downloaded file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    in_file_name = os.path.basename(url)
    out_dir = check_dir(out_dir)

    if out_file_name is None:
        out_file_name = in_file_name
    out_file_path = os.path.join(out_dir, out_file_name)

    if verbose:
        print("Downloading {} ...".format(url))

    try:
        urllib.request.urlretrieve(url, out_file_path)
    except Exception:
        raise Exception("The URL is invalid. Please double check the URL.")

    final_path = out_file_path

    if unzip:
        # if it is a zip file
        if ".zip" in out_file_name:
            if verbose:
                print("Unzipping {} ...".format(out_file_name))
            with zipfile.ZipFile(out_file_path, "r") as zip_ref:
                zip_ref.extractall(out_dir)
            final_path = os.path.join(
                os.path.abspath(out_dir), out_file_name.replace(".zip", "")
            )

        # if it is a tar file
        if ".tar" in out_file_name:
            if verbose:
                print("Unzipping {} ...".format(out_file_name))
            with tarfile.open(out_file_path, "r") as tar_ref:
                with tarfile.open(out_file_path, "r") as tar_ref:

                    def is_within_directory(directory, target):
                        abs_directory = os.path.abspath(directory)
                        abs_target = os.path.abspath(target)

                        prefix = os.path.commonprefix([abs_directory, abs_target])

                        return prefix == abs_directory

                    def safe_extract(
                        tar, path=".", members=None, *, numeric_owner=False
                    ):
                        for member in tar.getmembers():
                            member_path = os.path.join(path, member.name)
                            if not is_within_directory(path, member_path):
                                raise Exception("Attempted Path Traversal in Tar File")

                        tar.extractall(path, members, numeric_owner=numeric_owner)

                    safe_extract(tar_ref, out_dir)

            final_path = os.path.join(
                os.path.abspath(out_dir), out_file_name.replace(".tart", "")
            )

    if verbose:
        print("Data downloaded to: {}".format(final_path))


def download_from_gdrive(gfile_url, file_name, out_dir=".", unzip=True, verbose=True):
    """Download a file shared via Google Drive
       (e.g., https://drive.google.com/file/d/18SUo_HcDGltuWYZs1s7PpOmOq_FvFn04/view?usp=sharing)

    Args:
        gfile_url (str): The Google Drive shared file URL
        file_name (str): The output file name to use.
        out_dir (str, optional): The output directory. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the output file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    try:
        from google_drive_downloader import GoogleDriveDownloader as gdd
    except ImportError:
        raise ImportError(
            'Please install googledrivedownloader using "pip install googledrivedownloader"'
        )

    file_id = gfile_url.split("/")[5]
    if verbose:
        print("Google Drive file id: {}".format(file_id))

    out_dir = check_dir(out_dir)
    dest_path = os.path.join(out_dir, file_name)
    gdd.download_file_from_google_drive(file_id, dest_path, True, unzip)


def create_download_link(filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578

    Args:
        filename (str): The file path to the file to download
        title (str, optional): str. Defaults to "Click here to download: ".

    Returns:
        str: HTML download URL.
    """
    import base64
    from IPython.display import HTML

    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()
    basename = os.path.basename(filename)
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" style="color:#0000FF;" target="_blank">{title}</a>'
    html = html.format(payload=payload, title=title + f" {basename}", filename=basename)
    return HTML(html)


def edit_download_html(htmlWidget, filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578#issuecomment-617668058

    Args:
        htmlWidget (object): The HTML widget to display the URL.
        filename (str): File path to download.
        title (str, optional): Download description. Defaults to "Click here to download: ".
    """

    # from IPython.display import HTML
    # import ipywidgets as widgets
    import base64

    # Change widget html temporarily to a font-awesome spinner
    htmlWidget.value = '<i class="fa fa-spinner fa-spin fa-2x fa-fw"></i><span class="sr-only">Loading...</span>'

    # Process raw data
    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()

    basename = os.path.basename(filename)

    # Create and assign html to widget
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    htmlWidget.value = html.format(
        payload=payload, title=title + basename, filename=basename
    )


def csv_points_to_shp(in_csv, out_shp, latitude="latitude", longitude="longitude"):
    """Converts a csv file containing points (latitude, longitude) into a shapefile.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/opengeos/data/main/world/world_cities.csv
        out_shp (str): File path to the output shapefile.
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    """

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_name = os.path.basename(in_csv)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir)
        in_csv = os.path.join(out_dir, out_name)

    wbt = whitebox.WhiteboxTools()
    in_csv = os.path.abspath(in_csv)
    out_shp = os.path.abspath(out_shp)

    if not os.path.exists(in_csv):
        raise Exception("The provided csv file does not exist.")

    with open(in_csv, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fields = reader.fieldnames
        xfield = fields.index(longitude)
        yfield = fields.index(latitude)

    wbt.csv_points_to_vector(in_csv, out_shp, xfield=xfield, yfield=yfield, epsg=4326)


def csv_to_shp(
    in_csv, out_shp, latitude="latitude", longitude="longitude", encoding="utf-8"
):
    """Converts a csv file with latlon info to a point shapefile.

    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
    """
    import shapefile as shp

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        in_csv = github_raw_url(in_csv)
        in_csv = download_file(in_csv, quiet=True, overwrite=True)

    try:
        points = shp.Writer(out_shp, shapeType=shp.POINT)
        with open(in_csv, encoding=encoding) as csvfile:
            csvreader = csv.DictReader(csvfile)
            header = csvreader.fieldnames
            [points.field(field) for field in header]
            for row in csvreader:
                points.point((float(row[longitude])), (float(row[latitude])))
                points.record(*tuple([row[f] for f in header]))

        out_prj = out_shp.replace(".shp", ".prj")
        with open(out_prj, "w") as f:
            prj_str = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]] '
            f.write(prj_str)

    except Exception as e:
        raise Exception(e)


def df_to_geojson(
    df,
    out_geojson=None,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
):
    """Creates points for a Pandas DataFrame and exports data as a GeoJSON.

    Args:
        df (pandas.DataFrame): The input Pandas DataFrame.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """

    import json
    from geojson import Feature, FeatureCollection, Point

    if out_geojson is not None:
        out_dir = os.path.dirname(os.path.abspath(out_geojson))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    features = df.apply(
        lambda row: Feature(
            geometry=Point((float(row[longitude]), float(row[latitude]))),
            properties=dict(row),
        ),
        axis=1,
    ).tolist()

    geojson = FeatureCollection(features=features)

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding=encoding) as f:
            f.write(json.dumps(geojson))


def csv_to_geojson(
    in_csv,
    out_geojson=None,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
):
    """Creates points for a CSV file and exports data as a GeoJSON.

    Args:
        in_csv (str): The file path to the input CSV file.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """

    import pandas as pd

    in_csv = github_raw_url(in_csv)

    if out_geojson is not None:
        out_geojson = check_file_path(out_geojson)

    df = pd.read_csv(in_csv)
    geojson = df_to_geojson(
        df, latitude=latitude, longitude=longitude, encoding=encoding
    )

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding=encoding) as f:
            f.write(json.dumps(geojson))


def csv_to_gdf(in_csv, latitude="latitude", longitude="longitude", encoding="utf-8"):
    """Creates points for a CSV file and converts them to a GeoDataFrame.

    Args:
        in_csv (str): The file path to the input CSV file.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    Returns:
        object: GeoDataFrame.
    """

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    out_dir = os.getcwd()

    out_geojson = os.path.join(out_dir, random_string() + ".geojson")
    csv_to_geojson(in_csv, out_geojson, latitude, longitude, encoding)

    gdf = gpd.read_file(out_geojson)
    os.remove(out_geojson)
    return gdf


def csv_to_vector(
    in_csv,
    output,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
    **kwargs,
):
    """Creates points for a CSV file and converts them to a vector dataset.

    Args:
        in_csv (str): The file path to the input CSV file.
        output (str): The file path to the output vector dataset.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """
    gdf = csv_to_gdf(in_csv, latitude, longitude, encoding)
    gdf.to_file(output, **kwargs)


def create_code_cell(code="", where="below"):
    """Creates a code cell in the IPython Notebook.

    Args:
        code (str, optional): Code to fill the new code cell with. Defaults to ''.
        where (str, optional): Where to add the new code cell. It can be one of the following: above, below, at_bottom. Defaults to 'below'.
    """

    import base64
    from IPython.display import Javascript, display

    encoded_code = (base64.b64encode(str.encode(code))).decode()
    display(
        Javascript(
            """
        var code = IPython.notebook.insert_cell_{0}('code');
        code.set_text(atob("{1}"));
    """.format(
                where, encoded_code
            )
        )
    )


def local_tile_pixel_value(
    lon,
    lat,
    tile_client,
    verbose=True,
    **kwargs,
):
    """Get pixel value from COG.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a COG, e.g., 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'
        bidx (str, optional): Dataset band indexes (e.g bidx=1, bidx=1&bidx=2&bidx=3). Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        verbose (bool, optional): Print status messages. Defaults to True.

    Returns:
        list: A dictionary of band info.
    """

    r = tile_client.pixel(lat, lon, units="EPSG:4326", **kwargs)
    if "bands" in r:
        return r["bands"]
    else:
        if verbose:
            print("No pixel value found.")
        return None


def local_tile_vmin_vmax(
    source,
    bands=None,
    **kwargs,
):
    """Get vmin and vmax from COG.

    Args:
        source (str | TileClient): A local COG file path or TileClient object.
        bands (str | list, optional): A list of band names. Defaults to None.

    Raises:
        ValueError: If source is not a TileClient object or a local COG file path.

    Returns:
        tuple: A tuple of vmin and vmax.
    """
    check_package("localtileserver", "https://github.com/banesullivan/localtileserver")
    from localtileserver import TileClient

    if isinstance(source, str):
        tile_client = TileClient(source)
    elif isinstance(source, TileClient):
        tile_client = source
    else:
        raise ValueError("source must be a string or TileClient object.")

    stats = tile_client.metadata()["bands"]
    bandnames = list(stats.keys())

    if isinstance(bands, str):
        bands = [bands]
    elif isinstance(bands, list):
        pass
    elif bands is None:
        bands = bandnames

    if all(b in bandnames for b in bands):
        vmin = min([stats[b]["min"] for b in bands])
        vmax = max([stats[b]["max"] for b in bands])
    else:
        vmin = min([stats[b]["min"] for b in bandnames])
        vmax = max([stats[b]["max"] for b in bandnames])
    return vmin, vmax


def local_tile_bands(source):
    """Get band names from COG.

    Args:
        source (str | TileClient): A local COG file path or TileClient

    Returns:
        list: A list of band names.
    """
    check_package("localtileserver", "https://github.com/banesullivan/localtileserver")
    from localtileserver import TileClient

    if isinstance(source, str):
        tile_client = TileClient(source)
    elif isinstance(source, TileClient):
        tile_client = source
    else:
        raise ValueError("source must be a string or TileClient object.")

    bandnames = list(tile_client.metadata()["bands"].keys())
    return bandnames


def bbox_to_geojson(bounds):
    """Convert coordinates of a bounding box to a geojson.

    Args:
        bounds (list | tuple): A list of coordinates representing [left, bottom, right, top] or m.bounds.

    Returns:
        dict: A geojson feature.
    """

    if isinstance(bounds, tuple) and len(bounds) == 2:
        bounds = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]

    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [bounds[0], bounds[3]],
                    [bounds[0], bounds[1]],
                    [bounds[2], bounds[1]],
                    [bounds[2], bounds[3]],
                    [bounds[0], bounds[3]],
                ]
            ],
        },
        "type": "Feature",
    }


def coords_to_geojson(coords):
    """Convert a list of bbox coordinates representing [left, bottom, right, top] to geojson FeatureCollection.

    Args:
        coords (list): A list of bbox coordinates representing [left, bottom, right, top].

    Returns:
        dict: A geojson FeatureCollection.
    """

    features = []
    for bbox in coords:
        features.append(bbox_to_geojson(bbox))
    return {"type": "FeatureCollection", "features": features}


def explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield
    coordinate tuples. As long as the input is conforming, the type of
    the geometry doesn't matter.  From Fiona 1.4.8

    Args:
        coords (list): A list of coordinates.

    Yields:
        [type]: [description]
    """

    for e in coords:
        if isinstance(e, (float, int)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def get_bounds(geometry, north_up=True, transform=None):
    """Bounding box of a GeoJSON geometry, GeometryCollection, or FeatureCollection.
    left, bottom, right, top
    *not* xmin, ymin, xmax, ymax
    If not north_up, y will be switched to guarantee the above.
    Source code adapted from https://github.com/mapbox/rasterio/blob/master/rasterio/features.py#L361

    Args:
        geometry (dict): A GeoJSON dict.
        north_up (bool, optional): . Defaults to True.
        transform ([type], optional): . Defaults to None.

    Returns:
        list: A list of coordinates representing [left, bottom, right, top]
    """

    if "bbox" in geometry:
        return tuple(geometry["bbox"])

    geometry = geometry.get("geometry") or geometry

    # geometry must be a geometry, GeometryCollection, or FeatureCollection
    if not (
        "coordinates" in geometry or "geometries" in geometry or "features" in geometry
    ):
        raise ValueError(
            "geometry must be a GeoJSON-like geometry, GeometryCollection, "
            "or FeatureCollection"
        )

    if "features" in geometry:
        # Input is a FeatureCollection
        xmins = []
        ymins = []
        xmaxs = []
        ymaxs = []
        for feature in geometry["features"]:
            xmin, ymin, xmax, ymax = get_bounds(feature["geometry"])
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        if north_up:
            return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
        else:
            return min(xmins), max(ymaxs), max(xmaxs), min(ymins)

    elif "geometries" in geometry:
        # Input is a geometry collection
        xmins = []
        ymins = []
        xmaxs = []
        ymaxs = []
        for geometry in geometry["geometries"]:
            xmin, ymin, xmax, ymax = get_bounds(geometry)
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        if north_up:
            return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
        else:
            return min(xmins), max(ymaxs), max(xmaxs), min(ymins)

    elif "coordinates" in geometry:
        # Input is a singular geometry object
        if transform is not None:
            xyz = list(explode(geometry["coordinates"]))
            xyz_px = [transform * point for point in xyz]
            xyz = tuple(zip(*xyz_px))
            return min(xyz[0]), max(xyz[1]), max(xyz[0]), min(xyz[1])
        else:
            xyz = tuple(zip(*list(explode(geometry["coordinates"]))))
            if north_up:
                return min(xyz[0]), min(xyz[1]), max(xyz[0]), max(xyz[1])
            else:
                return min(xyz[0]), max(xyz[1]), max(xyz[0]), min(xyz[1])

    # all valid inputs returned above, so whatever falls through is an error
    raise ValueError(
        "geometry must be a GeoJSON-like geometry, GeometryCollection, "
        "or FeatureCollection"
    )


def get_center(geometry, north_up=True, transform=None):
    """Get the centroid of a GeoJSON.

    Args:
        geometry (dict): A GeoJSON dict.
        north_up (bool, optional): . Defaults to True.
        transform ([type], optional): . Defaults to None.

    Returns:
        list: [lon, lat]
    """
    bounds = get_bounds(geometry, north_up, transform)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def adjust_longitude(in_fc):
    """Adjusts longitude if it is less than -180 or greater than 180.

    Args:
        in_fc (dict): The input dictionary containing coordinates.

    Returns:
        dict: A dictionary containing the converted longitudes
    """
    try:
        keys = in_fc.keys()

        if "geometry" in keys:
            coordinates = in_fc["geometry"]["coordinates"]

            if in_fc["geometry"]["type"] == "Point":
                longitude = coordinates[0]
                if longitude < -180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc["geometry"]["coordinates"][0] = longitude

            elif in_fc["geometry"]["type"] == "Polygon":
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < -180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc["geometry"]["coordinates"][index1][index2][0] = longitude

            elif in_fc["geometry"]["type"] == "LineString":
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < -180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc["geometry"]["coordinates"][index][0] = longitude

        elif "type" in keys:
            coordinates = in_fc["coordinates"]

            if in_fc["type"] == "Point":
                longitude = coordinates[0]
                if longitude < -180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc["coordinates"][0] = longitude

            elif in_fc["type"] == "Polygon":
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < -180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc["coordinates"][index1][index2][0] = longitude

            elif in_fc["type"] == "LineString":
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < -180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc["coordinates"][index][0] = longitude

        return in_fc

    except Exception as e:
        print(e)
        return None


def is_GCS(in_shp):
    import warnings
    import pycrs

    if not os.path.exists(in_shp):
        raise FileNotFoundError("The input shapefile could not be found.")

    if not in_shp.endswith(".shp"):
        raise TypeError("The input shapefile is invalid.")

    in_prj = in_shp.replace(".shp", ".prj")

    if not os.path.exists(in_prj):
        warnings.warn(
            f"The projection file {in_prj} could not be found. Assuming the dataset is in a geographic coordinate system (GCS)."
        )
        return True
    else:
        with open(in_prj) as f:
            esri_wkt = f.read()
        epsg4326 = pycrs.parse.from_epsg_code(4326).to_proj4()
        try:
            crs = pycrs.parse.from_esri_wkt(esri_wkt).to_proj4()
            if crs == epsg4326:
                return True
            else:
                return False
        except Exception:
            return False


def kml_to_shp(in_kml, out_shp):
    """Converts a KML to shapefile.

    Args:
        in_kml (str): The file path to the input KML.
        out_shp (str): The file path to the output shapefile.

    Raises:
        FileNotFoundError: The input KML could not be found.
        TypeError: The output must be a shapefile.
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    out_shp = os.path.abspath(out_shp)
    if not out_shp.endswith(".shp"):
        raise TypeError("The output must be a shapefile.")

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd
    import fiona

    # print(fiona.supported_drivers)
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    df = gpd.read_file(in_kml, driver="KML")
    df.to_file(out_shp)


def kml_to_geojson(in_kml, out_geojson=None):
    """Converts a KML to GeoJSON.

    Args:
        in_kml (str): The file path to the input KML.
        out_geojson (str): The file path to the output GeoJSON. Defaults to None.

    Raises:
        FileNotFoundError: The input KML could not be found.
        TypeError: The output must be a GeoJSON.
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    if out_geojson is not None:
        out_geojson = os.path.abspath(out_geojson)
        ext = os.path.splitext(out_geojson)[1].lower()
        if ext not in [".json", ".geojson"]:
            raise TypeError("The output file must be a GeoJSON.")

        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd
    import fiona

    # import fiona
    # print(fiona.supported_drivers)
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    gdf = gpd.read_file(in_kml, driver="KML")

    if out_geojson is not None:
        gdf.to_file(out_geojson, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def csv_to_df(in_csv, **kwargs):
    """Converts a CSV file to pandas dataframe.

    Args:
        in_csv (str): File path to the input CSV.

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    import pandas as pd

    try:
        return pd.read_csv(in_csv, **kwargs)
    except Exception as e:
        raise Exception(e)


def shp_to_gdf(in_shp):
    """Converts a shapefile to Geopandas dataframe.

    Args:
        in_shp (str): File path to the input shapefile.

    Raises:
        FileNotFoundError: The provided shp could not be found.

    Returns:
        gpd.GeoDataFrame: geopandas.GeoDataFrame
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_shp = os.path.abspath(in_shp)
    if not os.path.exists(in_shp):
        raise FileNotFoundError("The provided shp could not be found.")

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    try:
        return gpd.read_file(in_shp)
    except Exception as e:
        raise Exception(e)


def shp_to_geojson(in_shp, output=None, encoding="utf-8", crs="EPSG:4326", **kwargs):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        output (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    try:
        import geopandas as gpd

        gdf = gpd.read_file(in_shp, **kwargs)
        gdf.to_crs(crs, inplace=True)
        if output is None:
            return gdf.__geo_interface__
        else:
            gdf.to_file(output, driver="GeoJSON")
    except Exception as e:
        raise Exception(e)


def delete_shp(in_shp, verbose=False):
    """Deletes a shapefile.

    Args:
        in_shp (str): The input shapefile to delete.
        verbose (bool, optional): Whether to print out descriptive text. Defaults to True.
    """
    from pathlib import Path

    in_shp = os.path.abspath(in_shp)
    in_dir = os.path.dirname(in_shp)
    basename = os.path.basename(in_shp).replace(".shp", "")

    files = Path(in_dir).rglob(basename + ".*")

    for file in files:
        filepath = os.path.join(in_dir, str(file))
        os.remove(filepath)
        if verbose:
            print(f"Deleted {filepath}")


def vector_to_geojson(
    filename,
    out_geojson=None,
    bbox=None,
    mask=None,
    rows=None,
    epsg="4326",
    encoding="utf-8",
    **kwargs,
):
    """Converts any geopandas-supported vector dataset to GeoJSON.

    Args:
        filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
        out_geojson (str, optional): The file path to the output GeoJSON. Defaults to None.
        bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
        mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
        rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
        epsg (str, optional): The EPSG number to convert to. Defaults to "4326".
        encoding (str, optional): The encoding of the input file. Defaults to "utf-8".


    Raises:
        ValueError: When the output file path is invalid.

    Returns:
        dict: A dictionary containing the GeoJSON.
    """
    import warnings

    warnings.filterwarnings("ignore")
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd
    import fiona

    if not filename.startswith("http"):
        filename = os.path.abspath(filename)
        if filename.endswith(".zip"):
            filename = "zip://" + filename
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        df = gpd.read_file(
            filename,
            bbox=bbox,
            mask=mask,
            rows=rows,
            driver="KML",
            encoding=encoding,
            **kwargs,
        )
    else:
        df = gpd.read_file(
            filename, bbox=bbox, mask=mask, rows=rows, encoding=encoding, **kwargs
        )
    gdf = df.to_crs(epsg=epsg)

    if out_geojson is not None:
        if not out_geojson.lower().endswith(".geojson"):
            raise ValueError("The output file must have a geojson file extension.")

        out_geojson = os.path.abspath(out_geojson)
        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        gdf.to_file(out_geojson, driver="GeoJSON")

    else:
        return gdf.__geo_interface__


def screen_capture(outfile, monitor=1):
    """Takes a full screenshot of the selected monitor.

    Args:
        outfile (str): The output file path to the screenshot.
        monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
    """
    try:
        from mss import mss
    except ImportError:
        raise ImportError("Please install mss using 'pip install mss'")

    out_dir = os.path.dirname(outfile)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not isinstance(monitor, int):
        print("The monitor number must be an integer.")
        return

    try:
        with mss() as sct:
            sct.shot(output=outfile, mon=monitor)
            return outfile

    except Exception as e:
        raise Exception(e)


def gdf_to_geojson(
    gdf, out_geojson=None, epsg=None, tuple_to_list=False, encoding="utf-8"
):
    """Converts a GeoDataFame to GeoJSON.

    Args:
        gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        out_geojson (str, optional): File path to he output GeoJSON. Defaults to None.
        epsg (str, optional): An EPSG string, e.g., "4326". Defaults to None.
        tuple_to_list (bool, optional): Whether to convert tuples to lists. Defaults to False.
        encoding (str, optional): The encoding to use for the GeoJSON. Defaults to "utf-8".

    Raises:
        TypeError: When the output file extension is incorrect.
        Exception: When the conversion fails.

    Returns:
        dict: When the out_json is None returns a dict.
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    def listit(t):
        return list(map(listit, t)) if isinstance(t, (list, tuple)) else t

    try:
        if epsg is not None:
            if gdf.crs is not None and gdf.crs.to_epsg() != epsg:
                gdf = gdf.to_crs(epsg=epsg)
        geojson = gdf.__geo_interface__

        if tuple_to_list:
            for feature in geojson["features"]:
                feature["geometry"]["coordinates"] = listit(
                    feature["geometry"]["coordinates"]
                )

        if out_geojson is None:
            return geojson
        else:
            ext = os.path.splitext(out_geojson)[1]
            if ext.lower() not in [".json", ".geojson"]:
                raise TypeError(
                    "The output file extension must be either .json or .geojson"
                )
            out_dir = os.path.dirname(out_geojson)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            gdf.to_file(out_geojson, driver="GeoJSON", encoding=encoding)
    except Exception as e:
        raise Exception(e)


def connect_postgis(
    database, host="localhost", user=None, password=None, port=5432, use_env_var=False
):
    """Connects to a PostGIS database.

    Args:
        database (str): Name of the database
        host (str, optional): Hosting server for the database. Defaults to "localhost".
        user (str, optional): User name to access the database. Defaults to None.
        password (str, optional): Password to access the database. Defaults to None.
        port (int, optional): Port number to connect to at the server host. Defaults to 5432.
        use_env_var (bool, optional): Whether to use environment variables. It set to True, user and password are treated as an environment variables with default values user="SQL_USER" and password="SQL_PASSWORD". Defaults to False.

    Raises:
        ValueError: If user is not specified.
        ValueError: If password is not specified.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    check_package(
        name="sqlalchemy",
        URL="https://docs.sqlalchemy.org/en/14/intro.html#installation",
    )

    from sqlalchemy import create_engine

    if use_env_var:
        if user is not None:
            user = os.getenv(user)
        else:
            user = os.getenv("SQL_USER")

        if password is not None:
            password = os.getenv(password)
        else:
            password = os.getenv("SQL_PASSWORD")

        if user is None:
            raise ValueError("user is not specified.")
        if password is None:
            raise ValueError("password is not specified.")

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(connection_string)

    return engine


def read_postgis(sql, con, geom_col="geom", crs=None, **kwargs):
    """Reads data from a PostGIS database and returns a GeoDataFrame.

    Args:
        sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
        con (sqlalchemy.engine.Engine): Active connection to the database to query.
        geom_col (str, optional): Column name to convert to shapely geometries. Defaults to "geom".
        crs (str | dict, optional): CRS to use for the returned GeoDataFrame; if not set, tries to determine CRS from the SRID associated with the first geometry in the database, and assigns that to all geometries. Defaults to None.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    gdf = gpd.read_postgis(sql, con, geom_col, crs, **kwargs)
    return gdf


def vector_col_names(filename, **kwargs):
    """Retrieves the column names of a vector attribute table.

    Args:
        filename (str): The input file path.

    Returns:
        list: The list of column names.
    """
    import warnings

    warnings.filterwarnings("ignore")
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd
    import fiona

    if not filename.startswith("http"):
        filename = os.path.abspath(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        gdf = gpd.read_file(filename, driver="KML", **kwargs)
    else:
        gdf = gpd.read_file(filename, **kwargs)
    col_names = gdf.columns.values.tolist()
    return col_names


def get_api_key(token_name, m=None):
    """Retrieves an API key based on a system environmen variable.

    Args:
        token_name (str): The token name.
        m (ipyleaflet.Map | folium.Map, optional): A Map instance. Defaults to None.

    Returns:
        str: The API key.
    """
    api_key = os.environ.get(token_name)
    if m is not None and token_name in m.api_keys:
        api_key = m.api_keys[token_name]

    return api_key


def set_api_key(token_name, api_key, m=None):
    """Sets an API key as an environment variable.

    Args:
        token_name (str): The token name.
        api_key (str): The API key.
        m (ipyleaflet.Map | folium.Map, optional): A Map instance.. Defaults to None.
    """
    os.environ[token_name] = api_key
    if m is not None:
        m.api_keys[token_name] = api_key


def planet_monthly_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    links = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2020, year_now + 1):
        for month in range(1, 13):
            m_str = str(year) + "-" + str(month).zfill(2)

            if year == 2020 and month < 9:
                continue
            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            links.append(url)

    return links


def planet_biannual_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    dates = [
        "2015-12_2016-05",
        "2016-06_2016-11",
        "2016-12_2017-05",
        "2017-06_2017-11",
        "2017-12_2018-05",
        "2018-06_2018-11",
        "2018-12_2019-05",
        "2019-06_2019-11",
        "2019-12_2020-05",
        "2020-06_2020-08",
    ]

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for d in dates:
        url = f"{prefix}{d}{subfix}{api_key}"
        link.append(url)

    return link


def planet_catalog_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Returns:
        list: A list of tile URLs.
    """
    biannual = planet_biannual_tropical(api_key, token_name)
    monthly = planet_monthly_tropical(api_key, token_name)
    return biannual + monthly


def planet_monthly_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly_tropical(api_key, token_name)
    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_biannual_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  bi-annual imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_biannual_tropical(api_key, token_name)
    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 15]
        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )
        tiles[name] = tile

    return tiles


def planet_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    catalog = {}
    biannul = planet_biannual_tiles_tropical(api_key, token_name, tile_format)
    monthly = planet_monthly_tiles_tropical(api_key, token_name, tile_format)

    for key in biannul:
        catalog[key] = biannul[key]

    for key in monthly:
        catalog[key] = monthly[key]

    return catalog


def planet_monthly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):
        for month in range(1, 13):
            m_str = str(year) + "_" + str(month).zfill(2)

            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_quarterly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet quarterly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):
        for quarter in range(1, 5):
            m_str = str(year) + "q" + str(quarter)

            if year == year_now and quarter >= quarter_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_catalog(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Returns:
        list: A list of tile URLs.
    """
    quarterly = planet_quarterly(api_key, token_name)
    monthly = planet_monthly(api_key, token_name)
    return quarterly + monthly


def planet_monthly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly(api_key, token_name)

    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_quarterly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    links = planet_quarterly(api_key, token_name)

    for url in links:
        index = url.find("20")
        name = "Planet_" + url[index : index + 6]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_tiles(api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"):
    """Generates Planet imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    catalog = {}
    quarterly = planet_quarterly_tiles(api_key, token_name, tile_format)
    monthly = planet_monthly_tiles(api_key, token_name, tile_format)

    for key in quarterly:
        catalog[key] = quarterly[key]

    for key in monthly:
        catalog[key] = monthly[key]

    return catalog


def planet_by_quarter(
    year=2016,
    quarter=1,
    api_key=None,
    token_name="PLANET_API_KEY",
):
    """Gets Planet global mosaic tile url by quarter. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: The Planet API key is not provided.
        ValueError: The year is invalid.
        ValueError: The quarter is invalid.
        ValueError: The quarter is invalid.

    Returns:
        str: A Planet global mosaic tile url.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    if year > year_now:
        raise ValueError(f"Year must be between 2016 and {year_now}.")
    elif year == year_now and quarter >= quarter_now:
        raise ValueError(f"Quarter must be less than {quarter_now} for year {year_now}")

    if quarter < 1 or quarter > 4:
        raise ValueError("Quarter must be between 1 and 4.")

    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    m_str = str(year) + "q" + str(quarter)
    url = f"{prefix}{m_str}{subfix}{api_key}"

    return url


def planet_by_month(
    year=2016,
    month=1,
    api_key=None,
    token_name="PLANET_API_KEY",
):
    """Gets Planet global mosaic tile url by month. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: The Planet API key is not provided.
        ValueError: The year is invalid.
        ValueError: The month is invalid.
        ValueError: The month is invalid.

    Returns:
        str: A Planet global mosaic tile url.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    # quarter_now = (month_now - 1) // 3 + 1

    if year > year_now:
        raise ValueError(f"Year must be between 2016 and {year_now}.")
    elif year == year_now and month >= month_now:
        raise ValueError(f"Month must be less than {month_now} for year {year_now}")

    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    m_str = str(year) + "_" + str(month).zfill(2)
    url = f"{prefix}{m_str}{subfix}{api_key}"

    return url


def planet_tile_by_quarter(
    year=2016,
    quarter=1,
    name=None,
    api_key=None,
    token_name="PLANET_API_KEY",
    tile_format="ipyleaflet",
):
    """Generates Planet quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
        name (str, optional): The layer name to use. Defaults to None.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    url = planet_by_quarter(year, quarter, api_key, token_name)

    if name is None:
        name = "Planet_" + str(year) + "_q" + str(quarter)

    if tile_format == "ipyleaflet":
        tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
    else:
        tile = folium.TileLayer(
            tiles=url,
            attr="Planet",
            name=name,
            overlay=True,
            control=True,
        )

    return tile


def planet_tile_by_month(
    year=2016,
    month=1,
    name=None,
    api_key=None,
    token_name="PLANET_API_KEY",
    tile_format="ipyleaflet",
):
    """Generates Planet monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
        name (str, optional): The layer name to use. Defaults to None.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    url = planet_by_month(year, month, api_key, token_name)

    if name is None:
        name = "Planet_" + str(year) + "_" + str(month).zfill(2)

    if tile_format == "ipyleaflet":
        tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
    else:
        tile = folium.TileLayer(
            tiles=url,
            attr="Planet",
            name=name,
            overlay=True,
            control=True,
        )

    return tile


def basemap_xyz_tiles():
    """Returns a dictionary containing a set of basemaps that are XYZ tile layers.

    Returns:
        dict: A dictionary of XYZ tile layers.
    """
    from .leafmap import basemaps

    layers_dict = {}
    keys = dict(basemaps).keys()
    for key in keys:
        if isinstance(basemaps[key], ipyleaflet.WMSLayer):
            pass
        else:
            layers_dict[key] = basemaps[key]
    return layers_dict


def to_hex_colors(colors):
    """Adds # to a list of hex color codes.

    Args:
        colors (list): A list of hex color codes.

    Returns:
        list: A list of hex color codes prefixed with #.
    """
    result = all([len(color.strip()) == 6 for color in colors])
    if result:
        return ["#" + color.strip() for color in colors]
    else:
        return colors


def display_html(src, width=950, height=600):
    """Display an HTML file in a Jupyter Notebook.

    Args
        src (str): File path to HTML file.
        width (int, optional): Width of the map. Defaults to 950.
        height (int, optional): Height of the map. Defaults to 600.
    """
    if not os.path.isfile(src):
        raise ValueError(f"{src} is not a valid file path.")
    display(IFrame(src=src, width=width, height=height))


def get_census_dict(reset=False):
    """Returns a dictionary of Census data.

    Args:
        reset (bool, optional): Reset the dictionary. Defaults to False.

    Returns:
        dict: A dictionary of Census data.
    """
    import json
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("leafmap", "leafmap.py"))
    census_data = os.path.join(pkg_dir, "data/census_data.json")

    if reset:
        try:
            from owslib.wms import WebMapService
        except ImportError:
            raise ImportError("Please install owslib using 'pip install owslib'.")

        census_dict = {}

        names = [
            "Current",
            "ACS 2021",
            "ACS 2019",
            "ACS 2018",
            "ACS 2017",
            "ACS 2016",
            "ACS 2015",
            "ACS 2014",
            "ACS 2013",
            "ACS 2012",
            "ECON 2012",
            "Census 2020",
            "Census 2010",
            "Physical Features",
            "Decennial Census 2020",
            "Decennial Census 2010",
            "Decennial Census 2000",
            "Decennial Physical Features",
        ]

        links = {}

        print("Retrieving data. Please wait ...")
        for name in names:
            if "Decennial" not in name:
                links[
                    name
                ] = f"https://tigerweb.geo.census.gov/arcgis/services/TIGERweb/tigerWMS_{name.replace(' ', '')}/MapServer/WMSServer"
            else:
                links[
                    name
                ] = f"https://tigerweb.geo.census.gov/arcgis/services/Census2020/tigerWMS_{name.replace('Decennial', '').replace(' ', '')}/MapServer/WMSServer"

            wms = WebMapService(links[name], timeout=300)
            layers = list(wms.contents)
            layers.sort()
            census_dict[name] = {
                "url": links[name],
                "layers": layers,
                # "title": wms.identification.title,
                # "abstract": wms.identification.abstract,
            }

        with open(census_data, "w") as f:
            json.dump(census_dict, f, indent=4)

    else:
        with open(census_data, "r") as f:
            census_dict = json.load(f)

    return census_dict


def search_xyz_services(keyword, name=None, list_only=True, add_prefix=True):
    """Search for XYZ tile providers from xyzservices.

    Args:
        keyword (str): The keyword to search for.
        name (str, optional): The name of the xyz tile. Defaults to None.
        list_only (bool, optional): If True, only the list of services will be returned. Defaults to True.
        add_prefix (bool, optional): If True, the prefix "xyz." will be added to the service name. Defaults to True.

    Returns:
        list: A list of XYZ tile providers.
    """

    import xyzservices.providers as xyz

    if name is None:
        providers = xyz.filter(keyword=keyword).flatten()
    else:
        providers = xyz.filter(name=name).flatten()

    if list_only:
        if add_prefix:
            return ["xyz." + provider for provider in providers]
        else:
            return [provider for provider in providers]
    else:
        return providers


def search_qms(keyword, limit=10, list_only=True, add_prefix=True):
    """Search for QMS tile providers from Quick Map Services.

    Args:
        keyword (str): The keyword to search for.
        limit (int, optional): The maximum number of results to return. Defaults to 10.
        list_only (bool, optional): If True, only the list of services will be returned. Defaults to True.
        add_prefix (bool, optional): If True, the prefix "qms." will be added to the service name. Defaults to True.

    Returns:
        list: A list of QMS tile providers.
    """

    QMS_API = "https://qms.nextgis.com/api/v1/geoservices"
    services = requests.get(
        f"{QMS_API}/?search={keyword}&type=tms&epsg=3857&limit={limit}"
    )
    services = services.json()
    if services["results"]:
        providers = services["results"]
        if list_only:
            if add_prefix:
                return ["qms." + provider["name"] for provider in providers]
            else:
                return [provider["name"] for provider in providers]
        else:
            return providers
    else:
        return None


def get_wms_layers(url):
    """Returns a list of WMS layers from a WMS service.

    Args:
        url (str): The URL of the WMS service.

    Returns:
        list: A list of WMS layers.
    """
    try:
        from owslib.wms import WebMapService
    except ImportError:
        raise ImportError("Please install owslib using 'pip install owslib'.")

    wms = WebMapService(url)
    layers = list(wms.contents)
    layers.sort()
    return layers


def streamlit_legend(html, width=None, height=None, scrolling=True):
    """Streamlit function to display a legend.

    Args:
        html (str): The HTML string of the legend.
        width (str, optional): The width of the legend. Defaults to None.
        height (str, optional): The height of the legend. Defaults to None.
        scrolling (bool, optional): Whether to allow scrolling in the legend. Defaults to True.

    """

    try:
        import streamlit.components.v1 as components

        components.html(html, width=width, height=height, scrolling=scrolling)

    except ImportError:
        print("Streamlit is not installed. Please run 'pip install streamlit'.")
        return


def read_file_from_url(url, return_type="list", encoding="utf-8"):
    """Reads a file from a URL.

    Args:
        url (str): The URL of the file.
        return_type (str, optional): The return type, can either be string or list. Defaults to "list".
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Raises:
        ValueError: The return type must be either list or string.

    Returns:
        str | list: The contents of the file.
    """
    from urllib.request import urlopen

    if return_type == "list":
        return [line.decode(encoding).rstrip() for line in urlopen(url).readlines()]
    elif return_type == "string":
        return urlopen(url).read().decode(encoding)
    else:
        raise ValueError("The return type must be either list or string.")


def st_download_button(
    label,
    data,
    file_name=None,
    mime=None,
    key=None,
    help=None,
    on_click=None,
    args=None,
    csv_sep=",",
    **kwargs,
):
    """Streamlit function to create a download button.

    Args:
        label (str): A short label explaining to the user what this button is for..
        data (str | list): The contents of the file to be downloaded. See example below for caching techniques to avoid recomputing this data unnecessarily.
        file_name (str, optional): An optional string to use as the name of the file to be downloaded, such as 'my_file.csv'. If not specified, the name will be automatically generated. Defaults to None.
        mime (str, optional): The MIME type of the data. If None, defaults to "text/plain" (if data is of type str or is a textual file) or "application/octet-stream" (if data is of type bytes or is a binary file). Defaults to None.
        key (str, optional): An optional string or integer to use as the unique key for the widget. If this is omitted, a key will be generated for the widget based on its content. Multiple widgets of the same type may not share the same key. Defaults to None.
        help (str, optional): An optional tooltip that gets displayed when the button is hovered over. Defaults to None.
        on_click (str, optional): An optional callback invoked when this button is clicked. Defaults to None.
        args (list, optional): An optional tuple of args to pass to the callback. Defaults to None.
        kwargs (dict, optional): An optional tuple of args to pass to the callback.

    """
    try:
        import streamlit as st
        import pandas as pd

        if isinstance(data, str):
            if file_name is None:
                file_name = data.split("/")[-1]

            if data.endswith(".csv"):
                data = pd.read_csv(data).to_csv(sep=csv_sep, index=False)
                if mime is None:
                    mime = "text/csv"
                return st.download_button(
                    label, data, file_name, mime, key, help, on_click, args, **kwargs
                )
            elif (
                data.endswith(".gif") or data.endswith(".png") or data.endswith(".jpg")
            ):
                if mime is None:
                    mime = f"image/{os.path.splitext(data)[1][1:]}"

                with open(data, "rb") as file:
                    return st.download_button(
                        label,
                        file,
                        file_name,
                        mime,
                        key,
                        help,
                        on_click,
                        args,
                        **kwargs,
                    )
        elif isinstance(data, pd.DataFrame):
            if file_name is None:
                file_name = "data.csv"

            data = data.to_csv(sep=csv_sep, index=False)
            if mime is None:
                mime = "text/csv"
            return st.download_button(
                label, data, file_name, mime, key, help, on_click, args, **kwargs
            )

        else:
            # if mime is None:
            #     mime = "application/pdf"
            return st.download_button(
                label,
                data,
                file_name,
                mime,
                key,
                help,
                on_click,
                args,
                **kwargs,
            )

    except ImportError:
        print("Streamlit is not installed. Please run 'pip install streamlit'.")
        return
    except Exception as e:
        raise Exception(e)


def save_data(data, file_ext=None, file_name=None):
    """Save data in the memory to a file.

    Args:
        data (object): The data to be saved.
        file_ext (str): The file extension of the file.
        file_name (str, optional): The name of the file to be saved. Defaults to None.

    Returns:
        str: The path of the file.
    """
    import tempfile
    import uuid

    try:
        if file_ext is None:
            if hasattr(data, "name"):
                _, file_ext = os.path.splitext(data.name)
        else:
            if not file_ext.startswith("."):
                file_ext = "." + file_ext

        if file_name is not None:
            file_path = os.path.abspath(file_name)
            if not file_path.endswith(file_ext):
                file_path = file_path + file_ext
        else:
            file_id = str(uuid.uuid4())
            file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_ext}")

        with open(file_path, "wb") as file:
            file.write(data.getbuffer())
        return file_path
    except Exception as e:
        print(e)
        return None


def temp_file_path(extension):
    """Returns a temporary file path.

    Args:
        extension (str): The file extension.

    Returns:
        str: The temporary file path.
    """

    import tempfile
    import uuid

    if not extension.startswith("."):
        extension = "." + extension
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{extension}")

    return file_path


def get_local_tile_layer(
    source,
    port="default",
    debug=False,
    projection="EPSG:3857",
    band=None,
    palette=None,
    vmin=None,
    vmax=None,
    nodata=None,
    attribution=None,
    tile_format="ipyleaflet",
    layer_name="Local COG",
    return_client=False,
    **kwargs,
):
    """Generate an ipyleaflet/folium TileLayer from a local raster dataset or remote Cloud Optimized GeoTIFF (COG).
        If you are using this function in JupyterHub on a remote server and the raster does not render properly, try
        running the following two lines before calling this function:

        import os
        os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

    Args:
        source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
        port (str, optional): The port to use for the server. Defaults to "default".
        debug (bool, optional): If True, the server will be started in debug mode. Defaults to False.
        projection (str, optional): The projection of the GeoTIFF. Defaults to "EPSG:3857".
        band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
        palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
        vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
        vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
        nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
        attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
        tile_format (str, optional): The tile layer format. Can be either ipyleaflet or folium. Defaults to "ipyleaflet".
        layer_name (str, optional): The layer name to use. Defaults to None.
        return_client (bool, optional): If True, the tile client will be returned. Defaults to False.

    Returns:
        ipyleaflet.TileLayer | folium.TileLayer: An ipyleaflet.TileLayer or folium.TileLayer.
    """

    check_package(
        "localtileserver", URL="https://github.com/banesullivan/localtileserver"
    )

    if "max_zoom" not in kwargs:
        kwargs["max_zoom"] = 100
    if "max_native_zoom" not in kwargs:
        kwargs["max_native_zoom"] = 100

    # Make it compatible with binder and JupyterHub
    if os.environ.get("JUPYTERHUB_SERVICE_PREFIX") is not None:
        os.environ[
            "LOCALTILESERVER_CLIENT_PREFIX"
        ] = f"{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}"

    if is_studio_lab():
        os.environ[
            "LOCALTILESERVER_CLIENT_PREFIX"
        ] = f"studiolab/default/jupyter/proxy/{{port}}"
    elif is_on_aws():
        os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = "proxy/{port}"
    elif "prefix" in kwargs:
        os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = kwargs["prefix"]
        kwargs.pop("prefix")

    from localtileserver import (
        get_leaflet_tile_layer,
        get_folium_tile_layer,
        TileClient,
    )

    if "show_loading" not in kwargs:
        kwargs["show_loading"] = False

    if isinstance(source, str):
        if not source.startswith("http"):
            if source.startswith("~"):
                source = os.path.expanduser(source)
            else:
                source = os.path.abspath(source)
            if not os.path.exists(source):
                raise ValueError("The source path does not exist.")
        else:
            source = github_raw_url(source)
    else:
        raise ValueError("The source must either be a string or TileClient")

    if isinstance(palette, str):
        palette = get_palette_colors(palette, hashtag=True)

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    if layer_name is None:
        if source.startswith("http"):
            layer_name = "RemoteTile_" + random_string(3)
        else:
            layer_name = "LocalTile_" + random_string(3)

    tile_client = TileClient(source, port=port, debug=debug)

    if "cmap" not in kwargs:
        kwargs["cmap"] = palette

    if tile_format == "ipyleaflet":
        tile_layer = get_leaflet_tile_layer(
            tile_client,
            port=port,
            debug=debug,
            projection=projection,
            band=band,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            name=layer_name,
            **kwargs,
        )
    else:
        tile_layer = get_folium_tile_layer(
            tile_client,
            port=port,
            debug=debug,
            projection=projection,
            band=band,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attr=attribution,
            overlay=True,
            name=layer_name,
            **kwargs,
        )

    if return_client:
        return tile_layer, tile_client
    else:
        return tile_layer

    # center = tile_client.center()
    # bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
    # bounds = (bounds[2], bounds[0], bounds[3], bounds[1])  # [minx, miny, maxx, maxy]

    # if get_center and get_bounds:
    #     return tile_layer, center, bounds
    # elif get_center:
    #     return tile_layer, center
    # elif get_bounds:
    #     return tile_layer, bounds
    # else:
    #     return tile_layer


def get_palettable(types=None):
    """Get a list of palettable color palettes.

    Args:
        types (list, optional): A list of palettable types to return, e.g., types=['matplotlib', 'cartocolors']. Defaults to None.

    Returns:
        list: A list of palettable color palettes.
    """
    try:
        import palettable
    except ImportError:
        raise ImportError(
            "Please install the palettable package using 'pip install palettable'."
        )

    if types is not None and (not isinstance(types, list)):
        raise ValueError("The types must be a list.")

    allowed_palettes = [
        "cartocolors",
        "cmocean",
        "colorbrewer",
        "cubehelix",
        "lightbartlein",
        "matplotlib",
        "mycarta",
        "scientific",
        "tableau",
        "wesanderson",
    ]

    if types is None:
        types = allowed_palettes[:]

    if all(x in allowed_palettes for x in types):
        pass
    else:
        raise ValueError(
            "The types must be one of the following: " + ", ".join(allowed_palettes)
        )

    palettes = []

    if "cartocolors" in types:
        cartocolors_diverging = [
            f"cartocolors.diverging.{c}"
            for c in dir(palettable.cartocolors.diverging)[:-19]
        ]
        cartocolors_qualitative = [
            f"cartocolors.qualitative.{c}"
            for c in dir(palettable.cartocolors.qualitative)[:-19]
        ]
        cartocolors_sequential = [
            f"cartocolors.sequential.{c}"
            for c in dir(palettable.cartocolors.sequential)[:-41]
        ]

        palettes = (
            palettes
            + cartocolors_diverging
            + cartocolors_qualitative
            + cartocolors_sequential
        )

    if "cmocean" in types:
        cmocean_diverging = [
            f"cmocean.diverging.{c}" for c in dir(palettable.cmocean.diverging)[:-19]
        ]
        cmocean_sequential = [
            f"cmocean.sequential.{c}" for c in dir(palettable.cmocean.sequential)[:-19]
        ]

        palettes = palettes + cmocean_diverging + cmocean_sequential

    if "colorbrewer" in types:
        colorbrewer_diverging = [
            f"colorbrewer.diverging.{c}"
            for c in dir(palettable.colorbrewer.diverging)[:-19]
        ]
        colorbrewer_qualitative = [
            f"colorbrewer.qualitative.{c}"
            for c in dir(palettable.colorbrewer.qualitative)[:-19]
        ]
        colorbrewer_sequential = [
            f"colorbrewer.sequential.{c}"
            for c in dir(palettable.colorbrewer.sequential)[:-41]
        ]

        palettes = (
            palettes
            + colorbrewer_diverging
            + colorbrewer_qualitative
            + colorbrewer_sequential
        )

    if "cubehelix" in types:
        cubehelix = [
            "classic_16",
            "cubehelix1_16",
            "cubehelix2_16",
            "cubehelix3_16",
            "jim_special_16",
            "perceptual_rainbow_16",
            "purple_16",
            "red_16",
        ]
        cubehelix = [f"cubehelix.{c}" for c in cubehelix]
        palettes = palettes + cubehelix

    if "lightbartlein" in types:
        lightbartlein_diverging = [
            f"lightbartlein.diverging.{c}"
            for c in dir(palettable.lightbartlein.diverging)[:-19]
        ]
        lightbartlein_sequential = [
            f"lightbartlein.sequential.{c}"
            for c in dir(palettable.lightbartlein.sequential)[:-19]
        ]

        palettes = palettes + lightbartlein_diverging + lightbartlein_sequential

    if "matplotlib" in types:
        matplotlib_colors = [
            f"matplotlib.{c}" for c in dir(palettable.matplotlib)[:-16]
        ]
        palettes = palettes + matplotlib_colors

    if "mycarta" in types:
        mycarta = [f"mycarta.{c}" for c in dir(palettable.mycarta)[:-16]]
        palettes = palettes + mycarta

    if "scientific" in types:
        scientific_diverging = [
            f"scientific.diverging.{c}"
            for c in dir(palettable.scientific.diverging)[:-19]
        ]
        scientific_sequential = [
            f"scientific.sequential.{c}"
            for c in dir(palettable.scientific.sequential)[:-19]
        ]

        palettes = palettes + scientific_diverging + scientific_sequential

    if "tableau" in types:
        tableau = [f"tableau.{c}" for c in dir(palettable.tableau)[:-14]]
        palettes = palettes + tableau

    return palettes


def points_from_xy(data, x="longitude", y="latitude", z=None, crs=None, **kwargs):
    """Create a GeoPandas GeoDataFrame from a csv or Pandas DataFrame containing x, y, z values.

    Args:
        data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
        x (str, optional): The column name for the x values. Defaults to "longitude".
        y (str, optional): The column name for the y values. Defaults to "latitude".
        z (str, optional): The column name for the z values. Defaults to None.
        crs (str | int, optional): The coordinate reference system for the GeoDataFrame. Defaults to None.

    Returns:
        geopandas.GeoDataFrame: A GeoPandas GeoDataFrame containing x, y, z values.
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd
    import pandas as pd

    if crs is None:
        crs = "epsg:4326"

    if isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, str):
        if not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data, **kwargs)
    else:
        raise TypeError("The data must be a pandas DataFrame or a csv file path.")

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y], z=z, crs=crs))

    return gdf


def html_to_streamlit(
    html,
    width=800,
    height=600,
    responsive=True,
    scrolling=False,
    token_name=None,
    token_value=None,
    **kwargs,
):
    """Renders an HTML file in a Streamlit app. This method is a static Streamlit Component, meaning, no information is passed back from Leaflet on browser interaction.

    Args:
        html (str): The HTML file to render. It can a local file path or a URL.
        width (int, optional): Width of the map. Defaults to 800.
        height (int, optional): Height of the map. Defaults to 600.
        responsive (bool, optional): Whether to make the map responsive. Defaults to True.
        scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.
        token_name (str, optional): The name of the token in the HTML file to be replaced. Defaults to None.
        token_value (str, optional): The value of the token to pass to the HTML file. Defaults to None.

    Returns:
        streamlit.components: components.html object.
    """

    try:
        import streamlit as st
        import streamlit.components.v1 as components

        if isinstance(html, str):
            temp_path = None
            if html.startswith("http") and html.endswith(".html"):
                temp_path = temp_file_path(".html")
                out_file = os.path.basename(temp_path)
                out_dir = os.path.dirname(temp_path)
                download_from_url(html, out_file, out_dir)
                html = temp_path

            elif not os.path.exists(html):
                raise FileNotFoundError("The specified input html does not exist.")

            with open(html) as f:
                lines = f.readlines()
                if (token_name is not None) and (token_value is not None):
                    lines = [line.replace(token_name, token_value) for line in lines]
                html_str = "".join(lines)

            if temp_path is not None:
                os.remove(temp_path)

            if responsive:
                make_map_responsive = """
                <style>
                [title~="st.iframe"] { width: 100%}
                </style>
                """
                st.markdown(make_map_responsive, unsafe_allow_html=True)
            return components.html(
                html_str, width=width, height=height, scrolling=scrolling
            )
        else:
            raise TypeError("The html must be a string.")

    except Exception as e:
        raise Exception(e)


def cesium_to_streamlit(
    html,
    width=800,
    height=600,
    responsive=True,
    scrolling=False,
    token_name=None,
    token_value=None,
    **kwargs,
):
    """Renders an cesium HTML file in a Streamlit app. This method is a static Streamlit Component, meaning, no information is passed back from Leaflet on browser interaction.

    Args:
        html (str): The HTML file to render. It can a local file path or a URL.
        width (int, optional): Width of the map. Defaults to 800.
        height (int, optional): Height of the map. Defaults to 600.
        responsive (bool, optional): Whether to make the map responsive. Defaults to True.
        scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.
        token_name (str, optional): The name of the token in the HTML file to be replaced. Defaults to None.
        token_value (str, optional): The value of the token to pass to the HTML file. Defaults to None.

    Returns:
        streamlit.components: components.html object.
    """
    if token_name is None:
        token_name = "your_access_token"

    if token_value is None:
        token_value = os.environ.get("CESIUM_TOKEN")

    html_to_streamlit(
        html, width, height, responsive, scrolling, token_name, token_value
    )


def geom_type(in_geojson, encoding="utf-8"):
    """Returns the geometry type of a GeoJSON object.

    Args:
        in_geojson (dict): A GeoJSON object.
        encoding (str, optional): The encoding of the GeoJSON object. Defaults to "utf-8".

    Returns:
        str: The geometry type of the GeoJSON object, such as Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon.
            For more info, see https://shapely.readthedocs.io/en/stable/manual.html
    """
    import json

    try:
        if isinstance(in_geojson, str):
            if in_geojson.startswith("http"):
                data = requests.get(in_geojson).json()
            else:
                in_geojson = os.path.abspath(in_geojson)
                if not os.path.exists(in_geojson):
                    raise FileNotFoundError(
                        "The provided GeoJSON file could not be found."
                    )

                with open(in_geojson, encoding=encoding) as f:
                    data = json.load(f)
        elif isinstance(in_geojson, dict):
            data = in_geojson
        else:
            raise TypeError("The input geojson must be a type of str or dict.")

        return data["features"][0]["geometry"]["type"]

    except Exception as e:
        raise Exception(e)


def geojson_to_gdf(in_geojson, encoding="utf-8", **kwargs):
    """Converts a GeoJSON object to a geopandas GeoDataFrame.

    Args:
        in_geojson (str | dict): The input GeoJSON file or GeoJSON object as a dict.
        encoding (str, optional): The encoding of the GeoJSON object. Defaults to "utf-8".

    Returns:
        geopandas.GeoDataFrame: A geopandas GeoDataFrame containing the GeoJSON object.
    """

    import geopandas as gpd

    if isinstance(in_geojson, dict):
        out_file = temp_file_path(extension="geojson")
        with open(out_file, "w") as f:
            json.dump(in_geojson, f)
            in_geojson = out_file

    gdf = gpd.read_file(in_geojson, encoding=encoding, **kwargs)
    return gdf


def geojson_to_df(in_geojson, encoding="utf-8", drop_geometry=True):
    """Converts a GeoJSON object to a pandas DataFrame.

    Args:
        in_geojson (str | dict): The input GeoJSON file or dict.
        encoding (str, optional): The encoding of the GeoJSON object. Defaults to "utf-8".
        drop_geometry (bool, optional): Whether to drop the geometry column. Defaults to True.

    Raises:
        FileNotFoundError: If the input GeoJSON file could not be found.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the GeoJSON object.
    """

    import json
    import pandas as pd
    from urllib.request import urlopen

    if isinstance(in_geojson, str):
        if in_geojson.startswith("http"):
            with urlopen(in_geojson) as f:
                data = json.load(f)
        else:
            in_geojson = os.path.abspath(in_geojson)
            if not os.path.exists(in_geojson):
                raise FileNotFoundError("The provided GeoJSON file could not be found.")

            with open(in_geojson, encoding=encoding) as f:
                data = json.load(f)

    elif isinstance(in_geojson, dict):
        data = in_geojson

    df = pd.json_normalize(data["features"])
    df.columns = [col.replace("properties.", "") for col in df.columns]
    if drop_geometry:
        df = df[df.columns.drop(list(df.filter(regex="geometry")))]
    return df


def geojson_to_shp(in_geojson, out_shp, **kwargs):
    """Converts a GeoJSON object to GeoPandas GeoDataFrame.

    Args:
        in_geojson (str | dict): The input GeoJSON file or dict.
        out_shp (str): The output shapefile path.
    """
    import geopandas as gpd
    import json

    ext = os.path.splitext(out_shp)[1]
    if ext != ".shp":
        out_shp = out_shp + ".shp"
    out_shp = check_file_path(out_shp)

    if isinstance(in_geojson, dict):
        out_file = temp_file_path(extension="geojson")
        with open(out_file, "w") as f:
            json.dump(in_geojson, f)
            in_geojson = out_file

    gdf = gpd.read_file(in_geojson, **kwargs)
    gdf.to_file(out_shp)


def geojson_to_gpkg(in_geojson, out_gpkg, **kwargs):
    """Converts a GeoJSON object to GeoPackage.

    Args:
        in_geojson (str | dict): The input GeoJSON file or dict.
        out_gpkg (str): The output GeoPackage path.
    """
    import geopandas as gpd
    import json

    ext = os.path.splitext(out_gpkg)[1]
    if ext.lower() != ".gpkg":
        out_gpkg = out_gpkg + ".gpkg"
    out_gpkg = check_file_path(out_gpkg)

    if isinstance(in_geojson, dict):
        out_file = temp_file_path(extension="geojson")
        with open(out_file, "w") as f:
            json.dump(in_geojson, f)
            in_geojson = out_file

    gdf = gpd.read_file(in_geojson, **kwargs)
    name = os.path.splitext(os.path.basename(out_gpkg))[0]
    gdf.to_file(out_gpkg, layer=name, driver="GPKG")


def gdf_to_df(gdf, drop_geom=True):
    """Converts a GeoDataFrame to a pandas DataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        drop_geom (bool, optional): Whether to drop the geometry column. Defaults to True.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the GeoDataFrame.
    """
    import pandas as pd

    if drop_geom:
        df = pd.DataFrame(gdf.drop(columns=["geometry"]))
    else:
        df = pd.DataFrame(gdf)

    return df


def gdf_bounds(gdf, return_geom=False):
    """Returns the bounding box of a GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        return_geom (bool, optional): Whether to return the bounding box as a GeoDataFrame. Defaults to False.

    Returns:
        list | gpd.GeoDataFrame: A bounding box in the form of a list (minx, miny, maxx, maxy) or GeoDataFrame.
    """
    bounds = gdf.total_bounds
    if return_geom:
        return bbox_to_gdf(bbox=bounds)
    else:
        return bounds


def gdf_centroid(gdf, return_geom=False):
    """Returns the centroid of a GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        return_geom (bool, optional): Whether to return the bounding box as a GeoDataFrame. Defaults to False.

    Returns:
        list | gpd.GeoDataFrame: A bounding box in the form of a list (lon, lat) or GeoDataFrame.
    """
    import warnings

    warnings.filterwarnings("ignore")

    centroid = gdf_bounds(gdf, return_geom=True).centroid
    if return_geom:
        return centroid
    else:
        return centroid.x[0], centroid.y[0]


def gdf_geom_type(gdf, first_only=True):
    """Returns the geometry type of a GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        first_only (bool, optional): Whether to return the geometry type of the first feature in the GeoDataFrame. Defaults to True.

    Returns:
        str: The geometry type of the GeoDataFrame, such as Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon.
            For more info, see https://shapely.readthedocs.io/en/stable/manual.html
    """
    import geopandas as gpd

    if first_only:
        return gdf.geometry.type[0]
    else:
        return gdf.geometry.type


def check_dir(dir_path, make_dirs=True):
    """Checks if a directory exists and creates it if it does not.

    Args:
        dir_path ([str): The path to the directory.
        make_dirs (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

    Raises:
        FileNotFoundError: If the directory could not be found.
        TypeError: If the input directory path is not a string.

    Returns:
        str: The path to the directory.
    """

    if isinstance(dir_path, str):
        if dir_path.startswith("~"):
            dir_path = os.path.expanduser(dir_path)
        else:
            dir_path = os.path.abspath(dir_path)

        if not os.path.exists(dir_path) and make_dirs:
            os.makedirs(dir_path)

        if os.path.exists(dir_path):
            return dir_path
        else:
            raise FileNotFoundError("The provided directory could not be found.")
    else:
        raise TypeError("The provided directory path must be a string.")


def check_file_path(file_path, make_dirs=True):
    """Gets the absolute file path.

    Args:
        file_path (str): The path to the file.
        make_dirs (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

    Raises:
        FileNotFoundError: If the directory could not be found.
        TypeError: If the input directory path is not a string.

    Returns:
        str: The absolute path to the file.
    """
    if isinstance(file_path, str):
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)
        else:
            file_path = os.path.abspath(file_path)

        file_dir = os.path.dirname(file_path)
        if not os.path.exists(file_dir) and make_dirs:
            os.makedirs(file_dir)

        return file_path

    else:
        raise TypeError("The provided file path must be a string.")


def dict_to_json(data, file_path, indent=4):
    """Writes a dictionary to a JSON file.

    Args:
        data (dict): A dictionary.
        file_path (str): The path to the JSON file.
        indent (int, optional): The indentation of the JSON file. Defaults to 4.

    Raises:
        TypeError: If the input data is not a dictionary.
    """
    import json

    file_path = check_file_path(file_path)

    if isinstance(data, dict):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=indent)
    else:
        raise TypeError("The provided data must be a dictionary.")


def image_to_cog(source, dst_path=None, profile="deflate", **kwargs):
    """Converts an image to a COG file.

    Args:
        source (str): A dataset path, URL or rasterio.io.DatasetReader object.
        dst_path (str, optional): An output dataset path or or PathLike object. Defaults to None.
        profile (str, optional): COG profile. More at https://cogeotiff.github.io/rio-cogeo/profile. Defaults to "deflate".

    Raises:
        ImportError: If rio-cogeo is not installed.
        FileNotFoundError: If the source file could not be found.
    """
    try:
        from rio_cogeo.cogeo import cog_translate
        from rio_cogeo.profiles import cog_profiles

    except ImportError:
        raise ImportError(
            "The rio-cogeo package is not installed. Please install it with `pip install rio-cogeo` or `conda install rio-cogeo -c conda-forge`."
        )

    if not source.startswith("http"):
        source = check_file_path(source)

        if not os.path.exists(source):
            raise FileNotFoundError("The provided input file could not be found.")

    if dst_path is None:
        if not source.startswith("http"):
            dst_path = os.path.splitext(source)[0] + "_cog.tif"
        else:
            dst_path = temp_file_path(extension=".tif")

    dst_path = check_file_path(dst_path)

    dst_profile = cog_profiles.get(profile)
    cog_translate(source, dst_path, dst_profile, **kwargs)


def cog_validate(source, verbose=False):
    """Validate Cloud Optimized Geotiff.

    Args:
        source (str): A dataset path or URL. Will be opened in "r" mode.
        verbose (bool, optional): Whether to print the output of the validation. Defaults to False.

    Raises:
        ImportError: If the rio-cogeo package is not installed.
        FileNotFoundError: If the provided file could not be found.

    Returns:
        tuple: A tuple containing the validation results (True is src_path is a valid COG, List of validation errors, and a list of validation warnings).
    """
    try:
        from rio_cogeo.cogeo import cog_validate, cog_info
    except ImportError:
        raise ImportError(
            "The rio-cogeo package is not installed. Please install it with `pip install rio-cogeo` or `conda install rio-cogeo -c conda-forge`."
        )

    if not source.startswith("http"):
        source = check_file_path(source)

        if not os.path.exists(source):
            raise FileNotFoundError("The provided input file could not be found.")

    if verbose:
        return cog_info(source)
    else:
        return cog_validate(source)


def image_to_numpy(image):
    """Converts an image to a numpy array.

    Args:
        image (str): A dataset path, URL or rasterio.io.DatasetReader object.

    Raises:
        FileNotFoundError: If the provided file could not be found.

    Returns:
        np.array: A numpy array.
    """
    import rasterio

    from osgeo import gdal

    # ... and suppress errors
    gdal.PushErrorHandler("CPLQuietErrorHandler")

    try:
        with rasterio.open(image, "r") as ds:
            arr = ds.read()  # read all raster values
        return arr
    except Exception as e:
        raise Exception(e)


def numpy_to_image(
    np_array,
    filename: str,
    transpose: bool = True,
    bands: Union[int, list] = None,
    size: tuple = None,
    resize_args: dict = None,
    **kwargs,
) -> None:
    """Converts a numpy array to an image in the specified format, such as JPG, PNG, TIFF, etc.

    Args:
        np_array (np.ndarray): A numpy array or a path to a raster file.
        filename (str): The output filename.
        transpose (bool, optional): Whether to transpose the array from (bands, rows, cols) to (rows, cols, bands). Defaults to True.
        bands (int | list, optional): The band(s) to use, starting from 0. Defaults to None.

    """

    import warnings
    import numpy as np
    from PIL import Image

    warnings.filterwarnings("ignore")

    if isinstance(np_array, str):
        np_array = image_to_numpy(np_array)

    if not isinstance(np_array, np.ndarray):
        raise TypeError("The provided input must be a numpy array.")

    if np_array.dtype == np.float64 or np_array.dtype == np.float32:
        # Convert the array to uint8
        # np_array = (np_array * 255).astype(np.uint8)
        np_array.interp(np_array, (np_array.min(), np_array.max()), (0, 255)).astype(
            np.uint8
        )
    else:
        # The array is already uint8
        np_array = np_array

    if np_array.ndim == 2:
        img = Image.fromarray(np_array)
    elif np_array.ndim == 3:
        if transpose:
            np_array = np_array.transpose(1, 2, 0)
        if bands is None:
            if np_array.shape[2] < 3:
                np_array = np_array[:, :, 0]
            elif np_array.shape[2] > 3:
                np_array = np_array[:, :, :3]

        elif isinstance(bands, list):
            if len(bands) == 1:
                np_array = np_array[:, :, bands[0]]
            else:
                np_array = np_array[:, :, bands]
        elif isinstance(bands, int):
            np_array = np_array[:, :, bands]
        img = Image.fromarray(np_array)
    else:
        raise ValueError("The provided input must be a 2D or 3D numpy array.")

    if isinstance(size, tuple):
        try:
            from skimage.transform import resize
        except ImportError:
            raise ImportError(
                "The scikit-image package is not installed. Please install it with `pip install scikit-image` \
                  or `conda install scikit-image -c conda-forge`."
            )
        if resize_args is None:
            resize_args = {}
        if "preserve_range" not in resize_args:
            resize_args["preserve_range"] = True
        np_array = resize(np_array, size, **resize_args).astype("uint8")
        img = Image.fromarray(np_array)

    img.save(filename, **kwargs)


def numpy_to_cog(
    np_array,
    out_cog,
    bounds=None,
    profile=None,
    dtype=None,
    dst_crs=None,
    coord_crs=None,
):
    """Converts a numpy array to a COG file.

    Args:
        np_array (np.array): A numpy array representing an image or an HTTP URL to an image.
        out_cog (str): The output COG file path.
        bounds (tuple, optional): The bounds of the image in the format of (minx, miny, maxx, maxy). Defaults to None.
        profile (str | dict, optional): File path to an existing COG file or a dictionary representing the profile. Defaults to None.
        dtype (str, optional): The data type of the output COG file. Defaults to None.
        dst_crs (str, optional): The coordinate reference system of the output COG file. Defaults to "epsg:4326".
        coord_crs (str, optional): The coordinate reference system of bbox coordinates. Defaults to None.

    """
    import warnings
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds

    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    warnings.filterwarnings("ignore")

    if isinstance(np_array, str):
        with rasterio.open(np_array, "r") as ds:
            np_array = ds.read()

    if not isinstance(np_array, np.ndarray):
        raise TypeError("The input array must be a numpy array.")

    out_dir = os.path.dirname(out_cog)
    check_dir(out_dir)

    if profile is not None:
        if isinstance(profile, str):
            if (not profile.startswith("http")) and (not os.path.exists(profile)):
                raise FileNotFoundError("The provided file could not be found.")
            with rasterio.open(profile) as ds:
                dst_crs = ds.crs
                if bounds is None:
                    bounds = ds.bounds

        elif isinstance(profile, rasterio.profiles.Profile):
            profile = dict(profile)
        elif not isinstance(profile, dict):
            raise TypeError("The provided profile must be a file path or a dictionary.")

    if bounds is None:
        print(
            "warning: bounds is not set. Using the default bounds (-180.0, -85.0511, 180.0, 85.0511)"
        )
        bounds = (-180.0, -85.0511287798066, 180.0, 85.0511287798066)

    if not isinstance(bounds, tuple) and len(bounds) != 4:
        raise TypeError("The provided bounds must be a tuple of length 4.")

    # Rasterio uses numpy array of shape of `(bands, height, width)`

    if len(np_array.shape) == 3:
        nbands = np_array.shape[0]
        height = np_array.shape[1]
        width = np_array.shape[2]
    elif len(np_array.shape) == 2:
        nbands = 1
        height = np_array.shape[0]
        width = np_array.shape[1]
        np_array = np_array.reshape((1, height, width))
    else:
        raise ValueError("The input array must be a 2D or 3D numpy array.")

    if coord_crs is not None and dst_crs is not None:
        bounds = transform_bbox_coords(bounds, coord_crs, dst_crs)

    src_transform = from_bounds(*bounds, width=width, height=height)
    if dtype is None:
        dtype = str(np_array.dtype)

    if dst_crs is None:
        dst_crs = "epsg:4326"

    if isinstance(profile, dict):
        src_profile = profile
        src_profile["count"] = nbands
    else:
        src_profile = dict(
            driver="GTiff",
            dtype=dtype,
            count=nbands,
            height=height,
            width=width,
            crs=dst_crs,
            transform=src_transform,
        )

    with MemoryFile() as memfile:
        with memfile.open(**src_profile) as mem:
            # Populate the input file with numpy array
            mem.write(np_array)

            dst_profile = cog_profiles.get("deflate")
            cog_translate(
                mem,
                out_cog,
                dst_profile,
                in_memory=True,
                quiet=True,
            )


def get_stac_collections(url, **kwargs):
    """Retrieve a list of STAC collections from a URL.
    This function is adapted from https://github.com/mykolakozyr/stacdiscovery/blob/a5d1029aec9c428a7ce7ae615621ea8915162824/app.py#L31.
    Credits to Mykola Kozyr.

    Args:
        url (str): A URL to a STAC catalog.
        **kwargs: Additional keyword arguments to pass to the pystac Client.open() method.
            See https://pystac-client.readthedocs.io/en/stable/api.html#pystac_client.Client.open

    Returns:
        list: A list of STAC collections.
    """
    from pystac_client import Client

    # Expensive function. Added cache for it.

    # Empty list that would be used for a dataframe to collect and visualize info about collections
    root_catalog = Client.open(url, **kwargs)
    collections_list = []
    # Reading collections in the Catalog
    collections = list(root_catalog.get_collections())
    print(collections)
    for collection in collections:
        id = collection.id
        title = collection.title
        # bbox = collection.extent.spatial.bboxes # not in use for the first release
        # interval = collection.extent.temporal.intervals # not in use for the first release
        description = collection.description

        # creating a list of lists of values
        collections_list.append([id, title, description])
    return collections_list


def get_stac_items(
    url,
    collection,
    limit=None,
    bbox=None,
    datetime=None,
    intersects=None,
    ids=None,
    open_args=None,
    **kwargs,
):
    """Retrieve a list of STAC items from a URL and a collection.
    This function is adapted from https://github.com/mykolakozyr/stacdiscovery/blob/a5d1029aec9c428a7ce7ae615621ea8915162824/app.py#L49.
    Credits to Mykola Kozyr.
    Available parameters can be found at https://github.com/radiantearth/stac-api-spec/tree/master/item-search

    Args:
        url (str): A URL to a STAC catalog.
        collection (str): A STAC collection ID.
        limit (int, optional): The maximum number of results to return (page size). Defaults to None.
        bbox (tuple, optional): Requested bounding box in the format of (minx, miny, maxx, maxy). Defaults to None.
        datetime (str, optional): Single date+time, or a range ('/' separator), formatted to RFC 3339, section 5.6. Use double dots .. for open date ranges.
        intersects (dict, optional): A dictionary representing a GeoJSON Geometry. Searches items by performing intersection between their geometry and provided GeoJSON geometry. All GeoJSON geometry types must be supported.
        ids (list, optional): A list of item ids to return.
        open_args (dict, optional): A dictionary of arguments to pass to the pystac Client.open() method. Defaults to None.
        **kwargs: Additional keyword arguments to pass to the Catalog.search() method.

    Returns:
        GeoPandas.GeoDataFraem: A GeoDataFrame with the STAC items.
    """

    import itertools
    import geopandas as gpd
    from shapely.geometry import shape
    from pystac_client import Client

    # Empty list that would be used for a dataframe to collect and visualize info about collections
    items_list = []

    if open_args is None:
        open_args = {}

    root_catalog = Client.open(url)

    if limit:
        kwargs["limit"] = limit
    if bbox:
        kwargs["bbox"] = bbox
    if datetime:
        kwargs["datetime"] = datetime
    if intersects:
        kwargs["intersects"] = intersects
    if ids:
        kwargs["ids"] = ids

    if kwargs:
        try:
            catalog = root_catalog.search(collections=collection, **kwargs)
        except NotImplementedError:
            catalog = root_catalog
    else:
        catalog = root_catalog

    iterable = catalog.get_all_items()
    items = list(
        itertools.islice(iterable, limit)
    )  # getting first 25000 items. To Do some smarter logic
    if len(items) == 0:
        try:
            catalog = root_catalog.get_child(collection)
            iterable = catalog.get_all_items()
            items = list(itertools.islice(iterable, limit))
        except Exception as _:
            print("Ooops, it looks like this collection does not have items.")
            return None
    # Iterating over items to collect main information
    for item in items:
        id = item.id
        geometry = shape(item.geometry)
        datetime = (
            item.datetime
            or item.properties["datetime"]
            or item.properties["end_datetime"]
            or item.properties["start_datetime"]
        )
        links = item.links
        for link in links:
            if link.rel == "self":
                self_url = link.target
        assets_list = []
        assets = item.assets
        for asset in assets:
            assets_list.append(asset)

        # creating a list of lists of values
        items_list.append([id, geometry, datetime, self_url, assets_list])

    if limit is not None:
        items_list = items_list[:limit]
    items_df = gpd.GeoDataFrame(items_list)
    items_df.columns = ["id", "geometry", "datetime", "self_url", "assets_list"]

    items_gdf = items_df.set_geometry("geometry")
    items_gdf["datetime"] = items_gdf["datetime"].astype(
        str
    )  # specifically for KeplerGL. See https://github.com/keplergl/kepler.gl/issues/602
    # items_gdf["assets_list"] = items_gdf["assets_list"].astype(str) #specifically for KeplerGL. See https://github.com/keplergl/kepler.gl/issues/602
    items_gdf.set_crs(epsg=4326, inplace=True)
    return items_gdf


def list_palettes(add_extra=False, lowercase=False):
    """List all available colormaps. See a complete lost of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.

    Returns:
        list: The list of colormap names.
    """
    import matplotlib.pyplot as plt

    result = plt.colormaps()
    if add_extra:
        result += ["dem", "ndvi", "ndwi"]
    if lowercase:
        result = [i.lower() for i in result]
    result.sort()
    return result


def get_palette_colors(cmap_name=None, n_class=None, hashtag=False):
    """Get a palette from a matplotlib colormap. See the list of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.

    Args:
        cmap_name (str, optional): The name of the matplotlib colormap. Defaults to None.
        n_class (int, optional): The number of colors. Defaults to None.
        hashtag (bool, optional): Whether to return a list of hex colors. Defaults to False.

    Returns:
        list: A list of hex colors.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    cmap = plt.cm.get_cmap(cmap_name, n_class)
    colors = [mpl.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
    if hashtag:
        colors = ["#" + i for i in colors]
    return colors


def mosaic_tile(url, titiler_endpoint=None, **kwargs):
    """Get the tile URL from a MosaicJSON.

    Args:
        url (str): HTTP URL to a MosaicJSON.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz". Defaults to None.

    Returns:
        str: The tile URL.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if isinstance(url, str) and url.startswith("http"):
        kwargs["url"] = url
    else:
        raise ValueError("url must be a string and start with http.")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/mosaicjson/tilejson.json",
            params=kwargs,
        ).json()
    else:
        raise ValueError("titiler_endpoint must be a string.")

    return r["tiles"][0]


def mosaic_bounds(url, titiler_endpoint=None, **kwargs):
    """Get the bounding box of a MosaicJSON.

    Args:
        url (str): HTTP URL to a MosaicJSON.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz". Defaults to None.

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if isinstance(url, str) and url.startswith("http"):
        kwargs["url"] = url
    else:
        raise ValueError("url must be a string and start with http.")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/mosaicjson/bounds",
            params=kwargs,
        ).json()
    else:
        raise ValueError("titiler_endpoint must be a string.")

    return r["bounds"]


def mosaic_info(url, titiler_endpoint=None, **kwargs):
    """Get the info of a MosaicJSON.

    Args:
        url (str): HTTP URL to a MosaicJSON.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz". Defaults to None.

    Returns:
        dict: A dictionary containing bounds, center, minzoom, maxzoom, and name as keys.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if isinstance(url, str) and url.startswith("http"):
        kwargs["url"] = url
    else:
        raise ValueError("url must be a string and start with http.")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/mosaicjson/info",
            params=kwargs,
        ).json()
    else:
        raise ValueError("titiler_endpoint must be a string.")

    return r


def mosaic_info_geojson(url, titiler_endpoint=None, **kwargs):
    """Get the info of a MosaicJSON.

    Args:
        url (str): HTTP URL to a MosaicJSON.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz". Defaults to None.

    Returns:
        dict: A dictionary representing a dict of GeoJSON.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if isinstance(url, str) and url.startswith("http"):
        kwargs["url"] = url
    else:
        raise ValueError("url must be a string and start with http.")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/mosaicjson/info.geojson",
            params=kwargs,
        ).json()
    else:
        raise ValueError("titiler_endpoint must be a string.")

    return r


def view_lidar(
    filename,
    cmap="terrain",
    backend="pyvista",
    background=None,
    eye_dome_lighting=False,
    **kwargs,
):
    """View LiDAR data in 3D.

    Args:
        filename (str): The filepath to the LiDAR data.
        cmap (str, optional): The colormap to use. Defaults to "terrain". cmap currently does not work for the open3d backend.
        backend (str, optional): The plotting backend to use, can be pyvista, ipygany, panel, and open3d. Defaults to "pyvista".
        background (str, optional): The background color to use. Defaults to None.
        eye_dome_lighting (bool, optional): Whether to use eye dome lighting. Defaults to False.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the backend is not supported.
    """
    import warnings
    import sys

    if os.environ.get("USE_MKDOCS") is not None:
        return

    if "google.colab" in sys.modules:
        print("This function is not supported in Google Colab.")
        return

    warnings.filterwarnings("ignore")
    filename = os.path.abspath(filename)
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    backend = backend.lower()
    if backend in ["pyvista", "ipygany", "panel"]:
        try:
            import pyntcloud
        except ImportError:
            print(
                "The pyvista and pyntcloud packages are required for this function. Use pip install leafmap[lidar] to install them."
            )
            return

        try:
            if backend == "pyvista":
                backend = None
            if backend == "ipygany":
                cmap = None
            data = pyntcloud.PyntCloud.from_file(filename)
            mesh = data.to_instance("pyvista", mesh=False)
            mesh = mesh.elevation()
            mesh.plot(
                scalars="Elevation",
                cmap=cmap,
                jupyter_backend=backend,
                background=background,
                eye_dome_lighting=eye_dome_lighting,
                **kwargs,
            )

        except Exception as e:
            print("Something went wrong.")
            print(e)
            return

    elif backend == "open3d":
        try:
            import laspy
            import open3d as o3d
            import numpy as np
        except ImportError:
            print(
                "The laspy and open3d packages are required for this function. Use pip install laspy open3d to install them."
            )
            return

        try:
            las = laspy.read(filename)
            point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))
            geom = o3d.geometry.PointCloud()
            geom.points = o3d.utility.Vector3dVector(point_data)
            # geom.colors =  o3d.utility.Vector3dVector(colors)  # need to add colors. A list in the form of [[r,g,b], [r,g,b]] with value range 0-1. https://github.com/isl-org/Open3D/issues/614
            o3d.visualization.draw_geometries([geom], **kwargs)

        except Exception as e:
            print("Something went wrong.")
            print(e)
            return

    else:
        raise ValueError(f"{backend} is not a valid backend.")


def read_lidar(filename, **kwargs):
    """Read a LAS file.

    Args:
        filename (str): A local file path or HTTP URL to a LAS file.

    Returns:
        LasData: The LasData object return by laspy.read.
    """
    try:
        import laspy
    except ImportError:
        print(
            "The laspy package is required for this function. Use `pip install laspy[lazrs,laszip]` to install it."
        )
        return

    if (
        isinstance(filename, str)
        and filename.startswith("http")
        and (filename.endswith(".las") or filename.endswith(".laz"))
    ):
        filename = github_raw_url(filename)
        filename = download_file(filename)

    return laspy.read(filename, **kwargs)


def convert_lidar(
    source, destination=None, point_format_id=None, file_version=None, **kwargs
):
    """Converts a Las from one point format to another Automatically upgrades the file version if source file version
        is not compatible with the new point_format_id

    Args:
        source (str | laspy.lasdatas.base.LasBase): The source data to be converted.
        destination (str, optional): The destination file path. Defaults to None.
        point_format_id (int, optional): The new point format id (the default is None, which won't change the source format id).
        file_version (str, optional): The new file version. None by default which means that the file_version may be upgraded
            for compatibility with the new point_format. The file version will not be downgraded.

    Returns:
        aspy.lasdatas.base.LasBase: The converted LasData object.
    """
    try:
        import laspy
    except ImportError:
        print(
            "The laspy package is required for this function. Use `pip install laspy[lazrs,laszip]` to install it."
        )
        return

    if isinstance(source, str):
        source = read_lidar(source)

    las = laspy.convert(
        source, point_format_id=point_format_id, file_version=file_version
    )

    if destination is None:
        return las
    else:
        destination = check_file_path(destination)
        write_lidar(las, destination, **kwargs)
        return destination


def write_lidar(source, destination, do_compress=None, laz_backend=None):
    """Writes to a stream or file.

    Args:
        source (str | laspy.lasdatas.base.LasBase): The source data to be written.
        destination (str): The destination filepath.
        do_compress (bool, optional): Flags to indicate if you want to compress the data. Defaults to None.
        laz_backend (str, optional): The laz backend to use. Defaults to None.
    """

    try:
        import laspy
    except ImportError:
        print(
            "The laspy package is required for this function. Use `pip install laspy[lazrs,laszip]` to install it."
        )
        return

    if isinstance(source, str):
        source = read_lidar(source)

    source.write(destination, do_compress=do_compress, laz_backend=laz_backend)


def download_file(
    url=None,
    output=None,
    quiet=False,
    proxy=None,
    speed=None,
    use_cookies=True,
    verify=True,
    id=None,
    fuzzy=False,
    resume=False,
    unzip=True,
    overwrite=False,
    subfolder=False,
):
    """Download a file from URL, including Google Drive shared URL.

    Args:
        url (str, optional): Google Drive URL is also supported. Defaults to None.
        output (str, optional): Output filename. Default is basename of URL.
        quiet (bool, optional): Suppress terminal output. Default is False.
        proxy (str, optional): Proxy. Defaults to None.
        speed (float, optional): Download byte size per second (e.g., 256KB/s = 256 * 1024). Defaults to None.
        use_cookies (bool, optional): Flag to use cookies. Defaults to True.
        verify (bool | str, optional): Either a bool, in which case it controls whether the server's TLS certificate is verified, or a string,
            in which case it must be a path to a CA bundle to use. Default is True.. Defaults to True.
        id (str, optional): Google Drive's file ID. Defaults to None.
        fuzzy (bool, optional): Fuzzy extraction of Google Drive's file Id. Defaults to False.
        resume (bool, optional): Resume the download from existing tmp file if possible. Defaults to False.
        unzip (bool, optional): Unzip the file. Defaults to True.
        overwrite (bool, optional): Overwrite the file if it already exists. Defaults to False.
        subfolder (bool, optional): Create a subfolder with the same name as the file. Defaults to False.

    Returns:
        str: The output file path.
    """
    try:
        import gdown
    except ImportError:
        print(
            "The gdown package is required for this function. Use `pip install gdown` to install it."
        )
        return

    if output is None:
        if isinstance(url, str) and url.startswith("http"):
            output = os.path.basename(url)

    out_dir = os.path.abspath(os.path.dirname(output))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if isinstance(url, str):
        if os.path.exists(os.path.abspath(output)) and (not overwrite):
            print(
                f"{output} already exists. Skip downloading. Set overwrite=True to overwrite."
            )
            return os.path.abspath(output)
        else:
            url = github_raw_url(url)

    if "https://drive.google.com/file/d/" in url:
        fuzzy = True

    output = gdown.download(
        url, output, quiet, proxy, speed, use_cookies, verify, id, fuzzy, resume
    )

    if unzip and output.endswith(".zip"):
        with zipfile.ZipFile(output, "r") as zip_ref:
            if not quiet:
                print("Extracting files...")
            if subfolder:
                basename = os.path.splitext(os.path.basename(output))[0]

                output = os.path.join(out_dir, basename)
                if not os.path.exists(output):
                    os.makedirs(output)
                zip_ref.extractall(output)
            else:
                zip_ref.extractall(os.path.dirname(output))

    return os.path.abspath(output)


def download_files(
    urls,
    out_dir=None,
    filenames=None,
    quiet=False,
    proxy=None,
    speed=None,
    use_cookies=True,
    verify=True,
    id=None,
    fuzzy=False,
    resume=False,
    unzip=True,
    overwrite=False,
    subfolder=False,
):
    """Download files from URLs, including Google Drive shared URL.

    Args:
        urls (list): The list of urls to download. Google Drive URL is also supported.
        out_dir (str, optional): The output directory. Defaults to None.
        filenames (list, optional): Output filename. Default is basename of URL.
        quiet (bool, optional): Suppress terminal output. Default is False.
        proxy (str, optional): Proxy. Defaults to None.
        speed (float, optional): Download byte size per second (e.g., 256KB/s = 256 * 1024). Defaults to None.
        use_cookies (bool, optional): Flag to use cookies. Defaults to True.
        verify (bool | str, optional): Either a bool, in which case it controls whether the server's TLS certificate is verified, or a string, in which case it must be a path to a CA bundle to use. Default is True.. Defaults to True.
        id (str, optional): Google Drive's file ID. Defaults to None.
        fuzzy (bool, optional): Fuzzy extraction of Google Drive's file Id. Defaults to False.
        resume (bool, optional): Resume the download from existing tmp file if possible. Defaults to False.
        unzip (bool, optional): Unzip the file. Defaults to True.
        overwrite (bool, optional): Overwrite the file if it already exists. Defaults to False.
        subfolder (bool, optional): Create a subfolder with the same name as the file. Defaults to False.
    """

    if out_dir is None:
        out_dir = os.getcwd()

    if filenames is None:
        filenames = [None] * len(urls)

    for url, output in zip(urls, filenames):
        if output is None:
            filename = os.path.join(out_dir, os.path.basename(url))
        else:
            filename = os.path.join(out_dir, output)

        download_file(
            url,
            filename,
            quiet,
            proxy,
            speed,
            use_cookies,
            verify,
            id,
            fuzzy,
            resume,
            unzip,
            overwrite,
            subfolder,
        )


def download_folder(
    url=None,
    id=None,
    output=None,
    quiet=False,
    proxy=None,
    speed=None,
    use_cookies=True,
    remaining_ok=False,
):
    """Downloads the entire folder from URL.

    Args:
        url (str, optional): URL of the Google Drive folder. Must be of the format 'https://drive.google.com/drive/folders/{url}'. Defaults to None.
        id (str, optional): Google Drive's folder ID. Defaults to None.
        output (str, optional):  String containing the path of the output folder. Defaults to current working directory.
        quiet (bool, optional): Suppress terminal output. Defaults to False.
        proxy (str, optional): Proxy. Defaults to None.
        speed (float, optional): Download byte size per second (e.g., 256KB/s = 256 * 1024). Defaults to None.
        use_cookies (bool, optional): Flag to use cookies. Defaults to True.
        resume (bool, optional): Resume the download from existing tmp file if possible. Defaults to False.

    Returns:
        list: List of files downloaded, or None if failed.
    """

    try:
        import gdown
    except ImportError:
        print(
            "The gdown package is required for this function. Use `pip install gdown` to install it."
        )
        return

    files = gdown.download_folder(
        url, id, output, quiet, proxy, speed, use_cookies, remaining_ok
    )
    return files


def clip_image(image, mask, output, to_cog=True):
    """Clip an image by mask.

    Args:
        image (str): Path to the image file in GeoTIFF format.
        mask (str | list | dict): The mask used to extract the image. It can be a path to vector datasets (e.g., GeoJSON, Shapefile), a list of coordinates, or m.user_roi.
        output (str): Path to the output file.
        to_cog (bool, optional): Flags to indicate if you want to convert the output to COG. Defaults to True.

    Raises:
        ImportError: If the fiona or rasterio package is not installed.
        FileNotFoundError: If the image is not found.
        ValueError: If the mask is not a valid GeoJSON or raster file.
        FileNotFoundError: If the mask file is not found.
    """
    try:
        import json
        import fiona
        import rasterio
        import rasterio.mask
    except ImportError as e:
        raise ImportError(e)

    if not os.path.exists(image):
        raise FileNotFoundError(f"{image} does not exist.")

    if not output.endswith(".tif"):
        raise ValueError("Output must be a tif file.")

    output = check_file_path(output)

    if isinstance(mask, str):
        if mask.startswith("http"):
            mask = download_file(mask, output)
        if not os.path.exists(mask):
            raise FileNotFoundError(f"{mask} does not exist.")
    elif isinstance(mask, list) or isinstance(mask, dict):
        if isinstance(mask, list):
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Polygon", "coordinates": [mask]},
                    }
                ],
            }
        else:
            geojson = {
                "type": "FeatureCollection",
                "features": [mask],
            }
        mask = temp_file_path(".geojson")
        with open(mask, "w") as f:
            json.dump(geojson, f)

    with fiona.open(mask, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]

    with rasterio.open(image) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta

    out_meta.update(
        {
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        }
    )

    with rasterio.open(output, "w", **out_meta) as dest:
        dest.write(out_image)

    if to_cog:
        image_to_cog(output, output)


def netcdf_to_tif(
    filename,
    output=None,
    variables=None,
    shift_lon=True,
    lat="lat",
    lon="lon",
    lev="lev",
    level_index=0,
    time=0,
    return_vars=False,
    **kwargs,
):
    """Convert a netcdf file to a GeoTIFF file.

    Args:
        filename (str): Path to the netcdf file.
        output (str, optional): Path to the output GeoTIFF file. Defaults to None. If None, the output file will be the same as the input file with the extension changed to .tif.
        variables (str | list, optional): Name of the variable or a list of variables to extract. Defaults to None. If None, all variables will be extracted.
        shift_lon (bool, optional): Flag to shift longitude values from [0, 360] to the range [-180, 180]. Defaults to True.
        lat (str, optional): Name of the latitude variable. Defaults to 'lat'.
        lon (str, optional): Name of the longitude variable. Defaults to 'lon'.
        lev (str, optional): Name of the level variable. Defaults to 'lev'.
        level_index (int, optional): Index of the level dimension. Defaults to 0'.
        time (int, optional): Index of the time dimension. Defaults to 0'.
        return_vars (bool, optional): Flag to return all variables. Defaults to False.

    Raises:
        ImportError: If the xarray or rioxarray package is not installed.
        FileNotFoundError: If the netcdf file is not found.
        ValueError: If the variable is not found in the netcdf file.
    """
    try:
        import xarray as xr
    except ImportError as e:
        raise ImportError(e)

    if filename.startswith("http"):
        filename = download_file(filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    if output is None:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".nc", ".nc4"]:
            raise TypeError(
                "The output file must be a netCDF with extension .nc or .nc4."
            )
        output = filename.replace(ext, ".tif")
    else:
        output = check_file_path(output)

    xds = xr.open_dataset(filename, **kwargs)

    coords = list(xds.coords.keys())
    if "time" in coords:
        xds = xds.isel(time=time, drop=True)

    if lev in coords:
        xds = xds.isel(lev=level_index, drop=True)

    if shift_lon:
        xds.coords[lon] = (xds.coords[lon] + 180) % 360 - 180
        xds = xds.sortby(xds.lon)

    allowed_vars = list(xds.data_vars.keys())
    if isinstance(variables, str):
        if variables not in allowed_vars:
            raise ValueError(f"{variables} is not a valid variable.")
        variables = [variables]

    if variables is not None and (not set(variables).issubset(allowed_vars)):
        raise ValueError(f"{variables} must be a subset of {allowed_vars}.")

    if variables is None:
        xds.rio.set_spatial_dims(x_dim=lon, y_dim=lat).rio.to_raster(output)
    else:
        xds[variables].rio.set_spatial_dims(x_dim=lon, y_dim=lat).rio.to_raster(output)

    if return_vars:
        return output, allowed_vars
    else:
        return output


def read_netcdf(filename, **kwargs):
    """Read a netcdf file.

    Args:
        filename (str): File path or HTTP URL to the netcdf file.

    Raises:
        ImportError: If the xarray or rioxarray package is not installed.
        FileNotFoundError: If the netcdf file is not found.

    Returns:
        xarray.Dataset: The netcdf file as an xarray dataset.
    """
    try:
        import xarray as xr
    except ImportError as e:
        raise ImportError(e)

    if filename.startswith("http"):
        filename = download_file(filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    xds = xr.open_dataset(filename, **kwargs)
    return xds


def netcdf_tile_layer(
    filename,
    variables=None,
    palette=None,
    vmin=None,
    vmax=None,
    nodata=None,
    port="default",
    debug=False,
    projection="EPSG:3857",
    attribution=None,
    tile_format="ipyleaflet",
    layer_name="NetCDF layer",
    return_client=False,
    shift_lon=True,
    lat="lat",
    lon="lon",
    **kwargs,
):
    """Generate an ipyleaflet/folium TileLayer from a netCDF file.
        If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer),
        try adding to following two lines to the beginning of the notebook if the raster does not render properly.

        import os
        os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f'{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}'

    Args:
        filename (str): File path or HTTP URL to the netCDF file.
        variables (int, optional): The variable/band names to extract data from the netCDF file. Defaults to None. If None, all variables will be extracted.
        port (str, optional): The port to use for the server. Defaults to "default".
        palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
        vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
        vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
        nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
        debug (bool, optional): If True, the server will be started in debug mode. Defaults to False.
        projection (str, optional): The projection of the GeoTIFF. Defaults to "EPSG:3857".
        attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
        tile_format (str, optional): The tile layer format. Can be either ipyleaflet or folium. Defaults to "ipyleaflet".
        layer_name (str, optional): The layer name to use. Defaults to "NetCDF layer".
        return_client (bool, optional): If True, the tile client will be returned. Defaults to False.
        shift_lon (bool, optional): Flag to shift longitude values from [0, 360] to the range [-180, 180]. Defaults to True.
        lat (str, optional): Name of the latitude variable. Defaults to 'lat'.
        lon (str, optional): Name of the longitude variable. Defaults to 'lon'.

    Returns:
        ipyleaflet.TileLayer | folium.TileLayer: An ipyleaflet.TileLayer or folium.TileLayer.
    """

    check_package(
        "localtileserver", URL="https://github.com/banesullivan/localtileserver"
    )

    try:
        import xarray as xr
    except ImportError as e:
        raise ImportError(e)

    if filename.startswith("http"):
        filename = download_file(filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    output = filename.replace(".nc", ".tif")

    xds = xr.open_dataset(filename, **kwargs)

    if shift_lon:
        xds.coords[lon] = (xds.coords[lon] + 180) % 360 - 180
        xds = xds.sortby(xds.lon)

    allowed_vars = list(xds.data_vars.keys())
    if isinstance(variables, str):
        if variables not in allowed_vars:
            raise ValueError(f"{variables} is not a subset of {allowed_vars}.")
        variables = [variables]

    if variables is not None and len(variables) > 3:
        raise ValueError("Only 3 variables can be plotted at a time.")

    if variables is not None and (not set(variables).issubset(allowed_vars)):
        raise ValueError(f"{variables} must be a subset of {allowed_vars}.")

    xds.rio.set_spatial_dims(x_dim=lon, y_dim=lat).rio.to_raster(output)
    if variables is None:
        if len(allowed_vars) >= 3:
            band_idx = [1, 2, 3]
        else:
            band_idx = [1]
    else:
        band_idx = [allowed_vars.index(var) + 1 for var in variables]

    tile_layer = get_local_tile_layer(
        output,
        port=port,
        debug=debug,
        projection=projection,
        band=band_idx,
        palette=palette,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
        attribution=attribution,
        tile_format=tile_format,
        layer_name=layer_name,
        return_client=return_client,
    )
    return tile_layer


def classify(
    data,
    column,
    cmap=None,
    colors=None,
    labels=None,
    scheme="Quantiles",
    k=5,
    legend_kwds=None,
    classification_kwds=None,
):
    """Classify a dataframe column using a variety of classification schemes.

    Args:
        data (str | pd.DataFrame | gpd.GeoDataFrame): The data to classify. It can be a filepath to a vector dataset, a pandas dataframe, or a geopandas geodataframe.
        column (str): The column to classify.
        cmap (str, optional): The name of a colormap recognized by matplotlib. Defaults to None.
        colors (list, optional): A list of colors to use for the classification. Defaults to None.
        labels (list, optional): A list of labels to use for the legend. Defaults to None.
        scheme (str, optional): Name of a choropleth classification scheme (requires mapclassify).
            Name of a choropleth classification scheme (requires mapclassify).
            A mapclassify.MapClassifier object will be used
            under the hood. Supported are all schemes provided by mapclassify (e.g.
            'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
            'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
            'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
            'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
            'UserDefined'). Arguments can be passed in classification_kwds.
        k (int, optional): Number of classes (ignored if scheme is None or if column is categorical). Default to 5.
        legend_kwds (dict, optional): Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or `matplotlib.pyplot.colorbar`. Defaults to None.
            Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or
            Additional accepted keywords when `scheme` is specified:
            fmt : string
                A formatting specification for the bin edges of the classes in the
                legend. For example, to have no decimals: ``{"fmt": "{:.0f}"}``.
            labels : list-like
                A list of legend labels to override the auto-generated labblels.
                Needs to have the same number of elements as the number of
                classes (`k`).
            interval : boolean (default False)
                An option to control brackets from mapclassify legend.
                If True, open/closed interval brackets are shown in the legend.
        classification_kwds (dict, optional): Keyword arguments to pass to mapclassify. Defaults to None.

    Returns:
        pd.DataFrame, dict: A pandas dataframe with the classification applied and a legend dictionary.
    """

    import warnings
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    try:
        import mapclassify
    except ImportError:
        raise ImportError(
            "mapclassify is required for this function. Install with `pip install mapclassify`."
        )

    if isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame):
        df = data
    else:
        try:
            df = gpd.read_file(data)
        except Exception:
            raise TypeError(
                "Data must be a GeoDataFrame or a path to a file that can be read by geopandas.read_file()."
            )

    if df.empty:
        warnings.warn(
            "The GeoDataFrame you are attempting to plot is "
            "empty. Nothing has been displayed.",
            UserWarning,
        )
        return

    columns = df.columns.values.tolist()
    if column not in columns:
        raise ValueError(
            f"{column} is not a column in the GeoDataFrame. It must be one of {columns}."
        )

    # Convert categorical data to numeric
    init_column = None
    value_list = None
    if np.issubdtype(df[column].dtype, np.object0):
        value_list = df[column].unique().tolist()
        value_list.sort()
        df["category"] = df[column].replace(value_list, range(0, len(value_list)))
        init_column = column
        column = "category"
        k = len(value_list)

    if legend_kwds is not None:
        legend_kwds = legend_kwds.copy()

    # To accept pd.Series and np.arrays as column
    if isinstance(column, (np.ndarray, pd.Series)):
        if column.shape[0] != df.shape[0]:
            raise ValueError(
                "The dataframe and given column have different number of rows."
            )
        else:
            values = column

            # Make sure index of a Series matches index of df
            if isinstance(values, pd.Series):
                values = values.reindex(df.index)
    else:
        values = df[column]

    values = df[column]
    nan_idx = np.asarray(pd.isna(values), dtype="bool")

    if cmap is None:
        cmap = "Blues"
    cmap = plt.cm.get_cmap(cmap, k)
    if colors is None:
        colors = [mpl.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
        colors = ["#" + i for i in colors]
    elif isinstance(colors, list):
        colors = [check_color(i) for i in colors]
    elif isinstance(colors, str):
        colors = [check_color(colors)] * k

    allowed_schemes = [
        "BoxPlot",
        "EqualInterval",
        "FisherJenks",
        "FisherJenksSampled",
        "HeadTailBreaks",
        "JenksCaspall",
        "JenksCaspallForced",
        "JenksCaspallSampled",
        "MaxP",
        "MaximumBreaks",
        "NaturalBreaks",
        "Quantiles",
        "Percentiles",
        "StdMean",
        "UserDefined",
    ]

    if scheme.lower() not in [s.lower() for s in allowed_schemes]:
        raise ValueError(
            f"{scheme} is not a valid scheme. It must be one of {allowed_schemes}."
        )

    if classification_kwds is None:
        classification_kwds = {}
    if "k" not in classification_kwds:
        classification_kwds["k"] = k

    binning = mapclassify.classify(
        np.asarray(values[~nan_idx]), scheme, **classification_kwds
    )
    df["category"] = binning.yb
    df["color"] = [colors[i] for i in df["category"]]

    if legend_kwds is None:
        legend_kwds = {}

    if "interval" not in legend_kwds:
        legend_kwds["interval"] = True

    if "fmt" not in legend_kwds:
        if np.issubdtype(df[column].dtype, np.floating):
            legend_kwds["fmt"] = "{:.2f}"
        else:
            legend_kwds["fmt"] = "{:.0f}"

    if labels is None:
        # set categorical to True for creating the legend
        if legend_kwds is not None and "labels" in legend_kwds:
            if len(legend_kwds["labels"]) != binning.k:
                raise ValueError(
                    "Number of labels must match number of bins, "
                    "received {} labels for {} bins".format(
                        len(legend_kwds["labels"]), binning.k
                    )
                )
            else:
                labels = list(legend_kwds.pop("labels"))
        else:
            # fmt = "{:.2f}"
            if legend_kwds is not None and "fmt" in legend_kwds:
                fmt = legend_kwds.pop("fmt")

            labels = binning.get_legend_classes(fmt)
            if legend_kwds is not None:
                show_interval = legend_kwds.pop("interval", False)
            else:
                show_interval = False
            if not show_interval:
                labels = [c[1:-1] for c in labels]

        if init_column is not None:
            labels = value_list
    elif isinstance(labels, list):
        if len(labels) != len(colors):
            raise ValueError("The number of labels must match the number of colors.")
    else:
        raise ValueError("labels must be a list or None.")

    legend_dict = dict(zip(labels, colors))
    df["category"] = df["category"] + 1
    return df, legend_dict


def check_cmap(cmap):
    """Check the colormap and return a list of colors.

    Args:
        cmap (str | list | Box): The colormap to check.

    Returns:
        list: A list of colors.
    """

    from box import Box
    from .colormaps import get_palette

    if isinstance(cmap, str):
        try:
            return get_palette(cmap)
        except Exception as e:
            raise Exception(f"{cmap} is not a valid colormap.")
    elif isinstance(cmap, Box):
        return list(cmap["default"])
    elif isinstance(cmap, list) or isinstance(cmap, tuple):
        return cmap
    else:
        raise Exception(f"{cmap} is not a valid colormap.")


def plot_raster(
    image,
    band=None,
    cmap="terrain",
    proj="EPSG:3857",
    figsize=None,
    open_kwargs={},
    **kwargs,
):
    """Plot a raster image.

    Args:
        image (str | xarray.DataArray ): The input raster image, can be a file path, HTTP URL, or xarray.DataArray.
        band (int, optional): The band index, starting from zero. Defaults to None.
        cmap (str, optional): The matplotlib colormap to use. Defaults to "terrain".
        proj (str, optional): The EPSG projection code. Defaults to "EPSG:3857".
        figsize (tuple, optional): The figure size as a tuple, such as (10, 8). Defaults to None.
        open_kwargs (dict, optional): The keyword arguments to pass to rioxarray.open_rasterio. Defaults to {}.
        **kwargs: Additional keyword arguments to pass to xarray.DataArray.plot().

    """
    if os.environ.get("USE_MKDOCS") is not None:
        return

    try:
        import pvxarray
        import rioxarray
        import xarray
    except ImportError:
        print(
            "pyxarray and rioxarray are required for plotting. Please install them using 'pip install rioxarray pyvista-xarray'."
        )
        return

    if isinstance(image, str):
        da = rioxarray.open_rasterio(image, **open_kwargs)
    elif isinstance(image, xarray.DataArray):
        da = image
    else:
        raise ValueError("image must be a string or xarray.Dataset.")

    if band is not None:
        da = da[dict(band=band)]

    da = da.rio.reproject(proj)
    kwargs["cmap"] = cmap
    kwargs["figsize"] = figsize
    da.plot(**kwargs)


def plot_raster_3d(
    image,
    band=None,
    cmap="terrain",
    factor=1.0,
    proj="EPSG:3857",
    background=None,
    x=None,
    y=None,
    z=None,
    order=None,
    component=None,
    open_kwargs={},
    mesh_kwargs={},
    **kwargs,
):
    """Plot a raster image in 3D.

    Args:
        image (str | xarray.DataArray): The input raster image, can be a file path, HTTP URL, or xarray.DataArray.
        band (int, optional): The band index, starting from zero. Defaults to None.
        cmap (str, optional): The matplotlib colormap to use. Defaults to "terrain".
        factor (float, optional): The scaling factor for the raster. Defaults to 1.0.
        proj (str, optional): The EPSG projection code. Defaults to "EPSG:3857".
        background (str, optional): The background color. Defaults to None.
        x (str, optional): The x coordinate. Defaults to None.
        y (str, optional): The y coordinate. Defaults to None.
        z (str, optional): The z coordinate. Defaults to None.
        order (str, optional): The order of the coordinates. Defaults to None.
        component (str, optional): The component of the coordinates. Defaults to None.
        open_kwargs (dict, optional): The keyword arguments to pass to rioxarray.open_rasterio. Defaults to {}.
        mesh_kwargs (dict, optional): The keyword arguments to pass to pyvista.mesh.warp_by_scalar(). Defaults to {}.
        **kwargs: Additional keyword arguments to pass to xarray.DataArray.plot().
    """
    import sys

    if os.environ.get("USE_MKDOCS") is not None:
        return

    if "google.colab" in sys.modules:
        print("This function is not supported in Google Colab.")
        return

    try:
        import pvxarray
        import pyvista
        import rioxarray
        import xarray
    except ImportError:
        print(
            "pyxarray and rioxarray are required for plotting. Please install them using 'pip install rioxarray pyvista-xarray'."
        )
        return

    if isinstance(background, str):
        pyvista.global_theme.background = background

    if isinstance(image, str):
        da = rioxarray.open_rasterio(image, **open_kwargs)
    elif isinstance(image, xarray.DataArray):
        da = image
    else:
        raise ValueError("image must be a string or xarray.Dataset.")

    if band is not None:
        da = da[dict(band=band)]

    da = da.rio.reproject(proj)
    mesh_kwargs["factor"] = factor
    kwargs["cmap"] = cmap

    coords = list(da.coords)

    if x is None:
        if "x" in coords:
            x = "x"
        elif "lon" in coords:
            x = "lon"
    if y is None:
        if "y" in coords:
            y = "y"
        elif "lat" in coords:
            y = "lat"
    if z is None:
        if "z" in coords:
            z = "z"
        elif "elevation" in coords:
            z = "elevation"
        elif "band" in coords:
            z = "band"

    # Grab the mesh object for use with PyVista
    mesh = da.pyvista.mesh(x=x, y=y, z=z, order=order, component=component)

    # Warp top and plot in 3D
    mesh.warp_by_scalar(**mesh_kwargs).plot(**kwargs)


def github_raw_url(url):
    """Get the raw URL for a GitHub file.

    Args:
        url (str): The GitHub URL.
    Returns:
        str: The raw URL.
    """
    if isinstance(url, str) and url.startswith("https://github.com/") and "blob" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace(
            "blob/", ""
        )
    return url


def get_direct_url(url):
    """Get the direct URL for a given URL.

    Args:
        url (str): The URL to get the direct URL for.

    Returns:
        str: The direct URL.
    """

    if not isinstance(url, str):
        raise ValueError("url must be a string.")

    if not url.startswith("http"):
        raise ValueError("url must start with http.")

    r = requests.head(url, allow_redirects=True)
    return r.url


def add_crs(filename, epsg):
    """Add a CRS to a raster dataset.

    Args:
        filename (str): The filename of the raster dataset.
        epsg (int | str): The EPSG code of the CRS.

    """
    try:
        import rasterio
    except ImportError:
        raise ImportError(
            "rasterio is required for adding a CRS to a raster. Please install it using 'pip install rasterio'."
        )

    if not os.path.exists(filename):
        raise ValueError("filename must exist.")

    if isinstance(epsg, int):
        epsg = f"EPSG:{epsg}"
    elif isinstance(epsg, str):
        epsg = "EPSG:" + epsg
    else:
        raise ValueError("epsg must be an integer or string.")

    crs = rasterio.crs.CRS({"init": epsg})
    with rasterio.open(filename, mode="r+") as src:
        src.crs = crs


def html_to_streamlit(
    filename, width=None, height=None, scrolling=False, replace_dict={}
):
    """Renders an HTML file as a Streamlit component.
    Args:
        filename (str): The filename of the HTML file.
        width (int, optional): Width of the map. Defaults to None.
        height (int, optional): Height of the map. Defaults to 600.
        scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.
        replace_dict (dict, optional): A dictionary of strings to replace in the HTML file. Defaults to {}.

    Raises:
        ValueError: If the filename does not exist.

    Returns:
        streamlit.components: components.html object.
    """

    import streamlit.components.v1 as components

    if not os.path.exists(filename):
        raise ValueError("filename must exist.")

    f = open(filename, "r")

    html = f.read()

    for key, value in replace_dict.items():
        html = html.replace(key, value)

    f.close()
    return components.html(html, width=width, height=height, scrolling=scrolling)


class The_national_map_USGS:
    """
    The national map is a collection of topological datasets, maintained by the USGS.

    It provides an API endpoint which can be used to find downloadable links for the products offered.
        - Full description of datasets available can retrieved.
          This consists of metadata such as detail description and publication dates.
        - A wide range of dataformats are available

    This class is a tiny wrapper to find and download files using the API.

    More complete documentation for the API can be found at
        https://apps.nationalmap.gov/tnmaccess/#/
    """

    def __init__(self):
        self.api_endpoint = r"https://tnmaccess.nationalmap.gov/api/v1/"
        self.DS = self.datasets_full

    @property
    def datasets_full(self) -> list:
        """
        Full description of datasets provided.
        Returns a JSON or empty list.
        """
        link = f"{self.api_endpoint}datasets?"
        try:
            return requests.get(link).json()
        except Exception:
            print(f"Failed to load metadata from The National Map API endpoint\n{link}")
            return []

    @property
    def prodFormats(self) -> list:
        """
        Return all datatypes available in any of the collections.
        Note that "All" is only peculiar to one dataset.
        """
        return set(i["displayName"] for ds in self.DS for i in ds["formats"])

    @property
    def datasets(self) -> list:
        """
        Returns a list of dataset tags (most common human readable self description for specific datasets).
        """
        return set(y["sbDatasetTag"] for x in self.DS for y in x["tags"])

    def parse_region(self, region, geopandas_args={}) -> list:
        """

        Translate a Vector dataset to its bounding box.

        Args:
            region (str | list): an URL|filepath to a vector dataset to a polygon
            geopandas_reader_args (dict, optional): A dictionary of arguments to pass to the geopandas.read_file() function.
                Used for reading a region URL|filepath.
        """
        import geopandas as gpd

        if isinstance(region, str):
            if region.startswith("http"):
                region = github_raw_url(region)
                region = download_file(region)
            elif not os.path.exists(region):
                raise ValueError("region must be a path or a URL to a vector dataset.")

            roi = gpd.read_file(region, **geopandas_args)
            roi = roi.to_crs(epsg=4326)
            return roi.total_bounds
        return region

    def download_tiles(
        self, region=None, out_dir=None, download_args={}, geopandas_args={}, API={}
    ) -> None:
        """

        Download the US National Elevation Datasets (NED) for a region.

        Args:
            region (str | list, optional): An URL|filepath to a vector dataset Or a list of bounds in the form of [minx, miny, maxx, maxy].
                Alternatively you could use API parameters such as polygon or bbox.
            out_dir (str, optional): The directory to download the files to. Defaults to None, which uses the current working directory.
            download_args (dict, optional): A dictionary of arguments to pass to the download_file function. Defaults to {}.
            geopandas_args (dict, optional): A dictionary of arguments to pass to the geopandas.read_file() function.
                Used for reading a region URL|filepath.
            API (dict, optional): A dictionary of arguments to pass to the self.find_details() function.
                Exposes most of the documented API. Defaults to {}.

        Returns:
            None
        """

        if os.environ.get("USE_MKDOCS") is not None:
            return

        if out_dir is None:
            out_dir = os.getcwd()
        else:
            out_dir = os.path.abspath(out_dir)

        tiles = self.find_tiles(
            region, return_type="list", geopandas_args=geopandas_args, API=API
        )
        T = len(tiles)
        errors = 0
        done = 0

        for i, link in enumerate(tiles):
            file_name = os.path.basename(link)
            out_name = os.path.join(out_dir, file_name)
            if i < 5 or (i < 50 and not (i % 5)) or not (i % 20):
                print(f"Downloading {i+1} of {T}: {file_name}")
            try:
                download_file(link, out_name, **download_args)
                done += 1
            except KeyboardInterrupt:
                print("Cancelled download")
                break
            except Exception:
                errors += 1
                print(f"Failed to download {i+1} of {T}: {file_name}")

        print(
            f"{done} Downloads completed, {errors} downloads failed, {T} files available"
        )
        return

    def find_tiles(self, region=None, return_type="list", geopandas_args={}, API={}):
        """
        Find a list of downloadable files.

        Args:
            region (str | list, optional): An URL|filepath to a vector dataset Or a list of bounds in the form of [minx, miny, maxx, maxy].
                Alternatively you could use API parameters such as polygon or bbox.
            out_dir (str, optional): The directory to download the files to. Defaults to None, which uses the current working directory.
            return_type (str): list | dict. Defaults to list. Changes the return output type and content.
            geopandas_args (dict, optional): A dictionary of arguments to pass to the geopandas.read_file() function.
                Used for reading a region URL|filepath.
            API (dict, optional): A dictionary of arguments to pass to the self.find_details() function.
                Exposes most of the documented API parameters. Defaults to {}.

        Returns:
            list: A list of download_urls.
            dict: A dictionary with urls and related metadata
        """
        assert region or API, "Provide a region or use the API"

        if region:
            API["bbox"] = self.parse_region(region, geopandas_args)

        results = self.find_details(**API)
        if return_type == "list":
            return [i["downloadURL"] for i in results.get("items")]
        return results

    def find_details(
        self,
        bbox: List[float] = None,
        polygon: List[Tuple[float, float]] = None,
        datasets: str = None,
        prodFormats: str = None,
        prodExtents: str = None,
        q: str = None,
        dateType: str = None,
        start: str = None,
        end: str = None,
        offset: int = 0,
        max: int = None,
        outputFormat: str = "JSON",
        polyType: str = None,
        polyCode: str = None,
        extentQuery: int = None,
    ) -> Dict:
        """
        Possible search parameters (kwargs) support by API

        Parameter               Values
            Description
        ---------------------------------------------------------------------------------------------------
        bbox                    'minx, miny, maxx, maxy'
            Geographic longitude/latitude values expressed in  decimal degrees in a comma-delimited list.
        polygon                 '[x,y x,y x,y x,y x,y]'
            Polygon, longitude/latitude values expressed in decimal degrees in a space-delimited list.
        datasets                See: Datasets (Optional)
            Dataset tag name (sbDatasetTag)
            From https://apps.nationalmap.gov/tnmaccess/#/product
        prodFormats             See: Product Formats (Optional)
            Dataset-specific format

        prodExtents             See: Product Extents (Optional)
            Dataset-specific extent
        q                       free text
            Text input which can be used to filter by product titles and text descriptions.
        dateType                dateCreated | lastUpdated | Publication
            Type of date to search by.
        start                   'YYYY-MM-DD'
            Start date
        end                     'YYYY-MM-DD'
            End date (required if start date is provided)
        offset                  integer
            Offset into paginated results - default=0
        max                     integer
            Number of results returned
        outputFormat            JSON | CSV | pjson
            Default=JSON
        polyType                state | huc2 | huc4 | huc8
            Well Known Polygon Type. Use this parameter to deliver data by state or HUC
            (hydrologic unit codes defined by the Watershed Boundary Dataset/WBD)
        polyCode                state FIPS code or huc number
            Well Known Polygon Code. This value needs to coordinate with the polyType parameter.
        extentQuery             integer
            A Polygon code in the science base system, typically from an uploaded shapefile
        """

        try:
            # call locals before creating new locals
            used_locals = {k: v for k, v in locals().items() if v and k != "self"}

            # Parsing
            if polygon:
                used_locals["polygon"] = ",".join(
                    " ".join(map(str, point)) for point in polygon
                )
            if bbox:
                used_locals["bbox"] = str(bbox)[1:-1]

            if max:
                max += 2

            # Fetch response
            response = requests.get(f"{self.api_endpoint}products?", params=used_locals)
            if response.status_code // 100 == 2:
                return response.json()
            else:
                # Parameter validation handled by API endpoint error responses
                print(response.json())
            return {}
        except Exception as e:
            print(e)
            return {}


def download_tnm(
    region=None,
    out_dir=None,
    return_url=False,
    download_args={},
    geopandas_args={},
    API={},
) -> Union[None, List]:
    """Download the US National Elevation Datasets (NED) for a region.

    Args:
        region (str | list, optional): An URL|filepath to a vector dataset Or a list of bounds in the form of [minx, miny, maxx, maxy].
            Alternatively you could use API parameters such as polygon or bbox.
        out_dir (str, optional): The directory to download the files to. Defaults to None, which uses the current working directory.
        return_url (bool, optional): Whether to return the download URLs of the files. Defaults to False.
        download_args (dict, optional): A dictionary of arguments to pass to the download_file function. Defaults to {}.
        geopandas_args (dict, optional): A dictionary of arguments to pass to the geopandas.read_file() function.
            Used for reading a region URL|filepath.
        API (dict, optional): A dictionary of arguments to pass to the The_national_map_USGS.find_details() function.
            Exposes most of the documented API. Defaults to {}

    Returns:
        list: A list of the download URLs of the files if return_url is True.
    """

    if os.environ.get("USE_MKDOCS") is not None:
        return

    TNM = The_national_map_USGS()
    if return_url:
        return TNM.find_tiles(region=region, geopandas_args=geopandas_args, API=API)
    return TNM.download_tiles(
        region=region,
        out_dir=out_dir,
        download_args=download_args,
        geopandas_args=geopandas_args,
        API=API,
    )


def download_ned(
    region,
    out_dir=None,
    return_url=False,
    download_args={},
    geopandas_args={},
    query={},
) -> Union[None, List]:
    """Download the US National Elevation Datasets (NED) for a region.

    Args:
        region (str | list): A filepath to a vector dataset or a list of bounds in the form of [minx, miny, maxx, maxy].
        out_dir (str, optional): The directory to download the files to. Defaults to None, which uses the current working directory.
        return_url (bool, optional): Whether to return the download URLs of the files. Defaults to False.
        download_args (dict, optional): A dictionary of arguments to pass to the download_file function. Defaults to {}.
        geopandas_args (dict, optional): A dictionary of arguments to pass to the geopandas.read_file() function.
            Used for reading a region URL|filepath.
        query (dict, optional): A dictionary of arguments to pass to the The_national_map_USGS.find_details() function.
            See https://apps.nationalmap.gov/tnmaccess/#/product for more information.

    Returns:
        list: A list of the download URLs of the files if return_url is True.
    """

    if os.environ.get("USE_MKDOCS") is not None:
        return

    if not query:
        query = {
            "datasets": "National Elevation Dataset (NED) 1/3 arc-second",
            "prodFormats": "GeoTIFF",
        }

    TNM = The_national_map_USGS()
    if return_url:
        return TNM.find_tiles(region=region, geopandas_args=geopandas_args, API=query)
    return TNM.download_tiles(
        region=region,
        out_dir=out_dir,
        download_args=download_args,
        geopandas_args=geopandas_args,
        API=query,
    )


def mosaic(
    images,
    output,
    ext="tif",
    recursive=True,
    merge_args={},
    to_cog=True,
    verbose=True,
    **kwargs,
):
    """Mosaics a list of images into a single image. Inspired by https://bit.ly/3A6roDK.

    Args:
        images (str | list): An input directory containing images or a list of images.
        output (str): The output image filepath.
        ext (str, optional): The file extension of the images. Defaults to 'tif'.
        recursive (bool, optional): Whether to recursively search for images in the input directory. Defaults to True.
        merge_args (dict, optional): A dictionary of arguments to pass to the rasterio.merge function. Defaults to {}.
        to_cog (bool, optional): Whether to convert the output image to a Cloud Optimized GeoTIFF. Defaults to True.
        verbose (bool, optional): Whether to print progress. Defaults to True.

    """
    from rasterio.merge import merge
    import rasterio as rio
    from pathlib import Path

    output = os.path.abspath(output)

    if isinstance(images, str):
        raster_files = find_files(images, ext=ext, recursive=recursive)
    elif isinstance(images, list):
        raster_files = images
    else:
        raise ValueError("images must be a list of raster files.")

    raster_to_mosiac = []

    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    for index, p in enumerate(raster_files):
        if verbose:
            print(f"Reading {index+1}/{len(raster_files)}: {os.path.basename(p)}")
        raster = rio.open(p, **kwargs)
        raster_to_mosiac.append(raster)

    if verbose:
        print("Merging rasters...")
    arr, transform = merge(raster_to_mosiac, **merge_args)

    output_meta = raster.meta.copy()
    output_meta.update(
        {
            "driver": "GTiff",
            "height": arr.shape[1],
            "width": arr.shape[2],
            "transform": transform,
        }
    )

    with rio.open(output, "w", **output_meta) as m:
        m.write(arr)

    if to_cog:
        if verbose:
            print("Converting to COG...")
        image_to_cog(output, output)

    if verbose:
        print(f"Saved mosaic to {output}")


def geometry_bounds(geometry, decimals=4):
    """Returns the bounds of a geometry.

    Args:
        geometry (dict): A GeoJSON geometry.
        decimals (int, optional): The number of decimal places to round the bounds to. Defaults to 4.

    Returns:
        list: A list of bounds in the form of [minx, miny, maxx, maxy].
    """
    if isinstance(geometry, dict):
        if "geometry" in geometry:
            coords = geometry["geometry"]["coordinates"][0]
        else:
            coords = geometry["coordinates"][0]

    else:
        raise ValueError("geometry must be a GeoJSON-like dictionary.")

    x = [p[0] for p in coords]
    y = [p[1] for p in coords]
    west = round(min(x), decimals)
    east = round(max(x), decimals)
    south = round(min(y), decimals)
    north = round(max(y), decimals)
    return [west, south, east, north]


def reproject(
    image, output, dst_crs="EPSG:4326", resampling="nearest", to_cog=True, **kwargs
):
    """Reprojects an image.

    Args:
        image (str): The input image filepath.
        output (str): The output image filepath.
        dst_crs (str, optional): The destination CRS. Defaults to "EPSG:4326".
        resampling (Resampling, optional): The resampling method. Defaults to "nearest".
        to_cog (bool, optional): Whether to convert the output image to a Cloud Optimized GeoTIFF. Defaults to True.
        **kwargs: Additional keyword arguments to pass to rasterio.open.

    """
    import rasterio as rio
    from rasterio.warp import calculate_default_transform, reproject, Resampling

    if isinstance(resampling, str):
        resampling = getattr(Resampling, resampling)

    image = os.path.abspath(image)
    output = os.path.abspath(output)

    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    with rio.open(image, **kwargs) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update(
            {
                "crs": dst_crs,
                "transform": transform,
                "width": width,
                "height": height,
            }
        )

        with rio.open(output, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resampling,
                    **kwargs,
                )

    if to_cog:
        image_to_cog(output, output)


def image_check(image):
    from localtileserver import TileClient

    if isinstance(image, str):
        if image.startswith("http") or os.path.exists(image):
            pass
        else:
            raise ValueError("image must be a URL or filepath.")
    elif isinstance(image, TileClient):
        pass
    else:
        raise ValueError("image must be a URL or filepath.")


def image_client(image, **kwargs):
    """Get a LocalTileserver TileClient from an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        TileClient: A LocalTileserver TileClient.
    """
    image_check(image)

    _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    return client


def image_center(image, **kwargs):
    """Get the center of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        tuple: A tuple of (latitude, longitude).
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.center()


def image_bounds(image, **kwargs):
    """Get the bounds of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        list: A list of bounds in the form of [(south, west), (north, east)].
    """

    image_check(image)
    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    bounds = client.bounds()
    return [(bounds[0], bounds[2]), (bounds[1], bounds[3])]


def image_metadata(image, **kwargs):
    """Get the metadata of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        dict: A dictionary of image metadata.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()


def image_bandcount(image, **kwargs):
    """Get the number of bands in an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        int: The number of bands in the image.
    """

    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return len(client.metadata()["bands"])


def image_size(image, **kwargs):
    """Get the size (width, height) of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        tuple: A tuple of (width, height).
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image

    metadata = client.metadata()
    return metadata["sourceSizeX"], metadata["sourceSizeY"]


def image_projection(image, **kwargs):
    """Get the projection of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        str: The projection of the image.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()["Projection"]


def image_set_crs(image, epsg):
    """Define the CRS of an image.

    Args:
        image (str): The input image filepath
        epsg (int): The EPSG code of the CRS to set.
    """

    from rasterio.crs import CRS
    import rasterio

    with rasterio.open(image, "r+") as rds:
        rds.crs = CRS.from_epsg(epsg)


def image_geotransform(image, **kwargs):
    """Get the geotransform of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        list: A list of geotransform values.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()["GeoTransform"]


def image_resolution(image, **kwargs):
    """Get the resolution of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        float: The resolution of the image.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()["GeoTransform"][1]


def find_files(input_dir, ext=None, fullpath=True, recursive=True):
    """Find files in a directory.

    Args:
        input_dir (str): The input directory.
        ext (str, optional): The file extension to match. Defaults to None.
        fullpath (bool, optional): Whether to return the full path. Defaults to True.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Returns:
        list: A list of matching files.
    """

    from pathlib import Path

    files = []

    if ext is None:
        ext = "*"
    else:
        ext = ext.replace(".", "")

    ext = f"*.{ext}"

    if recursive:
        if fullpath:
            files = [str(path.joinpath()) for path in Path(input_dir).rglob(ext)]
        else:
            files = [str(path.name) for path in Path(input_dir).rglob(ext)]
    else:
        if fullpath:
            files = [str(path.joinpath()) for path in Path(input_dir).glob(ext)]
        else:
            files = [path.name for path in Path(input_dir).glob(ext)]

    files.sort()
    return files


def zoom_level_resolution(zoom, latitude=0):
    """Returns the approximate pixel scale based on zoom level and latutude.
        See https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution

    Args:
        zoom (int): The zoom level.
        latitude (float, optional): The latitude. Defaults to 0.

    Returns:
        float: Map resolution in meters.
    """
    import math

    resolution = 156543.04 * math.cos(latitude) / math.pow(2, zoom)
    return abs(resolution)


def lnglat_to_meters(longitude, latitude):
    """coordinate conversion between lat/lon in decimal degrees to web mercator

    Args:
        longitude (float): The longitude.
        latitude (float): The latitude.

    Returns:
        tuple: A tuple of (x, y) in meters.
    """
    import numpy as np

    origin_shift = np.pi * 6378137
    easting = longitude * origin_shift / 180.0
    northing = np.log(np.tan((90 + latitude) * np.pi / 360.0)) * origin_shift / np.pi

    if np.isnan(easting):
        if longitude > 0:
            easting = 20026376
        else:
            easting = -20026376

    if np.isnan(northing):
        if latitude > 0:
            northing = 20048966
        else:
            northing = -20048966

    return (easting, northing)


def meters_to_lnglat(x, y):
    """coordinate conversion between web mercator to lat/lon in decimal degrees

    Args:
        x (float): The x coordinate.
        y (float): The y coordinate.

    Returns:
        tuple: A tuple of (longitude, latitude) in decimal degrees.
    """
    import numpy as np

    origin_shift = np.pi * 6378137
    longitude = (x / origin_shift) * 180.0
    latitude = (y / origin_shift) * 180.0
    latitude = (
        180 / np.pi * (2 * np.arctan(np.exp(latitude * np.pi / 180.0)) - np.pi / 2.0)
    )
    return (longitude, latitude)


def bounds_to_xy_range(bounds):
    """Convert bounds to x and y range to be used as input to bokeh map.

    Args:
        bounds (list): A list of bounds in the form [(south, west), (north, east)] or [xmin, ymin, xmax, ymax].

    Returns:
        tuple: A tuple of (x_range, y_range).
    """

    if isinstance(bounds, tuple):
        bounds = list(bounds)
    elif not isinstance(bounds, list):
        raise TypeError("bounds must be a list")

    if len(bounds) == 4:
        west, south, east, north = bounds
    elif len(bounds) == 2:
        south, west = bounds[0]
        north, east = bounds[1]

    xmin, ymin = lnglat_to_meters(west, south)
    xmax, ymax = lnglat_to_meters(east, north)
    x_range = (xmin, xmax)
    y_range = (ymin, ymax)
    return x_range, y_range


def center_zoom_to_xy_range(center, zoom):
    """Convert center and zoom to x and y range to be used as input to bokeh map.

    Args:
        center (tuple): A tuple of (latitude, longitude).
        zoom (int): The zoom level.

    Returns:
        tuple: A tuple of (x_range, y_range).
    """

    if isinstance(center, tuple) or isinstance(center, list):
        pass
    else:
        raise TypeError("center must be a tuple or list")

    if not isinstance(zoom, int):
        raise TypeError("zoom must be an integer")

    latitude, longitude = center
    x_range = (-179, 179)
    y_range = (-70, 70)
    x_full_length = x_range[1] - x_range[0]
    y_full_length = y_range[1] - y_range[0]

    x_length = x_full_length / 2 ** (zoom - 2)
    y_length = y_full_length / 2 ** (zoom - 2)

    south = latitude - y_length / 2
    north = latitude + y_length / 2
    west = longitude - x_length / 2
    east = longitude + x_length / 2

    xmin, ymin = lnglat_to_meters(west, south)
    xmax, ymax = lnglat_to_meters(east, north)

    x_range = (xmin, xmax)
    y_range = (ymin, ymax)

    return x_range, y_range


def get_geometry_coords(row, geom, coord_type, shape_type, mercator=False):
    """
    Returns the coordinates ('x' or 'y') of edges of a Polygon exterior.

    :param: (GeoPandas Series) row : The row of each of the GeoPandas DataFrame.
    :param: (str) geom : The column name.
    :param: (str) coord_type : Whether it's 'x' or 'y' coordinate.
    :param: (str) shape_type
    """

    # Parse the exterior of the coordinate
    if shape_type.lower() in ["polygon", "multipolygon"]:
        exterior = row[geom].geoms[0].exterior
        if coord_type == "x":
            # Get the x coordinates of the exterior
            coords = list(exterior.coords.xy[0])
            if mercator:
                coords = [lnglat_to_meters(x, 0)[0] for x in coords]
            return coords

        elif coord_type == "y":
            # Get the y coordinates of the exterior
            coords = list(exterior.coords.xy[1])
            if mercator:
                coords = [lnglat_to_meters(0, y)[1] for y in coords]
            return coords

    elif shape_type.lower() in ["linestring", "multilinestring"]:
        if coord_type == "x":
            coords = list(row[geom].coords.xy[0])
            if mercator:
                coords = [lnglat_to_meters(x, 0)[0] for x in coords]
            return coords
        elif coord_type == "y":
            coords = list(row[geom].coords.xy[1])
            if mercator:
                coords = [lnglat_to_meters(0, y)[1] for y in coords]
            return coords

    elif shape_type.lower() in ["point", "multipoint"]:
        exterior = row[geom]

        if coord_type == "x":
            # Get the x coordinates of the exterior
            coords = exterior.coords.xy[0][0]
            if mercator:
                coords = lnglat_to_meters(coords, 0)[0]
            return coords

        elif coord_type == "y":
            # Get the y coordinates of the exterior
            coords = exterior.coords.xy[1][0]
            if mercator:
                coords = lnglat_to_meters(0, coords)[1]
            return coords


def gdf_to_bokeh(gdf):
    """
    Function to convert a GeoPandas GeoDataFrame to a Bokeh
    ColumnDataSource object.

    :param: (GeoDataFrame) gdf: GeoPandas GeoDataFrame with polygon(s) under
                                the column name 'geometry.'

    :return: ColumnDataSource for Bokeh.
    """
    from bokeh.plotting import ColumnDataSource

    shape_type = gdf_geom_type(gdf)

    gdf_new = gdf.drop("geometry", axis=1).copy()
    gdf_new["x"] = gdf.apply(
        get_geometry_coords,
        geom="geometry",
        coord_type="x",
        shape_type=shape_type,
        mercator=True,
        axis=1,
    )

    gdf_new["y"] = gdf.apply(
        get_geometry_coords,
        geom="geometry",
        coord_type="y",
        shape_type=shape_type,
        mercator=True,
        axis=1,
    )

    return ColumnDataSource(gdf_new)


def get_overlap(img1, img2, overlap, out_img1=None, out_img2=None, to_cog=True):
    """Get overlapping area of two images.

    Args:
        img1 (str): Path to the first image.
        img2 (str): Path to the second image.
        overlap (str): Path to the output overlap area in GeoJSON format.
        out_img1 (str, optional): Path to the cropped image of the first image.
        out_img2 (str, optional): Path to the cropped image of the second image.
        to_cog (bool, optional): Whether to convert the output images to COG.

    Returns:
        str: Path to the overlap area in GeoJSON format.
    """
    import json
    from osgeo import gdal, ogr, osr
    import geopandas as gpd

    extent = gdal.Info(img1, format="json")["wgs84Extent"]
    poly1 = ogr.CreateGeometryFromJson(json.dumps(extent))
    extent = gdal.Info(img2, format="json")["wgs84Extent"]
    poly2 = ogr.CreateGeometryFromJson(json.dumps(extent))
    intersection = poly1.Intersection(poly2)
    gg = gdal.OpenEx(intersection.ExportToJson())
    ds = gdal.VectorTranslate(
        overlap,
        srcDS=gg,
        format="GeoJSON",
        layerCreationOptions=["RFC7946=YES", "WRITE_BBOX=YES"],
    )
    ds = None

    d = gdal.Open(img1)
    proj = osr.SpatialReference(wkt=d.GetProjection())
    epsg = proj.GetAttrValue("AUTHORITY", 1)

    gdf = gpd.read_file(overlap)
    gdf.to_crs(epsg=epsg, inplace=True)
    gdf.to_file(overlap)

    if out_img1 is not None:
        clip_image(img1, overlap, out_img1, to_cog=to_cog)

    if out_img2 is not None:
        clip_image(img2, overlap, out_img2, to_cog=to_cog)

    return overlap


def add_mask_to_image(image, mask, output, color="red"):
    """Overlay a binary mask (e.g., roads, building footprints, etc) on an image. Credits to Xingjian Shi for the sample code.

    Args:
        image (str): A local path or HTTP URL to an image.
        mask (str): A local path or HTTP URL to a binary mask.
        output (str): A local path to the output image.
        color (str, optional): Color of the mask. Defaults to 'red'.

    Raises:
        ImportError: If rasterio and detectron2 are not installed.
    """
    try:
        import rasterio
        from detectron2.utils.visualizer import Visualizer
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Please install rasterio and detectron2 to use this function. See https://detectron2.readthedocs.io/en/latest/tutorials/install.html"
        )

    ds = rasterio.open(image)
    image_arr = ds.read()

    mask_arr = rasterio.open(mask).read()

    vis = Visualizer(image_arr.transpose((1, 2, 0)))
    vis.draw_binary_mask(mask_arr[0] > 0, color=color)

    out_arr = Image.fromarray(vis.get_output().get_image())

    out_arr.save(output)

    if ds.crs is not None:
        numpy_to_cog(output, output, profile=image)


def is_on_aws():
    """Check if the current notebook is running on AWS.

    Returns:
        bool: True if the notebook is running on AWS.
    """

    import psutil

    output = psutil.Process().parent().cmdline()

    on_aws = False
    for item in output:
        if item.endswith(".aws") or "ec2-user" in item:
            on_aws = True
    return on_aws


def is_studio_lab():
    """Check if the current notebook is running on Studio Lab.

    Returns:
        bool: True if the notebook is running on Studio Lab.
    """

    import psutil

    output = psutil.Process().parent().cmdline()

    on_studio_lab = False
    for item in output:
        if "studiolab/bin" in item:
            on_studio_lab = True
    return on_studio_lab


def bbox_to_gdf(bbox, crs="epsg:4326"):
    """Convert a bounding box to a GeoPandas GeoDataFrame.

    Args:
        bbox (list): A bounding box in the format of [minx, miny, maxx, maxy].
        crs (str, optional): The CRS of the bounding box. Defaults to 'epsg:4326'.

    Returns:
        GeoDataFrame: A GeoDataFrame with a single polygon.
    """
    import geopandas as gpd
    from shapely.geometry import Polygon

    return gpd.GeoDataFrame(
        geometry=[Polygon.from_bounds(*bbox)],
        crs=crs,
    )


def bbox_to_polygon(bbox):
    """Convert a bounding box to a shapely Polygon.

    Args:
        bbox (list): A bounding box in the format of [minx, miny, maxx, maxy].

    Returns:
        Polygon: A shapely Polygon.
    """
    from shapely.geometry import Polygon

    return Polygon.from_bounds(*bbox)


def vector_area(vector, unit="m2", crs="epsg:3857"):
    """Calculate the area of a vector.

    Args:
        vector (str): A local path or HTTP URL to a vector.
        unit (str, optional): The unit of the area, can be 'm2', 'km2', 'ha', or 'acres'. Defaults to 'm2'.

    Returns:
        float: The area of the vector.
    """
    import geopandas as gpd

    if isinstance(vector, str):
        gdf = gpd.read_file(vector)
    elif isinstance(vector, gpd.GeoDataFrame):
        gdf = vector

    area = gdf.to_crs(crs).area.sum()

    if unit == "m2":
        return area
    elif unit == "km2":
        return area / 1000000
    elif unit == "ha":
        return area / 10000
    elif unit == "acres":
        return area / 4046.8564224
    else:
        raise ValueError("Invalid unit.")


def image_filesize(
    region,
    cellsize,
    bands=1,
    dtype="uint8",
    unit="MB",
    source_crs="epsg:4326",
    dst_crs="epsg:3857",
    bbox=False,
):
    """Calculate the size of an image in a given region and cell size.

    Args:
        region (list): A bounding box in the format of [minx, miny, maxx, maxy].
        cellsize (float): The resolution of the image.
        bands (int, optional): Number of bands. Defaults to 1.
        dtype (str, optional): Data type, such as unit8, float32. For more info,
            see https://numpy.org/doc/stable/user/basics.types.html. Defaults to 'uint8'.
        unit (str, optional): The unit of the output. Defaults to 'MB'.
        source_crs (str, optional): The CRS of the region. Defaults to 'epsg:4326'.
        dst_crs (str, optional): The destination CRS to calculate the area. Defaults to 'epsg:3857'.
        bbox (bool, optional): Whether to use the bounding box of the region to calculate the area. Defaults to False.

    Returns:
        float: The size of the image in a given unit.
    """
    import numpy as np
    import geopandas as gpd

    if bbox:
        if isinstance(region, gpd.GeoDataFrame):
            region = region.to_crs(dst_crs).total_bounds.tolist()
        elif isinstance(region, str) and os.path.exists(region):
            region = gpd.read_file(region).to_crs(dst_crs).total_bounds.tolist()
        elif isinstance(region, list):
            region = (
                bbox_to_gdf(region, crs=source_crs)
                .to_crs(dst_crs)
                .total_bounds.tolist()
            )
        else:
            raise ValueError("Invalid input region.")

        bytes = (
            np.prod(
                [
                    int((region[2] - region[0]) / cellsize),
                    int((region[3] - region[1]) / cellsize),
                    bands,
                ]
            )
            * np.dtype(dtype).itemsize
        )
    else:
        if isinstance(region, list):
            region = bbox_to_gdf(region, crs=source_crs)

        bytes = (
            vector_area(region, crs=dst_crs)
            / pow(cellsize, 2)
            * np.dtype(dtype).itemsize
            * bands
        )

    unit = unit.upper()

    if unit == "KB":
        return bytes / 1024
    elif unit == "MB":
        return bytes / pow(1024, 2)
    elif unit == "GB":
        return bytes / pow(1024, 3)
    elif unit == "TB":
        return bytes / pow(1024, 4)
    elif unit == "PB":
        return bytes / pow(1024, 5)
    else:
        return bytes


def is_jupyterlite():
    """Check if the current notebook is running on JupyterLite.

    Returns:
        book: True if the notebook is running on JupyterLite.
    """
    import sys

    if "pyodide" in sys.modules:
        return True
    else:
        return False


async def download_file_lite(url, output=None, binary=False, overwrite=False, **kwargs):
    """Download a file using Pyodide. This function is only available on JupyterLite. Call the function with await, such as await download_file_lite(url).

    Args:
        url (str): The URL of the file.
        output (str, optional): The local path to save the file. Defaults to None.
        binary (bool, optional): Whether the file is binary. Defaults to False.
        overwrite (bool, optional): Whether to overwrite the file if it exists. Defaults to False.
    """
    import sys
    import pyodide

    if "pyodide" not in sys.modules:
        raise ValueError("Pyodide is not available.")

    if output is None:
        output = os.path.basename(url)

    output = os.path.abspath(output)

    ext = os.path.splitext(output)[1]

    if ext in [".png", "jpg", ".tif", ".tiff", "zip", "gz", "bz2", "xz"]:
        binary = True

    if os.path.exists(output) and not overwrite:
        print(f"{output} already exists, skip downloading.")
        return output

    if binary:
        response = await pyodide.http.pyfetch(url)
        with open(output, "wb") as f:
            f.write(await response.bytes())

    else:
        obj = pyodide.http.open_url(url)
        with open(output, "w") as fd:
            shutil.copyfileobj(obj, fd)

    return output


def create_legend(
    title="Legend",
    labels=None,
    colors=None,
    legend_dict=None,
    builtin_legend=None,
    opacity=1.0,
    position="bottomright",
    draggable=True,
    output=None,
    style={},
):
    """Create a legend in HTML format. Reference: https://bit.ly/3oV6vnH

    Args:
        title (str, optional): Title of the legend. Defaults to 'Legend'. Defaults to "Legend".
        colors (list, optional): A list of legend colors. Defaults to None.
        labels (list, optional): A list of legend labels. Defaults to None.
        legend_dict (dict, optional): A dictionary containing legend items as keys and color as values.
            If provided, legend_keys and legend_colors will be ignored. Defaults to None.
        builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.
        opacity (float, optional): The opacity of the legend. Defaults to 1.0.
        position (str, optional): The position of the legend, can be one of the following:
            "topleft", "topright", "bottomleft", "bottomright". Defaults to "bottomright".
        draggable (bool, optional): If True, the legend can be dragged to a new position. Defaults to True.
        output (str, optional): The output file path (*.html) to save the legend. Defaults to None.
        style: Additional keyword arguments to style the legend, such as position, bottom, right, z-index,
            border, background-color, border-radius, padding, font-size, etc. The default style is:
            style = {
                'position': 'fixed',
                'z-index': '9999',
                'border': '2px solid grey',
                'background-color': 'rgba(255, 255, 255, 0.8)',
                'border-radius': '5px',
                'padding': '10px',
                'font-size': '14px',
                'bottom': '20px',
                'right': '5px'
            }

    Returns:
        str: The HTML code of the legend.
    """

    import pkg_resources
    from .legends import builtin_legends

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("leafmap", "leafmap.py"))
    legend_template = os.path.join(pkg_dir, "data/template/legend_style.html")

    if draggable:
        legend_template = os.path.join(pkg_dir, "data/template/legend.txt")

    if not os.path.exists(legend_template):
        raise FileNotFoundError("The legend template does not exist.")

    if labels is not None:
        if not isinstance(labels, list):
            print("The legend keys must be a list.")
            return
    else:
        labels = ["One", "Two", "Three", "Four", "etc"]

    if colors is not None:
        if not isinstance(colors, list):
            print("The legend colors must be a list.")
            return
        elif all(isinstance(item, tuple) for item in colors):
            try:
                colors = [rgb_to_hex(x) for x in colors]
            except Exception as e:
                print(e)
        elif all((item.startswith("#") and len(item) == 7) for item in colors):
            pass
        elif all((len(item) == 6) for item in colors):
            pass
        else:
            print("The legend colors must be a list of tuples.")
            return
    else:
        colors = [
            "#8DD3C7",
            "#FFFFB3",
            "#BEBADA",
            "#FB8072",
            "#80B1D3",
        ]

    if len(labels) != len(colors):
        print("The legend keys and values must be the same length.")
        return

    allowed_builtin_legends = builtin_legends.keys()
    if builtin_legend is not None:
        if builtin_legend not in allowed_builtin_legends:
            print(
                "The builtin legend must be one of the following: {}".format(
                    ", ".join(allowed_builtin_legends)
                )
            )
            return
        else:
            legend_dict = builtin_legends[builtin_legend]
            labels = list(legend_dict.keys())
            colors = list(legend_dict.values())

    if legend_dict is not None:
        if not isinstance(legend_dict, dict):
            print("The legend dict must be a dictionary.")
            return
        else:
            labels = list(legend_dict.keys())
            colors = list(legend_dict.values())
            if all(isinstance(item, tuple) for item in colors):
                try:
                    colors = [rgb_to_hex(x) for x in colors]
                except Exception as e:
                    print(e)

    allowed_positions = [
        "topleft",
        "topright",
        "bottomleft",
        "bottomright",
    ]
    if position not in allowed_positions:
        raise ValueError(
            "The position must be one of the following: {}".format(
                ", ".join(allowed_positions)
            )
        )

    if position == "bottomright":
        if "bottom" not in style:
            style["bottom"] = "20px"
        if "right" not in style:
            style["right"] = "5px"
        if "left" in style:
            del style["left"]
        if "top" in style:
            del style["top"]
    elif position == "bottomleft":
        if "bottom" not in style:
            style["bottom"] = "5px"
        if "left" not in style:
            style["left"] = "5px"
        if "right" in style:
            del style["right"]
        if "top" in style:
            del style["top"]
    elif position == "topright":
        if "top" not in style:
            style["top"] = "5px"
        if "right" not in style:
            style["right"] = "5px"
        if "left" in style:
            del style["left"]
        if "bottom" in style:
            del style["bottom"]
    elif position == "topleft":
        if "top" not in style:
            style["top"] = "5px"
        if "left" not in style:
            style["left"] = "5px"
        if "right" in style:
            del style["right"]
        if "bottom" in style:
            del style["bottom"]

    if "position" not in style:
        style["position"] = "fixed"
    if "z-index" not in style:
        style["z-index"] = "9999"
    if "background-color" not in style:
        style["background-color"] = "rgba(255, 255, 255, 0.8)"
    if "padding" not in style:
        style["padding"] = "10px"
    if "border-radius" not in style:
        style["border-radius"] = "5px"
    if "font-size" not in style:
        style["font-size"] = "14px"

    content = []

    with open(legend_template) as f:
        lines = f.readlines()

    if draggable:
        for index, line in enumerate(lines):
            if index < 36:
                content.append(line)
            elif index == 36:
                line = lines[index].replace("Legend", title)
                content.append(line)
            elif index < 39:
                content.append(line)
            elif index == 39:
                for i, color in enumerate(colors):
                    item = f"    <li><span style='background:{check_color(color)};opacity:{opacity};'></span>{labels[i]}</li>\n"
                    content.append(item)
            elif index > 41:
                content.append(line)
        content = content[3:-1]

    else:
        for index, line in enumerate(lines):
            if index < 8:
                content.append(line)
            elif index == 8:
                for key, value in style.items():
                    content.append(
                        "              {}: {};\n".format(key.replace("_", "-"), value)
                    )
            elif index < 17:
                pass
            elif index < 19:
                content.append(line)
            elif index == 19:
                content.append(line.replace("Legend", title))
            elif index < 22:
                content.append(line)
            elif index == 22:
                for index, key in enumerate(labels):
                    color = colors[index]
                    if not color.startswith("#"):
                        color = "#" + color
                    item = "                    <li><span style='background:{};opacity:{};'></span>{}</li>\n".format(
                        color, opacity, key
                    )
                    content.append(item)
            elif index < 33:
                pass
            else:
                content.append(line)

    legend_text = "".join(content)

    if output is not None:
        with open(output, "w") as f:
            f.write(legend_text)
    else:
        return legend_text


def png_to_gif(in_dir, out_gif, fps=10, loop=0):
    """Convert a list of png images to gif.

    Args:
        in_dir (str): The input directory containing png images.
        out_gif (str): The output file path to the gif.
        fps (int, optional): Frames per second. Defaults to 10.
        loop (bool, optional): controls how many times the animation repeats. 1 means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    Raises:
        FileNotFoundError: No png images could be found.
    """
    import glob

    from PIL import Image

    if not out_gif.endswith(".gif"):
        raise ValueError("The out_gif must be a gif file.")

    out_gif = os.path.abspath(out_gif)

    out_dir = os.path.dirname(out_gif)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Create the frames
    frames = []
    imgs = list(glob.glob(os.path.join(in_dir, "*.png")))
    imgs.sort()

    if len(imgs) == 0:
        raise FileNotFoundError(f"No png could be found in {in_dir}.")

    for i in imgs:
        new_frame = Image.open(i)
        frames.append(new_frame)

    # Save into a GIF file that loops forever
    frames[0].save(
        out_gif,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=1000 / fps,
        loop=loop,
    )


def add_text_to_gif(
    in_gif,
    out_gif,
    xy=None,
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#000000",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    duration=100,
    loop=0,
):
    """Adds animated text to a GIF image.

    Args:
        in_gif (str): The file path to the input GIF image.
        out_gif (str): The file path to the output GIF image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        duration (int, optional): controls how long each frame will be displayed for, in milliseconds. It is the inverse of the frame rate. Setting it to 100 milliseconds gives 10 frames per second. You can decrease the duration to give a smoother animation.. Defaults to 100.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    """
    import io
    import warnings

    import pkg_resources
    from PIL import Image, ImageDraw, ImageFont, ImageSequence

    warnings.simplefilter("ignore")
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("leafmap", "leafmap.py"))
    default_font = os.path.join(pkg_dir, "data/fonts/arial.ttf")

    in_gif = os.path.abspath(in_gif)
    out_gif = os.path.abspath(out_gif)

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if font_type == "arial.ttf":
        font = ImageFont.truetype(default_font, font_size)
    elif font_type == "alibaba.otf":
        default_font = os.path.join(pkg_dir, "data/fonts/alibaba.otf")
        font = ImageFont.truetype(default_font, font_size)
    else:
        try:
            font_list = system_fonts(show_full_path=True)
            font_names = [os.path.basename(f) for f in font_list]
            if (font_type in font_list) or (font_type in font_names):
                font = ImageFont.truetype(font_type, font_size)
            else:
                print(
                    "The specified font type could not be found on your system. Using the default font instead."
                )
                font = ImageFont.truetype(default_font, font_size)
        except Exception as e:
            print(e)
            font = ImageFont.truetype(default_font, font_size)

    color = check_color(font_color)
    progress_bar_color = check_color(progress_bar_color)

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print("An error occurred while opening the gif.")
        print(e)
        return

    count = image.n_frames
    W, H = image.size
    progress_bar_widths = [i * 1.0 / count * W for i in range(1, count + 1)]
    progress_bar_shapes = [
        [(0, H - progress_bar_height), (x, H)] for x in progress_bar_widths
    ]

    if xy is None:
        # default text location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                f"xy is out of bounds. x must be within [0, {W}], and y must be within [0, {H}]"
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = int(float(x.replace("%", "")) / 100.0 * W)
                y = int(float(y.replace("%", "")) / 100.0 * H)
                xy = (x, y)
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )
    else:
        print(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )
        return

    if text_sequence is None:
        text = [str(x) for x in range(1, count + 1)]
    elif isinstance(text_sequence, int):
        text = [str(x) for x in range(text_sequence, text_sequence + count + 1)]
    elif isinstance(text_sequence, str):
        try:
            text_sequence = int(text_sequence)
            text = [str(x) for x in range(text_sequence, text_sequence + count + 1)]
        except Exception:
            text = [text_sequence] * count
    elif isinstance(text_sequence, list) and len(text_sequence) != count:
        print(
            f"The length of the text sequence must be equal to the number ({count}) of frames in the gif."
        )
        return
    else:
        text = [str(x) for x in text_sequence]

    try:
        frames = []
        # Loop over each frame in the animated image
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            # Draw the text on the frame
            frame = frame.convert("RGB")
            draw = ImageDraw.Draw(frame)
            # w, h = draw.textsize(text[index])
            draw.text(xy, text[index], font=font, fill=color)
            if add_progress_bar:
                draw.rectangle(progress_bar_shapes[index], fill=progress_bar_color)
            del draw

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)

            frames.append(frame)
        # https://www.pythoninformer.com/python-libraries/pillow/creating-animated-gif/
        # Save the frames as a new image

        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            optimize=True,
        )
    except Exception as e:
        print(e)


def add_progress_bar_to_gif(
    in_gif,
    out_gif,
    progress_bar_color="blue",
    progress_bar_height=5,
    duration=100,
    loop=0,
):
    """Adds a progress bar to a GIF image.

    Args:
        in_gif (str): The file path to the input GIF image.
        out_gif (str): The file path to the output GIF image.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        duration (int, optional): controls how long each frame will be displayed for, in milliseconds. It is the inverse of the frame rate. Setting it to 100 milliseconds gives 10 frames per second. You can decrease the duration to give a smoother animation. Defaults to 100.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    """
    import io
    import warnings

    from PIL import Image, ImageDraw, ImageSequence

    warnings.simplefilter("ignore")

    in_gif = os.path.abspath(in_gif)
    out_gif = os.path.abspath(out_gif)

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    progress_bar_color = check_color(progress_bar_color)

    try:
        image = Image.open(in_gif)
    except Exception as e:
        raise Exception("An error occurred while opening the gif.")

    count = image.n_frames
    W, H = image.size
    progress_bar_widths = [i * 1.0 / count * W for i in range(1, count + 1)]
    progress_bar_shapes = [
        [(0, H - progress_bar_height), (x, H)] for x in progress_bar_widths
    ]

    try:
        frames = []
        # Loop over each frame in the animated image
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            # Draw the text on the frame
            frame = frame.convert("RGB")
            draw = ImageDraw.Draw(frame)
            # w, h = draw.textsize(text[index])
            draw.rectangle(progress_bar_shapes[index], fill=progress_bar_color)
            del draw

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)

            frames.append(frame)
        # https://www.pythoninformer.com/python-libraries/pillow/creating-animated-gif/
        # Save the frames as a new image

        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            optimize=True,
        )
    except Exception as e:
        raise Exception(e)


def add_image_to_gif(
    in_gif, out_gif, in_image, xy=None, image_size=(80, 80), circle_mask=False
):
    """Adds an image logo to a GIF image.

    Args:
        in_gif (str): Input file path to the GIF image.
        out_gif (str): Output file path to the GIF image.
        in_image (str): Input file path to the image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        image_size (tuple, optional): Resize image. Defaults to (80, 80).
        circle_mask (bool, optional): Whether to apply a circle mask to the image. This only works with non-png images. Defaults to False.
    """
    import io
    import warnings

    from PIL import Image, ImageDraw, ImageSequence

    warnings.simplefilter("ignore")

    in_gif = os.path.abspath(in_gif)

    is_url = False
    if in_image.startswith("http"):
        is_url = True

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if (not is_url) and (not os.path.exists(in_image)):
        print("The provided logo file does not exist.")
        return

    out_dir = check_dir((os.path.dirname(out_gif)))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        gif = Image.open(in_gif)
    except Exception as e:
        print("An error occurred while opening the image.")
        print(e)
        return

    logo_raw_image = None
    try:
        if in_image.startswith("http"):
            logo_raw_image = open_image_from_url(in_image)
        else:
            in_image = os.path.abspath(in_image)
            logo_raw_image = Image.open(in_image)
    except Exception as e:
        print(e)

    logo_raw_size = logo_raw_image.size

    ratio = max(
        logo_raw_size[0] / image_size[0],
        logo_raw_size[1] / image_size[1],
    )
    image_resize = (int(logo_raw_size[0] / ratio), int(logo_raw_size[1] / ratio))
    image_size = min(logo_raw_size[0], image_size[0]), min(
        logo_raw_size[1], image_size[1]
    )

    logo_image = logo_raw_image.convert("RGBA")
    logo_image.thumbnail(image_size, Image.ANTIALIAS)

    gif_width, gif_height = gif.size
    mask_im = None

    if circle_mask:
        mask_im = Image.new("L", image_size, 0)
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, image_size[0], image_size[1]), fill=255)

    if has_transparency(logo_raw_image):
        mask_im = logo_image.copy()

    if xy is None:
        # default logo location is 5% width and 5% height of the image.
        delta = 10
        xy = (gif_width - image_resize[0] - delta, gif_height - image_resize[1] - delta)
        # xy = (int(0.05 * gif_width), int(0.05 * gif_height))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < gif_width) and (y > 0) and (y < gif_height):
            pass
        else:
            print(
                "xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]".format(
                    gif_width, gif_height
                )
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = int(float(x.replace("%", "")) / 100.0 * gif_width)
                y = int(float(y.replace("%", "")) / 100.0 * gif_height)
                xy = (x, y)
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )

    else:
        raise Exception(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )

    try:
        frames = []
        for _, frame in enumerate(ImageSequence.Iterator(gif)):
            frame = frame.convert("RGBA")
            frame.paste(logo_image, xy, mask_im)

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            frames.append(frame)

        frames[0].save(out_gif, save_all=True, append_images=frames[1:])
    except Exception as e:
        print(e)


def reduce_gif_size(in_gif, out_gif=None):
    """Reduces a GIF image using ffmpeg.

    Args:
        in_gif (str): The input file path to the GIF image.
        out_gif (str, optional): The output file path to the GIF image. Defaults to None.
    """
    import warnings

    try:
        import ffmpeg
    except ImportError:
        print("ffmpeg is not installed on your computer. Skip reducing gif size.")
        return

    warnings.filterwarnings("ignore")

    if not is_tool("ffmpeg"):
        print("ffmpeg is not installed on your computer. Skip reducing gif size.")
        return

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if out_gif is None:
        out_gif = in_gif
    elif not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if in_gif == out_gif:
        tmp_gif = in_gif.replace(".gif", "_tmp.gif")
        shutil.copyfile(in_gif, tmp_gif)
        stream = ffmpeg.input(tmp_gif)
        stream = ffmpeg.output(stream, in_gif, loglevel="quiet").overwrite_output()
        ffmpeg.run(stream)
        os.remove(tmp_gif)

    else:
        stream = ffmpeg.input(in_gif)
        stream = ffmpeg.output(stream, out_gif, loglevel="quiet").overwrite_output()
        ffmpeg.run(stream)


def make_gif(images, out_gif, ext="jpg", fps=10, loop=0, mp4=False, clean_up=False):
    """Creates a gif from a list of images.

    Args:
        images (list | str): The list of images or input directory to create the gif from.
        out_gif (str): File path to the output gif.
        ext (str, optional): The extension of the images. Defaults to 'jpg'.
        fps (int, optional): The frames per second of the gif. Defaults to 10.
        loop (int, optional): The number of times to loop the gif. Defaults to 0.
        mp4 (bool, optional): Whether to convert the gif to mp4. Defaults to False.

    """
    import glob
    from PIL import Image

    ext = ext.replace(".", "")

    if isinstance(images, str) and os.path.isdir(images):
        images = list(glob.glob(os.path.join(images, f"*.{ext}")))
        if len(images) == 0:
            raise ValueError("No images found in the input directory.")
    elif not isinstance(images, list):
        raise ValueError("images must be a list or a path to the image directory.")

    images.sort()

    frames = [Image.open(image) for image in images]
    frame_one = frames[0]
    frame_one.save(
        out_gif,
        format="GIF",
        append_images=frames,
        save_all=True,
        duration=int(1000 / fps),
        loop=loop,
    )

    if mp4:
        if not is_tool("ffmpeg"):
            print("ffmpeg is not installed on your computer.")
            return

        if os.path.exists(out_gif):
            out_mp4 = out_gif.replace(".gif", ".mp4")
            cmd = f"ffmpeg -loglevel error -i {out_gif} -vcodec libx264 -crf 25 -pix_fmt yuv420p {out_mp4}"
            os.system(cmd)
            if not os.path.exists(out_mp4):
                raise Exception(f"Failed to create mp4 file.")
    if clean_up:
        for image in images:
            os.remove(image)


def create_timelapse(
    images: Union[list, str],
    out_gif: str,
    ext: str = ".tif",
    bands: Optional[list] = None,
    size: Optional[tuple] = None,
    bbox: Optional[list] = None,
    fps: int = 5,
    loop: int = 0,
    add_progress_bar: bool = True,
    progress_bar_color: str = "blue",
    progress_bar_height: int = 5,
    add_text: bool = False,
    text_xy: Optional[tuple] = None,
    text_sequence: Optional[list] = None,
    font_type: str = "arial.ttf",
    font_size: int = 20,
    font_color: str = "black",
    mp4: bool = False,
    quiet: bool = True,
    reduce_size: bool = False,
    clean_up: bool = True,
    **kwargs,
):
    """Creates a timelapse gif from a list of images.

    Args:
        images (Union[list, str]): The list of images or input directory to create the gif from.
            For example, '/path/to/images/*.tif' or ['/path/to/image1.tif', '/path/to/image2.tif', ...]
        out_gif (str): File path to the output gif.
        ext (str, optional): The extension of the images. Defaults to '.tif'.
        bands (Optional[list], optional): The bands to use for the gif. For example, [0, 1, 2] for RGB, and [0] for grayscale. Defaults to None.
        size (Optional[tuple], optional): The size of the gif. For example, (500, 500). Defaults to None, using the original size.
        bbox (Optional[list], optional): The bounding box of the gif. For example, [xmin, ymin, xmax, ymax]. Defaults to None, using the original bounding box.
        fps (int, optional): The frames per second of the gif. Defaults to 5.
        loop (int, optional): The number of times to loop the gif. Defaults to 0, looping forever.
        add_progress_bar (bool, optional): Whether to add a progress bar to the gif. Defaults to True.
        progress_bar_color (str, optional): The color of the progress bar, can be color name or hex code. Defaults to 'blue'.
        progress_bar_height (int, optional): The height of the progress bar. Defaults to 5.
        add_text (bool, optional): Whether to add text to the gif. Defaults to False.
        text_xy (Optional[tuple], optional): The x, y coordinates of the text. For example, ('10%', '10%').
            Defaults to None, using the bottom left corner.
        text_sequence (Optional[list], optional): The sequence of text to add to the gif. For example, ['year 1', 'year 2', ...].
        font_type (str, optional): The font type of the text, can be 'arial.ttf' or 'alibaba.otf', or any system font. Defaults to 'arial.ttf'.
        font_size (int, optional): The font size of the text. Defaults to 20.
        font_color (str, optional): The color of the text, can be color name or hex code. Defaults to 'black'.
        mp4 (bool, optional): Whether to convert the gif to mp4. Defaults to False.
        quiet (bool, optional): Whether to print the progress. Defaults to False.
        reduce_size (bool, optional): Whether to reduce the size of the gif using ffmpeg. Defaults to False.
        clean_up (bool, optional): Whether to clean up the temporary files. Defaults to True.

    """

    import glob
    import tempfile

    if isinstance(images, str):
        if not images.endswith(ext):
            images = os.path.join(images, f"*{ext}")
        images = list(glob.glob(images))

    if not isinstance(images, list):
        raise ValueError("images must be a list or a path to the image directory.")

    images.sort()

    temp_dir = os.path.join(tempfile.gettempdir(), "timelapse")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    if bbox is not None:
        clip_dir = os.path.join(tempfile.gettempdir(), "clip")
        if not os.path.exists(clip_dir):
            os.makedirs(clip_dir)

        if len(bbox) == 4:
            bbox = bbox_to_geojson(bbox)

    else:
        clip_dir = None

    output = widgets.Output()

    if "out_ext" in kwargs:
        out_ext = kwargs["out_ext"].lower()
    else:
        out_ext = ".jpg"

    try:
        for index, image in enumerate(images):
            if bbox is not None:
                clip_file = os.path.join(clip_dir, os.path.basename(image))
                with output:
                    clip_image(image, mask=bbox, output=clip_file, to_cog=False)
                image = clip_file

            if "add_prefix" in kwargs:
                basename = (
                    str(f"{index + 1}").zfill(len(str(len(images))))
                    + "-"
                    + os.path.basename(image).replace(ext, out_ext)
                )
            else:
                basename = os.path.basename(image).replace(ext, out_ext)
            if not quiet:
                print(f"Processing {index+1}/{len(images)}: {basename} ...")

            # ignore GDAL warnings
            with output:
                numpy_to_image(
                    image, os.path.join(temp_dir, basename), bands=bands, size=size
                )
        make_gif(
            temp_dir,
            out_gif,
            ext=out_ext,
            fps=fps,
            loop=loop,
            mp4=mp4,
            clean_up=clean_up,
        )

        if clip_dir is not None:
            shutil.rmtree(clip_dir)

        if add_text:
            add_text_to_gif(
                out_gif,
                out_gif,
                text_xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                1000 / fps,
                loop,
            )
        elif add_progress_bar:
            add_progress_bar_to_gif(
                out_gif,
                out_gif,
                progress_bar_color,
                progress_bar_height,
                1000 / fps,
                loop,
            )

        if reduce_size:
            reduce_gif_size(out_gif)
    except Exception as e:
        print(e)


def gif_to_mp4(in_gif, out_mp4):
    """Converts a gif to mp4.

    Args:
        in_gif (str): The input gif file.
        out_mp4 (str): The output mp4 file.
    """
    from PIL import Image

    if not os.path.exists(in_gif):
        raise FileNotFoundError(f"{in_gif} does not exist.")

    out_mp4 = os.path.abspath(out_mp4)
    if not out_mp4.endswith(".mp4"):
        out_mp4 = out_mp4 + ".mp4"

    if not os.path.exists(os.path.dirname(out_mp4)):
        os.makedirs(os.path.dirname(out_mp4))

    if not is_tool("ffmpeg"):
        print("ffmpeg is not installed on your computer.")
        return

    width, height = Image.open(in_gif).size

    if width % 2 == 0 and height % 2 == 0:
        cmd = f"ffmpeg -loglevel error -i {in_gif} -vcodec libx264 -crf 25 -pix_fmt yuv420p {out_mp4}"
        os.system(cmd)
    else:
        width += width % 2
        height += height % 2
        cmd = f"ffmpeg -loglevel error -i {in_gif} -vf scale={width}:{height} -vcodec libx264 -crf 25 -pix_fmt yuv420p {out_mp4}"
        os.system(cmd)

    if not os.path.exists(out_mp4):
        raise Exception(f"Failed to create mp4 file.")


def merge_gifs(in_gifs, out_gif):
    """Merge multiple gifs into one.

    Args:
        in_gifs (str | list): The input gifs as a list or a directory path.
        out_gif (str): The output gif.

    Raises:
        Exception:  Raise exception when gifsicle is not installed.
    """
    import glob

    try:
        if isinstance(in_gifs, str) and os.path.isdir(in_gifs):
            in_gifs = glob.glob(os.path.join(in_gifs, "*.gif"))
        elif not isinstance(in_gifs, list):
            raise Exception("in_gifs must be a list.")

        in_gifs = " ".join(in_gifs)

        cmd = f"gifsicle {in_gifs} > {out_gif}"
        os.system(cmd)

    except Exception as e:
        print(
            "gifsicle is not installed. Run 'sudo apt-get install -y gifsicle' to install it."
        )
        print(e)


def gif_to_png(in_gif, out_dir=None, prefix="", verbose=True):
    """Converts a gif to png.

    Args:
        in_gif (str): The input gif file.
        out_dir (str, optional): The output directory. Defaults to None.
        prefix (str, optional): The prefix of the output png files. Defaults to None.
        verbose (bool, optional): Whether to print the progress. Defaults to True.

    Raises:
        FileNotFoundError: Raise exception when the input gif does not exist.
        Exception: Raise exception when ffmpeg is not installed.
    """
    import tempfile

    in_gif = os.path.abspath(in_gif)
    if " " in in_gif:
        raise Exception("in_gif cannot contain spaces.")
    if not os.path.exists(in_gif):
        raise FileNotFoundError(f"{in_gif} does not exist.")

    basename = os.path.basename(in_gif).replace(".gif", "")
    if out_dir is None:
        out_dir = os.path.join(tempfile.gettempdir(), basename)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    elif isinstance(out_dir, str) and not os.path.exists(out_dir):
        os.makedirs(out_dir)
    elif not isinstance(out_dir, str):
        raise Exception("out_dir must be a string.")

    out_dir = os.path.abspath(out_dir)
    cmd = f"ffmpeg -loglevel error -i {in_gif} -vsync 0 {out_dir}/{prefix}%d.png"
    os.system(cmd)

    if verbose:
        print(f"Images are saved to {out_dir}")


def gif_fading(in_gif, out_gif, duration=1, verbose=True):
    """Fade in/out the gif.

    Args:
        in_gif (str): The input gif file. Can be a directory path or http URL, e.g., "https://i.imgur.com/ZWSZC5z.gif"
        out_gif (str): The output gif file.
        duration (float, optional): The duration of the fading. Defaults to 1.
        verbose (bool, optional): Whether to print the progress. Defaults to True.

    Raises:
        FileNotFoundError: Raise exception when the input gif does not exist.
        Exception: Raise exception when ffmpeg is not installed.
    """
    import glob
    import tempfile

    current_dir = os.getcwd()

    if isinstance(in_gif, str) and in_gif.startswith("http"):
        ext = os.path.splitext(in_gif)[1]
        file_path = temp_file_path(ext)
        download_from_url(in_gif, file_path, verbose=verbose)
        in_gif = file_path

    in_gif = os.path.abspath(in_gif)
    if not in_gif.endswith(".gif"):
        raise Exception("in_gif must be a gif file.")

    if " " in in_gif:
        raise Exception("The filename cannot contain spaces.")

    out_gif = os.path.abspath(out_gif)
    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if not os.path.exists(in_gif):
        raise FileNotFoundError(f"{in_gif} does not exist.")

    basename = os.path.basename(in_gif).replace(".gif", "")
    temp_dir = os.path.join(tempfile.gettempdir(), basename)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    gif_to_png(in_gif, temp_dir, verbose=verbose)

    os.chdir(temp_dir)

    images = list(glob.glob(os.path.join(temp_dir, "*.png")))
    count = len(images)

    files = []
    for i in range(1, count + 1):
        files.append(f"-loop 1 -t {duration} -i {i}.png")
    inputs = " ".join(files)

    filters = []
    for i in range(1, count):
        if i == 1:
            filters.append(
                f"\"[1:v][0:v]blend=all_expr='A*(if(gte(T,3),1,T/3))+B*(1-(if(gte(T,3),1,T/3)))'[v0];"
            )
        else:
            filters.append(
                f"[{i}:v][{i-1}:v]blend=all_expr='A*(if(gte(T,3),1,T/3))+B*(1-(if(gte(T,3),1,T/3)))'[v{i-1}];"
            )

    last_filter = ""
    for i in range(count - 1):
        last_filter += f"[v{i}]"
    last_filter += f'concat=n={count-1}:v=1:a=0[v]" -map "[v]"'
    filters.append(last_filter)
    filters = " ".join(filters)

    cmd = f"ffmpeg -y -loglevel error {inputs} -filter_complex {filters} {out_gif}"

    os.system(cmd)
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(e)

    os.chdir(current_dir)


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    return shutil.which(name) is not None


def vector_to_gif(
    filename,
    out_gif,
    colname,
    vmin=None,
    vmax=None,
    step=1,
    facecolor="black",
    figsize=(10, 8),
    padding=3,
    title=None,
    add_text=True,
    xy=("1%", "1%"),
    fontsize=20,
    add_progress_bar=True,
    progress_bar_color="blue",
    progress_bar_height=5,
    dpi=300,
    fps=10,
    loop=0,
    mp4=False,
    keep_png=False,
    verbose=True,
    open_args={},
    plot_args={},
):
    """Convert a vector to a gif. This function was inspired by by Johannes Uhl's shapefile2gif repo at
            https://github.com/johannesuhl/shapefile2gif. Credits to Johannes Uhl.

    Args:
        filename (str): The input vector file. Can be a directory path or http URL, e.g., "https://i.imgur.com/ZWSZC5z.gif"
        out_gif (str): The output gif file.
        colname (str): The column name of the vector that contains numerical values.
        vmin (float, optional): The minimum value to filter the data. Defaults to None.
        vmax (float, optional): The maximum value to filter the data. Defaults to None.
        step (float, optional): The step to filter the data. Defaults to 1.
        facecolor (str, optional): The color to visualize the data. Defaults to "black".
        figsize (tuple, optional): The figure size. Defaults to (10, 8).
        padding (int, optional): The padding of the figure tight_layout. Defaults to 3.
        title (str, optional): The title of the figure. Defaults to None.
        add_text (bool, optional): Whether to add text to the figure. Defaults to True.
        xy (tuple, optional): The position of the text from the lower-left corner. Defaults to ("1%", "1%").
        fontsize (int, optional): The font size of the text. Defaults to 20.
        add_progress_bar (bool, optional): Whether to add a progress bar to the figure. Defaults to True.
        progress_bar_color (str, optional): The color of the progress bar. Defaults to "blue".
        progress_bar_height (int, optional): The height of the progress bar. Defaults to 5.
        dpi (int, optional): The dpi of the figure. Defaults to 300.
        fps (int, optional): The frames per seconc (fps) of the gif. Defaults to 10.
        loop (int, optional): The number of loops of the gif. Defaults to 0, infinite loop.
        mp4 (bool, optional): Whether to convert the gif to mp4. Defaults to False.
        keep_png (bool, optional): Whether to keep the png files. Defaults to False.
        verbose (bool, optional): Whether to print the progress. Defaults to True.
        open_args (dict, optional): The arguments for the geopandas.read_file() function. Defaults to {}.
        plot_args (dict, optional): The arguments for the geopandas.GeoDataFrame.plot() function. Defaults to {}.

    """
    import geopandas as gpd
    import matplotlib.pyplot as plt

    out_dir = os.path.dirname(out_gif)
    tmp_dir = os.path.join(out_dir, "tmp_png")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    if isinstance(filename, str):
        gdf = gpd.read_file(filename, **open_args)
    elif isinstance(filename, gpd.GeoDataFrame):
        gdf = filename
    else:
        raise ValueError(
            "filename must be a string or a geopandas.GeoDataFrame object."
        )

    bbox = gdf.total_bounds

    if colname not in gdf.columns:
        raise Exception(
            f"{colname} is not in the columns of the GeoDataFrame. It must be one of {gdf.columns}"
        )

    values = gdf[colname].unique().tolist()
    values.sort()

    if vmin is None:
        vmin = values[0]
    if vmax is None:
        vmax = values[-1]

    options = range(vmin, vmax + step, step)

    W = bbox[2] - bbox[0]
    H = bbox[3] - bbox[1]

    if xy is None:
        # default text location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        raise Exception("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")

    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                f"xy is out of bounds. x must be within [0, {W}], and y must be within [0, {H}]"
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = float(x.replace("%", "")) / 100.0 * W
                y = float(y.replace("%", "")) / 100.0 * H
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )
    else:
        raise Exception(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )

    x = bbox[0] + x
    y = bbox[1] + y

    for index, v in enumerate(options):
        if verbose:
            print(f"Processing {index+1}/{len(options)}: {v}...")
        yrdf = gdf[gdf[colname] <= v]
        fig, ax = plt.subplots()
        ax = yrdf.plot(facecolor=facecolor, figsize=figsize, **plot_args)
        ax.set_title(title, fontsize=fontsize)
        ax.set_axis_off()
        ax.set_xlim([bbox[0], bbox[2]])
        ax.set_ylim([bbox[1], bbox[3]])
        if add_text:
            ax.text(x, y, v, fontsize=fontsize)
        fig = ax.get_figure()
        plt.tight_layout(pad=padding)
        fig.savefig(tmp_dir + os.sep + "%s.png" % v, dpi=dpi)
        plt.clf()
        plt.close("all")

    png_to_gif(tmp_dir, out_gif, fps=fps, loop=loop)

    if add_progress_bar:
        add_progress_bar_to_gif(
            out_gif,
            out_gif,
            progress_bar_color,
            progress_bar_height,
            duration=1000 / fps,
            loop=loop,
        )

    if mp4:
        gif_to_mp4(out_gif, out_gif.replace(".gif", ".mp4"))

    if not keep_png:
        shutil.rmtree(tmp_dir)

    if verbose:
        print(f"Done. The GIF is saved to {out_gif}.")


def save_colorbar(
    out_fig=None,
    width=4.0,
    height=0.3,
    vmin=0,
    vmax=1.0,
    palette=None,
    vis_params=None,
    cmap="gray",
    discrete=False,
    label=None,
    label_size=10,
    label_weight="normal",
    tick_size=8,
    bg_color="white",
    orientation="horizontal",
    dpi="figure",
    transparent=False,
    show_colorbar=True,
    **kwargs,
):
    """Create a standalone colorbar and save it as an image.

    Args:
        out_fig (str): Path to the output image.
        width (float): Width of the colorbar in inches. Default is 4.0.
        height (float): Height of the colorbar in inches. Default is 0.3.
        vmin (float): Minimum value of the colorbar. Default is 0.
        vmax (float): Maximum value of the colorbar. Default is 1.0.
        palette (list): List of colors to use for the colorbar. It can also be a cmap name, such as ndvi, ndwi, dem, coolwarm. Default is None.
        vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
        cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
        discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
        label (str, optional): Label for the colorbar. Defaults to None.
        label_size (int, optional): Font size for the colorbar label. Defaults to 12.
        label_weight (str, optional): Font weight for the colorbar label, can be "normal", "bold", etc. Defaults to "normal".
        tick_size (int, optional): Font size for the colorbar tick labels. Defaults to 10.
        bg_color (str, optional): Background color for the colorbar. Defaults to "white".
        orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
        dpi (float | str, optional): The resolution in dots per inch.  If 'figure', use the figure's dpi value. Defaults to "figure".
        transparent (bool, optional): Whether to make the background transparent. Defaults to False.
        show_colorbar (bool, optional): Whether to show the colorbar. Defaults to True.
        **kwargs: Other keyword arguments to pass to matplotlib.pyplot.savefig().

    Returns:
        str: Path to the output image.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    from .colormaps import palettes, get_palette

    if out_fig is None:
        out_fig = temp_file_path("png")
    else:
        out_fig = check_file_path(out_fig)

    if vis_params is None:
        vis_params = {}
    elif not isinstance(vis_params, dict):
        raise TypeError("The vis_params must be a dictionary.")

    if palette is not None:
        if palette in ["ndvi", "ndwi", "dem"]:
            palette = palettes[palette]
        elif palette in list(palettes.keys()):
            palette = get_palette(palette)
        vis_params["palette"] = palette

    orientation = orientation.lower()
    if orientation not in ["horizontal", "vertical"]:
        raise ValueError("The orientation must be either horizontal or vertical.")

    if "opacity" in vis_params:
        alpha = vis_params["opacity"]
        if type(alpha) not in (int, float):
            raise ValueError("The provided opacity value must be type scalar.")
    else:
        alpha = 1

    if cmap is not None:
        cmap = mpl.pyplot.get_cmap(cmap)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    if "palette" in vis_params:
        hexcodes = to_hex_colors(vis_params["palette"])
        if discrete:
            cmap = mpl.colors.ListedColormap(hexcodes)
            vals = np.linspace(vmin, vmax, cmap.N + 1)
            norm = mpl.colors.BoundaryNorm(vals, cmap.N)

        else:
            cmap = mpl.colors.LinearSegmentedColormap.from_list(
                "custom", hexcodes, N=256
            )
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    elif cmap is not None:
        cmap = mpl.pyplot.get_cmap(cmap)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    else:
        raise ValueError(
            'cmap keyword or "palette" key in vis_params must be provided.'
        )

    fig, ax = plt.subplots(figsize=(width, height))
    cb = mpl.colorbar.ColorbarBase(
        ax, norm=norm, alpha=alpha, cmap=cmap, orientation=orientation, **kwargs
    )
    if label is not None:
        cb.set_label(label=label, size=label_size, weight=label_weight)
    cb.ax.tick_params(labelsize=tick_size)

    if transparent:
        bg_color = None

    if bg_color is not None:
        kwargs["facecolor"] = bg_color
    if "bbox_inches" not in kwargs:
        kwargs["bbox_inches"] = "tight"

    fig.savefig(out_fig, dpi=dpi, transparent=transparent, **kwargs)
    if not show_colorbar:
        plt.close(fig)
    return out_fig


def is_arcpy():
    """Check if arcpy is available.

    Returns:
        book: True if arcpy is available, False otherwise.
    """
    import sys

    if "arcpy" in sys.modules:
        return True
    else:
        return False


def arc_active_map():
    """Get the active map in ArcGIS Pro.

    Returns:
        arcpy.Map: The active map in ArcGIS Pro.
    """
    if is_arcpy():
        import arcpy

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.activeMap
        return m
    else:
        return None


def arc_active_view():
    """Get the active view in ArcGIS Pro.

    Returns:
        arcpy.MapView: The active view in ArcGIS Pro.
    """
    if is_arcpy():
        import arcpy

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        view = aprx.activeView
        return view
    else:
        return None


def arc_add_layer(url, name=None, shown=True, opacity=1.0):
    """Add a layer to the active map in ArcGIS Pro.

    Args:
        url (str): The URL of the tile layer to add.
        name (str, optional): The name of the layer. Defaults to None.
        shown (bool, optional): Whether the layer is shown. Defaults to True.
        opacity (float, optional): The opacity of the layer. Defaults to 1.0.
    """
    if is_arcpy():
        m = arc_active_map()
        if m is not None:
            m.addDataFromPath(url)
            if isinstance(name, str):
                layers = m.listLayers("Tiled service layer")
                if len(layers) > 0:
                    layer = layers[0]
                    layer.name = name
                    layer.visible = shown
                    layer.transparency = 100 - (opacity * 100)


def arc_zoom_to_extent(xmin, ymin, xmax, ymax):
    """Zoom to an extent in ArcGIS Pro.

    Args:
        xmin (float): The minimum x value of the extent.
        ymin (float): The minimum y value of the extent.
        xmax (float): The maximum x value of the extent.
        ymax (float): The maximum y value of the extent.
    """
    if is_arcpy():
        import arcpy

        view = arc_active_view()
        if view is not None:
            view.camera.setExtent(
                arcpy.Extent(
                    xmin,
                    ymin,
                    xmax,
                    ymax,
                    spatial_reference=arcpy.SpatialReference(4326),
                )
            )

        # if isinstance(zoom, int):
        #     scale = 156543.04 * math.cos(0) / math.pow(2, zoom)
        #     view.camera.scale = scale  # Not working properly


def arc_zoom_to_bounds(bounds):
    """Zoom to a bounding box.

    Args:
        bounds (list): The bounding box to zoom to in the form [xmin, ymin, xmax, ymax] or [(ymin, xmin), (ymax, xmax)].

    Raises:
        ValueError: _description_
    """

    if len(bounds) == 4:
        xmin, ymin, xmax, ymax = bounds
    elif len(bounds) == 2:
        (ymin, xmin), (ymax, xmax) = bounds
    else:
        raise ValueError("bounds must be a tuple of length 2 or 4.")

    arc_zoom_to_extent(xmin, ymin, xmax, ymax)


def vector_to_raster(
    vector,
    output,
    field="FID",
    assign="last",
    nodata=True,
    cell_size=None,
    base=None,
    callback=None,
    verbose=False,
    to_epsg=None,
):
    """Convert a vector to a raster.

    Args:
        vector (str | GeoPandas.GeoDataFrame): The input vector data, can be a file path or a GeoDataFrame.
        output (str): The output raster file path.
        field (str, optional): Input field name in attribute table. Defaults to 'FID'.
        assign (str, optional): Assignment operation, where multiple points are in the same grid cell; options
            include 'first', 'last' (default), 'min', 'max', 'sum', 'number'. Defaults to 'last'.
        nodata (bool, optional): Background value to set to NoData. Without this flag, it will be set to 0.0.
        cell_size (float, optional): Optionally specified cell size of output raster. Not used when base raster is specified
        base (str, optional): Optionally specified input base raster file. Not used when a cell size is specified. Defaults to None.
        callback (fuct, optional): A callback function to report progress. Defaults to None.
        verbose (bool, optional): Whether to print progress to the console. Defaults to False.
        to_epsg (integer, optional): Optionally specified the EPSG code to reproject the raster to. Defaults to None.

    """
    import geopandas as gpd
    import whitebox

    output = os.path.abspath(output)

    if isinstance(vector, str):
        gdf = gpd.read_file(vector)
    elif isinstance(vector, gpd.GeoDataFrame):
        gdf = vector
    else:
        raise TypeError("vector must be a file path or a GeoDataFrame")

    if to_epsg is None:
        to_epsg = 3857

    if to_epsg == 4326:
        raise ValueError("to_epsg cannot be 4326")

    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=to_epsg)
        vector = temp_file_path(extension=".shp")
        gdf.to_file(vector)
    else:
        to_epsg = gdf.crs.to_epsg()

    wbt = whitebox.WhiteboxTools()
    wbt.verbose = verbose

    goem_type = gdf.geom_type[0]

    if goem_type == "LineString":
        wbt.vector_lines_to_raster(
            vector, output, field, nodata, cell_size, base, callback
        )
    elif goem_type == "Polygon":
        wbt.vector_polygons_to_raster(
            vector, output, field, nodata, cell_size, base, callback
        )
    else:
        wbt.vector_points_to_raster(
            vector, output, field, assign, nodata, cell_size, base, callback
        )

    image_set_crs(output, to_epsg)


def show_youtube_video(url, width=800, height=450, allow_autoplay=False, **kwargs):
    """
    Displays a Youtube video in a Jupyter notebook.

    Args:
        url (string): a link to a Youtube video.
        width (int, optional): the width of the video. Defaults to 800.
        height (int, optional): the height of the video. Defaults to 600.
        allow_autoplay (bool, optional): whether to allow autoplay. Defaults to False.
        **kwargs: further arguments for IPython.display.YouTubeVideo

    Returns:
        YouTubeVideo: a video that is displayed in your notebook.
    """
    import re
    from IPython.display import YouTubeVideo

    if not isinstance(url, str):
        raise TypeError("URL must be a string")

    match = re.match(
        r"^https?:\/\/(?:www\.)?youtube\.com\/watch\?(?=.*v=([^\s&]+)).*$|^https?:\/\/(?:www\.)?youtu\.be\/([^\s&]+).*$",
        url,
    )
    if not match:
        raise ValueError("Invalid YouTube video URL")

    video_id = match.group(1) if match.group(1) else match.group(2)

    return YouTubeVideo(
        video_id, width=width, height=height, allow_autoplay=allow_autoplay, **kwargs
    )


def html_to_gradio(html, width="100%", height="500px", **kwargs):
    """Converts the map to an HTML string that can be used in Gradio. Removes unsupported elements, such as
        attribution and any code blocks containing functions. See https://github.com/gradio-app/gradio/issues/3190

    Args:
        width (str, optional): The width of the map. Defaults to '100%'.
        height (str, optional): The height of the map. Defaults to '500px'.

    Returns:
        str: The HTML string to use in Gradio.
    """

    if isinstance(width, int):
        width = f"{width}px"

    if isinstance(height, int):
        height = f"{height}px"

    if isinstance(html, str):
        with open(html, "r") as f:
            lines = f.readlines()
    elif isinstance(html, list):
        lines = html
    else:
        raise TypeError("html must be a file path or a list of strings")

    output = []
    skipped_lines = []
    for index, line in enumerate(lines):
        if index in skipped_lines:
            continue
        if line.lstrip().startswith('{"attribution":'):
            continue
        elif "on(L.Draw.Event.CREATED, function(e)" in line:
            for i in range(14):
                skipped_lines.append(index + i)
        elif "L.Control.geocoder" in line:
            for i in range(5):
                skipped_lines.append(index + i)
        elif "function(e)" in line:
            print(
                f"Warning: The folium plotting backend does not support functions in code blocks. Please delete line {index + 1}."
            )
        else:
            output.append(line + "\n")

    return f"""<iframe style="width: {width}; height: {height}" name="result" allow="midi; geolocation; microphone; camera; 
    display-capture; encrypted-media;" sandbox="allow-modals allow-forms 
    allow-scripts allow-same-origin allow-popups 
    allow-top-navigation-by-user-activation allow-downloads" allowfullscreen="" 
    allowpaymentrequest="" frameborder="0" srcdoc='{"".join(output)}'></iframe>"""


def filter_bounds(data, bbox, within=False, align=True, **kwargs):
    """Filters a GeoDataFrame or GeoSeries by a bounding box.

    Args:
        data (str | GeoDataFrame): The input data to filter. Can be a file path or a GeoDataFrame.
        bbox (list | GeoDataFrame): The bounding box to filter by. Can be a list of 4 coordinates or a file path or a GeoDataFrame.
        within (bool, optional): Whether to filter by the bounding box or the bounding box's interior. Defaults to False.
        align (bool, optional): If True, automatically aligns GeoSeries based on their indices. If False, the order of elements is preserved.

    Returns:
        GeoDataFrame: The filtered data.
    """
    import geopandas as gpd

    if isinstance(data, str):
        data = gpd.read_file(data, **kwargs)
    elif not isinstance(data, (gpd.GeoDataFrame, gpd.GeoSeries)):
        raise TypeError("data must be a file path or a GeoDataFrame or GeoSeries")

    if isinstance(bbox, list):
        if len(bbox) != 4:
            raise ValueError("bbox must be a list of 4 coordinates")
        bbox = bbox_to_gdf(bbox)
    elif isinstance(bbox, str):
        bbox = gpd.read_file(bbox, **kwargs)

    if within:
        result = data[data.within(bbox.unary_union, align=align)]
    else:
        result = data[data.intersects(bbox.unary_union, align=align)]

    return result


def filter_date(
    data, start_date=None, end_date=None, date_field="date", date_args={}, **kwargs
):
    """Filters a DataFrame, GeoDataFrame or GeoSeries by a date range.

    Args:
        data (str | DataFrame | GeoDataFrame): The input data to filter. Can be a file path or a DataFrame or GeoDataFrame.
        start_date (str, optional): The start date, e.g., 2023-01-01. Defaults to None.
        end_date (str, optional): The end date, e.g., 2023-12-31. Defaults to None.
        date_field (str, optional): The name of the date field. Defaults to "date".
        date_args (dict, optional): Additional arguments for pd.to_datetime. Defaults to {}.

    Returns:
        DataFrame: The filtered data.
    """

    import datetime
    import pandas as pd
    import geopandas as gpd

    if isinstance(data, str):
        data = gpd.read_file(data, **kwargs)
    elif not isinstance(
        data, (gpd.GeoDataFrame, gpd.GeoSeries, pd.DataFrame, pd.Series)
    ):
        raise TypeError("data must be a file path or a GeoDataFrame or GeoSeries")

    if date_field not in data.columns:
        raise ValueError(f"date_field must be one of {data.columns}")

    new_field = f"{date_field}_temp"
    data[new_field] = pd.to_datetime(data[date_field], **date_args)

    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    if start_date is None:
        start_date = data[new_field].min()

    mask = (data[new_field] >= start_date) & (data[new_field] <= end_date)
    result = data.loc[mask]
    return result.drop(columns=[new_field], axis=1)


def skip_mkdocs_build():
    """Skips the MkDocs build if the USE_MKDOCS environment variable is set.

    Returns:
        bool: Whether to skip the MkDocs build.
    """
    if os.environ.get("USE_MKDOCS") is not None:
        return True
    else:
        return False


def disjoint(input_features, selecting_features, output=None, **kwargs):
    """Find the features in the input_features that do not intersect the selecting_features.

    Args:
        input_features (str | GeoDataFrame): The input features to select from. Can be a file path or a GeoDataFrame.
        selecting_features (str | GeoDataFrame): The features in the Input Features parameter will be selected based
            on their relationship to the features from this layer.
        output (are, optional): The output path to save the GeoDataFrame in a vector format (e.g., shapefile). Defaults to None.

    Returns:
        str | GeoDataFrame: The path to the output file or the GeoDataFrame.
    """
    import geopandas as gpd

    if isinstance(input_features, str):
        input_features = gpd.read_file(input_features, **kwargs)
    elif not isinstance(input_features, gpd.GeoDataFrame):
        raise TypeError("input_features must be a file path or a GeoDataFrame")

    if isinstance(selecting_features, str):
        selecting_features = gpd.read_file(selecting_features, **kwargs)
    elif not isinstance(selecting_features, gpd.GeoDataFrame):
        raise TypeError("selecting_features must be a file path or a GeoDataFrame")

    selecting_features = selecting_features.to_crs(input_features.crs)

    input_features["savedindex"] = input_features.index
    intersecting = selecting_features.sjoin(input_features, how="inner")["savedindex"]
    results = input_features[~input_features.savedindex.isin(intersecting)].drop(
        columns=["savedindex"], axis=1
    )

    if output is not None:
        results.to_file(output, **kwargs)
    else:
        return results


def zonal_stats(
    vectors,
    raster,
    layer=0,
    band_num=1,
    nodata=None,
    affine=None,
    stats=None,
    all_touched=False,
    categorical=False,
    category_map=None,
    add_stats=None,
    raster_out=False,
    prefix=None,
    geojson_out=False,
    gdf_out=False,
    dst_crs=None,
    open_vector_args={},
    open_raster_args={},
    **kwargs,
):
    """This function wraps rasterstats.zonal_stats and performs reprojection if necessary.
        See https://pythonhosted.org/rasterstats/rasterstats.html.

    Args:
        vectors (str | list | GeoDataFrame): path to an vector source or geo-like python objects.
        raster (str | ndarray): ndarray or path to a GDAL raster source.
        layer (int, optional): If vectors is a path to an fiona source, specify the vector layer to
            use either by name or number. Defaults to 0
        band_num (int | str, optional): If raster is a GDAL source, the band number to use (counting from 1). defaults to 1.
        nodata (float, optional): If raster is a GDAL source, this value overrides any NODATA value
            specified in the file’s metadata. If None, the file’s metadata’s NODATA value (if any)
            will be used. defaults to None.
        affine (Affine, optional): required only for ndarrays, otherwise it is read from src. Defaults to None.
        stats (str | list, optional): Which statistics to calculate for each zone.
            It can be ['min', 'max', 'mean', 'count']. For more, see https://pythonhosted.org/rasterstats/manual.html#zonal-statistics
            Defaults to None.
        all_touched (bool, optional): Whether to include every raster cell touched by a geometry, or only those having
            a center point within the polygon. defaults to False
        categorical (bool, optional): If True, the raster values will be treated as categorical.
        category_map (dict, optional):A dictionary mapping raster values to human-readable categorical names.
            Only applies when categorical is True
        add_stats (dict, optional): with names and functions of additional stats to compute. Defaults to None.
        raster_out (bool, optional): Include the masked numpy array for each feature?. Defaults to False.
        prefix (str, optional): add a prefix to the keys. Defaults to None.
        geojson_out (bool, optional): Return list of GeoJSON-like features (default: False)
            Original feature geometry and properties will be retained with zonal stats
            appended as additional properties. Use with prefix to ensure unique and
            meaningful property names.. Defaults to False.
        gdf_out (bool, optional): Return a GeoDataFrame. Defaults to False.
        dst_crs (str, optional): The destination CRS. Defaults to None.
        open_vector_args (dict, optional): Pass additional arguments to geopandas.open_file(). Defaults to {}.
        open_raster_args (dict, optional): Pass additional arguments to rasterio.open(). Defaults to {}.

    Returns:
        dict | list | GeoDataFrame: The zonal statistics results
    """

    import geopandas as gpd
    import rasterio

    try:
        import rasterstats
    except ImportError:
        raise ImportError(
            "rasterstats is not installed. Install it with pip install rasterstats"
        )
    try:
        if isinstance(raster, str):
            with rasterio.open(raster, **open_raster_args) as src:
                affine = src.transform
                nodata = src.nodata
                array = src.read(band_num, masked=True)
                raster_crs = src.crs
        elif isinstance(raster, rasterio.io.DatasetReader):
            affine = raster.transform
            nodata = raster.nodata
            array = raster.read(band_num, masked=True)
            raster_crs = raster.crs
        else:
            array = raster

        if isinstance(vectors, str):
            gdf = gpd.read_file(vectors, **open_vector_args)
        elif isinstance(vectors, list):
            gdf = gpd.GeoDataFrame.from_features(vectors)
        else:
            gdf = vectors

        vector_crs = gdf.crs

        if gdf.crs.is_geographic:
            if not raster_crs.is_geographic:
                gdf = gdf.to_crs(raster_crs)
        elif gdf.crs != raster_crs:
            if not raster_crs.is_geographic:
                gdf = gdf.to_crs(raster_crs)
            else:
                raise ValueError("The vector and raster CRSs are not compatible")

        if gdf_out is True:
            geojson_out = True

        result = rasterstats.zonal_stats(
            gdf,
            array,
            layer=layer,
            band_num=band_num,
            nodata=nodata,
            affine=affine,
            stats=stats,
            all_touched=all_touched,
            categorical=categorical,
            category_map=category_map,
            add_stats=add_stats,
            raster_out=raster_out,
            prefix=prefix,
            geojson_out=geojson_out,
            **kwargs,
        )

        if gdf_out is True:
            if dst_crs is None:
                dst_crs = vector_crs

            out_gdf = gpd.GeoDataFrame.from_features(result)
            out_gdf.crs = raster_crs
            return out_gdf.to_crs(dst_crs)
        else:
            return result

    except Exception as e:
        raise Exception(e)


def s3_list_objects(
    bucket,
    prefix=None,
    limit=None,
    ext=None,
    fullpath=True,
    request_payer="bucket-owner",
    **kwargs,
):
    """List objects in a S3 bucket

    Args:
        bucket (str): The name of the bucket.
        prefix (str, optional): Limits the response to keys that begin with the specified prefix. Defaults to None.
        limit (init, optional): The maximum number of keys returned in the response body.
        ext (str, optional): Filter by file extension. Defaults to None.
        fullpath (bool, optional): Return full path. Defaults to True.
        request_payer (str, optional): Specifies who pays for the download from S3.
            Can be "bucket-owner" or "requester". Defaults to "bucket-owner".

    Returns:
        list: List of objects.
    """
    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 is not installed. Install it with pip install boto3")

    client = boto3.client("s3")

    if prefix is not None:
        kwargs["Prefix"] = prefix

    files = []
    kwargs["RequestPayer"] = request_payer
    if isinstance(limit, int) and limit < 1000:
        kwargs["MaxKeys"] = limit
        response = client.list_objects_v2(Bucket=bucket, **kwargs)
        for obj in response["Contents"]:
            files.append(obj)
    else:
        paginator = client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, **kwargs)

        for page in pages:
            files.extend(page.get("Contents", []))

    if ext is not None:
        files = [f for f in files if f["Key"].endswith(ext)]

    if fullpath:
        return [f"s3://{bucket}/{r['Key']}" for r in files]
    else:
        return [r["Key"] for r in files]


def s3_download_file(filename=None, bucket=None, key=None, outfile=None, **kwargs):
    """Download a file from S3.

    Args:
        filename (str, optional): The full path to the file. Defaults to None.
        bucket (str, optional): The name of the bucket. Defaults to None.
        key (str, optional): The key of the file. Defaults to None.
        outfile (str, optional): The name of the output file. Defaults to None.
    Raises:
        ImportError: If boto3 is not installed.
    """

    if os.environ.get("USE_MKDOCS") is not None:
        return

    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 is not installed. Install it with pip install boto3")

    client = boto3.client("s3", **kwargs)

    if filename is not None:
        bucket = filename.split("/")[2]
        key = "/".join(filename.split("/")[3:])

    if outfile is None:
        outfile = key.split("/")[-1]

    if not os.path.exists(outfile):
        client.download_file(bucket, key, outfile)
    else:
        print(f"File already exists: {outfile}")


def s3_download_files(
    filenames=None, bucket=None, keys=None, outdir=None, quiet=False, **kwargs
):
    """Download multiple files from S3.

    Args:
        filenames (list, optional): A list of filenames. Defaults to None.
        bucket (str, optional): The name of the bucket. Defaults to None.
        keys (list, optional): A list of keys. Defaults to None.
        outdir (str, optional): The name of the output directory. Defaults to None.
        quiet (bool, optional): Suppress output. Defaults to False.

    Raises:
        ValueError: If neither filenames or keys are provided.
    """

    if keys is None:
        keys = []

    if filenames is not None:
        if isinstance(filenames, list):
            for filename in filenames:
                bucket = filename.split("/")[2]
                key = "/".join(filename.split("/")[3:])
                keys.append(key)
    elif filenames is None and keys is None:
        raise ValueError("Either filenames or keys must be provided")

    for index, key in enumerate(keys):
        if outdir is not None:
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            outfile = os.path.join(outdir, key.split("/")[-1])
        else:
            outfile = key.split("/")[-1]

        if not quiet:
            print(f"Downloading {index+1} of {len(keys)}: {outfile}")
        s3_download_file(bucket=bucket, key=key, outfile=outfile, **kwargs)


def s3_get_object(
    bucket,
    key,
    output=None,
    chunk_size=1024 * 1024,
    request_payer="bucket-owner",
    quiet=False,
    client_args={},
    **kwargs,
):
    """Download a file from S3.

    Args:
        bucket (str): The name of the bucket.
        key (key): The key of the file.
        output (str, optional): The name of the output file. Defaults to None.
        chunk_size (int, optional): The chunk size in bytes. Defaults to 1024 * 1024.
        request_payer (str, optional): Specifies who pays for the download from S3.
        quiet (bool, optional): Suppress output. Defaults to False.
            Can be "bucket-owner" or "requester". Defaults to "bucket-owner".
        client_args (dict, optional): Additional arguments to pass to boto3.client(). Defaults to {}.
        **kwargs: Additional arguments to pass to boto3.client().get_object().
    """

    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 is not installed. Install it with pip install boto3")

    # Set up the S3 client
    s3 = boto3.client("s3", **client_args)

    if output is None:
        output = key.split("/")[-1]

    out_dir = os.path.dirname(os.path.abspath(output))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Set up the progress bar
    def progress_callback(bytes_amount):
        # This function will be called by the StreamingBody object
        # to report the number of bytes downloaded so far
        total_size = int(response["ContentLength"])
        progress_percent = int(bytes_amount / total_size * 100)
        if not quiet:
            print(f"\rDownloading: {progress_percent}% complete.", end="")

    # Download the file
    response = s3.get_object(
        Bucket=bucket, Key=key, RequestPayer=request_payer, **kwargs
    )

    # Save the file to disk
    with open(output, "wb") as f:
        # Use the StreamingBody object to read the file in chunks
        # and track the download progress
        body = response["Body"]
        downloaded_bytes = 0
        for chunk in body.iter_chunks(chunk_size=chunk_size):
            f.write(chunk)
            downloaded_bytes += len(chunk)
            progress_callback(downloaded_bytes)


def s3_get_objects(
    bucket,
    keys=None,
    out_dir=None,
    prefix=None,
    limit=None,
    ext=None,
    chunk_size=1024 * 1024,
    request_payer="bucket-owner",
    quiet=True,
    client_args={},
    **kwargs,
):
    """Download multiple files from S3.

    Args:
        bucket (str): The name of the bucket.
        keys (list, optional): A list of keys. Defaults to None.
        out_dir (str, optional): The name of the output directory. Defaults to None.
        prefix (str, optional): Limits the response to keys that begin with the specified prefix. Defaults to None.
        limit (int, optional): The maximum number of keys returned in the response body.
        ext (str, optional): Filter by file extension. Defaults to None.
        chunk_size (int, optional): The chunk size in bytes. Defaults to 1024 * 1024.
        request_payer (str, optional): Specifies who pays for the download from S3.
            Can be "bucket-owner" or "requester". Defaults to "bucket-owner".
        quiet (bool, optional): Suppress output. Defaults to True.
        client_args (dict, optional): Additional arguments to pass to boto3.client(). Defaults to {}.
        **kwargs: Additional arguments to pass to boto3.client().get_object().

    """

    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 is not installed. Install it with pip install boto3")

    if out_dir is None:
        out_dir = os.getcwd()

    if keys is None:
        fullpath = False
        keys = s3_list_objects(
            bucket, prefix, limit, ext, fullpath, request_payer, **kwargs
        )

    for index, key in enumerate(keys):
        print(f"Downloading {index+1} of {len(keys)}: {key}")
        output = os.path.join(out_dir, key.split("/")[-1])
        s3_get_object(
            bucket, key, output, chunk_size, request_payer, quiet, client_args, **kwargs
        )


def read_raster(
    source,
    window=None,
    return_array=True,
    coord_crs=None,
    request_payer="bucket-owner",
    env_args={},
    open_args={},
    **kwargs,
):
    """Read a raster from S3.

    Args:
        source (str): The path to the raster on S3.
        window (tuple, optional): The window (col_off, row_off, width, height) to read. Defaults to None.
        return_array (bool, optional): Whether to return a numpy array. Defaults to True.
        coord_crs (str, optional): The coordinate CRS of the input coordinates. Defaults to None.
        request_payer (str, optional): Specifies who pays for the download from S3.
            Can be "bucket-owner" or "requester". Defaults to "bucket-owner".
        env_args (dict, optional): Additional arguments to pass to rasterio.Env(). Defaults to {}.
        open_args (dict, optional): Additional arguments to pass to rasterio.open(). Defaults to {}.

    Returns:
        np.ndarray: The raster as a numpy array.
    """
    import rasterio
    from rasterio.windows import Window

    with rasterio.Env(AWS_REQUEST_PAYER=request_payer, **env_args):
        src = rasterio.open(source, **open_args)
        if not return_array:
            return src
        else:
            if window is None:
                window = Window(0, 0, src.width, src.height)
            else:
                if isinstance(window, list):
                    coords = coords_to_xy(
                        source,
                        window,
                        coord_crs,
                        env_args=env_args,
                        open_args=open_args,
                    )
                    window = xy_to_window(coords)
                window = Window(*window)

            array = src.read(window=window, **kwargs)
            return array


def read_rasters(
    sources,
    window=None,
    coord_crs=None,
    request_payer="bucket-owner",
    env_args={},
    open_args={},
    **kwargs,
):
    """Read a raster from S3.

    Args:
        sources (str): The list of paths to the raster files.
        window (tuple, optional): The window (col_off, row_off, width, height) to read. Defaults to None.
        coord_crs (str, optional): The coordinate CRS of the input coordinates. Defaults to None.
        request_payer (str, optional): Specifies who pays for the download from S3.
            Can be "bucket-owner" or "requester". Defaults to "bucket-owner".
        env_args (dict, optional): Additional arguments to pass to rasterio.Env(). Defaults to {}.
        open_args (dict, optional): Additional arguments to pass to rasterio.open(). Defaults to {}.

    Returns:
        np.ndarray: The raster as a numpy array.
    """
    import numpy as np

    if not isinstance(sources, list):
        sources = [sources]

    array_list = []

    for source in sources:
        array = read_raster(
            source,
            window,
            True,
            coord_crs,
            request_payer,
            env_args,
            open_args,
            **kwargs,
        )
        array_list.append(array)

    result = np.concatenate(array_list, axis=0)
    return result


def transform_coords(x, y, src_crs, dst_crs, **kwargs):
    """Transform coordinates from one CRS to another.

    Args:
        x (float): The x coordinate.
        y (float): The y coordinate.
        src_crs (str): The source CRS, e.g., "EPSG:4326".
        dst_crs (str): The destination CRS, e.g., "EPSG:3857".

    Returns:
        dict: The transformed coordinates in the format of (x, y)
    """
    import pyproj

    transformer = pyproj.Transformer.from_crs(
        src_crs, dst_crs, always_xy=True, **kwargs
    )
    return transformer.transform(x, y)


def transform_bbox_coords(bbox, src_crs, dst_crs, **kwargs):
    """Transforms the coordinates of a bounding box [x1, y1, x2, y2] from one CRS to another.

    Args:
        bbox (list | tuple): The bounding box [x1, y1, x2, y2] coordinates.
        src_crs (str): The source CRS, e.g., "EPSG:4326".
        dst_crs (str): The destination CRS, e.g., "EPSG:3857".

    Returns:
        list: The transformed bounding box [x1, y1, x2, y2] coordinates.
    """
    x1, y1, x2, y2 = bbox

    x1, y1 = transform_coords(x1, y1, src_crs, dst_crs, **kwargs)
    x2, y2 = transform_coords(x2, y2, src_crs, dst_crs, **kwargs)

    return [x1, y1, x2, y2]


def coords_to_xy(
    src_fp: str,
    coords: list,
    coord_crs: str = "epsg:4326",
    request_payer="bucket-owner",
    env_args={},
    open_args={},
    **kwargs,
) -> list:
    """Converts a list of coordinates to pixel coordinates, i.e., (col, row) coordinates.

    Args:
        src_fp: The source raster file path.
        coords: A list of coordinates in the format of [[x1, y1], [x2, y2], ...]
        coord_crs: The coordinate CRS of the input coordinates. Defaults to "epsg:4326".
        request_payer: Specifies who pays for the download from S3.
            Can be "bucket-owner" or "requester". Defaults to "bucket-owner".
        env_args: Additional keyword arguments to pass to rasterio.Env.
        open_args: Additional keyword arguments to pass to rasterio.open.
        **kwargs: Additional keyword arguments to pass to rasterio.transform.rowcol.

    Returns:
        A list of pixel coordinates in the format of [[x1, y1], [x2, y2], ...]
    """
    import numpy as np
    import rasterio

    if isinstance(coords, np.ndarray):
        coords = coords.tolist()

    if len(coords) == 4 and all([isinstance(c, (int, float)) for c in coords]):
        coords = [[coords[0], coords[1]], [coords[2], coords[3]]]

    xs, ys = zip(*coords)
    with rasterio.Env(AWS_REQUEST_PAYER=request_payer, **env_args):
        with rasterio.open(src_fp, **open_args) as src:
            width = src.width
            height = src.height
            if coord_crs != src.crs:
                xs, ys = transform_coords(xs, ys, coord_crs, src.crs, **kwargs)
            rows, cols = rasterio.transform.rowcol(src.transform, xs, ys, **kwargs)
        result = [[col, row] for col, row in zip(cols, rows)]

        result = [
            [x, y] for x, y in result if x >= 0 and y >= 0 and x < width and y < height
        ]
        if len(result) == 0:
            print("No valid pixel coordinates found.")
        elif len(result) < len(coords):
            print("Some coordinates are out of the image boundary.")

        return result


def xy_to_window(xy):
    """Converts a list of coordinates to a rasterio window.

    Args:
        xy (list): A list of coordinates in the format of [[x1, y1], [x2, y2]]

    Returns:
        tuple: The rasterio window in the format of (col_off, row_off, width, height)
    """

    x1, y1 = xy[0]
    x2, y2 = xy[1]

    left = min(x1, x2)
    right = max(x1, x2)
    top = min(y1, y2)
    bottom = max(y1, y2)

    width = right - left
    height = bottom - top

    return (left, top, width, height)


def tms_to_geotiff(
    output,
    bbox,
    zoom=None,
    resolution=None,
    source="OpenStreetMap",
    crs="EPSG:3857",
    to_cog=False,
    quiet=False,
    **kwargs,
):
    """Download TMS tiles and convert them to a GeoTIFF. The source is adapted from https://github.com/gumblex/tms2geotiff.
        Credits to the GitHub user @gumblex.

    Args:
        output (str): The output GeoTIFF file.
        bbox (list): The bounding box [minx, miny, maxx, maxy] coordinates in EPSG:4326, e.g., [-122.5216, 37.733, -122.3661, 37.8095]
        zoom (int, optional): The map zoom level. Defaults to None.
        resolution (float, optional): The resolution in meters. Defaults to None.
        source (str, optional): The tile source. It can be one of the following: "OPENSTREETMAP", "ROADMAP",
            "SATELLITE", "TERRAIN", "HYBRID", or an HTTP URL. Defaults to "OpenStreetMap".
        crs (str, optional): The coordinate reference system. Defaults to "EPSG:3857".
        to_cog (bool, optional): Convert to Cloud Optimized GeoTIFF. Defaults to False.
        quiet (bool, optional): Suppress output. Defaults to False.
        **kwargs: Additional arguments to pass to gdal.GetDriverByName("GTiff").Create().

    """

    import io
    import math
    import itertools
    import concurrent.futures

    import numpy
    from PIL import Image

    try:
        from osgeo import gdal, osr
    except ImportError:
        raise ImportError("GDAL is not installed. Install it with pip install GDAL")

    try:
        import httpx

        SESSION = httpx.Client()
    except ImportError:
        import requests

        SESSION = requests.Session()

    xyz_tiles = {
        "OPENSTREETMAP": {
            "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": "OpenStreetMap",
            "name": "OpenStreetMap",
        },
        "ROADMAP": {
            "url": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            "attribution": "Google",
            "name": "Google Maps",
        },
        "SATELLITE": {
            "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            "attribution": "Google",
            "name": "Google Satellite",
        },
        "TERRAIN": {
            "url": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
            "attribution": "Google",
            "name": "Google Terrain",
        },
        "HYBRID": {
            "url": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            "attribution": "Google",
            "name": "Google Satellite",
        },
    }

    if isinstance(source, str) and source.upper() in xyz_tiles:
        source = xyz_tiles[source.upper()]["url"]
    elif isinstance(source, str) and source.startswith("http"):
        pass
    else:
        raise ValueError(
            'source must be one of "OpenStreetMap", "ROADMAP", "SATELLITE", "TERRAIN", "HYBRID", or a URL'
        )

    def resolution_to_zoom_level(resolution):
        """
        Convert map resolution in meters to zoom level for Web Mercator (EPSG:3857) tiles.
        """
        # Web Mercator tile size in meters at zoom level 0
        initial_resolution = 156543.03392804097

        # Calculate the zoom level
        zoom_level = math.log2(initial_resolution / resolution)

        return int(zoom_level)

    if isinstance(bbox, list) and len(bbox) == 4:
        west, south, east, north = bbox
    else:
        raise ValueError(
            "bbox must be a list of 4 coordinates in the format of [xmin, ymin, xmax, ymax]"
        )

    if zoom is None and resolution is None:
        raise ValueError("Either zoom or resolution must be provided")
    elif zoom is not None and resolution is not None:
        raise ValueError("Only one of zoom or resolution can be provided")

    if resolution is not None:
        zoom = resolution_to_zoom_level(resolution)

    EARTH_EQUATORIAL_RADIUS = 6378137.0

    Image.MAX_IMAGE_PIXELS = None

    gdal.UseExceptions()
    web_mercator = osr.SpatialReference()
    web_mercator.ImportFromEPSG(3857)

    WKT_3857 = web_mercator.ExportToWkt()

    def from4326_to3857(lat, lon):
        xtile = math.radians(lon) * EARTH_EQUATORIAL_RADIUS
        ytile = (
            math.log(math.tan(math.radians(45 + lat / 2.0))) * EARTH_EQUATORIAL_RADIUS
        )
        return (xtile, ytile)

    def deg2num(lat, lon, zoom):
        lat_r = math.radians(lat)
        n = 2**zoom
        xtile = (lon + 180) / 360 * n
        ytile = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n
        return (xtile, ytile)

    def is_empty(im):
        extrema = im.getextrema()
        if len(extrema) >= 3:
            if len(extrema) > 3 and extrema[-1] == (0, 0):
                return True
            for ext in extrema[:3]:
                if ext != (0, 0):
                    return False
            return True
        else:
            return extrema[0] == (0, 0)

    def paste_tile(bigim, base_size, tile, corner_xy, bbox):
        if tile is None:
            return bigim
        im = Image.open(io.BytesIO(tile))
        mode = "RGB" if im.mode == "RGB" else "RGBA"
        size = im.size
        if bigim is None:
            base_size[0] = size[0]
            base_size[1] = size[1]
            newim = Image.new(
                mode, (size[0] * (bbox[2] - bbox[0]), size[1] * (bbox[3] - bbox[1]))
            )
        else:
            newim = bigim

        dx = abs(corner_xy[0] - bbox[0])
        dy = abs(corner_xy[1] - bbox[1])
        xy0 = (size[0] * dx, size[1] * dy)
        if mode == "RGB":
            newim.paste(im, xy0)
        else:
            if im.mode != mode:
                im = im.convert(mode)
            if not is_empty(im):
                newim.paste(im, xy0)
        im.close()
        return newim

    def finish_picture(bigim, base_size, bbox, x0, y0, x1, y1):
        xfrac = x0 - bbox[0]
        yfrac = y0 - bbox[1]
        x2 = round(base_size[0] * xfrac)
        y2 = round(base_size[1] * yfrac)
        imgw = round(base_size[0] * (x1 - x0))
        imgh = round(base_size[1] * (y1 - y0))
        retim = bigim.crop((x2, y2, x2 + imgw, y2 + imgh))
        if retim.mode == "RGBA" and retim.getextrema()[3] == (255, 255):
            retim = retim.convert("RGB")
        bigim.close()
        return retim

    def get_tile(url):
        retry = 3
        while 1:
            try:
                r = SESSION.get(url, timeout=60)
                break
            except Exception:
                retry -= 1
                if not retry:
                    raise
        if r.status_code == 404:
            return None
        elif not r.content:
            return None
        r.raise_for_status()
        return r.content

    def draw_tile(
        source, lat0, lon0, lat1, lon1, zoom, filename, quiet=False, **kwargs
    ):
        x0, y0 = deg2num(lat0, lon0, zoom)
        x1, y1 = deg2num(lat1, lon1, zoom)
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        corners = tuple(
            itertools.product(
                range(math.floor(x0), math.ceil(x1)),
                range(math.floor(y0), math.ceil(y1)),
            )
        )
        totalnum = len(corners)
        futures = []
        with concurrent.futures.ThreadPoolExecutor(5) as executor:
            for x, y in corners:
                futures.append(
                    executor.submit(get_tile, source.format(z=zoom, x=x, y=y))
                )
            bbox = (math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1))
            bigim = None
            base_size = [256, 256]
            for k, (fut, corner_xy) in enumerate(zip(futures, corners), 1):
                bigim = paste_tile(bigim, base_size, fut.result(), corner_xy, bbox)
                if not quiet:
                    print("Downloaded image %d/%d" % (k, totalnum))

        if not quiet:
            print("Saving GeoTIFF. Please wait...")
        img = finish_picture(bigim, base_size, bbox, x0, y0, x1, y1)
        imgbands = len(img.getbands())
        driver = gdal.GetDriverByName("GTiff")

        if "options" not in kwargs:
            kwargs["options"] = [
                "COMPRESS=DEFLATE",
                "PREDICTOR=2",
                "ZLEVEL=9",
                "TILED=YES",
            ]

        gtiff = driver.Create(
            filename,
            img.size[0],
            img.size[1],
            imgbands,
            gdal.GDT_Byte,
            **kwargs,
        )
        xp0, yp0 = from4326_to3857(lat0, lon0)
        xp1, yp1 = from4326_to3857(lat1, lon1)
        pwidth = abs(xp1 - xp0) / img.size[0]
        pheight = abs(yp1 - yp0) / img.size[1]
        gtiff.SetGeoTransform((min(xp0, xp1), pwidth, 0, max(yp0, yp1), 0, -pheight))
        gtiff.SetProjection(WKT_3857)
        for band in range(imgbands):
            array = numpy.array(img.getdata(band), dtype="u8")
            array = array.reshape((img.size[1], img.size[0]))
            band = gtiff.GetRasterBand(band + 1)
            band.WriteArray(array)
        gtiff.FlushCache()

        if not quiet:
            print(f"Image saved to {filename}")
        return img

    try:
        draw_tile(source, south, west, north, east, zoom, output, quiet, **kwargs)
        if crs.upper() != "EPSG:3857":
            reproject(output, output, crs, to_cog=to_cog)
        elif to_cog:
            image_to_cog(output, output)
    except Exception as e:
        raise Exception(e)


def tif_to_jp2(filename, output, creationOptions=None):
    """Converts a GeoTIFF to JPEG2000.

    Args:
        filename (str): The path to the GeoTIFF file.
        output (str): The path to the output JPEG2000 file.
        creationOptions (list): A list of creation options for the JPEG2000 file. See
            https://gdal.org/drivers/raster/jp2openjpeg.html. For example, to specify the compression
            ratio, use ``["QUALITY=20"]``. A value of 20 means the file will be 20% of the size in comparison
            to uncompressed data.

    """

    if not os.path.exists(filename):
        raise Exception(f"File {filename} does not exist")

    if not output.endswith(".jp2"):
        output += ".jp2"

    from osgeo import gdal

    in_ds = gdal.Open(filename)
    gdal.Translate(output, in_ds, format="JP2OpenJPEG", creationOptions=creationOptions)
    in_ds = None


def image_comparison(
    img1: str,
    img2: str,
    label1: str = "1",
    label2: str = "2",
    width: int = 704,
    show_labels: bool = True,
    starting_position: int = 50,
    make_responsive: bool = True,
    in_memory: bool = True,
    out_html: str = None,
):
    """Create a comparison slider for two images. The source code is adapted from
        https://github.com/fcakyon/streamlit-image-comparison. Credits to the GitHub user @fcakyon.
        Users can also use https://juxtapose.knightlab.com to create a comparison slider.

    Args:
        img1 (str): Path to the first image. It can be a local file path, a URL, or a numpy array.
        img2 (str): Path to the second image. It can be a local file path, a URL, or a numpy array.
        label1 (str, optional): Label for the first image. Defaults to "1".
        label2 (str, optional): Label for the second image. Defaults to "2".
        width (int, optional): Width of the component in pixels. Defaults to 704.
        show_labels (bool, optional): Whether to show labels on the images. Default is True.
        starting_position (int, optional): Starting position of the slider as a percentage (0-100). Default is 50.
        make_responsive (bool, optional): Whether to enable responsive mode. Default is True.
        in_memory (bool, optional): Whether to handle pillow to base64 conversion in memory without saving to local. Default is True.
        out_html (str, optional): Whether to handle pillow to base64 conversion in memory without saving to local. Default is True.

    """

    from PIL import Image
    import base64
    import io
    import os
    import uuid
    from typing import Union
    import requests
    import tempfile
    import numpy as np
    from IPython.display import HTML, display

    TEMP_DIR = os.path.join(tempfile.gettempdir(), random_string(6))
    os.makedirs(TEMP_DIR, exist_ok=True)

    def exif_transpose(image: Image.Image):
        """
        Transpose a PIL image accordingly if it has an EXIF Orientation tag.
        Inplace version of https://github.com/python-pillow/Pillow/blob/master/src/PIL/ImageOps.py exif_transpose()
        :param image: The image to transpose.
        :return: An image.
        """
        exif = image.getexif()
        orientation = exif.get(0x0112, 1)  # default 1
        if orientation > 1:
            method = {
                2: Image.FLIP_LEFT_RIGHT,
                3: Image.ROTATE_180,
                4: Image.FLIP_TOP_BOTTOM,
                5: Image.TRANSPOSE,
                6: Image.ROTATE_270,
                7: Image.TRANSVERSE,
                8: Image.ROTATE_90,
            }.get(orientation)
            if method is not None:
                image = image.transpose(method)
                del exif[0x0112]
                image.info["exif"] = exif.tobytes()
        return image

    def read_image_as_pil(
        image: Union[Image.Image, str, np.ndarray], exif_fix: bool = False
    ):
        """
        Loads an image as PIL.Image.Image.
        Args:
            image : Can be image path or url (str), numpy image (np.ndarray) or PIL.Image
        """
        # https://stackoverflow.com/questions/56174099/how-to-load-images-larger-than-max-image-pixels-with-pil
        Image.MAX_IMAGE_PIXELS = None

        if isinstance(image, Image.Image):
            image_pil = image.convert("RGB")
        elif isinstance(image, str):
            # read image if str image path is provided
            try:
                image_pil = Image.open(
                    requests.get(image, stream=True).raw
                    if str(image).startswith("http")
                    else image
                ).convert("RGB")
                if exif_fix:
                    image_pil = exif_transpose(image_pil)
            except:  # handle large/tiff image reading
                try:
                    import skimage.io
                except ImportError:
                    raise ImportError(
                        "Please run 'pip install -U scikit-image imagecodecs' for large image handling."
                    )
                image_sk = skimage.io.imread(image).astype(np.uint8)
                if len(image_sk.shape) == 2:  # b&w
                    image_pil = Image.fromarray(image_sk, mode="1").convert("RGB")
                elif image_sk.shape[2] == 4:  # rgba
                    image_pil = Image.fromarray(image_sk, mode="RGBA").convert("RGB")
                elif image_sk.shape[2] == 3:  # rgb
                    image_pil = Image.fromarray(image_sk, mode="RGB")
                else:
                    raise TypeError(
                        f"image with shape: {image_sk.shape[3]} is not supported."
                    )
        elif isinstance(image, np.ndarray):
            if image.shape[0] < 5:  # image in CHW
                image = image[:, :, ::-1]
            image_pil = Image.fromarray(image).convert("RGB")
        else:
            raise TypeError("read image with 'pillow' using 'Image.open()'")

        return image_pil

    def pillow_to_base64(image: Image.Image) -> str:
        """
        Convert a PIL image to a base64-encoded string.

        Parameters
        ----------
        image: PIL.Image.Image
            The image to be converted.

        Returns
        -------
        str
            The base64-encoded string.
        """
        in_mem_file = io.BytesIO()
        image.save(in_mem_file, format="JPEG", subsampling=0, quality=100)
        img_bytes = in_mem_file.getvalue()  # bytes
        image_str = base64.b64encode(img_bytes).decode("utf-8")
        base64_src = f"data:image/jpg;base64,{image_str}"
        return base64_src

    def local_file_to_base64(image_path: str) -> str:
        """
        Convert a local image file to a base64-encoded string.

        Parameters
        ----------
        image_path: str
            The path to the image file.

        Returns
        -------
        str
            The base64-encoded string.
        """
        file_ = open(image_path, "rb")
        img_bytes = file_.read()
        image_str = base64.b64encode(img_bytes).decode("utf-8")
        file_.close()
        base64_src = f"data:image/jpg;base64,{image_str}"
        return base64_src

    def pillow_local_file_to_base64(image: Image.Image, temp_dir: str):
        """
        Convert a Pillow image to a base64 string, using a temporary file on disk.

        Parameters
        ----------
        image : PIL.Image.Image
            The Pillow image to convert.
        temp_dir : str
            The directory to use for the temporary file.

        Returns
        -------
        str
            A base64-encoded string representing the image.
        """
        # Create temporary file path using os.path.join()
        img_path = os.path.join(temp_dir, str(uuid.uuid4()) + ".jpg")

        # Save image to temporary file
        image.save(img_path, subsampling=0, quality=100)

        # Convert temporary file to base64 string
        base64_src = local_file_to_base64(img_path)

        return base64_src

    # Prepare images
    img1_pillow = read_image_as_pil(img1)
    img2_pillow = read_image_as_pil(img2)

    img_width, img_height = img1_pillow.size
    h_to_w = img_height / img_width
    height = int((width * h_to_w) * 0.95)

    if in_memory:
        # Convert images to base64 strings
        img1 = pillow_to_base64(img1_pillow)
        img2 = pillow_to_base64(img2_pillow)
    else:
        # Create base64 strings from temporary files
        os.makedirs(TEMP_DIR, exist_ok=True)
        for file_ in os.listdir(TEMP_DIR):
            if file_.endswith(".jpg"):
                os.remove(os.path.join(TEMP_DIR, file_))
        img1 = pillow_local_file_to_base64(img1_pillow, TEMP_DIR)
        img2 = pillow_local_file_to_base64(img2_pillow, TEMP_DIR)

    # Load CSS and JS
    cdn_path = "https://cdn.knightlab.com/libs/juxtapose/latest"
    css_block = f'<link rel="stylesheet" href="{cdn_path}/css/juxtapose.css">'
    js_block = f'<script src="{cdn_path}/js/juxtapose.min.js"></script>'

    # write html block
    htmlcode = f"""
        <html>
        <head>
        <style>body {{ margin: unset; }}</style>
        {css_block}
        {js_block}
        <div id="foo" style="height: {height}; width: {width or '100%'};"></div>
        <script>
        slider = new juxtapose.JXSlider('#foo',
            [
                {{
                    src: '{img1}',
                    label: '{label1}',
                }},
                {{
                    src: '{img2}',
                    label: '{label2}',
                }}
            ],
            {{
                animate: true,
                showLabels: {'true' if show_labels else 'false'},
                showCredits: true,
                startingPosition: "{starting_position}%",
                makeResponsive: {'true' if make_responsive else 'false'},
            }});
        </script>
        </head>
        </html>
        """

    if out_html is not None:
        with open(out_html, "w") as f:
            f.write(htmlcode)

    shutil.rmtree(TEMP_DIR)

    display(HTML(htmlcode))


def display_html(filename, width="100%", height="600px", **kwargs):
    """Show an HTML file in a Jupyter notebook.

    Args:
        filename (str): The path to the HTML file.
        width (str, optional): The width of the HTML file. Defaults to "100%".
        height (str, optional): The height of the HTML file. Defaults to "600px".

    Returns:
        IFrame: An IFrame object.
    """

    from IPython.display import IFrame

    if not os.path.exists(filename):
        raise Exception(f"File {filename} does not exist")

    return IFrame(filename, width=width, height=height, **kwargs)


def get_nhd_basins(
    feature_ids,
    fsource="nwissite",
    split_catchment=False,
    simplified=True,
    **kwargs,
):
    """Get NHD basins for a list of station IDs.

    Args:
        feature_ids (str | list): Target feature ID(s).
        fsource (str, optional): The name of feature(s) source, defaults to ``nwissite``.
            The valid sources are:
            * 'comid' for NHDPlus comid.
            * 'ca_gages' for Streamgage catalog for CA SB19
            * 'gfv11_pois' for USGS Geospatial Fabric V1.1 Points of Interest
            * 'huc12pp' for HUC12 Pour Points
            * 'nmwdi-st' for New Mexico Water Data Initative Sites
            * 'nwisgw' for NWIS Groundwater Sites
            * 'nwissite' for NWIS Surface Water Sites
            * 'ref_gage' for geoconnex.us reference gauges
            * 'vigil' for Vigil Network Data
            * 'wade' for Water Data Exchange 2.0 Sites
            * 'WQP' for Water Quality Portal
        split_catchment (bool, optional): If True, split basins at their outlet locations
        simplified (bool, optional): If True, return a simplified version of basin geometries.
            Default to True.

    Raises:
        ImportError: If pynhd is not installed.

    Returns:
        geopandas.GeoDataFrame: NLDI indexed basins in EPSG:4326. If some IDs don't return any features
            a list of missing ID(s) are returned as well.
    """

    try:
        from pynhd import NLDI
    except ImportError:
        raise ImportError("pynhd is not installed. Install it with pip install pynhd")

    return NLDI().get_basins(
        feature_ids, fsource, split_catchment, simplified, **kwargs
    )


def get_3dep_dem(
    geometry,
    resolution=30,
    src_crs="EPSG:4326",
    output=None,
    dst_crs="EPSG:5070",
    to_cog=False,
    overwrite=False,
    **kwargs,
):
    """Get DEM data at any resolution from 3DEP.

    Args:
        geometry (Polygon | MultiPolygon | tuple): It can be a polygon or a bounding
            box of form (xmin, ymin, xmax, ymax).
        resolution (int): arget DEM source resolution in meters. Defaults to 30.
        src_crs (str, optional): The spatial reference system of the input geometry. Defaults to "EPSG:4326".
        output (str, optional): The output GeoTIFF file. Defaults to None.
        dst_crs (str, optional): The spatial reference system of the output GeoTIFF file. Defaults to "EPSG:5070".
        to_cog (bool, optional): Convert to Cloud Optimized GeoTIFF. Defaults to False.
        overwrite (bool, optional): Whether to overwrite the output file if it exists. Defaults to False.

    Returns:
        xarray.DataArray: DEM at the specified resolution in meters and CRS.
    """

    try:
        import py3dep
    except ImportError:
        raise ImportError("py3dep is not installed. Install it with pip install py3dep")

    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError(
            "geopandas is not installed. Install it with pip install geopandas"
        )

    if output is not None and os.path.exists(output) and not overwrite:
        print(f"File {output} already exists. Set overwrite=True to overwrite it")
        return

    if isinstance(geometry, gpd.GeoDataFrame):
        geometry = geometry.geometry.unary_union

    dem = py3dep.get_dem(geometry, resolution=resolution, crs=src_crs)
    dem = dem.rio.reproject(dst_crs)

    if output is not None:
        if not output.endswith(".tif"):
            output += ".tif"
        print(output)
        dem.rio.to_raster(output, **kwargs)

        if to_cog:
            image_to_cog(output, output)

    else:
        return dem


def vector_set_crs(source, output=None, crs="EPSG:4326", **kwargs):
    """Set CRS of a vector file.

    Args:
        source (str | gpd.GeoDataFrame): The path to the vector file or a GeoDataFrame.
        output (str, optional): The path to the output vector file. Defaults to None.
        crs (str, optional): The CRS to set. Defaults to "EPSG:4326".


    Returns:
        gpd.GeoDataFrame: The GeoDataFrame with the new CRS.
    """

    import geopandas as gpd

    if isinstance(source, str):
        source = gpd.read_file(source, **kwargs)

    if not isinstance(source, gpd.GeoDataFrame):
        raise TypeError("source must be a GeoDataFrame or a file path")

    gdf = source.set_crs(crs)

    if output is not None:
        gdf.to_file(output)
    else:
        return gdf


def select_largest(source, column, count=1, output=None, **kwargs):
    """Select the largest features in a GeoDataFrame based on a column.

    Args:
        source (str | gpd.GeoDataFrame): The path to the vector file or a GeoDataFrame.
        column (str): The column to sort by.
        count (int, optional): The number of features to select. Defaults to 1.
        output (str, optional): The path to the output vector file. Defaults to None.

    Returns:
        str: The path to the output vector file.
    """

    import geopandas as gpd

    if isinstance(source, str):
        gdf = gpd.read_file(source, **kwargs)
    else:
        gdf = source

    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("source must be a GeoDataFrame or a file path")

    gdf = gdf.sort_values(column, ascending=False).head(count)

    if output is not None:
        gdf.to_file(output)

    else:
        return gdf


def coords_to_vector(coords, output=None, crs="EPSG:4326", **kwargs):
    """Convert a list of coordinates to a GeoDataFrame or a vector file.

    Args:
        coords (list): A list of coordinates in the format of [(x1, y1), (x2, y2), ...].
        output (str, optional): The path to the output vector file. Defaults to None.
        crs (str, optional): The CRS of the coordinates. Defaults to "EPSG:4326".

    Returns:
        gpd.GeoDataFraem: A GeoDataFrame of the coordinates.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    if not isinstance(coords, list):
        raise TypeError("coords must be a list of coordinates")

    if isinstance(coords[0], int) or isinstance(coords[0], float):
        coords = [(coords[0], coords[1])]

    # convert the points to a GeoDataFrame
    geometry = [Point(xy) for xy in coords]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")
    gdf.to_crs(crs, inplace=True)

    if output is not None:
        gdf.to_file(output, **kwargs)
    else:
        return gdf


def check_html_string(html_string):
    """Check if an HTML string contains local images and convert them to base64.

    Args:
        html_string (str): The HTML string.

    Returns:
        str: The HTML string with local images converted to base64.
    """
    import re
    import base64

    # Search for img tags with src attribute
    img_regex = r'<img[^>]+src\s*=\s*["\']([^"\':]+)["\'][^>]*>'

    for match in re.findall(img_regex, html_string):
        with open(match, "rb") as img_file:
            img_data = img_file.read()
            base64_data = base64.b64encode(img_data).decode("utf-8")
            html_string = html_string.replace(
                'src="{}"'.format(match),
                'src="data:image/png;base64,' + base64_data + '"',
            )

    return html_string


def split_raster(filename, out_dir, tile_size=256, overlap=0):
    """Split a raster into tiles.

    Args:
        filename (str): The path or http URL to the raster file.
        out_dir (str): The path to the output directory.
        tile_size (int | tuple, optional): The size of the tiles. Can be an integer or a tuple of (width, height). Defaults to 256.
        overlap (int, optional): The number of pixels to overlap between tiles. Defaults to 0.

    Raises:
        ImportError: Raised if GDAL is not installed.
    """

    try:
        from osgeo import gdal
    except ImportError:
        raise ImportError(
            "GDAL is required to use this function. Install it with `conda install gdal -c conda-forge`"
        )

    if isinstance(filename, str):
        if filename.startswith("http"):
            output = filename.split("/")[-1]
            download_file(filename, output)
            filename = output

    # Open the input GeoTIFF file
    ds = gdal.Open(filename)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if isinstance(tile_size, int):
        tile_width = tile_size
        tile_height = tile_size
    elif isinstance(tile_size, tuple):
        tile_width = tile_size[0]
        tile_height = tile_size[1]

    # Get the size of the input raster
    width = ds.RasterXSize
    height = ds.RasterYSize

    # Calculate the number of tiles needed in both directions, taking into account the overlap
    num_tiles_x = (width - overlap) // (tile_width - overlap) + int(
        (width - overlap) % (tile_width - overlap) > 0
    )
    num_tiles_y = (height - overlap) // (tile_height - overlap) + int(
        (height - overlap) % (tile_height - overlap) > 0
    )

    # Get the georeferencing information of the input raster
    geotransform = ds.GetGeoTransform()

    # Loop over all the tiles
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            # Calculate the pixel coordinates of the tile, taking into account the overlap and clamping to the edge of the raster
            x_min = i * (tile_width - overlap)
            y_min = j * (tile_height - overlap)
            x_max = min(x_min + tile_width, width)
            y_max = min(y_min + tile_height, height)

            # Adjust the size of the last tile in each row and column to include any remaining pixels
            if i == num_tiles_x - 1:
                x_min = max(x_max - tile_width, 0)
            if j == num_tiles_y - 1:
                y_min = max(y_max - tile_height, 0)

            # Calculate the size of the tile, taking into account the overlap
            tile_width = x_max - x_min
            tile_height = y_max - y_min

            # Set the output file name
            output_file = f"{out_dir}/tile_{i}_{j}.tif"

            # Create a new dataset for the tile
            driver = gdal.GetDriverByName("GTiff")
            tile_ds = driver.Create(
                output_file,
                tile_width,
                tile_height,
                ds.RasterCount,
                ds.GetRasterBand(1).DataType,
            )

            # Calculate the georeferencing information for the output tile
            tile_geotransform = (
                geotransform[0] + x_min * geotransform[1],
                geotransform[1],
                0,
                geotransform[3] + y_min * geotransform[5],
                0,
                geotransform[5],
            )

            # Set the geotransform and projection of the tile
            tile_ds.SetGeoTransform(tile_geotransform)
            tile_ds.SetProjection(ds.GetProjection())

            # Read the data from the input raster band(s) and write it to the tile band(s)
            for k in range(ds.RasterCount):
                band = ds.GetRasterBand(k + 1)
                tile_band = tile_ds.GetRasterBand(k + 1)
                tile_data = band.ReadAsArray(x_min, y_min, tile_width, tile_height)
                tile_band.WriteArray(tile_data)

            # Close the tile dataset
            tile_ds = None

    # Close the input dataset
    ds = None


def merge_rasters(
    input_dir,
    output,
    input_pattern="*.tif",
    output_format="GTiff",
    output_nodata=None,
    output_options=["COMPRESS=DEFLATE"],
):
    """Merge a directory of rasters into a single raster.

    Args:
        input_dir (str): The path to the input directory.
        output (str): The path to the output raster.
        input_pattern (str, optional): The pattern to match the input files. Defaults to "*.tif".
        output_format (str, optional): The output format. Defaults to "GTiff".
        output_nodata (float, optional): The output nodata value. Defaults to None.
        output_options (list, optional): A list of output options. Defaults to ["COMPRESS=DEFLATE"].

    Raises:
        ImportError: Raised if GDAL is not installed.
    """

    import glob

    try:
        from osgeo import gdal
    except ImportError:
        raise ImportError(
            "GDAL is required to use this function. Install it with `conda install gdal -c conda-forge`"
        )
    # Get a list of all the input files
    input_files = glob.glob(os.path.join(input_dir, input_pattern))

    # Merge the input files into a single output file
    gdal.Warp(
        output,
        input_files,
        format=output_format,
        dstNodata=output_nodata,
        options=output_options,
    )
