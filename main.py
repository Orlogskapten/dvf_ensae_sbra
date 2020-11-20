import geopandas as gpd
import pandas as pd
import numpy as np

from bokeh.models import (GeoJSONDataSource, HoverTool, CustomJS, Select
, LinearColorMapper, ColorBar, ColumnDataSource, Button, RadioButtonGroup
, Tabs, Panel, RadioGroup)
from bokeh.palettes import RdYlGn
from bokeh.plotting import (figure, curdoc)
from bokeh.layouts import (column, row)
from bokeh.tile_providers import (get_provider, Vendors)

grouped_price_time_median= pd.read_csv("csv/grouped_price_time_median.csv")
grouped_price_time_mean= pd.read_csv("csv/grouped_price_time_mean.csv")
dico= {"valeurfonc": "Valeur foncière", "sbati": "Surface des logements (mutation)"
    , "pp": "Nombre de pièce (mutation)", "valeur_per_met": "Valeur foncière par mètre carré"}
grouped_price_time_mean.rename(columns= dico, inplace= True)
grouped_price_time_median.rename(columns= dico, inplace= True)
# Reput datetime object
def put_time(df, col= "datemut"):
    datmut_serie = pd.to_datetime(pd.Series(df[col]), format="%Y-%m-%d")
    return gpd.GeoSeries(datmut_serie)

grouped_price_time_mean["datemut"]= put_time(grouped_price_time_mean)
grouped_price_time_median["datemut"]= put_time(grouped_price_time_median)

dico_data= {0: grouped_price_time_mean, 1: grouped_price_time_median}

base_crs= {"init": "epsg:4326"}

menage_per_arr_mean= gpd.read_file("menage_per_arr_mean.shp")
menage_per_arr_mean.rename(columns= {"valeurfonc": "Valeur foncière", "Ind": "Nombre d'individus"
    , "Men": "Nombre de ménages", "Men_pauv": "Proportion de ménages pauvres"
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
var_arr_col= [col for col in menage_per_arr_mean.columns if col not in ["c_ar", "counts", "geometry"]]

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
p= figure(title= "Carte des arrondissements de Paris", plot_height= 500, plot_width= 800, toolbar_location= "below"
          , x_axis_type="linear", y_axis_type="linear", tools= tools)
tile_provider= get_provider(Vendors.CARTODBPOSITRON_RETINA)
p.add_tile(tile_provider)

# Define both line plot
plot= figure(title= "Par année", plot_height= 300, plot_width= 600
              , toolbar_location= None, tools= "")
plot2= figure(title= "Par mois", plot_height= 300, plot_width= 600
              , toolbar_location= None, tools= "")

# Select for map figure
select= Select(title="Sélectionner la variable", options= var_arr_col, value= var_base)

# Reset plot and map localisation in the figure
# from https://www.kaggle.com/pavlofesenko/interactive-titanic-dashboard-using-bokeh
callback3_test= CustomJS(args= dict(p= p), code= '''
    p.reset.emit();
''')
button= Button(label= 'Reset')
button.js_on_click(callback3_test)

# Select month or year for line plot
line_list= [col for col in grouped_price_time_mean.columns if col not in ["datemut", "Unnamed: 0"]]
select_line_var= Select(title= "Sélectionner la variable", options= line_list, value= var_base)
radio_group_type= RadioGroup(labels= ["Moyenne", "Mediane"], active= 0)


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
# tooltips="""
#
#     <div style ="border-width: 1px;background-color:orange;">
#         <div>
#             <span style="font-size: 12px; ">Arrondissement</span>
#             <span style="font-size: 12px; "> @c_ar</span>
#         </div>
#     </div>
#     """
p.add_tools(HoverTool(tooltips= [("Arrondissement ", "@c_ar")
    , ("Nombre de ménages (en moyenne)", "@{Nombre de ménages}{int}")
    , ("Nombre d'individus (en moyenne)", "@{Nombre d'individus}{int}")
    , ("Proportion de ménages pauvres ", "@{Proportion de ménages pauvres}{1.1} %")
    , ("Valeur foncière ", "@{Valeur foncière}{int} €")
    , ("Note globale de l'arrondissement ", "@{Note globale}{1.1}")]))

# Adjust our grid (delete line, ticks etc.)
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_label_text_font_size = '0pt'
p.yaxis.major_label_text_font_size = '0pt'
p.background_fill_color= None
p.border_fill_color= None
# Legend color bar
p.add_layout(color_bar, "below")

select.on_change("value", update_map)

# Page 2 : line plot
def update_line_kind_data(attr, old, new):
    kind= radio_group_type.active

    new_data= dico_data[kind]
    date = new_data["datemut"].dt.to_period("Y")  # Per month
    mean_grouped_price_time_mean= new_data.groupby(date).mean()
    mean_grouped_price_time_mean.reset_index(level=0, inplace=True)
    mean_grouped_price_time_mean["datemut"] = mean_grouped_price_time_mean["datemut"].astype(str)

    line_source.data = dict(ColumnDataSource(mean_grouped_price_time_mean).data)

    date = new_data["datemut"].dt.month  # Per month
    mean_grouped_price_time_mean= new_data.groupby(date).mean()
    mean_grouped_price_time_mean.reset_index(level=0, inplace=True)
    mean_grouped_price_time_mean["datemut"] = mean_grouped_price_time_mean["datemut"].astype(str)

    line_source2.data = dict(ColumnDataSource(mean_grouped_price_time_mean).data)

    pass
radio_group_type.on_change("active", update_line_kind_data)

# Year xaxis
date= grouped_price_time_mean["datemut"].dt.to_period("Y") # Per year
mean_grouped_price_time_mean= grouped_price_time_mean.groupby(date).mean()
mean_grouped_price_time_mean.reset_index(level=0, inplace=True)
mean_grouped_price_time_mean["datemut"]= mean_grouped_price_time_mean["datemut"].astype(str)

line_source= ColumnDataSource(mean_grouped_price_time_mean)
line= plot.line(source= line_source, x= "datemut", y= var_base
                , line_width= 2, line_color= "darkorange", alpha= 0.3)
circle= plot.circle(source= line_source, x= "datemut", y= var_base, size= 7
                    , line_width= 2, line_color= "darkorange", alpha= 0.8
                    , color= "lightblue")

plot.xaxis.major_label_orientation = 3.14 / 4
plot.add_tools(HoverTool(tooltips= [("Année ", "@datemut")]))


# Month xaxis
date= grouped_price_time_mean["datemut"].dt.month#to_period("M") # Per year
mean_grouped_price_time_mean= grouped_price_time_mean.groupby(date).mean()
mean_grouped_price_time_mean.reset_index(level=0, inplace=True)
mean_grouped_price_time_mean["datemut"]= mean_grouped_price_time_mean["datemut"].astype(str).str.replace("-", "")

line_source2= ColumnDataSource(mean_grouped_price_time_mean)
line2= plot2.line(source= line_source2, x= "datemut", y= var_base
                  , line_width= 2, line_color= "darkorange", alpha= 0.3)
circle2= plot2.circle(source= line_source2, x= "datemut", y= var_base, size= 7
                     , line_width= 2, line_color= "darkorange", alpha= 0.8
                      , color= "lightblue")
plot2.xaxis.major_label_orientation = 3.14 / 4
plot2.xaxis.major_label_overrides = {1:"Janvier", 2:"Fevrier", 3:"Mars", 4:"Avril", 5:"Mai", 6:"Juin"
                                                         , 7:"Juillet", 8:"Aout", 9:"Septembre", 10:"Octobre"
                                                         , 11:"Novembre", 12:"Decembre"}
plot2.add_tools(HoverTool(tooltips= [("Mois ", "@datemut")]))


def update_line_var(attr, old, new):
    var= select_line_var.value

    line.glyph.y= var
    line2.glyph.y= var

    circle.glyph.y = var
    circle2.glyph.y= var
    pass
select_line_var.on_change("value", update_line_var)


# HTML page formation
page1= column(column(row(p, width= 800)
                     , column(row(select, width= 400), row(button, width= 50))))
tab1= Panel(child= page1, title= "Valeur par arrondissemeent")

page2= column(plot, plot2, row(row(select_line_var, width= 250), radio_group_type))
tab2= Panel(child= page2, title= "Valeur dans le temps")

final_page= Tabs(tabs= [tab1, tab2])
curdoc().add_root(final_page)
