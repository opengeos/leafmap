# Changelog

## v0.19.0 - Apr 10, 2023

**New Features**

-   Added GUI for custom STAC catalogs (#413)

## v0.18.10 - Apr 6, 2023

**Improvement**

-   Dropped support for Python 3.7 (#410)
-   Fixed create_timelapse bug (#410)

## v0.18.9 - Apr 6, 2023

**Improvement**

-   Set toolbar widget visibility with env variables (#407)
-   Moved repo to opengeos org and updated repo URL (#408)
-   Removed ipykernel
-   Updated docker image url

## v0.18.8 - Mar 26, 2023

**Improvement**

-   Removed ipykernel import ([#402](https://github.com/opengeos/leafmap/pull/402))

## v0.18.7 - Mar 24, 2023

**New Features**

-   Added support for creating satellite timelapse animations (#398)

## v0.18.6 - Mar 22, 2023

**Improvement**

-   Fixed ipywidgets comm error ([#396](https://github.com/opengeos/leafmap/pull/396))

## v0.18.5 - Mar 19, 2023

**Improvement**

-   Updated mkdocs-jupyter execute_ignore
-   Removed Google Search from menu
-   Set mkdocs material version lower bound ([#394](https://github.com/opengeos/leafmap/pull/394))
-   Added mkdocs built-in search ([#393](https://github.com/opengeos/leafmap/pull/393))
-   Fixed CodeQL warnings ([#392](https://github.com/opengeos/leafmap/pull/392))
-   Fixed notebook 71 error

## v0.18.4 - Mar 15, 2023

**New Features**

-   Added support for loading raster datasets from AWS S3 buckets ([#391](https://github.com/opengeos/leafmap/pull/391))
-   Added `zonal_stats` function ([#389](https://github.com/opengeos/leafmap/pull/389))
-   Added `disjoint` function for filtering vector data ([#388](https://github.com/opengeos/leafmap/pull/388))

**Improvement**

-   Updated installation instructions
-   Updated Dockerfile

## v0.18.3 - Mar 6, 2023

**New Features**

-   Added docker image ([#387](https://github.com/opengeos/leafmap/pull/387))

**Improvement**

-   Cleaned up notebooks ([#386](https://github.com/opengeos/leafmap/pull/386))

## v0.18.2 - Mar 5, 2023

**New Features**

-   Added filter_date and filter_bounds functions ([#385](https://github.com/opengeos/leafmap/pull/385))
-   Added Google Search for docs ([#383](https://github.com/opengeos/leafmap/pull/383))
-   Added SageMaker Studio Lab and Planetary Computer badges ([#380](https://github.com/opengeos/leafmap/pull/380))

**Improvement**

-   Cleaned up notebooks ([#384](https://github.com/opengeos/leafmap/pull/384))
-   Added missing dependencies to notebook ([#382](https://github.com/opengeos/leafmap/pull/382))
-   Added default_vis option to cog_tile ([#378](https://github.com/opengeos/leafmap/pull/378))

## v0.18.1 - Mar 1, 2023

**Improvement**

-   Deprecated ipyleaflet add_layer and add_control methods ([#377](https://github.com/opengeos/leafmap/pull/377))
-   Fixed add geojson style bug ([#376](https://github.com/opengeos/leafmap/pull/376))

## v0.18.0 - Mar 1, 2023

**New Features**

-   Added support for searching OpenAerialMap imagery ([#375](https://github.com/opengeos/leafmap/pull/375))
-   Added Google Search for docs ([#374](https://github.com/opengeos/leafmap/pull/374))
-   Added leafmap logo ([#372](https://github.com/opengeos/leafmap/pull/372))

**Improvement**

-   Fixed datapane bug ([#373](https://github.com/opengeos/leafmap/pull/373))
-   Pin osmnx version lower bound ([#369](https://github.com/opengeos/leafmap/pull/368))

## v0.17.1 - Feb 16, 2023

**New Features**

-   Added support for visualizing Maxar Open Data ([#367](https://github.com/opengeos/leafmap/pull/367))

## v0.17.0 - Feb 15, 2023

**New Features**

-   Added support for gradio for developing interactive web apps ([#364](https://github.com/opengeos/leafmap/pull/364))

## v0.16.1 - Feb 7, 2023

**New Features**

-   Added support for visualizing raster datasets in AWS SageMaker ([#359](https://github.com/opengeos/leafmap/pull/359))

## v0.16.0 - Feb 3, 2023

**New Features**

-   Added STAC API Browser GUI ([#347](https://github.com/opengeos/leafmap/pull/347), [#354](https://github.com/opengeos/leafmap/pull/354))
-   Added support for vector tiles ([#352](https://github.com/opengeos/leafmap/pull/352))
-   Added support for editing an empty vector dataset interactively ([#353](https://github.com/opengeos/leafmap/pull/353))
-   Added vector-to-raster function ([#343](https://github.com/opengeos/leafmap/pull/343))

**Improvement**

-   Updated 04_cog_mosaic.ipynb ([#342](https://github.com/opengeos/leafmap/pull/342))
-   Fixed tar file bug CVE-2007-4559 ([#350](https://github.com/opengeos/leafmap/pull/350))
-   Fixed folium add basemap bug

## v0.15.0 - Dec 23, 2022

**New Features**

-   Added support for ArcGIS Pro ([#334](https://github.com/opengeos/leafmap/pull/334))

## v0.14.2 - Dec 22, 2022

**New Features**

-   Added colorbar support for folium ([#330](https://github.com/opengeos/leafmap/pull/330))

**Improvement**

-   Updated vector_to_gif notebook

## v0.14.1 - Dec 11, 2022

**New Features**

-   Added support for vector_to_gif ([#323](https://github.com/opengeos/leafmap/pull/323))

**Improvement**

-   Updated TiTiler endpoint ([#325](https://github.com/opengeos/leafmap/pull/325))
-   Fixed `stac_pixel_value()` bug

## v0.14.0 - Nov 27, 2022

**New Features**

-   Added functions for creating legends and adding widgets to the map ([#321](https://github.com/opengeos/leafmap/pull/321))
-   New functions include `create_legend()`, `add_legend()`, `add_text()`, `add_image()`, `add_html()`, and `add_widget()`
-   Added two notebook examples for using newly added functions
-   Split-map now supports adding multiple legends
-   Added ESA World Cover 2021 basemaps

## v0.13.3 - Nov 25, 2022

**New Features**

-   Added function for downloading files using pyodide ([#320](https://github.com/opengeos/leafmap/pull/320))
-   Added JupyterLite badge to notebook examples ([#319](https://github.com/opengeos/leafmap/pull/319))
-   Added gdown and JupyterLite badge to docs ([#318](https://github.com/opengeos/leafmap/pull/318))

## v0.13.1 - Nov 24, 2022

**New Features**

-   Added support for JupyterLite ([#317](https://github.com/opengeos/leafmap/pull/317))

## v0.13.0 - Nov 23, 2022

**New Features**

-   Added support for JupyterLite ([#316](https://github.com/opengeos/leafmap/pull/316))
-   Added choropleth map legend position option #305 ([#315](https://github.com/opengeos/leafmap/pull/315))
-   Added dark mode and fix bugs ([#312](https://github.com/opengeos/leafmap/pull/312))
-   Added vector_area and image_filesize functions ([#309](https://github.com/opengeos/leafmap/pull/309))
-   Added bbox to gdf and polygon func
-   Added raster support for SageMaker AWS ([#307](https://github.com/opengeos/leafmap/pull/307))

**Improvement**

-   Fixed kml bug ([#308](https://github.com/opengeos/leafmap/pull/308))

## v0.12.1 - Nov 10, 2022

**New Features**

-   Added add_mask_to_image() function ([#306](https://github.com/opengeos/leafmap/pull/306))

## v0.12.0 - Nov 8, 2022

**New Features**

-   Added bokeh as a new plotting backend [#298](https://github.com/opengeos/leafmap/issues/298) [#301](https://github.com/opengeos/leafmap/pull/301)
-   The bokeh backend supports loading COG, STAC, local rasters, GeoJSON, Shapefile, etc.
-   Added GeoJSON support for split-view map [#291](https://github.com/opengeos/leafmap/issues/291) [#300](https://github.com/opengeos/leafmap/pull/300)

**Improvement**

-   Fixed numpy to cog crs bug
-   Improved cog rescale param and docs [#284](https://github.com/opengeos/leafmap/issues/284) [#299](https://github.com/opengeos/leafmap/pull/299)

## v0.11.3 - Nov 3, 2022

**Improvement**

-   Fixed split map bug (layer visualization args)
-   Improved linked maps to support COG and local GeoTIFFs

## v0.11.2 - Nov 2, 2022

**Improvement**

-   Improved the mosaic() function to support creating COG
-   Improved the download_file() function to support downloading and extracting files

## v0.11.1 - Nov 2, 2022

**New Features**:

-   Added find_files() function for searching files recursively in a directory

**Improvement**

-   Improved the mosaic() function

## v0.11.0 - Nov 2, 2022

**New Features**:

-   Improved support for creating split-panel map [#297](https://github.com/opengeos/leafmap/pull/297)
-   Split-panel map supports any local or remote raster datasets
-   Added several image functions:
-   `image_center()`
-   `image_bounds()`
-   `image_size()`
-   `image_resolution()`
-   `image_metadata()`
-   `image_projection()`
-   `image_geotransform()`

## v0.10.6 - Oct 31, 2022

**New Features**:

-   Added reproject image function
-   Added download ned notebook tutorial [#285](https://github.com/opengeos/leafmap/pull/285)
-   Added download ned by huc and bbox [#287](https://github.com/opengeos/leafmap/discussions/287) [#289](https://github.com/opengeos/leafmap/pull/289)
-   Added USGS The national map API wrapper [#290](https://github.com/opengeos/leafmap/pull/290)

**Improvement**

-   Added codeql.yml
-   Improved Colab import error message
-   Added Python 3.11 to CI
-   Fixed max zoom bug
-   Improved split control

## v0.10.5 - Sep 7, 2022

**New Features**:

-   Added geometry_bounds() function
-   Added Map.user_roi_bounds() method

**Improvement**

-   Fixed download NED bug

## v0.10.4 - Sep 7, 2022

**New Features**:

-   Added download_ned and mosaic image functions
-   Added html_to_streamlit function

**Improvement**

-   Updated Map.to_streamlit()

## v0.10.3 - Jul 22, 2022

**New Features**:

-   Added lidar tutorial [#276](https://github.com/opengeos/leafmap/pull/276)
-   Added add_crs function [#275](https://github.com/opengeos/leafmap/pull/275)
-   Added more lidar functions
-   Added get_direct_url function

**Improvement**

-   Improved add_raster function [#275](https://github.com/opengeos/leafmap/pull/275)

## v0.10.2 - Jul 15, 2022

**New Features**:

-   Added csv_to_vector function [#270](https://github.com/opengeos/leafmap/pull/270)

**Improvement**

-   Pin ipyleaflet version > 0.17.0
-   Updated sample datasets
-   Fixed json import error

## v0.10.1 - Jul 11, 2022

**New Features**:

-   Added github_raw_url function [#267](https://github.com/opengeos/leafmap/pull/267)

**Improvement**

-   Pin ipyleaflet version for Colab [#269](https://github.com/opengeos/leafmap/pull/269)
-   Improved add data methods to accept HTTP URL [#262](https://github.com/opengeos/leafmap/issues/262)
-   Changed parameter name to layer_name [#262](https://github.com/opengeos/leafmap/issues/262)
-   Improved download_file function

## v0.10.0 - Jul 8, 2022

**New Features**:

-   Added support for changing geojson layer opacity [#265](https://github.com/opengeos/leafmap/pull/265)

**Improvement**

-   Updated plot raster 3d function [#264](https://github.com/opengeos/leafmap/pull/264)
-   Fixed clip image bug

## v0.9.5 - Jun 26, 2022

**Improvement**

-   Made mapclassify optional [#257](https://github.com/opengeos/leafmap/pull/257)

## v0.9.6 - Jul 1, 2022

**New Features**:

-   Added plotting raster in 3D [#259](https://github.com/opengeos/leafmap/pull/259)
-   Added scooby report for reporting issues [#260](https://github.com/opengeos/leafmap/pull/260)

## v0.9.5 - Jun 26, 2022

**Improvement**

-   Made mapclassify optional [#257](https://github.com/opengeos/leafmap/pull/257)
-   Improved wording on the home page [#256](https://github.com/opengeos/leafmap/pull/256)
-   Fixed typos [#251](https://github.com/opengeos/leafmap/pull/251)

## v0.9.4 - Jun 7, 2022

**Improvement**

-   Added ESA WorldCover and USGS NAIP basemaps [#250](https://github.com/opengeos/leafmap/pull/250)
-   Fixed bugs in add_points_from_xy functions [#249](https://github.com/opengeos/leafmap/pull/249)
-   Fixed link redirects [#247](https://github.com/opengeos/leafmap/pull/247)
-   Added check_cmap function

## v0.9.3 - Apr 27, 2022

**Improvement**

-   Fixed stac stats bug [#245](https://github.com/opengeos/leafmap/issues/245)

## v0.9.2 - Apr 27, 2022

**New Features**:

-   Added support for creating interactive choropleth maps with a variety of classification schemes [#235](https://github.com/opengeos/leafmap/issues/235) [#239](https://github.com/opengeos/leafmap/pull/239) [#240](https://github.com/opengeos/leafmap/pull/240)
-   Added tooltip and popup for GeoJSON
-   Added examples module [#238](https://github.com/opengeos/leafmap/pull/238)

**Improvement**

-   Fixed add velocity bug [#234](https://github.com/opengeos/leafmap/issues/234)
-   Added ability to handle levels and times in netCDF files [#232](https://github.com/opengeos/leafmap/pull/232)

## v0.9.1 - Apr 2, 2022

**Improvement**

-   Fixed heremap import error

## v0.9.0 - Apr 2, 2022

**Improvement**

-   Reduced number of dependencies, making plotting backends optional except ipyleaflet and folium [#230](https://github.com/opengeos/leafmap/pull/230)
-   Updated clip image notebook
-   Updated docs

## v0.8.6 - Mar 22, 2022

**Improvement**

-   Renamed basemaps and updated notebooks [#228](https://github.com/opengeos/leafmap/pull/228)

## v0.8.5 - Mar 19, 2022

**New Features**:

-   Added support for NetCDF data [#127](https://github.com/opengeos/leafmap/issues/127) [#226](https://github.com/opengeos/leafmap/pull/226)
-   Converting NetCDF to GeoTIFF
-   Adding velocity map
-   Added clip_image function [#108](https://github.com/opengeos/leafmap/issues/108) [#225](https://github.com/opengeos/leafmap/pull/225)

**Improvement**

-   Added optional dependencies (netcdf4 and rioxarray) to setup.py

## v0.8.4 - Mar 15, 2022

**New Features**:

-   Added streamlit folium bidirectional functionality [#223](https://github.com/opengeos/leafmap/pull/223)
-   Added marker icon options for marker cluster [#222](https://github.com/opengeos/leafmap/pull/222)
-   Added folium search control

**Improvement**

-   Renamed data files [#221](https://github.com/opengeos/leafmap/pull/221)
-   Fixed circle marker bug

## v0.8.3 - Mar 12, 2022

**New Features**:

-   Added split map for folium and streamlit [#218](https://github.com/opengeos/leafmap/pull/218)
-   Added eye dome lighting for lidar data [#212](https://github.com/opengeos/leafmap/issues/212)
-   Added ipygany and panel 3D plotting backends for LiDAR data [#212](https://github.com/opengeos/leafmap/issues/212)

**Improvement**

-   Updated binder env

## v0.8.2 - Mar 2, 2022

**Improvement**

-   Added missing requirements.txt to MANIFEST

## v0.8.1 - Mar 2, 2022

**New Features**:

-   Added support for visualizing LiDAR data in 3D [#212](https://github.com/opengeos/leafmap/issues/212)
-   Added support for downloading Googld Drive folder [#212](https://github.com/opengeos/leafmap/issues/212)

**Improvement**

-   Improved COG STAC palette
-   Fixed getattr bug [#207](https://github.com/opengeos/leafmap/pull/207)

## v0.8.0 - Feb 25, 2022

**New Features**:

-   Added STAC search and visualization GUI [#181](https://github.com/opengeos/leafmap/issues/181)
-   Added support for STAC MosaicJSON [#206](https://github.com/opengeos/leafmap/issues/206)
-   Added encoding param for reading vector [#208](https://github.com/opengeos/leafmap/pull/208)

**Improvement**

-   Use getattr instead of eval [#207](https://github.com/opengeos/leafmap/pull/207)

## v0.7.8 - Feb 22, 2022

**New Features**:

-   Added numpy to cog [#200](https://github.com/opengeos/leafmap/issues/200)

**Improvement**

-   Fixed LGTM alerts

## v0.7.7 - Feb 15, 2022

**New Features**:

-   Added raster support for JupyterHub
-   Added new function add_raster

**Improvement**

-   Fixed Colab plotly bug [#199](https://github.com/opengeos/leafmap/issues/199)

## v0.7.6 - Feb 4, 2022

**New Features**:

-   Added support for editing vector data [#178](https://github.com/opengeos/leafmap/discussions/178) [#179](https://github.com/opengeos/leafmap/issues/179)

**Improvement**

-   Fixed Colab widgets.jslink bug
-   Updated STAC notebooks
-   Changed STAC items to item
-   Added sample vector data

## v0.7.5 - Jan 27, 2022

**New Features**:

-   Added vector creation GUI [#179](https://github.com/opengeos/leafmap/issues/179) [#194](https://github.com/opengeos/leafmap/pull/194)

## v0.7.4 - Jan 24, 2022

**New Features**:

-   Added attribute table GUI [#179](https://github.com/opengeos/leafmap/issues/179)

**Improvement**

-   Improved add_labels function [#188](https://github.com/opengeos/leafmap/discussions/188)
-   Improved GitHub workflows [#192](https://github.com/opengeos/leafmap/pull/192)
-   Improved add_raster function [#191](https://github.com/opengeos/leafmap/pull/191)
-   Removed nominatim URL from Search Control [#182](https://github.com/opengeos/leafmap/issues/182)
-   Fixed search control bug [#183](https://github.com/opengeos/leafmap/pull/183)

## v0.7.3 - Jan 21, 2022

**New Features**:

-   Added search control GUI [#182](https://github.com/opengeos/leafmap/issues/182) [#183](https://github.com/opengeos/leafmap/pull/183)
-   Added COG creation [#176](https://github.com/opengeos/leafmap/issues/176)

**Improvement**

-   Removed COG mosaic function #180
-   Updated binder env

## v0.7.2 - Jan 11, 2022

**New Features**:

-   Added GUI for loading COG/STAC [#164](https://github.com/opengeos/leafmap/issues/164)
-   Added ROI to GeoJSON function [#170](https://github.com/opengeos/leafmap/issues/170)
-   Added add_geojson for plotly [#163](https://github.com/opengeos/leafmap/issues/163) [#167](https://github.com/opengeos/leafmap/pull/167)

## v0.7.1 - Jan 3, 2022

**New Features**:

-   Added plotly toolbar GUI [#160](https://github.com/opengeos/leafmap/issues/160)
-   Added layer control [#160](https://github.com/opengeos/leafmap/issues/160)
-   Added Inspector support for local tile [#162](https://github.com/opengeos/leafmap/issues/162)
-   Added add_gdf for plotly [#163](https://github.com/opengeos/leafmap/issues/163)

**Improvement**

-   Improved COG visualization [#161](https://github.com/opengeos/leafmap/issues/161)
-   Fixed citation bug [#165](https://github.com/opengeos/leafmap/pull/165)

## v0.7.0 - Dec 29, 2021

**New Features**:

-   Added Planetary Computer STAC support [#137](https://github.com/opengeos/leafmap/issues/137)
-   Added plotly backend [#109](https://github.com/opengeos/leafmap/issues/109)
-   Added Inspector tool [#158](https://github.com/opengeos/leafmap/pull/158)
-   Added plotly COG STAC support [#109](https://github.com/opengeos/leafmap/issues/109)
-   Added plotly planet imagery support [#109](https://github.com/opengeos/leafmap/issues/109)
-   Added plotly toolbar [#160](https://github.com/opengeos/leafmap/issues/160)
-   Added geojson_to_df and geom_type functions

**Improvement**

-   Removed pangeo broken binder links
-   Improved kepler config options [#150](https://github.com/opengeos/leafmap/discussions/150)
-   Improved stac tile function [#137](https://github.com/opengeos/leafmap/issues/156)
-   Updated STAC notebook example [#156](https://github.com/opengeos/leafmap/issues/156)

## v0.6.1 - Dec 23, 2021

**New Features**:

-   Added image overlay functionality [#136](https://github.com/opengeos/leafmap/issues/136)
-   Added marker cluster function [#138](https://github.com/opengeos/leafmap/issues/138)
-   Added locate control to folium
-   Added cesium_to_streamlit function [#139](https://github.com/opengeos/leafmap/issues/139)
-   Added add_points_from_xy function [#138](https://github.com/opengeos/leafmap/issues/138)
-   Added circle markers function [#140](https://github.com/opengeos/leafmap/issues/143)

**Improvement**

-   Added localtileserver to env.yml
-   Fixed gdf style callback bug [#119](https://github.com/opengeos/leafmap/issues/119)
-   Added ts_inspector docstring [#147](https://github.com/opengeos/leafmap/discussions/147)
-   Improved streamlit download button

## v0.6.0 - Nov 27, 2021

**New Features**:

-   Added add_marker function
-   Added save_data function
-   Added support for local tile [#129](https://github.com/opengeos/leafmap/issues/129)
-   Added open raster GUI [#129](https://github.com/opengeos/leafmap/issues/129)
-   Added zoom to tile [#129](https://github.com/opengeos/leafmap/issues/129)

## v0.5.5 - Nov 9, 2021

**New Features**:

-   Added YouthMappers workshop [notebook](https://leafmap.org/workshops/YouthMappers_2021/)

**Improvement**

-   Fixed `add_legend` bug
-   Changed default `max_zoom` to 24

## v0.5.4 - Nov 2, 2021

**New Features**:

-   Added search basemaps GUI [#93](https://github.com/opengeos/leafmap/issues/93)
-   Added get wms layers function
-   Made streamlit map width reponsive [#126](https://github.com/opengeos/leafmap/issues/126)
-   Added function read file from url
-   Added streamlit download button
-   Added SIGSPATIAL workshop notebook

**Improvement**

-   Fixed layer attribution error [#93](https://github.com/opengeos/leafmap/issues/93)
-   Fixed open vector bug [#124](https://github.com/opengeos/leafmap/discussions/124)
-   Improved streamlit support

## v0.5.3 - Oct 17, 2021

**New Features**:

-   Added support for US Census data with hundreds of WMS layers [#123](https://github.com/opengeos/leafmap/issues/123)

## v0.5.2 - Oct 17, 2021

**Improvement**

-   Fixed pydeck import error

## v0.5.1 - Oct 17, 2021

**New Features**:

-   Added support for pydeck [#122](https://github.com/opengeos/leafmap/issues/122)
-   Added streamlit support for heremap [#118](https://github.com/opengeos/leafmap/issues/118)
-   Added create_colormap function

**Improvement**

-   Added optional postgis port param [#144](https://github.com/opengeos/leafmap/pull/114)
-   Added STAC time slider example to notebook [#177](https://github.com/opengeos/leafmap/pull/117)
-   Fixed geojson style callback bug [#119](https://github.com/opengeos/leafmap/issues/119)
-   Updated foss4g notebook
-   Fixed planet imagery bug
-   Improved vector to geojson
-   Added streamlit app link to docs

## v0.4.3 - Sep 17, 2021

**New Features**:

-   Added `sandbox_path` option allowing users to restrict Voila app access to system directories [#113](https://github.com/opengeos/leafmap/issues/113)

## v0.4.2 - Sep 10, 2021

**New Features**:

-   Changed default plotting backend on Colab from folium to ipyleaflet [#112](https://github.com/opengeos/leafmap/issues/112)
-   Added streamlit support [#96](https://github.com/opengeos/leafmap/issues/96)
-   Added support for xyzservices provider [#92](https://github.com/opengeos/leafmap/issues/92)
-   Added a basemap gallery [#91](https://github.com/opengeos/leafmap/issues/91)

**Improvement**

-   Fixed linked maps bug
-   Improved folium basemaps [#91](https://github.com/opengeos/leafmap/issues/91)

## v0.4.1 - Aug 4, 2021

**New Features**:

-   Added 200+ basemaps from xyzservices [#91](https://github.com/opengeos/leafmap/issues/91)

**Improvement**

-   Fixed typo [#90](https://github.com/opengeos/leafmap/pull/90)
-   Added kepler module to mkdocs
-   Removed support for Python 3.6 due to xyzservices

## v0.4.0 - Jul 28, 2021

**New Features**:

-   Added kepler.gl plotting backend [#88](https://github.com/opengeos/leafmap/issues/88)
-   Added keplergl sample data [#88](https://github.com/opengeos/leafmap/issues/88)
-   Added keplergl sample html [#88](https://github.com/opengeos/leafmap/issues/88)

**Improvement**

-   Added CITATIONS.cff

## v0.3.5 - Jul 26, 2021

**New Features**:

-   Added kepler.gl plotting backend [#88](https://github.com/opengeos/leafmap/issues/88)

**Improvement**

-   Added unittest for toolbar module [#83](https://github.com/opengeos/leafmap/issues/83)
-   Updated paper.md

## v0.3.4 - Jul 21, 2021

**New Features**:

-   Added map title function [#84](https://github.com/opengeos/leafmap/issues/84)

**Improvement**

-   Improved add_ahp and add_kml for http
-   Added codespell to docs.yml
-   Made XYZ tiles attribution required [#83](https://github.com/opengeos/leafmap/issues/83)
-   Changed some functions to be private [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added more info about plotting backends [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added text description to notebooks [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added NotImplementedError for foliumap [#83](https://github.com/opengeos/leafmap/issues/83)
-   Fixed typos using codespell [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added Code of Conduct [#83](https://github.com/opengeos/leafmap/issues/83)
-   Made usage page interactive [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added key features notebook [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added plotting backend comparison [#83](https://github.com/opengeos/leafmap/issues/83)
-   Added leafmap and foliumap unittest [#83](https://github.com/opengeos/leafmap/issues/83)
-   Improved JOSS paper [#83](https://github.com/opengeos/leafmap/issues/83)

## v0.3.3 - Jul 8, 2021

**New Features**:

-   Added troubleshooting section [#76](https://github.com/opengeos/leafmap/issues/76)
-   Added df_to_geojson function [#75](https://github.com/opengeos/leafmap/issues/75)
-   Added creating heat map from csv [#64](https://github.com/opengeos/leafmap/issues/64)
-   Added cog mosaic from file [#61](https://github.com/opengeos/leafmap/issues/61)
-   Added colormap notebook [#60](https://github.com/opengeos/leafmap/issues/60)

**Improvement**

-   Changed COG and STAC function names [#61](https://github.com/opengeos/leafmap/issues/61)
-   Updated colormap example [#60](https://github.com/opengeos/leafmap/issues/60)

## v0.3.2 - Jun 22, 2021

**New Features**:

-   Added time slider [#42](https://github.com/opengeos/leafmap/issues/42)
-   Added JOSS manuscript
-   Added unittests

## v0.3.1 - Jun 20, 2021

**New Features**:

-   Added GUI for loading COG [#50](https://github.com/opengeos/leafmap/issues/50)
-   Added methods to add vector data on heremap [#43 ](https://github.com/opengeos/leafmap/pull/43)
-   Added Planet imagery GUI [#9](https://github.com/opengeos/leafmap/commit/2bea287e08886b8d20b96a80364d898237b425bd)

**Improvement**

-   Improved support for folium styles [#47](https://github.com/opengeos/leafmap/discussions/47)
-   Improved save map to image [#37](https://github.com/opengeos/leafmap/issues/37)
-   Updated toolbar icons [#9](https://github.com/opengeos/leafmap/issues/9)
-   Added LGTM
-   Updated installation docs

## v0.3.0 - Jun 14, 2021

**New Features**:

-   Added Planet basemaps GUI [#9](https://github.com/opengeos/leafmap/issues/9)
-   Added open point layer GUI [#29](https://github.com/opengeos/leafmap/issues/29)
-   Improved GUI for opening vector data from http [#33](https://github.com/opengeos/leafmap/issues/33)
-   Added map to html function [#32](https://github.com/opengeos/leafmap/issues/32)
-   Added point layer with popup [#27](https://github.com/opengeos/leafmap/issues/27)
-   Added vector tile layer support [#26](https://github.com/opengeos/leafmap/pull/26)
-   Added HERE map plotting backend [#20](https://github.com/opengeos/leafmap/pull/20)

**Improvement**

-   Allow json file in open data widget
-   Added five notebook tutorials
-   Fixed folium map custom size bug [#21](https://github.com/opengeos/leafmap/issues/21)

## v0.2.0 - Jun 5, 2021

**New Features**:

-   Added handle-draw function [#2](https://github.com/opengeos/leafmap/issues/2)
-   Added split-panel map [#7](https://github.com/opengeos/leafmap/issues/7)
-   Added GeoPandas support [#16](https://github.com/opengeos/leafmap/issues/16)
-   Added support for PostGIS [#15](https://github.com/opengeos/leafmap/issues/15)
-   Added support for downloading OpenStreetMap data [#10](https://github.com/opengeos/leafmap/issues/10) [#12](https://github.com/opengeos/leafmap/issues/12)

**Improvement**

-   Fixed basemap bug [#5](https://github.com/opengeos/leafmap/discussions/5)
-   Fixed output scroll bug [#11](https://github.com/opengeos/leafmap/issues/11)
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
