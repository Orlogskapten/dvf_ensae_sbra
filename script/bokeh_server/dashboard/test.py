from tornado.ioloop import IOLoop

import geopandas as gpd
import pandas as pd

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models import (GeoJSONDataSource, HoverTool, Div, CustomJS, Select
, LinearColorMapper, ColorBar, ColumnDataSource)
from bokeh.palettes import RdYlGn
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.layouts import (column, row)


base_crs= {"init": "epsg:4326"}

arrondissement= gpd.read_file("../../../good_data/mutation_paris/paris/arrondissements.shp")
paris_mutation= gpd.read_file("../../../good_data/data/filo_mutation/paris_mutation_filo.shp")
score_arrondissement= pd.read_csv("../../../good_data/saved/score_per_arr.csv")

# Adjust score arrondissment to merge with arrondissement
score_arrondissement= score_arrondissement.rename({"Arrondissement": "c_ar"}, axis= 1) # simplify merging index
score_arrondissement["c_ar"]= score_arrondissement["c_ar"].astype("str")

for col in [col for col in score_arrondissement if col != "c_ar"]: # delete , into . to set float type
    score_arrondissement[col]= score_arrondissement[col].apply(lambda x: x.replace(",", ".")).astype("float")


# Adjust arrondissement type to merge with paris_mutation
arrondissement["c_ar"]= arrondissement["c_ar"].astype("float").astype("str")
arrondissement["c_ar"]= arrondissement["c_ar"].apply(lambda x: x.replace(".0", ""))

# Stock into a dict arrondissement:geographic form
arrondissement_geometry= dict(zip(arrondissement["c_ar"], arrondissement.geometry))
arrondissement.drop(columns= ["geometry"], inplace= True)

paris_mutation["c_ar"]= paris_mutation["l_codinsee"].apply(lambda x: x.replace("}", "")[-2:])
paris_mutation["c_ar"]= paris_mutation["c_ar"].apply(lambda x: x if x[0] != "0" else x[1])

# We complete arrondissement dataset and then merge it with paris mutation
arrondissement= arrondissement.merge(score_arrondissement, on= "c_ar")
paris_arr= paris_mutation.merge(arrondissement, on= "c_ar")
paris_arr["valeur_metre_carre"]= paris_arr["valeurfonc"] / paris_arr["sbati"]

# Set up our data CRS
base_crs= {"init": "epsg:4326"}
paris_mutation.crs= base_crs
arrondissement.crs= base_crs
paris_arr.crs= base_crs

base_arr_col= ["c_ar"]
var_arr_col= ["valeurfonc", "Ind", "Men", "Men_pauv", "Men_prop","Men_fmp", "Ind_snv", "Men_surf", "Men_coll"
    , "Men_mais", "sbati", "pp", "valeur_metre_carre", "Note global", "Qualité de vie", "Commerces", "Enseignement"
    , "Culture", "Sports et loisirs", "Santé", "Sécurité", "Transports", "Environnement"]

menage_per_arr= paris_arr[base_arr_col+var_arr_col].groupby(base_arr_col, as_index= False)
menage_per_arr_mean= menage_per_arr.mean()

# Add arrondissement shape (Polygon)
menage_per_arr_mean["geometry"]= menage_per_arr_mean["c_ar"].map(arrondissement_geometry)
menage_per_arr_mean= gpd.GeoDataFrame(menage_per_arr_mean)
menage_per_arr_mean.crs= base_crs

var_base= "valeur_metre_carre"

def to_geojson(geopd):
    return GeoJSONDataSource(geojson= geopd.to_json())

geo_arr_json= to_geojson(menage_per_arr_mean)


def modify_doc(doc):
    """Add a plotted function to the document.

    Arguments:
        doc: A bokeh document to which elements can be added.
    """

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

    p= figure(title= "Paris", plot_height= 500, plot_width= 1000
               , toolbar_location= "below")

    select = Select(title="Sélectionner la variable", options=var_arr_col)

    def update_map(attr, old, new):
        var_base = select.value

        # Update data
        our_new_data= gpd.GeoDataFrame(menage_per_arr_mean[["geometry"]+[var_base]])
        our_new_data.crs= base_crs
        geo_arr_json.geojson= our_new_data.to_json()

        # Update color bar
        color_mapper.high= our_new_data[var_base].max()
        color_mapper.low = our_new_data[var_base].min()

        # Update color change in map
        fill_color["field"]= var_base
        fill_color["transform"]= color_mapper
        # Dont know how to update patches property
        arr= p.patches(source= geo_arr_json
                        , fill_color= fill_color
                        , line_color= "black"
                        )
        pass

    arr = p.patches(source=geo_arr_json
                    , fill_color= fill_color
                    , line_color="black"
                    )

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
    select.on_change("value", update_map)
    layout= column(row(select, width= 400), p)

    doc.add_root(layout)
    # doc.add_root(p)
    pass


def main():
    """Launch the server and connect to it.
    """
    print("Preparing a bokeh application.")
    io_loop = IOLoop.current()
    bokeh_app = Application(FunctionHandler(modify_doc))

    server = Server({"/": bokeh_app}, io_loop=io_loop)
    server.start()
    print("Opening Bokeh application on http://localhost:5006/")

    io_loop.add_callback(server.show, "/")
    io_loop.start()


if __name__ == '__main__':
    main( )