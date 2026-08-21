# mercator-sync
 
![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=mapbox&logoColor=white)
![Vcenter](https://img.shields.io/badge/Vcenter-API-4A90D9?logo=vmware&logoColor=white)
![XOA](https://img.shields.io/badge/XOA-API-4A90D9?logo=cloudflare&logoColor=white)
![Proxmox](https://img.shields.io/badge/Proxmox-API-4A90D9?logo=proxmox&logoColor=white)
![Grist](https://img.shields.io/badge/Grist-API-4A90D9?logo=databricks&logoColor=white)
![License](https://img.shields.io/github/license/AmonKm/mercator-sync?cacheSeconds=1)
![Last Commit](https://img.shields.io/github/last-commit/AmonKm/mercator-sync)
![Release](https://img.shields.io/github/v/release/AmonKm/mercator-sync)
 
[🇫🇷 Français](#fr) | [🇬🇧 English](#en)
 
## Sommaire
 
- [Contexte](#contexte)
- [Sync virtualisation -> Mercator](#synchronisation-des-machines-virtuelles-et-des-clusters-de-différentes-sources-vers-mercator)
- [Sync Grist -> Mercator](#synchronisation-dun-registre-de-traitement-grist-dans-mercator)
- [Installation](#installer-le-repo-et-se-lapproprier)
- [Roadmap](ROADMAP.md)
 
---
 
<a name="fr"></a>
 
# FR 🇫🇷
 
## Contexte
 
Ce repo Gihtub est une **réponse** à un besoin principal :
 
Alimenter [**Mercator**](https://github.com/sourcentis/mercator) avec une solution de virtualisation établi dans une organisation.
 
Dans mon/notre *contexte*, nous avions notamment besoin de l'ensemble des VMs et des clusters supportant des applications du système.
 
Faisant suite à différents échanges, le simple script d'alimentation s'est transformé en **orchestrateur** pour qu'il soit modulaire et pour permettre une utilisation généralisé en cas de changement de solution de virtualisation.
 
Ainsi, ce repo contient un orchestrateur permettant d'alimenter l'ensemble des clusters et des VMs par clusters sur trois sources : **Vcenter, XOA, Proxmox.**
 
Egalement, il existe un script pour permettre la synchronisation de traitement Grist vers mercator.
 
---
 
### Synchronisation des machines virtuelles et des clusters de différentes sources vers Mercator
 
### Sources :
 
- Vcenter (VMware)
- XOA (XCP-ng)
- Proxmox
### Fonctionnement
 
<img width="1312" height="1352" alt="github_schemzz drawio" src="https://github.com/user-attachments/assets/aa347dc4-fb35-4885-a4ed-d09a4c3f3e2f" />

### Installer le repo et se l'approprier
 
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

Ce script se base sur l'utilisation d'un template mis à disposition dans ce dépôt : <br>`Registre-sync/Registres-Protection-des-Donnees-template.grist`, un template Grist de Registre des traitements.
<br>
Pour l'ajouter à votre espace :
 
- Aller dans votre espace
- Cliquer sur "Ajouter"
- Cliquer sur "Importer un document"
- Choisir le modèle


 
### Structure
 
Le script Grist est découpé en trois fichiers dans `Registre-sync/`, sur le même principe que l'orchestrateur `sync.py` :
 
```
Registre-sync/
├── registre_sync.py   # Orchestration : boucle principale, CLI
├── grist_client.py    # Client API Grist (lecture des fiches, mappage applications)
└── transform.py        # Mapping des champs Grist -> payload Mercator
```
 
`registre_sync.py` réutilise directement le `MercatorClient` défini dans `sync.py`.

### Configuration
 
En plus de la section `destination.mercator` déjà présente, `config/sources.yaml` contient une section `destination.grist` :
 
```yaml
destination:
  grist:
    base_url: "https://grist.numerique.gouv.fr"
    table_id: Registre_des_Fiches_de_Traitements
    mapping_table_id: Mercator_mappage
    auth:
      doc_id_env: GRIST_DOC_ID
      token_env: GRIST_API_TOKEN
```
 
Le `doc_id` et le token restent dans `.env` (déjà couverts par `.env.example` : `GRIST_API_TOKEN`, `GRIST_DOC_ID`), le reste (URL, noms de tables) est directement en clair dans le yaml puisqu'il n'a rien de sensible.
 
Seules les fiches dont le champ `STATUT` vaut `✅ Fiche traitée` côté Grist sont poussées vers Mercator.
 
### Installer le repo et se l'approprier
 
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd Registre-sync
python3 registre_sync.py --dry-run
```
 
### Les différentes options :
 
```
python registre_sync.py                              # sync mappage applications + fiches de traitement
python registre_sync.py --dry-run                     # aucune écriture dans Mercator, "simulation" uniquement
python registre_sync.py --mapping-only                # met à jour uniquement le mappage des applications Grist <-> Mercator
python registre_sync.py --config ../config/sources.yaml   # chemin alternatif vers le fichier de config
```
 
Le mappage des applications (`Mercator_mappage`) est mis à jour par upsert : les lignes déjà présentes gardent leur id Grist, donc les références déjà posées sur les fiches de traitement (`Application_1/2/3_concernee_par_le_traitement`) ne sont jamais cassées par un run. **ATTENTION** il est nécessaire de modifier votre formulaire pour que le champ d'un traitement vise une entrée de la table mercator_mappage. Un tuto sera bientôt disponible !
 
---
 
<a name="en"></a>
 
# EN 🇬🇧
 
## Context
 
This GitHub repository was created to address the following need:
 
Populate [**Mercator**](https://github.com/sourcentis/mercator) using an organization's existing virtualization solution.
 
In our context, we needed to synchronize all virtual machines and clusters hosting applications within the information system.
 
Following several discussions, what initially started as a simple synchronization script evolved into a modular **orchestrator**, making it reusable and allowing it to support different virtualization platforms if the infrastructure changes.
 
As a result, this repository contains an orchestrator capable of synchronizing clusters and their virtual machines from three different sources: **vCenter, XOA, and Proxmox**.
 
It also includes a script to synchronize a **Grist processing register** with Mercator.
 
---
 
### Synchronizing Virtual Machines and Clusters from Multiple Sources to Mercator
 
### Sources:
 
- vCenter (VMware)
- XOA (XCP-ng)
- Proxmox
### Architecture
 
<img width="1313" height="1352" alt="schema-git drawio" src="https://github.com/user-attachments/assets/201dec34-d85a-4f10-a06d-35e2339957c6" />

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
 
<img width="1371" height="430" alt="schema-grist drawio" src="https://github.com/user-attachments/assets/8a3ce0b6-7ebe-4a9c-b958-7efe0378cdfb" />

This script relies on the use of a template available in this repository: <br>`Registre-sync/Registres-Protection-des-Donnees-template.grist`, a Grist model for the processing registry.
<br>
To add it to your workspace:
 
- Go to your workspace
- Click "Add"
- Click "Import document"
- Choose the template


 
### Structure
 
The Grist script is split into three files under `Registre-sync/`, following the same pattern as the `sync.py` orchestrator:
 
```
Registre-sync/
├── registre_sync.py   # Orchestration: main loop, CLI
├── grist_client.py    # Grist API client (sheet reads, application mapping)
└── transform.py        # Grist field -> Mercator payload mapping
```
 
`registre_sync.py` reuses the `MercatorClient` defined in `sync.py` directly, no duplicated Mercator authentication logic.

### Configuration
 
In addition to the existing `destination.mercator` section, `config/sources.yaml` now includes a `destination.grist` section:
 
```yaml
destination:
  grist:
    base_url: "https://grist.numerique.gouv.fr"
    table_id: Registre_des_Fiches_de_Traitements
    mapping_table_id: Mercator_mappage
    auth:
      doc_id_env: GRIST_DOC_ID
      token_env: GRIST_API_TOKEN
```
 
The `doc_id` and API token stay in `.env` (already covered by `.env.example`: `GRIST_API_TOKEN`, `GRIST_DOC_ID`); everything else (URL, table names) is stored in plain text in the yaml since none of it is sensitive.
 
Only sheets whose `STATUT` field is `✅ Fiche traitée` on the Grist side are pushed to Mercator.
 
### Clone the repository and get started:
 
```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd Registre-sync
python3 registre_sync.py --dry-run
```
 
### Available options:
 
```
python registre_sync.py                               # sync application mapping + processing sheets
python registre_sync.py --dry-run                      # simulation mode (no data is written to Mercator)
python registre_sync.py --mapping-only                 # updates only the Grist <-> Mercator application mapping
python registre_sync.py --config ../config/sources.yaml  # use an alternative configuration file
```
 
The application mapping (`Mercator_mappage`) is updated via upsert: rows that already exist keep their Grist id, so references already set on processing sheets (`Application_1/2/3_concernee_par_le_traitement`) are never broken by a run.
**Careful !** it is necessary to modify your form so that the field of a run is aimed at an entry in the mercator_mappage table. A tutorial will be available soon!
