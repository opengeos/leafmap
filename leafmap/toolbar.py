"""Module for dealing with the toolbar.
"""
import math
import os
import ipyevents
import ipyleaflet
import ipywidgets as widgets
from ipyleaflet import TileLayer, WidgetControl
from IPython.core.display import display
from ipyfilechooser import FileChooser
from .common import *


def tool_template(m=None):
    """Generates a tool GUI template using ipywidgets.

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
    widgets.jslink((int_slider, "value"), (int_slider_label, "value"))

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
    widgets.jslink((float_slider, "value"), (float_slider_label, "value"))

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
                output.clear_output()
                print("Running ...")
        elif change["new"] == "Reset":
            textarea.value = ""
            output.clear_output()
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
        toolbar_control = WidgetControl(widget=toolbar_widget, position="topright")

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
    tools = {
        "map": {
            "name": "basemap",
            "tooltip": "Change basemap",
        },
        "adjust": {
            "name": "split_map",
            "tooltip": "Split-panel map",
        },
        "globe": {
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
        "eraser": {
            "name": "eraser",
            "tooltip": "Remove all drawn features",
        },
        "camera": {
            "name": "save_map",
            "tooltip": "Save map as HTML or image",
        },
        # "smile-o": {
        #     "name": "placeholder",
        #     "tooltip": "This is a placehold",
        # },
        "spinner": {
            "name": "placeholder2",
            "tooltip": "This is a placehold",
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
            width="107px",
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
                split_basemaps(m, layers_dict=planet_tiles_tropical())
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
                    tools_dict, max_width="800px", max_height="500px"
                )
                wbt_control = WidgetControl(widget=wbt_toolbox, position="bottomright")
                m.whitebox = wbt_control
                m.add_control(wbt_control)
            elif tool_name == "save_map":
                save_map((m))
            elif tool_name == "help":
                import webbrowser

                webbrowser.open_new_tab("https://leafmap.org")
                current_tool.value = False
        else:
            tool = change["owner"]
            tool_name = tools[tool.icon]["name"]

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
                        layer.visible = True
                else:
                    for layer in m.layers:
                        layer.visible = False

            all_layers_chk.observe(all_layers_chk_changed, "value")

            layers = [
                lyr
                for lyr in m.layers[1:]
                if (isinstance(lyr, TileLayer) or isinstance(lyr, ipyleaflet.WMSLayer))
            ]

            # if the layers contain unsupported layers (e.g., GeoJSON, GeoData), adds the ipyleaflet built-in LayerControl
            if len(layers) < (len(m.layers) - 1):
                if m.layer_control is None:
                    layer_control = ipyleaflet.LayersControl(position="topright")
                    m.layer_control = layer_control
                if m.layer_control not in m.controls:
                    m.add_control(m.layer_control)

            # for non-TileLayer, use layer.style={'opacity':0, 'fillOpacity': 0} to turn layer off.
            for layer in layers:
                layer_chk = widgets.Checkbox(
                    value=layer.visible,
                    description=layer.name,
                    indent=False,
                    layout=widgets.Layout(height="18px"),
                )
                layer_chk.layout.width = "25ex"
                layer_opacity = widgets.FloatSlider(
                    value=layer.opacity,
                    min=0,
                    max=1,
                    step=0.01,
                    readout=False,
                    layout=widgets.Layout(width="80px"),
                )
                layer_settings = widgets.ToggleButton(
                    icon="gear",
                    tooltip=layer.name,
                    layout=widgets.Layout(
                        width="25px", height="25px", padding="0px 0px 0px 5px"
                    ),
                )

                def layer_vis_on_click(change):
                    if change["new"]:
                        layer_name = change["owner"].tooltip
                        change["owner"].value = False

                layer_settings.observe(layer_vis_on_click, "value")

                def layer_chk_changed(change):
                    layer_name = change["owner"].description

                layer_chk.observe(layer_chk_changed, "value")

                widgets.jslink((layer_chk, "value"), (layer, "visible"))
                widgets.jsdlink((layer_opacity, "value"), (layer, "opacity"))
                hbox = widgets.HBox(
                    [layer_chk, layer_settings, layer_opacity],
                    layout=widgets.Layout(padding="0px 8px 0px 8px"),
                )
                layers_hbox.append(hbox)

            toolbar_footer.children = layers_hbox
            toolbar_button.value = False
        else:
            toolbar_footer.children = [toolbar_grid]

    layers_button.observe(layers_btn_click, "value")

    toolbar_control = WidgetControl(widget=toolbar_widget, position="topright")

    m.add_control(toolbar_control)


def open_data_widget(m):
    """A widget for opening local vector/raster data.

    Args:
        m (object): leafmap.Map
    """

    padding = "0px 0px 0px 5px"
    style = {"description_width": "initial"}

    file_type = widgets.ToggleButtons(
        options=["Shapefile", "GeoJSON", "Vector", "CSV", "GeoTIFF"],
        tooltips=[
            "Open a shapefile",
            "Open a GeoJSON file",
            "Open a vector dataset",
            "Create points from CSV",
            "Open a vector dataset" "Open a GeoTIFF",
        ],
    )
    file_type.style.button_width = "88px"

    filepath = widgets.Text(
        value="",
        description="File path or HTTP URL:",
        tooltip="Enter a file path or HTTP URL to vector data",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )
    http_widget = widgets.HBox()

    file_chooser = FileChooser(os.getcwd())
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
    # ok_cancel.style.button_width = "133px"

    bands = widgets.Text(
        value="1",
        description="Bands:",
        tooltip="Enter a list of band indices",
        style=style,
        layout=widgets.Layout(width="110px"),
    )

    colormap = widgets.Dropdown(
        options=[],
        value=None,
        description="colormap:",
        layout=widgets.Layout(width="172px"),
        style=style,
    )

    x_dim = widgets.Text(
        value="x",
        description="x_dim:",
        tooltip="The x dimension",
        style=style,
        layout=widgets.Layout(width="80px"),
    )

    y_dim = widgets.Text(
        value="y",
        description="y_dim:",
        tooltip="The xydimension",
        style=style,
        layout=widgets.Layout(width="80px"),
    )

    raster_options = widgets.HBox()

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

    tool_output_ctrl = WidgetControl(widget=main_widget, position="topright")

    if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
        m.remove_control(m.tool_output_ctrl)

    def bands_changed(change):
        if change["new"] and "," in change["owner"].value:
            colormap.value = None
            colormap.disabled = True
        else:
            colormap.disabled = False

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
        tool_output.clear_output()

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
        elif change["new"] == "GeoTIFF":
            import matplotlib.pyplot as plt

            file_chooser.filter_pattern = "*.tif"
            colormap.options = plt.colormaps()
            colormap.value = "terrain"
            raster_options.children = [bands, colormap, x_dim, y_dim]
            point_widget.children = []
            point_check.value = False
            http_widget.children = []

    def ok_cancel_clicked(change):
        if change["new"] == "Apply":
            m.default_style = {"cursor": "wait"}
            file_path = filepath.value

            with tool_output:
                tool_output.clear_output()
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
                        m.add_shp(file_path, style=None, layer_name=layer_name.value)
                    elif ext.lower() == ".geojson":

                        m.add_geojson(
                            file_path, style=None, layer_name=layer_name.value
                        )

                    elif ext.lower() == ".csv":

                        m.add_xy_data(
                            file_path,
                            x=longitude.value,
                            y=latitude.value,
                            label=label.value,
                            layer_name=layer_name.value,
                        )

                    elif ext.lower() == ".tif":
                        sel_bands = [int(b.strip()) for b in bands.value.split(",")]
                        m.add_raster(
                            image=file_path,
                            bands=sel_bands,
                            layer_name=layer_name.value,
                            colormap=colormap.value,
                            x_dim=x_dim.value,
                            y_dim=y_dim.value,
                        )
                    else:
                        m.add_vector(file_path, style=None, layer_name=layer_name.value)
                else:
                    print("Please select a file to open.")

            m.toolbar_reset()
            m.default_style = {"cursor": "default"}

        elif change["new"] == "Reset":
            file_chooser.reset()
            tool_output.clear_output()
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

    m.add_control(tool_output_ctrl)
    m.tool_output_ctrl = tool_output_ctrl


def change_basemap(m):
    """Widget for changing basemaps.

    Args:
        m (object): leafmap.Map.
    """
    from .basemaps import leaf_basemaps

    dropdown = widgets.Dropdown(
        options=list(leaf_basemaps.keys()),
        value="ROADMAP",
        layout=widgets.Layout(width="200px")
        # description="Basemaps",
    )

    close_btn = widgets.Button(
        icon="times",
        tooltip="Close the basemap widget",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    basemap_widget = widgets.HBox([dropdown, close_btn])

    def on_click(change):
        basemap_name = change["new"]

        if len(m.layers) == 1:
            old_basemap = m.layers[0]
        else:
            old_basemap = m.layers[1]
        m.substitute_layer(old_basemap, leaf_basemaps[basemap_name])

    dropdown.observe(on_click, "value")

    def close_click(change):
        m.toolbar_reset()
        if m.basemap_ctrl is not None and m.basemap_ctrl in m.controls:
            m.remove_control(m.basemap_ctrl)
        basemap_widget.close()

    close_btn.on_click(close_click)

    basemap_control = WidgetControl(widget=basemap_widget, position="topright")
    m.add_control(basemap_control)
    m.basemap_ctrl = basemap_control


def save_map(m):
    """Saves the map as HTML, JPG, or PNG.

    Args:
        m (leafmap.Map): The leafmap Map object.
    """
    import time

    tool_output = widgets.Output()
    m.tool_output = tool_output
    tool_output.clear_output(wait=True)
    save_map_widget = widgets.VBox()

    save_type = widgets.ToggleButtons(
        options=["HTML", "PNG", "JPG"],
        tooltips=[
            "Save the map as an HTML file",
            "Take a screenshot and save as a PNG file",
            "Take a screenshot and save as a JPG file",
        ],
    )

    file_chooser = FileChooser(os.getcwd())
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
                tool_output.clear_output()
                m.to_html(file_path)
            elif save_type.value == "PNG" and ext.upper() == ".PNG":
                tool_output.clear_output()
                m.toolbar_button.value = False
                time.sleep(1)
                screen_capture(outfile=file_path)
            elif save_type.value == "JPG" and ext.upper() == ".JPG":
                tool_output.clear_output()
                m.toolbar_button.value = False
                time.sleep(1)
                screen_capture(outfile=file_path)
            else:
                label = widgets.Label(
                    value="The selected file extension does not match the selected exporting type."
                )
                save_map_widget.children = [save_type, file_chooser, label]
        elif change["new"] == "Cancel":
            tool_output.clear_output()
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
    save_map_control = WidgetControl(widget=save_map_widget, position="topright")
    m.add_control(save_map_control)
    m.save_map_control = save_map_control


def split_basemaps(m, layers_dict=None, left_name=None, right_name=None, width="120px"):

    from .basemaps import basemap_tiles

    m.layers = [m.layers[0]]
    m.clear_controls()

    # layers_dict = None
    # left_name = None
    # right_name = None
    # width = "120px"
    add_zoom = True
    add_fullscreen = True

    if layers_dict is None:
        layers_dict = {}
        keys = dict(basemap_tiles).keys()
        for key in keys:
            if isinstance(basemap_tiles[key], ipyleaflet.WMSLayer):
                pass
            else:
                layers_dict[key] = basemap_tiles[key]

    keys = list(layers_dict.keys())
    if left_name is None:
        left_name = keys[0]
    if right_name is None:
        right_name = keys[-1]

    left_layer = layers_dict[left_name]
    right_layer = layers_dict[right_name]

    control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    m.add_control(control)

    left_dropdown = widgets.Dropdown(
        options=keys, value=left_name, layout=widgets.Layout(width=width)
    )

    left_control = ipyleaflet.WidgetControl(widget=left_dropdown, position="topleft")
    m.add_control(left_control)

    right_dropdown = widgets.Dropdown(
        options=keys, value=right_name, layout=widgets.Layout(width=width)
    )

    right_control = ipyleaflet.WidgetControl(widget=right_dropdown, position="topright")
    m.add_control(right_control)

    if add_zoom:
        m.add_control(ipyleaflet.ZoomControl())
    if add_fullscreen:
        m.add_control(ipyleaflet.FullScreenControl())
    m.add_control(ipyleaflet.ScaleControl(position="bottomleft"))

    split_control = None
    for ctrl in m.controls:
        if isinstance(ctrl, ipyleaflet.SplitMapControl):
            split_control = ctrl
            break

    def left_change(change):
        split_control.left_layer.url = layers_dict[left_dropdown.value].url

    left_dropdown.observe(left_change, "value")

    def right_change(change):
        split_control.right_layer.url = layers_dict[right_dropdown.value].url

    right_dropdown.observe(right_change, "value")
