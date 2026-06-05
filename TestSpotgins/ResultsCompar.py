import pandas as pd 
import numpy as np
import os
import re 

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

def Open(dir_path):
    dic = {}
    for (root,dirs,file) in os.walk(dir_path):
        for d in sorted(dirs):
            for f in os.listdir(root + '/' + d):
                if f.endswith('.IPPP'):
                    path = f"{root}/{d}/{f}" 
                    dic[d]=(pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,names = cols))
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
    
        
    Xref = -2341332.129261
    Yref = -3539048.188331
    Zref =  4745792.713020
    
    lat, lon = heikkinen(Xref,Yref,Zref)
    print(lat*180/np.pi,lon*180/np.pi)

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
    
    Results_ENU = {}
    
    for key in Results:
        
        df = Results[key]
        X = df.iloc[0,4]
        Y = df.iloc[0,6]
        Z = df.iloc[0,8]
        
        dX = X-Xref
        dY = Y-Yref
        dZ = Z-Zref
        
        E = mat11*dX + mat12*dY + mat13*dZ
        N = mat21*dX + mat22*dY + mat23*dZ
        U = mat31*dX + mat32*dY + mat33*dZ  
        
        df_date = Results[key].iloc[[0],1:3]

        df_ENU = pd.DataFrame(np.array([E,N,U]).reshape(1,3),columns = ["E","N","U"])
        df_ENU = pd.concat([df_date,df_ENU],axis = 1)
        
        Results_ENU[key] = df_ENU
        
    return Results_ENU
    
if __name__ == "__main__":
    
    cols = ["# type","calendar  epoch","julian days(1950)","correction (X or lat)",
            "position (X or lat)","correction (Y or lon)","position (Y or lon)","correction (Z or h)",
            "position (Z or h)","cov11","cov22","cov33","cov21","cov31","cov32"]
    data = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_094832.260504_114926.gins.PPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    data2 = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_095248.260504_115338.gins.IPPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    
    
    ### Ouverturedes résultats Gins
    GinsResults = Open('../GinsResults')
    
    ### Comparaison avec la ref SHOM
    Diff_dic = Diff(GinsResults, data)
    
    ### Export
    d,useless = Tri(Diff_dic)
    
    export(d,useless,"../GinsResults/Changements_calcul")

    Gins_Results_ENU = convert(GinsResults)
    