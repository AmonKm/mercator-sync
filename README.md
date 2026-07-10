# mercator-sync

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=graphql&logoColor=white)
![Vcenter](https://img.shields.io/badge/Vcenter-API-4A90D9?logo=vmware&logoColor=white)
![XOA](https://img.shields.io/badge/XOA-API-4A90D9?logo=cloudflare&logoColor=white)
![Proxmox](https://img.shields.io/badge/Proxmox-API-4A90D9?logo=proxmox&logoColor=white)
![Status](https://img.shields.io/badge/Statut-En%20développement-orange)

# Mercator-sync
## Contexte
Ce repo Gihtub est une **réponse** à un besoin principal : 

Alimenter **Mercator** avec une solution de virtualisation établi dans une organisation. 

Dans mon/notre *contexte*, nous avions notamment besoin de l'ensemble des VMs et des clusters supportant des applications du système.

Faisant suite à différents échanges, le simple script d'alimentation s'est transformé en **orchestrateur** pour qu'il soit modulaire et pour permettre une utilisation généralisé en cas de changement de solution de virtualisation.

Ainsi, ce repo contient un orchestrateur permettant d'alimenter l'ensemble des clusters et des VMs par clusters sur trois sources : **Vcenter, XOA, Proxmox.**

Egalement, il existe un script pour permettre la synchronisation de traitement Grist vers mercator.

---
### Synchronisation des machines virtuelles et des clusters de différentes sources vers Mercator :
### Sources :
- Vcenter (VMware)
- XOA (XCP-ng)
- Proxmox

### Fonctionnement
<img width="1312" height="1352" alt="github_schemzz drawio" src="https://github.com/user-attachments/assets/aa347dc4-fb35-4885-a4ed-d09a4c3f3e2f" />

### Installer le repo et se l'approprier :
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python sync.py --dry-run
```
### Les différentes options :
```
python sync.py                         # toutes les sources activées
python sync.py --source vcenter_prod   # une source précise selon le nom de cette source défini dans config/sources.yaml
python sync.py --dry-run               # aucune écriture dans Mercator, "simulation" uniquement
python sync.py --config config/sources.yaml   # chemin alternatif vers le fichier de config
```
---
### Synchronisation d'un registre de traitement Grist dans Mercator
### Source :
- Grist

### Fonctionnement
<img width="1370" height="430" alt="github-gri drawio" src="https://github.com/user-attachments/assets/361dd847-4c76-459f-9126-12aa2b07df77" />

### Installer le repo et se l'approprier :
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd /Registre-sync
python data-processings-sync.py
```
### Template Grist sur lequel on se base ici :

