import pandas as pd 
import numpy as np


def Compar(f1,f2):
    
    df1, df2 = f1.align(f2)
    compar = (df1 == df2).to_numpy()
    ratio = np.sum(compar)/f1.size*100
    
    return ratio
    
if __name__ == "__main__":
    
    data = pd.read_csv("ALBH00CAN.enu",comment = "#",delimiter = "\s+",header = None,usecols=[0,1,2,3,4,5,6])
    data2 = pd.read_csv("SPOTGINS_ALBH00CAN.enu",comment = "#",delimiter = "\s+",header = None,usecols=[0,1,2,3,4,5,6])
    
    test = Compar(data,data2)