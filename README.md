# mercator-sync

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=data:image/svg+xml;base64,)
![Status](https://img.shields.io/badge/Statut-En%20développement-orange)

Synchronisation des machines virtuelles et des clusters de différentes sources vers Mercator :
- XOA (XCP-ng) en projet
- Vcenter (VMware)

---

## Fonctionnement

```
Mercator API
  │
  ▼
Index Mercator (xcpng_id:uuid) Ou vcenter_id dans le cas de vcenter
  │
  ▼
Récupération des VMs
  │
  ▼
Mapping payload en fonction de la source → champs Mercator - Parcours par cluster
  │
  ├── id connu → PATCH sur Mercator (mise à jour)
  └── id inconnu → POST sur Mercator (création)
```

Le script suit trois étapes :

1. **Index** : interroge l'API Mercator pour récupérer tous les serveurs logiques dont l'attribut contient un tag `xcpng_id:` ou `vcenter_id`, et construit une table de réconciliation `{ uuid → id_mercator }`.
2. **Collecte** : interroge l'API REST de la source pour lister les VMs avec leurs détails (CPU, mémoire, OS, IP, tags) et le cluster associé.
3. **Upsert** : pour chaque VM, construit un payload mappé sur les champs Mercator. Si l'`uuid` est présent dans l'index, la VM est mise à jour (`PATCH`). Sinon, elle est créée (`POST`) avec le tag `xcpng_id:<uuid>` dans le champ attribut.

---

## Champs synchronisés # A revoir depuis la nouvelle version avec Vcenter + Orch
Ce tableau est amené à évoluer :
| XOA | Mercator |
|-----|----------|
| `name_label` | `name` |
| `uuid` | `attributes` (`xcpng_id:`) |
| `CPUs.number` | `cpu` |
| `memory.size` | `memory` (Go) |
| `os_version.name` | `operating_system` |
| `mainIpAddress` | `address_ip` |
| `os_version.distro` | `attributes` (`distro:`) |
| `tags` | `attributes` |

---

## Installation

```bash # En cours
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
pip install requests
```

---

## Configuration 
Se base désormais sur un .env et un fichier yml !
> Un `.env.example` sera disponible prochainement. En attendant, les champs à modifier sont directement dans le script :

| Ligne | Champ | Description |
|-------|-------|-------------|
| 41 | `BASE_URL_MERCATOR` | URL de l'instance Mercator |
| 43 | `login` | Login du compte admin Mercator |
| 77 | `BASE_URL_XOA` | URL de l'instance XOA |
| 85 | `$pool:[ID_DU_POOL]` | ID du pool XCP-ng à synchroniser si nécessaire |

Au lancement, le script demande interactivement :
- le mot de passe du compte Mercator
- le token d'authentification XOA

---

## Utilisation

```bash
python sync_xcpng.py
```

---

## Prérequis

- Python 3.10+
- Un compte admin Mercator avec accès à l'API
- Un token d'authentification XOA (`authenticationToken`) avec les accès API.
- Instance Mercator en 2026.06.11
