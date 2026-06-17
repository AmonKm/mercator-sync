# mercator-sync

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Mercator](https://img.shields.io/badge/Mercator-API-4A90D9?logo=data:image/svg+xml;base64,)
![Status](https://img.shields.io/badge/Statut-En%20développement-orange)

Synchronisation des machines virtuelles XCP-ng/XOA vers [Mercator](https://github.com/dbarzin/mercator) par réconciliation sur l'attribut `xcpng_id:`.
En projet : Synchronisation des machines virtuelles Vcenter (VMware)

---

## Fonctionnement

```
Mercator API
  │
  ▼
Index Mercator (xcpng_id:uuid)
  │
  ▼
Récupération des VMs XOA
  │
  ▼
Mapping payload → champs Mercator
  │
  ├── xcpng_id connu → PATCH sur Mercator (mise à jour)
  └── xcpng_id inconnu → POST sur Mercator (création)
```

Le script suit trois étapes :

1. **Index** : interroge l'API Mercator pour récupérer tous les serveurs logiques dont l'attribut contient un tag `xcpng_id:`, et construit une table de réconciliation `{ uuid_xcpng → id_mercator }`.
2. **Collecte** : interroge l'API REST XOA pour lister les VMs du pool cible avec leurs détails (CPU, mémoire, OS, IP, tags). (L'id du pool peut ne pas être précisé.
3. **Upsert** : pour chaque VM, construit un payload mappé sur les champs Mercator. Si l'`uuid` est présent dans l'index, la VM est mise à jour (`PATCH`). Sinon, elle est créée (`POST`) avec le tag `xcpng_id:<uuid>` dans le champ attribut.

---

## Champs synchronisés
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

```bash
git clone https://github.com/AmonKm/mercator-sync
cd mercator-sync
pip install requests
```

---

## Configuration

> Un `.env.example` sera disponible prochainement. En attendant, les champs à modifier sont directement dans le script :

| Ligne | Champ | Description |
|-------|-------|-------------|
| 41 | `BASE_URL_MERCATOR` | URL de l'instance Mercator |
| 43 | `login` | Login du compte admin Mercator |
| 77 | `BASE_URL_XOA` | URL de l'instance XOA |
| 84 | `$pool:[ID_DU_POOL]` | ID du pool XCP-ng à synchroniser si nécessaire |

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
