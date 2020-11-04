import geopandas as gpd
from bokeh.plotting import (figure, save, output_file)
from bokeh.models import (GeoJSONDataSource, HoverTool)


arrondissement= gpd.read_file("../good_data/mutation_paris/paris/arrondissements.shp")
paris_mutation= gpd.read_file("../good_data/data/filo_mutation/paris_mutation_filo.shp")

# Set up our data CRS
base_crs= {"init": "epsg:4326"}
paris_mutation.crs= base_crs
arrondissement.crs= base_crs

# Paris arrondissement plotting
def to_geojson(geopd):
    return GeoJSONDataSource(geojson= geopd.to_json())

geo_arr_json= to_geojson(arrondissement)
# geo_pmut_json= to_geojson(paris_mutation)

p= figure(title= "Paris", plot_height= 500, plot_width= 1000
          , toolbar_location= "above")

# Add arrondissement layer
arr= p.patches(source= geo_arr_json, fill_color= None
               , line_color= "black")
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.add_tools(HoverTool(tooltips= [("Arrondissement", "@l_aroff")]))

# Save into html file
output_file(r"./dashboard/paris_mutation.html")
save(obj= p)

