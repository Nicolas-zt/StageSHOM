import numpy as np 
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
from shapely.geometry import Point

if __name__ == "__main__":
    
    #Ouverture des fichiers csv
    NGL = pd.read_csv("NGL_sta.txt",header = None,sep = '\s+',names=['code','Lat','Lon','he'])
    SPOTGINS = pd.read_csv("SPOTGINS_sta.csv",sep=',',header = 0,skiprows = 2)
    SONEL = pd.read_csv("SONEL_sta.csv",sep = ';',skiprows=10,encoding='latin-1')
    RGP = pd.read_csv("rgp_sta.txt",header = None)
    RGP_OLD = pd.read_csv("rgp_sta_old.txt",header = None)
    
    #Ouverture du Shapefile
    coast = geopandas.read_file('ne_10m_coastline.shp')
    
    
    #Selection des stations
    SONEL_sta = SONEL["gps_code"]
    SPOTGINS_sta = SPOTGINS["NAME"].str[9:13]
    
    OUT_sta = []
    
    #Stations NGL hors SONEL
    for index,row in NGL.iterrows():
        if row[0] not in SONEL_sta.values and row[0] not in SPOTGINS_sta.values:
            OUT_sta.append(row)
            
    OUT_sta = pd.DataFrame(OUT_sta)
    #Conversion GeoDataFrame
    OUT_sta["geometry"] = OUT_sta.apply(lambda row: Point(row['Lon'],row['Lat']),axis = 1)
    OUT_sta = geopandas.GeoDataFrame(OUT_sta,geometry="geometry",crs=4326)
    
    #Calcul des distances à la côte
    coast = coast.to_crs(epsg = 32662)
    OUT_sta = OUT_sta.to_crs(epsg = 32662)
    coast_union = coast.unary_union
    OUT_sta['dist'] = OUT_sta['geometry'].apply(lambda point: point.distance(coast_union))
    
    
    dmax = 1000
    
    mask = OUT_sta["dist"]<=dmax
    verif = OUT_sta[mask]
    coast.plot(figsize=(22,20), edgecolor='black',alpha = 0.5)
    OUT_sta[mask].plot(ax=plt.gca(), color='red', markersize=10,alpha = 1)  # les points sont dans le même CRS
    plt.title(f"Stations hors SONEL à moins de {dmax}m des côtes")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()
    

