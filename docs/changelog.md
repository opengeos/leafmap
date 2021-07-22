# Changelog

## v0.3.4 - July 21, 2021

**New Features**:

-   Added map title function [#84](https://github.com/giswqs/leafmap/issues/84)

**Improvement**

-   Improved add_ahp and add_kml for http
-   Added codespell to docs.yml
-   Made XYZ tiles attribution required [#83](https://github.com/giswqs/leafmap/issues/83)
-   Changed some functions to be private [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added more info about plotting backends [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added text description to notebooks [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added NotImplementedError for foliumap [#83](https://github.com/giswqs/leafmap/issues/83)
-   Fixed typos using codespell [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added Code of Conduct [#83](https://github.com/giswqs/leafmap/issues/83)
-   Made usage page interactive [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added key features notebook [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added plotting backend comparison [#83](https://github.com/giswqs/leafmap/issues/83)
-   Added leafmap and foliumap unittest [#83](https://github.com/giswqs/leafmap/issues/83)
-   Improved JOSS paper [#83](https://github.com/giswqs/leafmap/issues/83)

## v0.3.3 - July 8, 2021

**New Features**:

-   Added troubleshooting section [#76](https://github.com/giswqs/leafmap/issues/76)
-   Added pandas_to_geojson function [#75](https://github.com/giswqs/leafmap/issues/75)
-   Added creating heat map from csv [#64](https://github.com/giswqs/leafmap/issues/64)
-   Added cog mosaic from file [#61](https://github.com/giswqs/leafmap/issues/61)
-   Added colormap notebook [#60](https://github.com/giswqs/leafmap/issues/60)

**Improvement**

-   Changed COG and STAC function names [#61](https://github.com/giswqs/leafmap/issues/61)
-   Updated colormap example [#60](https://github.com/giswqs/leafmap/issues/60)

## v0.3.2 - June 22, 2021

**New Features**:

-   Added time slider [#42](https://github.com/giswqs/leafmap/issues/42)
-   Added JOSS manuscript
-   Added unittests

## v0.3.1 - June 20, 2021

**New Features**:

-   Added GUI for loading COG [#50](https://github.com/giswqs/leafmap/issues/50)
-   Added methods to add vector data on heremap [#43 ](https://github.com/giswqs/leafmap/pull/43)
-   Added Planet imagery GUI [#9](https://github.com/giswqs/leafmap/commit/2bea287e08886b8d20b96a80364d898237b425bd)

**Improvement**

-   Improved support for folium styles [#47](https://github.com/giswqs/leafmap/discussions/47)
-   Improved save map to image [#37](https://github.com/giswqs/leafmap/issues/37)
-   Updated toolbar icons [#9](https://github.com/giswqs/leafmap/issues/9)
-   Added LGTM
-   Updated installation docs

## v0.3.0 - June 14, 2021

**New Features**:

-   Added Planet basemaps GUI [#9](https://github.com/giswqs/leafmap/issues/9)
-   Added open point layer GUI [#29](https://github.com/giswqs/leafmap/issues/29)
-   Improved GUI for opening vector data from http [#33](https://github.com/giswqs/leafmap/issues/33)
-   Added map to html function [#32](https://github.com/giswqs/leafmap/issues/32)
-   Added point layer with popup [#27](https://github.com/giswqs/leafmap/issues/27)
-   Added vector tile layer support [#26](https://github.com/giswqs/leafmap/pull/26)
-   Added HERE map plotting backend [#20](https://github.com/giswqs/leafmap/pull/20)

**Improvement**

-   Allow json file in open data widget
-   Added five notebook tutorials
-   Fixed folium map custom size bug [#21](https://github.com/giswqs/leafmap/issues/21)

## v0.2.0 - June 5, 2021

**New Features**:

-   Added handle-draw function [#2](https://github.com/giswqs/leafmap/issues/2)
-   Added split-panel map [#7](https://github.com/giswqs/leafmap/issues/7)
-   Added GeoPandas support [#16](https://github.com/giswqs/leafmap/issues/16)
-   Added support for PostGIS [#15](https://github.com/giswqs/leafmap/issues/15)
-   Added support for downloading OpenStreetMap data [#10](https://github.com/giswqs/leafmap/issues/10) [#12](https://github.com/giswqs/leafmap/issues/12)

**Improvement**

-   Fixed basemap bug [#5](https://github.com/giswqs/leafmap/discussions/5)
-   Fixed output scroll bug [#11](https://github.com/giswqs/leafmap/issues/11)
-   Changed COG and STAC functions to snake_case
-   Added binder badge to notebooks
-   Added binder env
-   Added 15 tutorials
-   Added domain name leafmap.org

## v0.1.0 - May 25, 2021

**New Features**:

-   Create an interactive map with only one-line of code.
-   Select from a variety of basemaps interactively without coding.
-   Add XYZ and WMS tile services to the map.
-   Convert CSV to points and display points as a marker cluster.
-   Add local vector data (e.g., shapefile, GeoJSON, KML) to the map without coding.
-   Add local raster data (e.g., GeoTIFF) to the map without coding.
-   Add Cloud Optimized GeoTIFF (COG) and SpatialTemporal Asset Catalog (STAC) to the map.
-   Add custom legends and colorbars to the map.
-   Perform geospatial analysis using WhiteboxTools and whiteboxgui.
-   Publish interactive maps with only one line of code.
