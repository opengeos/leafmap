"""This module contains some common functions for both folium and ipyleaflet.
"""

import csv
import os
import shutil
import tarfile
import urllib.request
import zipfile
import ipywidgets as widgets
from IPython.display import display


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def is_drive_mounted():
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
    import requests

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


def check_install(package):
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
        clone_repo(out_dir=download_dir)

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


def clone_repo(out_dir=".", unzip=True):
    """Clones the leafmap GitHub repository.

    Args:
        out_dir (str, optional): Output folder for the repo. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the repository. Defaults to True.
    """
    url = "https://github.com/giswqs/leafmap/archive/master.zip"
    filename = "leafmap-master.zip"
    download_from_url(url, out_file_name=filename, out_dir=out_dir, unzip=unzip)


def install_from_github(url):
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


def check_git_install():
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


def clone_github_repo(url, out_dir):
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


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    from shutil import which

    return which(name) is not None


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
    import requests
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
    if not is_tool(pkg_name):
        check_install(pkg_name)

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
    """Download a file from a URL (e.g., https://github.com/giswqs/whitebox/raw/master/examples/testdata.zip)

    Args:
        url (str): The HTTP URL to download.
        out_file_name (str, optional): The output file name to use. Defaults to None.
        out_dir (str, optional): The output directory to use. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the downloaded file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    in_file_name = os.path.basename(url)

    if out_file_name is None:
        out_file_name = in_file_name
    out_file_path = os.path.join(os.path.abspath(out_dir), out_file_name)

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
    from google_drive_downloader import GoogleDriveDownloader as gdd

    file_id = gfile_url.split("/")[5]
    if verbose:
        print("Google Drive file id: {}".format(file_id))

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
    import whitebox

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


def csv_to_shp(in_csv, out_shp, latitude="latitude", longitude="longitude"):
    """Converts a csv file with latlon info to a point shapefile.

    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
    """
    import shapefile as shp

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_name = os.path.basename(in_csv)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir)
        in_csv = os.path.join(out_dir, out_name)

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        points = shp.Writer(out_shp, shapeType=shp.POINT)
        with open(in_csv, encoding="utf-8") as csvfile:
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


def csv_to_geojson(
    in_csv, out_geojson=None, latitude="latitude", longitude="longitude"
):
    """Creates points for a CSV file and exports data as a GeoJSON.

    Args:
        in_csv (str): The file path to the input CSV file.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".

    """

    import json
    import shapefile

    if out_geojson is not None:
        out_dir = os.path.dirname(out_geojson)
    else:
        out_dir = os.path.expanduser("~/Downloads")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_shp = os.path.join(out_dir, random_string() + ".shp")

    csv_to_shp(in_csv, out_shp, latitude=latitude, longitude=longitude)
    sf = shapefile.Reader(out_shp)
    geojson = sf.__geo_interface__

    delete_shp(out_shp, verbose=False)

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding="utf-8") as f:
            f.write(json.dumps(geojson))


def csv_to_gdf(in_csv, latitude="latitude", longitude="longitude"):
    """Creates points for a CSV file and converts them to a GeoDataFrame.

    Args:
        in_csv (str): The file path to the input CSV file.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".

    Returns:
        object: GeoDataFrame.
    """

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    out_dir = os.path.expanduser("~/Downloads")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_shp = os.path.join(out_dir, random_string() + ".shp")

    csv_to_shp(in_csv, out_shp, latitude=latitude, longitude=longitude)

    gdf = gpd.read_file(out_shp)
    delete_shp(out_shp)
    return gdf


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


def get_cog_tile(url, titiler_endpoint="https://api.cogeo.xyz/", **kwargs):
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG).
        Source code adapted from https://developmentseed.org/titiler/examples/Working_with_CloudOptimizedGeoTIFF_simple/

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        tuple: Returns the COG Tile layer URL and bounds.
    """
    import requests

    params = {"url": url}

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
    if "tile_format" in kwargs.keys():
        params["tile_format"] = kwargs["tile_format"]
    if "tile_scale" in kwargs.keys():
        params["tile_scale"] = kwargs["tile_scale"]
    if "minzoom" in kwargs.keys():
        params["minzoom"] = kwargs["minzoom"]
    if "maxzoom" in kwargs.keys():
        params["maxzoom"] = kwargs["maxzoom"]

    r = requests.get(
        f"{titiler_endpoint}/cog/{TileMatrixSetId}/tilejson.json", params=params
    ).json()

    return r["tiles"][0]


def get_cog_mosaic(
    links,
    titiler_endpoint="https://api.cogeo.xyz/",
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):

    import requests

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


def get_cog_bounds(url, titiler_endpoint="https://api.cogeo.xyz/"):
    """Get the bounding box of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """
    import requests

    r = requests.get(f"{titiler_endpoint}/cog/bounds", params={"url": url}).json()

    if "bounds" in r.keys():
        bounds = r["bounds"]
    else:
        bounds = None
    return bounds


def get_cog_center(url, titiler_endpoint="https://api.cogeo.xyz/"):
    """Get the centroid of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    bounds = get_cog_bounds(url, titiler_endpoint)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def get_cog_bands(url, titiler_endpoint="https://api.cogeo.xyz/"):
    """Get band names of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        list: A list of band names
    """
    import requests

    r = requests.get(
        f"{titiler_endpoint}/cog/info",
        params={
            "url": url,
        },
    ).json()

    bands = [b[1] for b in r["band_descriptions"]]
    return bands


def get_stac_tile(url, bands=None, titiler_endpoint="https://api.cogeo.xyz/", **kwargs):
    """Get a tile layer from a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        tuple: Returns the COG Tile layer URL and bounds.
    """
    import requests

    params = {"url": url}

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
    if "expression" in kwargs.keys():
        params["expression"] = kwargs["expression"]
    if "tile_format" in kwargs.keys():
        params["tile_format"] = kwargs["tile_format"]
    if "tile_scale" in kwargs.keys():
        params["tile_scale"] = kwargs["tile_scale"]
    if "minzoom" in kwargs.keys():
        params["minzoom"] = kwargs["minzoom"]
    if "maxzoom" in kwargs.keys():
        params["maxzoom"] = kwargs["maxzoom"]

    allowed_bands = get_stac_bands(url, titiler_endpoint)

    if bands is None:
        bands = [allowed_bands[0]]
    elif len(bands) <= 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        raise Exception(
            "You can only select 3 bands from the following: {}".format(
                ", ".join(allowed_bands)
            )
        )

    assets = ",".join(bands)
    params["assets"] = assets

    r = requests.get(
        f"{titiler_endpoint}/stac/{TileMatrixSetId}/tilejson.json", params=params
    ).json()

    return r["tiles"][0]


def get_stac_bounds(url, titiler_endpoint="https://api.cogeo.xyz/"):
    """Get the bounding box of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """
    import requests

    r = requests.get(f"{titiler_endpoint}/stac/bounds", params={"url": url}).json()

    bounds = r["bounds"]
    return bounds


def get_stac_center(url, titiler_endpoint="https://api.cogeo.xyz/"):
    """Get the centroid of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    bounds = get_stac_bounds(url, titiler_endpoint)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def get_stac_bands(url, titiler_endpoint="https://api.cogeo.xyz/"):
    """Get band names of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".

    Returns:
        list: A list of band names
    """
    import requests

    r = requests.get(
        f"{titiler_endpoint}/stac/assets",
        params={
            "url": url,
        },
    ).json()

    return r


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


def csv_to_pandas(in_csv, **kwargs):
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


def shp_to_geojson(in_shp, out_json=None, **kwargs):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    try:
        import shapefile
        from datetime import date

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
                in_gdf = gpd.read_file(in_shp)
                out_gdf = in_gdf.to_crs(epsg="4326")
                out_shp = in_shp.replace(".shp", "_gcs.shp")
                out_gdf.to_file(out_shp)
                in_shp = out_shp
            except Exception as e:
                raise Exception(e)

        if "encoding" in kwargs:
            reader = shapefile.Reader(in_shp, encoding=kwargs.pop("encoding"))
        else:
            reader = shapefile.Reader(in_shp)
        out_dict = reader.__geo_interface__

        if out_json is not None:
            from json import dumps

            with open(out_json, "w") as geojson:
                geojson.write(dumps(out_dict, indent=2) + "\n")
        else:
            return out_dict

    except Exception as e:
        raise Exception(e)


def delete_shp(in_shp, verbose=True):
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
    filename, out_geojson=None, bbox=None, mask=None, rows=None, epsg="4326", **kwargs
):
    """Converts any geopandas-supported vector dataset to GeoJSON.

    Args:
        filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
        out_geojson (str, optional): The file path to the output GeoJSON. Defaults to None.
        bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
        mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
        rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
        epsg (str, optional): The EPSG number to convert to. Defaults to "4326".

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
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        df = gpd.read_file(
            filename, bbox=bbox, mask=mask, rows=rows, driver="KML", **kwargs
        )
    else:
        df = gpd.read_file(filename, bbox=bbox, mask=mask, rows=rows, **kwargs)
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
    from mss import mss

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


def gdf_to_geojson(gdf, out_geojson=None, epsg=None):
    """Converts a GeoDataFame to GeoJSON.

    Args:
        gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        out_geojson (str, optional): File path to he output GeoJSON. Defaults to None.
        epsg (str, optional): An EPSG string, e.g., "4326". Defaults to None.

    Raises:
        TypeError: When the output file extension is incorrect.
        Exception: When the conversion fails.

    Returns:
        dict: When the out_json is None returns a dict.
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    try:
        if epsg is not None:
            gdf = gdf.to_crs(epsg=epsg)
        geojson = gdf.__geo_interface__

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

            gdf.to_file(out_geojson, driver="GeoJSON")
    except Exception as e:
        raise Exception(e)


def connect_postgis(
    database, host="localhost", user=None, password=None, use_env_var=False
):
    """Connects to a PostGIS database.

    Args:
        database (str): Name of the database
        host (str, optional): Hosting server for the database. Defaults to "localhost".
        user (str, optional): User name to access the database. Defaults to None.
        password (str, optional): Password to access the database. Defaults to None.
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

    connection_string = f"postgresql://{user}:{password}@{host}/{database}"
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
    """Retrieves the column names of a vector atrribute table.

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


def planet_monthly_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

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

    url_list = []
    for year in range(2020, year_now + 1):

        for month in range(1, 13):
            m_str = str(year) + "-" + str(month).zfill(2)

            if year == 2020 and month < 9:
                continue
            if year == year_now and month >= month_now:
                break

            prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
            subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="
            url = f"{prefix}{m_str}{subfix}{api_key}"
            url_list.append(url)

    return url_list


def planet_biannual_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual imagery URLs based on API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

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

    url_list = []

    for d in dates:
        prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
        subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="
        url = f"{prefix}{d}{subfix}{api_key}"
        url_list.append(url)

    return url_list


def planet_catalog_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

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
    """Generates Planet  monthly imagery TileLayer based on API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import ipyleaflet
    import folium

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    url_list = planet_monthly_tropical(api_key, token_name)
    for url in url_list:
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
    """Generates Planet  bi-annual imagery TileLayer based on API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    import ipyleaflet
    import folium

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    url_list = planet_biannual_tropical(api_key, token_name)
    for url in url_list:
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
    """Generates Planet  monthly imagery TileLayer based on API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

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
