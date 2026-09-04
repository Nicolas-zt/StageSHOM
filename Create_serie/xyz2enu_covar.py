#!/usr/bin/python

import numpy as np
import sys
import re

def print_usage():
    print()
    print(" *** use like that from GINS solution file ***")
    print()
    print("values=$(cat sol_file*.gins | grep XYZ | awk '{printf \"%.15e %.15e %.15e %.15e %.15e %.15e %.15e %.15e %.15e\\n\", $5, $7, $9, $10, $11, $12, $13, $14, $15}')")
    print("python xyz2enu_covar.py \"${values}\"")
    print()
    print("OR")
    print()
    print("values=$(cat sol_file*.gins | grep XYZ | awk '{printf \"%.15e %.15e %.15e %.15e %.15e %.15e\\n\", $10, $11, $12, $13, $14, $15}')")
    print("python xyz2enu_covar.py xref_val yref_val zref_val \"${values}\"")
    print()
    print("OR")
    print()
    print("python xyz2enu_covar.py xref_val yref_val zref_val cov11_val cov22_val cov33_val cov12_val cov13_val cov23_val")
    print()
    print(" *** ------------------------------------- ***")


if len(sys.argv[1:]) == 1:
#option for a huge set of covariance matrices to transform
    a = sys.argv[1]
    raw=int(len(re.split(" |\n",a))/9)
    XYZ = np.reshape([float(j) for i in a.split("\n") for j in i.split(" ")],(raw,9))
    Xref=XYZ[:,0]
    Yref=XYZ[:,1]
    Zref=XYZ[:,2]
    cov11=XYZ[:,3]
    cov22=XYZ[:,4]
    cov33=XYZ[:,5]
    cov12=XYZ[:,6]
    cov13=XYZ[:,7]
    cov23=XYZ[:,8]
    pr=1
elif len(sys.argv[1:]) == 4:
#option for a huge set of covariance matrices to transform
    a = sys.argv[-1]
    raw=int(len(re.split(" |\n",a))/6)
    XYZ = np.reshape([float(j) for i in a.split("\n") for j in i.split(" ")],(raw,6))
    Xref=float(sys.argv[1])
    Yref=float(sys.argv[2])
    Zref=float(sys.argv[3])
    cov11=XYZ[:,0]
    cov22=XYZ[:,1]
    cov33=XYZ[:,2]
    cov12=XYZ[:,3]
    cov13=XYZ[:,4]
    cov23=XYZ[:,5]
    pr=1
elif len(sys.argv[1:]) == 9:
#option for 1 set of covariance matrix to transform
    #position of point
    Xref=float(sys.argv[1])
    Yref=float(sys.argv[2])
    Zref=float(sys.argv[3])
    #covariance of xyz coordinates
    cov11=float(sys.argv[4])
    cov22=float(sys.argv[5])
    cov33=float(sys.argv[6])
    cov12=float(sys.argv[7])
    cov13=float(sys.argv[8])
    cov23=float(sys.argv[9])
    pr=0
else:
    print("ERROR : wrong format for input data in the script !")
    print_usage()
    exit()

#earth ellipsoid definition
a=6378137.0000 #m
b=6356752.3142 #m

#Ferrari method with Heikkinen algo
#[Zhu 1994 : Conversion of Earth-centered Earth-fixed coordinates to geodetic coordinates]
def heikkinen(X1,Y1,Z1):
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

lat, lon = heikkinen(Xref,Yref,Zref)

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

#version allowing vectorization
#resultats de S_xyz @ mat.T
interm11 = cov11*mat11 + cov12*mat12 + cov13*mat13
interm12 = cov11*mat21 + cov12*mat22 + cov13*mat23
interm13 = cov11*mat31 + cov12*mat32 + cov13*mat33
interm21 = cov12*mat11 + cov22*mat12 + cov23*mat13
interm22 = cov12*mat21 + cov22*mat22 + cov23*mat23
interm23 = cov12*mat31 + cov22*mat32 + cov23*mat33
interm31 = cov13*mat11 + cov23*mat12 + cov33*mat13
interm32 = cov13*mat21 + cov23*mat22 + cov33*mat23
interm33 = cov13*mat31 + cov23*mat32 + cov33*mat33
# S_enu = mat @ S_xyz @ mat.T
cov11_enu = mat11*interm11 + mat12*interm21 + mat13*interm31
cov22_enu = mat21*interm12 + mat22*interm22 + mat23*interm32
cov33_enu = mat31*interm13 + mat32*interm23 + mat33*interm33
cov12_enu = mat11*interm12 + mat12*interm22 + mat13*interm32
cov13_enu = mat11*interm13 + mat12*interm23 + mat13*interm33
cov23_enu = mat21*interm13 + mat22*interm23 + mat23*interm33

#display results
print("ENU")
if pr==0:
    print(cov11_enu,cov22_enu,cov33_enu,cov12_enu,cov13_enu,cov23_enu)
else:
    for i in range(len(cov11_enu)):
        print(cov11_enu[i],cov22_enu[i],cov33_enu[i],cov12_enu[i],cov13_enu[i],cov23_enu[i])



