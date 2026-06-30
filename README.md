# mercator-sync

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=data:image/svg+xml;base64,)
![Status](https://img.shields.io/badge/Statut-En%20développement-orange)
## Synchronisation d'une infrastructure de virtualisation 
Synchronisation des machines virtuelles et des clusters de différentes sources vers Mercator :
- Vcenter (VMware)
- XOA (XCP-ng) en projet
- Proxmox à venir
## Fonctionnement
<img width="1104" height="628" alt="Schema-github-sync-infra drawio" src="https://github.com/user-attachments/assets/ed82a832-1ad7-43c9-8658-70ad0bc95e9d" />

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
