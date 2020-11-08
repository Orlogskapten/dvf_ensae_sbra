import geopandas as gpd
import pandas as pd
import bokeh.plotting as bp
from bokeh.plotting import (figure, save, output_file)
from bokeh.models import (GeoJSONDataSource, HoverTool, Div, CustomJS, Select
, LinearColorMapper, ColorBar, ColumnDataSource)
from bokeh.palettes import RdYlGn

base_crs= {"init": "epsg:4326"}

arrondissement= gpd.read_file("../../good_data/mutation_paris/paris/arrondissements.shp")
paris_mutation= gpd.read_file("../../good_data/data/filo_mutation/paris_mutation_filo.shp")
score_arrondissement= pd.read_csv("../../good_data/saved/score_per_arr.csv")

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

def swap_geometry(df, col_to_set, geometry= "geometry", base_crs= base_crs):
    """
    Set our CRS when we change geometry column
    """
    df[col_to_set]= gpd.GeoSeries(df[col_to_set]).centroid
    df[geometry]= df[col_to_set]
    df[col_to_set].crs= base_crs
    df[geometry]= df[col_to_set]
    df[geometry].crs= base_crs
    return df


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

# Paris arrondissement plotting
def to_geojson(geopd):
    return GeoJSONDataSource(geojson= geopd.to_json())

def to_columnsdatasource(geopd):
    geopd["x"]= geopd.geometry.centroid.x
    geopd["y"] = geopd.geometry.centroid.y
    geopd_copy= geopd.copy()
    geopd_copy= geopd_copy.drop(["geometry"], axis= 1)
    return ColumnDataSource(geopd_copy)

geo_arr_json= to_geojson(menage_per_arr_mean)
# arr_columndatasource= to_columnsdatasource(menage_per_arr_mean)
var_test= "valeur_metre_carre"


# Create the variable selector
select= Select(title= "Sélectionner la variable",  options= var_arr_col)
# https://www.kaggle.com/pavlofesenko/interactive-titanic-dashboard-using-bokeh

color_mapper= LinearColorMapper(
    palette= RdYlGn[7],
    low= menage_per_arr_mean[var_test].min(),
    high= menage_per_arr_mean[var_test].max()
)

color_bar= ColorBar(color_mapper= color_mapper
                    , orientation= "horizontal"
                    , border_line_color= None
                    , location= (0, 0)
                    )

p= figure(title= "Paris", plot_height= 500, plot_width= 1000
          , toolbar_location= "below")


arr= p.patches(source= geo_arr_json
               , fill_color= {"field": "valeur_metre_carre"
                              , "transform": color_mapper}
               , line_color= "black"

               )

# Adjust our grid (delete line, ticks etc.)
p.xgrid.grid_line_color= None
p.ygrid.grid_line_color= None
p.xaxis.major_tick_line_color= None
p.xaxis.minor_tick_line_color= None
p.yaxis.major_tick_line_color= None
p.yaxis.minor_tick_line_color= None
p.xaxis.major_label_text_font_size = '0pt'
p.yaxis.major_label_text_font_size = '0pt'

# Legend color bar
p.add_layout(color_bar, "below")

# p.add_tools(HoverTool(tooltips= [("Arrondissement", "@c_ar")]))
#
#
# tab1= Panel(child= p, title= "Arrondissement")
#
# # autre plot
# p_map= Div(text="<iframe src="r'paris_map.html'" style='min-width:calc(100vw - 26px); height: 500px'><iframe>")
# tab2= Panel(child= p_map, title= "Je sais pas encore")


# # Save into html file
output_file(r"paris_mutation.html")
# tabs= Tabs(tabs= [ tab1, tab2 ])
# save(obj= tabs)
save(obj= p)
