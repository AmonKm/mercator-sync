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
## En construction ! :D
