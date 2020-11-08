import folium

center = [48.862, 2.346]
paris = folium.Map(center, zoom_start = 12, width= 800, height= 500)

paris.save("paris_map.html")