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
import argparse
import logging
import sys
from pathlib import Path
 
from dotenv import load_dotenv
import yaml
 
RACINE = Path(__file__).resolve().parent.parent
# FR : Racine du projet, pour retrouver sync.py et le .env peu importe le cwd
# EN : Project root, to find sync.py and .env regardless of the cwd
sys.path.insert(0, str(RACINE))
load_dotenv(RACINE / ".env", override=True)
 
from sync import MercatorClient
from grist_client import GristClient
from transform import payload_grist
 
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)
 
STATUT_TRAITE = "✅ Fiche traitée"
# FR : On ne pousse vers Mercator que les fiches marquées comme traitées côté Grist
# EN : Only sheets marked as processed on the Grist side are pushed to Mercator
 
 
# FR : Boucle principale, prend les clients déjà authentifiés
# EN : Main loop, takes the already-authenticated clients
def sync_data_processings(mercator: MercatorClient, grist: GristClient) -> None:
    grist.sync_applications_mercator(mercator)
    app_index = grist.get_app_index()
 
    index = mercator.build_index("/api/data-processings", mercator_key="grist_uuid", source_name="Grist")
 
    records = grist.get_records()
    for record in records:
        fields = record.get("fields", {})
        uuid = fields.get("UUID")
        if fields.get("STATUT") != STATUT_TRAITE or not uuid:
            continue
 
        payload = payload_grist(record, app_index)
        mercator.upsert("/api/data-processings", index, uuid, payload)
        log.info("Fiche traitement : %s", payload.get("name", uuid))
 
 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(RACINE / "config" / "sources.yaml"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--mapping-only",
        action="store_true",
        help="FR : Met à jour uniquement la table de mappage applications, sans synchroniser les fiches de traitement. "
             "EN : Updates only the applications mapping table, without syncing the processing sheets.",
    )

    arguments = parser.parse_args()
 
    with open(arguments.config) as fichier_config:
        configuration = yaml.safe_load(fichier_config)
 
    dry_run = arguments.dry_run or configuration.get("sync", {}).get("dry_run", False)
 
    mercator = MercatorClient(configuration, dry_run=dry_run)
    grist = GristClient(configuration)

    # FR : Toujours exécuté, même en --mapping-only : sync_data_processings() a besoin
    #      d'un mappage à jour pour résoudre les colonnes Application_X des fiches.
    # EN : Always run, even with --mapping-only: sync_data_processings() needs an
    #      up-to-date mapping to resolve the sheets' Application_X columns.
    grist.sync_applications_mercator(mercator)
 
    if arguments.mapping_only:
        log.info("Mode --mapping-only : table de mappage mise à jour, fiches de traitement non synchronisées.")
        return
 
    sync_data_processings(mercator, grist)
 
 
if __name__ == "__main__":
    main()
