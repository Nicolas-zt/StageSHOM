import numpy as np 
import pandas as pd

if __name__ == "__main__":
    
    PPP = pd.read_csv("ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_094832.260504_114926.gins.PPP",
                      sep = "\s+",skiprows=9,header = None,
                      names = ['type','calendar  epoch','julian days(1950)' ,'correction (X or lat)',
                               'position (X or lat)','correction (Y or lon)','position (Y or lon)',
                               'correction (Z or h)', 'position (Z or h)', 'cov11', 'cov22', 'cov33',                 
                               'cov21', 'cov31','cov32'])