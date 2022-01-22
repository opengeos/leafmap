# Changelog

## v0.7.3 - January 21, 2022

**New Features**:

-   Added search control GUI [#182](https://github.com/giswqs/leafmap/issues/182) [#183](https://github.com/giswqs/leafmap/pull/183)
-   Added COG creation [#176](https://github.com/giswqs/leafmap/issues/176)

**Improvement**

-   Removed COG mosaic function #180
-   Updated binder env

## v0.7.2 - January 11, 2022

**New Features**:

-   Added GUI for loading COG/STAC [#164](https://github.com/giswqs/leafmap/issues/164)
-   Added ROI to GeoJSON function [#170](https://github.com/giswqs/leafmap/issues/170)
-   Added add_geojson for plotly [#163](https://github.com/giswqs/leafmap/issues/163) [#167](https://github.com/giswqs/leafmap/pull/167)

## v0.7.1 - January 3, 2022

**New Features**:

-   Added plotly toolbar GUI [#160](https://github.com/giswqs/leafmap/issues/160)
-   Added layer control [#160](https://github.com/giswqs/leafmap/issues/160)
-   Added Inspector support for local tile [#162](https://github.com/giswqs/leafmap/issues/162)
-   Added add_gdf for plotly [#163](https://github.com/giswqs/leafmap/issues/163)

**Improvement**

-   Improved COG visualization [#161](https://github.com/giswqs/leafmap/issues/161)
-   Fixed citation bug [#165](https://github.com/giswqs/leafmap/pull/165)

## v0.7.0 - December 29, 2021

**New Features**:

-   Added Planetary Computer STAC support [#137](https://github.com/giswqs/leafmap/issues/137)
-   Added plotly backend [#109](https://github.com/giswqs/leafmap/issues/109)
-   Added Inspector tool [#158](https://github.com/giswqs/leafmap/pull/158)
-   Added plotly COG STAC support [#109](https://github.com/giswqs/leafmap/issues/109)
-   Added plotly planet imagery support [#109](https://github.com/giswqs/leafmap/issues/109)
-   Added plotly toolbar [#160](https://github.com/giswqs/leafmap/issues/160)
-   Added geojson_to_df and geom_type functions

**Improvement**

-   Removed pangeo broken binder links
-   Improved kepler config options [#150](https://github.com/giswqs/leafmap/discussions/150)
-   Improved stac tile function [#137](https://github.com/giswqs/leafmap/issues/156)
-   Updated STAC notebook example [#156](https://github.com/giswqs/leafmap/issues/156)

## v0.6.1 - December 23, 2021

**New Features**:

-   Added image overlay functionality [#136](https://github.com/giswqs/leafmap/issues/136)
-   Added marker cluster function [#138](https://github.com/giswqs/leafmap/issues/138)
-   Added locate control to folium
-   Added cesium_to_streamlit function [#139](https://github.com/giswqs/leafmap/issues/139)
-   Added add_points_from_xy function [#138](https://github.com/giswqs/leafmap/issues/138)
-   Added circle markers function [#140](https://github.com/giswqs/leafmap/issues/143)

**Improvement**

-   Added localtileserver to env.yml
-   Fixed gdf style callback bug [#119](https://github.com/giswqs/leafmap/issues/119)
-   Added ts_inspector docstring [#147](https://github.com/giswqs/leafmap/discussions/147)
-   Improved streamlit download button

## v0.6.0 - November 27, 2021

**New Features**:

-   Added add_marker function
-   Added save_data function
-   Added support for local tile [#129](https://github.com/giswqs/leafmap/issues/129)
-   Added open raster GUI [#129](https://github.com/giswqs/leafmap/issues/129)
-   Added zoom to tile [#129](https://github.com/giswqs/leafmap/issues/129)

## v0.5.5 - November 9, 2021

**New Features**:

-   Added YouthMappers workshop [notebook](https://leafmap.org/workshops/YouthMappers_2021/)

**Improvement**

-   Fixed `add_legend` bug
-   Changed default `max_zoom` to 24

## v0.5.4 - November 2, 2021

**New Features**:

-   Added search basemaps GUI [#93](https://github.com/giswqs/leafmap/issues/93)
-   Added get wms layers function
-   Made streamlit map width reponsive [#126](https://github.com/giswqs/leafmap/issues/126)
-   Added function read file from url
-   Added streamlit download button
-   Added SIGSPATIAL workshop notebook

**Improvement**

-   Fixed layer attribution error [#93](https://github.com/giswqs/leafmap/issues/93)
-   Fixed open vector bug [#124](https://github.com/giswqs/leafmap/discussions/124)
-   Improved streamlit support

## v0.5.3 - October 17, 2021

**New Features**:

-   Added support for US Census data with hundreds of WMS layers [#123](https://github.com/giswqs/leafmap/issues/123)

## v0.5.2 - October 17, 2021

**Improvement**

-   Fixed pydeck import error

## v0.5.1 - October 17, 2021

**New Features**:

-   Added support for pydeck [#122](https://github.com/giswqs/leafmap/issues/122)
-   Added streamlit support for heremap [#118](https://github.com/giswqs/leafmap/issues/118)
-   Added create_colormap function

**Improvement**

-   Added optional postgis port param [#144](https://github.com/giswqs/leafmap/pull/114)
-   Added STAC time slider example to notebook [#177](https://github.com/giswqs/leafmap/pull/117)
-   Fixed geojson style callback bug [#119](https://github.com/giswqs/leafmap/issues/119)
-   Updated foss4g notebook
-   Fixed planet imagery bug
-   Improved vector to geojson
-   Added streamlit app link to docs

## v0.4.3 - September 17, 2021

**New Features**:

-   Added `sandbox_path` option allowing users to restrict Voila app access to system directories [#113](https://github.com/giswqs/leafmap/issues/113)

## v0.4.2 - September 10, 2021

**New Features**:

-   Changed default plotting backend on Colab from folium to ipyleaflet [#112](https://github.com/giswqs/leafmap/issues/112)
-   Added streamlit support [#96](https://github.com/giswqs/leafmap/issues/96)
-   Added support for xyzservices provider [#92](https://github.com/giswqs/leafmap/issues/92)
-   Added a basemap gallery [#91](https://github.com/giswqs/leafmap/issues/91)

**Improvement**

-   Fixed linked maps bug
-   Improved folium basemaps [#91](https://github.com/giswqs/leafmap/issues/91)

## v0.4.1 - August 4, 2021

**New Features**:

-   Added 200+ basemaps from xyzservices [#91](https://github.com/giswqs/leafmap/issues/91)

**Improvement**

-   Fixed typo [#90](https://github.com/giswqs/leafmap/pull/90)
-   Added kepler module to mkdocs
-   Removed support for Python 3.6 due to xyzservices

## v0.4.0 - July 28, 2021

**New Features**:

-   Added kepler.gl plotting backend [#88](https://github.com/giswqs/leafmap/issues/88)
-   Added keplergl sample data [#88](https://github.com/giswqs/leafmap/issues/88)
-   Added keplergl sample html [#88](https://github.com/giswqs/leafmap/issues/88)

**Improvement**

-   Added CITATIONS.cff

## v0.3.5 - July 26, 2021

**New Features**:

-   Added kepler.gl plotting backend [#88](https://github.com/giswqs/leafmap/issues/88)

**Improvement**

-   Added unittest for toolbar module [#83](https://github.com/giswqs/leafmap/issues/83)
-   Updated paper.md

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
