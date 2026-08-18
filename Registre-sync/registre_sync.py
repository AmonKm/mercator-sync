"""
FR :
registre_sync.py Orchestrateur Grist vers Mercator
Synchronise le registre des fiches de traitement Grist vers les objets "data-processings" de Mercator.
Usage :
    python registre_sync.py                          # config par défaut
    python registre_sync.py --config ../config/sources.yaml
    python registre_sync.py --dry-run                # aucune écriture Mercator
"""
"""
EN:
registre_sync.py Grist -> Mercator Orchestrator
Synchronizes the Grist processing register into Mercator's
data-processings.
Usage:
    python registre_sync.py                          # default config
    python registre_sync.py --config ../config/sources.yaml
    python registre_sync.py --dry-run                 # no write to Mercator
"""
