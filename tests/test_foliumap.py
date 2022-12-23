#!/usr/bin/env python

"""Tests for `leafmap` module."""

import os
import unittest
import leafmap.foliumap as leafmap
import geopandas as gpd
import pandas as pd
from unittest.mock import patch


class TestFoliumap(unittest.TestCase):
    """Tests for `foliumap` module."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_add_basemap(self):
        """Check basemaps"""
        m = leafmap.Map()
        m.add_basemap("TERRAIN")
        out_str = m.to_html()
        assert "Google Terrain" in out_str

    # def test_add_cog_layer(self):
    #     """Check COG layer"""
    #     m = leafmap.Map()
    #     url = "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif"
    #     m.add_cog_layer(url, name="Fire (pre-event)")
    #     out_str = m.to_html()
    #     assert "Fire (pre-event)" in out_str

    # def test_add_cog_mosaic(self):
    #     """Check COG mosaic"""
    #     m = leafmap.Map()
    #     links = [
    #         "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif",
    #         "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-08-18/pine-gulch-fire20/1040010041D3B300.tif",
    #     ]

    #     m.add_cog_mosaic(links, name="COG mosaic", attribution="MAXAR")
    #     out_str = m.to_html()
    #     assert "COG mosaic" in out_str
    #     assert "MAXAR" in out_str

    def test_add_colorbar(self):
        """Check colorbar"""
        m = leafmap.Map()
        colors = ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"]
        vmin = 0
        vmax = 4000
        m.add_colorbar(colors=colors, vmin=vmin, vmax=vmax, caption="Elevation")
        out_str = m.to_html()
        assert "Elevation" in out_str

    # @patch("matplotlib.pyplot.show")
    # def test_add_colormap(self, mock_show):
    #     """Check colormap"""
    #     with self.assertRaises(NotImplementedError):
    #         m = leafmap.Map()
    #         m.add_colormap(cmap="gray", label="Elevation")
    #         out_str = m.to_html()
    #         assert "Elevation" in out_str

    def test_add_gdf(self):
        """Check GeoDataFrame"""
        m = leafmap.Map()
        gdf = gpd.read_file(
            "https://github.com/giswqs/leafmap/raw/master/examples/data/cable_geo.geojson"
        )
        m.add_gdf(gdf, layer_name="Cable lines")
        out_str = m.to_html()
        assert "Cable lines" in out_str

    def test_add_gdf_from_postgis(self):
        """Check PostGIS"""
        m = leafmap.Map()
        try:
            con = leafmap.connect_postgis(
                database="nyc",
                host="localhost",
                user=None,
                password=None,
                port=5432,
                use_env_var=True,
            )
            sql = "SELECT * FROM nyc_neighborhoods"
            gdf = leafmap.read_postgis(sql, con)
            m.add_gdf(gdf, layer_name="NYC")
            m.add_gdf_from_postgis(
                sql,
                con,
                layer_name="NYC Neighborhoods",
                fill_colors=["red", "green", "blue"],
            )
            out_str = m.to_html()
            assert "NYC Neighborhoods" in out_str

        except Exception as _:
            out_str = m.to_html()
            assert "NYC Neighborhoods" not in out_str

    def test_add_geojson(self):
        """Check GeoJSON"""
        m = leafmap.Map()
        in_geojson = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/cable_geo.geojson"
        m.add_geojson(in_geojson, layer_name="Cable lines")
        out_str = m.to_html()
        assert "Cable lines" in out_str

    def test_add_heatmap(self):
        """Check heat map"""
        m = leafmap.Map()
        in_csv = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/world_cities.csv"
        m.add_heatmap(
            in_csv,
            latitude="latitude",
            longitude="longitude",
            value="pop_max",
            name="Heat map",
            radius=20,
        )
        out_str = m.to_html()
        assert "Heat map" in out_str

    def test_add_kml(self):
        """Check KML"""
        m = leafmap.Map()
        in_kml = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us_states.kml"
        m.add_kml(in_kml, layer_name="US States KML")
        out_str = m.to_html()
        assert "US States KML" in out_str

    def test_add_legend(self):
        """Check legend"""
        m = leafmap.Map()
        url = (
            "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms?"
        )
        m.add_wms_layer(
            url,
            layers="NLCD_2016_Land_Cover_L48",
            name="NLCD 2016 CONUS Land Cover",
            format="image/png",
            transparent=True,
        )
        m.add_legend(builtin_legend="NLCD")
        out_str = m.to_html()
        assert "NLCD" in out_str

    # def test_add_marker_cluster(self):
    #     """Check marker cluster"""
    #     with self.assertRaises(NotImplementedError):
    #         m = leafmap.Map()
    #         m.add_marker_cluster()
    #         out_str = m.to_html()
    #         assert "Marker Cluster" in out_str

    def test_add_minimap(self):
        """Check minimap"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            m.add_minimap()
            out_str = m.to_html()
            assert "150px" in out_str

    def test_add_osm_from_address(self):
        """Check OSM data from address"""
        m = leafmap.Map()
        m.add_osm_from_address(
            address="New York City",
            tags={"amenity": "bar"},
            dist=1500,
            layer_name="NYC bars",
        )
        out_str = m.to_html()
        assert "NYC bars" in out_str

    def test_add_osm_from_bbox(self):
        """Check OSM data from bbox"""
        m = leafmap.Map()
        north, south, east, west = 40.7551, 40.7454, -73.9738, -73.9965
        m.add_osm_from_bbox(
            north, south, east, west, tags={"amenity": "bar"}, layer_name="NYC bars"
        )
        out_str = m.to_html()
        assert "NYC bars" in out_str

    def test_add_osm_from_geocode(self):
        """Check OSM data from geocode"""
        m = leafmap.Map()
        m.add_osm_from_geocode("New York City", layer_name="NYC")
        out_str = m.to_html()
        assert "NYC" in out_str

    # def test_add_osm_from_place(self):
    #     """Check OSM data from place"""
    #     m = leafmap.Map()
    #     place = "Bunker Hill, Los Angeles, California"
    #     tags = {"building": True}
    #     m.add_osm_from_place(place, tags, layer_name="Los Angeles, CA")
    #     out_str = m.to_html()
    #     assert "Los Angeles, CA" in out_str

    def test_add_osm_from_point(self):
        """Check OSM data from point"""
        m = leafmap.Map()
        m.add_osm_from_point(
            center_point=(46.7808, -96.0156),
            tags={"natural": "water"},
            dist=10000,
            layer_name="Lakes",
        )
        out_str = m.to_html()
        assert "Lakes" in out_str

    def test_add_osm_from_polygon(self):
        """Check OSM data from polygon"""
        from shapely.geometry import Polygon

        m = leafmap.Map()
        polygon = Polygon(
            [
                [-73.996784, 40.725046],
                [-73.996784, 40.734282],
                [-73.983052, 40.734282],
                [-73.983052, 40.725046],
                [-73.996784, 40.725046],
            ]
        )
        tags = {"building": True}
        m.add_osm_from_polygon(polygon, tags, layer_name="NYC Buildings")
        out_str = m.to_html()
        assert "NYC Buildings" in out_str

    def test_add_osm_from_view(self):
        """Check OSM data from view"""
        m = leafmap.Map()
        m.add_osm_from_view(tags={"building": True}, layer_name="NYC buildings")
        out_str = m.to_html()
        assert "NYC buildings" not in out_str

    def test_add_planet_by_month(self):
        """Check Planet monthly imagery"""
        m = leafmap.Map()
        m.add_planet_by_month(year=2020, month=8)
        out_str = m.to_html()
        assert "Planet_2020_08" in out_str

    def test_add_planet_by_quarter(self):
        """Check Planet quarterly imagery"""
        m = leafmap.Map()
        m.add_planet_by_quarter(year=2019, quarter=2)
        out_str = m.to_html()
        assert "Planet_2019_q2" in out_str

    def test_add_point_layer(self):
        """Check adding point layer"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            url = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us_cities.geojson"
            m.add_point_layer(url, popup=["name", "pop_max"], layer_name="US Cities")
            out_str = m.to_html()
            assert "US Cities" in out_str

    # def test_add_raster(self):
    #     """Check loading raster data"""
    #     with self.assertRaises(NotImplementedError):
    #         m = leafmap.Map()
    #         landsat_url = "https://drive.google.com/file/d/1vRkAWQYsLWCi6vcTMk8vLxoXMFbdMFn8/view?usp=sharing"
    #         leafmap.download_from_gdrive(landsat_url, "dem.tif", unzip=False)
    #         m.add_raster("dem.tif", colormap="terrain", layer_name="DEM")
    #         out_str = m.to_html()
    #         assert "DEM" in out_str

    # def test_add_shp(self):
    #     """Check adding shapefile"""
    #     m = leafmap.Map()
    #     in_shp = (
    #         "https://github.com/giswqs/leafmap/raw/master/examples/data/countries.zip"
    #     )
    #     m.add_shp(in_shp, layer_name="Countries")
    #     out_str = m.to_html()
    #     assert "Countries" in out_str

    def test_add_stac_layer(self):
        """Check adding STAC layer"""
        m = leafmap.Map()
        url = "https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json"
        m.add_stac_layer(url, bands=["B3", "B2", "B1"], name="False color")
        out_str = m.to_html()
        assert "False color" in out_str

    def test_add_tile_layer(self):
        """Check adding tile layer"""
        m = leafmap.Map()
        m.add_tile_layer(
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            name="Google Satellite",
            attribution="Google",
        )
        out_str = m.to_html()
        assert "Google Satellite" in out_str

    def test_add_time_slider(self):
        """Check adding time slider"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            layers_dict = leafmap.planet_quarterly_tiles()
            m.add_time_slider(layers_dict, time_interval=1)
            out_str = m.to_html()
            assert "Planet_2019_q2" in out_str

    def test_add_vector(self):
        """Check adding vector"""
        m = leafmap.Map()
        url = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/countries.geojson"
        m.add_vector(
            url,
            layer_name="Countries",
            fill_colors=["red", "yellow", "green", "orange"],
        )
        out_str = m.to_html()
        assert "Countries" in out_str

    def test_add_vector_tile_layer(self):
        """Check adding vector tile layer"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            url = "https://tile.nextzen.org/tilezen/vector/v1/512/all/{z}/{x}/{y}.mvt?api_key=gCZXZglvRQa6sB2z7JzL1w"
            attribution = "Nextzen"
            m.add_vector_tile_layer(url, attribution)
            out_str = m.to_html()
            assert "Nextzen" in out_str

    def test_add_wms_layer(self):
        """Check adding WMS layer"""
        m = leafmap.Map()
        naip_url = "https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?"
        m.add_wms_layer(
            url=naip_url,
            layers="0",
            name="NAIP Imagery",
            format="image/png",
            shown=True,
        )
        out_str = m.to_html()
        assert "NAIP Imagery" in out_str

    def test_add_xy_data(self):
        """Check adding xy data"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            in_csv = "https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv"
            m.add_xy_data(
                in_csv, x="longitude", y="latitude", layer_name="World Cities"
            )
            out_str = m.to_html()
            assert "World Cities" in out_str

    def test_add_points_from_xy(self):
        "Check adding point data"
        m = leafmap.Map()
        in_csv = (
            "https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv"
        )
        m.add_points_from_xy(
            in_csv, x="longitude", y="latitude", layer_name="World Cities"
        )
        out_str = m.to_html()
        assert "World Cities" in out_str

    def test_basemap_demo(self):
        """Check basemap demo"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            m.basemap_demo()
            out_str = m.to_html()
            assert "Basemaps" in out_str

    def test_find_layer(self):
        """Check finding layer"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            self.assertIsNone(m.find_layer("HYBRID"))
            self.assertIsNotNone(m.find_layer("OpenStreetMap"))

    def test_find_layer_index(self):
        with self.assertRaises(NotImplementedError):
            """Check finding layer index"""
            m = leafmap.Map()
            self.assertEqual(m.find_layer_index("OpenStreetMap"), 0)

    def test_get_layer_names(self):
        """Check getting layer names"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            assert "OpenStreetMap" in m.get_layer_names()

    def test_get_scale(self):
        """Check getting scale"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            self.assertEqual(m.get_scale(), 39135.76)

    def test_image_overlay(self):
        """Check image overlay"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            url = "https://www.mrlc.gov/sites/default/files/NLCD_Colour_Classification_Update.jpg"
            bounds = [(28, -128), (35, -123)]
            m.image_overlay(url=url, bounds=bounds, name="NLCD legend")
            out_str = m.to_html()
            assert "NLCD legend" in out_str

    def test_layer_opacity(self):
        """Check layer opacity"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            m.layer_opacity("OpenStreetMap", 0.5)
            layer = m.find_layer("OpenStreetMap")
            self.assertEqual(layer.opacity, 0.5)

    def test_set_center(self):
        """Check set map center"""
        m = leafmap.Map()
        m.set_center(lon=100, lat=40)
        with self.assertRaises(AttributeError):
            m.center

    def test_to_html(self):
        """Check map to html"""
        m = leafmap.Map()
        out_str = m.to_html()
        assert "OpenStreetMap" in out_str

    def test_to_image(self):
        """Check map to image"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            out_file = os.path.abspath("map.png")
            m.to_image(out_file)
            self.assertTrue(os.path.exists(out_file))

    def test_toolbar_reset(self):
        """Check toolbar reset"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            m.toolbar_reset()
            toolbar_grid = m.toolbar
            for tool in toolbar_grid.children:
                self.assertFalse(tool.value)

    def test_video_overlay(self):
        """Check video overlay"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.Map()
            url = "https://www.mapbox.com/bites/00188/patricia_nasa.webm"
            bounds = [(13, -130), (32, -100)]
            m.video_overlay(url=url, bounds=bounds, name="Video")
            out_str = m.to_html()
            assert "Video" in out_str

    def test_zoom_to_bounds(self):
        """Check zoom to bounds"""
        m = leafmap.Map()
        bounds = [13, -130, 32, -100]
        m.zoom_to_bounds(bounds)
        out_str = m.to_html()
        assert "OpenStreetMap" in out_str

    def test_zoom_to_gdf(self):
        """Check zoom to GeoDataFrame"""
        m = leafmap.Map()
        gdf = gpd.read_file(
            "https://github.com/giswqs/leafmap/raw/master/examples/data/cable_geo.geojson"
        )
        m.zoom_to_gdf(gdf)
        out_str = m.to_html()
        assert "OpenStreetMap" in out_str

    def test_leafmap_split_map(self):
        """Check split-panel map"""
        with self.assertRaises(NotImplementedError):
            m = leafmap.split_map(left_layer="ROADMAP", right_layer="HYBRID")
            out_str = m.to_html()
            assert "OpenStreetMap" in out_str

    def test_linked_maps(self):
        """Check linked maps"""
        with self.assertRaises(NotImplementedError):
            layers = ["ROADMAP", "HYBRID"]
            m = leafmap.linked_maps(rows=1, cols=2, height="400px", layers=layers)

            self.assertEqual(m.n_rows, 1)
            self.assertEqual(m.n_columns, 2)


if __name__ == "__main__":
    unittest.main()
