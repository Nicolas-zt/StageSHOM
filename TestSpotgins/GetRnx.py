import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import subprocess
import time
import sys

def GetRnx(y,d) :
    start = time.time()
    
    base_url = "http://loading.u-strasbg.fr/SPOTGINS/TEST/rinex/"
    RNX2 = ".Z"
    RNX3 = ".crx.gz"
    dossier_sortie = "Rinex/"
    
    os.makedirs(dossier_sortie, exist_ok=True)
    
    s = requests.Session()

    year = f"{y}/"
    url_year = urljoin(base_url,year)
    os.makedirs(os.path.join(dossier_sortie,year),exist_ok = True)
    
     
    day = f"{d:03d}/"
    url_day = urljoin(url_year, day)
    os.makedirs(os.path.join(dossier_sortie,year,day),exist_ok = True)

    print(f"\nLecture : {url_day}")

    try:
        r = requests.get(url_day, timeout=15)

        soup = BeautifulSoup(r.text, "html.parser")

        liens = []
        sta = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            if href.endswith(RNX3):
                liens.append(urljoin(url_day, href))
                sta.append(href[:4])
            elif href.endswith(RNX2) and href[:4].upper() not in sta:
                liens.append(urljoin(url_day, href))

        print(f"{len(liens)} fichiers trouvés")

        for lien in liens:

            nom = os.path.basename(lien)
            chemin = os.path.join(dossier_sortie,year,day,nom)

            if os.path.exists(chemin[:-2]) or os.path.exists(chemin[:-3]):
                print(f"Déjà présent : {nom}")
                continue

            print(f"Téléchargement : {nom}")

            fichier = requests.get(lien, stream=True)
            fichier.raise_for_status()

            with open(chemin, "wb") as f:
                for chunk in fichier.iter_content(8192):
                    f.write(chunk)
                    
                    
            if False:     
                subprocess.run([
                    r"C:\Program Files\7-Zip\7z.exe",
                    "x",
                    chemin,
                    f"-o{os.path.dirname(chemin)}",
                    "-y"
                ], check=True)
                
                os.remove(chemin)
                
                

    except Exception as e:
        print("Erreur :", e)
            
    end = time.time()
    t = (end - start)//60
    print(f"Temps total du téléchargement : {t}")

if __name__ == "__main__":
    
    y = int(sys.argv[1])
    d = int(sys.argv[2])
    GetRnx(y,d)
