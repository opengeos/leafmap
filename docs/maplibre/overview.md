# Overview

This directory contains examples of using MapLibre with Leafmap. The source code for each example is adapted from the [MapLibre documentation](https://maplibre.org/maplibre-gl-js/docs/examples/). Credits to the original authors.

## Display buildings in 3D

Use extrusions to display buildings' height in 3D.

[![](https://i.imgur.com/9QeicaE.png)](https://leafmap.org/maplibre/3d_buildings)

## Extrude polygons for 3D indoor mapping

Create a 3D indoor map with the fill-extrude-height paint property.

[![](https://i.imgur.com/eYhSWaT.png)](https://leafmap.org/maplibre/3d_indoor_mapping)

## 3D Terrain

Go beyond hillshade and show elevation in actual 3D.

[![](https://i.imgur.com/sjXZ2Jm.jpeg)](https://leafmap.org/maplibre/3d_terrain)

## Add a default marker

Add a default marker to the map.

[![](https://i.imgur.com/ufmqTzx.png)](https://leafmap.org/maplibre/add_marker)

## Add deck.gl layers

Add deck.gl layers to the map.

[![](https://i.imgur.com/rQR4687.png)](https://leafmap.org/maplibre/deckgl_layer)

## Add an icon to the map

Add an icon to the map from an external URL and use it in a symbol layer.

[![](https://i.imgur.com/Nq1uV9d.png)](https://leafmap.org/maplibre/add_image)

## Add a generated icon to the map

Add an icon to the map that was generated at runtime.

[![](https://i.imgur.com/qWWlnAm.png)](https://leafmap.org/maplibre/add_image_generated)

## Animate map camera around a point

Animate the map camera around a point.

[![](https://i.imgur.com/odCwtjT.png)](https://leafmap.org/maplibre/animate_camera_around_point)

## Animate a series of images

Use a series of image sources to create an animation.

[![](https://i.imgur.com/2CY0in2.png)](https://leafmap.org/maplibre/animate_images)

## Change the default position for attribution

Place attribution in the top-left position when initializing a map.

[![](https://i.imgur.com/DsmqIOy.png)](https://leafmap.org/maplibre/attribution_position)

## Change building color based on zoom level

Use the interpolate expression to ease-in the building layer and smoothly fade from one color to the next.

[![](https://i.imgur.com/PayiTON.png)](https://leafmap.org/maplibre/change_building_color)

## Change the case of labels

Use the upcase and downcase expressions to change the case of labels.

[![](https://i.imgur.com/FzGOovv.png)](https://leafmap.org/maplibre/change_case_of_labels)

## Create and style clusters

Use MapLibre GL JS' built-in functions to visualize points as clusters.

[![](https://i.imgur.com/VWvJKwl.png)](https://leafmap.org/maplibre/cluster)

## Change a layer's color with buttons

Use setPaintProperty to change a layer's fill color.

[![](https://i.imgur.com/Q3BbItI.png)](https://leafmap.org/maplibre/color_switcher)

## Style lines with a data-driven property

Create a visualization with a data expression for line-color.

[![](https://i.imgur.com/GY2ZVtf.png)](https://leafmap.org/maplibre/data_driven_lines)

## Display and style rich text labels

Use the format expression to display country labels in both English and in the local language.

[![](https://i.imgur.com/cUiD0XX.png)](https://leafmap.org/maplibre/display_rich_text)

## Use a fallback image

Use a coalesce expression to display another image when a requested image is not available.

[![](https://i.imgur.com/0A9yuyL.png)](https://leafmap.org/maplibre/fallback_image)

## Add a video

Display a video on top of a satellite raster baselayer.

[![](https://i.imgur.com/8YGYanS.jpeg)](https://leafmap.org/maplibre/add_video)

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

# Add a GeoJSON polygon

Style a polygon with the fill layer type.

[![](https://i.imgur.com/ZRFTymo.png)](https://leafmap.org/maplibre/geojson_polygon)

## Create a heatmap layer

Visualize earthquake frequency by location using a heatmap layer.

[![](https://i.imgur.com/OLCRPKj.png)](https://leafmap.org/maplibre/heatmap_layer)

## Display a non-interactive map

Disable interactivity to create a static map.

[![](https://i.imgur.com/qZw8g3C.png)](https://leafmap.org/maplibre/interactive_false)

## Jump to a series of locations

Use the jumpTo function to showcase multiple locations.

[![](https://i.imgur.com/kzzegQ8.png)](https://leafmap.org/maplibre/jump_to)

## Create a gradient line using an expression

Use the line-gradient paint property and an expression to visualize distance from the starting point of a line.

[![](https://i.imgur.com/I91N6Sk.png)](https://leafmap.org/maplibre/line_gradient)

## Update a feature in realtime

Change an existing feature on your map in real-time by updating its data.

[![](https://i.imgur.com/FPB5j6V.png)](https://leafmap.org/maplibre/live_update_feature)

## Add live realtime data

Use realtime GeoJSON data streams to move a symbol on your map.

[![](https://i.imgur.com/dayWZIG.png)](https://leafmap.org/maplibre/live_geojson)

## View local GeoJSON

View local GeoJSON without server upload.

[![](https://i.imgur.com/w3mbV2O.png)](https://leafmap.org/maplibre/local_geojson)

## Locate the user

Geolocate the user and then track their current location on the map using the GeolocateControl.

[![](https://i.imgur.com/nqYXzbN.png)](https://leafmap.org/maplibre/locate_user)

## Add a raster tile source

Add a third-party raster source to the map.

[![](https://i.imgur.com/GX7reQP.png)](https://leafmap.org/maplibre/map_tiles)

## Get coordinates of the mouse pointer

Show mouse position on hover with pixel and latitude and longitude coordinates.

[![](https://i.imgur.com/jd2hBSz.png)](https://leafmap.org/maplibre/mouse_position)

## Add multiple geometries from one GeoJSON source

Add a polygon and circle layer from the same GeoJSON source.

[![](https://i.imgur.com/9q7npbO.png)](https://leafmap.org/maplibre/multiple_geometries)

## Display map navigation controls

Add zoom and rotation controls to the map.

[![](https://i.imgur.com/0A2o0oI.png)](https://leafmap.org/maplibre/navigation)

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

## Variable label placement

Use text-variable-anchor to allow high priority labels to shift position to stay on the map.

[![](https://i.imgur.com/4fo0ODF.png)](https://leafmap.org/maplibre/variable_label_placement)

## Variable label placement with offset

Use text-variable-anchor-offset to allow high priority labels to shift position to stay on the map.

[![](https://i.imgur.com/HKfcsoc.png)](https://leafmap.org/maplibre/variable_offset_label_placement)

## Add a vector tile source

Add a vector source to a map.

[![](https://i.imgur.com/svfZwFh.jpeg)](https://leafmap.org/maplibre/vector_tile)

## Visualize population density

Use a variable binding expression to calculate and display population density.

[![](https://i.imgur.com/7qpnvOP.png)](https://leafmap.org/maplibre/visualize_population_density)

## Add a WMS source

Add an external Web Map Service raster layer to the map using addSource's tiles option.

[![](https://i.imgur.com/itFOq8z.png)](https://leafmap.org/maplibre/wms_source)

## Fit to the bounds of a LineString

Get the bounds of a LineString.

[![](https://i.imgur.com/DEnUdXS.png)](https://leafmap.org/maplibre/zoom_to_linestring)
