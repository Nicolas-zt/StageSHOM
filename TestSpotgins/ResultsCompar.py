import pandas as pd 
import numpy as np
import os
import pyproj
import matplotlib.pyplot as plt
import re

def Compar(f1,f2):
    
    df1, df2 = f1.align(f2)
    compar = (df1 == df2).to_numpy()
    ratio = np.sum(compar)/f1.size*100
    
    return ratio

def Diff(df_dic,ref):
    dic = {}
    for key in df_dic:
        if str(key).startswith('TEST'):
            if len(df_dic[key]) <= 3:
                df = df_dic[key]
                dfc = df.copy()
                dfc.iloc[:,3:] = np.abs(dfc.iloc[:,3:] - ref.iloc[:,3:])
                dic[key] = (dfc)
        
    return dic

def Diff_SPOTGINS(df,df_ref,n):
    date = df['date']
    for i,d in enumerate(date):
        date.iloc[i] = d[5:10]
    df = df.iloc[:,1:].astype(float)
    df_ref = df_ref.iloc[-n:,1:4]

    
    diff = (df.reset_index() - df_ref.reset_index()).iloc[:,1:]
    diff['date']=date
    
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
                        df = pd.read_csv(path,comment = "#",delimiter = "\s+",header = None,usecols = [0,1,2,3,4,5,6,11],names = ["MJD","E","N","U","SE","SN","SU","Date"])
                        dic[f]= df
                    elif ext == 'txt':
                        patterns = [
                        (r'.*_([0-9]{4}_[0-9]{3}).*([0-9]{6}_[0-9]{6}).*PPP',
                         lambda m: f"{m.group(1)} {m.group(2)}"),
                    
                        (r'.*_R_([0-9]{4})([0-9]{3})[0-9]{4}.*([0-9]{6}_[0-9]{6}).*PPP',
                         lambda m: f"{m.group(1)}_{m.group(2)} {m.group(3)}"),
                    
                        (r'^[a-z0-9]{4}([0-9]{3})[0-9]\.([0-9]{2})o.*([0-9]{6}_[0-9]{6}).*PPP',
                         lambda m: f"20{m.group(2)}_{m.group(1)} {m.group(3)}"),
                        ]
                        
                        for pattern, replacement in patterns:
                            match = re.match(pattern, f)
                            if match:
                                Doy,Doe = replacement(match).split()
                                break
                        nom = re.findall(".*yml",f)[0]
                        day=f[10:17]
                        with open(path,'r') as file:
                            xyz = []
                            cov = []
                            date = []
                            sys = []
                            for line in file:
                                if line.startswith('GEOC_POS'):
                                    xyz.append(line.split()[1:])
                                if line.startswith('GEOC_COV'):
                                    cov.append(line.split()[1:])
                                if line.startswith('GEOD_SYS'):
                                    date.append([line.split()[2]])
                                    sys.append(line.split()[1])
                            df = pd.DataFrame([date[0]+xyz[0]+cov[0]],columns=['Date','X','Y','Z','vX','vY','vZ','covXY','covXZ','covYZ'],dtype=float)
                            df["SysRef"] = [sys[0]]
                            df['Date'] = df['Date']
                            df['Station'] = [f"{nom[:4].upper()}_{Doy}"]
                            df['DateOfExe']=[Doe]
                            df['Dossier']=[d]
                            try:
                                Data = pd.concat((Data,df))
                            except:
                                Data = df
                    elif ext == 'ztd':
                        df = pd.read_csv(path,comment = '#', delimiter = '\s+',usecols=[0,1,2,3],names=['MJD','TROTOT','TRODRY','TROWET'],dtype=float)
                        df['MJD']=df['MJD'].round(3)
                        dic[f] = df
                    elif ext == 'grad':
                        df = pd.read_csv(path,comment = '#', delimiter = '\s+',usecols=[0,1,3],names=['MJD','TGNTOT','TGETOT'],dtype=float)
                        df['MJD']=df['MJD'].round(3)
                        dic[f] = df
                    elif ext =='xyz':
                        df = pd.read_csv(path,delimiter = '\s+',usecols=[0,2,3,4,5,6,7,8,9,10,11],names=['Sta','Date','X','Y','Z','vX','vY','vZ','corrXY','corrYZ','corrXZ'])
                        dic[f] = df
    if ext == 'txt':
        return Data.reset_index(drop=True)
    else:
        return dic

def Tri(diff_dic,ref):
    d = {}
    useless = []
    values = list(diff_dic.values())
    keys = list(diff_dic.keys())
    for i,v in enumerate(values):
        f = keys[i]
        if i >= 1:
            diff = Diff({'TEST':values[i-1]},values[i])
        else :
            continue
        if 0.0 not in diff['TEST'].to_numpy():
            # diff_dic[f].to_csv(f"../GinsResults/{f}.csv")
            d[f] = diff['TEST']
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
    
    GRG = df[df['Dossier']=='GRG']
    SPOTGINS = df.drop(df[df['Dossier']=='GRG'].index)
    
    return SPOTGINS,GRG

def corr(A,B):
    EA = np.mean(A)
    sigmaA = np.std(A)
    EB = np.mean(B)
    sigmaB = np.std(B)
    covAB = EA*EB - np.mean(A*B)
    
    corrAB = covAB/(sigmaA*sigmaB)
    
    return corrAB

def EcartsSHOM():
    
    ComparSHOM = ComparStaSHOM(SHOMResults)
    
    # Création du dataframe comprenant l'ancienne et la nouvelle solution SHOM sur chaque ligne
    All = ComparSHOM[0].join(ComparSHOM[1].set_index('Station'),on='Station',lsuffix='_SPOTGINS',rsuffix='_GRG',how='inner')
    All = pd.merge(ComparSHOM[0],ComparSHOM[1],left_on = 'Station',right_on='Station',suffixes=('_SPOTGINS','_GRG'))
    noms=[]
    for name in All['Station']:
        noms.append(name[:4])
    All['Nom_Station']=noms

    #Différences de coordonnées ENU centré sur la solution GRG

    
    suffix = ['_SPOTGINS','_GRG']
    for s in suffix :
        
        E=[]
        N=[]
        U=[] 
        vE = []
        vN = []
        vU = []
        
        for index,row in All.iterrows():
        
            Xref = row['X_GRG']
            Yref = row['Y_GRG']
            Zref = row['Z_GRG']
            X = row['X_SPOTGINS']
            Y = row['Y_SPOTGINS']
            Z = row['Z_SPOTGINS']
            lat, lon = heikkinen(Xref,Yref,Zref)   
            dX = X-Xref
            dY = Y-Yref
            dZ = Z-Zref
            
    
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
    
            E.append(mat11*dX + mat12*dY + mat13*dZ)
            N.append(mat21*dX + mat22*dY + mat23*dZ)
            U.append(mat31*dX + mat32*dY + mat33*dZ)  
            
            cov11 = row[f"vX{s}"]
            cov22 = row[f"vY{s}"]
            cov33 = row[f"vZ{s}"]
            cov12 = row[f"covXY{s}"]
            cov13 = row[f"covXZ{s}"]
            cov23 = row[f"covYZ{s}"]
            
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
                
            vE.append(cov11_enu)
            vN.append(cov22_enu)
            vU.append(cov33_enu)
            
        All[f'vE{s}']=vE
        All[f'vN{s}']=vN
        All[f'vU{s}']=vU
        All['E']=E
        All['N']=N
        All['U']=U

    
    # Différences de coordonnées XYZ
    # SHOM_Diff = abs(All.iloc[:,1:4].rename(columns={'X_SPOTGINS': 'dX', 'Y_SPOTGINS': 'dY', 'Z_SPOTGINS': 'dZ'})  - All.iloc[:,14:17].rename(columns={'X_GRG': 'dX', 'Y_GRG': 'dY', 'Z_GRG': 'dZ'}))
    # SHOM_Diff['Nom_Rinex'] = All['Nom_Rinex']
    # SHOM_Diff['Nom_Station'] = All['Nom_Station']
    # SHOM_Diff.to_latex("DiffSHOM",index=False,header=['Ecart en X','Ecart en Y','Ecart en Z','Nom'],longtable=True)
    transformer = pyproj.Transformer.from_crs(crs_from=9988,crs_to=4326,always_xy=True)
    All['E_WGS84'],All['N_WGS84'],All['H_WGS84'] = transformer.transform(All['X_GRG'],All['Y_GRG'],All['Z_GRG'])
    ### Ajout de FixAmbis dans All
    FixAmbis["Station"]=FixAmbis["STATION"] + '_' + FixAmbis["DATE"]
    All = pd.merge(All,FixAmbis,on='Station',suffixes=('_G','_R'))
    
    
    seuil = 0.001
    
    n = len(All)
    milieu = n // 2
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 11))
    
    for ax, df in zip(
        [ax1, ax2],
        [All.iloc[:milieu], All.iloc[milieu:]]
    ):
    
        x = np.arange(len(df))
        width = 0.9
        ax.bar(x - width/3,df['E_G'],width/3, label='dE')
        ax.bar(x,df['N'], width/3, label='dN')
        ax.bar(x + width/3,df['U'], width/3, label='dU')
        ax.set_ylim(ymax=1,ymin=-1)
        # ax.grouped_bar(df['E','N','U'])
    
        mask = (
            (df['E_G'].abs() > seuil) |
            (df['N'].abs() > seuil) |
            (df['U'].abs() > seuil)
        )
    
        ax.set_xticks(np.where(mask)[0])
        ax.set_xticklabels(
            df.loc[mask, 'Nom_Station'],
            rotation=60,
            ha='right'
        )
        ax.set_ylabel("Écart en mètres")
        ax.legend()
        ax.grid(True, alpha=1, linestyle ='-')
    
    plt.title("Ecarts de solutions entre les versions de calcul sur toutes les stations SHOM")
    plt.tight_layout()
    plt.show()
    

    
    
    #Affichage Taux de fixation
    fig, (ax1,ax2) = plt.subplots(2, 1, figsize=(15, 12))
    for ax, df in zip(
        [ax1, ax2],
        [All.iloc[:milieu], All.iloc[milieu:]]
    ):
        x = np.arange(len(df))
        width = 0.4
        ax.bar(x - width/2, df['G.1'], width, label='GPS')
        ax.bar(x + width/2, df['E.1'], width, label='Galileo')
        ax.set_xticks(x)
        ax.set_xticklabels(df['STATION'], rotation=60, ha='right')
        ax.set_ylabel("Taux de fixation en %")
        ax.legend()
        ax.grid(True)
    plt.tight_layout()
    plt.title('Taux de fixation des ambiguïtés par station Shom')
    plt.show()
    
    
    
    
    
    
    Obs = {'G.1' : 'Taux de fixation GPS','E.1' : 'Taux de fixation Galileo'
           ,'NbSat.1' : 'Nombre de satellites observés'}
    fig,ax = plt.subplots(2, 3, figsize=(15, 9))
    All['D'] = np.sqrt(All['E_G']**2 + All['N']**2 + All['U']**2)
    
    for i,o in enumerate(Obs.keys()) :
        ax[0,i].scatter(All['D'],All[f"{o}"],marker='+',s=50)
        ax[0,i].set_title(Obs[o])
        ax[0,0].set_ylabel("Distance",rotation=0,labelpad=20)
        ax[0,i].grid()
        
    
    for i,o in enumerate(Obs.keys()) :
        ax[1,i].scatter(abs(All['U']),All[f"{o}"],marker='+',s=50)
        ax[1,0].set_ylabel("Up",rotation=0)
        ax[1,i].set_xlabel("Différence en mètres")
        ax[1,i].grid()
    
    plt.tight_layout()
    plt.show()
    
    ones = np.ones_like(All["D"]).reshape(-1,1)
    
    # All = All[All['D']<0.1]
    fig,ax = plt.subplots(2, 3, figsize=(15, 9))
    for i,l in enumerate(['E','N','U']):
        
        A = np.concatenate((ones,All['D'].to_numpy().reshape(-1,1)),axis=1)
        B = np.sqrt(All[f'v{l}_SPOTGINS'])
        N = A.T@A
        K = A.T@B
        X = np.linalg.inv(N)@K
        V = B - A@X
        sigma0 = V.T@V/(len(B)-2)
        
        B_pred = A@X
        SS_res = np.sum((B - B_pred)**2)
        SS_tot = np.sum((B - np.mean(B))**2)
        R2 = 1 - SS_res / SS_tot
        print(R2)
        
        ax[0,i].scatter(All["D"],np.sqrt(All[f'v{l}_SPOTGINS']),marker='+',s=50)
        ax[0,i].plot(All["D"],X[1]*All["D"]+X[0])
        ax[0, i].text(
        0.05, 0.95,
        f"$\\sigma = {X[1]:.3f}D + {X[0]:.3f}$\n$R^2 = {R2:.3f}$",
        transform=ax[0, i].transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(facecolor="white", alpha=0.8)
        )
        ax[0,i].set_title(f'Ecart-type sur la coordonnée {l}')
        ax[0,0].set_ylabel("SPOTGINS",rotation=0,labelpad = 40)
        ax[0,i].grid()
        
    for i,l in enumerate(['E','N','U']):
        
        A = np.concatenate((ones,All['D'].to_numpy().reshape(-1,1)),axis=1)
        B = np.sqrt(All[f'v{l}_GRG'])
        N = A.T@A
        K = A.T@B
        X = np.linalg.inv(N)@K
        V = B - A@X
        sigma0 = V.T@V/(len(B)-2)
        
        B_pred = A@X
        SS_res = np.sum((B - B_pred)**2)
        SS_tot = np.sum((B - np.mean(B))**2)
        R2 = 1 - SS_res / SS_tot
        print(R2)
        
        ax[1,i].scatter(All["D"],np.sqrt(All[f'v{l}_GRG']),marker='+',s=50)
        ax[1,i].plot(All["D"],X[1]*All["D"]+X[0])
        ax[1, i].text(
        0.5, 0.95,
        f"$\\sigma = {X[1]:.3f}D + {X[0]:.3f}$\n$R^2 = {R2:.3f}$",
        transform=ax[1, i].transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(facecolor="white", alpha=0.8)
        )
        ax[1,0].set_ylabel("Old GRG",rotation=0,labelpad=40)
        ax[1,i].set_xlabel("Différence en mètres")
        ax[1,i].grid()
        
    plt.tight_layout()
    plt.show()
    
    
    #Taux de fixation en fonction du NbObs
    
    All_G = All[(All["NbObs_G.1"]!=0)]  
    plt.figure(figsize=(15,9))
    plt.scatter(All_G["NbObs_G.1"],All_G["G.1"],marker='+',s=50)

    plt.title("Taux de fixation des ambiguïtés GPS en fonction du nombre d'observations")
    plt.xlabel("Nombre d'observations GPS en %")
    plt.ylabel("Taux de fixation GPS")
    plt.grid()
    plt.tight_layout()
    plt.show()
    
    plt.figure(figsize=(15,9))
    All_E = All[(All["NbObs_E.1"]!=0) & (All["E.1"]!=0)]
    plt.scatter(All_E["NbObs_E.1"],All_E["E.1"],marker='+',s=50)
    plt.title("Taux de fixation des ambiguïtés Galileo en fonction du nombre d'observations")
    plt.xlabel("Nombre d'observations Galileo")
    plt.ylabel("Taux de fixation Galileo en %")
    plt.grid()
    plt.tight_layout()
    plt.show()
    
    #NbObs en fonction du NbSat
    data = [All_G,All_E]
    fig,ax = plt.subplots(1,2, figsize=(15, 9))
    Const = {'G':'GPS','E':'Galileo'}
    
    for i,c in enumerate(Const.keys()):   
        ones = np.ones_like(data[i]["D"]).reshape(-1,1)
        A = np.concatenate((ones,data[i][f'NbSat.1'].to_numpy().reshape(-1,1)),axis=1)
        B = data[i][f'NbObs_{c}.1']
        N = A.T@A
        K = A.T@B
        X = np.linalg.inv(N)@K
        V = B - A@X
        sigma0 = V.T@V/(len(B)-2)
        B_pred = A@X
        SS_res = np.sum((B - B_pred)**2)
        SS_tot = np.sum((B - np.mean(B))**2)
        R2 = 1 - SS_res / SS_tot
    
        ax[i].scatter(data[i]["NbSat.1"],data[i][f"NbObs_{c}.1"],marker='+',s=50)
        ax[i].plot(data[i]["NbSat.1"],X[1]*data[i]["NbSat.1"]+X[0])
        ax[i].text(
        0.5, 0.95,
        f"$\\sigma = {X[1]:.3f}D + {X[0]:.3f}$\n$R^2 = {R2:.3f}$",
        transform=ax[i].transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(facecolor="white", alpha=0.8)
        )
        # ax[i].suptitle(f"Nombre d'observations {Const[c]} en fonction du nombre total de satellites")
        ax[i].set_xlabel("Nombre total de satellites")
        ax[i].set_ylabel(f"Nombre d'observations {Const[c]}")
        ax[i].grid()
    plt.tight_layout()
    plt.show()   


    Ecart_V=[]
    for index,row in All.iterrows():
        Ecart_V.append(int(row["VERSION.1"][7:9]) - int(row["VERSION"][7:9]))
        
    plt.figure(figsize=(15,9))
    plt.scatter(Ecart_V,All["D"],marker='+',s=50)
    plt.title("Distance entre les solutions en fonction de l'écart de version de GINS")
    plt.xlabel("Nombre de versions GINS d'écart avec la version actuelle")
    plt.ylabel("Distance entre les solutions en mètres")
    plt.grid()
    plt.tight_layout()
    plt.show()
    
    
    pos_diff = SPOTGINSResults[f"ALBH00CAN_OTL_SHOM.enu"].join(SPOTGINSResults[f"ALBH00CAN_SHOM.enu"].set_index('MJD'),on="MJD",lsuffix='_OTL_SHOM',rsuffix='_SHOM')
    date = pos_diff["MJD"]
    fig, ax = plt.subplots(3,1,figsize=(15,12))
    ax[0].plot(date,pos_diff["E_OTL_SHOM"]-pos_diff["E_SHOM"],marker='o',markersize=1,linewidth=0,color='black')
    ax[0].set_title("dE (en mètres)")
    ax[1].plot(date,pos_diff["N_OTL_SHOM"]-pos_diff["N_SHOM"],marker='o',markersize=1,linewidth=0,color='black')
    ax[1].set_title("dN (en mètres)")
    ax[2].plot(date,pos_diff["U_OTL_SHOM"]-pos_diff["U_SHOM"],marker='o',markersize=1,linewidth=0,color='black')
    ax[2].set_title("dU (en mètres)")
    fig.suptitle(f'Ecarts de positions sur la station ALBH00CAN au SHOM avec différents fichiers OTL')
    plt.show()
    
    #Affichage Nb de satellites
    #Stats
    # corrdXdY=corr(SHOM_Diff['dX'].to_numpy(),SHOM_Diff['dY'].to_numpy())
    # moydX = np.mean(SHOM_Diff['dX'].to_numpy())
    # sigmadX = np.std(SHOM_Diff['dX'].to_numpy())
    # corrdXdZ=corr(SHOM_Diff['dX'].to_numpy(),SHOM_Diff['dZ'].to_numpy())
    # moydY = np.mean(SHOM_Diff['dY'].to_numpy())
    # sigmadY = np.std(SHOM_Diff['dY'].to_numpy())
    # corrdYdZ=corr(SHOM_Diff['dY'].to_numpy(),SHOM_Diff['dZ'].to_numpy())
    # moydZ = np.mean(SHOM_Diff['dZ'].to_numpy())
    # sigmadZ = np.std(SHOM_Diff['dZ'].to_numpy())
    return All
    return All[['Nom_Station','E_WGS84','N_WGS84','H_WGS84']].drop_duplicates(subset=['Nom_Station'])

def SHOM_OMP_POSIT():
    
    Sta = ["ALBH00CAN","CASC00PRT","HOB200AUS","STJO00CAN","ZIMM00CHE"]
    
    for s in Sta :
        
        #Echelle par défaut
        pos_diff = SPOTGINSResults[f"{s}_SHOM.enu"].join(SPOTGINSResults[f"{s}_OMP.enu"].set_index('MJD'),on="MJD",lsuffix='_SHOM',rsuffix='_OMP')
        date = pos_diff["MJD"]
        fig, ax = plt.subplots(3,1,figsize=(15,12))
        ax[0].plot(date,pos_diff["E_SHOM"]-pos_diff["E_OMP"],marker='o',markersize=1,linewidth=0,color='black')
        ax[0].set_title("dE (en mètres)")
        ax[1].plot(date,pos_diff["N_SHOM"]-pos_diff["N_OMP"],marker='o',markersize=1,linewidth=0,color='black')
        ax[1].set_title("dN (en mètres)")
        ax[2].plot(date,pos_diff["U_SHOM"]-pos_diff["U_OMP"],marker='o',markersize=1,linewidth=0,color='black')
        ax[2].set_title("dU (en mètres)")
        fig.suptitle(f'Ecarts de positions entre SHOM et OMP sur {s}')
        plt.show()
        
        #Echelle sub-millimétrique
        pos_sub_diff = SPOTGINSResults["ALBH00CAN_SHOM.enu"].join(SPOTGINSResults["ALBH00CAN_OMP.enu"].set_index('MJD'),on="MJD",lsuffix='_SHOM',rsuffix='_OMP')
        date = pos_sub_diff["MJD"]
        fig, ax = plt.subplots(3,1,figsize=(15,12))
        ax[0].plot(date,pos_sub_diff["E_SHOM"]-pos_sub_diff["E_OMP"],marker='o',markersize=1,linewidth=0,color='black')
        ax[0].set_ylim(-2e-5,2e-5)
        ax[0].set_title("dE (en mètres)")
        ax[1].plot(date,pos_sub_diff["N_SHOM"]-pos_sub_diff["N_OMP"],marker='o',markersize=1,linewidth=0,color='black')
        ax[1].set_ylim(-2e-5,2e-5)
        ax[1].set_title("dN (en mètres)")
        ax[2].plot(date,pos_sub_diff["U_SHOM"]-pos_sub_diff["U_OMP"],marker='o',markersize=1,linewidth=0,color='black')
        ax[2].set_ylim(-2e-5,2e-5)
        ax[2].set_title("dU (en mètres)")
        fig.suptitle('Ecarts de positions entre SHOM et OMP sur ALBH00CAN')
        plt.show()
        
        d = np.sqrt(pos_diff["E_SHOM"]**2 + pos_diff["N_SHOM"]**2 + pos_diff["U_SHOM"]**2) - np.sqrt(pos_diff["E_OMP"]**2 + pos_diff["N_OMP"]**2 + pos_diff["U_OMP"]**2)
        outliers = pos_diff[d>=1E-5]
        print(f"Pourcentage d'outliers sur la série {s} : {round(len(outliers)/len(pos_diff)*100,2)}%")
    
    
def SHOM_OMP_TROPO():
    
    Sta = ["ALBH00CAN","CASC00PRT","HOB200AUS","STJO00CAN","ZIMM00CHE"]
    
    for s in Sta :
        
        ztd_diff = ZTD[f"SPOTGINS_{s}.ztd"].join(ZTD[f"{s}.ztd"].set_index('MJD'),on="MJD",lsuffix='_SHOM',rsuffix='_OMP')
        date = ztd_diff["MJD"]
        fig, ax = plt.subplots(3,1,figsize=(15,12))
        ax[0].plot(date,ztd_diff['TROTOT_SHOM'] - ztd_diff['TROTOT_OMP'],marker='o',markersize=1,linewidth=0,color='black')
        # ax[0].set_ylim(-2e-5,2e-5)
        ax[0].set_title("Différence de tropo totale")
        ax[1].plot(date,ztd_diff['TRODRY_SHOM'] - ztd_diff['TRODRY_OMP'],marker='o',markersize=1,linewidth=0,color='black')
        # ax[1].set_ylim(-2e-5,2e-5)
        ax[1].set_title("Différence de tropo sèche")
        ax[2].plot(date,ztd_diff['TROWET_SHOM'] - ztd_diff['TROWET_OMP'],marker='o',markersize=1,linewidth=0,color='black')
        # ax[2].set_ylim(-2e-5,2e-5)
        ax[2].set_title("Différence de tropo humide")
        fig.suptitle(f'Ecarts de ZTD entre SHOM et OMP sur {s}')
        plt.show()
        
        grad_diff = GRAD[f"SPOTGINS_{s}.grad"].join(GRAD[f"{s}.grad"].set_index('MJD'),on="MJD",lsuffix='_SHOM',rsuffix='_OMP')
        
        date = grad_diff["MJD"]
        fig, ax = plt.subplots(2,1,figsize=(15,12))
        ax[0].plot(date,grad_diff['TGETOT_SHOM'] - grad_diff['TGETOT_OMP'],marker='o',markersize=1,linewidth=0,color='black')
        # ax[0].set_ylim(-2e-5,2e-5)
        ax[0].set_title("Différence de gradient Est")
        ax[1].plot(date,grad_diff['TGNTOT_SHOM'] - grad_diff['TGNTOT_OMP'],marker='o',markersize=1,linewidth=0,color='black')
        # ax[1].set_ylim(-2e-5,2e-5)
        ax[1].set_title("Différence de gradient Nord")
        fig.suptitle(f'Ecarts de Gradients entre SHOM et OMP sur {s}')
        plt.show()

        outliers_ztd = ztd_diff[ (np.abs(ztd_diff['TROTOT_SHOM'] - ztd_diff['TROTOT_OMP']) > 0.01)]
        outliers_grad = grad_diff[np.abs(grad_diff['TGETOT_SHOM'] - grad_diff['TGETOT_OMP'] > 0.01) |
                                    np.abs(grad_diff['TGNTOT_SHOM'] - grad_diff['TGNTOT_OMP'] > 0.01) ]
        print(f"Pourcentage d'outliers sur la série ztd {s} : {round(len(outliers_ztd)/len(ztd_diff)*100,2)}%")
        print(f"Pourcentage d'outliers sur la série grad {s} : {round(len(outliers_grad)/len(grad_diff)*100,2)}%")
        

    
    
def Singugins_IPGP():
    
    # SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"] = SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"].iloc[13:,:]
    SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"]["MJD"] = SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"]["MJD"].round(1)
    ALBH_diff_SINGUGINS = SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"].join(SPOTGINSResults["ALBH00CAN_SHOM.enu"].set_index('MJD'),on="MJD",lsuffix='_SINGUGINS',rsuffix='_SHOM')
    date = ALBH_diff_SINGUGINS["MJD"]
    fig, ax = plt.subplots(3,1,figsize=(15,12))
    ax[0].plot(date,ALBH_diff_SINGUGINS["E_SHOM"]-ALBH_diff_SINGUGINS["E_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[0].plot(date,date*0,linestyle=':',color = 'black')
    #ax[0].set_ylim(-2e-7,2e-7)
    ax[0].set_title("dE (en mètres)")
    ax[0].set_ylabel("Différence de coordonnée East")
    ax[1].plot(date,ALBH_diff_SINGUGINS["N_SHOM"]-ALBH_diff_SINGUGINS["N_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[1].plot(date,date*0,linestyle=':',color = 'black')
    #ax[1].set_ylim(-2e-7,2e-7)
    ax[1].set_title("dN (en mètres)")
    ax[1].set_ylabel("Différence de coordonnée North")
    ax[2].plot(date,ALBH_diff_SINGUGINS["U_SHOM"]-ALBH_diff_SINGUGINS["U_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[2].plot(date,date*0,linestyle=':',color = 'black')
    #ax[2].set_ylim(-2e-7,2e-7)
    ax[2].set_title("dU (en mètres)")
    ax[2].set_ylabel("Différence de coordonnée Up")
    ax[2].set_xlabel("MJD")
    fig.suptitle("Ecarts de résultat entre Singugins et SHOM",fontsize=20)
    plt.show()
    
    ALBH_diff_SINGUGINS = SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"].join(SPOTGINSResults["ALBH00CAN_IPGP.enu"].set_index('MJD'),on="MJD",lsuffix='_SINGUGINS',rsuffix='_OMP')
    date = ALBH_diff_SINGUGINS["MJD"]
    fig, ax = plt.subplots(3,1,figsize=(15,12))
    ax[0].plot(date,ALBH_diff_SINGUGINS["E_OMP"]-ALBH_diff_SINGUGINS["E_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[0].plot(date,date*0,linestyle='--',color = 'black',linewidth=0.7)
    #ax[0].set_ylim(-2e-5,2e-5)
    ax[0].set_title("dE (en mètres)")
    ax[0].set_ylabel("Différence de coordonnée East")
    ax[1].plot(date,ALBH_diff_SINGUGINS["N_OMP"]-ALBH_diff_SINGUGINS["N_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[1].plot(date,date*0,linestyle='--',color = 'black',linewidth=0.7)
    #ax[1].set_ylim(-2e-5,2e-5)
    ax[1].set_title("dN (en mètres)")
    ax[1].set_ylabel("Différence de coordonnée North")
    ax[2].plot(date,ALBH_diff_SINGUGINS["U_OMP"]-ALBH_diff_SINGUGINS["U_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[2].plot(date,date*0,linestyle='--',color = 'black',linewidth=0.7)
    #ax[2].set_ylim(-2e-5,2e-5)
    ax[2].set_title("dU (en mètres)")
    ax[2].set_xlabel("MJD")
    ax[2].set_ylabel("Différence de coordonnée Up")
    fig.suptitle("Ecarts de résultats entre Singugins et IPGP",fontsize=20)
    plt.show()
    
    ALBH_diff_SINGUGINS = SPOTGINSResults["ALBH00CAN_SINGUGINS.enu"].join(SPOTGINSResults["ALBH00CAN_IPGP.enu"].set_index('MJD'),on="MJD",lsuffix='_SINGUGINS',rsuffix='_OMP')
    date = ALBH_diff_SINGUGINS["MJD"]
    fig, ax = plt.subplots(3,1,figsize=(15,12))
    ax[0].plot(date,ALBH_diff_SINGUGINS["E_OMP"]-ALBH_diff_SINGUGINS["E_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[0].plot(date,date*0,linestyle=':',color = 'black')
    ax[0].set_ylim(-2e-5,2e-5)
    ax[0].set_title("dE (en mètres)")
    ax[0].set_ylabel("Différence de coordonnée East")
    ax[1].plot(date,ALBH_diff_SINGUGINS["N_OMP"]-ALBH_diff_SINGUGINS["N_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[1].plot(date,date*0,linestyle=':',color = 'black')
    ax[1].set_ylim(-2e-5,2e-5)
    ax[1].set_title("dN (en mètres)")
    ax[1].set_ylabel("Différence de coordonnée North")
    ax[2].plot(date,ALBH_diff_SINGUGINS["U_OMP"]-ALBH_diff_SINGUGINS["U_SINGUGINS"],marker='o',markersize=1,linewidth=0,color='black')
    #ax[2].plot(date,date*0,linestyle=':',color = 'black')
    ax[2].set_ylim(-2e-5,2e-5)
    ax[2].set_title("dU (en mètres)")
    ax[2].set_xlabel("MJD")
    ax[2].set_ylabel("Différence de coordonnée Up")
    fig.suptitle("Ecarts d'arrondis entre Singugins et IPGP",fontsize=20)
    plt.show()
    
    
def H(x):
    if isinstance(x, (pd.Series, pd.DataFrame)):
        return (x >= 0).astype(int)
    else:
        return 0 if x < 0 else 1
    
def MC_lineaire(A,B,P):
    N = A.T@P@A
    K = A.T@P@B
    X_ = np.linalg.inv(N)@K
    return X_
    

def MC_saisonnier(station,chgmt_antenne=[],corrected=False):
    """Station est le df de la station
    date_debut, date_fin sont les dates sur laquelle on estime la composante saisonnière et la tendance linéaire
    coord est soit "dN", "dE" ou "dU", càd la série temporelle à laquelle on s'interesse"""
    
    fig, ax = plt.subplots(3,1,figsize=(15,12))
    #Pour récupérer les écart-types dans la bonne colonne
    table_ecart_type = {"E":"SE", "N":"SN", "U":"SU"}
    for nc,coord in enumerate(table_ecart_type.keys()):
        ecart_type = table_ecart_type[coord]
        
        
        #Définition des tailles de matrice
        A = np.zeros((station.shape[0], 6+len(chgmt_antenne)))
        P = np.identity(station.shape[0])
        B = np.zeros((station.shape[0], 1))
        
        #Remplissage des matrices
        for i in range(0,station.shape[0]):
            ligne = station.iloc[i]
            t = ligne["Date"]
            A[i,:6] = [t,1,np.cos(2*np.pi*t),np.sin(2*np.pi*t),np.cos(4*np.pi*t), np.sin(4*np.pi*t)]
            A[i,6:] = [H(t-tau) for tau in chgmt_antenne]
            P[i,i] = 1/ligne[ecart_type]**2
            B[i,:] = ligne[coord]
        print(A.shape)
        X_ = MC_lineaire(A,B,P)
        
        
        a,b,c,d,e,f = X_[0,0],X_[1,0],X_[2,0],X_[3,0],X_[4,0],X_[5,0]
        t = station["Date"]
        f = a*t+b+c*np.cos(2*np.pi*t)+d*np.sin(2*np.pi*t)+e*np.cos(4*np.pi*t)+f*np.sin(4*np.pi*t) 
        for i,tau in enumerate(chgmt_antenne):
            f += np.array([H(ti - tau) for ti in t]) * X_[i+6,0]
        station[coord+"_signal_saisonnier"] = station[coord] - (a*t+b)
        
        #Modélisation du signal brut
        if corrected == False:
            ax[nc].plot(t,station[coord],marker='o',markersize=1,linewidth=0,color='blue')
            ax[nc].plot(t,f,color="red")
            ax[nc].set_title(f"{coord} (en mètres)")
        #Modélisation du signal corrigé de la tendance linéaire
        if corrected == True:
            ax[nc].plot(t,station[coord+"_signal_saisonnier"],marker='o',markersize=1,linewidth=0,color='blue')
            ax[nc].plot(t,f-(a*t+b),color="red")
            ax[nc].set_title(f"{coord} (en mètres)")

    plt.show()
    
def SHOM_NGL():
    
    ###Conversion NGL vers ENU
    Refs = np.array([[ -2350703.952688 ,4909742.417940 , -3312874.130422],
                     [-3970925.999058,3048946.815943,-3938538.543603]])
    
    for i,Sta in enumerate(NGLResults.values()):
        E=[]
        N=[]
        U=[] 
        
        SE = []
        SN = []
        SU = []
        
        for index,row in Sta.iterrows():
        
            Xref = Refs[i,0]
            Yref = Refs[i,1]
            Zref = Refs[i,2]
            X = row['X']
            Y = row['Y']
            Z = row['Z']
            lat, lon = heikkinen(Xref,Yref,Zref)   
            dX = X-Xref
            dY = Y-Yref
            dZ = Z-Zref
            
    
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
    
            E.append(mat11*dX + mat12*dY + mat13*dZ)
            N.append(mat21*dX + mat22*dY + mat23*dZ)
            U.append(mat31*dX + mat32*dY + mat33*dZ)  
            
            #Conversion des écarts-types en variances
            cov11 = row["vX"]**2
            cov22 = row["vY"]**2
            cov33 = row["vZ"]**2
            #Conversion des coefficients de corrélation en covariances
            cov12 = row["corrXY"]*row["vX"]*row["vY"]
            cov13 = row["corrXZ"]*row["vX"]*row["vZ"]
            cov23 = row["corrYZ"]*row["vY"]*row["vZ"]
            
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
                
            SE.append(np.sqrt(cov11_enu))
            SN.append(np.sqrt(cov22_enu))
            SU.append(np.sqrt(cov33_enu))
            
        Sta['E']=E
        Sta['N']=N
        Sta['U']=U
        Sta['SE']=SE
        Sta['SN']=SN
        Sta['SU']=SU
        
        fig, ax = plt.subplots(3,1,figsize=(15,12))
        ax[0].plot(Sta['Date'],Sta['E'],marker='o',markersize=1,linewidth=0,color='blue')
        ax[0].set_title("dE (en mètres)")
        ax[1].plot(Sta['Date'],Sta['N'],marker='o',markersize=1,linewidth=0,color='blue')
        ax[1].set_title("dN (en mètres)")
        ax[2].plot(Sta['Date'],Sta['U'],marker='o',markersize=1,linewidth=0,color='blue')
        ax[2].set_title("dU (en mètres)")
        plt.show()

    
if __name__ == "__main__":
    
    cols = ["# type","calendar  epoch","julian days(1950)","correction (X or lat)",
            "position (X or lat)","correction (Y or lon)","position (Y or lon)","correction (Z or h)",
            "position (Z or h)","cov11","cov22","cov33","cov21","cov31","cov32"]
    # data = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_094832.260504_114926.gins.PPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    # data2 = pd.read_csv("../GinsResults/ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml.260504_095248.260504_115338.gins.IPPP",comment = "#",delimiter = "\s+",header = None,names = cols)
    
    
    ### Ouverture des résultats Gins
    GinsResults = Open('../GinsResults/','IPPP')
    
    ### Ouverture des résultats SPOTGINS
    SPOTGINSResults = Open('../GinsResults','enu')
    ZTD = Open('../GinsResults/','ztd')
    GRAD = Open('../GinsResults/','grad')
    ### Ouverture des stations SHOM
    SHOMResults = Open('../RecalculSHOM/ComparDir2','txt')
    
    NGLResults = Open('../GinsResults','xyz')
    
    Gins_Results_ENU = convert(GinsResults)
    
    FixAmbis = pd.read_csv('../RecalculSHOM/Shom.FixAmbis',comment='#',delimiter='\s+')
    
    ### Comparaison avec la ref SHOM
    Diff_dic = Diff(GinsResults, GinsResults['Réf'])
    
    ### Export
    d,useless = Tri(Diff_dic,GinsResults['Réf'])
    
    # export(d,useless,"../GinsResults/Changements_calcul")

    #Ecarts de calcul entre la nouvelle chaine SHOM et SPOTGINS
    
    Sta = ['ALBH','CASC','HOB2','STJO','ZIMM']
    diff = []
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["ALBH_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["ALBH00CAN_OMP.enu"],15).sort_values(by='date').reset_index(drop=True))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["CASC_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["CASC00PRT_OMP.enu"],15).sort_values(by='date').reset_index(drop=True))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["HOB2_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["HOB200AUS_OMP.enu"],15).sort_values(by='date').reset_index(drop=True))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["STJO_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["STJO00CAN_OMP.enu"],15).sort_values(by='date').reset_index(drop=True))
    # diff.append(Diff_SPOTGINS(Gins_Results_ENU["zimm_Calc_15Doy"].sort_values(by="date"),SPOTGINSResults["ZIMM00CHE_OMP.enu"],8).sort_values(by='date').reset_index(drop=True))
    # fig,ax = plt.subplots(3,2,figsize=(18,15))
    # # fig.subplots_adjust(hspace=0.5,wspace=0.1)
    # ax = ax.ravel()
    # for i,d in enumerate(diff):
    #     ax[i].plot(d['date'],d['E'],label = "East",marker='+')
    #     ax[i].plot(d['date'],d['N'],label = "North",marker='+')
    #     ax[i].plot(d['date'],d['U'],label = "Up",marker='+')
    #     # ax[i].xlabel('date au format MM-DD')
    #     # ax[i].ylabel('Différence de coordonnées en mètres')
    #     ax[i].legend()
    #     ax[i].set_title(f"Ecarts de coordonnées entre le SHOM et l'OMP sur la station {Sta[i]} en 2024")
    #     ax[i].grid(True,alpha=0.3)
    # fig.supxlabel("Date au format MM-DD")
    # fig.supylabel("Ecart de coordonées en mètres")
    # ax[-1].axis('off')
    # plt.show()
        # d.to_latex(f'{Sta[i]}.tex',index=False,header=['Ecart en Est','Ecart en Nord','Ecart en Up'])
    # diff[0].to_latex('ZIMM.tex',index=False,header=['Ecart en Est','Ecart en Nord','Ecart en Up'])


    #Ecarts de calcul entre les deux versions SHOM
    # All = EcartsSHOM()
    # All.to_csv('SHOM_coord.csv')
    
    #Ecarts de calcul entre le SHOM et l'OMP
    # SHOM_OMP_POSIT()
    # test = SHOM_OMP_TROPO()
    
    #Ecarts de Singugins
    # Singugins_IPGP()
    
    
    # FUN1 = SPOTGINSResults['FUN100PRT.enu']
    # date = FUN1["MJD"]
    # fig, ax = plt.subplots(3,1,figsize=(15,12))
    # ax[0].plot(date,FUN1['E'],marker='o',markersize=1,linewidth=0,color='black')
    # ax[0].set_title("dE (en mètres)")
    # ax[1].plot(date,FUN1['N'],marker='o',markersize=1,linewidth=0,color='black')
    # ax[1].set_title("dN (en mètres)")
    # ax[2].plot(date,FUN1['U'],marker='o',markersize=1,linewidth=0,color='black')
    # ax[2].set_title("dU (en mètres)")
    # fig.suptitle('Séries temporelles de la station FUN100PRT')
    # plt.show()
    
    # SHOM_NGL()
    MC_saisonnier(SPOTGINSResults["TORK00AUS.enu"],corrected=False)
    MC_saisonnier(SPOTGINSResults["TORK00AUS.enu"],corrected=True)
    
    # MC_saisonnier(NGLResults["WBOL_NGL.xyz"],chgmt_antenne=[2024.197],corrected=False)
    # MC_saisonnier(NGLResults["WBOL_NGL.xyz"],chgmt_antenne=[2024.197],corrected=True)
    
