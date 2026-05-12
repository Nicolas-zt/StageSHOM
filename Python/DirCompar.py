import pandas as pd 
import yaml

def flatten(d, parent_key=""):
    items = []
    
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            items.extend(flatten(v, new_key))
            
    elif isinstance(d, list):
        for i, v in enumerate(d):
            new_key = f"{parent_key}[{i}]"
            items.extend(flatten(v, new_key))
            
    else:
        items.append((parent_key, str(d)))
        
    return items


def convert(file):
    with open(file, "r") as f:
        data = yaml.safe_load(f)
        
    flat = flatten(data)
    
    return pd.DataFrame(flat, columns=["key", "value"])


def missing(f1, f2):
    # On compare les clés
    missing_f1 = f1[~f1["key"].isin(f2["key"])]
    missing_f2 = f2[~f2["key"].isin(f1["key"])]
    return missing_f1,missing_f2

def diff(f1,f2,noms):
    diff = f1.merge(f2,on="key",suffixes = (f'_{noms[0]}',f'_{noms[1]}'))
    diff = diff[diff[f"value_{noms[0]}"] != diff[f"value_{noms[1]}"]]
    
    drop = []
    values_x = set(diff[f"value_{noms[0]}"])
    values_y = set(diff[f"value_{noms[1]}"])
    
    for index,row in diff.iterrows():
        if row[f"value_{noms[0]}"] in values_y:
            try: 
                float(row[f"value_{noms[0]}"]) 
            except:
                print(row[f"value_{noms[0]}"])
                drop.append(index)
                
        elif row[f"value_{noms[1]}"] in values_x:
            try: 
                float(row[f"value_{noms[0]}"]) 
            except:
                print(row[f"value_{noms[0]}"])
                drop.append(index)
            
    diff.drop(drop, inplace=True)
    return diff

if __name__ == "__main__":

    shom_directeur = convert("ALBH00CAN_R_20250010000_01D_30S_MO.rnx.yml")
    singugins_directeur = convert("directeur.yml")
    modele = convert('DIR_SPOTGINS_G20_GE_VALIDE_25_2.yml')

    missing_shom,missing_singugins = missing(shom_directeur, singugins_directeur)
    df_diff = diff(shom_directeur, singugins_directeur,["Shom","Singugins"])
    
    verif_singu = diff(modele,singugins_directeur,["modele","singugins"])

    