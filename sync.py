"""
FR : 
sync.py Orchestrateur Mercator
Usage :
    python sync.py                         # toutes les sources activées
    python sync.py --source vcenter_prod   # une source précise
    python sync.py --dry-run               # aucune écriture Mercator
"""
"""
EN:
sync.py Mercator Orchestrator
Usage:
    python sync.py                         # all enabled sources
    python sync.py --source vcenter_prod   # a specific source
    python sync.py --dry-run               # no write to Mercator
"""
import argparse
import logging
import os
import time
import requests
import yaml
from dotenv import load_dotenv
load_dotenv(override=True)

from connectors import REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FR : Client Mercator
# EN : Mercator Client
# ---------------------------------------------------------------------------

class MercatorClient: 
# FR : Classe permettant de gérer une session Mercator et de faire appel aux méthodes associées
# EN : Class that manages a Mercator session and exposes the related methods
    def __init__(self, config: dict, dry_run: bool = False):
        base     = config["destination"]["mercator"] 
        # FR : Prend l'entrée mercator avec les différentes sous-entrées dans le fichier sources.yaml
        # EN : Get the mercator entry and its sub-entries from the sources.yaml file

        username = os.environ[base["auth"]["username_env"]] 
        # FR : Identifiant d'un compte Admin de Mercator défini dans .env et utilisé dans sources.yaml
        # EN : Mercator admin account username, defined in .env and referenced in sources.yaml

        password = os.environ[base["auth"]["password_env"]] 
        # FR : Mot de passe d'un compte Admin de Mercator défini dans .env et utilisé dans sources.yaml
        # EN : Mercator admin account password, defined in .env and referenced in sources.yaml

        self.base_url = os.environ[base["base_url"]] 
        # FR : URL de Mercator définie dans sources.yaml
        # EN : Mercator URL, defined in sources.yaml

        self.dry_run  = dry_run 
        # FR : Booléen, si True cela sert à ne pas changer les informations de prod
        # EN : Boolean; if True, prevents any write to production data

        requête = requests.post( 
            # FR : Requête pour obtenir le token visant le endpoint /api/login
            # EN : Request to get the token from the /api/login endpoint
            f"{self.base_url}/api/login",
            headers={"Content-Type": "application/json"},
            json={"login": username, "password": password}
        )

        requête.raise_for_status()
        token = requête.json()["access_token"] 
        # FR : Notre saint token 
        # EN : Our precious token
        self.headers = { 
            # FR : Création du header avec le token 
            # EN : Build the header with the token
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

# FR : Fonction qui permet de créer le dictionnaire "index" pour lier les objets mercator à leurs IDs de source
# EN : Function that builds the "index" dictionary linking Mercator objects to their source IDs
    def build_index(self, endpoint: str, mercator_key: str, source_name: str = None) -> dict[str, int]: 
        # FR : Prend en argument l'endpoint à viser (objets de mercator) et le nom de la source visée (XOA, vCenter...)
        # EN : Takes the target endpoint (Mercator objects) and the source name (XOA, vCenter...) as arguments
        requête = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=10)
        requête.raise_for_status()
        index = {}
        for item in requête.json():
            ext_refs = item.get("ext_refs", "") or ""
            for ref in ext_refs.split("|"):
                if ref.startswith(f"{{{source_name}}}"):
                    val = ref.replace(f"{{{source_name}}}", "")
                    if val:
                        index[val] = item["id"]
        return index

    # FR : Récupère un objet Mercator par son chemin complet
    # EN : Fetches a Mercator object by its full path
    def get(self, path: str) -> dict:
        requête = requests.get(f"{self.base_url}{path}", headers=self.headers, timeout=10)
        requête.raise_for_status()
        return requête.json().get("data", requête.json())

    # FR : Met à jour un objet Mercator par son chemin complet
    # EN : Updates a Mercator object by its full path
    def patch(self, path: str, payload: dict) -> dict:
        requête = requests.patch(f"{self.base_url}{path}", json=payload, headers=self.headers, timeout=10)
        if not requête.ok:
            log.error("PATCH %s failed (%s): %s", path, requête.status_code, requête.text)
        requête.raise_for_status()
        return requête.json()

    # FR : Fonction qui effectue les requêtes pour créer les objets souhaités
    # EN : Function that performs the requests to create the desired objects
    def upsert(self, endpoint: str, index: dict, key_value: str, payload: dict) -> int | None: 
        # FR : Prend en argument l'endpoint visé, le dictionnaire d'index ci-dessus, la clé source, et le payload mappé
        # EN : Takes the target endpoint, the index dict above, the source key, and the mapped payload
        if self.dry_run:
            action = "PATCH" if key_value in index else "POST"
            log.info("[dry-run] %s %s  key=%s", action, endpoint, key_value)
            return 

        if key_value in index: 
            # FR : Si ma valeur de clé est dans l'index, on met à jour l'objet car il existe déjà dans Mercator
            # EN : If the key value is in the index, we update the object since it already exists in Mercator
            requête = requests.patch( 
                # FR : Il existe DONC on patch (update)
                # EN : It exists, SO we patch (update)
                f"{self.base_url}{endpoint}/{index[key_value]}",
                json=payload, headers=self.headers
            )
            time.sleep(1)
        else: 
            # FR : Sinon on le créer 
            # EN : Otherwise, we create it
            requête = requests.post(f"{self.base_url}{endpoint}", json=payload, headers=self.headers)
        if not requête.ok:
            log.warning("Mercator %s  key=%s  status=%s  body=%s",
                        endpoint, key_value, requête.status_code, requête.text[:200])
            return None 
        response_data = requête.json()

        if isinstance(response_data, list):
            return index.get(key_value)
        return response_data.get("id")




def handle_orphans(mercator, index, orphan_ids, mapping, sync_cfg):
    # FR : Pour chaque VM absente du dernier pull, on tague sans supprimer ni renommer
    # EN : For each VM missing from the last pull, we tag it without deleting or renaming
    for source_key in orphan_ids:
        mercator_id = index[source_key]
        try:
            objet = mercator.get(f"{mapping['mercator_endpoint']}/{mercator_id}")
            current_name = objet.get("name", "")
            current_attributes_str = objet.get("attributes", "")
            current_attributes_tokens = current_attributes_str.split()

            if sync_cfg["orphan_tag"] in current_attributes_tokens:
                continue  # FR : deja tague, on ne repasse pas dessus | EN : Already tagged, skipping 

            payload = {
                "name": current_name,
                "attributes": f"{current_attributes_str} {sync_cfg['orphan_tag']}".strip(),
            }
            mercator.patch(f"{mapping['mercator_endpoint']}/{mercator_id}", payload)
            print(f"[ORPHAN] {current_name} ({source_key}) tague comme orphelin")
        except Exception as e:
            log.error("Echec du tag orphelin pour %s (mercator_id=%s) : %s", source_key, mercator_id, e)
            continue



# ---------------------------------------------------------------------------
# Code principal - Contient la gestion des sources
# Main code - Contains source management
# ---------------------------------------------------------------------------

# FR : Fonction qui orchestre le tout, elle fait appel aux méthodes pour créer les mappings et mettre à jour ou créer les objets pour les sources souhaitées
# EN : Function that orchestrates everything; it calls the methods to build mappings and update or create the objects for the target sources
def sync_source(source_name: str, source_cfg: dict, mappings: dict,
                mercator: MercatorClient, sync_cfg: dict) -> None: 
    # FR : Fonction principale, prend le nom de la source, sa conf dans sources.yaml, le mapping d'URL selon le type de source, l'instance MercatorClient authentifiée et la section sync du yaml (orphelins, dry_run)
    # EN : Main function, takes the source name, its config in sources.yaml, the URL mapping for the source type, the authenticated MercatorClient instance, and the sync section of the yaml (orphans, dry_run)

    source_type = source_cfg["type"] 
    if source_type not in REGISTRY: 
        # FR : Gestion d'un type inconnu (proxmox par exemple :D)
        # EN : Handles an unknown type (proxmox for example :D)
        log.error("Type inconnu : %s", source_type)
        return

    connector = REGISTRY[source_type](source_name, source_cfg)
    log.info("=== Source : %s (%s) ===", source_name, source_type)
# ------ FR : Essai de connexion sur la source
# ------ EN : Attempt to connect to the source
    try:
        connector.authenticate()
    except Exception as e:
        log.error("Authentification échouée pour %s : %s", source_name, e)
        return

    map = mappings.get(source_type, {})
    cluster_cfg = map.get("cluster") 
    vm_cfg      = map.get("logical_server")

    # --- FR : Index Mercator (une seule requête par endpoint) ---
    # --- EN : Mercator index (one request per endpoint) ---

    cluster_index = mercator.build_index(cluster_cfg["mercator_endpoint"], cluster_cfg["mercator_key"], source_name) if cluster_cfg else {}
    vm_index      = mercator.build_index(vm_cfg["mercator_endpoint"],      vm_cfg["mercator_key"], source_name)      if vm_cfg      else {}

    seen_vm_keys = set()
    mercator_cluster_id = None
    # --- Extract + Transform + Load ---
    try:
        clusters = connector.fetch_clusters()
    except Exception as e:
        log.warning("Récupération des clusters échouée pour %s : %s", source_name, e)
        return

    for cluster in clusters:
        mercator_cluster_id = None
        cluster_id = cluster[cluster_cfg["source_key"]] if cluster_cfg else cluster["id"]

        if cluster_cfg:
            payload_cluster = connector.build_cluster_payload(cluster_id, cluster)
            mercator_cluster_id = mercator.upsert(cluster_cfg["mercator_endpoint"], cluster_index, cluster_id, payload_cluster)
            log.info("Cluster : %s", payload_cluster.get("name", cluster_id))
        try:
            vms = connector.fetch_vms(cluster_id)
        except Exception as e:
            log.warning("Récupération des VMs échouée pour le cluster %s : %s", cluster_id, e)
            continue
        for vm in vms: 
            # FR : Parcours des VMs 
            # EN : Loop over VMs
            vm_id = str(vm[vm_cfg["source_key"]])
            try:
                enriched = connector.enrich_vm(vm_id, vm)
            except Exception as e:
                log.warning("Enrichissement échoué pour VM %s : %s", vm_id, e)
                continue

            payload_vm = connector.build_vm_payload(vm_id, enriched)
            # Une VM vCenter appartient à un seul cluster
            # TODO : si plusieurs clusters possibles, récupérer la liste existante via GET et appender

            # A vCenter VM belongs to a single cluster
            # TODO: if several clusters are possible, fetch the existing list via GET and append
            if mercator_cluster_id:
                payload_vm["clusters"] = [mercator_cluster_id]

            payload_vm[vm_cfg["mercator_key"]] = vm_id
            mercator.upsert(vm_cfg["mercator_endpoint"], vm_index, vm_id, payload_vm)
            seen_vm_keys.add(vm_id)
            log.info("  VM : %s", payload_vm.get("name", vm_id))


    if vm_cfg:
        orphan_ids = set(vm_index.keys()) - seen_vm_keys
        if orphan_ids:
            handle_orphans(mercator, vm_index, orphan_ids, vm_cfg, sync_cfg)


# ---------------------------------------------------------------------------
# FR : Entrée
# EN : Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",  default="config/sources.yaml")
    parser.add_argument("--source",  default=None, help="Nom d'une source précise")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    with open(arguments.config) as fichier_config:
        configuration = yaml.safe_load(fichier_config)

    dry_run          = arguments.dry_run or configuration.get("sync", {}).get("dry_run", False)
    client_mercator  = MercatorClient(configuration, dry_run=dry_run)
    mappings         = configuration.get("mappings", {})
    config_sync      = configuration.get("sync", {})

    sources = configuration.get("sources", {})
    if arguments.source:
        sources = {
            nom_source: config_source
            for nom_source, config_source in sources.items()
            if nom_source == arguments.source
        }

    for nom_source, config_source in sources.items():
        if not config_source.get("enabled", True):
            log.info("Source désactivée : %s", nom_source)
            continue
        sync_source(nom_source, config_source, mappings, client_mercator, config_sync)


if __name__ == "__main__":
    main()
