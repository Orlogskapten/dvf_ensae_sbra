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

menage_per_arr_mean= gpd.read_file("menage_per_arr_mean.shp")
menage_per_arr_mean.rename(columns= {"valeurfonc": "Valeur foncière", "Ind": "Nombre d'individus"
    , "Men": "Nombre de ménage", "Men_pauv": "Proportion de ménages pauvres"
    , "Men_prop": "Proportion de ménages d’un seul individu", "Men_fmp": "Proportion de ménages monoparentaux"
    , "Ind_snv": "Somme des niveaux de vie winsorisés des individus"
    , "Men_surf": "Somme de la surface des logements du carreau"
    , "Men_coll": "Proportion de ménages en logements collectifs", "Men_mais": "Proportion de ménages en maison"
    , "sbati": "Surface des logements (mutation)", "pp": "Nombre de pièce (mutation)"
    , "valeur_met": "Valeur foncière par mètre carré", "Note globa": "Note globale", "Qualite de": "Note qualite de vie"
    , "Enseigneme": "Note enseignement", "Commerces": "Note commerces", "Culture": "Note culture"
    , "Sports et": "Note sport et loisirs", "Sante": "Note sante", "Securite": "Note securite"
    , "Transports": "Note transports", "Environnem": "Note environnement"}
                           , inplace= True)

base_arr_col= ["c_ar"]
# var_arr_col= ["valeurfonc", "Ind", "Men", "Men_pauv", "Men_prop","Men_fmp", "Ind_snv", "Men_surf", "Men_coll"
#     , "Men_mais", "sbati", "pp", "valeur_met", "Note globa", "Qualite de", "Commerces", "Enseigneme"
#     , "Culture", "Sports et", "Sante", "Securite", "Transports", "Environnem"]
var_arr_col= [col for col in menage_per_arr_mean.columns if col not in ["c-ar", "counts", "geometry"]]

var_base= "Valeur foncière"

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
select= Select(title="Sélectionner la variable", options= var_arr_col, value= var_base)

# Reset plot and map localisation in the figure
# from https://www.kaggle.com/pavlofesenko/interactive-titanic-dashboard-using-bokeh
callback3_test= CustomJS(args= dict(p= p, plot= plot), code= '''
    p.reset.emit();
    plot.reset.emit();
''')
button= Button(label= 'Reset')
button.js_on_click(callback3_test)

# Select month or year for line plot

# # Select bins with slider
# num_bins= 20
# slider= Slider(start= 10, end= 100, value= num_bins,
#                 step= 10, title='Nombre de bins')

def update_map(attr, old, new):
    # Get the new value of our selectors
    var_base= select.value # Select

    # Update data
    our_new_data= gpd.GeoDataFrame(menage_per_arr_mean[["geometry"]+var_arr_col+["counts"]+base_arr_col])
    our_new_data.crs= base_crs
    geo_arr_json.geojson= our_new_data.to_json()

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

    pass

# Map figure
arr= p.patches(source= geo_arr_json
                , fill_color= fill_color
                , line_color= "black"
                , fill_alpha= 0.8
                )

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


select.on_change("value", update_map)
# radio_button.on_change("active", update_line_select)

# layout= column(column(row(select, width= 400), p), button)
layout= column(
    column(
        row(
            select, width= 400
        )
        , row( p, width= 800
        ), sizing_mode="scale_width"
    )
    , row(
        button, width= 50
    )
)

curdoc().add_root(layout)
