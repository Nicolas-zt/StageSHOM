import numpy as np 
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
from shapely.geometry import Point
from shapely.ops import unary_union

def OutSta(Source,Networks):
    
    OUT_sta = []
    
    #Stations NGL hors SONEL
    for index,row in Source.iterrows():
        c=0
        for n in Networks:
            try :
                if row["code"] not in n.values:
                    c += 1
            except:
                if row["four_char_id"] not in n.values:
                    c += 1
        if c == len(Networks):
            OUT_sta.append(row)
            
    OUT_sta = pd.DataFrame(OUT_sta)
    
    return OUT_sta

def InSta(Source,Networks):
    
    OUT_sta = []
    
    #Stations NGL hors SONEL
    for index,row in Source.iterrows():
        c=0
        for n in Networks:
            if row["code"] in n.values:
                c += 1
        if c == len(Networks):
            OUT_sta.append(row)
            
    OUT_sta = pd.DataFrame(OUT_sta)
    
    return OUT_sta

def Coast_sta(Sta,dmax,plot = False):
    
    global coast
    
    #Conversion GeoDataFrame
    for col in Sta.columns:
        if col.lower().startswith('lon'):
            Lon = col
        elif col.lower().startswith('lat'):
            Lat = col
    Sta["geometry"] = Sta.apply(lambda row: Point(row[Lon],row[Lat]),axis = 1)
    Sta = geopandas.GeoDataFrame(Sta,geometry="geometry",crs=4326)
    
    #Calcul des distances à la côte
    coast = coast.to_crs(epsg = 32662)
    Sta = Sta.to_crs(epsg = 32662)
    coast_union = coast.unary_union
    Sta['dist'] = Sta['geometry'].apply(lambda point: point.distance(coast_union))
    
    mask = Sta["dist"]<=dmax
    Coast_sta = Sta[mask]
    
    if plot :
        #PLOTS
        coast.plot(figsize=(22,20), edgecolor='gray',alpha = 0.5)
        Sta[mask].plot(ax=plt.gca(), color='red', markersize=10,alpha = 0.5,label = 'Stations côtières')
        plt.title(f"Stations à moins de {dmax}m des côtes")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.legend()
        # plt.savefig(f"StaMap_{dmax}m")
        plt.show()
    
    return Coast_sta

def InFrance(Sta):
    
    #Stations en France 
    FR = France.to_crs(epsg = 32662).unary_union
    Sta['dist_to_france'] = Sta['geometry'].apply(lambda point: point.distance(FR))
    FR_sta = Sta[Sta['dist_to_france']<=500]

    
    return FR_sta

if __name__ == "__main__":
    
    #Ouverture des fichiers csv
    NGL = pd.read_csv("NGL_sta.txt",header = None,sep = '\s+',names=['code','Lat','Lon','he'])
    SPOTGINS = pd.read_csv("SPOTGINS_sta.csv",sep=',',header = 0,skiprows = 2)
    SONEL = pd.read_csv("SONEL_sta.csv",sep = ';',skiprows=10,encoding='latin-1')
    RGP = pd.read_csv("rgp_sta.txt",header = None)
    RGP_OLD = pd.read_csv("rgp_sta_old.txt",header = None)
    IGS = pd.read_json("IGSNetwork.json").transpose()
    RENAG = pd.read_csv("Liste_stations_RENAG_Orpheon_lMIqvgp.csv",sep = ';')
    #Ouverture des Shapefile
    coast = geopandas.read_file('QGIS/ne_10m_coastline.shp')
    countries = geopandas.read_file('QGIS/ne_10m_admin_0_countries.shp')
    France = countries[countries['SOVEREIGNT'] == 'France']['geometry']
            
    #Selection des stations
    SONEL_sta = SONEL["gps_code"]
    SPOTGINS_sta = SPOTGINS["NAME"].str[9:13]
    IGS_sta = IGS.index.str[0:4]
    
    NGL_Hors_SONEL = OutSta(NGL,[SONEL_sta,SPOTGINS_sta])
    NGL_Hors_SONEL_côte = Coast_sta(NGL_Hors_SONEL, 1000,plot = True)
    
    #Toutes les stations RENAG sont dans SONEL ou SPOTGINS
    Renag_Hors_Sonel= OutSta(RENAG, [SONEL_sta,SPOTGINS_sta])
    Renag_Hors_Sonel_cote = Coast_sta(Renag_Hors_Sonel, 1000,plot = True)
    



    

