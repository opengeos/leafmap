"""Module for dealing with the toolbar.
"""

import math
import os
import ipyevents
import ipyleaflet
import ipywidgets as widgets
from ipyfilechooser import FileChooser
from .common import *
from .pc import *
from typing import Optional, Union, Dict, List


def tool_template(m, opened: Optional[bool] = True):
    """Generates a tool GUI template using ipywidgets. Icons can be found at https://fontawesome.com/v4/icons

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.
        opened (bool, optional): Whether to open the toolbar. Defaults to True.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gear",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    checkbox = widgets.Checkbox(
        description="Checkbox",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    dropdown = widgets.Dropdown(
        options=["Option 1", "Option 2", "Option 3"],
        value=None,
        description="Dropdown:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    int_slider = widgets.IntSlider(
        min=1,
        max=100,
        description="Int Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style=style,
    )

    int_slider_label = widgets.Label(str(int_slider.value))

    def update_int_slider(change):
        int_slider_label.value = str(change["new"])

    int_slider.observe(update_int_slider, "value")

    float_slider = widgets.FloatSlider(
        min=1,
        max=100,
        description="Float Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="210px", padding=padding),
        style=style,
    )

    float_slider_label = widgets.Label(str(float_slider.value))

    def update_float_slider(change):
        float_slider_label.value = str(change["new"])

    float_slider.observe(update_float_slider, "value")

    color = widgets.ColorPicker(
        concise=False,
        description="Color:",
        value="white",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    text = widgets.Text(
        value="",
        description="Textbox:",
        placeholder="Placeholder",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    textarea = widgets.Textarea(
        placeholder="Placeholder",
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        checkbox,
        widgets.HBox([int_slider, int_slider_label]),
        widgets.HBox([float_slider, float_slider_label]),
        dropdown,
        text,
        color,
        textarea,
        buttons,
        output,
    ]

    # toolbar_event = ipyevents.Event(
    #     source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    # )

    # def handle_toolbar_event(event):
    #     if event["type"] == "mouseenter":
    #         toolbar_widget.children = [toolbar_header, toolbar_footer]
    #     elif event["type"] == "mouseleave":
    #         if not toolbar_button.value:
    #             toolbar_widget.children = [toolbar_button]
    #             toolbar_button.value = False
    #             close_button.value = False

    # toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.outputs = ()
                print("Running ...")
        elif change["new"] == "Reset":
            textarea.value = ""
            output.outputs = ()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = opened
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def tool_header_template(m, opened: Optional[bool] = True):
    """Create a toolbar widget.

    Args:
        m (geemap.Map, optional): The geemap.Map instance. Defaults to None.
        opened (bool, optional): Whether to open the toolbar. Defaults to True.
    """

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gear",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        buttons,
        output,
    ]

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.outputs = ()
                print("Running ...")
        elif change["new"] == "Reset":
            output.outputs = ()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = opened
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def main_toolbar(m):
    """Creates the main toolbar and adds it to the map.

    Args:
        m (leafmap.Map): The leafmap Map object.
    """
    all_tools = {
        "map": {
            "name": "basemap",
            "tooltip": "Change basemap",
        },
        "globe": {
            "name": "split_map",
            "tooltip": "Split-panel map",
        },
        "adjust": {
            "name": "planet",
            "tooltip": "Planet imagery",
        },
        "folder-open": {
            "name": "open_data",
            "tooltip": "Open local vector/raster data",
        },
        "gears": {
            "name": "whitebox",
            "tooltip": "WhiteboxTools for local geoprocessing",
        },
        "fast-forward": {
            "name": "timeslider",
            "tooltip": "Activate the time slider",
        },
        "eraser": {
            "name": "eraser",
            "tooltip": "Remove all drawn features",
        },
        "camera": {
            "name": "save_map",
            "tooltip": "Save map as HTML or image",
        },
        "filter": {
            "name": "census",
            "tooltip": "Get US Census data",
        },
        "info": {
            "name": "inspector",
            "tooltip": "Get COG/STAC pixel value",
        },
        "search": {
            "name": "search_xyz",
            "tooltip": "Search XYZ tile services",
        },
        "download": {
            "name": "download_osm",
            "tooltip": "Download OSM data",
        },
        "picture-o": {
            "name": "raster",
            "tooltip": "Open COG/STAC dataset",
        },
        "search-plus": {
            "name": "search_geojson",
            "tooltip": "Search features in GeoJSON layer",
        },
        "table": {
            "name": "attribute_table",
            "tooltip": "Open attribute table",
        },
        "pencil-square-o": {
            "name": "edit_vector",
            "tooltip": "Create vector data",
        },
        "stack-exchange": {
            "name": "stac",
            "tooltip": "Discover STAC Catalog",
        },
        "plane": {
            "name": "oam",
            "tooltip": "Search OpenAerialMap",
        },
        # "spinner": {
        #     "name": "placeholder2",
        #     "tooltip": "This is a placeholder",
        # },
        # "question": {
        #     "name": "help",
        #     "tooltip": "Get help",
        # },
    }

    # if m.sandbox_path is None and (os.environ.get("USE_VOILA") is not None):
    #     voila_tools = ["camera", "folder-open", "gears"]

    #     for item in voila_tools:
    #         if item in tools.keys():
    #             del tools[item]

    tools = {}
    for tool in all_tools:
        if os.environ.get(all_tools[tool]["name"].upper(), "").upper() != "FALSE":
            tools[tool] = all_tools[tool]

    icons = list(tools.keys())
    tooltips = [item["tooltip"] for item in list(tools.values())]
    toolnames = [item["name"].upper() for item in list(all_tools.values())]
    toolnames.sort()
    setattr(m, "_ENV_VARS", toolnames)

    icon_width = "32px"
    icon_height = "32px"
    n_cols = 3
    n_rows = math.ceil(len(icons) / n_cols)

    toolbar_grid = widgets.GridBox(
        children=[
            widgets.ToggleButton(
                layout=widgets.Layout(
                    width="auto", height="auto", padding="0px 0px 0px 4px"
                ),
                button_style="primary",
                icon=icons[i],
                tooltip=tooltips[i],
            )
            for i in range(len(icons))
        ],
        layout=widgets.Layout(
            width="109px",
            grid_template_columns=(icon_width + " ") * n_cols,
            grid_template_rows=(icon_height + " ") * n_rows,
            grid_gap="1px 1px",
            padding="5px",
        ),
    )
    m.toolbar = toolbar_grid

    def tool_callback(change):
        if change["new"]:
            current_tool = change["owner"]
            for tool in toolbar_grid.children:
                if tool is not current_tool:
                    tool.value = False
            tool = change["owner"]
            tool_name = tools[tool.icon]["name"]

            if tool_name == "basemap":
                change_basemap(m)
            if tool_name == "split_map":
                split_basemaps(m)
            if tool_name == "planet":
                split_basemaps(m, layers_dict=planet_tiles())
            elif tool_name == "open_data":
                open_data_widget(m)
            elif tool_name == "eraser":
                if m.draw_control is not None:
                    m.draw_control.clear()
                    m.user_roi = None
                    m.user_rois = None
                    m.draw_features = []
            elif tool_name == "whitebox":
                import whiteboxgui.whiteboxgui as wbt

                tools_dict = wbt.get_wbt_dict()
                wbt_toolbox = wbt.build_toolbox(
                    tools_dict,
                    max_width="800px",
                    max_height="500px",
                    sandbox_path=m.sandbox_path,
                )
                wbt_control = ipyleaflet.WidgetControl(
                    widget=wbt_toolbox, position="bottomright"
                )
                m.whitebox = wbt_control
                m.add(wbt_control)
            elif tool_name == "timeslider":
                m.add_time_slider()
            elif tool_name == "save_map":
                save_map((m))
            elif tool_name == "census":
                census_widget(m)
            elif tool_name == "inspector":
                inspector_gui(m)
            elif tool_name == "search_xyz":
                search_basemaps(m)
            elif tool_name == "download_osm":
                download_osm(m)
            elif tool_name == "raster":
                open_raster_gui(m)
            elif tool_name == "search_geojson":
                search_geojson_gui(m)
            elif tool_name == "attribute_table":
                select_table_gui(m)
            elif tool_name == "edit_vector":
                edit_draw_gui(m)
            elif tool_name == "stac":
                stac_gui(m)
            elif tool_name == "oam":
                oam_search_gui(m)
            elif tool_name == "help":
                import webbrowser

                webbrowser.open_new_tab("https://leafmap.org")
                current_tool.value = False
        else:
            # tool = change["owner"]
            # tool_name = tools[tool.icon]["name"]
            pass

        m.toolbar_reset()

    for tool in toolbar_grid.children:
        tool.observe(tool_callback, "value")

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="wrench",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )
    m.toolbar_button = toolbar_button

    layers_button = widgets.ToggleButton(
        value=False,
        tooltip="Layers",
        icon="server",
        layout=widgets.Layout(height="28px", width="72px"),
    )

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [layers_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [toolbar_grid]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                layers_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            layers_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not layers_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def layers_btn_click(change):
        if change["new"]:
            toolbar_footer.children = layer_manager_gui(m, return_widget=True)
            toolbar_button.value = False
        else:
            toolbar_footer.children = [toolbar_grid]

    layers_button.observe(layers_btn_click, "value")

    toolbar_control = ipyleaflet.WidgetControl(
        widget=toolbar_widget, position="topright"
    )

    m.add(toolbar_control)


def open_data_widget(m):
    """A widget for opening local vector/raster data.

    Args:
        m (object): leafmap.Map
    """
    import warnings
    from .colormaps import list_colormaps

    warnings.filterwarnings("ignore")

    padding = "0px 0px 0px 5px"
    style = {"description_width": "initial"}

    file_type = widgets.ToggleButtons(
        options=["Shapefile", "GeoJSON", "CSV", "Vector", "Raster"],
        tooltips=[
            "Open a shapefile",
            "Open a GeoJSON file",
            "Open a vector dataset",
            "Create points from CSV",
            "Open a vector dataset",
            "Open a raster dataset",
        ],
    )
    file_type.style.button_width = "88px"

    filepath = widgets.Text(
        value="",
        description="File path or http URL:",
        tooltip="Enter a file path or http URL to vector data",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )
    http_widget = widgets.HBox()

    file_chooser = FileChooser(
        os.getcwd(), sandbox_path=m.sandbox_path, layout=widgets.Layout(width="454px")
    )
    file_chooser.filter_pattern = "*.shp"
    file_chooser.use_dir_icons = True

    layer_name = widgets.Text(
        value="Shapefile",
        description="Enter a layer name:",
        tooltip="Enter a layer name for the selected file",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    longitude = widgets.Dropdown(
        options=[],
        value=None,
        description="Longitude:",
        layout=widgets.Layout(width="149px", padding=padding),
        style=style,
    )

    latitude = widgets.Dropdown(
        options=[],
        value=None,
        description="Latitude:",
        layout=widgets.Layout(width="149px", padding=padding),
        style=style,
    )

    label = widgets.Dropdown(
        options=[],
        value=None,
        description="Label:",
        layout=widgets.Layout(width="149px", padding=padding),
        style=style,
    )

    point_check = widgets.Checkbox(
        description="Is it a point layer?",
        indent=False,
        layout=widgets.Layout(padding=padding, width="150px"),
        style=style,
    )

    point_popup = widgets.SelectMultiple(
        options=[
            "None",
        ],
        value=["None"],
        description="Popup attributes:",
        disabled=False,
        style=style,
    )

    csv_widget = widgets.HBox()
    point_widget = widgets.HBox()

    def point_layer_check(change):
        if point_check.value:
            if filepath.value.strip() != "":
                m.default_style = {"cursor": "wait"}
                point_popup.options = vector_col_names(filepath.value)
                point_popup.value = [point_popup.options[0]]

            point_widget.children = [point_check, point_popup]
        else:
            point_widget.children = [point_check]

    point_check.observe(point_layer_check)

    ok_cancel = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    # ok_cancel.style.button_width = "50px"

    bands = widgets.Text(
        value=None,
        description="Band:",
        tooltip="Enter a list of band indices",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    vmin = widgets.Text(
        value=None,
        description="vmin:",
        tooltip="Minimum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="148px"),
    )

    vmax = widgets.Text(
        value=None,
        description="vmax:",
        tooltip="Maximum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="148px"),
    )

    nodata = widgets.Text(
        value=None,
        description="Nodata:",
        tooltip="Nodata the raster to visualize",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    palette = widgets.Dropdown(
        options=[],
        value=None,
        description="palette:",
        layout=widgets.Layout(width="300px"),
        style=style,
    )

    raster_options = widgets.VBox()

    def filepath_change(change):
        if file_type.value == "Raster":
            pass
            # if (
            #     filepath.value.startswith("http")
            #     or filepath.value.endswith(".txt")
            #     or filepath.value.endswith(".csv")
            # ):
            #     bands.disabled = True
            #     palette.disabled = False
            #     # x_dim.disabled = True
            #     # y_dim.disabled = True
            # else:
            #     bands.disabled = False
            #     palette.disabled = False
            #     # x_dim.disabled = True
            #     # y_dim.disabled = True

    filepath.observe(filepath_change, "value")

    tool_output = widgets.Output(
        layout=widgets.Layout(max_height="150px", max_width="500px", overflow="auto")
    )

    main_widget = widgets.VBox(
        [
            file_type,
            file_chooser,
            http_widget,
            csv_widget,
            layer_name,
            point_widget,
            raster_options,
            ok_cancel,
            tool_output,
        ]
    )

    tool_output_ctrl = ipyleaflet.WidgetControl(widget=main_widget, position="topright")

    if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
        m.remove_control(m.tool_output_ctrl)

    def bands_changed(change):
        if change["new"] and "," in change["owner"].value:
            palette.value = None
            palette.disabled = True
        else:
            palette.disabled = False

    bands.observe(bands_changed, "value")

    def chooser_callback(chooser):
        filepath.value = file_chooser.selected

        if file_type.value == "CSV":
            import pandas as pd

            df = pd.read_csv(filepath.value)
            col_names = df.columns.values.tolist()
            longitude.options = col_names
            latitude.options = col_names
            label.options = col_names

            if "longitude" in col_names:
                longitude.value = "longitude"
            if "latitude" in col_names:
                latitude.value = "latitude"
            if "name" in col_names:
                label.value = "name"

    file_chooser.register_callback(chooser_callback)

    def file_type_changed(change):
        ok_cancel.value = None
        file_chooser.default_path = os.getcwd()
        file_chooser.reset()
        layer_name.value = file_type.value
        csv_widget.children = []
        filepath.value = ""
        tool_output.outputs = ()

        if change["new"] == "Shapefile":
            file_chooser.filter_pattern = "*.shp"
            raster_options.children = []
            point_widget.children = []
            point_check.value = False
            http_widget.children = []
        elif change["new"] == "GeoJSON":
            file_chooser.filter_pattern = ["*.geojson", "*.json"]
            raster_options.children = []
            point_widget.children = []
            point_check.value = False
            http_widget.children = [filepath]
        elif change["new"] == "Vector":
            file_chooser.filter_pattern = "*.*"
            raster_options.children = []
            point_widget.children = [point_check]
            point_check.value = False
            http_widget.children = [filepath]
        elif change["new"] == "CSV":
            file_chooser.filter_pattern = ["*.csv", "*.CSV"]
            csv_widget.children = [longitude, latitude, label]
            raster_options.children = []
            point_widget.children = []
            point_check.value = False
            http_widget.children = [filepath]
        elif change["new"] == "Raster":
            file_chooser.filter_pattern = ["*.tif", "*.img"]
            palette.options = list_colormaps(add_extra=True)
            palette.value = None
            raster_options.children = [
                widgets.HBox([bands, vmin, vmax]),
                widgets.HBox([nodata, palette]),
            ]
            point_widget.children = []
            point_check.value = False
            http_widget.children = [filepath]

    def ok_cancel_clicked(change):
        if change["new"] == "Apply":
            m.default_style = {"cursor": "wait"}
            file_path = filepath.value

            with tool_output:
                tool_output.outputs = ()
                if file_path.strip() != "":
                    ext = os.path.splitext(file_path)[1]
                    if point_check.value:
                        popup = list(point_popup.value)
                        if len(popup) == 1:
                            popup = popup[0]
                        m.add_point_layer(
                            file_path,
                            popup=popup,
                            layer_name=layer_name.value,
                        )
                    elif ext.lower() == ".shp":
                        m.add_shp(file_path, style={}, layer_name=layer_name.value)
                    elif ext.lower() == ".geojson":
                        m.add_geojson(file_path, style={}, layer_name=layer_name.value)

                    elif ext.lower() == ".csv" and file_type.value == "CSV":
                        m.add_xy_data(
                            file_path,
                            x=longitude.value,
                            y=latitude.value,
                            label=label.value,
                            layer_name=layer_name.value,
                        )

                    elif (
                        ext.lower() in [".tif", "img"]
                    ) and file_type.value == "Raster":
                        band = None
                        vis_min = None
                        vis_max = None
                        vis_nodata = None

                        try:
                            if len(bands.value) > 0:
                                band = int(bands.value)
                            if len(vmin.value) > 0:
                                vis_min = float(vmin.value)
                            if len(vmax.value) > 0:
                                vis_max = float(vmax.value)
                            if len(nodata.value) > 0:
                                vis_nodata = float(nodata.value)
                        except Exception as _:
                            pass

                        m.add_raster(
                            file_path,
                            layer_name=layer_name.value,
                            band=band,
                            palette=palette.value,
                            vmin=vis_min,
                            vmax=vis_max,
                            nodata=vis_nodata,
                        )

                else:
                    print("Please select a file to open.")

            m.toolbar_reset()
            m.default_style = {"cursor": "default"}

        elif change["new"] == "Reset":
            file_chooser.reset()
            tool_output.outputs = ()
            filepath.value = ""
            m.toolbar_reset()
        elif change["new"] == "Close":
            if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
                m.remove_control(m.tool_output_ctrl)
                m.tool_output_ctrl = None
                m.toolbar_reset()

        ok_cancel.value = None

    file_type.observe(file_type_changed, names="value")
    ok_cancel.observe(ok_cancel_clicked, names="value")
    # file_chooser.register_callback(chooser_callback)

    m.add(tool_output_ctrl)
    m.tool_output_ctrl = tool_output_ctrl


def open_raster_gui(m):
    """A widget for opening local/remote COG/STAC data.

    Args:
        m (object): leafmap.Map
    """

    padding = "0px 0px 0px 5px"
    style = {"description_width": "initial"}

    tool_output = widgets.Output(
        layout=widgets.Layout(max_height="150px", max_width="500px", overflow="auto")
    )

    file_type = widgets.ToggleButtons(
        options=["GeoTIFF", "COG", "STAC", "Microsoft"],
        tooltips=[
            "Open a local GeoTIFF file",
            "Open a remote COG file",
            "Open a remote STAC item",
            "Create COG from Microsoft Planetary Computer",
        ],
    )
    file_type.style.button_width = "110px"

    file_chooser = FileChooser(
        os.getcwd(), sandbox_path=m.sandbox_path, layout=widgets.Layout(width="454px")
    )
    file_chooser.filter_pattern = ["*.tif", "*.tiff"]
    file_chooser.use_dir_icons = True

    source_widget = widgets.VBox([file_chooser])

    http_url = widgets.Text(
        value="",
        description="HTTP URL:",
        tooltip="Enter an http URL to COG file",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    collection = widgets.Dropdown(
        options=["landsat-8-c2-l2 - Landsat 8 Collection 2 Level-2"],
        value="landsat-8-c2-l2 - Landsat 8 Collection 2 Level-2",
        description="PC Collection:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    items = widgets.Text(
        value="LC08_L2SP_047027_20201204_02_T1",
        description="STAC Items:",
        tooltip="STAC Item ID",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    assets = widgets.Text(
        value="SR_B7,SR_B5,SR_B4",
        description="STAC Assets:",
        tooltip="STAC Asset ID",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    layer_name = widgets.Text(
        value="GeoTIFF",
        description="Enter a layer name:",
        tooltip="Enter a layer name for the selected file",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    ok_cancel = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    # ok_cancel.style.button_width = "50px"

    bands = widgets.Text(
        value=None,
        description="Band:",
        tooltip="Enter a list of band indices",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    band_width = "149px"
    red = widgets.Dropdown(
        value=None,
        options=[],
        description="Red:",
        tooltip="Select a band for the red channel",
        style=style,
        layout=widgets.Layout(width=band_width, padding=padding),
    )

    green = widgets.Dropdown(
        value=None,
        options=[],
        description="Green:",
        tooltip="Select a band for the green channel",
        style=style,
        layout=widgets.Layout(width="148px", padding=padding),
    )

    blue = widgets.Dropdown(
        value=None,
        options=[],
        description="Blue:",
        tooltip="Select a band for the blue channel",
        style=style,
        layout=widgets.Layout(width=band_width, padding=padding),
    )

    vmin = widgets.Text(
        value=None,
        description="vmin:",
        tooltip="Minimum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="148px", padding=padding),
    )

    vmax = widgets.Text(
        value=None,
        description="vmax:",
        tooltip="Maximum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="148px", padding=padding),
    )

    nodata = widgets.Text(
        value=None,
        description="Nodata:",
        tooltip="Nodata the raster to visualize",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    local_tile_palettes = list_palettes(add_extra=True)
    cog_stac_palettes = list_palettes(lowercase=True)
    palette_options = local_tile_palettes
    palette = widgets.Dropdown(
        options=palette_options,
        value=None,
        description="palette:",
        layout=widgets.Layout(width="300px", padding=padding),
        style=style,
    )

    checkbox = widgets.Checkbox(
        value=False,
        description="Additional params",
        indent=False,
        layout=widgets.Layout(width="154px", padding=padding),
        style=style,
    )

    add_params_text1 = "Additional parameters in the format of a dictionary, for example, \n {'palette': ['#006633', '#E5FFCC', '#662A00', '#D8D8D8', '#F5F5F5']}"
    add_params_text2 = "Additional parameters in the format of a dictionary, for example, \n {'expression': '(SR_B5-SR_B4)/(SR_B5+SR_B4)'}"
    add_params = widgets.Textarea(
        value="",
        placeholder=add_params_text1,
        layout=widgets.Layout(width="454px", padding=padding),
        style=style,
    )

    params_widget = widgets.HBox()

    raster_options = widgets.VBox()
    raster_options.children = [
        widgets.HBox([red, green, blue]),
        widgets.HBox([vmin, vmax, nodata]),
        widgets.HBox([palette, checkbox]),
        params_widget,
    ]

    def collection_changed(change):
        if change["new"]:
            if not hasattr(m, "pc_inventory"):
                setattr(m, "pc_inventory", get_pc_inventory())
            col_name = change["new"].split(" - ")[0]
            items.value = m.pc_inventory[col_name]["first_item"]
            band_names = m.pc_inventory[col_name]["bands"]
            red.options = band_names
            green.options = band_names
            blue.options = band_names

            if change["new"] == "landsat-8-c2-l2 - Landsat 8 Collection 2 Level-2":
                items.value = "LC08_L2SP_047027_20201204_02_T1"
                assets.value = "SR_B7,SR_B5,SR_B4"
                red.value = "SR_B7"
                green.value = "SR_B5"
                blue.value = "SR_B4"
            elif change["new"] == "sentinel-2-l2a - Sentinel-2 Level-2A":
                items.value = "S2B_MSIL2A_20190629T212529_R043_T06VVN_20201006T080531"
                assets.value = "B08,B04,B03"
                red.value = "B08"
                green.value = "B04"
                blue.value = "B03"
            else:
                if len(band_names) > 2:
                    assets.value = ",".join(band_names[:3])
                    red.value = band_names[0]
                    green.value = band_names[1]
                    blue.value = band_names[2]
                else:
                    assets.value = band_names[0]
                    red.value = band_names[0]
                    green.value = band_names[0]
                    blue.value = band_names[0]

    collection.observe(collection_changed, names="value")

    def band_changed(change):
        if change["name"]:
            if not checkbox.value:
                if file_type.value == "GeoTIFF":
                    if hasattr(m, "tile_client"):
                        min_max = local_tile_vmin_vmax(
                            m.tile_client, bands=[red.value, green.value, blue.value]
                        )
                        vmin.value = str(min_max[0])
                        vmax.value = str(min_max[1])
                elif file_type.value == "Microsoft":
                    if len(set([red.value, green.value, blue.value])) == 1:
                        assets.value = f"{red.value}"
                    else:
                        assets.value = f"{red.value},{green.value},{blue.value}"

    red.observe(band_changed, names="value")
    green.observe(band_changed, names="value")
    blue.observe(band_changed, names="value")

    def checkbox_changed(change):
        if change["new"]:
            params_widget.children = [add_params]
        else:
            params_widget.children = []

    checkbox.observe(checkbox_changed, names="value")

    def url_change(change):
        if change["new"] and change["new"].startswith("http"):
            with tool_output:
                try:
                    print("Retrieving band names...")
                    if file_type.value == "COG":
                        bandnames = cog_bands(change["new"])
                    elif file_type.value == "STAC":
                        bandnames = stac_bands(change["new"])
                    red.options = bandnames
                    green.options = bandnames
                    blue.options = bandnames
                    if len(bandnames) > 2:
                        red.value = bandnames[0]
                        green.value = bandnames[1]
                        blue.value = bandnames[2]
                    else:
                        red.value = bandnames[0]
                        green.value = bandnames[0]
                        blue.value = bandnames[0]
                    tool_output.outputs = ()

                except Exception as e:
                    print(e)
                    print("Error loading URL.")
                    return
        else:
            red.options = []
            green.options = []
            blue.options = []
            vmin.value = ""
            vmax.value = ""
            nodata.value = ""
            palette.value = None

    http_url.observe(url_change, names="value")

    main_widget = widgets.VBox(
        [
            file_type,
            source_widget,
            layer_name,
            raster_options,
            ok_cancel,
            tool_output,
        ]
    )

    tool_output_ctrl = ipyleaflet.WidgetControl(widget=main_widget, position="topright")

    if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
        m.remove_control(m.tool_output_ctrl)

    def bands_changed(change):
        if change["new"] and "," in change["owner"].value:
            palette.value = None
            palette.disabled = True
        else:
            palette.disabled = False

    bands.observe(bands_changed, "value")

    def chooser_callback(chooser):
        try:
            source = file_chooser.selected
            tile_layer, tile_client = get_local_tile_layer(source, return_client=True)
            if not hasattr(m, "tile_client"):
                setattr(m, "tile_client", tile_client)
            bandnames = local_tile_bands(tile_client)
            red.options = bandnames
            green.options = bandnames
            blue.options = bandnames
            if len(bandnames) > 2:
                red.value = bandnames[0]
                green.value = bandnames[1]
                blue.value = bandnames[2]
                min_max = local_tile_vmin_vmax(
                    tile_client, bands=[red.value, green.value, blue.value]
                )
                vmin.value = str(min_max[0])
                vmax.value = str(min_max[1])
            else:
                red.value = bandnames[0]
                green.value = bandnames[0]
                blue.value = bandnames[0]
                min_max = local_tile_vmin_vmax(tile_client)
                vmin.value = str(min_max[0])
                vmax.value = str(min_max[1])
        except Exception as e:
            with tool_output:
                print(e)

    file_chooser.register_callback(chooser_callback)

    def file_type_changed(change):
        ok_cancel.value = None
        file_chooser.default_path = os.getcwd()
        file_chooser.reset()
        layer_name.value = file_type.value
        http_url.value = ""
        tool_output.outputs = ()
        red.value = None
        green.value = None
        blue.value = None
        vmin.value = ""
        vmax.value = ""
        nodata.value = ""
        palette.value = None

        if change["new"] == "GeoTIFF":
            source_widget.children = [file_chooser]
            file_chooser.filter_pattern = ["*.tif", "*.tiff"]
            palette.options = local_tile_palettes
            palette.value = None
            add_params.placeholder = add_params_text1
            raster_options.children = [
                widgets.HBox([red, green, blue]),
                widgets.HBox([vmin, vmax, nodata]),
                widgets.HBox([palette, checkbox]),
                params_widget,
            ]
        elif change["new"] == "COG":
            http_url.value = "https://github.com/opengeos/data/releases/download/raster/Libya-2023-09-13.tif"
            source_widget.children = [http_url]
            palette.options = cog_stac_palettes
            palette.value = None
            add_params.placeholder = add_params_text2
        elif change["new"] == "STAC":
            http_url.value = "https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json"
            source_widget.children = [http_url]
            palette.options = cog_stac_palettes
            palette.value = None
            red.value = "B3"
            green.value = "B2"
            blue.value = "B1"
            add_params.placeholder = add_params_text2
        elif change["new"] == "Microsoft":
            source_widget.children = [collection, items, assets]
            palette.options = cog_stac_palettes
            palette.value = None
            add_params.placeholder = add_params_text2
            collection.options = get_pc_collection_list()
            collection.value = "landsat-8-c2-l2 - Landsat 8 Collection 2 Level-2"
            if not hasattr(m, "pc_inventory"):
                setattr(m, "pc_inventory", get_pc_inventory())
            items.value = "LC08_L2SP_047027_20201204_02_T1"
            assets.value = "SR_B7,SR_B5,SR_B4"

    def ok_cancel_clicked(change):
        if change["new"] == "Apply":
            m.default_style = {"cursor": "wait"}
            # file_path = http_url.value

            with tool_output:
                tool_output.outputs = ()
                print("Loading data...")
                if file_type.value == "GeoTIFF" and file_chooser.selected:
                    band = None
                    vis_min = None
                    vis_max = None
                    vis_nodata = None
                    vis_palette = None

                    try:
                        if len(red.options) > 2:
                            band = [red.value, green.value, blue.value]
                            if len(set(band)) > 1:
                                palette.value = None
                            else:
                                band = [red.value]
                        else:
                            band = [red.value]
                        if len(vmin.value) > 0:
                            vis_min = float(vmin.value)
                        if len(vmax.value) > 0:
                            vis_max = float(vmax.value)
                        if len(nodata.value) > 0:
                            vis_nodata = float(nodata.value)
                        if (
                            checkbox.value
                            and add_params.value.strip().startswith("{")
                            and add_params.value.strip().endswith("}")
                        ):
                            vis_params = eval(add_params.value)
                            if "palette" in vis_params:
                                vis_palette = vis_params["palette"]
                            else:
                                vis_palette = get_palette_colors(
                                    palette.value, hashtag=True
                                )
                        elif palette.value is not None:
                            vis_palette = get_palette_colors(
                                palette.value, hashtag=True
                            )
                    except Exception as e:
                        pass

                    m.add_raster(
                        file_chooser.selected,
                        layer_name=layer_name.value,
                        band=band,
                        palette=vis_palette,
                        vmin=vis_min,
                        vmax=vis_max,
                        nodata=vis_nodata,
                    )
                    tool_output.outputs = ()
                elif file_type.value in ["COG", "STAC"] and http_url.value:
                    try:
                        tool_output.outputs = ()
                        print("Loading data...")

                        if (
                            checkbox.value
                            and add_params.value.strip().startswith("{")
                            and add_params.value.strip().endswith("}")
                        ):
                            vis_params = eval(add_params.value)
                        else:
                            vis_params = {}

                        if (
                            palette.value
                            and len(set([red.value, green.value, blue.value])) == 1
                        ):
                            vis_params["colormap_name"] = palette.value
                        elif (
                            palette.value
                            and len(set([red.value, green.value, blue.value])) > 1
                        ):
                            palette.value = None
                            print("Palette can only be set for single band images.")

                        if vmin.value and vmax.value:
                            vis_params["rescale"] = f"{vmin.value},{vmax.value}"

                        if nodata.value:
                            vis_params["nodata"] = nodata.value

                        if file_type.value == "COG":
                            m.add_cog_layer(
                                http_url.value,
                                name=layer_name.value,
                                bands=[red.value, green.value, blue.value],
                                **vis_params,
                            )
                        elif file_type.value == "STAC":
                            m.add_stac_layer(
                                http_url.value,
                                bands=[red.value, green.value, blue.value],
                                name=layer_name.value,
                                **vis_params,
                            )
                        tool_output.outputs = ()
                    except Exception as e:
                        print(e)
                        print("Error loading data.")
                        return

                elif file_type.value == "Microsoft":
                    try:
                        tool_output.outputs = ()
                        print("Loading data...")

                        if (
                            checkbox.value
                            and add_params.value.strip().startswith("{")
                            and add_params.value.strip().endswith("}")
                        ):
                            vis_params = eval(add_params.value)
                        else:
                            vis_params = {}

                        if (
                            palette.value
                            and len(set([red.value, green.value, blue.value])) == 1
                        ) or (palette.value and "expression" in vis_params):
                            vis_params["colormap_name"] = palette.value
                        elif (
                            palette.value
                            and len(set([red.value, green.value, blue.value])) > 1
                            and "expression" not in vis_params
                        ):
                            palette.value = None
                            print("Palette can only be set for single band images.")

                        if vmin.value and vmax.value:
                            vis_params["rescale"] = f"{vmin.value},{vmax.value}"

                        if nodata.value:
                            vis_params["nodata"] = nodata.value

                        col = collection.value.split(" - ")[0]
                        m.add_stac_layer(
                            collection=col,
                            item=items.value,
                            assets=assets.value,
                            name=layer_name.value,
                            **vis_params,
                        )
                        tool_output.outputs = ()
                    except Exception as e:
                        print(e)
                        print("Error loading data.")
                        return

                else:
                    tool_output.outputs = ()
                    print("Please select a file and enter an http URL.")

            m.toolbar_reset()
            m.default_style = {"cursor": "default"}

        elif change["new"] == "Reset":
            file_chooser.reset()
            tool_output.outputs = ()
            http_url.value = ""
            add_params.value = ""
            checkbox.value = False
            palette.value = None
            red.value = None
            green.value = None
            blue.value = None
            vmin.value = ""
            vmax.value = ""
            nodata.value = ""
            collection.value = None
            items.value = ""
            assets.value = ""
            m.toolbar_reset()
        elif change["new"] == "Close":
            if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
                m.remove_control(m.tool_output_ctrl)
                m.tool_output_ctrl = None
                m.toolbar_reset()

        ok_cancel.value = None

    file_type.observe(file_type_changed, names="value")
    ok_cancel.observe(ok_cancel_clicked, names="value")

    m.add(tool_output_ctrl)
    m.tool_output_ctrl = tool_output_ctrl


def change_basemap(m, position: Optional[str] = "topright"):
    """Widget for changing basemaps.

    Args:
        m (object): leafmap.Map.
    """
    from .basemaps import get_xyz_dict
    from .leafmap import basemaps, get_basemap

    xyz_dict = get_xyz_dict()

    value = "OpenStreetMap"

    dropdown = widgets.Dropdown(
        options=list(basemaps.keys()),
        value=value,
        layout=widgets.Layout(width="200px"),
    )

    close_btn = widgets.Button(
        icon="times",
        tooltip="Close the basemap widget",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    basemap_widget = widgets.HBox([dropdown, close_btn])

    def on_click(change):
        if change["new"]:
            basemap_name = dropdown.value
            if basemap_name not in m.get_layer_names():
                m.add_basemap(basemap_name)
                if basemap_name in xyz_dict:
                    if "bounds" in xyz_dict[basemap_name]:
                        bounds = xyz_dict[basemap_name]["bounds"]
                        bounds = [
                            bounds[0][1],
                            bounds[0][0],
                            bounds[1][1],
                            bounds[1][0],
                        ]
                        m.zoom_to_bounds(bounds)

    dropdown.observe(on_click, "value")

    def close_click(change):
        m.toolbar_reset()
        if m.basemap_ctrl is not None and m.basemap_ctrl in m.controls:
            m.remove_control(m.basemap_ctrl)
        basemap_widget.close()

    close_btn.on_click(close_click)

    basemap_control = ipyleaflet.WidgetControl(widget=basemap_widget, position=position)
    m.add(basemap_control)
    m.basemap_ctrl = basemap_control


def save_map(m):
    """Saves the map as HTML, JPG, or PNG.

    Args:
        m (leafmap.Map): The leafmap Map object.
    """
    import time

    tool_output = widgets.Output()
    m.tool_output = tool_output
    tool_output.outputs = ()
    save_map_widget = widgets.VBox()

    save_type = widgets.ToggleButtons(
        options=["HTML", "PNG", "JPG"],
        tooltips=[
            "Save the map as an HTML file",
            "Take a screenshot and save as a PNG file",
            "Take a screenshot and save as a JPG file",
        ],
    )

    file_chooser = FileChooser(
        os.getcwd(), sandbox_path=m.sandbox_path, layout=widgets.Layout(width="454px")
    )
    file_chooser.default_filename = "my_map.html"
    file_chooser.use_dir_icons = True

    ok_cancel = widgets.ToggleButtons(
        value=None,
        options=["OK", "Cancel", "Close"],
        tooltips=["OK", "Cancel", "Close"],
        button_style="primary",
    )

    def save_type_changed(change):
        ok_cancel.value = None
        # file_chooser.reset()
        file_chooser.default_path = os.getcwd()
        if change["new"] == "HTML":
            file_chooser.default_filename = "my_map.html"
        elif change["new"] == "PNG":
            file_chooser.default_filename = "my_map.png"
        elif change["new"] == "JPG":
            file_chooser.default_filename = "my_map.jpg"
        save_map_widget.children = [save_type, file_chooser]

    def chooser_callback(chooser):
        save_map_widget.children = [save_type, file_chooser, ok_cancel]

    def ok_cancel_clicked(change):
        if change["new"] == "OK":
            file_path = file_chooser.selected
            ext = os.path.splitext(file_path)[1]
            if save_type.value == "HTML" and ext.upper() == ".HTML":
                tool_output.outputs = ()
                m.to_html(file_path)
            elif save_type.value == "PNG" and ext.upper() == ".PNG":
                tool_output.outputs = ()
                m.toolbar_button.value = False
                if m.save_map_control is not None:
                    m.remove_control(m.save_map_control)
                    m.save_map_control = None
                time.sleep(2)
                screen_capture(outfile=file_path)
            elif save_type.value == "JPG" and ext.upper() == ".JPG":
                tool_output.outputs = ()
                m.toolbar_button.value = False
                if m.save_map_control is not None:
                    m.remove_control(m.save_map_control)
                    m.save_map_control = None
                time.sleep(2)
                screen_capture(outfile=file_path)
            else:
                label = widgets.Label(
                    value="The selected file extension does not match the selected exporting type."
                )
                save_map_widget.children = [save_type, file_chooser, label]
        elif change["new"] == "Cancel":
            tool_output.outputs = ()
            file_chooser.reset()
        elif change["new"] == "Close":
            if m.save_map_control is not None:
                m.remove_control(m.save_map_control)
                m.save_map_control = None
        ok_cancel.value = None
        m.toolbar_reset()

    save_type.observe(save_type_changed, names="value")
    ok_cancel.observe(ok_cancel_clicked, names="value")

    file_chooser.register_callback(chooser_callback)

    save_map_widget.children = [save_type, file_chooser]
    save_map_control = ipyleaflet.WidgetControl(
        widget=save_map_widget, position="topright"
    )
    m.add(save_map_control)
    m.save_map_control = save_map_control


def split_basemaps(
    m,
    layers_dict: Optional[Dict] = None,
    left_name=None,
    right_name=None,
    width="120px",
    **kwargs,
):
    """Create a split-panel map for visualizing two maps.

    Args:
        m (ipyleaflet.Map): An ipyleaflet map object.
        layers_dict (dict, optional): A dictionary of TileLayers. Defaults to None.
        left_name (str, optional): The default value of the left dropdown list. Defaults to None.
        right_name (str, optional): The default value of the right dropdown list. Defaults to None.
        width (str, optional): The width of the dropdown list. Defaults to "120px".
    """
    from .basemaps import wms_tiles
    from .leafmap import basemaps, get_basemap

    controls = m.controls
    layers = m.layers
    m.clear_controls()

    add_zoom = True
    add_fullscreen = True

    if layers_dict is None:
        keys = []
        tmp_keys = list(basemaps.keys())
        for key in tmp_keys:
            if key not in wms_tiles:
                keys.append(key)
    else:
        keys = list(layers_dict.keys())

    if layers_dict is None:
        if left_name is None:
            left_name = "ROADMAP"
        if right_name is None:
            right_name = "HYBRID"
    else:
        if left_name is None:
            left_name = keys[0]
        if right_name is None:
            right_name = keys[-1]

    if layers_dict is None:
        if isinstance(left_name, str):
            left_layer = get_basemap(left_name)

        if isinstance(right_name, str):
            right_layer = get_basemap(right_name)
    else:
        left_layer = layers_dict[left_name]
        right_layer = layers_dict[right_name]

    control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    m.add(control)
    m.dragging = False

    left_dropdown = widgets.Dropdown(
        options=keys, value=left_name, layout=widgets.Layout(width=width)
    )

    left_control = ipyleaflet.WidgetControl(widget=left_dropdown, position="topleft")
    m.add(left_control)

    right_dropdown = widgets.Dropdown(
        options=keys, value=right_name, layout=widgets.Layout(width=width)
    )

    right_control = ipyleaflet.WidgetControl(widget=right_dropdown, position="topright")
    m.add(right_control)

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        # button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    def close_btn_click(change):
        if change["new"]:
            m.controls = controls
            m.clear_layers()
            m.layers = layers

    close_button.observe(close_btn_click, "value")
    close_control = ipyleaflet.WidgetControl(
        widget=close_button, position="bottomright"
    )
    m.add(close_control)

    if add_zoom:
        m.add(ipyleaflet.ZoomControl())
    if add_fullscreen:
        m.add(ipyleaflet.FullScreenControl())
    m.add(ipyleaflet.ScaleControl(position="bottomleft"))

    split_control = None
    for ctrl in m.controls:
        if isinstance(ctrl, ipyleaflet.SplitMapControl):
            split_control = ctrl
            break

    def left_change(change):
        if layers_dict is None:
            split_control.left_layer.url = get_basemap(left_dropdown.value).url
        else:
            split_control.left_layer.url = layers_dict[left_dropdown.value].url

    left_dropdown.observe(left_change, "value")

    def right_change(change):
        if layers_dict is None:
            split_control.right_layer.url = get_basemap(right_dropdown.value).url
        else:
            split_control.right_layer.url = layers_dict[right_dropdown.value].url

    right_dropdown.observe(right_change, "value")


def time_slider(
    m,
    layers: Optional[Union[Dict, List, str]] = None,
    labels: Optional[List] = None,
    time_interval: Optional[int] = 1,
    position: Optional[str] = "bottomright",
    slider_length: Optional[str] = "150px",
    zoom_to_layer: Optional[bool] = False,
    **kwargs,
):
    """Adds a time slider to the map.

    Args:
        layers (dict, optional): The dictionary containing a set of XYZ tile layers.
        labels (list, optional): The list of labels to be used for the time series. Defaults to None.
        time_interval (int, optional): Time interval in seconds. Defaults to 1.
        position (str, optional): Position to place the time slider, can be any of ['topleft', 'topright', 'bottomleft', 'bottomright']. Defaults to "bottomright".
        slider_length (str, optional): Length of the time slider. Defaults to "150px".
        zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to False.

    """
    import time
    import threading

    bounds = None

    if isinstance(layers, str):
        layers = find_files(layers, ext="*.tif", recursive=False)

    if isinstance(layers, list):
        if zoom_to_layer:
            layer0 = layers[0]
            _, tile_client = get_local_tile_layer(
                layer0,
                return_client=True,
            )

            bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
            bounds = (
                bounds[2],
                bounds[0],
                bounds[3],
                bounds[1],
            )  # [minx, miny, maxx, maxy]
            m.zoom_to_bounds(bounds)

        layers = images_to_tiles(layers, names=labels, **kwargs)

    if not isinstance(layers, dict):
        raise TypeError("The layers must be a dictionary.")

    if len(layers) == 0:
        layers = planet_monthly_tiles()

    if labels is None:
        labels = list(layers.keys())
    if len(labels) != len(layers):
        raise ValueError("The length of labels is not equal to that of layers.")

    slider = widgets.IntSlider(
        min=1,
        max=len(labels),
        readout=False,
        continuous_update=False,
        layout=widgets.Layout(width=slider_length),
    )
    label = widgets.Label(
        value=labels[0], layout=widgets.Layout(padding="0px 5px 0px 5px")
    )

    play_btn = widgets.Button(
        icon="play",
        tooltip="Play the time slider",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    pause_btn = widgets.Button(
        icon="pause",
        tooltip="Pause the time slider",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    close_btn = widgets.Button(
        icon="times",
        tooltip="Close the time slider",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    play_chk = widgets.Checkbox(value=False)

    slider_widget = widgets.HBox([label, slider, play_btn, pause_btn, close_btn])

    def play_click(b):
        play_chk.value = True

        def work(slider):
            while play_chk.value:
                if slider.value < len(labels):
                    slider.value += 1
                else:
                    slider.value = 1
                time.sleep(time_interval)

        thread = threading.Thread(target=work, args=(slider,))
        thread.start()

    def pause_click(b):
        play_chk.value = False

    play_btn.on_click(play_click)
    pause_btn.on_click(pause_click)

    keys = list(layers.keys())
    layer = layers[keys[0]]
    m.add(layer)

    def slider_changed(change):
        m.default_style = {"cursor": "wait"}
        index = slider.value - 1
        label.value = labels[index]
        layer.url = layers[label.value].url
        layer.name = layers[label.value].name
        m.default_style = {"cursor": "default"}

    slider.observe(slider_changed, "value")

    def close_click(b):
        play_chk.value = False
        m.toolbar_reset()

        if m.slider_ctrl is not None and m.slider_ctrl in m.controls:
            m.remove_control(m.slider_ctrl)
        slider_widget.close()

    close_btn.on_click(close_click)

    slider_ctrl = ipyleaflet.WidgetControl(widget=slider_widget, position=position)
    m.add(slider_ctrl)
    m.slider_ctrl = slider_ctrl


def census_widget(m):
    """Widget for adding US Census data.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    # from owslib.wms import WebMapService

    census_dict = get_census_dict()
    m.add_census_data("Census 2020", "States")

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="filter",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    wms = widgets.Dropdown(
        options=census_dict.keys(),
        value="Census 2020",
        description="WMS:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    layer = widgets.Dropdown(
        options=census_dict["Census 2020"]["layers"],
        value="States",
        description="Layer:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    checkbox = widgets.Checkbox(
        description="Replace existing census data layer",
        value=True,
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    # output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        wms,
        layer,
        checkbox,
        # output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def wms_change(change):
        layer.options = census_dict[change["new"]]["layers"]
        layer.value = layer.options[0]

    wms.observe(wms_change, "value")

    def layer_change(change):
        if change["new"] != "":
            if checkbox.value:
                m.layers = m.layers[:-1]
            m.add_census_data(wms.value, layer.value)

            # with output:
            #     w = WebMapService(census_dict[wms.value]["url"])
            #     output.outputs = ()
            #     print(w[layer.value].abstract)

    layer.observe(layer_change, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def search_basemaps(m):
    """The widget for search XYZ tile services.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import xyzservices.providers as xyz
    from xyzservices import TileProvider

    layers = m.layers

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="search",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    checkbox = widgets.Checkbox(
        description="Search Quick Map Services (QMS)",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    providers = widgets.Dropdown(
        options=[],
        value=None,
        description="XYZ Tile:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    keyword = widgets.Text(
        value="",
        description="Search keyword:",
        placeholder="OpenStreetMap",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    def search_callback(change):
        providers.options = []
        if keyword.value != "":
            tiles = search_xyz_services(keyword=keyword.value)
            if checkbox.value:
                tiles = tiles + search_qms(keyword=keyword.value)
            providers.options = tiles

    keyword.on_submit(search_callback)

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Search", "Reset", "Close"],
        tooltips=["Search", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    def providers_change(change):
        if change["new"] != "":
            provider = change["new"]
            if provider is not None:
                if provider.startswith("qms"):
                    with output:
                        output.outputs = ()
                        print("Adding data. Please wait...")
                    name = provider[4:]
                    qms_provider = TileProvider.from_qms(name)
                    url = qms_provider.build_url()
                    attribution = qms_provider.attribution
                    m.layers = layers
                    m.add_tile_layer(url, name, attribution)
                    output.outputs = ()
                elif provider.startswith("xyz"):
                    name = provider[4:]
                    xyz_provider = xyz.flatten()[name]
                    url = xyz_provider.build_url()
                    attribution = xyz_provider.attribution
                    m.layers = layers
                    if xyz_provider.requires_token():
                        with output:
                            output.outputs = ()
                            print(f"{provider} requires an API Key.")
                    m.add_tile_layer(url, name, attribution)

    providers.observe(providers_change, "value")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        checkbox,
        keyword,
        providers,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Search":
            providers.options = []
            if keyword.value != "":
                tiles = search_xyz_services(keyword=keyword.value)
                if checkbox.value:
                    tiles = tiles + search_qms(keyword=keyword.value)
                providers.options = tiles
            with output:
                output.outputs = ()
                # print("Running ...")
        elif change["new"] == "Reset":
            keyword.value = ""
            providers.options = []
            output.outputs = ()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def download_osm(m):
    """Widget for downloading OSM data.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gear",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    checkbox = widgets.Checkbox(
        description="Checkbox",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    dropdown = widgets.Dropdown(
        options=["Option 1", "Option 2", "Option 3"],
        value=None,
        description="Dropdown:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    int_slider = widgets.IntSlider(
        min=1,
        max=100,
        description="Int Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style=style,
    )

    int_slider_label = widgets.Label()

    # widgets.jslink((int_slider, "value"), (int_slider_label, "value"))
    def int_slider_changed(change):
        if change["new"]:
            int_slider_label.value = str(int_slider.value)

    int_slider.observe(int_slider_changed, "value")

    float_slider = widgets.FloatSlider(
        min=1,
        max=100,
        description="Float Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style=style,
    )

    float_slider_label = widgets.Label()

    # widgets.jslink((float_slider, "value"), (float_slider_label, "value"))
    def float_slider_changed(change):
        if change["new"]:
            float_slider_label.value = str(float_slider.value)

    float_slider.observe(float_slider_changed, "value")

    color = widgets.ColorPicker(
        concise=False,
        description="Color:",
        value="white",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    text = widgets.Text(
        value="",
        description="Textbox:",
        placeholder="Placeholder",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    textarea = widgets.Textarea(
        placeholder="Placeholder",
        layout=widgets.Layout(width=widget_width),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"
    buttons.style.button_padding = "0px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        checkbox,
        widgets.HBox([int_slider, int_slider_label]),
        widgets.HBox([float_slider, float_slider_label]),
        dropdown,
        text,
        color,
        textarea,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.outputs = ()
                print("Running ...")
        elif change["new"] == "Reset":
            textarea.value = ""
            output.outputs = ()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def inspector_gui(
    m,
    position: Optional[str] = "topright",
    opened: Optional[bool] = True,
):
    """Generates a tool GUI template using ipywidgets.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import pandas as pd

    widget_width = "250px"
    padding = "0px 5px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    if m is not None:
        marker_cluster = ipyleaflet.MarkerCluster(name="Inspector Markers")
        setattr(m, "pixel_values", [])
        setattr(m, "marker_cluster", marker_cluster)

        if not hasattr(m, "interact_mode"):
            setattr(m, "interact_mode", False)

        if not hasattr(m, "inspector_output"):
            inspector_output = widgets.Output(
                layout=widgets.Layout(width=widget_width, padding="0px 5px 5px 5px")
            )
            setattr(m, "inspector_output", inspector_output)

        output = m.inspector_output
        output.outputs = ()

        if not hasattr(m, "inspector_add_marker"):
            inspector_add_marker = widgets.Checkbox(
                description="Add Marker at clicked location",
                value=True,
                indent=False,
                layout=widgets.Layout(padding=padding, width=widget_width),
            )
            setattr(m, "inspector_add_marker", inspector_add_marker)
        add_marker = m.inspector_add_marker

        if not hasattr(m, "inspector_bands_chk"):
            inspector_bands_chk = widgets.Checkbox(
                description="Get pixel value for visible bands only",
                indent=False,
                layout=widgets.Layout(padding=padding, width=widget_width),
            )
            setattr(m, "inspector_bands_chk", inspector_bands_chk)
        bands_chk = m.inspector_bands_chk

        if not hasattr(m, "inspector_class_label"):
            inspector_label = widgets.Text(
                value="",
                description="Class label:",
                placeholder="Add a label to the marker",
                style=style,
                layout=widgets.Layout(width=widget_width, padding=padding),
            )
            setattr(m, "inspector_class_label", inspector_label)
        label = m.inspector_class_label

        options = []
        if hasattr(m, "cog_layer_dict"):
            options = list(m.cog_layer_dict.keys())
            options.sort()
        if len(options) == 0:
            default_option = None
        else:
            default_option = options[0]
        if not hasattr(m, "inspector_dropdown"):
            inspector_dropdown = widgets.Dropdown(
                options=options,
                value=default_option,
                description="Select a layer:",
                layout=widgets.Layout(width=widget_width, padding=padding),
                style=style,
            )
            setattr(m, "inspector_dropdown", inspector_dropdown)

        dropdown = m.inspector_dropdown

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="info",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Download", "Reset", "Close"],
        tooltips=["Download", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    if len(options) == 0:
        with output:
            print("No COG/STAC layers available")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        add_marker,
        label,
        dropdown,
        bands_chk,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def chk_change(change):
        if hasattr(m, "pixel_values"):
            m.pixel_values = []
        if hasattr(m, "marker_cluster"):
            m.marker_cluster.markers = []
        output.outputs = ()

    bands_chk.observe(chk_change, "value")

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if hasattr(m, "inspector_mode"):
                    delattr(m, "inspector_mode")
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.default_style = {"cursor": "default"}

                m.marker_cluster.markers = []
                m.pixel_values = []
                marker_cluster_layer = m.find_layer("Inspector Markers")
                if marker_cluster_layer is not None:
                    m.remove_layer(marker_cluster_layer)

                if hasattr(m, "pixel_values"):
                    delattr(m, "pixel_values")

                if hasattr(m, "marker_cluster"):
                    delattr(m, "marker_cluster")

            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Download":
            with output:
                output.outputs = ()
                if len(m.pixel_values) == 0:
                    print(
                        "No pixel values available. Click on the map to start collection data."
                    )
                else:
                    print("Downloading pixel values...")
                    df = pd.DataFrame(m.pixel_values)
                    temp_csv = temp_file_path("csv")
                    df.to_csv(temp_csv, index=False)
                    link = create_download_link(temp_csv)
                    with output:
                        output.outputs = ()
                        display(link)
        elif change["new"] == "Reset":
            label.value = ""
            output.outputs = ()
            if hasattr(m, "pixel_values"):
                m.pixel_values = []
            if hasattr(m, "marker_cluster"):
                m.marker_cluster.markers = []
        elif change["new"] == "Close":
            if m is not None:
                if hasattr(m, "inspector_mode"):
                    delattr(m, "inspector_mode")
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.default_style = {"cursor": "default"}
                m.marker_cluster.markers = []
                marker_cluster_layer = m.find_layer("Inspector Markers")
                if marker_cluster_layer is not None:
                    m.remove_layer(marker_cluster_layer)
                m.pixel_values = []

                if hasattr(m, "pixel_values"):
                    delattr(m, "pixel_values")

                if hasattr(m, "marker_cluster"):
                    delattr(m, "marker_cluster")

            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = opened

    def handle_interaction(**kwargs):
        latlon = kwargs.get("coordinates")
        lat = round(latlon[0], 4)
        lon = round(latlon[1], 4)
        if (
            kwargs.get("type") == "click"
            and hasattr(m, "inspector_mode")
            and m.inspector_mode
        ):
            m.default_style = {"cursor": "wait"}

            with output:
                output.outputs = ()
                print("Getting pixel value ...")

                layer_dict = m.cog_layer_dict[dropdown.value]

            if layer_dict["type"] == "STAC":
                if bands_chk.value:
                    assets = layer_dict["assets"]
                else:
                    assets = None

                result = stac_pixel_value(
                    lon,
                    lat,
                    layer_dict["url"],
                    layer_dict["collection"],
                    layer_dict["item"],
                    assets,
                    layer_dict["titiler_endpoint"],
                    verbose=False,
                )

                if result is not None:
                    with output:
                        output.clear_output()
                        print(f"lat, lon: {lat:.4f}, {lon:.4f}\n")
                        for key in result:
                            print(f"{key}: {result[key]}")

                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["label"] = label.value
                        m.pixel_values.append(result)
                    if add_marker.value:
                        markers = list(m.marker_cluster.markers)
                        markers.append(ipyleaflet.Marker(location=latlon))
                        m.marker_cluster.markers = markers

                else:
                    with output:
                        output.clear_output()
                        print("No pixel value available")
                        bounds = m.cog_layer_dict[m.inspector_dropdown.value]["bounds"]
                        m.zoom_to_bounds(bounds)
            elif layer_dict["type"] == "COG":

                if m.inspector_bands_chk.value:
                    indexes = layer_dict["indexes"]
                else:
                    indexes = list(range(1, len(layer_dict["band_names"]) + 1))

                result = cog_pixel_value(
                    lon, lat, layer_dict["url"], indexes, verbose=False
                )
                if result is not None:
                    with output:
                        output.clear_output()
                        print(f"lat, lon: {lat:.4f}, {lon:.4f}\n")
                        for key in result:
                            print(f"{key}: {result[key]}")

                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["label"] = label.value
                        m.pixel_values.append(result)
                    if add_marker.value:
                        markers = list(m.marker_cluster.markers)
                        markers.append(ipyleaflet.Marker(location=latlon))
                        m.marker_cluster.markers = markers
                else:
                    with output:
                        output.outputs = ()
                        print("No pixel value available")
                        bounds = m.cog_layer_dict[m.inspector_dropdown.value]["bounds"]
                        m.zoom_to_bounds(bounds)

            elif layer_dict["type"] == "LOCAL":
                try:
                    data = local_tile_pixel_value(
                        lon, lat, layer_dict["tile_client"], verbose=False
                    )

                    result = {}
                    band_names = data.band_names
                    values = data.array.data.tolist()
                    for i, band in enumerate(band_names):
                        result[band] = values[i]

                    if m.inspector_bands_chk.value:
                        vis_bands = m.cog_layer_dict[m.inspector_dropdown.value][
                            "vis_bands"
                        ]
                        new_result = {}
                        for key in result:
                            if key in vis_bands:
                                new_result[key] = result[key]
                        result = new_result

                    with output:
                        output.clear_output()
                        print(f"lat, lon: {lat:.4f}, {lon:.4f}\n")
                        for key in result:
                            print(f"{key}: {result[key]}")

                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["label"] = label.value
                        m.pixel_values.append(result)
                    if add_marker.value:
                        markers = list(m.marker_cluster.markers)
                        markers.append(ipyleaflet.Marker(location=latlon))
                        m.marker_cluster.markers = markers

                except Exception as e:
                    with output:
                        output.clear_output()
                        print(e)
                        bounds = m.cog_layer_dict[m.inspector_dropdown.value]["bounds"]
                        m.zoom_to_bounds(bounds)

            m.default_style = {"cursor": "crosshair"}

    if m is not None:
        if not hasattr(m, "marker_cluster"):
            setattr(m, "marker_cluster", marker_cluster)
        m.add(marker_cluster)

        if not m.interact_mode:
            m.on_interaction(handle_interaction)
            m.interact_mode = True

    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position=position
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control

        if not hasattr(m, "inspector_mode"):
            if hasattr(m, "cog_layer_dict"):
                setattr(m, "inspector_mode", True)
            else:
                setattr(m, "inspector_mode", False)

    else:
        return toolbar_widget


def plotly_toolbar(
    canvas,
):
    """Creates the main toolbar and adds it to the map.

    Args:
        m (plotlymap.Map): The plotly Map object.
    """
    m = canvas.map
    map_min_width = canvas.map_min_width
    map_max_width = canvas.map_max_width
    map_refresh = canvas.map_refresh
    map_widget = canvas.map_widget

    if not map_refresh:
        width = int(map_min_width.replace("%", ""))
        if width > 90:
            map_min_width = "90%"

    tools = {
        "map": {
            "name": "basemap",
            "tooltip": "Change basemap",
        },
        "search": {
            "name": "search_xyz",
            "tooltip": "Search XYZ tile services",
        },
        "gears": {
            "name": "whitebox",
            "tooltip": "WhiteboxTools for local geoprocessing",
        },
        "folder-open": {
            "name": "vector",
            "tooltip": "Open local vector/raster data",
        },
        "picture-o": {
            "name": "raster",
            "tooltip": "Open COG/STAC dataset",
        },
        "question": {
            "name": "help",
            "tooltip": "Get help",
        },
    }

    icons = list(tools.keys())
    tooltips = [item["tooltip"] for item in list(tools.values())]

    icon_width = "32px"
    icon_height = "32px"
    n_cols = 3
    n_rows = math.ceil(len(icons) / n_cols)

    toolbar_grid = widgets.GridBox(
        children=[
            widgets.ToggleButton(
                layout=widgets.Layout(
                    width="auto", height="auto", padding="0px 0px 0px 4px"
                ),
                button_style="primary",
                icon=icons[i],
                tooltip=tooltips[i],
            )
            for i in range(len(icons))
        ],
        layout=widgets.Layout(
            width="115px",
            grid_template_columns=(icon_width + " ") * n_cols,
            grid_template_rows=(icon_height + " ") * n_rows,
            grid_gap="1px 1px",
            padding="5px",
        ),
    )
    canvas.toolbar = toolbar_grid

    def tool_callback(change):
        if change["new"]:
            current_tool = change["owner"]
            for tool in toolbar_grid.children:
                if tool is not current_tool:
                    tool.value = False
            tool = change["owner"]
            tool_name = tools[tool.icon]["name"]
            canvas.container_widget.children = []

            if tool_name == "basemap":
                plotly_basemap_gui(canvas)
            elif tool_name == "search_xyz":
                plotly_search_basemaps(canvas)
            elif tool_name == "whitebox":
                plotly_whitebox_gui(canvas)
            elif tool_name == "vector":
                plotly_tool_template(canvas)
            elif tool_name == "raster":
                plotly_tool_template(canvas)
            elif tool_name == "help":
                import webbrowser

                webbrowser.open_new_tab("https://leafmap.org")
                tool.value = False
        else:
            canvas.container_widget.children = []
            map_widget.layout.width = map_max_width

    for tool in toolbar_grid.children:
        tool.observe(tool_callback, "value")

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="wrench",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )
    canvas.toolbar_button = toolbar_button

    layers_button = widgets.ToggleButton(
        value=False,
        tooltip="Layers",
        icon="server",
        layout=widgets.Layout(height="28px", width="72px"),
    )
    canvas.layers_button = layers_button

    toolbar_widget = widgets.VBox(layout=widgets.Layout(overflow="hidden"))
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox(layout=widgets.Layout(overflow="hidden"))
    toolbar_header.children = [layers_button, toolbar_button]
    toolbar_footer = widgets.VBox(layout=widgets.Layout(overflow="hidden"))
    toolbar_footer.children = [toolbar_grid]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            # map_widget.layout.width = "85%"
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                layers_button.value = False
                # map_widget.layout.width = map_max_width

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            map_widget.layout.width = map_min_width
            if map_refresh:
                with map_widget:
                    map_widget.outputs = ()
                    display(m)
            layers_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            canvas.toolbar_reset()
            map_widget.layout.width = map_max_width
            if not layers_button.value:
                toolbar_widget.children = [toolbar_button]
            if map_refresh:
                with map_widget:
                    map_widget.outputs = ()
                    display(m)

    toolbar_button.observe(toolbar_btn_click, "value")

    def layers_btn_click(change):
        if change["new"]:
            layer_names = list(m.get_layers().keys())
            layers_hbox = []
            all_layers_chk = widgets.Checkbox(
                value=True,
                description="All layers on/off",
                indent=False,
                layout=widgets.Layout(height="18px", padding="0px 8px 25px 8px"),
            )
            all_layers_chk.layout.width = "30ex"
            layers_hbox.append(all_layers_chk)

            layer_chk_dict = {}

            for name in layer_names:
                if name in m.get_tile_layers():
                    index = m.find_layer_index(name)
                    layer = m.layout.mapbox.layers[index]
                elif name in m.get_data_layers():
                    index = m.find_layer_index(name)
                    layer = m.data[index]

                layer_chk = widgets.Checkbox(
                    value=layer.visible,
                    description=name,
                    indent=False,
                    layout=widgets.Layout(height="18px"),
                )
                layer_chk.layout.width = "25ex"
                layer_chk_dict[name] = layer_chk

                if hasattr(layer, "opacity"):
                    opacity = layer.opacity
                elif hasattr(layer, "marker"):
                    opacity = layer.marker.opacity
                else:
                    opacity = 1.0

                layer_opacity = widgets.FloatSlider(
                    value=opacity,
                    description_tooltip=name,
                    min=0,
                    max=1,
                    step=0.01,
                    readout=False,
                    layout=widgets.Layout(width="80px"),
                )

                layer_settings = widgets.ToggleButton(
                    icon="gear",
                    tooltip=name,
                    layout=widgets.Layout(
                        width="25px", height="25px", padding="0px 0px 0px 5px"
                    ),
                )

                def layer_chk_change(change):
                    if change["new"]:
                        m.set_layer_visibility(change["owner"].description, True)
                    else:
                        m.set_layer_visibility(change["owner"].description, False)

                layer_chk.observe(layer_chk_change, "value")

                def layer_opacity_change(change):
                    if change["new"]:
                        m.set_layer_opacity(
                            change["owner"].description_tooltip, change["new"]
                        )

                layer_opacity.observe(layer_opacity_change, "value")

                hbox = widgets.HBox(
                    [layer_chk, layer_settings, layer_opacity],
                    layout=widgets.Layout(padding="0px 8px 0px 8px"),
                )
                layers_hbox.append(hbox)

            def all_layers_chk_changed(change):
                if change["new"]:
                    for name in layer_names:
                        m.set_layer_visibility(name, True)
                        layer_chk_dict[name].value = True
                else:
                    for name in layer_names:
                        m.set_layer_visibility(name, False)
                        layer_chk_dict[name].value = False

            all_layers_chk.observe(all_layers_chk_changed, "value")

            toolbar_footer.children = layers_hbox
            toolbar_button.value = False
        else:
            toolbar_footer.children = [toolbar_grid]

    layers_button.observe(layers_btn_click, "value")

    return toolbar_widget


def plotly_tool_template(canvas):
    container_widget = canvas.container_widget
    map_widget = canvas.map_widget
    map_width = "70%"
    map_widget.layout.width = map_width

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    # style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gears",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )
    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))
    with output:
        print("To be implemented")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            map_widget.layout.width = map_width
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False
                map_widget.layout.width = canvas.map_max_width

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            map_widget.layout.width = map_width
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]
            map_widget.layout.width = canvas.map_max_width

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            canvas.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    container_widget.children = [toolbar_widget]


def plotly_basemap_gui(canvas, map_min_width="78%", map_max_width="98%"):
    """Widget for changing basemaps.

    Args:
        m (object): leafmap.Map.
    """
    from .plotlymap import basemaps

    m = canvas.map
    layer_count = len(m.layout.mapbox.layers)
    container_widget = canvas.container_widget
    map_widget = canvas.map_widget

    map_widget.layout.width = map_min_width

    value = "Esri.WorldTopoMap"
    m.add_basemap(value)

    dropdown = widgets.Dropdown(
        options=list(basemaps.keys()),
        value=value,
        layout=widgets.Layout(width="200px"),
    )

    close_btn = widgets.Button(
        icon="times",
        tooltip="Close the basemap widget",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    basemap_widget = widgets.HBox([dropdown, close_btn])
    container_widget.children = [basemap_widget]

    def on_click(change):
        basemap_name = change["new"]
        m.layout.mapbox.layers = m.layout.mapbox.layers[:layer_count]
        m.add_basemap(basemap_name)

    dropdown.observe(on_click, "value")

    def close_click(change):
        container_widget.children = []
        basemap_widget.close()
        map_widget.layout.width = map_max_width
        canvas.toolbar_reset()
        canvas.toolbar_button.value = False

    close_btn.on_click(close_click)


def plotly_search_basemaps(canvas):
    """The widget for search XYZ tile services.

    Args:
        m (plotlymap.Map, optional): The Plotly Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import xyzservices.providers as xyz
    from xyzservices import TileProvider

    m = canvas.map
    container_widget = canvas.container_widget
    map_widget = canvas.map_widget
    map_widget.layout.width = "75%"

    # map_widget.layout.width = map_min_width

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="search",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    checkbox = widgets.Checkbox(
        description="Search Quick Map Services (QMS)",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    providers = widgets.Dropdown(
        options=[],
        value=None,
        description="XYZ Tile:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    keyword = widgets.Text(
        value="",
        description="Search keyword:",
        placeholder="OpenStreetMap",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    def search_callback(change):
        providers.options = []
        if keyword.value != "":
            tiles = search_xyz_services(keyword=keyword.value)
            if checkbox.value:
                tiles = tiles + search_qms(keyword=keyword.value)
            providers.options = tiles

    keyword.on_submit(search_callback)

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Search", "Reset", "Close"],
        tooltips=["Search", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    def providers_change(change):
        if change["new"] != "":
            provider = change["new"]
            if provider is not None:
                if provider.startswith("qms"):
                    with output:
                        output.outputs = ()
                        print("Adding data. Please wait...")
                    name = provider[4:]
                    qms_provider = TileProvider.from_qms(name)
                    url = qms_provider.build_url()
                    attribution = qms_provider.attribution
                    m.add_tile_layer(url, name, attribution)
                    output.outputs = ()
                elif provider.startswith("xyz"):
                    name = provider[4:]
                    xyz_provider = xyz.flatten()[name]
                    url = xyz_provider.build_url()
                    attribution = xyz_provider.attribution
                    if xyz_provider.requires_token():
                        with output:
                            output.outputs = ()
                            print(f"{provider} requires an API Key.")
                    m.add_tile_layer(url, name, attribution)

    providers.observe(providers_change, "value")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        checkbox,
        keyword,
        providers,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            canvas.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Search":
            providers.options = []
            output.outputs = ()
            if keyword.value != "":
                tiles = search_xyz_services(keyword=keyword.value)
                if checkbox.value:
                    tiles = tiles + search_qms(keyword=keyword.value)
                providers.options = tiles
            else:
                with output:
                    print("Please enter a search keyword.")
        elif change["new"] == "Reset":
            keyword.value = ""
            providers.options = []
            output.outputs = ()
        elif change["new"] == "Close":
            canvas.toolbar_reset()
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    container_widget.children = [toolbar_widget]


def plotly_whitebox_gui(canvas):
    """Display a GUI for the whitebox tool.

    Args:
        canvas (plotlymap.Canvas): Map canvas.
    """
    import whiteboxgui.whiteboxgui as wbt

    container_widget = canvas.container_widget
    map_widget = canvas.map_widget
    map_width = "25%"
    map_widget.layout.width = map_width

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    # style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gears",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )
    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    tools_dict = wbt.get_wbt_dict()
    wbt_toolbox = wbt.build_toolbox(
        tools_dict,
        max_width="800px",
        max_height="500px",
        sandbox_path=os.getcwd(),
    )

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        wbt_toolbox,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            map_widget.layout.width = map_width
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False
                map_widget.layout.width = canvas.map_max_width

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            map_widget.layout.width = map_width
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]
            map_widget.layout.width = canvas.map_max_width

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            canvas.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    container_widget.children = [toolbar_widget]


def search_geojson_gui(m):
    """Generates a tool GUI template using ipywidgets.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    if len(m.geojson_layers) > 0:
        geojson_layer_group = ipyleaflet.LayerGroup()
        for geojson_layer in m.geojson_layers:
            geojson_layer_group.add(geojson_layer)
        if not hasattr(m, "geojson_layer_group"):
            setattr(m, "geojson_layer_group", geojson_layer_group)
        else:
            m.geojson_layer_group = geojson_layer_group

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="search-plus",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    layer_options = []
    if len(m.geojson_layers) > 0:
        layer_options = [layer.name for layer in m.geojson_layers]

    layers = widgets.Dropdown(
        options=layer_options,
        value=None,
        description="Layer:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    attributes = widgets.Dropdown(
        options=[],
        value=None,
        description="Attribute:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    if len(m.geojson_layers) == 0:
        with output:
            print("Please add vector data layers to the map before using this tool.")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        layers,
        attributes,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def layer_change(change):
        if change["new"]:
            for layer in m.geojson_layers:
                if layer.name == change["new"]:
                    df = geojson_to_df(layer.data)
                    attributes.options = list(df.columns)

    layers.observe(layer_change, names="value")

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                if len(m.geojson_layers) > 0 and m.search_control is not None:
                    m.search_control.marker.visible = False
                    m.remove_control(m.search_control)
                    m.search_control = None
                    m.geojson_layer_group.clear_layers()
                    delattr(m, "geojson_layer_group")

            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            if len(m.geojson_layers) > 0 and attributes.value is not None:
                if m.search_control is None:
                    geojson_control = ipyleaflet.SearchControl(
                        position="topleft",
                        layer=m.geojson_layer_group,
                        property_name=attributes.value,
                        marker=ipyleaflet.Marker(
                            icon=ipyleaflet.AwesomeIcon(
                                name="check", marker_color="green", icon_color="darkred"
                            )
                        ),
                    )
                    m.add(geojson_control)
                    m.search_control = geojson_control
                else:
                    m.search_control.property_name = attributes.value
            with output:
                output.outputs = ()
        elif change["new"] == "Reset":
            output.outputs = ()
            layers.value = None
            attributes.value = None

        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                if len(m.geojson_layers) > 0 and m.search_control is not None:
                    m.search_control.marker.visible = False
                    m.remove_control(m.search_control)
                    m.search_control = None
                    if hasattr(m, "geojson_layer_group"):
                        m.geojson_layer_group.clear_layers()
                        delattr(m, "geojson_layer_group")

            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def select_table_gui(m=None):
    """GUI for selecting layers to display attribute table.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import ipysheet

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="table",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    layer_options = []
    if len(m.geojson_layers) > 0:
        layer_options = [layer.name for layer in m.geojson_layers]

    layers = widgets.Dropdown(
        options=layer_options,
        value=None,
        description="Layer:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    if len(m.geojson_layers) == 0:
        with output:
            print("Please add vector data layers to the map before using this tool.")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        layers,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None

            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            if len(m.geojson_layers) > 0 and layers.value is not None:
                if hasattr(m, "table_control"):
                    m.remove_control(m.table_control)
                lyr_index = layers.options.index(layers.value)
                data = m.geojson_layers[lyr_index].data
                df = geojson_to_df(data)
                show_table_gui(m, df)
        elif change["new"] == "Reset":
            output.outputs = ()
            layers.value = None

        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None

            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def show_table_gui(m, df):
    """Open the attribute table GUI.

    Args:
        m (leafmap.Map, optional): The leaflet Map object

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import ipysheet

    widget_width = "560px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    # style = {"description_width": "initial"}

    sheet = ipysheet.from_dataframe(df.head(10))

    output = widgets.Output(
        layout=widgets.Layout(
            width=widget_width,
            padding=padding,
        )
    )

    checkbox = widgets.Checkbox(
        description="Show all rows",
        indent=False,
        layout=widgets.Layout(padding=padding, width="115px"),
    )

    sheet.layout.width = output.layout.width

    def checkbox_clicked(change):
        output.outputs = ()

        if change["new"]:
            sheet = ipysheet.from_dataframe(df)
        else:
            sheet = ipysheet.from_dataframe(df.head(10))

        sheet.layout.max_width = output.layout.width
        output.layout.max_height = str(int(m.layout.height[:-2]) - 220) + "px"
        sheet.layout.max_height = output.layout.height
        if sheet.layout.height > output.layout.max_height:
            sheet.layout.height = output.layout.max_height
        with output:
            display(sheet)

    checkbox.observe(checkbox_clicked, "value")

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Minimize window",
        icon="window-minimize",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    toolbar_widget = widgets.VBox()
    m.table_widget = toolbar_widget
    m.table_output = output

    reset_btn = widgets.Button(
        tooltip="Reset the plot",
        icon="home",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 0px"),
    )

    def reset_btn_clicked(b):
        output.layout.width = widget_width
        output.layout.max_height = str(int(m.layout.height[:-2]) - 220) + "px"

    reset_btn.on_click(reset_btn_clicked)

    fullscreen_btn = widgets.Button(
        tooltip="Fullscreen the attribute table",
        icon="arrows-alt",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 0px"),
    )

    def fullscreen_btn_clicked(b):
        output.layout.width = "1000px"
        output.layout.max_height = str(int(m.layout.height[:-2]) - 220) + "px"

        sheet.layout.width = output.layout.width
        with output:
            output.outputs = ()
            display(sheet)

    fullscreen_btn.on_click(fullscreen_btn_clicked)

    width_btn = widgets.Button(
        tooltip="Change table width",
        icon="arrows-h",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 0px"),
    )

    height_btn = widgets.Button(
        tooltip="Change table height",
        icon="arrows-v",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 0px"),
    )

    width_slider = widgets.IntSlider(
        value=560,
        min=550,
        max=1500,
        step=10,
        description="",
        readout=False,
        continuous_update=False,
        layout=widgets.Layout(width="100px", padding=padding),
        style={"description_width": "initial"},
    )

    width_slider_label = widgets.Label(
        value="560", layout=widgets.Layout(padding="0px 10px 0px 0px")
    )
    # widgets.jslink((width_slider, "value"), (width_slider_label, "value"))

    def width_changed(change):
        if change["new"]:
            width_slider_label.value = str(width_slider.value)
            output.layout.width = str(width_slider.value) + "px"

            if checkbox.value:
                sheet = ipysheet.from_dataframe(df)
            else:
                sheet = ipysheet.from_dataframe(df.head(10))
            sheet.layout.width = output.layout.width
            with output:
                output.outputs = ()
                display(sheet)

    width_slider.observe(width_changed, "value")

    height_slider = widgets.IntSlider(
        value=250,
        min=200,
        max=1000,
        step=10,
        description="",
        readout=False,
        continuous_update=False,
        layout=widgets.Layout(width="100px", padding=padding),
        style={"description_width": "initial"},
    )

    height_slider_label = widgets.Label(value="250")
    # widgets.jslink((height_slider, "value"), (height_slider_label, "value"))

    def height_changed(change):
        if change["new"]:
            height_slider_label.value = str(height_slider.value)
            output.layout.max_height = str(height_slider.value) + "px"
            if checkbox.value:
                sheet = ipysheet.from_dataframe(df)
            else:
                sheet = ipysheet.from_dataframe(df.head(10))

            sheet.layout.height = output.layout.max_height
            with output:
                output.outputs = ()
                display(sheet)

    height_slider.observe(height_changed, "value")

    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [
        close_button,
        toolbar_button,
        reset_btn,
        fullscreen_btn,
        width_btn,
        width_slider,
        width_slider_label,
        height_btn,
        height_slider,
        height_slider_label,
        checkbox,
    ]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            toolbar_button.icon = "window-minimize"
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False
                toolbar_button.icon = "window-maximize"

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            toolbar_button.icon = "window-minimize"
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.icon = "window-maximize"

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.table_control is not None and m.table_control in m.controls:
                    m.remove_control(m.table_control)
                    m.table_control = None
                    delattr(m, "table_control")

            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    with output:
        display(sheet)

    toolbar_button.value = True
    if m is not None:
        table_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if table_control not in m.controls:
            m.add(table_control)
            m.table_control = table_control
    else:
        return toolbar_widget


def edit_draw_gui(m):
    """Generates a tool GUI for editing vector data attribute table.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import ipysheet
    import pandas as pd

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}
    m.edit_mode = True

    n_props = len(m.get_draw_props())
    if n_props == 0:
        n_props = 1

    if "MAX_PROPS" in os.environ:
        max_props = int(os.environ["MAX_PROPS"])
    else:
        max_props = n_props + 10

    sheet = ipysheet.from_dataframe(m.get_draw_props(n_props, return_df=True))
    m.edit_sheet = sheet

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))
    m.edit_output = output

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Edit attribute table",
        icon="pencil-square-o",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    open_button = widgets.ToggleButton(
        value=False,
        tooltip="Open vector data",
        icon="folder-open",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    save_button = widgets.ToggleButton(
        value=False,
        tooltip="Save to file",
        icon="floppy-o",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    refresh_button = widgets.ToggleButton(
        value=False,
        tooltip="Get attribute",
        icon="refresh",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )
    m.edit_refresh = refresh_button

    int_slider = widgets.IntSlider(
        min=n_props,
        max=max_props,
        description="Rows:",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="85px", padding=padding),
        style=style,
    )

    int_slider_label = widgets.Label()

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "64px"

    with output:
        output.outputs = ()
        display(m.edit_sheet)

    def int_slider_changed(change):
        if change["new"]:
            int_slider_label.value = str(int_slider.value)
            m.edit_sheet.rows = int_slider.value
            m.num_attributes = int_slider.value
            with output:
                output.outputs = ()
                m.edit_sheet = ipysheet.from_dataframe(
                    m.get_draw_props(n=int_slider.value, return_df=True)
                )
                display(m.edit_sheet)

    int_slider.observe(int_slider_changed, "value")
    m.num_attributes = int_slider.value

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [
        close_button,
        toolbar_button,
        open_button,
        save_button,
        refresh_button,
        int_slider,
        int_slider_label,
    ]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        output,
        buttons,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.edit_mode = False
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def open_chooser_callback(chooser):
        with output:
            import geopandas as gpd

            gdf = gpd.read_file(chooser.selected)
            geojson = gdf_to_geojson(gdf, epsg=4326, tuple_to_list=True)
            m.draw_control.data = m.draw_control.data + (geojson["features"])
            m.draw_features = m.draw_features + (geojson["features"])
            open_button.value = False

            m.edit_props = gdf.drop(["geometry"], axis=1).columns.tolist()
            int_slider.value = len(m.edit_props)

        if m.open_control in m.controls:
            m.remove_control(m.open_control)
            delattr(m, "open_control")

    def open_btn_click(change):
        if change["new"]:
            save_button.value = False

            open_chooser = FileChooser(
                os.getcwd(),
                sandbox_path=m.sandbox_path,
                layout=widgets.Layout(width="454px"),
            )
            open_chooser.filter_pattern = ["*.shp", "*.geojson", "*.gpkg"]
            open_chooser.use_dir_icons = True
            open_chooser.register_callback(open_chooser_callback)

            open_control = ipyleaflet.WidgetControl(
                widget=open_chooser, position="topright"
            )
            m.add(open_control)
            m.open_control = open_control

    open_button.observe(open_btn_click, "value")

    def chooser_callback(chooser):
        m.save_draw_features(chooser.selected, indent=None)
        if m.file_control in m.controls:
            m.remove_control(m.file_control)
            delattr(m, "file_control")
        with output:
            print(f"Saved to {chooser.selected}")

    def save_btn_click(change):
        if change["new"]:
            save_button.value = False

            file_chooser = FileChooser(
                os.getcwd(),
                sandbox_path=m.sandbox_path,
                layout=widgets.Layout(width="454px"),
            )
            file_chooser.filter_pattern = ["*.shp", "*.geojson", "*.gpkg"]
            file_chooser.default_filename = "data.geojson"
            file_chooser.use_dir_icons = True
            file_chooser.register_callback(chooser_callback)

            file_control = ipyleaflet.WidgetControl(
                widget=file_chooser, position="topright"
            )
            m.add(file_control)
            m.file_control = file_control

    save_button.observe(save_btn_click, "value")

    def refresh_btn_click(change):
        if change["new"]:
            refresh_button.value = False
            if m.draw_control.last_action == "edited":
                with output:
                    geometries = [
                        feature["geometry"] for feature in m.draw_control.data
                    ]
                    if len(m.draw_features) > 0:
                        if (
                            m.draw_features[-1]["geometry"]
                            == m.draw_control.last_draw["geometry"]
                        ):
                            m.draw_features.pop()
                    for feature in m.draw_features:
                        if feature["geometry"] not in geometries:
                            feature["geometry"] = m.draw_control.last_draw["geometry"]
                            values = []
                            props = ipysheet.to_dataframe(m.edit_sheet)["Key"].tolist()
                            for prop in props:
                                if prop in feature["properties"]:
                                    values.append(feature["properties"][prop])
                                else:
                                    values.append("")
                            df = pd.DataFrame({"Key": props, "Value": values})
                            df.index += 1
                            m.edit_sheet = ipysheet.from_dataframe(df)
                            output.outputs = ()
                            display(m.edit_sheet)

    refresh_button.observe(refresh_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.outputs = ()
                display(m.edit_sheet)
                if len(m.draw_control.data) == 0:
                    print("Please draw a feature first.")
                else:
                    if m.draw_control.last_action == "edited":
                        m.update_draw_features()
                    m.update_draw_props(ipysheet.to_dataframe(m.edit_sheet))
        elif change["new"] == "Reset":
            m.edit_sheet = ipysheet.from_dataframe(
                m.get_draw_props(int_slider.value, return_df=True)
            )
            with output:
                output.outputs = ()
                display(m.edit_sheet)
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.edit_mode = False
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def stac_gui(
    m,
    position: Optional[str] = "topright",
    opened: Optional[bool] = True,
    **kwargs,
):
    """Generates a tool GUI template using ipywidgets.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import pandas as pd

    if os.environ.get("STAC_CATALOGS") is not None:
        try:
            source = eval(os.environ.get("STAC_CATALOGS"))
            m.set_catalog_source(source)
        except Exception as e:
            print(e)
            print("Invalid STAC_CATALOGS environment variable.")

    if hasattr(m, "_STAC_CATALOGS"):
        stac_custom_gui(m, **kwargs)
        return

    widget_width = "450px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}
    MAX_ITEMS = 20
    if "MAX_ITEMS" in os.environ:
        MAX_ITEMS = int(os.environ["MAX_ITEMS"])

    catalog_path = download_data_catalogs()
    aws_open_data_path = os.path.join(catalog_path, "aws_stac_catalogs.tsv")
    gee_path = os.path.join(catalog_path, "gee_catalog.tsv")
    pc_path = os.path.join(catalog_path, "pc_catalog.tsv")
    nasa_path = os.path.join(catalog_path, "nasa_cmr_catalog.tsv")
    stac_index_path = os.path.join(catalog_path, "stac_catalogs.tsv")
    stac_data = []

    stac_info = {
        "AWS Open Data": {
            "filename": aws_open_data_path,
            "name": "Name",
            "url": "Endpoint",
            "description": "Description",
        },
        "Google Earth Engine": {
            "filename": gee_path,
            "name": "id",
            "url": "url",
            "description": "title",
        },
        "Microsoft Planetary Computer": {
            "filename": pc_path,
            "name": "title",
            "url": "link",
            "description": "description",
        },
        "NASA Common Metadata Repository": {
            "filename": nasa_path,
            "name": "id",
            "url": "url",
            "description": "title",
        },
        "STAC Index Catalogs": {
            "filename": stac_index_path,
            "name": "title",
            "url": "url",
            "description": "summary",
        },
        "Custom STAC API Endpoint": {
            "filename": "",
            "name": "",
            "url": "",
            "description": "",
        },
    }

    connections = list(stac_info.keys())

    output = widgets.Output(
        layout=widgets.Layout(width=widget_width, padding=padding, overflow="auto")
    )

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Discver STAC Catalog",
        icon="stack-exchange",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    connection = widgets.Dropdown(
        options=connections,
        value="AWS Open Data",
        description="Catalog:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    df = pd.read_csv(stac_info[connection.value]["filename"], sep="\t")
    datasets = df[stac_info[connection.value]["name"]].tolist()

    dataset = widgets.Dropdown(
        options=datasets,
        value="Sentinel-2 Cloud-Optimized GeoTIFFs",
        description="Dataset:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    description = widgets.Text(
        value="Sentinel-2 Level 2A scenes and metadata",
        description="Description:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    http_url = widgets.Text(
        value="https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a",
        description="URL:",
        tooltip="STAC Catalog URL",
        placeholder="Enter a STAC URL, e.g., https://earth-search.aws.element84.com/v1",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    custom_dataset = widgets.Dropdown(
        options=[],
        value=None,
        description="Dataset:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    start_date = widgets.DatePicker(
        description="Start date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width="225px", padding=padding),
    )
    end_date = widgets.DatePicker(
        description="End date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width="225px", padding=padding),
    )

    collection = widgets.Dropdown(
        options=[],
        value=None,
        description="Collection:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    band_names = ["red", "green", "blue"]

    item = widgets.Dropdown(
        options=[],
        description="Item:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    layer_name = widgets.Text(
        value="STAC Layer",
        description="Layer name:",
        tooltip="Enter a layer name for the selected file",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    band_width = "149px"
    red = widgets.Dropdown(
        options=band_names,
        value="red",
        description="Red:",
        tooltip="Select a band for the red channel",
        style=style,
        layout=widgets.Layout(width=band_width, padding=padding),
    )

    green = widgets.Dropdown(
        options=band_names,
        value="green",
        description="Green:",
        tooltip="Select a band for the green channel",
        style=style,
        layout=widgets.Layout(width="148px", padding=padding),
    )

    blue = widgets.Dropdown(
        options=band_names,
        value="blue",
        description="Blue:",
        tooltip="Select a band for the blue channel",
        style=style,
        layout=widgets.Layout(width=band_width, padding=padding),
    )

    max_items = widgets.Text(
        value="20",
        description="Max items:",
        placeholder="Maximum number of items to return from the STAC API",
        tooltip="Maximum number of items to return from the STAC API",
        style=style,
        layout=widgets.Layout(width="130px", padding=padding),
    )

    vmin = widgets.Text(
        value=None,
        description="vmin:",
        tooltip="Minimum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="100px", padding=padding),
    )

    vmax = widgets.Text(
        value=None,
        description="vmax:",
        tooltip="Maximum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="100px", padding=padding),
    )

    nodata = widgets.Text(
        value=None,
        description="Nodata:",
        tooltip="Nodata the raster to visualize",
        style=style,
        layout=widgets.Layout(width="113px", padding=padding),
    )

    palette_options = list_palettes(lowercase=True)
    palette = widgets.Dropdown(
        options=palette_options,
        value=None,
        description="palette:",
        layout=widgets.Layout(width="180px", padding=padding),
        style=style,
    )

    add_footprints = widgets.Checkbox(
        value=True,
        description="Add footprints",
        indent=False,
        layout=widgets.Layout(width="120px", padding=padding),
        style=style,
    )

    checkbox = widgets.Checkbox(
        value=False,
        description="Additional params",
        indent=False,
        layout=widgets.Layout(width="154px", padding=padding),
        style=style,
    )

    query_params_text = "Additional parameters to query the STAC API, for example: {'query': {'eo:cloud_cover':{'lt':10}}}"
    query_params = widgets.Textarea(
        value="",
        placeholder=query_params_text,
        layout=widgets.Layout(width="454px", padding=padding),
        style=style,
    )

    add_params_text = "Additional parameters to visualize imagery, for example: {'palette': ['#006633', '#E5FFCC', '#662A00', '#D8D8D8', '#F5F5F5'], 'expression': '(SR_B5-SR_B4)/(SR_B5+SR_B4)'}"
    add_params = widgets.Textarea(
        value="",
        placeholder=add_params_text,
        layout=widgets.Layout(width="454px", padding=padding),
        style=style,
    )

    def reset_options(reset_url=True):
        """Reset the options to their default values."""
        connection.value = "AWS Open Data"
        dataset.options = datasets
        dataset.value = "Sentinel-2 Cloud-Optimized GeoTIFFs"
        http_url.value = (
            "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a"
        )
        start_date.value = None
        end_date.value = None
        item.options = []
        item.value = None
        layer_name.value = ""
        red.options = ["red", "green", "blue"]
        green.options = ["red", "green", "blue"]
        blue.options = ["red", "green", "blue"]
        red.value = "red"
        green.value = "green"
        blue.value = "blue"
        max_items.value = "20"
        vmin.value = ""
        vmax.value = ""
        nodata.value = ""
        palette.value = None
        add_params.value = ""
        output.outputs = ()

    params_widget = widgets.VBox()

    raster_options = widgets.VBox()
    raster_options.children = [
        widgets.HBox([red, green, blue]),
        widgets.HBox([palette, add_footprints, checkbox]),
        params_widget,
    ]

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Search", "Display", "Reset", "Close"],
        tooltips=["Get Items", "Display Image", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "65px"

    dataset_widget = widgets.VBox()
    dataset_widget.children = [
        dataset,
        description,
        http_url,
    ]

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        connection,
        dataset_widget,
        widgets.HBox([start_date, end_date]),
        item,
        raster_options,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def update_bands():
        if len(stac_data) > 0:
            bnames = stac_data[0][item.value]["bands"]
        else:
            bnames = []

        red.options = bnames
        green.options = bnames
        blue.options = bnames

        default_bands = set_default_bands(bnames)
        try:
            red.value = default_bands[0]
            green.value = default_bands[1]
            blue.value = default_bands[2]
        except Exception as e:
            red.value = None
            green.value = None
            blue.value = None

    def connection_changed(change):
        if change["new"]:
            if connection.value != "Custom STAC API Endpoint":
                df = pd.read_csv(stac_info[connection.value]["filename"], sep="\t")
                datasets = df[stac_info[connection.value]["name"]].tolist()
                dataset.options = datasets
                dataset.value = datasets[0]
                dataset_widget.children = [dataset, description, http_url]
            else:
                http_url.value = "https://earth-search.aws.element84.com/v1"
                dataset_widget.children = [http_url, custom_dataset]
                with output:
                    print("Enter a STAC API endpoint and press Enter to list datasets")

    connection.observe(connection_changed, names="value")

    def dataset_changed(change):
        if change["new"]:
            if connection.value != "Custom STAC API Endpoint":
                df = pd.read_csv(stac_info[connection.value]["filename"], sep="\t")
                df = df[df[stac_info[connection.value]["name"]] == dataset.value]
                description.value = df[
                    stac_info[connection.value]["description"]
                ].tolist()[0]
                http_url.value = df[stac_info[connection.value]["url"]].tolist()[0]
                item.options = []
                custom_dataset.options = []
                stac_data.clear()
                update_bands()

    dataset.observe(dataset_changed, names="value")

    def http_url_changed(change):
        with output:
            output.outputs = ()
            print("Searching...")
            try:
                if connection.value == "Custom STAC API Endpoint":
                    custom_collections = stac_collections(
                        http_url.value, return_ids=True
                    )
                    if custom_collections:
                        custom_dataset.options = custom_collections

                        collection_id = http_url.value.split("/")[-1]
                        if collection_id in custom_collections:
                            custom_dataset.value = collection_id

                    else:
                        custom_dataset.options = []

                else:
                    custom_cols = stac_collections(http_url.value, return_ids=True)
                    item.options = custom_cols
                    stac_data.clear()
                update_bands()
                output.outputs = ()
            except Exception as e:
                print(e)

    http_url.on_submit(http_url_changed)

    def item_changed(change):
        if change["new"]:
            layer_name.value = item.value
            with output:
                update_bands()

            if dataset.value == "Sentinel-2 Cloud-Optimized GeoTIFFs":
                vmin.value = "0"
                vmax.value = "3000"
            else:
                vmin.value = ""
                vmax.value = ""

    item.observe(item_changed, names="value")

    def checkbox_changed(change):
        if change["new"]:
            params_widget.children = [
                layer_name,
                widgets.HBox([max_items, vmin, vmax, nodata]),
                query_params,
                add_params,
            ]
        else:
            params_widget.children = []

    checkbox.observe(checkbox_changed, names="value")

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Search":
            with output:
                output.outputs = ()
                if http_url.value is not None:
                    if start_date.value is not None and end_date.value is not None:
                        datetime = str(start_date.value) + "/" + str(end_date.value)
                    elif start_date.value is not None:
                        datetime = str(start_date.value) + "/.."
                    elif end_date.value is not None:
                        datetime = "../" + str(end_date.value)
                    else:
                        datetime = None

                    if m is not None:
                        if m.user_roi is not None:
                            intersects = m.user_roi["geometry"]
                        else:
                            intersects = bbox_to_geojson(m.bounds)

                    else:
                        intersects = None

                    if (
                        checkbox.value
                        and query_params.value.strip().startswith("{")
                        and query_params.value.strip().endswith("}")
                    ):
                        query = eval(query_params.value)
                    elif query_params.value.strip() == "":
                        query = {}
                    else:
                        print(
                            "Invalid query parameters. It must be a dictionary with keys such as 'query', 'sortby', 'filter', 'fields'"
                        )
                        query = {}

                print("Retrieving items...")
                try:
                    if connection.value in [
                        "Google Earth Engine",
                        "NASA Common Metadata Repository",
                    ]:
                        output.outputs = ()
                        print(f"{connection.value} is not supported yet.")
                    else:
                        if connection.value == "Custom STAC API Endpoint":
                            search = stac_search(
                                url=http_url.value,
                                max_items=int(max_items.value),
                                intersects=intersects,
                                datetime=datetime,
                                collections=custom_dataset.value,
                                **query,
                            )

                        else:
                            search = stac_search(
                                url=http_url.value,
                                max_items=int(max_items.value),
                                intersects=intersects,
                                datetime=datetime,
                                **query,
                            )
                        search_dict = stac_search_to_dict(search)
                        item.options = list(search_dict.keys())
                        setattr(m, "stac_search", search)
                        setattr(m, "stac_dict", search_dict)
                        setattr(m, "stac_items", stac_search_to_list(search))

                        if add_footprints.value and m is not None:
                            gdf = stac_search_to_gdf(search)
                            style = {
                                "stroke": True,
                                "color": "#000000",
                                "weight": 2,
                                "opacity": 1,
                                "fill": True,
                                "fillColor": "#000000",
                                "fillOpacity": 0,
                            }
                            hover_style = {"fillOpacity": 0.3}
                            m.add_gdf(
                                gdf,
                                style=style,
                                hover_style=hover_style,
                                layer_name="Footprints",
                                zoom_to_layer=False,
                            )
                            setattr(m, "stac_gdf", gdf)

                        stac_data.clear()
                        stac_data.append(search_dict)
                        update_bands()
                        output.outputs = ()
                except NotImplementedError as e:
                    print(e)

                except Exception as e:
                    print(e)

        elif change["new"] == "Display":
            with output:
                output.outputs = ()

                if item.value and m is not None:
                    print("Loading data...")

                    if (
                        checkbox.value
                        and add_params.value.strip().startswith("{")
                        and add_params.value.strip().endswith("}")
                    ):
                        vis_params = eval(add_params.value)
                    else:
                        vis_params = {}

                    if (
                        palette.value
                        and len(set([red.value, green.value, blue.value])) == 1
                    ) or (palette.value and "expression" in vis_params):
                        vis_params["colormap_name"] = palette.value
                    elif (
                        palette.value
                        and len(set([red.value, green.value, blue.value])) > 1
                        and "expression" not in vis_params
                    ):
                        palette.value = None
                        print("Palette can only be set for single band images.")

                    if vmin.value and vmax.value:
                        vis_params["rescale"] = f"{vmin.value},{vmax.value}"

                    if nodata.value:
                        vis_params["nodata"] = nodata.value

                    if len(set([red.value, green.value, blue.value])) == 1:
                        assets = red.value
                    else:
                        assets = f"{red.value},{green.value},{blue.value}"

                    try:
                        if connection.value == "Microsoft Planetary Computer":
                            m.add_stac_layer(
                                collection=http_url.value.split("/")[-1],
                                item=item.value,
                                assets=assets,
                                name=layer_name.value,
                                fit_bounds=False,
                                **vis_params,
                            )
                            setattr(
                                m,
                                "stac_item",
                                m.stac_dict[item.value],
                            )
                            m.stac_item["collection"] = http_url.value.split("/")[-1]

                        else:
                            m.add_stac_layer(
                                url=stac_data[0][item.value]["href"],
                                item=item.value,
                                assets=assets,
                                name=layer_name.value,
                                fit_bounds=False,
                                **vis_params,
                            )
                            setattr(m, "stac_item", m.stac_dict[item.value])
                        output.outputs = ()
                    except Exception as e:
                        print(e)

                else:
                    print("Please click on the search button first.")
                    buttons.value = None

        elif change["new"] == "Reset":
            reset_options()

        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = opened
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position=position
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def stac_custom_gui(m, button_width: Optional[str] = "85px", **kwargs):
    """Generates a tool GUI template using ipywidgets.

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.
        button_width (str, optional): The button width. Defaults to "85px".
        **kwargs: Additional keyword arguments that will be passed to the pystac Client.open() function.

    Returns:
        ipywidgets: The tool GUI widget.
    """

    if hasattr(m, "_STAC_CATALOGS") and isinstance(m._STAC_CATALOGS, dict):
        catalogs = m._STAC_CATALOGS
    else:
        raise ValueError("Please set the STAC catalogs first.")

    if not hasattr(m, "_STAC_COLLECTIONS"):
        m._STAC_COLLECTIONS = {}

    if len(catalogs) == 0:
        raise ValueError("Please set the STAC catalogs first.")

    catalog_ids = list(catalogs.keys())

    widget_width = "450px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}
    MAX_ITEMS = 20
    if "MAX_ITEMS" in os.environ:
        MAX_ITEMS = int(os.environ["MAX_ITEMS"])

    stac_data = []

    output = widgets.Output(
        layout=widgets.Layout(width=widget_width, padding=padding, overflow="auto")
    )

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Discver STAC Catalog",
        icon="stack-exchange",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    catalog = widgets.Dropdown(
        options=catalog_ids,
        value=catalog_ids[0],
        description="Catalog:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    endpoint = widgets.Text(
        value=catalogs[catalog.value],
        description="URL:",
        tooltip="STAC Catalog URL",
        placeholder="Enter a STAC URL, e.g., https://earth-search.aws.element84.com/v1",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    collection = widgets.Dropdown(
        options=[],
        value=None,
        description="Collection:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    start_date = widgets.DatePicker(
        description="Start date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width="225px", padding=padding),
    )
    end_date = widgets.DatePicker(
        description="End date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width="225px", padding=padding),
    )

    band_names = []

    item = widgets.Dropdown(
        options=[],
        description="Item:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    vis_option = widgets.Dropdown(
        options=["1 band (Grayscale)", "3 bands (RGB)"],
        value="3 bands (RGB)",
        description="Visualization:",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    layer_name = widgets.Text(
        value="STAC Layer",
        description="Layer name:",
        tooltip="Enter a layer name for the selected file",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )

    band_width = "149px"
    red = widgets.Dropdown(
        options=band_names,
        value=None,
        description="Red:",
        tooltip="Select a band for the red channel",
        style=style,
        layout=widgets.Layout(width=band_width, padding=padding),
    )

    green = widgets.Dropdown(
        options=band_names,
        value=None,
        description="Green:",
        tooltip="Select a band for the green channel",
        style=style,
        layout=widgets.Layout(width="148px", padding=padding),
    )

    blue = widgets.Dropdown(
        options=band_names,
        value=None,
        description="Blue:",
        tooltip="Select a band for the blue channel",
        style=style,
        layout=widgets.Layout(width=band_width, padding=padding),
    )

    gray_band = widgets.Dropdown(
        options=band_names,
        value=None,
        description="Band:",
        tooltip="Select a band for visualization",
        style=style,
        layout=widgets.Layout(width="227px", padding=padding),
    )

    palette_options = list_palettes(lowercase=True)
    palette = widgets.Dropdown(
        options=palette_options,
        value=None,
        description="Palette:",
        layout=widgets.Layout(width="223px", padding=padding),
        style=style,
    )

    band_box = widgets.HBox([red, green, blue])

    def vis_option_changed(change):
        if change["new"] == "1 band (Grayscale)":
            band_box.children = [gray_band, palette]
        else:
            band_box.children = [red, green, blue]

    vis_option.observe(vis_option_changed, names="value")

    max_items = widgets.Text(
        value="20",
        description="Max items:",
        placeholder="Maximum number of items to return from the STAC API",
        tooltip="Maximum number of items to return from the STAC API",
        style=style,
        layout=widgets.Layout(width="130px", padding=padding),
    )

    vmin = widgets.Text(
        value=None,
        description="vmin:",
        tooltip="Minimum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="100px", padding=padding),
    )

    vmax = widgets.Text(
        value=None,
        description="vmax:",
        tooltip="Maximum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="100px", padding=padding),
    )

    nodata = widgets.Text(
        value=None,
        description="Nodata:",
        tooltip="Nodata the raster to visualize",
        style=style,
        layout=widgets.Layout(width="113px", padding=padding),
    )

    more_label = widgets.Label(
        "More options:",
        layout=widgets.Layout(width="100px", padding=padding),
        style=style,
    )

    add_footprints = widgets.Checkbox(
        value=True,
        description="Add image footprints",
        indent=False,
        layout=widgets.Layout(width="170px", padding=padding),
        style=style,
    )

    checkbox = widgets.Checkbox(
        value=False,
        description="Additional params",
        indent=False,
        layout=widgets.Layout(width="154px", padding=padding),
        style=style,
    )

    query_params_text = "Additional parameters to query the STAC API, for example: {'query': {'eo:cloud_cover':{'lt':10}}}"
    query_params = widgets.Textarea(
        value="",
        placeholder=query_params_text,
        layout=widgets.Layout(width="454px", padding=padding),
        style=style,
    )

    add_params_text = "Additional parameters to visualize imagery, for example: {'palette': ['#006633', '#E5FFCC', '#662A00', '#D8D8D8', '#F5F5F5'], 'expression': '(SR_B5-SR_B4)/(SR_B5+SR_B4)'}"
    add_params = widgets.Textarea(
        value="",
        placeholder=add_params_text,
        layout=widgets.Layout(width="454px", padding=padding),
        style=style,
    )

    def reset_options():
        """Reset the options to their default values."""
        catalog.value = catalog_ids[0]
        collection.options = []
        collection.value = None
        endpoint.value = catalogs[catalog.value]
        start_date.value = None
        end_date.value = None
        item.options = []
        item.value = None
        layer_name.value = ""
        max_items.value = "20"
        vmin.value = ""
        vmax.value = ""
        nodata.value = ""
        palette.value = None
        add_params.value = ""
        reset_bands()
        vis_option.value = "3 bands (RGB)"
        output.outputs = ()

    params_widget = widgets.VBox()

    more_options = widgets.VBox()
    more_options.children = [
        widgets.HBox([more_label, add_footprints, checkbox]),
        params_widget,
    ]

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Collections", "Items", "Display", "Reset", "Close"],
        tooltips=["Get Collections", "Get Items", "Display Image", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = button_width

    dataset_widget = widgets.VBox()

    dataset_widget.children = [endpoint, collection]

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        catalog,
        dataset_widget,
        widgets.HBox([start_date, end_date]),
        item,
        vis_option,
        band_box,
        more_options,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def update_bands():
        excluded = [
            "index",
            "metadata",
            "mtl.json",
            "mtl.txt",
            "mtl.xml",
            "qa",
            "qa-browse",
            "QA",
            "rendered_preview",
            "tilejson",
            "tir-browse",
            "vnir-browse",
            "xml",
            "documentation",
        ]

        if len(stac_data) > 0:
            bnames = stac_data[0][item.value]["bands"]
        else:
            bnames = []

        bnames = [b for b in bnames if b not in excluded]

        red.options = bnames
        green.options = bnames
        blue.options = bnames

        if len(bnames) >= 3:
            vis_option.value = "3 bands (RGB)"
            palette.value = None
            gray_band.options = bnames

            default_bands = set_default_bands(bnames)
            try:
                red.value = default_bands[0]
                green.value = default_bands[1]
                blue.value = default_bands[2]
            except Exception as e:
                red.value = None
                green.value = None
                blue.value = None
        elif len(bnames) >= 1:
            vis_option.value = "1 band (Grayscale)"
            gray_band.options = bnames
            gray_band.value = bnames[0]
            red.value = bnames[0]
            green.value = bnames[0]
            blue.value = bnames[0]

    def reset_bands():
        red.options = []
        green.options = []
        blue.options = []
        gray_band.options = []
        red.value = None
        green.value = None
        blue.value = None
        gray_band.value = None

    def catalog_changed(change):
        if change["new"]:
            endpoint.value = catalogs[catalog.value]
            collection.options = []
            collection.value = None
            item.options = []
            item.value = None
            if catalog.value in m._STAC_COLLECTIONS:
                collection.options = m._STAC_COLLECTIONS[catalog.value]
                collection.value = m._STAC_COLLECTIONS[catalog.value][0]
            reset_bands()

    catalog.observe(catalog_changed, names="value")

    def endpoint_changed(change):
        with output:
            output.outputs = ()
            output.clear_output()
            print("Retrieving collections...")
            try:
                if endpoint.value is not None:
                    collection.options = []
                    collection.value = None

                    collections = stac_collections(
                        endpoint.value, return_ids=True, get_root=False, **kwargs
                    )
                    if collections:
                        collections.sort()
                        collection.options = collections
                        collection.value = collections[0]
                        output.clear_output()
                        output.outputs = ()
                    else:
                        print("No collections found.")
                else:
                    print("No URL provided.")
                reset_bands()

            except Exception as e:
                print(e)

    endpoint.on_submit(endpoint_changed)

    def collection_changed(change):
        if change["new"]:
            reset_bands()
            item.options = []
            item.value = None

    collection.observe(collection_changed, names="value")

    def item_changed(change):
        if change["new"]:
            layer_name.value = item.value

    item.observe(item_changed, names="value")

    def checkbox_changed(change):
        if change["new"]:
            params_widget.children = [
                layer_name,
                widgets.HBox([max_items, vmin, vmax, nodata]),
                query_params,
                add_params,
            ]
        else:
            params_widget.children = []

    checkbox.observe(checkbox_changed, names="value")

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Collections":
            collection.options = []
            with output:
                output.outputs = ()
                print("Retrieving collections...")
                try:
                    if endpoint.value is not None:
                        if (
                            endpoint.value == catalogs[catalog.value]
                            and catalog.value in m._STAC_COLLECTIONS
                        ):
                            collections = m._STAC_COLLECTIONS[catalog.value]
                        else:
                            collections = stac_collections(
                                endpoint.value, return_ids=True, **kwargs
                            )

                        if collections:
                            collections.sort()
                            collection.options = collections
                            collection.value = collections[0]

                            m._STAC_COLLECTIONS[catalog.value] = collections
                            output.clear_output()
                            output.outputs = ()
                        else:
                            print("No collections found.")
                    else:
                        print("No URL provided.")
                except Exception as e:
                    print(e)

        elif change["new"] == "Items":
            with output:
                output.outputs = ()
                if endpoint.value is not None:
                    if start_date.value is not None and end_date.value is not None:
                        datetime = str(start_date.value) + "/" + str(end_date.value)
                    elif start_date.value is not None:
                        datetime = str(start_date.value) + "/.."
                    elif end_date.value is not None:
                        datetime = "../" + str(end_date.value)
                    else:
                        datetime = None

                    if m is not None:
                        if m.user_roi is not None:
                            intersects = m.user_roi["geometry"]
                        else:
                            intersects = bbox_to_geojson(m.bounds)

                    else:
                        intersects = None

                    if (
                        checkbox.value
                        and query_params.value.strip().startswith("{")
                        and query_params.value.strip().endswith("}")
                    ):
                        query = eval(query_params.value)
                    elif query_params.value.strip() == "":
                        query = {}
                    else:
                        print(
                            "Invalid query parameters. It must be a dictionary with keys such as 'query', 'sortby', 'filter', 'fields'"
                        )
                        query = {}

                print("Retrieving items...")
                try:
                    if collection.value is None:
                        output.outputs = ()
                        print("Please click on 'Collections' to retrieve collections.")
                    else:
                        item.options = []
                        item.value = None
                        reset_bands()
                        search = stac_search(
                            url=endpoint.value,
                            collections=[collection.value],
                            max_items=int(max_items.value),
                            intersects=intersects,
                            datetime=datetime,
                            **query,
                            **kwargs,
                        )
                        search_dict = stac_search_to_dict(search)
                        item.options = list(search_dict.keys())
                        item.value = list(search_dict.keys())[0]
                        setattr(m, "stac_search", search)
                        setattr(m, "stac_dict", search_dict)
                        setattr(m, "stac_items", stac_search_to_list(search))

                        if add_footprints.value and m is not None:
                            gdf = stac_search_to_gdf(search)
                            style = {
                                "stroke": True,
                                "color": "#3388ff",
                                "weight": 2,
                                "opacity": 1,
                                "fill": True,
                                "fillColor": "#000000",
                                "fillOpacity": 0,
                            }
                            hover_style = {"weight": 4}
                            m.add_gdf(
                                gdf,
                                style=style,
                                hover_style=hover_style,
                                layer_name="Footprints",
                                zoom_to_layer=False,
                                info_mode="on_click",
                            )
                            setattr(m, "stac_gdf", gdf)

                        stac_data.clear()
                        stac_data.append(search_dict)
                        update_bands()
                        output.clear_output()
                        output.outputs = ()
                except NotImplementedError as e:
                    print(e)

                except Exception as e:
                    print(e)

        elif change["new"] == "Display":
            with output:
                output.outputs = ()

                if item.value and m is not None:
                    print("Loading data...")

                    if (
                        checkbox.value
                        and add_params.value.strip().startswith("{")
                        and add_params.value.strip().endswith("}")
                    ):
                        vis_params = eval(add_params.value)
                    else:
                        vis_params = {}

                    if (
                        vis_option.value == "1 band (Grayscale)"
                        and (palette.value is not None)
                    ) or (palette.value and "expression" in vis_params):
                        vis_params["colormap_name"] = palette.value
                    elif (
                        palette.value
                        and len(set([red.value, green.value, blue.value])) > 1
                        and "expression" not in vis_params
                    ):
                        palette.value = None
                        print("Palette can only be set for single band images.")

                    if vmax.value and not vmin.value:
                        vmin.value = "0"

                    if vmin.value and vmax.value:
                        vis_params["rescale"] = f"{vmin.value},{vmax.value}"

                    if nodata.value:
                        vis_params["nodata"] = nodata.value

                    if vis_option.value == "1 band (Grayscale)":
                        assets = gray_band.value
                    else:
                        assets = f"{red.value},{green.value},{blue.value}"

                    try:
                        if "Planetary Computer" in catalog.value:
                            output.outputs = ()
                            m.add_stac_layer(
                                collection=collection.value,
                                item=item.value,
                                assets=assets,
                                name=layer_name.value,
                                fit_bounds=False,
                                **vis_params,
                            )
                            setattr(
                                m,
                                "stac_item",
                                m.stac_dict[item.value],
                            )
                            m.stac_item["collection"] = collection.value

                        else:
                            output.outputs = ()
                            m.add_stac_layer(
                                url=stac_data[0][item.value]["href"],
                                assets=assets,
                                name=layer_name.value,
                                fit_bounds=False,
                                **vis_params,
                            )
                            setattr(m, "stac_item", m.stac_dict[item.value])
                            if "rescale" in m.layers[-1].url:
                                output.outputs = ()

                        output.clear_output()
                    except Exception as e:
                        print(e)

                else:
                    print("Please click on 'Items' to retrieve items.")
                    buttons.value = None

        elif change["new"] == "Reset":
            reset_options()

        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def oam_search_gui(
    m,
    position: Optional[str] = "topright",
    opened: Optional[bool] = True,
):
    """Generates a tool GUI template using ipywidgets. Icons can be found at https://fontawesome.com/v4/icons

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="plane",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    dropdown = widgets.Dropdown(
        options=["Map bounds", "User drawn ROI", "Custom bbox"],
        value="Map bounds",
        description="bbox:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    start_date = widgets.DatePicker(
        description="start date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )
    end_date = widgets.DatePicker(
        description="end date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    checkbox = widgets.Checkbox(
        description="Additional parameters",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    textarea = widgets.Textarea(
        placeholder="Addition parameters as a dictionary, e.g., {'platform': 'UAV'}",
        layout=widgets.Layout(width=widget_width),
    )

    params_hbox = widgets.HBox()

    def checkbox_changed(change):
        if checkbox.value:
            params_hbox.children = [textarea]
        else:
            params_hbox.children = []

    checkbox.observe(checkbox_changed, "value")

    int_slider = widgets.IntSlider(
        value=100,
        min=1,
        max=200,
        description="Limit: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style=style,
    )

    int_slider_label = widgets.Label("100")

    def int_slider_changed(change):
        if change["new"]:
            int_slider_label.value = str(int_slider.value)

    int_slider.observe(int_slider_changed, "value")

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Search", "Reset", "Close"],
        tooltips=["Search", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        dropdown,
        start_date,
        end_date,
        widgets.HBox([int_slider, int_slider_label]),
        checkbox,
        params_hbox,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Search":
            with output:
                output.outputs = ()
                if m is not None:
                    if dropdown.value == "Map bounds":
                        bbox = m.get_bbox()
                    elif dropdown.value == "User drawn ROI":
                        bbox = m.user_roi_bounds()
                    else:
                        bbox = None

                    if start_date.value is not None:
                        start = str(start_date.value)
                    else:
                        start = None
                    if end_date.value is not None:
                        end = str(end_date.value)
                    else:
                        end = None

                    if (
                        checkbox.value
                        and textarea.value.strip().startswith("{")
                        and textarea.value.strip().endswith("}")
                    ):
                        params = eval(textarea.value)
                    else:
                        params = {}

                    limit = int_slider.value

                    m.oam_search(bbox, start, end, limit=limit, **params)

        elif change["new"] == "Reset":
            textarea.value = ""
            dropdown.value = "Map bounds"
            start_date.value = None
            end_date.value = None
            checkbox.value = False
            int_slider.value = 100
            output.outputs = ()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = opened
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position=position
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def layer_manager_gui(
    m,
    position: Optional[str] = "topright",
    opened: Optional[bool] = True,
    return_widget: Optional[bool] = False,
):
    """Creates a layer manager widget.

    Args:
        m (geemap.Map): The geemap.Map object.
        position (str, optional): The position of the widget. Defaults to "topright".
        return_widget (bool, optional): Whether to return the widget. Defaults to False.
    """

    layers_button = widgets.ToggleButton(
        value=False,
        tooltip="Layer Manager",
        icon="server",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    toolbar_header = widgets.HBox()
    toolbar_header.children = [layers_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = []
    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_header]

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [layers_button]

    layers_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            layers_button.value = False
            m.toolbar_reset()
            if m.layer_manager is not None and m.layer_manager in m.controls:
                m.remove_control(m.layer_manager)
                m.layer_manager = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def layers_btn_click(change):
        if change["new"]:
            layers_hbox = []
            all_layers_chk = widgets.Checkbox(
                value=False,
                description="All layers on/off",
                indent=False,
                layout=widgets.Layout(height="18px", padding="0px 8px 25px 8px"),
            )
            all_layers_chk.layout.width = "30ex"
            layers_hbox.append(all_layers_chk)

            def all_layers_chk_changed(change):
                if change["new"]:
                    for layer in m.layers:
                        if hasattr(layer, "visible"):
                            layer.visible = True
                else:
                    for layer in m.layers:
                        if hasattr(layer, "visible"):
                            layer.visible = False

            all_layers_chk.observe(all_layers_chk_changed, "value")

            layers = [lyr for lyr in m.layers if lyr.name]

            # if the layers contain unsupported layers (e.g., GeoJSON, GeoData), adds the ipyleaflet built-in LayerControl
            if len(layers) < (len(m.layers) - 1):
                if m.layer_control is None:
                    layer_control = ipyleaflet.LayersControl(position="topright")
                    m.layer_control = layer_control
                if m.layer_control not in m.controls:
                    m.add(m.layer_control)

            # for non-TileLayer, use layer.style={'opacity':0, 'fillOpacity': 0} to turn layer off.
            for layer in layers:
                visible = True
                if hasattr(layer, "visible"):
                    visible = layer.visible
                layer_chk = widgets.Checkbox(
                    value=visible,
                    description=layer.name,
                    indent=False,
                    layout=widgets.Layout(height="18px"),
                )
                layer_chk.layout.width = "25ex"

                if layer in m.geojson_layers:
                    try:
                        opacity = max(
                            layer.style["opacity"], layer.style["fillOpacity"]
                        )
                    except KeyError:
                        opacity = 1.0
                elif hasattr(layer, "opacity"):
                    opacity = layer.opacity
                else:
                    opacity = 1.0

                layer_opacity = widgets.FloatSlider(
                    value=opacity,
                    min=0,
                    max=1,
                    step=0.01,
                    readout=False,
                    layout=widgets.Layout(width="80px"),
                )
                layer_settings = widgets.Button(
                    icon="gear",
                    tooltip=layer.name,
                    layout=widgets.Layout(
                        width="25px", height="25px", padding="0px 0px 0px 0px"
                    ),
                )

                def layer_settings_click(b):
                    if b.tooltip in m.cog_layer_dict:
                        m._add_layer_editor(
                            position="topright",
                            layer_dict=m.cog_layer_dict[b.tooltip],
                        )

                layer_settings.on_click(layer_settings_click)

                def layer_opacity_changed(change):
                    if change["new"]:
                        layer.style = {
                            "opacity": change["new"],
                            "fillOpacity": change["new"],
                        }

                if hasattr(layer, "visible"):
                    widgets.jslink((layer_chk, "value"), (layer, "visible"))

                if layer in m.geojson_layers:
                    layer_opacity.observe(layer_opacity_changed, "value")
                elif hasattr(layer, "opacity"):
                    widgets.jsdlink((layer_opacity, "value"), (layer, "opacity"))

                hbox = widgets.HBox(
                    [layer_chk, layer_settings, layer_opacity],
                    layout=widgets.Layout(padding="0px 8px 0px 8px"),
                )
                layers_hbox.append(hbox)
                m.layer_widget = layers_hbox

            toolbar_header.children = [close_button, layers_button]
            toolbar_footer.children = layers_hbox

        else:
            toolbar_header.children = [layers_button]

    layers_button.observe(layers_btn_click, "value")
    layers_button.value = opened

    if not hasattr(m, "_layer_manager_widget"):
        m._layer_manager_widget = toolbar_footer

    if return_widget:
        return m.layer_widget
    else:
        layer_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position=position
        )

        if layer_control not in m.controls:
            m.add_control(layer_control)
            m.layer_manager = layer_control


def nasa_data_gui(
    m,
    position: Optional[str] = "topright",
    opened: Optional[bool] = True,
    default_dataset: Optional[str] = "GEDI_L4A_AGB_Density_V2_1_2056",
    **kwargs,
):
    """Search NASA Earth data interactive

    Args:
        m (leafmap.Map, optional): The leaflet Map object. Defaults to None.
        position (str, optional): The position of the widget. Defaults to "topright".
        opened (bool, optional): Whether to open the widget. Defaults to True.
        default_dataset (str, optional): The default dataset. Defaults to "GEDI_L4A_AGB_Density_V2_1_2056".

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import pandas as pd
    from datetime import datetime

    widget_width = "400px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    if not hasattr(m, "_NASA_DATA"):
        url = "https://github.com/opengeos/NASA-Earth-Data/raw/main/nasa_earth_data.tsv"
        df = pd.read_csv(url, sep="\t")
        setattr(m, "_NASA_DATA", df)
        names = df["ShortName"].tolist()
        setattr(m, "_NASA_DATA_NAMES", names)

    default_title = m._NASA_DATA[m._NASA_DATA["ShortName"] == default_dataset][
        "EntryTitle"
    ].values[0]

    output = widgets.Output(
        layout=widgets.Layout(width=widget_width, padding=padding, overflow="auto")
    )

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Search NASA Earth data",
        icon="search",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    keyword = widgets.Text(
        value="",
        description="Keyword:",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    short_name = widgets.Dropdown(
        options=m._NASA_DATA_NAMES,
        value=default_dataset,
        description="Short Name:",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    title = widgets.Text(
        value=default_title,
        description="Title:",
        style=style,
        disabled=True,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    max_items = widgets.IntText(
        value=50,
        description="Max items:",
        style=style,
        layout=widgets.Layout(width="125px", padding=padding),
    )

    bbox = widgets.Text(
        value="",
        description="Bounding box:",
        placeholder="xmin, ymin, xmax, ymax",
        style=style,
        layout=widgets.Layout(width="271px", padding=padding),
    )

    start_date = widgets.DatePicker(
        description="Start date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width="198px", padding=padding),
    )
    end_date = widgets.DatePicker(
        description="End date:",
        disabled=False,
        style=style,
        layout=widgets.Layout(width="198px", padding=padding),
    )

    dataset = widgets.Dropdown(
        value=None,
        description="Dataset:",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Search", "Display", "Reset", "Close"],
        tooltips=["Get Items", "Display Image", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "65px"

    def change_keyword(change):
        short_name.options = nasa_datasets(
            keyword.value, df=m._NASA_DATA, return_short_name=True
        )

    keyword.on_submit(change_keyword)

    def change_dataset(change):
        title.value = m._NASA_DATA[m._NASA_DATA["ShortName"] == short_name.value][
            "EntryTitle"
        ].values[0]
        dataset.value = None
        dataset.options = []

    short_name.observe(change_dataset, "value")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        keyword,
        short_name,
        title,
        widgets.HBox([max_items, bbox]),
        widgets.HBox([start_date, end_date]),
        dataset,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):
        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Search":
            with output:
                output.clear_output()
                with output:
                    print("Searching...")

                    if bbox.value.strip() == "":
                        if m.user_roi_bounds() is not None:
                            bounds = tuple(m.user_roi_bounds())
                        else:
                            bounds = (
                                m.bounds[0][1],
                                m.bounds[0][0],
                                m.bounds[1][1],
                                m.bounds[1][0],
                            )
                    else:
                        bounds = tuple(map(float, bbox.value.split(",")))
                        if len(bounds) != 4:
                            print("Please provide a valid bounding box.")
                            bounds = None

                    if start_date.value is not None and end_date.value is not None:
                        date_range = (str(start_date.value), str(end_date.value))
                    elif start_date.value is not None:
                        date_range = (
                            str(start_date.value),
                            datetime.today().strftime("%Y-%m-%d"),
                        )
                    else:
                        date_range = None

                    output.clear_output(wait=True)
                    try:
                        results, gdf = nasa_data_search(
                            count=max_items.value,
                            short_name=short_name.value,
                            bbox=bounds,
                            temporal=date_range,
                            return_gdf=True,
                        )

                        if len(results) > 0:
                            if "Footprints" in m.get_layer_names():
                                m.remove(m.find_layer("Footprints"))
                            if (
                                hasattr(m, "_NASA_DATA_CTRL")
                                and m._NASA_DATA_CTRL in m.controls
                            ):
                                m.remove(m._NASA_DATA_CTRL)
                            m.add_gdf(
                                gdf,
                                layer_name="Footprints",
                                info_mode="on_click",
                                zoom_to_layer=False,
                            )
                            setattr(m, "_NASA_DATA_CTRL", m.controls[-1])

                            dataset.options = gdf["native-id"].values.tolist()
                            dataset.value = dataset.options[0]

                            setattr(m, "_NASA_DATA_GDF", gdf)
                            setattr(m, "_NASA_DATA_RESULTS", results)

                    except Exception as e:
                        print(e)

        elif change["new"] == "Display":
            output.clear_output()
            with output:
                print("To be implemented...")

        elif change["new"] == "Reset":
            keyword.value = ""
            short_name.options = m._NASA_DATA_NAMES
            short_name.value = default_dataset
            title.value = default_title
            max_items.value = 50
            bbox.value = ""
            bbox.placeholder = "xmin, ymin, xmax, ymax"
            start_date.value = None
            end_date.value = None
            dataset.options = []
            dataset.value = None
            output.clear_output()

            if "Footprints" in m.get_layer_names():
                m.remove(m.find_layer("Footprints"))
            if hasattr(m, "_NASA_DATA_CTRL") and m._NASA_DATA_CTRL in m.controls:
                m.remove(m._NASA_DATA_CTRL)

        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = opened
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position=position
        )

        if toolbar_control not in m.controls:
            m.add(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget
