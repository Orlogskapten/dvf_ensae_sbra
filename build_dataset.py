import geopandas as gpd
import pandas as pd

base_crs= {"init": "epsg:4326"}

arrondissement= gpd.read_file("arrondissements.shp")
# https://geopandas.org/io.html
paris_mutation= gpd.read_file("zip://paris_mutation_filo.zip!paris_mutation_filo.shp")
score_arrondissement= pd.read_csv("score_per_arr.csv")

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

paris_arr["Securite"]= paris_arr["Sécurité"]
paris_arr["Sante"]= paris_arr["Santé"]
paris_arr["Qualite de vie"]= paris_arr["Qualité de vie"]
paris_arr.drop(columns= ["Sécurité", "Santé", "Qualité de vie"], inplace= True)


# Set up our data CRS
paris_mutation.crs= base_crs
arrondissement.crs= base_crs
paris_arr.crs= base_crs

base_arr_col= ["c_ar"]
var_arr_col= ["valeurfonc", "Ind", "Men", "Men_pauv", "Men_prop","Men_fmp", "Ind_snv", "Men_surf", "Men_coll"
    , "Men_mais", "sbati", "pp", "valeur_metre_carre", "Note global", "Qualite de vie", "Commerces", "Enseignement"
    , "Culture", "Sports et loisirs", "Sante", "Securite", "Transports", "Environnement"]


menage_per_arr= paris_arr[base_arr_col+var_arr_col].groupby(base_arr_col, as_index= False)
menage_per_arr_mean= menage_per_arr.mean()
menage_per_arr_count= menage_per_arr.size().reset_index(name= "counts")
# Add num mutation per arrondissement into our principal dataset
menage_per_arr_mean= menage_per_arr_mean.merge(menage_per_arr_count, on= "c_ar")
del menage_per_arr_count

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

# print(menage_per_arr_mean.info())
menage_per_arr_mean.to_file("menage_per_arr_mean.shp")
# paris_arr.to_file("paris_arr.shp")

