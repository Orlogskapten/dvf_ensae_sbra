from tornado.ioloop import IOLoop

import geopandas as gpd
import pandas as pd
import numpy as np
import json

from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.models import (GeoJSONDataSource, HoverTool, CustomJS, Select
, LinearColorMapper, ColorBar, ColumnDataSource, Button, Slider, TapTool, RadioButtonGroup)
from bokeh.palettes import RdYlGn
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.layouts import (column, row)
from bokeh.tile_providers import (get_provider, Vendors)
from bokeh.models.tickers import FixedTicker

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
paris_mutation.crs= base_crs
arrondissement.crs= base_crs
paris_arr.crs= base_crs

base_arr_col= ["c_ar"]
var_arr_col= ["valeurfonc", "Ind", "Men", "Men_pauv", "Men_prop","Men_fmp", "Ind_snv", "Men_surf", "Men_coll"
    , "Men_mais", "sbati", "pp", "valeur_metre_carre", "Note global", "Qualité de vie", "Commerces", "Enseignement"
    , "Culture", "Sports et loisirs", "Santé", "Sécurité", "Transports", "Environnement"]

menage_per_arr= paris_arr[base_arr_col+var_arr_col].groupby(base_arr_col, as_index= False)
menage_per_arr_mean= menage_per_arr.mean()
menage_per_arr_count= menage_per_arr.size().reset_index(name= "counts")
# Add num mutation per arrondissement into our principal dataset
menage_per_arr_mean= menage_per_arr_mean.merge(menage_per_arr_count, on= "c_ar")

# Add arrondissement shape (Polygon)
menage_per_arr_mean["geometry"]= menage_per_arr_mean["c_ar"].map(arrondissement_geometry)
menage_per_arr_mean= gpd.GeoDataFrame(menage_per_arr_mean)
menage_per_arr_mean.crs= base_crs

menage_per_arr_mean= menage_per_arr_mean.to_crs({'init': 'epsg:3395'}) # mercator projection

# Ordering arrondissement to make easier the manipulation on CustomJS
menage_per_arr_mean["c_ar"]= menage_per_arr_mean["c_ar"].astype(int)
menage_per_arr_mean.sort_values(by= "c_ar", ascending= True, inplace= True)
menage_per_arr_mean["c_ar"]= menage_per_arr_mean["c_ar"].astype(str)
menage_per_arr_mean.reset_index(inplace= True, drop= True)

def to_date_col(df, col= "datemut", formated= "%Y-%m-%d"):
    return pd.to_datetime(df[col], format= "%Y-%m-%d")


paris_arr["datemut"]= to_date_col(paris_arr)
paris_arr["mois"]= paris_arr["datemut"].apply(lambda x: x.month)
paris_arr["annee"]= paris_arr["datemut"].apply(lambda x: x.year)

month_paris_arr= paris_arr[var_arr_col+["mois"]].groupby(["mois"], as_index= False).mean()
year_paris_arr= paris_arr[var_arr_col+["annee"]].groupby(["annee"], as_index= False).mean()


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

    tools= "pan,wheel_zoom,poly_select,box_select,tap"
    p= figure(title= "Paris", plot_height= 500, plot_width= 800, toolbar_location= "below"
              , x_axis_type="linear", y_axis_type="linear", tools= tools)
    tile_provider= get_provider(Vendors.CARTODBPOSITRON_RETINA)
    p.add_tile(tile_provider)

    # Define the left histogram / barplot
    plot= figure(title= "Densité", plot_height= 200, plot_width= 500
                  , toolbar_location= None)
    plot_annee= figure(title="Densité arr", plot_height=200, plot_width=500
                  , toolbar_location=None)

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
    radio_button= RadioButtonGroup(labels= ["Année", "Mois"], active= 0)

    # Select bins with slider
    num_bins= 20
    slider= Slider(start= 10, end= 100, value= num_bins,
                    step= 10, title='Nombre de bins')

    def update_map(attr, old, new):
        # Get the new value of our selectors
        var_base= select.value # Select
        num_bins= slider.value # Slider
        active_but = radio_button.active # Button month / year

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

        if active_but == 0:
            line_data.data= dict(ColumnDataSource(year_paris_arr).data)
            let_go = plot_annee.line(source=line_data, x="annee", y= var_base)
        else:
            line_data.data= dict(ColumnDataSource(month_paris_arr).data)
            let_go = plot_annee.line(source=line_data, x="mois", y= var_base)
            plot_annee.xaxis.major_label_overrides= {1:"Janvier", 2:"Fevrier", 3:"Mars", 4:"Avril", 5:"Mai", 6:"Juin"
                                                         , 7:"Juillet", 8:"Aout", 9:"Septembre", 10:"Octobre"
                                                         , 11:"Novembre", 12:"Decembre"}

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

    def update_line_select(attr, old, new):
        active_but= radio_button.active
        var_base= select.value

        if active_but == 0:
            line_data.data= dict(ColumnDataSource(year_paris_arr).data)
            let_go = plot_annee.line(source=line_data, x="annee", y= var_base)
        else:
            line_data.data= dict(ColumnDataSource(month_paris_arr).data)
            let_go = plot_annee.line(source=line_data, x="mois", y= var_base)
            plot_annee.xaxis.major_label_overrides= {1:"Janvier", 2:"Fevrier", 3:"Mars", 4:"Avril", 5:"Mai", 6:"Juin"
                                                         , 7:"Juillet", 8:"Aout", 9:"Septembre", 10:"Octobre"
                                                         , 11:"Novembre", 12:"Decembre"}
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

    # Plot line per year : month
    line_base_var= var_base
    year_or_month= "annee"
    line_data= ColumnDataSource(year_paris_arr)
    let_go= plot_annee.line(source= line_data, x= year_or_month, y= var_base)
    plot_annee.xaxis.major_label_orientation = 3.14 / 4

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

    select.on_change("value", update_map)
    slider.on_change("value", update_bins)
    radio_button.on_change("active", update_line_select)

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
                        , plot_annee
                        , row(radio_button, width= 400)
                )
            ), sizing_mode="scale_width"
        )
        , row(
            button, width= 50
        )
    )
    doc.add_root(layout)

    # doc.add_root(p)
    pass


def main():
    """Launch the server and connect to it.
    """
    print("Preparing a bokeh application.")
    io_loop= IOLoop.current()
    bokeh_app= Application(FunctionHandler(modify_doc))

    server= Server({"/": bokeh_app}, io_loop=io_loop)
    server.start()
    print("Opening Bokeh application on http://localhost:5006/")

    io_loop.add_callback(server.show, "/")
    io_loop.start()


if __name__ == '__main__':
    main()


