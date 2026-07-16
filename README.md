# mercator-sync

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=mapbox&logoColor=white)
![Vcenter](https://img.shields.io/badge/Vcenter-API-4A90D9?logo=vmware&logoColor=white)
![XOA](https://img.shields.io/badge/XOA-API-4A90D9?logo=cloudflare&logoColor=white)
![Proxmox](https://img.shields.io/badge/Proxmox-API-4A90D9?logo=proxmox&logoColor=white)
![Grist](https://img.shields.io/badge/Grist-API-4A90D9?logo=databricks&logoColor=white)
![Status](https://img.shields.io/badge/Statut-En%20développement-orange)

## FR 🇫🇷
## Contexte
Ce repo Gihtub est une **réponse** à un besoin principal : 

Alimenter [**Mercator**](https://github.com/sourcentis/mercator) avec une solution de virtualisation établi dans une organisation. 

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

Ce script se base sur l'utilisation d'un template mis à disposition dans votre espace Grist.
Il suffit d'aller sur ce lien : https://grist.numerique.gouv.fr/o/docs/p/templates
Puis de cliquer sur le template "Registre Protection des données".
Une fois fait, il suffit de :
- Cliquer sur "Ajouter"
- Ajouter une page
- Table
- Nouvelle Table
- La renommer **mercator_mappage**
- La placer sous "TRAITEMENTS (script)"

```
Cette procédure sera automatiser à l'avenir (au moins en partie et directement dans le script)
```


### Installer le repo et se l'approprier :
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd /Registre-sync
python3 data-processings-sync.py
```
# EN 🇬🇧
## Context
This GitHub repository was created to address the following need:

Populate [**Mercator**](https://github.com/sourcentis/mercator) using an organization's existing virtualization solution.

In our context, we needed to synchronize all virtual machines and clusters hosting applications within the information system.

Following several discussions, what initially started as a simple synchronization script evolved into a modular **orchestrator**, making it reusable and allowing it to support different virtualization platforms if the infrastructure changes.

As a result, this repository contains an orchestrator capable of synchronizing clusters and their virtual machines from three different sources: **vCenter, XOA, and Proxmox**.

It also includes a script to synchronize a **Grist processing register** with Mercator.

---
### Synchronizing Virtual Machines and Clusters from Multiple Sources to Mercator:
### Sources:
- vCenter (VMware)
- XOA (XCP-ng)
- Proxmox

### Architecture
<img width="1312" height="1352" alt="github_schemzz drawio" src="https://github.com/user-attachments/assets/aa347dc4-fb35-4885-a4ed-d09a4c3f3e2f" />

### Clone the repository and get started:
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python sync.py --dry-run
```

### Available options:
```
python sync.py                               # synchronize all enabled sources
python sync.py --source vcenter_prod         # synchronize a specific source defined in config/sources.yaml
python sync.py --dry-run                     # simulation mode (no data is written to Mercator)
python sync.py --config config/sources.yaml  # use an alternative configuration file
```

---
### Synchronizing a Grist Processing Register with Mercator
### Source:
- Grist

### Architecture
<img width="1370" height="430" alt="github-gri drawio" src="https://github.com/user-attachments/assets/361dd847-4c76-459f-9126-12aa2b07df77" />

This script relies on the use of a template available in your Grist workspace.

Simply open the following link:
https://grist.numerique.gouv.fr/o/docs/p/templates

Then:

- Click **"Data Protection Register"**. If you don't see it, click **"Registre Protection des données"**.
- Click **"Add"**.
- Add a new page.
- Create a new table.
- Rename it **mercator_mapping**.
- Place it under **"PROCESSINGS (script)"**. **Warning** : This may appear as "TRAITEMENTS (script)".

```
This setup will be automated in a future release (at least partially and directly from the script).
```

### Clone the repository and get started:
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd Registre-sync
python3 data-processings-sync.py
```
