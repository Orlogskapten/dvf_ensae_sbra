import geopandas as gpd
import pandas as pd
import numpy as np

from bokeh.models import (GeoJSONDataSource, HoverTool, CustomJS, Select
, LinearColorMapper, ColorBar, ColumnDataSource, Button, Slider, RadioButtonGroup)
from bokeh.palettes import RdYlGn
from bokeh.plotting import (figure, curdoc)
from bokeh.layouts import (column, row)
from bokeh.tile_providers import (get_provider, Vendors)


base_crs= {"init": "epsg:4326"}

arrondissement= gpd.read_file("arrondissements.shp")
# https://geopandas.org/io.html
paris_mutation= gpd.read_file("zip://paris_mutation_filo.zip!paris_mutation_filo.shp")
score_arrondissement= pd.read_csv("score_per_arr.csv")

base_arr_col= ["c_ar"]
var_arr_col= ["valeurfonc", "Ind", "Men", "Men_pauv", "Men_prop","Men_fmp", "Ind_snv", "Men_surf", "Men_coll"
    , "Men_mais", "sbati", "pp", "valeur_metre_carre", "Note global", "Qualité de vie", "Commerces", "Enseignement"
    , "Culture", "Sports et loisirs", "Santé", "Sécurité", "Transports", "Environnement"]

var_base= "valeur_metre_carre"

def to_geojson(geopd):
    return GeoJSONDataSource(geojson= geopd.to_json())

geo_arr_json= to_geojson(menage_per_arr_mean)


color_mapper= LinearColorMapper(
    palette= RdYlGn[11],
    low= menage_per_arr_mean[var_base].min(),
    high= menage_per_arr_mean[var_base].max()
)

fill_color = {"field": var_base, "transform": color_mapper}

color_bar= ColorBar(color_mapper= color_mapper
                     , orientation= "horizontal"
                     , border_line_color= None
                     , location= (0, 0)
                     )

tools= "pan,wheel_zoom,poly_select,box_select"
p= figure(title= "Paris", plot_height= 500, plot_width= 800, toolbar_location= "below"
          , x_axis_type="linear", y_axis_type="linear", tools= tools)
tile_provider= get_provider(Vendors.CARTODBPOSITRON_RETINA)
p.add_tile(tile_provider)

# Define the left histogram / barplot
plot= figure(title= "Densité", plot_height= 200, plot_width= 500
              , toolbar_location= None, tools= "")

# Select for map figure
select= Select(title="Sélectionner la variable", options= var_arr_col, value= "valeur_metre_carre")

# Reset plot and map localisation in the figure
# from https://www.kaggle.com/pavlofesenko/interactive-titanic-dashboard-using-bokeh
callback3_test= CustomJS(args= dict(p= p, plot= plot), code= '''
    p.reset.emit();
    plot.reset.emit();
''')
button= Button(label= 'Reset')
button.js_on_click(callback3_test)

# Select month or year for line plot

# Select bins with slider
num_bins= 20
slider= Slider(start= 10, end= 100, value= num_bins,
                step= 10, title='Nombre de bins')

def update_map(attr, old, new):
    # Get the new value of our selectors
    var_base= select.value # Select
    num_bins= slider.value # Slider

    # Update data
    our_new_data= gpd.GeoDataFrame(menage_per_arr_mean[["geometry"]+var_arr_col+["counts"]+base_arr_col])
    our_new_data.crs= base_crs
    geo_arr_json.geojson= our_new_data.to_json()

    # Update hist data
    hist_data = paris_arr[var_base].apply(lambda x: np.log(x) if x > 0 else x)
    hist, edges= np.histogram(hist_data[np.isfinite(hist_data)], bins= num_bins)
    hist_df = pd.DataFrame({var_base: hist,
                            "left": edges[:-1],
                            "right": edges[1:]})
    hist_df["interval"] = ["%d to %d" % (left, right) \
                           for left, right in zip(hist_df["left"], hist_df["right"])]
    # print(hist_df)
    src_hist.data= dict(ColumnDataSource(hist_df).data)

    # Update color bar
    color_mapper.high= our_new_data[var_base].max()
    color_mapper.low= our_new_data[var_base].min()

    # Update color change in map
    fill_color["field"]= var_base
    fill_color["transform"]= color_mapper
    # Dont know how to update patches property (and hist)
    # update map
    arr= p.patches(source= geo_arr_json
                    , fill_color= fill_color
                    , line_color= "black"
                    , fill_alpha= 0.8
                    )

    # Update histogram
    plot_hist = plot.quad(source=src_hist, left="left", right="right", top=var_base, bottom=0)

    pass

def update_bins(attr, old, new):
    num_bins = slider.value  # Slider
    var_base = select.value  # Select

    # Update hist data
    hist_data = paris_arr[var_base].apply(lambda x: np.log(x) if x > 0 else x)
    hist, edges = np.histogram(hist_data[np.isfinite(hist_data)], bins=num_bins)
    hist_df = pd.DataFrame({var_base: hist,
                            "left": edges[:-1],
                            "right": edges[1:]})
    hist_df["interval"] = ["%d to %d" % (left, right) \
                           for left, right in zip(hist_df["left"], hist_df["right"])]
    # print(hist_df)
    src_hist.data = dict(ColumnDataSource(hist_df).data)

    # Update histogram
    plot_hist = plot.quad(source=src_hist, left="left", right="right", top=var_base, bottom=0)
    pass

# Map figure
arr= p.patches(source= geo_arr_json
                , fill_color= fill_color
                , line_color= "black"
                , fill_alpha= 0.8
                )

# Histogram figure
hist_data = paris_arr[var_base].apply(lambda x: np.log(x) if x > 0 else x)
hist, edges = np.histogram(hist_data[np.isfinite(hist_data)], bins=num_bins)
hist_df = pd.DataFrame({var_base: hist,
                        "left": edges[:-1],
                        "right": edges[1:]})
hist_df["interval"] = ["%d to %d" % (left, right) \
                       for left, right in zip(hist_df["left"], hist_df["right"])]
src_hist = ColumnDataSource(hist_df)
plot_hist = plot.quad(source=src_hist, left="left", right="right", top=var_base, bottom=0)


# Map hover
p.add_tools(HoverTool(tooltips= [("Arrondissement", "@c_ar")
                                 , ("OK", "OK")]))


# Adjust our grid (delete line, ticks etc.)
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_label_text_font_size = '0pt'
p.yaxis.major_label_text_font_size = '0pt'


# Legend color bar
p.add_layout(color_bar, "below")

# Update our data
fake_data = ColumnDataSource({"indices": []})
codes = """
var index_selected = source.selected.indices;
fake_data.data= {new: index_selected};
fake_data.change.emit();
console.log(index_selected)
console.log(fake_data);
"""
callback= CustomJS(args= dict(source= geo_arr_json, fake_data= fake_data), code= codes)
p.js_on_event("tap", callback)

# code_line_plot = """
#     var column = cb_obj.value;
#     line1.glyph.x.field = column;
#     source.trigger('change')
#     """
# callback_line_plot= CustomJS(args= dict(source= ), code= code_line_plot)


select.on_change("value", update_map)
slider.on_change("value", update_bins)
# radio_button.on_change("active", update_line_select)

# layout= column(column(row(select, width= 400), p), button)
layout= column(
    column(
        row(
            select, width= 400
        )
        , row(
            row(
                p, width= 800
            )
            , column(
                    plot
                    , slider
            )
        ), sizing_mode="scale_width"
    )
    , row(
        button, width= 50
    )
)

curdoc().add_root(layout)
