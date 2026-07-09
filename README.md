# mercator-sync

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=graphql&logoColor=white)
![Vcenter](https://img.shields.io/badge/Vcenter-API-4A90D9?logo=vmware&logoColor=white)
![XOA](https://img.shields.io/badge/XOA-API-4A90D9?logo=cloudflare&logoColor=white)
![Proxmox](https://img.shields.io/badge/Proxmox-API-4A90D9?logo=proxmox&logoColor=white)
![Status](https://img.shields.io/badge/Statut-En%20développement-orange)

## Synchronisation d'une infrastructure de virtualisation avec Mercator
Synchronisation des machines virtuelles et des clusters de différentes sources vers Mercator :
- Vcenter (VMware)
- XOA (XCP-ng)
- Proxmox
## Fonctionnement
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
python sync.py --source vcenter_prod   # une source précise
python sync.py --dry-run               # aucune écriture dans Mercator, "simulation" uniquement
python sync.py --config config/sources.yaml   # chemin alternatif vers le fichier de config
```
---
## En construction pour le reste ! :D
