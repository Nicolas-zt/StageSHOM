#!/usr/bin/python

import numpy as np
import sys
import re

def print_usage():
    print()
    print(" *** use like that from GINS solution file ***")
    print()
    print("values=$(cat sol_file*.gins | grep XYZ | awk '{printf \"%.15e %.15e %.15e %.15e %.15e %.15e\\n\", $5-$4, $7-$6, $9-$8, $5, $7, $9}')")
    print("python xyz2enu_coord.py \"${values}\"")
    print()
    print("OR")
    print()
    print("values=$(cat sol_file*.gins | grep XYZ | awk '{printf \"%.15e %.15e %.15e\\n\", $5, $7, $9}')")
    print("python xyz2enu_coord.py xref_val yref_val zref_val \"${values}\"")
    print()
    print("OR")
    print()
    print("python xyz2enu_covar.py xref_val yref_val zref_val x_val y_val z_val")
    print()
    print(" *** ------------------------------------- ***")


if len(sys.argv[1:]) == 1:
#option for a huge set of coordinates to transform
    a = sys.argv[1]
    raw=int(len(re.split(" |\n",a))/6)
    XYZ = np.reshape([float(j) for i in a.split("\n") for j in i.split(" ")],(raw,6))
    Xref=XYZ[:,0]
    Yref=XYZ[:,1]
    Zref=XYZ[:,2]
    X=XYZ[:,3]
    Y=XYZ[:,4]
    Z=XYZ[:,5]
    pr=1
elif len(sys.argv[1:]) == 4:
#option for a huge set of coordinates to transform
    a = sys.argv[-1]
    raw=int(len(re.split(" |\n",a))/3)
    XYZ = np.reshape([float(j) for i in a.split("\n") for j in i.split(" ")],(raw,3))
    Xref=float(sys.argv[1])
    Yref=float(sys.argv[2])
    Zref=float(sys.argv[3])
    X=XYZ[:,0]
    Y=XYZ[:,1]
    Z=XYZ[:,2]
    pr=1
elif len(sys.argv[1:]) == 6:
#option for 1 set of coordinates to transform
    #reference for point
    Xref=float(sys.argv[1])
    Yref=float(sys.argv[2])
    Zref=float(sys.argv[3])
    #real position of point
    X=float(sys.argv[4])
    Y=float(sys.argv[5])
    Z=float(sys.argv[6])
    pr=0
else:
    print("ERROR : wrong format for input data in the script !")
    print_usage()
    exit()

#differences
dX = (X-Xref)
dY = (Y-Yref)
dZ = (Z-Zref)




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
E = mat11*dX + mat12*dY + mat13*dZ
N = mat21*dX + mat22*dY + mat23*dZ
U = mat31*dX + mat32*dY + mat33*dZ

#display results
print("ENU")
if pr==0:
    print(E,N,U)
else:
    for i in range(len(E)):
        print(E[i], N[i], U[i])



