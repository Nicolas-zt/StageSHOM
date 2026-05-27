import pandas as pd 
import numpy as np
import os

def Compar(f1,f2):
    
    df1, df2 = f1.align(f2)
    compar = (df1 == df2).to_numpy()
    ratio = np.sum(compar)/f1.size*100
    
    return ratio

def Diff(df_list,ref):
    List = []
    for df in df_list:
        
        dfc = df.copy()
        dfc.iloc[:,3:] = np.abs(dfc.iloc[:,3:] - ref.iloc[:,3:])
        List.append(dfc)
        
    return List

def Open(dir_path):
    List = []
    for (root,dirs,file) in os.walk(dir_path):
        for d in sorted(dirs):
            print(d)
            for f in os.listdir(root + '/' + d):
                if f.endswith('.PPP'):
                    path = f"{root}/{d}/{f}"
                    
                    List.append(pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,names = cols))
                    
    return List
if __name__ == "__main__":
    
    cols = ["# type","calendar  epoch","julian days(1950)","correction (X or lat)",
            "position (X or lat)","correction (Y or lon)","position (Y or lon)","correction (Z or h)",
            "position (Z or h)","cov11","cov22","cov33","cov21","cov31","cov32"]
    data = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_094832.260504_114926.gins.PPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    data2 = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_095248.260504_115338.gins.IPPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    
    
    ### Ouverturedes résultats Gins
    GinsResults = Open('../GinsResults')
    
    ### Comparaison avec la ref SHOM
    Diff_list = Diff(GinsResults, data)
    
    