import solara
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from ipyleaflet import Map, GeoJSON, Popup, basemaps, basemap_to_tiles
from ipyleaflet import WidgetControl, FullScreenControl, ScaleControl

# Load the .geojson file into a GeoDataFrame 
gdf = gpd.read_file("./earthquake_data.geojson") 
gdf['time'] = gdf['time'].apply(str)
min_lat = gdf['latitude'].min()
max_lat = gdf['latitude'].max()
min_lon = gdf['longitude'].min()
max_lon = gdf['longitude'].max()
min_magnitude = gdf['mag'].min()
max_magnitude = gdf['mag'].max()
min_depth = gdf['depth'].min()
max_depth = gdf['depth'].max()

# make json from geodataframe so we can use GeoJSON from ipyleaflet
geojson_data_initial = json.loads(gdf.to_json())

# Create a map
start_location = (-0.3, 101)
m = Map(center=start_location, 
        basemap=basemap_to_tiles(basemaps.Esri.WorldImagery),
        zoom=6)

# create widget
input_min_lat = widgets.BoundedFloatText(
    description='Min Lat:',
    value=min_lat,
    min=-90,
    max=90,
    step=0.01,
)

input_max_lat = widgets.BoundedFloatText(
    description='Max Lat:',
    value=max_lat,
    min=-90,
    max=90,
    step=0.01,
)

input_min_lon = widgets.BoundedFloatText(
    description='Min Lon:',
    value=min_lon,
    min=-180,
    max=180,
    step=0.01,
)

input_max_lon = widgets.BoundedFloatText(
    description='Max Lon:',
    value=max_lon,
    min=-180,
    max=180,
    step=0.01,
)

slider_depth = widgets.FloatRangeSlider(
    value=[min_depth, max_depth],
    min=min_depth,
    max=max_depth,
    step=1,
    description='Depth:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
)

dropdown_magnitude = widgets.Dropdown(
    options=['3', '4', '5', '6', '7', '8', '9'],
    value='3',
    description='Min Mag:',
    disabled=False,
)

checkbox_show_lat = widgets.Checkbox(
    description='Filter Latitude',
    value=False  # Checked by default
)
checkbox_show_lon = widgets.Checkbox(
    description='Filter Longitude',
    value=False  # Checked by default
)
checkbox_show_depth = widgets.Checkbox(
    description='Filter Depth',
    value=False  # Checked by default
)
checkbox_show_mag = widgets.Checkbox(
    description='Filter Magnitude',
    value=False  # Checked by default
)

icon_button = widgets.Button(
    icon="list",
    layout=widgets.Layout(width='40px', height='40px') 
)
apply_button = widgets.Button(description='Apply Filter')
reset_button = widgets.Button(description='Reset Filter')

# put widget to layout
buttons_box = widgets.HBox([apply_button,reset_button])
widget_lat_box = widgets.VBox([input_min_lat,input_max_lat])
widget_lon_box = widgets.VBox([input_min_lon,input_max_lon])
widget_depth_box = widgets.VBox([slider_depth])
widget_mag_box = widgets.VBox([dropdown_magnitude])
widget_box = widgets.VBox([
    checkbox_show_lat,
    widget_lat_box,
    checkbox_show_lon,
    widget_lon_box,
    checkbox_show_depth,
    widget_depth_box,
    checkbox_show_mag,
    widget_mag_box,
    buttons_box
])

def on_icon_button_click(b):
    if widget_box.layout.display == 'none':
        widget_box.layout.display = 'block'
    else:
        widget_box.layout.display = 'none'

def create_popup(lat,lon,properties):
    target_info = ['mag','magType','latitude','longitude','depth','place','time']
    
    string_info = ""
    for key in target_info:
        string_info += f"<div>{key} = {properties[key]}</div>"
    string_info = widgets.HTML(string_info)
    popup_content = widgets.VBox([string_info])
    return Popup(
        location=(lat,lon),
        child= popup_content,
        close_button=True,
        auto_close=False,
        close_on_escape_key=False,
        keep_in_view=True,
        min_width = 300
    )

def gdf_onclick_handler(event=None, feature=None, id=None, properties=None,**kwargs):
    lat = properties['latitude']
    lon = properties['longitude']
    popup = create_popup(lat,lon,properties)
    m.add(popup)


cmap = plt.get_cmap('gist_rainbow')
norm = plt.Normalize(20, 100) 
def value_to_color(value):   
    rgba = cmap(norm(value)) 
    return f'#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}'

# Function to scale the value to marker size
def scale_value(value, min_size=2, max_size=20):
    scale = ((value - min_magnitude) / (max_magnitude - min_magnitude))
    return int(min_size + (max_size - min_size) * scale)

# Define a style callback function
def style_callback(feature):
    magnitude = feature['properties']['mag']
    depth = feature['properties']['depth']
    return {
        'radius': scale_value(magnitude),
        'fillColor': value_to_color(depth),
        'fillOpacity': 0.8,
        'color': 'black',
        'weight': 1
    }

def add_geojson_layer(geojson_data):
    # Add GeoJSON layer to the map
    geojson_layer = GeoJSON(
        data=geojson_data,
        point_style={'radius': 5, 'color': 'blue', 'fillColor': 'blue', 'fillOpacity': 0.8},
        style_callback=style_callback,
        hover_style={'fillColor': 'white', 'color': 'black', 'fillOpacity': 1}
    )
    # add click handler to create pop up
    geojson_layer.on_click(gdf_onclick_handler)
    # add layer
    m.add_layer(geojson_layer)


# Create a continuous horizontal colormap legend using Matplotlib
def create_depth_cmap_legend():
    fig, ax = plt.subplots(figsize=(4, 1))
    fig.patch.set_facecolor('white')
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax, orientation='horizontal')
    cb.set_label('Depth (Km)')
    plt.tight_layout()
    
    # Save the legend to a file
    fig.savefig('colormap_legend_horizontal.png', bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    
    # Load the legend image as an HTML widget
    legend_img = open('colormap_legend_horizontal.png', 'rb').read()
    legend_widget = widgets.Image(value=legend_img, format='png')
    return WidgetControl(widget=legend_widget, position='bottomleft')

def toggle_show_lat(change):
    if widget_lat_box.layout.display == 'none':
        widget_lat_box.layout.display = 'flex'
    else:
        widget_lat_box.layout.display = 'none'

def toggle_show_lon(change):
    if widget_lon_box.layout.display == 'none':
        widget_lon_box.layout.display = 'flex'
    else:
        widget_lon_box.layout.display = 'none'

def toggle_show_depth(change):
    if widget_depth_box.layout.display == 'none':
        widget_depth_box.layout.display = 'flex'
    else:
        widget_depth_box.layout.display = 'none'

def toggle_show_mag(change):
    if widget_mag_box.layout.display == 'none':
        widget_mag_box.layout.display = 'flex'
    else:
        widget_mag_box.layout.display = 'none'

def apply_filter_handler(*args):
    selected_gdf = gdf.copy()
    
    # filter latitude
    if checkbox_show_lat.value:
        min_lat_filter = input_min_lat.value
        max_lat_filter = input_max_lat.value
        selected_gdf = selected_gdf[
            (selected_gdf['latitude'] >= min_lat_filter) & 
            (selected_gdf['latitude'] <= max_lat_filter)
        ]

    # filter longitude
    if checkbox_show_lon.value:
        min_lon_filter = input_min_lon.value
        max_lon_filter = input_max_lon.value
        selected_gdf = selected_gdf[
            (selected_gdf['longitude'] >= min_lon_filter) & 
            (selected_gdf['longitude'] <= max_lon_filter)
        ]

    # filter depth
    if checkbox_show_depth.value:
        (min_depth_filter,max_depth_filter) = slider_depth.value
        selected_gdf = selected_gdf[
            (selected_gdf['depth'] >= min_depth_filter) & 
            (selected_gdf['depth'] <= max_depth_filter)
        ]

    # filter magnitude
    if checkbox_show_mag.value:
        min_mag_filter = float(dropdown_magnitude.value)
        selected_gdf = selected_gdf[ selected_gdf['mag'] >= min_mag_filter ]

    # Clear existing markers
    for layer in m.layers:
        if isinstance(layer, (Popup,GeoJSON)):
            m.remove(layer)

    if len(selected_gdf) > 0 :
        geojson_data = json.loads(selected_gdf.to_json())
        add_geojson_layer(geojson_data)

def reset_filter_handler(*args):
    checkbox_show_lat.value = False
    checkbox_show_lon.value = False
    checkbox_show_depth.value = False
    checkbox_show_mag.value = False

    input_min_lat.value = min_lat
    input_max_lat.value = max_lat
    input_min_lon.value = min_lon
    input_max_lon.value = max_lon
    slider_depth.value = [min_depth, max_depth]
    dropdown_magnitude.value = '3'

    # Clear existing markers
    for layer in m.layers:
        if isinstance(layer, (Popup,GeoJSON)):
            m.remove(layer)
            
    add_geojson_layer(geojson_data_initial)
    
# add event to widget
checkbox_show_lat.observe(toggle_show_lat, names='value')
checkbox_show_lon.observe(toggle_show_lon, names='value')
checkbox_show_depth.observe(toggle_show_depth, names='value')
checkbox_show_mag.observe(toggle_show_mag, names='value')
icon_button.on_click(on_icon_button_click)
apply_button.on_click(apply_filter_handler)
reset_button.on_click(reset_filter_handler)

# add initial data to map
add_geojson_layer(geojson_data_initial)

# Initially hide the widget box
widget_lat_box.layout.display = 'none'
widget_lon_box.layout.display = 'none'
widget_depth_box.layout.display = 'none'
widget_mag_box.layout.display = 'none'
widget_box.layout.display = 'none'

# create WidgetControl, so the widget can be added to the map
button_control = WidgetControl(widget=icon_button, position='topright')
widget_box_control = WidgetControl(widget=widget_box, position='topright')

# Display the map, widget and legend
m.add(button_control)
m.add(widget_box_control)
m.add(FullScreenControl())
m.add(ScaleControl(position='bottomright'))

legend_control = create_depth_cmap_legend()
m.add_control(legend_control) # Add the legend to the map
m.layout.height = '100vh'


page = widgets.VBox(
    [
        m
    ]
)