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
                if f.endswith('.PPP'):
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
            print(diff[0].iloc[:,3:])
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
    