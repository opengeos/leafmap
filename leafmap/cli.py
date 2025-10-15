"""Command-line interface for leafmap."""

import argparse
import os
import sys
import webbrowser
from typing import Optional
from .common import read_vector


def view_raster(
    file_path: str,
    port: Optional[int] = None,
    indexes: Optional[int | list[int]] = None,
    colormap: Optional[str] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    nodata: Optional[float] = None,
    open_browser: bool = True,
) -> None:
    """
    View a raster file interactively in the browser using localtileserver.

    Args:
        file_path (str): Path or URL to the raster file to view. Supports both local
            paths and HTTP/HTTPS URLs.
        port (int, optional): Port to use for the tile server. Defaults to None.
        indexes (int | list[int], optional): Band index to display (1-based) or list of
            band indices for RGB visualization (e.g., [3, 2, 1]). Defaults to None.
        colormap (str, optional): Colormap name to apply. Defaults to None.
        vmin (float, optional): Minimum value for color mapping. Defaults to None.
        vmax (float, optional): Maximum value for color mapping. Defaults to None.
        nodata (float, optional): Nodata value to use. Defaults to None.
        open_browser (bool, optional): Whether to open browser automatically. Defaults to True.

    Raises:
        FileNotFoundError: If the local raster file does not exist.
        ImportError: If localtileserver is not installed.
    """
    try:
        from localtileserver import TileClient
    except ImportError:
        print(
            "Error: localtileserver is not installed. "
            "Install it with: pip install 'leafmap[raster]'"
        )
        sys.exit(1)

    # Check if it's a URL or local file
    is_url = file_path.startswith("http://") or file_path.startswith("https://")

    if not is_url:
        # Expand and validate local file path
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)

        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

    print(f"Loading raster: {file_path}")

    # Create TileClient
    try:
        client_args = {}
        if port:
            client_args["port"] = port

        tile_client = TileClient(file_path, **client_args)
    except Exception as e:
        print(f"Error creating tile client: {e}")
        sys.exit(1)

    # Get tile URL with parameters
    # TileClient.get_tile_url() accepts indexes, colormap, vmin, vmax, nodata as parameters
    tile_url_kwargs = {}
    if indexes is not None:
        tile_url_kwargs["indexes"] = indexes
    if colormap:
        tile_url_kwargs["colormap"] = colormap
    if vmin is not None:
        tile_url_kwargs["vmin"] = vmin
    if vmax is not None:
        tile_url_kwargs["vmax"] = vmax
    if nodata is not None:
        tile_url_kwargs["nodata"] = nodata

    tile_url = tile_client.get_tile_url(**tile_url_kwargs)

    # Get bounds and metadata for the raster
    # bounds() returns (lat_min, lat_max, lon_min, lon_max)
    bounds = tile_client.bounds()
    center_lat = (bounds[0] + bounds[1]) / 2
    center_lon = (bounds[2] + bounds[3]) / 2

    # Get proper zoom level
    default_zoom = tile_client.default_zoom
    min_zoom = tile_client.min_zoom
    max_zoom = tile_client.max_zoom

    # Get metadata
    metadata = tile_client.metadata
    n_bands = len(tile_client.band_names)
    width = metadata.get("width", "N/A")
    height = metadata.get("height", "N/A")

    # Create HTML viewer
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leafmap Raster Viewer - {os.path.basename(file_path)}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@latest/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@latest/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            position: absolute;
            top: 50px;
            bottom: 0;
            left: 0;
            right: 0;
        }}
        .header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 50px;
            background-color: #2c3e50;
            color: white;
            display: flex;
            align-items: center;
            padding: 0 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        .header h1 {{
            margin: 0;
            font-size: 18px;
            font-weight: 500;
        }}
        .info-panel {{
            position: absolute;
            bottom: 35px;
            right: 10px;
            background: white;
            padding: 10px 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 12px;
            max-width: 300px;
        }}
        .info-panel h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
        }}
        .info-item {{
            margin: 5px 0;
        }}
        .info-label {{
            font-weight: bold;
        }}
        .opacity-control {{
            position: absolute;
            bottom: 35px;
            right: 220px;
            background: white;
            padding: 12px 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 12px;
            min-width: 200px;
        }}
        .opacity-control h4 {{
            margin: 0 0 8px 0;
            font-size: 13px;
            font-weight: 600;
        }}
        .slider-container {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .opacity-slider {{
            flex: 1;
            height: 4px;
            border-radius: 2px;
            background: #ddd;
            outline: none;
            -webkit-appearance: none;
        }}
        .opacity-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #2c3e50;
            cursor: pointer;
        }}
        .opacity-slider::-moz-range-thumb {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #2c3e50;
            cursor: pointer;
            border: none;
        }}
        .opacity-value {{
            font-weight: 600;
            min-width: 35px;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Leafmap Raster Viewer: {os.path.basename(file_path)}</h1>
    </div>
    <div class="opacity-control">
        <h4>Raster Opacity</h4>
        <div class="slider-container">
            <input type="range" min="0" max="100" value="80" class="opacity-slider" id="opacitySlider">
            <span class="opacity-value" id="opacityValue">80%</span>
        </div>
    </div>
    <div class="info-panel">
        <h3>Raster Information</h3>
        <div class="info-item"><span class="info-label">File:</span> {os.path.basename(file_path)}</div>
        <div class="info-item"><span class="info-label">Bands:</span> {n_bands}</div>
        <div class="info-item"><span class="info-label">Width:</span> {width}</div>
        <div class="info-item"><span class="info-label">Height:</span> {height}</div>
        {f'<div class="info-item"><span class="info-label">Colormap:</span> {colormap}</div>' if colormap else ''}
        {f'<div class="info-item"><span class="info-label">Band{"s" if isinstance(indexes, list) else ""}:</span> {indexes if not isinstance(indexes, list) else str(indexes)}</div>' if indexes else ''}
    </div>
    <div id="map"></div>
    <script>
        // Initialize map with center and default zoom
        var map = L.map('map').setView([{center_lat}, {center_lon}], {default_zoom});

        // Add base layer
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }}).addTo(map);

        // Add raster layer with correct tile URL
        // Use maxNativeZoom to allow zooming beyond the raster's max zoom
        // by scaling tiles from the highest available zoom level
        var rasterLayer = L.tileLayer('{tile_url}', {{
            attribution: 'Raster Layer',
            opacity: 0.8,
            minZoom: {min_zoom},
            maxNativeZoom: {max_zoom},
            maxZoom: 22
        }}).addTo(map);

        // Fit bounds to raster (bounds format: lat_min, lat_max, lon_min, lon_max)
        var bounds = L.latLngBounds(
            [{bounds[0]}, {bounds[2]}],
            [{bounds[1]}, {bounds[3]}]
        );
        map.fitBounds(bounds);

        // Add layer control
        var baseMaps = {{
            "OpenStreetMap": L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}),
            "Satellite": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                attribution: 'Tiles &copy; Esri'
            }})
        }};

        var overlayMaps = {{
            "Raster": rasterLayer
        }};

        L.control.layers(baseMaps, overlayMaps).addTo(map);

        // Add scale
        L.control.scale().addTo(map);

        // Add coordinates display
        var coordsDiv = L.control({{position: 'bottomleft'}});
        coordsDiv.onAdd = function(map) {{
            this._div = L.DomUtil.create('div', 'info-panel');
            this._div.style.bottom = '35px';
            this._div.style.left = '10px';
            this._div.style.right = 'auto';
            this._div.style.top = 'auto';
            this.update();
            return this._div;
        }};
        coordsDiv.update = function(latlng) {{
            this._div.innerHTML = latlng ?
                '<span class="info-label">Lat:</span> ' + latlng.lat.toFixed(6) + '<br><span class="info-label">Lon:</span> ' + latlng.lng.toFixed(6) :
                'Move mouse over map';
        }};
        coordsDiv.addTo(map);

        map.on('mousemove', function(e) {{
            coordsDiv.update(e.latlng);
        }});

        // Opacity slider control
        var opacitySlider = document.getElementById('opacitySlider');
        var opacityValue = document.getElementById('opacityValue');

        opacitySlider.addEventListener('input', function() {{
            var opacity = this.value / 100;
            rasterLayer.setOpacity(opacity);
            opacityValue.textContent = this.value + '%';
        }});
    </script>
</body>
</html>
"""

    # Save HTML to temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html_content)
        html_file = f.name

    print(f"\nRaster viewer created successfully!")
    print(f"  - Bands: {n_bands}")
    print(f"  - Size: {width} x {height}")
    print(f"  - Zoom levels: {min_zoom}-{max_zoom}")
    print(f"  - Server: http://localhost:{tile_client.server.port}")

    if colormap:
        print(f"  - Colormap: {colormap}")
    if indexes:
        if isinstance(indexes, list):
            print(f"  - Bands (RGB): {indexes}")
        else:
            print(f"  - Band: {indexes}")

    # Open in browser
    if open_browser:
        print(f"\nOpening viewer in browser...")
        webbrowser.open(f"file://{html_file}")
    else:
        print(f"\nViewer HTML saved to: {html_file}")
        print(f"Open it manually in your browser.")

    print("\nPress Ctrl+C to stop the server and exit.")

    try:
        # Keep the server running
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        try:
            os.unlink(html_file)
        except Exception:
            pass
        print("Goodbye!")


def view_vector(
    file_path: str,
    style: str = "dark-matter",
    open_browser: bool = True,
) -> None:
    """
    View a vector file interactively in the browser using maplibregl.

    Args:
        file_path (str): Path or URL to the vector file to view. Supports both local
            paths and HTTP/HTTPS URLs.
        style (str, optional): Map style. Defaults to "dark-matter".
        open_browser (bool, optional): Whether to open browser automatically. Defaults to True.

    Raises:
        FileNotFoundError: If the local vector file does not exist.
        ImportError: If required dependencies are not installed.
    """
    try:
        from leafmap import maplibregl
    except ImportError:
        print(
            "Error: maplibregl dependencies are not installed. "
            "Install them with: pip install 'leafmap[maplibre]'"
        )
        sys.exit(1)

    # Check if it's a URL or local file
    is_url = file_path.startswith("http://") or file_path.startswith("https://")

    if not is_url:
        # Expand and validate local file path
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)

        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

    print(f"Loading vector: {file_path}")

    try:

        # Read vector file
        gdf = read_vector(file_path)

        # Get info
        n_features = len(gdf)
        geom_type = gdf.geom_type.iloc[0] if len(gdf) > 0 else "Unknown"
        crs = gdf.crs.to_string() if gdf.crs else "Unknown"
        gdf = gdf.to_crs(epsg=4326)

        # Create map
        m = maplibregl.Map(
            style=style,
            height="100%",
            use_message_queue=True,
        )

        # Add vector data
        m.add_vector(gdf, name="Vector Layer")
        m.add_layer_control()

        # Generate HTML
        html_content = m.to_html(title="Leafmap Vector Viewer")

        print(f"\nVector viewer created successfully!")
        print(f"  - Features: {n_features}")
        print(f"  - Geometry: {geom_type}")
        print(f"  - CRS: {crs}")
        print(f"  - Style: {style}")

    except Exception as e:
        print(f"Error loading vector file: {e}")
        sys.exit(1)

    # Save HTML to temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html_content)
        html_file = f.name

    # Open in browser
    if open_browser:
        print(f"\nOpening viewer in browser...")
        webbrowser.open(f"file://{html_file}")
    else:
        print(f"\nViewer HTML saved to: {html_file}")
        print(f"Open it manually in your browser.")

    print("\nViewer is ready. Close the browser when done.")


def view_raster_cli():
    """Direct CLI entry point for view-raster command."""
    parser = argparse.ArgumentParser(
        description="View a raster file interactively in the browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file_path", help="Path or URL to the raster file")
    parser.add_argument(
        "--port", type=int, help="Port for the tile server (default: auto)"
    )
    parser.add_argument(
        "--band",
        "--indexes",
        type=str,
        dest="indexes",
        help="Band index to display (1-based) or comma-separated list for RGB (e.g., '3,2,1')",
    )
    parser.add_argument("--colormap", help="Colormap name to apply")
    parser.add_argument("--vmin", type=float, help="Minimum value for color mapping")
    parser.add_argument("--vmax", type=float, help="Maximum value for color mapping")
    parser.add_argument("--nodata", type=float, help="Nodata value")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    args = parser.parse_args()

    # Parse indexes: can be a single int or comma-separated list
    indexes = None
    if args.indexes:
        if "," in args.indexes:
            indexes = [int(x.strip()) for x in args.indexes.split(",")]
        else:
            indexes = int(args.indexes)

    view_raster(
        file_path=args.file_path,
        port=args.port,
        indexes=indexes,
        colormap=args.colormap,
        vmin=args.vmin,
        vmax=args.vmax,
        nodata=args.nodata,
        open_browser=not args.no_browser,
    )


def view_vector_cli():
    """Direct CLI entry point for view-vector command."""
    parser = argparse.ArgumentParser(
        description="View a vector file interactively in the browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file_path", help="Path or URL to the vector file")
    parser.add_argument(
        "--style",
        default="dark-matter",
        help="Map style (default: dark-matter). Options: dark-matter, positron, voyager, etc.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    args = parser.parse_args()

    view_vector(
        file_path=args.file_path,
        style=args.style,
        open_browser=not args.no_browser,
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Leafmap - Interactive geospatial analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # view-raster command
    raster_parser = subparsers.add_parser(
        "view-raster", help="View a raster file interactively in the browser"
    )
    raster_parser.add_argument("file_path", help="Path or URL to the raster file")
    raster_parser.add_argument(
        "--port", type=int, help="Port for the tile server (default: auto)"
    )
    raster_parser.add_argument(
        "--band",
        "--indexes",
        type=str,
        dest="indexes",
        help="Band index to display (1-based) or comma-separated list for RGB (e.g., '3,2,1')",
    )
    raster_parser.add_argument("--colormap", help="Colormap name to apply")
    raster_parser.add_argument(
        "--vmin", type=float, help="Minimum value for color mapping"
    )
    raster_parser.add_argument(
        "--vmax", type=float, help="Maximum value for color mapping"
    )
    raster_parser.add_argument("--nodata", type=float, help="Nodata value")
    raster_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    # view-vector command
    vector_parser = subparsers.add_parser(
        "view-vector", help="View a vector file interactively in the browser"
    )
    vector_parser.add_argument("file_path", help="Path or URL to the vector file")
    vector_parser.add_argument(
        "--style",
        default="dark-matter",
        help="Map style (default: dark-matter)",
    )
    vector_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )

    args = parser.parse_args()

    if args.command == "view-raster":
        # Parse indexes: can be a single int or comma-separated list
        indexes = None
        if args.indexes:
            if "," in args.indexes:
                indexes = [int(x.strip()) for x in args.indexes.split(",")]
            else:
                indexes = int(args.indexes)

        view_raster(
            file_path=args.file_path,
            port=args.port,
            indexes=indexes,
            colormap=args.colormap,
            vmin=args.vmin,
            vmax=args.vmax,
            nodata=args.nodata,
            open_browser=not args.no_browser,
        )
    elif args.command == "view-vector":
        view_vector(
            file_path=args.file_path,
            style=args.style,
            open_browser=not args.no_browser,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
