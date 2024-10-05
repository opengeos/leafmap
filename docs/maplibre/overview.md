# Overview

This page contains examples of using [MapLibre](https://maplibre.org) with Leafmap. Built on top of the [py-maplibregl](https://github.com/eodaGmbH/py-maplibregl) Python package, Leafmap makes it much easier to create stunning 3D maps with MapLibre in just a few lines of code. Some examples are adapted from the [MapLibre documentation](https://maplibre.org/maplibre-gl-js/docs/examples/) and [py-maplibregl examples](https://eodagmbh.github.io/py-maplibregl/examples/every_person_in_manhattan/). Credits to the original authors.

To preview the examples, visit <https://maps.gishub.org>.

## Video tutorials on YouTube

Video tutorials on how to use Leafmap with MapLibre are available on YouTube: <https://bit.ly/maplibre>

[![](https://i.imgur.com/dsxACGG.png)](https://bit.ly/maplibre)

## Display buildings in 3D

Use extrusions to display buildings' height in 3D.

[![](https://i.imgur.com/9QeicaE.png)](https://leafmap.org/maplibre/3d_buildings)

## Create a 3D choropleth map

Create a 3D choropleth map of Europe with countries extruded

[![](https://i.imgur.com/fLgqYTa.png)](https://leafmap.org/maplibre/3d_choropleth)

## Extrude polygons for 3D indoor mapping

Create a 3D indoor map with the fill-extrude-height paint property.

[![](https://i.imgur.com/eYhSWaT.png)](https://leafmap.org/maplibre/3d_indoor_mapping)

## Visualize PMTiles in 3D

Visualize polygons from a PMTiles source in 3D.

[![](https://i.imgur.com/113bGei.png)](https://leafmap.org/maplibre/3d_pmtiles)

## Construct 3D map styles with MapTiler

[![](https://i.imgur.com/3Q2Q3CG.png)](https://leafmap.org/maplibre/3d_style)

## 3D Terrain

Go beyond hillshade and show elevation in actual 3D.

[![](https://i.imgur.com/sjXZ2Jm.jpeg)](https://leafmap.org/maplibre/3d_terrain)

## Add 3D buildings and GIF animations

Add 3D buildings and GIF animations to the map.

[![](https://i.imgur.com/qadwFXm.png)](https://leafmap.org/maplibre/3d_buildings_gif)

## Add a default marker

Add a default marker to the map.

[![](https://i.imgur.com/ufmqTzx.png)](https://leafmap.org/maplibre/add_a_marker)

## Add a colorbar

Add a colorbar to the map.

[![](https://i.imgur.com/84t0Sum.png)](https://leafmap.org/maplibre/add_colorbar)

## Add components to the map

Add various components to the map, including legends, colorbars, text, and HTML content.

[![](https://i.imgur.com/ZWmiKAF.png)](https://leafmap.org/maplibre/add_components)

## Add deck.gl layers

Add deck.gl layers to the map.

[![](https://i.imgur.com/rQR4687.png)](https://leafmap.org/maplibre/add_deckgl_layer)

## Add GIF animations to the map

Add GIF animations to the map.

[![](https://i.imgur.com/auytBtD.png)](https://leafmap.org/maplibre/add_gif)

## Add HTML content to the map

Add HTML content to the map.

[![](https://i.imgur.com/TgalNOv.png)](https://leafmap.org/maplibre/add_html)

## Add an icon to the map

Add an icon to the map from an external URL and use it in a symbol layer.

[![](https://i.imgur.com/Nq1uV9d.png)](https://leafmap.org/maplibre/add_image)

## Add a generated icon to the map

Add an icon to the map that was generated at runtime.

[![](https://i.imgur.com/qWWlnAm.png)](https://leafmap.org/maplibre/add_image_generated)

## Add a legend to the map

Add a custom legend to the map.

[![](https://i.imgur.com/dy60trf.png)](https://leafmap.org/maplibre/add_legend)

## Add a logo to the map

Add an image to the map as a logo.

[![](https://i.imgur.com/Pp9U4Li.png)](https://leafmap.org/maplibre/add_logo)

## Add text to the map

Add text to the map.

[![](https://i.imgur.com/UAtlh3r.png)](https://leafmap.org/maplibre/add_text)

## Animate a line

Animate a line by updating a GeoJSON source on each frame.

[![](https://i.imgur.com/LRwfBl9.png)](https://leafmap.org/maplibre/animate_a_line)

## Animate map camera around a point

Animate the map camera around a point.

[![](https://i.imgur.com/odCwtjT.png)](https://leafmap.org/maplibre/animate_camera_around_point)

## Animate a series of images

Use a series of image sources to create an animation.

[![](https://i.imgur.com/2CY0in2.png)](https://leafmap.org/maplibre/animate_images)

## Animate a point

Animate the position of a point by updating a GeoJSON source on each frame.

[![](https://i.imgur.com/EAxNQx4.png)](https://leafmap.org/maplibre/animate_point_along_line)

## Animate a point along a route

Animate a point along the distance of a line.

[![](https://i.imgur.com/kdP1oT1.png)](https://leafmap.org/maplibre/animate_point_along_route)

## Change the default position for attribution

Place attribution in the top-left position when initializing a map.

[![](https://i.imgur.com/DsmqIOy.png)](https://leafmap.org/maplibre/attribution_position)

## Customize basemaps

Customize basemaps with MapTiler and xyzservices.

[![](https://i.imgur.com/inM3a7w.png)](https://leafmap.org/maplibre/basemaps)

## Center the map on a clicked symbol

Use events and flyTo to center the map on a symbol.

[![](https://i.imgur.com/kfU5VLm.png)](https://leafmap.org/maplibre/center_on_symbol)

## Change building color based on zoom level

Use the interpolate expression to ease-in the building layer and smoothly fade from one color to the next.

[![](https://i.imgur.com/PayiTON.png)](https://leafmap.org/maplibre/change_building_color)

## Change the case of labels

Use the upcase and downcase expressions to change the case of labels.

[![](https://i.imgur.com/FzGOovv.png)](https://leafmap.org/maplibre/change_case_of_labels)

## Cloud Optimized GeoTIFF (COG)

Visualize Cloud Optimized GeoTIFF (COG) files with TiTiler.

[![](https://i.imgur.com/t3nX3vj.png)](https://leafmap.org/maplibre/cloud_optimized_geotiff)

## Create and style clusters

Use MapLibre GL JS' built-in functions to visualize points as clusters.

[![](https://i.imgur.com/VWvJKwl.png)](https://leafmap.org/maplibre/cluster)

## Change a layer's color with buttons

Use setPaintProperty to change a layer's fill color.

[![](https://i.imgur.com/Q3BbItI.png)](https://leafmap.org/maplibre/color_switcher)

## Countries filter

Utilize and refine data from the MapTiler Countries to create a Choropleth map of the US states.

[![](https://i.imgur.com/k1d6k9I.png)](https://leafmap.org/maplibre/countries_filter)

## Customize marker icon image

Use the icon-image property to change the icon image of a marker.

[![](https://i.imgur.com/yEVKJlA.png)](https://leafmap.org/maplibre/custom_marker)

## Style lines with a data-driven property

Create a visualization with a data expression for line-color.

[![](https://i.imgur.com/GY2ZVtf.png)](https://leafmap.org/maplibre/data_driven_lines)

## Disable scroll zoom

Prevent scroll from zooming a map.

[![](https://i.imgur.com/ShhYGaq.png)](https://leafmap.org/maplibre/disable_scroll_zoom)

## Display and style rich text labels

Use the format expression to display country labels in both English and in the local language.

[![](https://i.imgur.com/cUiD0XX.png)](https://leafmap.org/maplibre/display_rich_text)

## Create a draggable Marker

Drag the marker to a new location on a map and populate its coordinates in a display.

[![](https://i.imgur.com/9RNVuRf.png)](https://leafmap.org/maplibre/drag_a_marker)

## Draw features on the map

Use the draw control to draw features on the map.

[![](https://i.imgur.com/w8UFssd.png)](https://leafmap.org/maplibre/draw_features)

## Use a fallback image

Use a coalesce expression to display another image when a requested image is not available.

[![](https://i.imgur.com/0A9yuyL.png)](https://leafmap.org/maplibre/fallback_image)

## Add a pattern to a polygon

Use fill-pattern to draw a polygon from a repeating image pattern.

[![](https://i.imgur.com/ZEV5gbI.png)](https://leafmap.org/maplibre/fill_pattern)

## Fit a map to a bounding box

Fit the map to a specific area, regardless of the pixel size of the map.

[![](https://i.imgur.com/ufrSWfP.png)](https://leafmap.org/maplibre/fit_bounds)

## Fly to a location

Use flyTo to smoothly interpolate between locations.

[![](https://i.imgur.com/UVlvpi9.png)](https://leafmap.org/maplibre/fly_to)

## Slowly fly to a location

Use flyTo with flyOptions to slowly zoom to a location.

[![](https://i.imgur.com/ZzOzfP5.png)](https://leafmap.org/maplibre/fly_to_options)

## View a fullscreen map

Toggle between current view and fullscreen mode.

[![](https://i.imgur.com/Vn3carH.png)](https://leafmap.org/maplibre/fullscreen)

## Add a new layer below labels

Use the second argument of addLayer to add a layer below labels.

[![](https://i.imgur.com/TelRIyZ.png)](https://leafmap.org/maplibre/geojson_layer_in_stack)

## Add a GeoJSON line

Add a GeoJSON line to a map using addSource, then style it using addLayer’s paint properties.

[![](https://i.imgur.com/03ylQm0.png)](https://leafmap.org/maplibre/geojson_line)

## Draw GeoJSON points

Draw points from a GeoJSON collection to a map.

[![](https://i.imgur.com/cJsnBby.png)](https://leafmap.org/maplibre/geojson_points)

## Add a GeoJSON polygon

Style a polygon with the fill layer type.

[![](https://i.imgur.com/ZRFTymo.png)](https://leafmap.org/maplibre/geojson_polygon)

## Add a GeoPandas GeoDataFrame

Add a GeoPandas GeoDataFrame to a map.

[![](https://i.imgur.com/CQHcD7N.png)](https://leafmap.org/maplibre/geopandas)

## Google Earth Engine

Add Google Earth Engine data layers to a map.

[![](https://i.imgur.com/oHQDf79.png)](https://leafmap.org/maplibre/google_earth_engine)

## Create a heatmap layer

Visualize earthquake frequency by location using a heatmap layer.

[![](https://i.imgur.com/OLCRPKj.png)](https://leafmap.org/maplibre/heatmap_layer)

## Display a non-interactive map

Disable interactivity to create a static map.

[![](https://i.imgur.com/qZw8g3C.png)](https://leafmap.org/maplibre/interactive_false)

## Jump to a series of locations

Use the jumpTo function to showcase multiple locations.

[![](https://i.imgur.com/kzzegQ8.png)](https://leafmap.org/maplibre/jump_to)

## Change a map's language

Use setLayoutProperty to switch languages dynamically.

[![](https://i.imgur.com/gIRDqQK.png)](https://leafmap.org/maplibre/language_switch)

## Add a layer control

Control layer visibility with a layer control.

[![](https://i.imgur.com/NffngdY.png)](https://leafmap.org/maplibre/layer_control)

## Create a gradient line using an expression

Use the line-gradient paint property and an expression to visualize distance from the starting point of a line.

[![](https://i.imgur.com/I91N6Sk.png)](https://leafmap.org/maplibre/line_gradient)

## Add live realtime data

Use realtime GeoJSON data streams to move a symbol on your map.

[![](https://i.imgur.com/dayWZIG.png)](https://leafmap.org/maplibre/live_geojson)

## Update a feature in realtime

Change an existing feature on your map in real-time by updating its data.

[![](https://i.imgur.com/FPB5j6V.png)](https://leafmap.org/maplibre/live_update_feature)

## View local GeoJSON

View local GeoJSON without server upload.

[![](https://i.imgur.com/w3mbV2O.png)](https://leafmap.org/maplibre/local_geojson)

## View local raster datasets

View local raster datasets with localtileserver

[![](https://i.imgur.com/Q9sQLCP.png)](https://leafmap.org/maplibre/local_raster)

## Locate the user

Geolocate the user and then track their current location on the map using the GeolocateControl.

[![](https://i.imgur.com/nqYXzbN.png)](https://leafmap.org/maplibre/locate_user)

## Add a raster tile source

Add a third-party raster source to the map.

[![](https://i.imgur.com/GX7reQP.png)](https://leafmap.org/maplibre/map_tiles)

## Use MapTiler styles

Use MapTiler styles to customize the look of your map.

[![](https://i.imgur.com/0CKEFBx.png)](https://leafmap.org/maplibre/maptiler_styles)

## Get coordinates of the mouse pointer

Show mouse position on hover with pixel and latitude and longitude coordinates.

[![](https://i.imgur.com/jd2hBSz.png)](https://leafmap.org/maplibre/mouse_position)

## Add multiple geometries from one GeoJSON source

Add a polygon and circle layer from the same GeoJSON source.

[![](https://i.imgur.com/9q7npbO.png)](https://leafmap.org/maplibre/multiple_geometries)

## Display map navigation controls

Add zoom and rotation controls to the map.

[![](https://i.imgur.com/0A2o0oI.png)](https://leafmap.org/maplibre/navigation)

## Ocean Bathymetry 3D

Visualize ocean bathymetry in 3D.

[![](https://i.imgur.com/m6NwSWG.png)](https://leafmap.org/maplibre/ocean_bathymetry)

## Use OpenFreeMap vector tiles

Use free vector tiles from OpenFreeMap.

[![](https://github.com/user-attachments/assets/0a9c8cb8-2b7e-4ca5-ba7b-183b8b3f54a6)](https://leafmap.org/maplibre/openfreemap)

## Visualze Overture data

Visualize Overture Maps data.

[![](https://github.com/user-attachments/assets/e07986eb-cc5a-4f25-b7e0-bed480a415d3)](https://leafmap.org/maplibre/overture)

## PMTiles source and protocol

Uses the PMTiles plugin and protocol to present a map.

[![](https://i.imgur.com/9gQQreo.png)](https://leafmap.org/maplibre/pmtiles)

## Restrict map panning to an area

Prevent a map from being panned to a different place by setting max_bounds.

[![](https://i.imgur.com/RH5O9d3.png)](https://leafmap.org/maplibre/restrict_bounds)

## Display a satellite map

Display a satellite raster baselayer.

[![](https://i.imgur.com/S17IRDh.png)](https://leafmap.org/maplibre/satellite_map)

## Set pitch and bearing

Initialize a map with pitch and bearing camera options.

[![](https://i.imgur.com/onKRYXz.png)](https://leafmap.org/maplibre/set_pitch_bearing)

## Visualize SpatioTemporal Asset Catalog (STAC)

Visualize SpatioTemporal Asset Catalog (STAC) items with TiTiler.

[![](https://i.imgur.com/zWsNXSF.png)](https://leafmap.org/maplibre/stac)

## Export 3D maps as HTML files for website hosting

Export 3D maps as HTML files for website hosting.

[![](https://i.imgur.com/1h8tKqw.png)](https://leafmap.org/maplibre/to_html)

## Variable label placement

Use text-variable-anchor to allow high priority labels to shift position to stay on the map.

[![](https://i.imgur.com/4fo0ODF.png)](https://leafmap.org/maplibre/variable_label_placement)

## Variable label placement with offset

Use text-variable-anchor-offset to allow high priority labels to shift position to stay on the map.

[![](https://i.imgur.com/HKfcsoc.png)](https://leafmap.org/maplibre/variable_offset_label_placement)

## Add a vector tile source

Add a vector source to a map.

[![](https://i.imgur.com/svfZwFh.jpeg)](https://leafmap.org/maplibre/vector_tile)

## Add a video

Display a video on top of a satellite raster baselayer.

[![](https://i.imgur.com/8YGYanS.jpeg)](https://leafmap.org/maplibre/video_on_a_map)

## Visualize population density

Use a variable binding expression to calculate and display population density.

[![](https://i.imgur.com/7qpnvOP.png)](https://leafmap.org/maplibre/visualize_population_density)

## Add a WMS source

Add an external Web Map Service raster layer to the map using addSource's tiles option.

[![](https://i.imgur.com/itFOq8z.png)](https://leafmap.org/maplibre/wms_source)

## Fit to the bounds of a LineString

Get the bounds of a LineString.

[![](https://i.imgur.com/DEnUdXS.png)](https://leafmap.org/maplibre/zoom_to_linestring)
