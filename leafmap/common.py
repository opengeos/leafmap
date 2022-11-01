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
from typing import Union, List, Dict, Tuple
from IPython.display import display, IFrame


class TitilerEndpoint:
    """This class contains the methods for the titiler endpoint."""

    def __init__(
        self,
        endpoint="https://titiler.xyz",
        name="stac",
        TileMatrixSetId="WebMercatorQuad",
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
        endpoint="https://planetarycomputer.microsoft.com/api/data/v1",
        name="item",
        TileMatrixSetId="WebMercatorQuad",
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


def check_titiler_endpoint(titiler_endpoint=None):
    """Returns the default titiler endpoint.

    Returns:
        object: A titiler endpoint.
    """
    if titiler_endpoint is None:
        if os.environ.get("TITILER_ENDPOINT") == "planetary-computer":
            titiler_endpoint = PlanetaryComputerEndpoint()
        else:
            titiler_endpoint = TitilerEndpoint()
    elif titiler_endpoint in ["planetary-computer", "pc"]:
        titiler_endpoint = PlanetaryComputerEndpoint()

    return titiler_endpoint


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
    url = "https://github.com/giswqs/leafmap/archive/master.zip"
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
        out.clear_output(wait=True)
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
        in_color (str or tuple): It can be a string (e.g., 'red', '#ffff00') or tuple (e.g., (255, 127, 0)).

    Returns:
        str: A hex color code.
    """
    import colour

    out_color = "#000000"  # default black color
    if isinstance(in_color, tuple) and len(in_color) == 3:
        if all(isinstance(item, int) for item in in_color):
            rescaled_color = [x / 255.0 for x in in_color]
            out_color = colour.Color(rgb=tuple(rescaled_color))
            return out_color.hex_l
        else:
            print(
                "RGB color must be a tuple with three integer values ranging from 0 to 255."
            )
            return
    else:
        try:
            out_color = colour.Color(in_color)
            return out_color.hex_l
        except Exception as e:
            print("The provided color is invalid. Using the default black color.")
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
    """Download a file from a URL (e.g., https://github.com/giswqs/whitebox-python/raw/master/examples/testdata.zip)

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
                tar_ref.extractall(out_dir)
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
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
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


def cog_tile(url, bands=None, titiler_endpoint="https://titiler.xyz", **kwargs):
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG).
        Source code adapted from https://developmentseed.org/titiler/examples/notebooks/Working_with_CloudOptimizedGeoTIFF_simple/

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        bands (list, optional): List of bands to use. Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        tuple: Returns the COG Tile layer URL and bounds.
    """

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

    if "rescale" not in kwargs:
        stats = cog_stats(url, titiler_endpoint)
        if "message" not in stats:
            percentile_2 = min([stats[s]["percentile_2"] for s in stats])
            percentile_98 = max([stats[s]["percentile_98"] for s in stats])
            kwargs["rescale"] = f"{percentile_2},{percentile_98}"

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    r = requests.get(
        f"{titiler_endpoint}/cog/{TileMatrixSetId}/tilejson.json", params=kwargs
    ).json()
    return r["tiles"][0]


def cog_tile_vmin_vmax(
    url, bands=None, titiler_endpoint="https://titiler.xyz", percentile=True, **kwargs
):
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG) and return the minimum and maximum values.

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        bands (list, optional): List of bands to use. Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        percentile (bool, optional): Whether to use percentiles or not. Defaults to True.
    Returns:
        tuple: Returns the minimum and maximum values.
    """
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
    links,
    titiler_endpoint="https://titiler.xyz",
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):
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

    if layername is None:
        layername = "layer_" + random_string(5)

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
    filepath,
    skip_rows=0,
    titiler_endpoint="https://titiler.xyz",
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):
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


def cog_bounds(url, titiler_endpoint="https://titiler.xyz"):
    """Get the bounding box of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    r = requests.get(f"{titiler_endpoint}/cog/bounds", params={"url": url}).json()

    if "bounds" in r.keys():
        bounds = r["bounds"]
    else:
        bounds = None
    return bounds


def cog_center(url, titiler_endpoint="https://titiler.xyz"):
    """Get the centroid of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    bounds = cog_bounds(url, titiler_endpoint)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def cog_bands(url, titiler_endpoint="https://titiler.xyz"):
    """Get band names of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A list of band names
    """

    r = requests.get(
        f"{titiler_endpoint}/cog/info",
        params={
            "url": url,
        },
    ).json()

    bands = [b[0] for b in r["band_descriptions"]]
    return bands


def cog_stats(url, titiler_endpoint="https://titiler.xyz"):
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A dictionary of band statistics.
    """

    r = requests.get(
        f"{titiler_endpoint}/cog/statistics",
        params={
            "url": url,
        },
    ).json()

    return r


def cog_info(url, titiler_endpoint="https://titiler.xyz", return_geojson=False):
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A dictionary of band info.
    """

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
    lon,
    lat,
    url,
    bidx=None,
    titiler_endpoint="https://titiler.xyz",
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
    url=None,
    collection=None,
    item=None,
    assets=None,
    bands=None,
    titiler_endpoint=None,
    **kwargs,
):

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

        # if ("expression" in kwargs) and ("rescale" not in kwargs):
        #     stats = stac_stats(
        #         collection=collection,
        #         item=item,
        #         expression=kwargs["expression"],
        #         titiler_endpoint=titiler_endpoint,
        #     )
        #     kwargs[
        #         "rescale"
        #     ] = f"{stats[0]['percentile_2']},{stats[0]['percentile_98']}"

        # if ("asset_expression" in kwargs) and ("rescale" not in kwargs):
        #     stats = stac_stats(
        #         collection=collection,
        #         item=item,
        #         expression=kwargs["asset_expression"],
        #         titiler_endpoint=titiler_endpoint,
        #     )
        #     kwargs[
        #         "rescale"
        #     ] = f"{stats[0]['percentile_2']},{stats[0]['percentile_98']}"

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
        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")

        if assets is None and (bands is not None):
            assets = bands
        else:
            kwargs["asset_bidx"] = bands
        kwargs["assets"] = assets

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/{TileMatrixSetId}/tilejson.json",
            params=kwargs,
        ).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_item(), params=kwargs).json()

    return r["tiles"][0]


def stac_bounds(url=None, collection=None, item=None, titiler_endpoint=None, **kwargs):
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

    if url is not None:
        kwargs["url"] = url
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


def stac_center(url=None, collection=None, item=None, titiler_endpoint=None, **kwargs):
    """Get the centroid of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    bounds = stac_bounds(url, collection, item, titiler_endpoint, **kwargs)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lon, lat)
    return center


def stac_bands(url=None, collection=None, item=None, titiler_endpoint=None, **kwargs):
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
    url=None, collection=None, item=None, assets=None, titiler_endpoint=None, **kwargs
):
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


def stac_info(
    url=None, collection=None, item=None, assets=None, titiler_endpoint=None, **kwargs
):
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
    url=None, collection=None, item=None, assets=None, titiler_endpoint=None, **kwargs
):
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


def stac_assets(url=None, collection=None, item=None, titiler_endpoint=None, **kwargs):
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
    lon,
    lat,
    url=None,
    collection=None,
    item=None,
    assets=None,
    titiler_endpoint=None,
    verbose=True,
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
        assets = ",".join(assets)
    kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/{lon},{lat}", params=kwargs).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_pixel_value(lon, lat), params=kwargs
        ).json()

    if "detail" in r:
        if verbose:
            print(r["detail"])
        return None
    else:
        values = [v[0] for v in r["values"]]
        result = dict(zip(assets.split(","), values))
        return result


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
        bounds (list): A list of coordinates representing [left, bottom, right, top].

    Returns:
        dict: A geojson feature.
    """
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

    # import fiona
    # print(fiona.supported_drivers)
    gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
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

    # import fiona
    # print(fiona.supported_drivers)
    gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
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


def shp_to_geojson(in_shp, out_json=None, encoding="utf-8", **kwargs):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    try:
        import shapefile

        in_shp = os.path.abspath(in_shp)

        if out_json is not None:
            ext = os.path.splitext(out_json)[1]
            print(ext)
            if ext.lower() not in [".json", ".geojson"]:
                raise TypeError("The output file extension must the .json or .geojson.")

            if not os.path.exists(os.path.dirname(out_json)):
                os.makedirs(os.path.dirname(out_json))

        if not is_GCS(in_shp):
            try:
                import geopandas as gpd

            except Exception:
                raise ImportError(
                    "Geopandas is required to perform reprojection of the data. See https://geopandas.org/install.html"
                )

            try:
                in_gdf = gpd.read_file(in_shp, encoding=encoding)
                out_gdf = in_gdf.to_crs(epsg="4326")
                out_shp = in_shp.replace(".shp", "_gcs.shp")
                out_gdf.to_file(out_shp)
                in_shp = out_shp
            except Exception as e:
                raise Exception(e)

        kwargs["encoding"] = encoding
        if "encoding" in kwargs:
            reader = shapefile.Reader(in_shp, encoding=kwargs.pop("encoding"))
        else:
            reader = shapefile.Reader(in_shp)
        out_dict = reader.__geo_interface__

        if out_json is not None:
            import json

            with open(out_json, "w") as geojson:
                geojson.write(json.dumps(out_dict, indent=2) + "\n")
        else:
            return out_dict

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

    if not filename.startswith("http"):
        filename = os.path.abspath(filename)
        if filename.endswith(".zip"):
            filename = "zip://" + filename
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
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

    if not filename.startswith("http"):
        filename = os.path.abspath(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
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


def create_legend(
    legend_title="Legend",
    legend_dict=None,
    legend_keys=None,
    legend_colors=None,
    builtin_legend=None,
    **kwargs,
):
    """Create a custom legend.

    Args:
        legend_title (str, optional): Title of the legend. Defaults to 'Legend'.
        legend_dict (dict, optional): A dictionary containing legend items as keys and color as values. If provided, legend_keys and legend_colors will be ignored. Defaults to None.
        legend_keys (list, optional): A list of legend keys. Defaults to None.
        legend_colors (list, optional): A list of legend colors. Defaults to None.
        builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.

    """
    import pkg_resources
    from .legends import builtin_legends

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("leafmap", "leafmap.py"))
    legend_template = os.path.join(pkg_dir, "data/template/legend.html")

    # if "min_width" not in kwargs.keys():
    #     min_width = None
    # if "max_width" not in kwargs.keys():
    #     max_width = None
    # else:
    #     max_width = kwargs["max_width"]
    # if "min_height" not in kwargs.keys():
    #     min_height = None
    # else:
    #     min_height = kwargs["min_height"]
    # if "max_height" not in kwargs.keys():
    #     max_height = None
    # else:
    #     max_height = kwargs["max_height"]
    # if "height" not in kwargs.keys():
    #     height = None
    # else:
    #     height = kwargs["height"]
    # if "width" not in kwargs.keys():
    #     width = None
    # else:
    #     width = kwargs["width"]

    # if width is None:
    #     max_width = "300px"
    # if height is None:
    #     max_height = "400px"

    if not os.path.exists(legend_template):
        print("The legend template does not exist.")
        return

    if legend_keys is not None:
        if not isinstance(legend_keys, list):
            print("The legend keys must be a list.")
            return
    else:
        legend_keys = ["One", "Two", "Three", "Four", "etc"]

    if legend_colors is not None:
        if not isinstance(legend_colors, list):
            print("The legend colors must be a list.")
            return
        elif all(isinstance(item, tuple) for item in legend_colors):
            try:
                legend_colors = [rgb_to_hex(x) for x in legend_colors]
            except Exception as e:
                print(e)
        elif all((item.startswith("#") and len(item) == 7) for item in legend_colors):
            pass
        elif all((len(item) == 6) for item in legend_colors):
            pass
        else:
            print("The legend colors must be a list of tuples.")
            return
    else:
        legend_colors = [
            "#8DD3C7",
            "#FFFFB3",
            "#BEBADA",
            "#FB8072",
            "#80B1D3",
        ]

    if len(legend_keys) != len(legend_colors):
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
            legend_keys = list(legend_dict.keys())
            legend_colors = list(legend_dict.values())

    if legend_dict is not None:
        if not isinstance(legend_dict, dict):
            print("The legend dict must be a dictionary.")
            return
        else:
            legend_keys = list(legend_dict.keys())
            legend_colors = list(legend_dict.values())
            if all(isinstance(item, tuple) for item in legend_colors):
                try:
                    legend_colors = [rgb_to_hex(x) for x in legend_colors]
                except Exception as e:
                    print(e)

    header = []
    content = []
    footer = []

    with open(legend_template) as f:
        lines = f.readlines()
        lines[3] = lines[3].replace("Legend", legend_title)
        header = lines[:6]
        footer = lines[11:]

    for index, key in enumerate(legend_keys):
        color = legend_colors[index]
        if not color.startswith("#"):
            color = "#" + color
        item = "      <li><span style='background:{};'></span>{}</li>\n".format(
            color, key
        )
        content.append(item)

    legend_html = header + content + footer
    legend_text = "".join(legend_html)
    return legend_text


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

    # Make it compatible with binder and JupyterHub
    if os.environ.get("JUPYTERHUB_SERVICE_PREFIX") is not None:
        os.environ[
            "LOCALTILESERVER_CLIENT_PREFIX"
        ] = f"{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}"

    from localtileserver import (
        get_leaflet_tile_layer,
        get_folium_tile_layer,
        TileClient,
    )

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

    if tile_format == "ipyleaflet":
        tile_layer = get_leaflet_tile_layer(
            tile_client,
            port=port,
            debug=debug,
            projection=projection,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            name=layer_name,
            max_zoom=30,
            max_native_zoom=30,
            **kwargs,
        )
    else:
        tile_layer = get_folium_tile_layer(
            tile_client,
            port=port,
            debug=debug,
            projection=projection,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attr=attribution,
            overlay=True,
            name=layer_name,
            max_zoom=30,
            max_native_zoom=30,
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
        str: The geometry type of the GeoJSON object.
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


def bbox_to_gdf(bbox, crs="EPSG:4326"):
    """Converts a bounding box to a GeoDataFrame.

    Args:
        bbox (tuple): A bounding box in the form of a tuple (minx, miny, maxx, maxy).
        crs (str, optional): The coordinate reference system of the bounding box to convert to. Defaults to "EPSG:4326".

    Returns:
        geopandas.GeoDataFrame: A GeoDataFrame containing the bounding box.
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    from shapely.geometry import box
    import geopandas as gpd

    minx, miny, maxx, maxy = bbox
    geometry = box(minx, miny, maxx, maxy)
    d = {"geometry": [geometry]}
    gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")
    gdf.to_crs(crs=crs, inplace=True)
    return gdf


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
        str: The geometry type of the GeoDataFrame.
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

    if not os.path.exists(image):
        raise FileNotFoundError("The provided input file could not be found.")

    with rasterio.open(image, "r") as ds:
        arr = ds.read()  # read all raster values

    return arr


def numpy_to_cog(
    np_array, out_cog, bounds=None, profile=None, dtype=None, crs="epsg:4326"
):
    """Converts a numpy array to a COG file.

    Args:
        np_array (np.array): A numpy array representing the image.
        out_cog (str): The output COG file path.
        bounds (tuple, optional): The bounds of the image in the format of (minx, miny, maxx, maxy). Defaults to None.
        profile (str | dict, optional): File path to an existing COG file or a dictionary representing the profile. Defaults to None.
        dtype (str, optional): The data type of the output COG file. Defaults to None.
        crs (str, optional): The coordinate reference system of the output COG file. Defaults to "epsg:4326".

    """
    import warnings
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds

    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    warnings.filterwarnings("ignore")
    if not isinstance(np_array, np.ndarray):
        raise TypeError("The input array must be a numpy array.")

    out_dir = os.path.dirname(out_cog)
    check_dir(out_dir)

    if profile is not None:
        if isinstance(profile, str):
            if not os.path.exists(profile):
                raise FileNotFoundError("The provided file could not be found.")
            with rasterio.open(profile) as ds:
                bounds = ds.bounds
        elif isinstance(profile, rasterio.profiles.Profile):
            profile = dict(profile)
        elif not isinstance(profile, dict):
            raise TypeError("The provided profile must be a file path or a dictionary.")

    if bounds is None:
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

    src_transform = from_bounds(*bounds, width=width, height=height)
    if dtype is None:
        dtype = str(np_array.dtype)

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
            crs=crs,
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


def get_stac_collections(url):
    """Retrieve a list of STAC collections from a URL.
    This function is adapted from https://github.com/mykolakozyr/stacdiscovery/blob/a5d1029aec9c428a7ce7ae615621ea8915162824/app.py#L31.
    Credits to Mykola Kozyr.

    Args:
        url (str): A URL to a STAC catalog.

    Returns:
        list: A list of STAC collections.
    """
    from pystac_client import Client

    # Expensive function. Added cache for it.

    # Empty list that would be used for a dataframe to collect and visualize info about collections
    root_catalog = Client.open(url)
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

    Returns:
        GeoPandas.GeoDataFraem: A GeoDataFrame with the STAC items.
    """

    import itertools
    import geopandas as gpd
    from shapely.geometry import shape
    from pystac_client import Client

    # Empty list that would be used for a dataframe to collect and visualize info about collections
    items_list = []
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

    if titiler_endpoint is None:
        titiler_endpoint = "https://titiler.xyz"

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

    if titiler_endpoint is None:
        titiler_endpoint = "https://titiler.xyz"

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

    if titiler_endpoint is None:
        titiler_endpoint = "https://titiler.xyz"

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

    if titiler_endpoint is None:
        titiler_endpoint = "https://titiler.xyz"

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
):
    """Download a file from URL, including Google Drive shared URL.

    Args:
        url (str, optional): Google Drive URL is also supported. Defaults to None.
        output (str, optional): Output filename. Default is basename of URL.
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

    Returns:
        str: The output file path.
    """

    import gdown

    if output is None:
        if isinstance(url, str) and url.startswith("http"):
            output = os.path.basename(url)

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
            zip_ref.extractall(os.path.dirname(output))

    return os.path.abspath(output)


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
    import gdown

    files = gdown.download_folder(
        url, id, output, quiet, proxy, speed, use_cookies, remaining_ok
    )
    return files


def clip_image(image, mask, output):
    """Clip an image by mask.

    Args:
        image (str): Path to the image file in GeoTIFF format.
        mask (str | list | dict): The mask used to extract the image. It can be a path to vector datasets (e.g., GeoJSON, Shapefile), a list of coordinates, or m.user_roi.
        output (str): Path to the output file.

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
        raise ImportError(
            "pyxarray and rioxarray are required for plotting. Please install them using 'pip install rioxarray pyvista-xarray'."
        )

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
        raise ImportError(
            "pyxarray and rioxarray are required for plotting. Please install them using 'pip install rioxarray pyvista-xarray'."
        )

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
    region, out_dir=None, return_url=False, download_args={}, geopandas_args={}
) -> Union[None, List]:
    """Download the US National Elevation Datasets (NED) for a region.

    Args:
        region (str | list): A filepath to a vector dataset or a list of bounds in the form of [minx, miny, maxx, maxy].
        out_dir (str, optional): The directory to download the files to. Defaults to None, which uses the current working directory.
        return_url (bool, optional): Whether to return the download URLs of the files. Defaults to False.
        download_args (dict, optional): A dictionary of arguments to pass to the download_file function. Defaults to {}.
        geopandas_args (dict, optional): A dictionary of arguments to pass to the geopandas.read_file() function.
            Used for reading a region URL|filepath.

    Returns:
        list: A list of the download URLs of the files if return_url is True.
    """

    TNM = The_national_map_USGS()
    if return_url:
        return TNM.find_tiles(
            region=region, geopandas_args=geopandas_args, API={"q": "NED"}
        )
    return TNM.download_tiles(
        region=region,
        out_dir=out_dir,
        download_args=download_args,
        geopandas_args=geopandas_args,
        API={"q": "NED"},
    )


def mosaic(images, output, merge_args={}, verbose=True, **kwargs):
    """Mosaics a list of images into a single image. Inspired by https://bit.ly/3A6roDK.

    Args:
        images (str | list): An input directory containing images or a list of images.
        output (str): The output image filepath.
        merge_args (dict, optional): A dictionary of arguments to pass to the rasterio.merge function. Defaults to {}.
        verbose (bool, optional): Whether to print progress. Defaults to True.

    """
    from rasterio.merge import merge
    import rasterio as rio
    from pathlib import Path

    output = os.path.abspath(output)

    if isinstance(images, str):
        path = Path(images)
        raster_files = list(path.iterdir())
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


def reproject(image, output, dst_crs="EPSG:4326", resampling="nearest", **kwargs):
    """Reprojects an image.

    Args:
        image (str): The input image filepath.
        output (str): The output image filepath.
        dst_crs (str, optional): The destination CRS. Defaults to "EPSG:4326".
        resampling (Resampling, optional): The resampling method. Defaults to "nearest".
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
