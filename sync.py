"""
sync.py Orchestrateur Mercator
Usage :
    python sync.py                         # toutes les sources activées
    python sync.py --source vcenter_prod   # une source précise
    python sync.py --dry-run               # aucune écriture Mercator
"""
import argparse
import logging
import os
import time
import requests
import yaml
from dotenv import load_dotenv
load_dotenv(override=True)
print(os.environ.get("MERCATOR_USER", "NON CHARGÉ"))

from connectors import REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s") # Parce que pourquoi pas
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Client Mercator
# ---------------------------------------------------------------------------

class MercatorClient: # Classe qui permet de définir différentes méthodes pour mercator 

    def __init__(self, config: dict, dry_run: bool = False):
        base     = config["destination"]["mercator"] # Prend l'entrée mercator avec les différentes sous-entrées dans le fichier sources.yaml
        username = os.environ[base["auth"]["username_env"]] # Login d'un compte Admin de Mercator défini dans .env et sources.yaml
        password = os.environ[base["auth"]["password_env"]] # Password d'un compte Admin de Mercator défini dans .env et sources.yaml
        self.base_url = os.environ[base["base_url"]] # URL de Mercator défini dans sources.yaml
        self.dry_run  = dry_run # Booléen, si True cela servira à ne pas changer les informations de prod

        requête = requests.post( # Requête pour obtenir letoken visant le endpoint /api/login
            f"{self.base_url}/api/login",
            headers={"Content-Type": "application/json"},
            json={"login": username, "password": password}
        )

        requête.raise_for_status()
        token = requête.json()["access_token"] # Notre saint token
        self.headers = { # Création du header avec le token -> Attribut de la classe
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def build_index(self, endpoint: str, mercator_key: str, source_name: str = None) -> dict[str, int]: # retirer clé, on change de logique avec ext refs !
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

    def upsert(self, endpoint: str, index: dict, key_value: str, payload: dict) -> int | None: # Prend en argument l'endpoint à viser, le dictionnaire d'index au dessus, une valeur de clé de la source, le payload mappé !
        if self.dry_run: # Si notre dry_run est True
            action = "PATCH" if key_value in index else "POST"
            log.info("[dry-run] %s %s  key=%s", action, endpoint, key_value)
            return # On fait pas vraiment la requête en gros ... :D

        if key_value in index: # Si ma valeur de cle est dans l'index ou met à jour l'objet car il existe dans mercator
            requête = requests.patch( # Il existe DONC on patch (update)
                f"{self.base_url}{endpoint}/{index[key_value]}",
                json=payload, headers=self.headers
            )
            time.sleep(1)
        else: # Sinon on le créer 
            requête = requests.post(f"{self.base_url}{endpoint}", json=payload, headers=self.headers)
        if not requête.ok:
            log.warning("Mercator %s  key=%s  status=%s  body=%s",
                        endpoint, key_value, requête.status_code, requête.text[:200]) # A revoir pour modifier le warning
            return None 
        response_data = requête.json()

        if isinstance(response_data, list): # A revoir !!!
            return index.get(key_value)
        return response_data.get("id")

    def tag_orphans(self, endpoint: str, orphan_tag: str, seen_keys: set, mercator_key: str) -> None: # A revoir, en construction ...
        return None


# ---------------------------------------------------------------------------
# Code principal - Contient la gestion des sources
# ---------------------------------------------------------------------------
# OLD
# def parse_attribute(attributes: str, key: str) -> str | None: # Key étant la clé soit xcpng_id ou vcenter_id pour identifier la source
#     """Extrait la valeur d'une clé dans le champ attributes Mercator."""
#     for attr in attributes.split(" "):
#         if attr.startswith(f"{key}:"):
#             return attr.split(":", 1)[1]
#     return None
# La logique changera, un champ sera disponible pour la gestion de source directement intégré à Mercator !!!
# --------------------------------------------------------------------------
def sync_source(source_name: str, source_cfg: dict, mappings: dict,
                mercator: MercatorClient, sync_cfg: dict) -> None: # La fonction principale, prend en argument le nom de la source, sa conf contenu dans sources.yaml + le mappings d'url en fonction du type de source, l'instance MercatorClient authentifié et la section sync du yaml contenant la notion d'orphan et de dry_run

    source_type = source_cfg["type"] # Soit xoa soit vcenter
    if source_type not in REGISTRY: # Gestion d'un type inconnu (proxmox par exemple :D)
        log.error("Type inconnu : %s", source_type)
        return

    connector = REGISTRY[source_type](source_name, source_cfg) # On se base sur notre fichier init
    log.info("=== Source : %s (%s) ===", source_name, source_type) # Pour la décoration
# ------ Essai de connexion sur la source 
    try:
        connector.authenticate()
    except Exception as e:
        log.error("Authentification échouée pour %s : %s", source_name, e)
        return

    map = mappings.get(source_type, {}) 
    cluster_cfg = map.get("cluster") # On prend la section cluster de l'une des sources contenant le endpoint à viser, la cle id et la source cle (vm ou cluster)
    vm_cfg      = map.get("logical_server")

    # --- Index Mercator (une seule requête par endpoint) ---
    cluster_index = mercator.build_index(cluster_cfg["mercator_endpoint"], cluster_cfg["mercator_key"], source_name) if cluster_cfg else {}
    vm_index      = mercator.build_index(vm_cfg["mercator_endpoint"],      vm_cfg["mercator_key"], source_name)      if vm_cfg      else {}

    seen_vm_keys = set() # Un ensemble pour l'unicité des valeurs quand même !
    mercator_cluster_id = None
    # --- Extract + Transform + Load ---
    clusters = connector.fetch_clusters()
    for cluster in clusters:
        cluster_id = cluster[cluster_cfg["source_key"]] if cluster_cfg else cluster["id"]

        if cluster_cfg:
            payload_cluster = connector.build_cluster_payload(cluster_id, cluster)
            mercator_cluster_id = mercator.upsert(cluster_cfg["mercator_endpoint"], cluster_index, cluster_id, payload_cluster)
            log.info("Cluster : %s", payload_cluster.get("name", cluster_id))

        vms = connector.fetch_vms(cluster_id)
        for vm in vms:
            vm_id = str(vm[vm_cfg["source_key"]])
            try:
                enriched = connector.enrich_vm(vm_id, vm)
            except Exception as e:
                log.warning("Enrichissement échoué pour VM %s : %s", vm_id, e)
                continue

            payload_vm = connector.build_vm_payload(vm_id, enriched)
            # Une VM vCenter appartient à un seul cluster
            # TODO : si plusieurs clusters possibles, récupérer la liste existante via GET et appender
            if mercator_cluster_id:
                payload_vm["clusters"] = [mercator_cluster_id]

            mercator.upsert(vm_cfg["mercator_endpoint"], vm_index, vm_id, payload_vm)
            seen_vm_keys.add(vm_id)
            log.info("  VM : %s", payload_vm.get("name", vm_id))

        # --- Tag orphelins --- A revoir...
    if vm_cfg:
        mercator.tag_orphans(
            vm_cfg["mercator_endpoint"],
            sync_cfg.get("orphan_tag", "etat_sync:orphelin"),
            seen_vm_keys,
            vm_cfg["mercator_key"],
        )


# ---------------------------------------------------------------------------
# Entrée
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
# Equivalent de tout ça :
# nouveau_dict = {}
# for nom_source, config_source in sources.items():
#     if nom_source == arguments.source:
#         nouveau_dict[nom_source] = config_source
# sources = nouveau_dict

    for nom_source, config_source in sources.items():
        if not config_source.get("enabled", True):
            log.info("Source désactivée : %s", nom_source)
            continue
        sync_source(nom_source, config_source, mappings, client_mercator, config_sync)


# En construction
# TODO : 
# Proxmox
# Plusieurs clusters ?
# Enrichir les informations.
# Condenser le code + efficace ?
# Concanténer les attributs et ne pas les écraser dans les payloads !


if __name__ == "__main__":
    main()
