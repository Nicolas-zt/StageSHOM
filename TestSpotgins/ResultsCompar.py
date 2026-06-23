import pandas as pd 
import numpy as np
import os
import pyproj

def Compar(f1,f2):
    
    df1, df2 = f1.align(f2)
    compar = (df1 == df2).to_numpy()
    ratio = np.sum(compar)/f1.size*100
    
    return ratio

def Diff(df_dic,ref):
    dic = {}
    for key in df_dic:
        
        df = df_dic[key]
        dfc = df.copy()
        dfc.iloc[:,3:] = np.abs(dfc.iloc[:,3:] - ref.iloc[:,3:])
        dic[key] = (dfc)
        
    return dic

def Diff_SPOTGINS(df,df_ref):
    df = df.iloc[:,1:].astype(float)
    df_ref = df_ref.iloc[-8:,1:4]
    
    diff = abs(df.reset_index() - df_ref.reset_index()).iloc[:,1:]
    
    return diff
    

def Open_IPPP(dir_path):
    dic = {}
    for (root,dirs,file) in os.walk(dir_path):
        for d in sorted(dirs):
            for f in os.listdir(root + '/' + d):
                if f.endswith('.IPPP'):
                    path = f"{root}/{d}/{f}" 
                    df = pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,names = cols)
                    try :
                        dic[d] = pd.concat((dic[d],df))
                    except:
                        dic[d]= df
    return dic

def Open_enu(dir_path):
    dic = {}
    for (root,dirs,file) in os.walk(dir_path):
        for d in sorted(dirs):
            for f in os.listdir(root + '/' + d):
                if f.endswith('.enu'):
                    path = f"{root}/{d}/{f}" 
                    df = pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,usecols = [0,1,2,3,10],names = ["MJD","E","N","U","date"])
                    dic[f]= df
    return dic

def Open(dir_path,ext):
    dic = {}
    for (root,dirs,file) in os.walk(dir_path):
        for d in sorted(dirs):
            for f in os.listdir(root + '/' + d):
                if f.endswith(f'.{ext}'):
                    path = f"{root}/{d}/{f}" 
                    if  ext == 'IPPP' :
                        df = pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,names = cols)
                        try :
                            dic[d] = pd.concat((dic[d],df))
                        except:
                            dic[d]= df
                    elif ext == 'enu':
                        df = pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,usecols = [0,1,2,3,10],names = ["MJD","E","N","U","date"])
                        dic[f]= df
                    elif ext == 'txt':
                        nom = f[:23]
                        with open(path,'r') as f:
                            xyz = []
                            date = []
                            sys = []
                            for line in f:
                                if line.startswith('GEOC_POS'):
                                    xyz.append(line.split()[1:])
                                if line.startswith('GEOD_SYS'):
                                    date.append([line.split()[2]])
                                    sys.append(line.split()[1])
                            df = pd.DataFrame([date[0]+xyz[0]],columns=['Date','X','Y','Z'],dtype=float)
                            df["SysRef"] = [sys[0]]
                            df['Date'] = df['Date'].round(4)
                            df['Station'] = [d]
                            df['Nom_Rinex'] = [nom]
                            try:
                                Data = pd.concat((Data,df))
                            except:
                                Data = df
    if ext == 'txt':
        return Data.reset_index(drop=True)
    else:
        return dic

def Tri(diff_dic):
    d = {}
    useless = []
    values = list(diff_dic.values())
    keys = list(diff_dic.keys())
    for i,v in enumerate(values):
        f = keys[i]
        diff = Diff({0:values[i-1]},values[i])
        if 0.0 not in diff[0].to_numpy():
            diff_dic[f].to_csv(f"../GinsResults/{f}.csv")
            d[f] = diff[0]
        else:
            useless.append(f)
    return d,useless

def export(export_list,useless_params,path):
    
    with open(path,"w") as f:
        
        for key in export_list:
            f.write("="*80 + f" Influence sur le calcul du {key} " + "="*80)
            f.write("\n")
            f.write(export_list[key].to_string())
            f.write("\n"*4)
            
        f.write("Paramètres n'ayant pas changé le calcul :" + "\n"*2)
        for param in useless_params:
            
            f.write(param[7:] + "\n")
        
def heikkinen(X1,Y1,Z1):
    
    a=6378137.0000 #m
    b=6356752.3142 

    e2 = (a**2 - b**2) / (a**2)
    ep2 = (a**2 - b**2) / (b**2)
    p=np.sqrt(X1**2+Y1**2)
    F=54*b**2*Z1**2
    G=p**2+(1.-e2)*Z1**2 - e2*(a**2-b**2)
    c=e2**2*F*p**2/G**3
    s=np.cbrt((1.+c+np.sqrt(c**2+2.*c)))
    k=s+1.+(1./s)
    P=F/(3.*k**2*G**2)
    Q=np.sqrt(1.+2.*P*e2**2)
    r0=-(P*e2*p)/(1+Q) + np.sqrt(0.5*a**2*(1.+1./Q) - (P*(1.-e2)*Z1**2)/(Q*(1.+Q)) - 0.5*P*p**2)
    U=np.sqrt(Z1**2 + (p-e2*r0)**2)
    V=np.sqrt((1.-e2)*Z1**2 + (p-e2*r0)**2)
    z0=b**2*Z1/(a*V)

    lat=np.arctan((Z1+ep2*z0)/p)
    lon=np.arctan2(Y1,X1)

    return lat, lon

def convert(Results):
    
    refs = [[-2341332.129261 , -3539048.188331 , 4745792.713020 ],
            [4917537.991116  , -815726.306152  , 3965856.072655 ],
            [-3950072.510418 ,  2522415.723761 , -4311636.991987],
            [2612632.988907  , -3426809.705573 , 4686754.886249 ],
            [4331297.348000  ,  567555.639000  , 4633133.728000 ]]
           
    Results_ENU = {}
    
    for key in Results:
        
        df = Results[key]

        
        array = []
        nb_row = 0
        
        for index,row in df.iterrows():
            
            if nb_row%3 == 0 :
            
                X = row.iloc[4]
                Y = row.iloc[6]
                Z = row.iloc[8]
                date = row.iloc[1]
                
                for ref in refs:
                    
                    Xref = ref[0]
                    Yref = ref[1]
                    Zref = ref[2]
                    lat, lon = heikkinen(Xref,Yref,Zref)   
                    dX = X-Xref
                    dY = Y-Yref
                    dZ = Z-Zref
                    
                    if abs(dX) < 10 :
                        #matrix elements
                        mat11=-np.sin(lon)
                        mat12=+np.cos(lon)
                        mat13=0.
                        mat21=-np.sin(lat)*np.cos(lon)
                        mat22=-np.sin(lat)*np.sin(lon)
                        mat23=+np.cos(lat)
                        mat31=+np.cos(lat)*np.cos(lon)
                        mat32=+np.cos(lat)*np.sin(lon)
                        mat33=+np.sin(lat)
                
                        E = mat11*dX + mat12*dY + mat13*dZ
                        N = mat21*dX + mat22*dY + mat23*dZ
                        U = mat31*dX + mat32*dY + mat33*dZ  
                        
                        array.append([date,E,N,U])
            nb_row += 1
            
        df_ENU = pd.DataFrame(np.array(array).reshape(nb_row//3,4),columns = ["date","E","N","U"])
        
        Results_ENU[key] = df_ENU
        
    return Results_ENU

def ComparStaSHOM(df):
    
    GRG = df[df['Station']=='GRG']
    SPOTGINS = df.drop(df[df['Station']=='GRG'].index)
    
    return SPOTGINS,GRG


if __name__ == "__main__":
    
    cols = ["# type","calendar  epoch","julian days(1950)","correction (X or lat)",
            "position (X or lat)","correction (Y or lon)","position (Y or lon)","correction (Z or h)",
            "position (Z or h)","cov11","cov22","cov33","cov21","cov31","cov32"]
    data = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_094832.260504_114926.gins.PPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    data2 = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_095248.260504_115338.gins.IPPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    
    
    ### Ouverture des résultats Gins
    GinsResults = Open('../GinsResults/','IPPP')
    
    ### Ouverture des résultats SPOTGINS
    SPOTGINSResults = Open('../GinsResults','enu')
    
    ### Ouverture des stations SHOM
    SHOMResults = Open('../RecalculSHOM/ComparDir','txt')
    
    ### Comparaison avec la ref SHOM
    # Diff_dic = Diff(GinsResults, data2)
    
    ### Export
    # d,useless = Tri(Diff_dic)
    
    # export(d,useless,"../GinsResults/Changements_calcul")

    #Ecarts de calcul entre la nouvelle chaine SHOM et SPOTGINS
    Gins_Results_ENU = convert(GinsResults)
    Sta = ['ALBH','CASC','HOB2','STJO']
    diff = []
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["ALBH_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["ALBH00CAN.enu"]))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["CASC_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["CASC00PRT.enu"]))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["HOB2_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["HOB200AUS.enu"]))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["STJO_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["STJO00CAN.enu"]))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["zimm_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["ZIMM00CHE.enu"]))
    # for i,d in enumerate(diff):
    #     d.to_latex(f'{Sta[i]}.tex',index=False,header=['Ecart en Est','Ecart en Nord','Ecart en Up'])
    # diff[0].to_latex('ZIMM.tex',index=False,header=['Ecart en Est','Ecart en Nord','Ecart en Up'])

    #Ecarts de calcul entre les deux versions SHOM
    ComparSHOM = ComparStaSHOM(SHOMResults)
    
    All = ComparSHOM[0].join(ComparSHOM[1].set_index('Nom_Rinex'),on='Nom_Rinex',lsuffix='_SPOTGINS',rsuffix='_GRG',how='inner')
    SHOM_Diff = abs(All.iloc[:,1:4].rename(columns={'X_SPOTGINS': 'X', 'Y_SPOTGINS': 'Y', 'Z_SPOTGINS': 'Z'})  - All.iloc[:,8:11].rename(columns={'X_GRG': 'X', 'Y_GRG': 'Y', 'Z_GRG': 'Z'}))
    SHOM_Diff['Nom_Rinex'] = All['Nom_Rinex']
    # SHOM_Diff.to_latex("DiffSHOM",index=False,header=['Ecart en X','Ecart en Y','Ecart en Z','Nom'],longtable=True)
    transformer = pyproj.Transformer.from_crs(crs_from=9988,crs_to=4326,always_xy=True)
    All['E_WGS84'],All['N_WGS84'],All['H_WGS84'] = transformer.transform(All['X_SPOTGINS'],All['Y_SPOTGINS'],All['Z_SPOTGINS'])
    noms=[]
    for name in All['Nom_Rinex']:
        noms.append(name[:4])
    All['Nom_Station']=noms