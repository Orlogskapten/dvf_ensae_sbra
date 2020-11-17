import geopandas as gpd
import pandas as pd

paris_mutation= gpd.read_file("zip://paris_arr.zip!paris_arr.shp")

datmut_serie= pd.to_datetime(pd.Series(paris_mutation["datemut"]), format= "%Y-%m-%d")
paris_mutation["datemut"]= gpd.GeoSeries(datmut_serie)
paris_mutation["valeur_per_met"]= paris_mutation["valeurfonc"] / paris_mutation["sbati"]

print(paris_mutation.info())

grouped_price_time= paris_mutation[["valeurfonc", "sbati", "pp", "valeur_per_met", "datemut"]]\
    .groupby(["datemut"], as_index= False)

grouped_price_time_mean= grouped_price_time.mean()
grouped_price_time_median= grouped_price_time.median()

grouped_price_time_median.to_csv("grouped_price_time_median.csv")
grouped_price_time_mean.to_csv("grouped_price_time_mean.csv")

print(grouped_price_time_median.head())
print(grouped_price_time_mean.head())
